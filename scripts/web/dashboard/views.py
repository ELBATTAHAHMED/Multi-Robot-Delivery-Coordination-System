import json
import time
import uuid

from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from .state import (
    MECHANISM_DESCRIPTIONS,
    SCENARIO_PRESETS,
    apply_config,
    build_state_payload,
    clear_suite,
    ensure_model,
    export_suite_csv,
    export_suite_zip as build_suite_zip,
    get_live_metrics,
    run_all_mechanisms_batch,
    start_suite,
    store,
)


def get_session_id(request) -> str:
    if "sid" not in request.session:
        request.session["sid"] = uuid.uuid4().hex
    return request.session["sid"]


def index(request):
    session_id = get_session_id(request)
    state = store.get(session_id)
    with state.lock:
        payload = build_state_payload(state)

    mechanisms = [
        {"value": key, "label": key.upper(), "description": desc}
        for key, desc in MECHANISM_DESCRIPTIONS.items()
    ]

    context = {
        "initial_state": json.dumps(payload),
        "scenarios": json.dumps(list(SCENARIO_PRESETS.keys())),
        "mechanisms": json.dumps(mechanisms),
    }
    return render(request, "dashboard/index.html", context)


@require_http_methods(["GET"])
def api_state(request):
    session_id = get_session_id(request)
    state = store.get(session_id)
    with state.lock:
        payload = build_state_payload(state)
    return JsonResponse(payload)


@require_http_methods(["POST"])
def api_tick(request):
    session_id = get_session_id(request)
    state = store.get(session_id)
    with state.lock:
        ensure_model(state)
        from .state import advance_simulation

        advance_simulation(state)
        payload = build_state_payload(state)
    return JsonResponse(payload)


@require_http_methods(["POST"])
def api_config(request):
    session_id = get_session_id(request)
    state = store.get(session_id)
    payload = json.loads(request.body or "{}")
    with state.lock:
        apply_config(state, payload)
        payload = build_state_payload(state)
    return JsonResponse(payload)


@require_http_methods(["POST"])
def api_control(request):
    session_id = get_session_id(request)
    state = store.get(session_id)
    payload = json.loads(request.body or "{}")
    action = payload.get("action")

    with state.lock:
        ensure_model(state)
        if action == "reset":
            from .state import reset_simulation

            reset_simulation(state)
        elif action == "play":
            state.running = True
            state.last_step_time = time.time()
            state.time_accum = 0.0
        elif action == "pause":
            state.running = False
        elif action == "step":
            if state.model and state.model.running:
                state.model.step()
                state.step_count = state.model.step_count
                metrics = get_live_metrics(state.model)
                if metrics:
                    state.metrics_history.append(metrics)
                    if len(state.metrics_history) > state.chart_window:
                        state.metrics_history = state.metrics_history[-state.chart_window :]
        payload = build_state_payload(state)

    return JsonResponse(payload)


@require_http_methods(["POST"])
def api_run_batch(request):
    session_id = get_session_id(request)
    state = store.get(session_id)
    with state.lock:
        params = state.active_params.copy()

    batch_results = run_all_mechanisms_batch(params)

    with state.lock:
        state.batch_results = batch_results
        payload = build_state_payload(state)

    return JsonResponse(payload)


@require_http_methods(["POST"])
def api_run_suite(request):
    session_id = get_session_id(request)
    state = store.get(session_id)
    with state.lock:
        start_suite(state)
        payload = build_state_payload(state)
    return JsonResponse(payload)


@require_http_methods(["POST"])
def api_clear_suite(request):
    session_id = get_session_id(request)
    state = store.get(session_id)
    with state.lock:
        clear_suite(state)
        payload = build_state_payload(state)
    return JsonResponse(payload)


@require_http_methods(["GET"])
def export_metrics(request):
    session_id = get_session_id(request)
    state = store.get(session_id)
    with state.lock:
        ensure_model(state)
        metrics = get_live_metrics(state.model)
    json_str = json.dumps(metrics, indent=2)
    response = HttpResponse(json_str, content_type="application/json")
    response["Content-Disposition"] = "attachment; filename=metrics_summary.json"
    return response


@require_http_methods(["GET"])
def export_model_csv(request):
    session_id = get_session_id(request)
    state = store.get(session_id)
    with state.lock:
        ensure_model(state)
        if hasattr(state.model.datacollector, "get_model_vars_dataframe"):
            model_df = state.model.datacollector.get_model_vars_dataframe()
        else:
            model_df = state.model.datacollector.get_model_reporters_dataframe()
    csv = model_df.to_csv()
    response = HttpResponse(csv, content_type="text/csv")
    response["Content-Disposition"] = "attachment; filename=model_data.csv"
    return response


@require_http_methods(["GET"])
def export_agent_csv(request):
    session_id = get_session_id(request)
    state = store.get(session_id)
    with state.lock:
        ensure_model(state)
        agent_df = state.model.datacollector.get_agent_vars_dataframe()
    csv = agent_df.to_csv()
    response = HttpResponse(csv, content_type="text/csv")
    response["Content-Disposition"] = "attachment; filename=agent_data.csv"
    return response


@require_http_methods(["GET"])
def export_suite_summary(request):
    session_id = get_session_id(request)
    state = store.get(session_id)
    with state.lock:
        if not state.suite_results:
            return HttpResponse("No suite results", status=404)
        csv = export_suite_csv(state.suite_results["summary"])
    response = HttpResponse(csv, content_type="text/csv")
    response["Content-Disposition"] = "attachment; filename=experiment_suite_summary.csv"
    return response


@require_http_methods(["GET"])
def export_suite_zip(request):
    session_id = get_session_id(request)
    state = store.get(session_id)
    with state.lock:
        if not state.suite_results:
            return HttpResponse("No suite results", status=404)
        zip_buffer = build_suite_zip(state.suite_results["summary"], state.suite_results["pngs"])
    response = HttpResponse(zip_buffer.getvalue(), content_type="application/zip")
    response["Content-Disposition"] = "attachment; filename=experiment_suite.zip"
    return response
