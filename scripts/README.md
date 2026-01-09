# Multi-Robot Delivery Coordination System

## Project Overview

This project implements a Multi-Agent System (MAS) simulation for warehouse robot coordination using the Mesa framework. The simulation compares two coordination mechanisms: **Contract Net Protocol (CNP)** and **Greedy/Emergent Strategy**.

## System Architecture

### Agent Types

1. **RobotAgent**
   - Autonomous robots that pick up packages from shelves and deliver to packing stations
   - Attributes: position, battery level, carrying capacity, current task, state
   - Behaviors: bidding for tasks, pathfinding, collision avoidance, battery management

2. **OrderManagerAgent**
   - Manages order generation and task allocation
   - Implements Contract Net Protocol for CNP mode
   - Tracks performance metrics

### Coordination Mechanisms

#### 1. Contract Net Protocol (CNP)
- Manager announces available orders
- Robots submit bids based on distance and battery level
- Manager selects the best robot (lowest bid = closest/most capable)
- Provides better task allocation and fairness

#### 2. Greedy/Emergent Strategy
- Each robot independently selects the nearest unassigned order
- No explicit coordination or communication
- Simpler but potentially less efficient

### Environment

- 10×10 grid warehouse layout
- Shelves positioned in a grid pattern with aisles
- Packing stations at the four corners
- 5 robots with battery management
- Dynamic order generation

## Installation

```bash
pip install -r requirements.txt
```

## Running the Simulation

```bash
python run.py
```

This will:
1. Run both CNP and Greedy mechanisms
2. Compare performance metrics
3. Generate visualizations
4. Save results to `/tmp/warehouse_comparison.png`

## Web Interface (Django)

```bash
python web/manage.py runserver
```

Then open http://127.0.0.1:8000/ in your browser.

## Performance Metrics

- **Throughput**: Orders completed per time step
- **Efficiency**: Total distance traveled, battery usage
- **Fairness**: Variance in task distribution across robots
- **Idle Time**: Time robots spend waiting for tasks
- **Collision Avoidances**: Number of collision prevention maneuvers

## Design Decisions

### Why Contract Net Protocol?
- Well-established coordination mechanism from MAS literature
- Balances efficiency (task allocation) with fairness
- Allows robots to bid based on multiple factors (distance, battery, state)

### Why Greedy Strategy?
- Represents emergent coordination without explicit communication
- Useful baseline for comparison
- Demonstrates reactive agent behavior

### Battery Management
- Robots recharge when battery drops below 20%
- Prevents robots from becoming stranded
- Adds realistic constraint to task allocation

### Collision Avoidance
- Simple cell-based collision detection
- Robots wait if target cell is occupied
- Tracks collision avoidances as a metric

## Expected Results

**Contract Net Protocol** typically shows:
- Better task fairness (lower variance)
- More efficient distance usage
- Slightly lower throughput initially (due to bidding overhead)

**Greedy Strategy** typically shows:
- Faster initial response
- Higher collision avoidances
- Less fair task distribution
- Potentially higher total distance

## Customization

Modify parameters in `run.py`:

```python
compare_mechanisms(
    num_robots=5,        # Number of robots
    order_rate=0.3,      # Order generation rate (0-1)
    max_steps=200        # Simulation duration
)
```

## Project Structure

```
scripts/
├── agents.py        # Agent definitions (RobotAgent, OrderManagerAgent)
├── model.py         # Mesa model (WarehouseModel)
├── run.py           # Simulation runner and analysis
├── requirements.txt # Python dependencies
└── README.md        # This file
```

Web project lives in `web/` (Django UI + API).

## Course Context

This project fulfills the requirements for the Multi-Agent Systems course (Master IPS – M2):
- ✅ Implements 2 coordination mechanisms (CNP and Greedy)
- ✅ Uses Mesa framework
- ✅ Collects and analyzes performance metrics
- ✅ Compares different approaches with visualizations
- ✅ Clean, commented code with proper documentation

## Author

Academic Year 2025–2026  
Mohamed V University, Rabat
