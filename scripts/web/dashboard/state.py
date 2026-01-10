import threading
import time
from io import BytesIO
import zipfile
from typing import Dict, List, Tuple

import matplotlib.pyplot as plt
import pandas as pd

from model import WarehouseModel
from agents import RobotAgent, ShelfAgent, PackingStationAgent

SCENARIO_PRESETS = {
    "Light Load": {
        "num_robots": 5,
        "grid_size": 20,
        "max_steps": 200,
        "order_mode": "fixed_orders",
        "order_count": 10,
        "order_rate": 0.3,
        "robot_failure_step": None,
        "clustered_orders": False,
        "cluster_center_x": 10,
        "cluster_center_y": 10,
        "cluster_radius": 5,
    },
    "Medium Load": {
        "num_robots": 5,
        "grid_size": 20,
        "max_steps": 200,
        "order_mode": "fixed_orders",
        "order_count": 30,
        "order_rate": 0.3,
        "robot_failure_step": None,
        "clustered_orders": False,
        "cluster_center_x": 10,
        "cluster_center_y": 10,
        "cluster_radius": 5,
    },
    "Heavy Load": {
        "num_robots": 5,
        "grid_size": 20,
        "max_steps": 200,
        "order_mode": "fixed_orders",
        "order_count": 50,
        "order_rate": 0.3,
        "robot_failure_step": None,
        "clustered_orders": False,
        "cluster_center_x": 10,
        "cluster_center_y": 10,
        "cluster_radius": 5,
    },
    "Robot Failure": {
        "num_robots": 5,
        "grid_size": 20,
        "max_steps": 200,
        "order_mode": "fixed_orders",
        "order_count": 30,
        "order_rate": 0.3,
        "robot_failure_step": 80,
        "clustered_orders": False,
        "cluster_center_x": 10,
        "cluster_center_y": 10,
        "cluster_radius": 5,
    },
    "Clustered Orders": {
        "num_robots": 5,
        "grid_size": 20,
        "max_steps": 200,
        "order_mode": "fixed_orders",
        "order_count": 30,
        "order_rate": 0.3,
        "robot_failure_step": None,
        "clustered_orders": True,
        "cluster_center_x": 10,
        "cluster_center_y": 10,
        "cluster_radius": 5,
    },
    "Dynamic Orders": {
        "num_robots": 5,
        "grid_size": 20,
        "max_steps": 200,
        "order_mode": "probabilistic",
        "order_count": 30,
        "order_rate": 0.4,
        "robot_failure_step": None,
        "clustered_orders": False,
        "cluster_center_x": 10,
        "cluster_center_y": 10,
        "cluster_radius": 5,
    },
    "Congestion Test": {
        "num_robots": 12,
        "grid_size": 12,
        "max_steps": 200,
        "order_mode": "fixed_orders",
        "order_count": 40,
        "order_rate": 0.3,
        "robot_failure_step": None,
        "clustered_orders": False,
        "cluster_center_x": 6,
        "cluster_center_y": 6,
        "cluster_radius": 3,
    },
    "Custom": {
        "num_robots": 5,
        "grid_size": 20,
        "max_steps": 200,
        "order_mode": "fixed_orders",
        "order_count": 20,
        "order_rate": 0.3,
        "robot_failure_step": None,
        "clustered_orders": False,
        "cluster_center_x": 10,
        "cluster_center_y": 10,
        "cluster_radius": 5,
    },
}

MECHANISM_DESCRIPTIONS = {
    "cnp": "Contract Negotiation Protocol",
    "greedy": "Greedy Assignment",
    "centralized": "Centralized Planner",
}


class SimulationState:
    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.model = None
        self.running = False
        self.step_count = 0
        self.metrics_history: List[Dict] = []
        self.selected_scenario = "Medium Load"
        self.mechanism = "cnp"
        self.speed = 5
        self.chart_window = 100
        self.preset_params = SCENARIO_PRESETS["Medium Load"].copy()
        self.custom_params = SCENARIO_PRESETS["Custom"].copy()
        self.active_params = SCENARIO_PRESETS["Medium Load"].copy()
        self.last_step_time = time.time()
        self.time_accum = 0.0
        self.batch_results = None
        self.suite_results = None
        self.suite_status = {"running": False, "progress": 0.0, "status": "Idle"}
        self.custom_initialized = False


class SimulationStore:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._states: Dict[str, SimulationState] = {}

    def get(self, session_id: str) -> SimulationState:
        with self._lock:
            if session_id not in self._states:
                self._states[session_id] = SimulationState()
            return self._states[session_id]


store = SimulationStore()


def create_model_from_params(params: Dict, mechanism: str) -> WarehouseModel:
    cluster_center = None
    if params.get("clustered_orders", False):
        cluster_center = (params["cluster_center_x"], params["cluster_center_y"])

    model = WarehouseModel(
        num_robots=params["num_robots"],
        grid_width=params["grid_size"],
        grid_height=params["grid_size"],
        coordination_mechanism=mechanism,
        order_generation_mode=params["order_mode"],
        order_generation_rate=params["order_rate"],
        fixed_order_count=params["order_count"],
        max_steps=params["max_steps"],
        robot_failure_step=params["robot_failure_step"],
        clustered_orders=params["clustered_orders"],
        cluster_center=cluster_center,
        cluster_radius=params["cluster_radius"],
    )
    return model


def ensure_model(state: SimulationState) -> None:
    if state.model is None:
        state.model = create_model_from_params(state.active_params, state.mechanism)
        state.step_count = state.model.step_count


def reset_simulation(state: SimulationState) -> None:
    state.model = create_model_from_params(state.active_params, state.mechanism)
    state.running = False
    state.step_count = 0
    state.metrics_history = []
    state.last_step_time = time.time()
    state.time_accum = 0.0
    state.batch_results = None


def get_grid_snapshot(model: WarehouseModel) -> Dict:
    snapshot = {
        "robots": [],
        "shelves": [],
        "stations": [],
        "orders": [],
        "grid_size": [model.grid_width, model.grid_height],
    }

    for agent in model.schedule.agents:
        if isinstance(agent, RobotAgent):
            snapshot["robots"].append(
                {
                    "id": agent.unique_id,
                    "pos": [agent.pos[0], agent.pos[1]],
                    "state": agent.state,
                    "battery": agent.battery_level,
                    "target": list(agent.target) if agent.target else None,
                    "current_task": agent.current_task,
                }
            )
        elif isinstance(agent, ShelfAgent):
            snapshot["shelves"].append({"pos": [agent.pos[0], agent.pos[1]]})
        elif isinstance(agent, PackingStationAgent):
            snapshot["stations"].append({"pos": [agent.pos[0], agent.pos[1]]})

    for order in model.orders:
        snapshot["orders"].append(
            {
                "id": order["id"],
                "pickup": list(order["pickup"]),
                "delivery": list(order["delivery"]),
                "assigned": order.get("assigned", False),
                "completed": order.get("completed", False),
            }
        )

    return snapshot


def get_live_metrics(model: WarehouseModel) -> Dict:
    if not model or not model.robot_agents:
        return {}

    num_robots = len(model.robot_agents)
    if num_robots == 0:
        return {}

    total_distance = sum(r.total_distance_traveled for r in model.robot_agents)
    attempted_conflicts = sum(r.attempted_conflicts for r in model.robot_agents)
    hard_blocks = sum(r.hard_blocks for r in model.robot_agents)
    total_conflicts = attempted_conflicts + hard_blocks
    total_idle = sum(r.idle_steps for r in model.robot_agents)
    avg_battery = sum(r.battery_level for r in model.robot_agents) / num_robots

    tasks_per_robot = [r.tasks_completed for r in model.robot_agents]
    avg_tasks = sum(tasks_per_robot) / num_robots
    variance = sum((t - avg_tasks) ** 2 for t in tasks_per_robot) / num_robots

    completed = len(model.completed_orders)
    generated = model.orders_generated_count
    step = model.step_count if model.step_count > 0 else 1

    throughput = completed / step
    efficiency = completed / total_distance if total_distance > 0 else 0

    delays = []
    for order in model.completed_orders:
        delay = order.get("completion_time", 0) - order.get("announce_time", 0)
        delays.append(delay)
    avg_delay = sum(delays) / len(delays) if delays else 0

    idle_robots = len([r for r in model.robot_agents if r.state == "idle"])
    broken_robots = len([r for r in model.robot_agents if r.state == "broken"])
    active_orders = len([o for o in model.orders if not o.get("completed", False)])

    return {
        "step": model.step_count,
        "orders_generated": generated,
        "orders_completed": completed,
        "active_orders": active_orders,
        "throughput": throughput,
        "efficiency": efficiency,
        "total_distance": total_distance,
        "avg_battery": avg_battery,
        "idle_robots": idle_robots,
        "broken_robots": broken_robots,
        "attempted_conflicts": attempted_conflicts,
        "hard_blocks": hard_blocks,
        "total_conflicts": total_conflicts,
        "total_idle_time": total_idle,
        "fairness_variance": variance,
        "avg_completion_delay": avg_delay,
        "avg_tasks_per_robot": avg_tasks,
        "avg_battery_end": avg_battery,
    }


def get_robots_snapshot(model: WarehouseModel) -> List[Dict]:
    if not model or not model.robot_agents:
        return []

    rows = []
    for robot in model.robot_agents:
        if robot.current_task and isinstance(robot.current_task, dict):
            task_id = str(robot.current_task.get("id", "-"))
        else:
            task_id = "-"

        target_str = f"{robot.target}" if robot.target else "-"

        rows.append(
            {
                "id": str(robot.unique_id),
                "state": str(robot.state),
                "battery": round(robot.battery_level, 1),
                "tasks_completed": robot.tasks_completed,
                "distance": round(robot.total_distance_traveled, 1),
                "conflicts": robot.attempted_conflicts,
                "hard_blocks": robot.hard_blocks,
                "current_task": task_id,
                "target": target_str,
            }
        )

    return rows


def get_orders_summary(model: WarehouseModel) -> Tuple[List, List, List]:
    if not model:
        return [], [], []

    pending = []
    assigned = []
    completed = []

    for order in model.orders:
        order_info = {
            "id": order["id"],
            "pickup": list(order["pickup"]),
            "delivery": list(order["delivery"]),
            "announce_time": order.get("announce_time", 0),
        }

        if order.get("completed", False):
            order_info["completion_time"] = order.get("completion_time", 0)
            order_info["delay"] = order_info["completion_time"] - order_info["announce_time"]
            completed.append(order_info)
        elif order.get("assigned", False):
            assigned.append(order_info)
        else:
            pending.append(order_info)

    return pending, assigned, completed


def advance_simulation(state: SimulationState) -> None:
    if not state.model:
        return

    if state.running and state.model.running:
        now = time.time()
        dt = now - state.last_step_time
        state.last_step_time = now
        state.time_accum += dt

        step_period = 1.0 / max(1, state.speed)

        while state.time_accum >= step_period and state.model.running:
            state.model.step()
            state.step_count = state.model.step_count
            metrics = get_live_metrics(state.model)
            if metrics:
                state.metrics_history.append(metrics)
                if len(state.metrics_history) > state.chart_window:
                    state.metrics_history = state.metrics_history[-state.chart_window :]
            state.time_accum -= step_period

        if not state.model.running:
            state.running = False
    else:
        state.last_step_time = time.time()


def normalize_params(params: Dict) -> Dict:
    grid_size = max(8, min(30, int(params.get("grid_size", 20))))
    max_steps = max(50, min(500, int(params.get("max_steps", 200))))
    num_robots = max(1, min(20, int(params.get("num_robots", 5))))

    order_mode = params.get("order_mode", "fixed_orders")
    order_count = max(5, min(100, int(params.get("order_count", 20))))
    order_rate = float(params.get("order_rate", 0.3))

    clustered_orders = bool(params.get("clustered_orders", False))

    cx = int(params.get("cluster_center_x", grid_size // 2))
    cy = int(params.get("cluster_center_y", grid_size // 2))
    cx = max(0, min(grid_size - 1, cx))
    cy = max(0, min(grid_size - 1, cy))

    cluster_radius = max(1, min(10, int(params.get("cluster_radius", 5))))

    failure_step = params.get("robot_failure_step", None)
    if failure_step is None or failure_step == "":
        failure_step = None
    else:
        failure_step = int(failure_step)
        if failure_step < 1:
            failure_step = 1
        if failure_step > max_steps:
            failure_step = max_steps

    return {
        "num_robots": num_robots,
        "grid_size": grid_size,
        "max_steps": max_steps,
        "order_mode": order_mode,
        "order_count": order_count,
        "order_rate": order_rate,
        "clustered_orders": clustered_orders,
        "cluster_center_x": cx,
        "cluster_center_y": cy,
        "cluster_radius": cluster_radius,
        "robot_failure_step": failure_step,
    }


def apply_config(state: SimulationState, payload: Dict) -> None:
    reset_needed = False

    if "speed" in payload:
        try:
            state.speed = max(1, min(20, int(payload["speed"])))
        except (TypeError, ValueError):
            pass

    if "mechanism" in payload:
        mechanism = payload["mechanism"]
        if mechanism in MECHANISM_DESCRIPTIONS and mechanism != state.mechanism:
            state.mechanism = mechanism
            reset_needed = True

    if "scenario" in payload:
        scenario = payload["scenario"]
        if scenario in SCENARIO_PRESETS and scenario != state.selected_scenario:
            state.selected_scenario = scenario
            if scenario == "Custom":
                if not state.custom_initialized:
                    state.custom_params = state.preset_params.copy()
                    state.custom_initialized = True
                state.active_params = state.custom_params.copy()
            else:
                state.preset_params = SCENARIO_PRESETS[scenario].copy()
                state.active_params = state.preset_params.copy()
                state.custom_initialized = False
            reset_needed = True

    if "params" in payload:
        params = normalize_params(payload["params"])
        if params != state.active_params:
            state.custom_params = params.copy()
            state.active_params = params.copy()
            state.custom_initialized = True
            reset_needed = True

    if reset_needed:
        reset_simulation(state)


def run_all_mechanisms_batch(params: Dict) -> Dict:
    mechanisms = ["cnp", "greedy", "centralized"]
    results = {}
    max_steps = params.get("max_steps", 200)

    for mech in mechanisms:
        batch_model = create_model_from_params(params, mech)

        while batch_model.running and batch_model.step_count < max_steps:
            batch_model.step()

        final_metrics = batch_model.get_metrics()

        if hasattr(batch_model.datacollector, "get_model_vars_dataframe"):
            model_df = batch_model.datacollector.get_model_vars_dataframe()
        else:
            model_df = batch_model.datacollector.get_model_reporters_dataframe()

        agent_df = batch_model.datacollector.get_agent_vars_dataframe()

        results[mech] = {
            "metrics": final_metrics,
            "model_df": model_df,
            "agent_df": agent_df,
        }

    return results


def run_full_experiment_suite(progress_cb=None) -> Dict:
    scenarios_to_run = [
        ("Light Load", SCENARIO_PRESETS["Light Load"]),
        ("Medium Load", SCENARIO_PRESETS["Medium Load"]),
        ("Heavy Load", SCENARIO_PRESETS["Heavy Load"]),
        ("Robot Failure", SCENARIO_PRESETS["Robot Failure"]),
        ("Clustered Orders", SCENARIO_PRESETS["Clustered Orders"]),
        ("Dynamic Orders", SCENARIO_PRESETS["Dynamic Orders"]),
        ("Congestion Test", SCENARIO_PRESETS["Congestion Test"]),
    ]

    mechanisms = ["cnp", "greedy", "centralized"]

    all_results = {
        "summary": [],
        "scenarios": {},
        "pngs": {},
    }

    total_runs = len(scenarios_to_run) * len(mechanisms)
    current_run = 0

    for scenario_name, scenario_params in scenarios_to_run:
        scenario_results = {}

        for mechanism in mechanisms:
            current_run += 1
            if progress_cb:
                progress_cb(current_run, total_runs, scenario_name, mechanism)

            model = create_model_from_params(scenario_params, mechanism)

            while model.running:
                model.step()

            metrics = model.get_metrics()

            if hasattr(model.datacollector, "get_model_vars_dataframe"):
                model_df = model.datacollector.get_model_vars_dataframe()
            else:
                model_df = model.datacollector.get_model_reporters_dataframe()

            summary_row = {
                "Scenario": scenario_name,
                "Mechanism": mechanism.upper(),
                "Throughput": metrics["throughput"],
                "Efficiency": metrics["efficiency"],
                "Total_Distance": metrics["total_distance"],
                "Total_Conflicts": metrics["total_conflicts"],
                "Total_Hard_Blocks": metrics["hard_blocks"],
                "Fairness_Variance": metrics["task_fairness_variance"],
                "Avg_Completion_Delay": metrics["avg_completion_delay"],
                "Avg_Battery_End": metrics["avg_battery_end"],
                "Orders_Completed": metrics["total_orders_completed"],
                "Orders_Generated": metrics["total_orders_generated"],
            }
            all_results["summary"].append(summary_row)

            scenario_results[mechanism] = {
                "metrics": metrics,
                "timeseries": model_df,
            }

        try:
            png_buffer = create_comparison_visualizations(scenario_results, scenario_name)
            all_results["pngs"][scenario_name] = png_buffer
        except Exception:
            pass

        all_results["scenarios"][scenario_name] = scenario_results

    return all_results


def create_comparison_visualizations(all_mechanisms_results: Dict, scenario_name: str) -> BytesIO:
    mechanisms = ["cnp", "greedy", "centralized"]

    fig, axes = plt.subplots(2, 2, figsize=(14, 10), facecolor="white")
    fig.suptitle(
        f"Scenario: {scenario_name} - Mechanism Comparison",
        fontsize=16,
        fontweight="bold",
    )

    ax = axes[0, 0]
    for mech in mechanisms:
        df = all_mechanisms_results[mech]["timeseries"]
        ax.plot(df.index, df["Throughput"], label=mech.upper(), linewidth=2)
    ax.set_xlabel("Step")
    ax.set_ylabel("Throughput (orders completed)")
    ax.set_title("Throughput Over Time")
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_facecolor("#fafafa")

    ax = axes[0, 1]
    for mech in mechanisms:
        df = all_mechanisms_results[mech]["timeseries"]
        ax.plot(df.index, df["Active_Orders"], label=mech.upper(), linewidth=2)
    ax.set_xlabel("Step")
    ax.set_ylabel("Active Orders")
    ax.set_title("Active Orders Over Time")
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_facecolor("#fafafa")

    ax = axes[1, 0]
    for mech in mechanisms:
        df = all_mechanisms_results[mech]["timeseries"]
        ax.plot(df.index, df["Avg_Battery"], label=mech.upper(), linewidth=2)
    ax.set_xlabel("Step")
    ax.set_ylabel("Avg Battery Level")
    ax.set_title("Average Battery Over Time")
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_facecolor("#fafafa")

    ax = axes[1, 1]
    for mech in mechanisms:
        df = all_mechanisms_results[mech]["timeseries"]
        ax.plot(df.index, df["Total_Conflicts"], label=mech.upper(), linewidth=2)
    ax.set_xlabel("Step")
    ax.set_ylabel("Total Conflicts")
    ax.set_title("Total Conflicts Over Time")
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_facecolor("#fafafa")

    plt.tight_layout()

    img_buffer = BytesIO()
    plt.savefig(img_buffer, format="png", dpi=100, bbox_inches="tight", facecolor="white")
    img_buffer.seek(0)
    plt.close(fig)

    return img_buffer


def start_suite(state: SimulationState) -> None:
    if state.suite_status.get("running"):
        return

    state.suite_status = {"running": True, "progress": 0.0, "status": "Starting"}
    state.suite_results = None

    def run_suite():
        def progress_cb(current, total, scenario, mechanism):
            with state.lock:
                state.suite_status = {
                    "running": True,
                    "progress": current / total,
                    "status": f"Running: {scenario} - {mechanism.upper()} ({current}/{total})",
                }

        results = run_full_experiment_suite(progress_cb)
        with state.lock:
            state.suite_results = results
            state.suite_status = {"running": False, "progress": 1.0, "status": "Complete"}

    thread = threading.Thread(target=run_suite, daemon=True)
    thread.start()


def clear_suite(state: SimulationState) -> None:
    state.suite_results = None
    state.suite_status = {"running": False, "progress": 0.0, "status": "Idle"}


def format_batch_results(batch_results: Dict) -> List[Dict]:
    if not batch_results:
        return []

    rows = []
    for mech, result in batch_results.items():
        metrics = result["metrics"]
        rows.append(
            {
                "mechanism": mech.upper(),
                "throughput": metrics["throughput"],
                "efficiency": metrics["efficiency"],
                "total_distance": metrics["total_distance"],
                "total_conflicts": metrics["total_conflicts"],
                "fairness_variance": metrics["task_fairness_variance"],
            }
        )

    return rows


def build_state_payload(state: SimulationState) -> Dict:
    ensure_model(state)

    metrics = get_live_metrics(state.model)
    pending, assigned, completed = get_orders_summary(state.model)

    payload = {
        "config": {
            "selected_scenario": state.selected_scenario,
            "mechanism": state.mechanism,
            "speed": state.speed,
            "active_params": state.active_params,
        },
        "running": state.running,
        "model_running": state.model.running if state.model else False,
        "step_count": state.step_count,
        "snapshot": get_grid_snapshot(state.model),
        "metrics": metrics,
        "metrics_history": state.metrics_history,
        "orders": {
            "pending": pending,
            "assigned": assigned,
            "completed": completed,
        },
        "robots": get_robots_snapshot(state.model),
        "batch_results": format_batch_results(state.batch_results),
        "suite_results": state.suite_results["summary"] if state.suite_results else [],
        "suite_status": state.suite_status,
    }

    return payload


def export_suite_csv(summary_rows: List[Dict]) -> str:
    if not summary_rows:
        return ""
    df = pd.DataFrame(summary_rows)
    return df.to_csv(index=False)


def export_suite_zip(summary_rows: List[Dict], pngs: Dict[str, BytesIO]) -> BytesIO:
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zip_file:
        if summary_rows:
            summary_csv = export_suite_csv(summary_rows)
            zip_file.writestr("summary.csv", summary_csv)
        for scenario_name, png_buffer in pngs.items():
            zip_file.writestr(f"warehouse_{scenario_name}.png", png_buffer.getvalue())
    zip_buffer.seek(0)
    return zip_buffer


def export_batch_summary_csv(batch_results: Dict) -> str:
    if not batch_results:
        return ""

    rows = []
    for mech, result in batch_results.items():
        metrics = result["metrics"]
        rows.append(
            {
                "Mechanism": mech.upper(),
                "Throughput": metrics["throughput"],
                "Efficiency": metrics["efficiency"],
                "Total_Distance": metrics["total_distance"],
                "Total_Conflicts": metrics["total_conflicts"],
                "Fairness_Variance": metrics["task_fairness_variance"],
                "Orders_Completed": metrics["total_orders_completed"],
                "Orders_Generated": metrics["total_orders_generated"],
            }
        )

    df = pd.DataFrame(rows)
    return df.to_csv(index=False)


def export_batch_model_csv(batch_results: Dict) -> str:
    if not batch_results:
        return ""

    frames = []
    for mech, result in batch_results.items():
        model_df = result.get("model_df")
        if model_df is None:
            continue
        df = model_df.copy()
        df["Mechanism"] = mech.upper()
        frames.append(df)

    if not frames:
        return ""

    combined = pd.concat(frames, axis=0)
    return combined.to_csv()


def export_batch_agent_csv(batch_results: Dict) -> str:
    if not batch_results:
        return ""

    frames = []
    for mech, result in batch_results.items():
        agent_df = result.get("agent_df")
        if agent_df is None:
            continue
        df = agent_df.copy()
        df["Mechanism"] = mech.upper()
        frames.append(df)

    if not frames:
        return ""

    combined = pd.concat(frames, axis=0)
    return combined.to_csv()
