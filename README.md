# Multi-Robot Delivery Coordination System
A Mesa-based warehouse simulation with a Django dashboard for live control, visualization, and exports.

## Project Overview
This project simulates a warehouse where multiple robots pick items from shelves and deliver them to packing stations. The simulation compares three coordination mechanisms (CNP, Greedy, Centralized), tracks performance metrics, and provides both a CLI runner and a web dashboard for interactive exploration.

## System Architecture
- **WarehouseModel (Mesa)**: owns the grid, order generation, metrics collection, and simulation loop.
- **RobotAgent**: navigates the grid, manages battery state, picks orders, and completes deliveries.
- **OrderManagerAgent**: announces and assigns orders for CNP and Centralized modes.
- **ShelfAgent / PackingStationAgent**: static grid objects that define pickup and delivery locations.
- **Django dashboard**: per-session in-memory state, REST endpoints, and a front-end UI.

## Coordination Mechanisms
- **Contract Net Protocol (CNP)**: manager announces unassigned orders every 2 steps; idle robots with sufficient battery bid; lowest bid wins.
- **Greedy**: each idle robot selects the nearest unassigned order on its own.
- **Centralized**: manager computes a cost for each idle robot and assigns the lowest-cost robot.

## Simulation Lifecycle
1. Generate orders (fixed count or probabilistic).
2. Assign tasks based on the selected mechanism.
3. Move robots toward pickup and then delivery targets.
4. Update battery, conflicts, and completion status.
5. Collect metrics and repeat until `max_steps` is reached.

Collision handling is integrated into the movement step (robots avoid occupied cells), and repeated blockages increment conflict and hard-block counters.

### Test Scenarios
- **Light Load**: fixed orders, 5 robots, 20x20 grid, 200 steps, 10 orders.
- **Medium Load**: fixed orders, 5 robots, 20x20 grid, 200 steps, 30 orders.
- **Heavy Load**: fixed orders, 5 robots, 20x20 grid, 200 steps, 50 orders.
- **Robot Failure**: fixed orders, 5 robots, 20x20 grid, 200 steps, 30 orders with one robot broken at step 80.
- **Clustered Orders**: fixed orders, 5 robots, 20x20 grid, 200 steps, 30 orders clustered around (10,10) with radius 5.
- **Dynamic Orders**: probabilistic order generation, 5 robots, 20x20 grid, 200 steps, order rate 0.4.
- **Congestion Test**: fixed orders, 20 robots, 8x8 grid, 250 steps, 80 orders clustered around (3,3) with radius 1.
- **Custom (dashboard only)**: adjustable parameters via the UI.

The same scenarios are run across all coordination mechanisms to provide a controlled comparison.

## Key Features
- Multiple coordination strategies with the same environment.
- Configurable order generation (fixed or probabilistic).
- Battery management with recharge state.
- Conflict and hard-block metrics from movement contention.
- CLI experiments with CSV/PNG outputs.
- Web dashboard with live grid, metrics, and exports.

## Project Structure
Core files and directories:
```
.
├─ README.md
├─ requirements.txt
├─ .gitignore
└─ scripts/
   ├─ agents.py
   ├─ model.py
   ├─ run.py
   ├─ requirements.txt
   └─ web/
      ├─ manage.py
      ├─ web/
      │  ├─ settings.py
      │  ├─ urls.py
      │  ├─ asgi.py
      │  └─ wsgi.py
      └─ dashboard/
         ├─ apps.py
         ├─ urls.py
         ├─ views.py
         ├─ state.py
         ├─ templates/
         │  └─ dashboard/
         │     └─ index.html
         └─ static/
            └─ dashboard/
               ├─ app.css
               └─ app.js
```

## Technologies Used
- **Python**
- **Mesa**
- **Django**
- **Pandas**
- **Matplotlib**
- **HTML/CSS/JavaScript**

## Getting Started
Python and `pip` are required on your system.

### Virtual Environment Setup
Windows (PowerShell or CMD):
```powershell
py -m venv .venv
```
Activate (PowerShell):
```powershell
.\.venv\Scripts\Activate.ps1
```
Activate (CMD):
```cmd
.\.venv\Scripts\activate.bat
```
PowerShell execution policy fix (if needed):
```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

Linux/macOS (bash/zsh):
```bash
python -m venv .venv
source .venv/bin/activate
```

### Dependency Installation
```bash
pip install -r requirements.txt
```

## Running the Project
Use the CLI for batch runs or the dashboard for interactive control.

### CLI Simulation
Runs the full scenario suite and exports CSV/PNG outputs.
```powershell
py scripts\run.py
```
```bash
python scripts/run.py
```

### Web Dashboard
Starts a local Django server with the interactive UI.
```powershell
py scripts\web\manage.py runserver
```
```bash
python scripts/web/manage.py runserver
```
Open `http://127.0.0.1:8000/`.

## Outputs & Metrics
- **CLI outputs**:
  - `model_*.csv` and `agent_*.csv` for each scenario/mechanism (saved under `scripts/results/`).
  - `summary_scenarios_mechanisms.csv` (saved under `scripts/results/`).
  - `warehouse_<scenario>.png` charts (saved under `scripts/results/`).
- **Dashboard exports**:
  - Metrics JSON.
  - Model/agent CSVs.
  - Batch and suite summary downloads.

Collected metrics are used to quantitatively compare coordination mechanisms under identical scenarios.

Metrics tracked include throughput, total distance, battery, conflicts, hard blocks, idle time, and completion delay.

## Limitations & Notes
- The simulation stops at `max_steps` even if orders remain.
- Recharge happens in place; robots do not route to charging stations.
- Collision checks only consider other robots, not shelves.
- Results are nondeterministic due to random initialization and scheduling.
- Dashboard state is stored in memory and resets on server restart.

## Authors

- **EL BATTAH Ahmed**

