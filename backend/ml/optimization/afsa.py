"""
Artificial Fish Swarm Algorithm (AFSA) for traffic signal timing optimization.
This algorithm optimizes traffic signal timings based on current and predicted traffic conditions.
"""

import numpy as np
import random
from typing import List, Tuple, Dict, Callable


class ArtificialFishSwarmAlgorithm:
    """
    Implementation of Artificial Fish Swarm Algorithm for traffic signal optimization.
    """
    
    def __init__(self, 
                 num_fish: int = 50,
                 max_iterations: int = 100,
                 visual_range: float = 5.0,
                 crowd_factor: float = 0.618,
                 step_size: float = 0.5,
                 try_number: int = 10):
        """
        Initialize AFSA parameters.
        
        Args:
            num_fish: Number of artificial fish in the swarm
            max_iterations: Maximum number of iterations
            visual_range: Visual range of artificial fish
            crowd_factor: Crowding factor (0-1)
            step_size: Maximum step size
            try_number: Maximum number of tries in prey behavior
        """
        self.num_fish = num_fish
        self.max_iterations = max_iterations
        self.visual_range = visual_range
        self.crowd_factor = crowd_factor
        self.step_size = step_size
        self.try_number = try_number
        self.best_solution = None
        self.best_fitness = float('-inf')
        
    def initialize_population(self, 
                              dimensions: int, 
                              lower_bounds: List[float], 
                              upper_bounds: List[float]) -> np.ndarray:
        """
        Initialize fish population within bounds.
        
        Args:
            dimensions: Number of dimensions (signal phases)
            lower_bounds: Lower bounds for each dimension
            upper_bounds: Upper bounds for each dimension
            
        Returns:
            Initial population of artificial fish
        """
        population = np.zeros((self.num_fish, dimensions))
        
        for i in range(self.num_fish):
            for j in range(dimensions):
                population[i, j] = random.uniform(lower_bounds[j], upper_bounds[j])
                
        return population
    
    def prey_behavior(self, 
                      current_fish: np.ndarray, 
                      population: np.ndarray, 
                      fitness_function: Callable, 
                      lower_bounds: List[float], 
                      upper_bounds: List[float]) -> np.ndarray:
        """
        Implement prey behavior of artificial fish.
        
        Args:
            current_fish: Current fish position
            population: Current population
            fitness_function: Function to evaluate fitness
            lower_bounds: Lower bounds for each dimension
            upper_bounds: Upper bounds for each dimension
            
        Returns:
            New position after prey behavior
        """
        current_fitness = fitness_function(current_fish)
        
        for _ in range(self.try_number):
            # Generate random direction within visual range
            dimensions = len(current_fish)
            random_direction = np.random.uniform(-1, 1, dimensions)
            random_direction = random_direction / np.linalg.norm(random_direction)
            
            # Calculate new position
            new_position = current_fish + self.visual_range * random_direction
            
            # Ensure new position is within bounds
            for j in range(dimensions):
                new_position[j] = max(lower_bounds[j], min(upper_bounds[j], new_position[j]))
            
            # Evaluate new position
            new_fitness = fitness_function(new_position)
            
            # Move if better position found
            if new_fitness > current_fitness:
                return new_position
        
        # Return original position if no better position found
        return current_fish
    
    def swarm_behavior(self, 
                       current_fish: np.ndarray, 
                       population: np.ndarray, 
                       fitness_function: Callable, 
                       lower_bounds: List[float], 
                       upper_bounds: List[float]) -> np.ndarray:
        """
        Implement swarm behavior of artificial fish.
        
        Args:
            current_fish: Current fish position
            population: Current population
            fitness_function: Function to evaluate fitness
            lower_bounds: Lower bounds for each dimension
            upper_bounds: Upper bounds for each dimension
            
        Returns:
            New position after swarm behavior
        """
        dimensions = len(current_fish)
        current_fitness = fitness_function(current_fish)
        
        # Find neighbors within visual range
        neighbors = []
        for fish in population:
            distance = np.linalg.norm(fish - current_fish)
            if 0 < distance < self.visual_range:
                neighbors.append(fish)
        
        # If no neighbors, return original position
        if not neighbors:
            return current_fish
        
        # Calculate center of neighbors
        center = np.zeros(dimensions)
        for neighbor in neighbors:
            center += neighbor
        center /= len(neighbors)
        
        # Check if center is too crowded
        if len(neighbors) / self.num_fish > self.crowd_factor:
            return self.prey_behavior(current_fish, population, fitness_function, lower_bounds, upper_bounds)
        
        # Evaluate center position
        center_fitness = fitness_function(center)
        
        # Move towards center if it's better
        if center_fitness > current_fitness:
            direction = center - current_fish
            if np.linalg.norm(direction) > 0:
                direction = direction / np.linalg.norm(direction)
            
            new_position = current_fish + self.step_size * direction
            
            # Ensure new position is within bounds
            for j in range(dimensions):
                new_position[j] = max(lower_bounds[j], min(upper_bounds[j], new_position[j]))
            
            return new_position
        
        # If center is not better, try prey behavior
        return self.prey_behavior(current_fish, population, fitness_function, lower_bounds, upper_bounds)
    
    def follow_behavior(self, 
                        current_fish: np.ndarray, 
                        population: np.ndarray, 
                        fitness_function: Callable, 
                        lower_bounds: List[float], 
                        upper_bounds: List[float]) -> np.ndarray:
        """
        Implement follow behavior of artificial fish.
        
        Args:
            current_fish: Current fish position
            population: Current population
            fitness_function: Function to evaluate fitness
            lower_bounds: Lower bounds for each dimension
            upper_bounds: Upper bounds for each dimension
            
        Returns:
            New position after follow behavior
        """
        dimensions = len(current_fish)
        current_fitness = fitness_function(current_fish)
        
        # Find best neighbor within visual range
        best_neighbor = None
        best_neighbor_fitness = float('-inf')
        
        for fish in population:
            distance = np.linalg.norm(fish - current_fish)
            if 0 < distance < self.visual_range:
                fish_fitness = fitness_function(fish)
                if fish_fitness > best_neighbor_fitness:
                    best_neighbor = fish
                    best_neighbor_fitness = fish_fitness
        
        # If no better neighbor found, try prey behavior
        if best_neighbor is None or best_neighbor_fitness <= current_fitness:
            return self.prey_behavior(current_fish, population, fitness_function, lower_bounds, upper_bounds)
        
        # Check if best neighbor area is too crowded
        neighbors_count = 0
        for fish in population:
            distance = np.linalg.norm(fish - best_neighbor)
            if distance < self.visual_range:
                neighbors_count += 1
        
        if neighbors_count / self.num_fish > self.crowd_factor:
            return self.prey_behavior(current_fish, population, fitness_function, lower_bounds, upper_bounds)
        
        # Move towards best neighbor
        direction = best_neighbor - current_fish
        if np.linalg.norm(direction) > 0:
            direction = direction / np.linalg.norm(direction)
        
        new_position = current_fish + self.step_size * direction
        
        # Ensure new position is within bounds
        for j in range(dimensions):
            new_position[j] = max(lower_bounds[j], min(upper_bounds[j], new_position[j]))
        
        return new_position
    
    def optimize(self, 
                fitness_function: Callable, 
                dimensions: int, 
                lower_bounds: List[float], 
                upper_bounds: List[float]) -> Tuple[np.ndarray, float]:
        """
        Run the AFSA optimization algorithm.
        
        Args:
            fitness_function: Function to evaluate fitness
            dimensions: Number of dimensions (signal phases)
            lower_bounds: Lower bounds for each dimension
            upper_bounds: Upper bounds for each dimension
            
        Returns:
            Tuple of (best solution, best fitness)
        """
        # Initialize population
        population = self.initialize_population(dimensions, lower_bounds, upper_bounds)
        
        # Evaluate initial population
        fitness_values = np.array([fitness_function(fish) for fish in population])
        best_index = np.argmax(fitness_values)
        self.best_solution = population[best_index].copy()
        self.best_fitness = fitness_values[best_index]
        
        # Main optimization loop
        for iteration in range(self.max_iterations):
            new_population = np.zeros_like(population)
            
            for i in range(self.num_fish):
                current_fish = population[i].copy()
                
                # Randomly choose behavior
                behavior = random.choice(['prey', 'swarm', 'follow'])
                
                if behavior == 'prey':
                    new_position = self.prey_behavior(current_fish, population, fitness_function, lower_bounds, upper_bounds)
                elif behavior == 'swarm':
                    new_position = self.swarm_behavior(current_fish, population, fitness_function, lower_bounds, upper_bounds)
                else:  # follow
                    new_position = self.follow_behavior(current_fish, population, fitness_function, lower_bounds, upper_bounds)
                
                new_population[i] = new_position
                
                # Update best solution if needed
                new_fitness = fitness_function(new_position)
                if new_fitness > self.best_fitness:
                    self.best_solution = new_position.copy()
                    self.best_fitness = new_fitness
            
            # Update population
            population = new_population.copy()
            
            # Optional: Print progress
            if (iteration + 1) % 10 == 0:
                print(f"Iteration {iteration + 1}/{self.max_iterations}, Best Fitness: {self.best_fitness}")
        
        return self.best_solution, self.best_fitness


class TrafficSignalOptimizer:
    """
    Traffic signal timing optimizer using AFSA.
    """
    
    def __init__(self, 
                 num_phases: int,
                 min_green_time: float = 10.0,
                 max_green_time: float = 120.0,
                 cycle_time_constraint: float = 180.0):
        """
        Initialize traffic signal optimizer.
        
        Args:
            num_phases: Number of signal phases
            min_green_time: Minimum green time for each phase (seconds)
            max_green_time: Maximum green time for each phase (seconds)
            cycle_time_constraint: Maximum total cycle time (seconds)
        """
        self.num_phases = num_phases
        self.min_green_time = min_green_time
        self.max_green_time = max_green_time
        self.cycle_time_constraint = cycle_time_constraint
        self.afsa = ArtificialFishSwarmAlgorithm()
        
    def fitness_function(self, 
                         solution: np.ndarray, 
                         traffic_volumes: List[float], 
                         queue_lengths: List[float],
                         waiting_times: List[float],
                         emergency_priority: List[float] = None) -> float:
        """
        Fitness function for evaluating signal timing solutions.
        
        Args:
            solution: Signal timing solution (green times for each phase)
            traffic_volumes: Traffic volume for each phase
            queue_lengths: Queue length for each phase
            waiting_times: Average waiting time for each phase
            emergency_priority: Emergency vehicle priority for each phase (optional)
            
        Returns:
            Fitness value (higher is better)
        """
        # Check cycle time constraint
        total_cycle_time = np.sum(solution)
        if total_cycle_time > self.cycle_time_constraint:
            return float('-inf')  # Invalid solution
        
        # Calculate throughput (vehicles served per cycle)
        throughput = np.sum([solution[i] * traffic_volumes[i] for i in range(self.num_phases)])
        
        # Calculate queue reduction
        queue_reduction = np.sum([solution[i] * queue_lengths[i] for i in range(self.num_phases)])
        
        # Calculate waiting time reduction
        waiting_time_reduction = np.sum([solution[i] / waiting_times[i] for i in range(self.num_phases)])
        
        # Calculate emergency priority if provided
        emergency_score = 0
        if emergency_priority is not None:
            emergency_score = np.sum([solution[i] * emergency_priority[i] for i in range(self.num_phases)])
        
        # Combine objectives with weights
        fitness = (
            0.4 * throughput + 
            0.3 * queue_reduction + 
            0.2 * waiting_time_reduction + 
            0.1 * emergency_score
        )
        
        return fitness
    
    def optimize_signal_timings(self, 
                               traffic_volumes: List[float], 
                               queue_lengths: List[float],
                               waiting_times: List[float],
                               emergency_priority: List[float] = None) -> Dict:
        """
        Optimize signal timings based on current traffic conditions.
        
        Args:
            traffic_volumes: Traffic volume for each phase
            queue_lengths: Queue length for each phase
            waiting_times: Average waiting time for each phase
            emergency_priority: Emergency vehicle priority for each phase (optional)
            
        Returns:
            Dictionary with optimized signal timings and metrics
        """
        # Define bounds
        lower_bounds = [self.min_green_time] * self.num_phases
        upper_bounds = [self.max_green_time] * self.num_phases
        
        # Create fitness function with current traffic conditions
        def fitness(solution):
            return self.fitness_function(solution, traffic_volumes, queue_lengths, waiting_times, emergency_priority)
        
        # Run optimization
        best_solution, best_fitness = self.afsa.optimize(
            fitness_function=fitness,
            dimensions=self.num_phases,
            lower_bounds=lower_bounds,
            upper_bounds=upper_bounds
        )
        
        # Calculate metrics for the best solution
        total_cycle_time = np.sum(best_solution)
        phase_proportions = best_solution / total_cycle_time
        
        return {
            'green_times': best_solution.tolist(),
            'cycle_time': total_cycle_time,
            'phase_proportions': phase_proportions.tolist(),
            'fitness': best_fitness
        }