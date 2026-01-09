"""
Multi-Robot Delivery Coordination System - Mesa Model
Implements warehouse environment with proper Mesa Grid and coordination mechanisms
"""

from mesa import Model
from mesa.space import MultiGrid
from mesa.time import RandomActivation
from mesa.datacollection import DataCollector
from agents import RobotAgent, OrderManagerAgent, ShelfAgent, PackingStationAgent
import random
from typing import List, Tuple, Dict


class WarehouseModel(Model):
    """
    Warehouse model with robots and dynamic order generation
    """
    
    def __init__(
        self,
        num_robots: int = 5,
        grid_width: int = 20,
        grid_height: int = 20,
        coordination_mechanism: str = "cnp",
        order_generation_mode: str = "fixed_orders",
        order_generation_rate: float = 0.3,
        fixed_order_count: int = 10,
        max_steps: int = 200,
        robot_failure_step: int = None,
        clustered_orders: bool = False,
        cluster_center: Tuple[int, int] = None,
        cluster_radius: int = 5
    ):
        super().__init__()
        self.num_robots = num_robots
        self.grid_width = grid_width
        self.grid_height = grid_height
        self.coordination_mechanism = coordination_mechanism
        self.order_generation_mode = order_generation_mode
        self.order_generation_rate = order_generation_rate
        self.fixed_order_count = fixed_order_count
        self.max_steps = max_steps
        self.robot_failure_step = robot_failure_step
        self.clustered_orders = clustered_orders
        self.cluster_center = cluster_center
        self.cluster_radius = cluster_radius
        
        self.schedule = RandomActivation(self)
        self.grid = MultiGrid(grid_width, grid_height, torus=False)
        
        self.orders: List[Dict] = []
        self.completed_orders: List[Dict] = []
        self.order_counter = 0
        self.orders_generated_count = 0
        self.step_count = 0
        
        self.shelf_positions = self.generate_shelf_positions()
        self.station_positions = self.generate_station_positions()
        
        if self.clustered_orders and self.cluster_center is None:
            self.cluster_center = (grid_width // 2, grid_height // 2)
        
        for i, pos in enumerate(self.shelf_positions):
            shelf = ShelfAgent(unique_id=f"shelf_{i}", model=self)
            self.grid.place_agent(shelf, pos)
            self.schedule.add(shelf)
        
        for i, pos in enumerate(self.station_positions):
            station = PackingStationAgent(unique_id=f"station_{i}", model=self)
            self.grid.place_agent(station, pos)
            self.schedule.add(station)
        
        self.manager = OrderManagerAgent(unique_id="manager", model=self)
        self.schedule.add(self.manager)
        
        self.robot_agents = []
        for i in range(num_robots):
            placed = False
            attempts = 0
            while not placed and attempts < 100:
                x = random.randint(0, grid_width - 1)
                y = random.randint(0, grid_height - 1)
                if (x, y) not in self.shelf_positions and (x, y) not in self.station_positions:
                    cell_contents = self.grid.get_cell_list_contents([(x, y)])
                    has_robot = any(isinstance(agent, RobotAgent) for agent in cell_contents)
                    if not has_robot:
                        robot = RobotAgent(unique_id=i, model=self)
                        self.robot_agents.append(robot)
                        self.grid.place_agent(robot, (x, y))
                        self.schedule.add(robot)
                        placed = True
                attempts += 1
        
        self.datacollector = DataCollector(
            model_reporters={
                "Throughput": lambda m: len(m.completed_orders),
                "Active_Orders": lambda m: len([o for o in m.orders if not o.get('completed', False)]),
                "Idle_Robots": lambda m: len([a for a in m.robot_agents if a.state == "idle"]),
                "Broken_Robots": lambda m: len([a for a in m.robot_agents if a.state == "broken"]),
                "Avg_Battery": lambda m: sum([a.battery_level for a in m.robot_agents]) / len(m.robot_agents),
                "Total_Distance": lambda m: sum([a.total_distance_traveled for a in m.robot_agents]),
                "Total_Conflicts": lambda m: sum([a.attempted_conflicts + a.hard_blocks for a in m.robot_agents]),
                "Total_Hard_Blocks": lambda m: sum([a.hard_blocks for a in m.robot_agents]),
            },
            agent_reporters={
                "Battery": lambda a: a.battery_level if isinstance(a, RobotAgent) else None,
                "State": lambda a: a.state if isinstance(a, RobotAgent) else None,
                "Tasks_Completed": lambda a: a.tasks_completed if isinstance(a, RobotAgent) else None,
                "Distance_Traveled": lambda a: a.total_distance_traveled if isinstance(a, RobotAgent) else None,
            }
        )
        
        self.running = True
    
    def generate_shelf_positions(self) -> List[Tuple[int, int]]:
        """Generate shelf positions in grid pattern"""
        shelves = []
        for x in range(2, self.grid_width - 2, 3):
            for y in range(2, self.grid_height - 2, 3):
                shelves.append((x, y))
                if x + 1 < self.grid_width - 2:
                    shelves.append((x + 1, y))
        return shelves
    
    def generate_station_positions(self) -> List[Tuple[int, int]]:
        """Generate packing station positions"""
        stations = [
            (1, 1),
            (self.grid_width - 2, 1),
            (1, self.grid_height - 2),
            (self.grid_width - 2, self.grid_height - 2)
        ]
        return stations
    
    def get_clustered_pickup(self) -> Tuple[int, int]:
        """Get pickup within cluster radius"""
        cx, cy = self.cluster_center
        clustered_shelves = [
            shelf for shelf in self.shelf_positions
            if abs(shelf[0] - cx) <= self.cluster_radius and abs(shelf[1] - cy) <= self.cluster_radius
        ]
        
        if clustered_shelves:
            return random.choice(clustered_shelves)
        else:
            return random.choice(self.shelf_positions)
    
    def generate_random_order(self):
        """Generate order based on generation mode"""
        if self.order_generation_mode == "fixed_orders":
            if self.orders_generated_count >= self.fixed_order_count:
                return
            
            if self.clustered_orders:
                pickup = self.get_clustered_pickup()
            else:
                pickup = random.choice(self.shelf_positions)
            
            delivery = random.choice(self.station_positions)
            self.order_counter += 1
            self.orders_generated_count += 1
            self.manager.generate_order(self.order_counter, pickup, delivery)
            
        elif self.order_generation_mode == "probabilistic":
            if random.random() < self.order_generation_rate:
                if self.clustered_orders:
                    pickup = self.get_clustered_pickup()
                else:
                    pickup = random.choice(self.shelf_positions)
                
                delivery = random.choice(self.station_positions)
                self.order_counter += 1
                self.orders_generated_count += 1
                self.manager.generate_order(self.order_counter, pickup, delivery)
    
    def complete_order(self, order_id: int):
        """Mark order as completed"""
        for order in self.orders:
            if order['id'] == order_id:
                order['completed'] = True
                order['completion_time'] = self.step_count
                self.completed_orders.append(order)
                break
    
    def break_robot(self):
        """Break a random robot"""
        available_robots = [r for r in self.robot_agents if r.state != "broken"]
        if available_robots:
            robot_to_break = random.choice(available_robots)
            robot_to_break.state = "broken"
            robot_to_break.current_task = None
            robot_to_break.target = None
    
    def step(self):
        """Advance model by one step"""
        self.generate_random_order()
        
        if self.robot_failure_step and self.step_count == self.robot_failure_step:
            self.break_robot()
        
        self.datacollector.collect(self)
        
        self.schedule.step()
        
        self.step_count += 1
        
        if self.step_count >= self.max_steps:
            self.running = False
    
    def get_metrics(self) -> Dict:
        """Calculate final performance metrics"""
        total_distance = sum(r.total_distance_traveled for r in self.robot_agents)
        total_tasks = sum(r.tasks_completed for r in self.robot_agents)
        total_idle_time = sum(r.idle_steps for r in self.robot_agents)
        total_attempted_conflicts = sum(r.attempted_conflicts for r in self.robot_agents)
        total_hard_blocks = sum(r.hard_blocks for r in self.robot_agents)
        
        tasks_per_robot = [r.tasks_completed for r in self.robot_agents]
        avg_tasks = sum(tasks_per_robot) / len(tasks_per_robot) if tasks_per_robot else 0
        variance = sum((t - avg_tasks) ** 2 for t in tasks_per_robot) / len(tasks_per_robot) if tasks_per_robot else 0
        
        efficiency = len(self.completed_orders) / total_distance if total_distance > 0 else 0
        
        completion_delays = []
        for order in self.completed_orders:
            delay = order.get('completion_time', 0) - order.get('announce_time', 0)
            completion_delays.append(delay)
        avg_completion_delay = sum(completion_delays) / len(completion_delays) if completion_delays else 0
        
        avg_battery_end = sum([r.battery_level for r in self.robot_agents]) / len(self.robot_agents)
        
        return {
            "total_orders_completed": len(self.completed_orders),
            "total_orders_generated": self.orders_generated_count,
            "throughput": len(self.completed_orders) / self.step_count if self.step_count > 0 else 0,
            "total_distance": total_distance,
            "avg_distance_per_robot": total_distance / len(self.robot_agents),
            "total_idle_time": total_idle_time,
            "avg_idle_time": total_idle_time / len(self.robot_agents),
            "attempted_conflicts": total_attempted_conflicts,
            "hard_blocks": total_hard_blocks,
            "total_conflicts": total_attempted_conflicts + total_hard_blocks,
            "task_fairness_variance": variance,
            "avg_tasks_per_robot": avg_tasks,
            "efficiency": efficiency,
            "avg_completion_delay": avg_completion_delay,
            "avg_battery_end": avg_battery_end,
            "coordination_mechanism": self.coordination_mechanism,
        }
