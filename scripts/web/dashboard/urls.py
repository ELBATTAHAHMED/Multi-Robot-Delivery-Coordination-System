from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("api/state", views.api_state, name="api_state"),
    path("api/tick", views.api_tick, name="api_tick"),
    path("api/config", views.api_config, name="api_config"),
    path("api/control", views.api_control, name="api_control"),
    path("api/run-batch", views.api_run_batch, name="api_run_batch"),
    path("api/run-suite", views.api_run_suite, name="api_run_suite"),
    path("api/clear-suite", views.api_clear_suite, name="api_clear_suite"),
    path("api/export/metrics", views.export_metrics, name="export_metrics"),
    path("api/export/model", views.export_model_csv, name="export_model_csv"),
    path("api/export/agent", views.export_agent_csv, name="export_agent_csv"),
    path("api/export/suite/summary", views.export_suite_summary, name="export_suite_summary"),
    path("api/export/suite/zip", views.export_suite_zip, name="export_suite_zip"),
]
