"""
Multi-Robot Delivery Coordination System - Agent Definitions
Implements RobotAgent, OrderManagerAgent, and warehouse objects with proper Mesa Grid integration
"""

from mesa import Agent
import math
import random
from typing import Optional, Dict, Tuple, List


class ShelfAgent(Agent):
    """Shelf in the warehouse where items are stored"""
    
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
    
    def step(self):
        pass


class PackingStationAgent(Agent):
    """Packing station where orders are delivered"""
    
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
    
    def step(self):
        pass


class RobotAgent(Agent):
    """
    Autonomous robot agent that picks up and delivers orders in a warehouse
    
    Attributes:
        pos: (x, y) coordinates on the grid
        battery_level: Current battery charge (0-100)
        current_task: The order currently being executed
        state: Current state (idle, moving_to_pickup, moving_to_delivery, recharging, broken)
    """
    
    def __init__(self, unique_id, model, battery_capacity=100, carrying_capacity=1):
        super().__init__(unique_id, model)
        self.battery_level = battery_capacity
        self.battery_capacity = battery_capacity
        self.carrying_capacity = carrying_capacity
        self.current_task = None
        self.state = "idle"
        self.target = None
        
        # Performance tracking
        self.total_distance_traveled = 0
        self.tasks_completed = 0
        self.idle_steps = 0
        
        self.attempted_conflicts = 0  # Times tried to move to occupied cell
        self.hard_blocks = 0  # Times completely blocked (no alternative)
        
        # Intelligent path planning state
        self.blocked_count = 0
    
    def calculate_distance(self, target_pos: Tuple[int, int]) -> float:
        """Calculate Manhattan distance to target position"""
        return abs(self.pos[0] - target_pos[0]) + abs(self.pos[1] - target_pos[1])
    
    def calculate_bid(self, order: Dict) -> float:
        """
        Calculate bid value for an order based on distance and battery
        Lower bid = better (wants the task more)
        """
        pickup_pos = order['pickup']
        delivery_pos = order['delivery']
        
        distance_to_pickup = self.calculate_distance(pickup_pos)
        delivery_distance = abs(pickup_pos[0] - delivery_pos[0]) + abs(pickup_pos[1] - delivery_pos[1])
        total_distance = distance_to_pickup + delivery_distance
        
        battery_factor = 1.0 if self.battery_level > 30 else 2.0
        state_penalty = 0 if self.state == "idle" else 5
        
        bid_value = total_distance * battery_factor + state_penalty
        return bid_value
    
    def compute_centralized_cost(self, order: Dict, alpha=0.1, beta=1.0) -> float:
        """
        Compute assignment cost for centralized mechanism
        cost = distance(robot→pickup) + distance(pickup→delivery) 
               + α * (1 - battery/100) 
               + β * (queue_penalty)
        Lower cost = better assignment
        """
        pickup_pos = order['pickup']
        delivery_pos = order['delivery']
        
        dist_to_pickup = self.calculate_distance(pickup_pos)
        dist_pickup_to_delivery = abs(pickup_pos[0] - delivery_pos[0]) + abs(pickup_pos[1] - delivery_pos[1])
        total_distance = dist_to_pickup + dist_pickup_to_delivery
        
        battery_cost = alpha * (1.0 - self.battery_level / 100.0)
        queue_penalty = beta * (1.0 if self.state != "idle" else 0.0)
        
        cost = total_distance + battery_cost + queue_penalty
        return cost
    
    def assign_task(self, order: Dict):
        """Assign an order to this robot"""
        self.current_task = order
        self.state = "moving_to_pickup"
        self.target = order['pickup']
    
    def move_towards(self, target: Tuple[int, int]):
        """Move one step towards target with intelligent collision avoidance"""
        if self.pos == target:
            return
        
        x, y = self.pos
        tx, ty = target
        
        possible_moves = self.get_smart_moves(target)
        
        next_pos = None
        for candidate in possible_moves:
            if self.is_position_free(candidate):
                next_pos = candidate
                self.blocked_count = 0
                break
        
        if next_pos is None:
            self.attempted_conflicts += 1
            self.blocked_count += 1
            
            if self.blocked_count >= 3:
                next_pos = self.try_sidestep()
                if next_pos:
                    self.blocked_count = 0
                else:
                    self.hard_blocks += 1
        
        if next_pos:
            self.model.grid.move_agent(self, next_pos)
            self.total_distance_traveled += 1
            self.battery_level = max(0, self.battery_level - 0.5)
    
    def get_smart_moves(self, target: Tuple[int, int]) -> List[Tuple[int, int]]:
        """
        Get list of possible moves sorted by distance to target
        Only 4-neighborhood (cardinal directions)
        """
        x, y = self.pos
        tx, ty = target
        
        neighbors = [
            (x + 1, y),
            (x - 1, y),
            (x, y + 1),
            (x, y - 1),
        ]
        
        valid_neighbors = [
            pos for pos in neighbors 
            if not self.model.grid.out_of_bounds(pos)
        ]
        
        valid_neighbors.sort(key=lambda pos: abs(pos[0] - tx) + abs(pos[1] - ty))
        
        return valid_neighbors
    
    def try_sidestep(self) -> Optional[Tuple[int, int]]:
        """Random side-step to escape congestion"""
        x, y = self.pos
        
        sidesteps = [
            (x + 1, y),
            (x - 1, y),
            (x, y + 1),
            (x, y - 1),
        ]
        
        random.shuffle(sidesteps)
        
        for pos in sidesteps:
            if not self.model.grid.out_of_bounds(pos) and self.is_position_free(pos):
                return pos
        
        return None
    
    def is_position_free(self, pos: Tuple[int, int]) -> bool:
        """Check if position is free of other robots"""
        if not self.model.grid.out_of_bounds(pos):
            cell_contents = self.model.grid.get_cell_list_contents([pos])
            for agent in cell_contents:
                if isinstance(agent, RobotAgent) and agent != self:
                    return False
            return True
        return False
    
    def step(self):
        """Execute one step of robot behavior"""
        if self.state == "broken":
            return
        
        if self.battery_level < 20 and self.state != "recharging":
            self.state = "recharging"
            self.current_task = None
            self.target = None
        
        if self.state == "recharging":
            self.battery_level = min(self.battery_capacity, self.battery_level + 5)
            if self.battery_level >= 80:
                self.state = "idle"
                if self.model.coordination_mechanism == "greedy":
                    self.greedy_task_selection()
            return
        
        if self.state == "idle":
            self.idle_steps += 1
            if self.model.coordination_mechanism == "greedy":
                self.greedy_task_selection()
            return
        
        if self.state == "moving_to_pickup":
            self.move_towards(self.target)
            if self.pos == self.target:
                self.state = "moving_to_delivery"
                self.target = self.current_task['delivery']
        
        elif self.state == "moving_to_delivery":
            self.move_towards(self.target)
            if self.pos == self.target:
                self.tasks_completed += 1
                self.model.complete_order(self.current_task['id'])
                self.current_task = None
                self.target = None
                self.state = "idle"
    
    def greedy_task_selection(self):
        """Greedy strategy: grab nearest unassigned order"""
        unassigned = [o for o in self.model.orders if not o.get('assigned', False) and not o.get('completed', False)]
        
        if unassigned:
            nearest = min(unassigned, key=lambda o: self.calculate_distance(o['pickup']))
            nearest['assigned'] = True
            self.assign_task(nearest)


class OrderManagerAgent(Agent):
    """
    Manager agent that generates orders and coordinates task allocation
    Implements CNP, Greedy, and Centralized mechanisms
    """
    
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.pending_orders = []
        self.announced_orders = []
    
    def generate_order(self, order_id: int, pickup: Tuple[int, int], delivery: Tuple[int, int]):
        """Generate a new order"""
        order = {
            'id': order_id,
            'pickup': pickup,
            'delivery': delivery,
            'assigned': False,
            'completed': False,
            'announce_time': self.model.step_count
        }
        self.pending_orders.append(order)
        self.model.orders.append(order)
    
    def announce_tasks_cnp(self):
        """Contract Net Protocol: Announce and bid"""
        unassigned = [o for o in self.model.orders if not o.get('assigned', False) and not o.get('completed', False)]
        
        for order in unassigned:
            bids = []
            robots = [a for a in self.model.schedule.agents if isinstance(a, RobotAgent)]
            for robot in robots:
                if robot.state == "idle" and robot.battery_level > 30:
                    bid_value = robot.calculate_bid(order)
                    bids.append({'robot': robot, 'bid': bid_value})
            
            if bids:
                winner = min(bids, key=lambda b: b['bid'])
                winner['robot'].assign_task(order)
                order['assigned'] = True
    
    def announce_tasks_centralized(self):
        """
        Centralized mechanism: Manager assigns each order to robot minimizing cost
        """
        unassigned = [o for o in self.model.orders if not o.get('assigned', False) and not o.get('completed', False)]
        
        for order in unassigned:
            robots = [a for a in self.model.schedule.agents if isinstance(a, RobotAgent)]
            costs = []
            
            for robot in robots:
                if robot.state == "idle" and robot.battery_level > 20:
                    cost = robot.compute_centralized_cost(order)
                    costs.append({'robot': robot, 'cost': cost})
            
            if costs:
                best = min(costs, key=lambda c: c['cost'])
                best['robot'].assign_task(order)
                order['assigned'] = True
    
    def step(self):
        """Execute manager behavior based on mechanism"""
        if self.model.coordination_mechanism == "cnp":
            if self.model.step_count % 2 == 0:
                self.announce_tasks_cnp()
        
        elif self.model.coordination_mechanism == "centralized":
            if self.model.step_count % 2 == 0:
                self.announce_tasks_centralized()
