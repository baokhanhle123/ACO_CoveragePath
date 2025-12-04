"""
Ant Colony Optimization (ACO) for block traversal sequence optimization.

Implements Section 2.4.2 from Zhou et al. 2014:
- ACO parameters: α, β, ρ (rho), q
- Ant construction: probabilistic selection based on pheromone and heuristic
- Pheromone update: evaporation + deposit
- Elitist strategy: extra weight to best solution
"""

from dataclasses import dataclass, field
from typing import List, Optional

import numpy as np

from ..data.block import Block, BlockNode


@dataclass
class ACOParameters:
    """
    ACO algorithm parameters.

    From paper Section 2.4.2:
    - α (alpha): pheromone importance weight (default 1.0)
    - β (beta): heuristic importance weight (default 5.0 in paper)
    - ρ (rho): pheromone evaporation rate (default 0.5 in paper)
    - q: pheromone deposit constant (default 100.0)
    - num_ants: number of ants (suggested: n, where n = num_nodes)
    - num_iterations: number of iterations (paper uses 100)
    - elitist_weight: extra weight for best solution (default 2.0)
    """

    alpha: float = 1.0  # Pheromone importance
    beta: float = 2.0  # Heuristic importance (paper uses 5.0)
    rho: float = 0.1  # Evaporation rate (paper uses 0.5)
    q: float = 100.0  # Pheromone deposit constant
    num_ants: int = 20  # Number of ants per iteration
    num_iterations: int = 100  # Number of iterations
    elitist_weight: float = 2.0  # Extra weight for best solution


@dataclass
class Solution:
    """
    Represents a complete TSP solution (path through all blocks).

    Attributes:
        path: List of node indices in visit order
        cost: Total cost of path
        block_sequence: List of block IDs visited (2 nodes per block)
    """

    path: List[int]
    cost: float
    block_sequence: List[int] = field(default_factory=list)

    def is_valid(self, num_blocks: int) -> bool:
        """
        Check if solution is valid.

        A valid solution must:
        1. Visit all blocks exactly once (entering and exiting)
        2. Each block appears exactly twice in block_sequence (entry + exit)
        3. Path length equals 2 * num_blocks

        Args:
            num_blocks: Expected number of blocks

        Returns:
            True if valid, False otherwise
        """
        if len(self.path) != 2 * num_blocks:
            return False

        if len(self.block_sequence) != 2 * num_blocks:
            return False

        # Check each block appears exactly twice
        from collections import Counter

        block_counts = Counter(self.block_sequence)
        for block_id in range(num_blocks):
            if block_counts.get(block_id, 0) != 2:
                return False

        return True


class Ant:
    """
    Represents an ant that constructs a solution.

    Each ant builds a complete solution by probabilistically selecting
    next nodes based on pheromone trails and heuristic information.
    """

    def __init__(self, nodes: List[BlockNode], blocks: List[Block], cost_matrix: np.ndarray):
        """
        Initialize ant.

        Args:
            nodes: List of all entry/exit nodes
            blocks: List of all blocks
            cost_matrix: Cost matrix for transitions
        """
        self.nodes = nodes
        self.blocks = blocks
        self.cost_matrix = cost_matrix
        self.num_nodes = len(nodes)
        self.num_blocks = len(blocks)

        # Solution state
        self.path: List[int] = []
        self.visited_nodes: set = set()
        self.visited_blocks: set = set()
        self.current_node: Optional[int] = None
        self.total_cost: float = 0.0

    def reset(self):
        """Reset ant to initial state."""
        self.path = []
        self.visited_nodes = set()
        self.visited_blocks = set()
        self.current_node = None
        self.total_cost = 0.0

    def get_available_nodes(self) -> List[int]:
        """
        Get list of available nodes for next move.

        CRITICAL: When we enter a block, we MUST exit it before moving to another block.
        This ensures consecutive entry/exit pairs in the solution.

        A node is available if:
        1. It hasn't been visited yet
        2. Its block hasn't been fully visited (2 nodes per block)
        3. The transition cost from current node is finite
        4. If we just entered a block, we must exit it before visiting other blocks

        Returns:
            List of available node indices
        """
        available = []

        # Check if we just entered a block and need to exit it
        current_block_id = None
        if self.current_node is not None:
            current_node = self.nodes[self.current_node]
            current_block_id = current_node.block_id

            # Count how many times we've visited current block
            current_block_visits = sum(
                1 for n_idx in self.path if self.nodes[n_idx].block_id == current_block_id
            )

            # If we've visited current block once, we MUST exit it next (complete the pair)
            if current_block_visits == 1:
                # Only allow nodes from the same block that form valid exit
                for node_idx in range(self.num_nodes):
                    if node_idx in self.visited_nodes:
                        continue

                    node = self.nodes[node_idx]
                    if node.block_id != current_block_id:
                        continue

                    # Check if transition is valid
                    cost = self.cost_matrix[self.current_node][node_idx]
                    if cost >= 1e9:
                        continue

                    available.append(node_idx)

                return available

        # Normal case: can visit any unvisited block
        for node_idx in range(self.num_nodes):
            # Skip visited nodes
            if node_idx in self.visited_nodes:
                continue

            node = self.nodes[node_idx]

            # Skip if block already fully visited (2 nodes per block means block done)
            block_visits = sum(1 for n_idx in self.path if self.nodes[n_idx].block_id == node.block_id)
            if block_visits >= 2:
                continue

            # If we have a current node, check transition cost
            if self.current_node is not None:
                cost = self.cost_matrix[self.current_node][node_idx]
                if cost >= 1e9:  # Invalid transition
                    continue

            available.append(node_idx)

        return available

    def move_to(self, node_idx: int):
        """
        Move ant to specified node.

        Args:
            node_idx: Index of node to move to
        """
        # Add to path
        self.path.append(node_idx)
        self.visited_nodes.add(node_idx)

        # Update visited blocks
        node = self.nodes[node_idx]
        self.visited_blocks.add(node.block_id)

        # Update cost
        if self.current_node is not None:
            self.total_cost += self.cost_matrix[self.current_node][node_idx]

        self.current_node = node_idx

    def select_next_node(
        self, available: List[int], pheromone: np.ndarray, heuristic: np.ndarray, alpha: float, beta: float
    ) -> int:
        """
        Select next node probabilistically based on pheromone and heuristic.

        Implements ACO probability formula from Section 2.4.2:
        p_ij = (τ_ij^α * η_ij^β) / Σ(τ_ik^α * η_ik^β)

        where:
        - τ_ij (tau) = pheromone on edge i->j
        - η_ij (eta) = heuristic value (1/cost) for edge i->j
        - α (alpha) = pheromone importance
        - β (beta) = heuristic importance

        Args:
            available: List of available node indices
            pheromone: Pheromone matrix
            heuristic: Heuristic matrix
            alpha: Pheromone importance weight
            beta: Heuristic importance weight

        Returns:
            Selected node index
        """
        if not available:
            raise ValueError("No available nodes to select")

        # If first move, select randomly
        if self.current_node is None:
            return np.random.choice(available)

        # Calculate probabilities
        probabilities = []
        for node_idx in available:
            tau = pheromone[self.current_node][node_idx]
            eta = heuristic[self.current_node][node_idx]
            prob = (tau ** alpha) * (eta ** beta)
            probabilities.append(prob)

        # Normalize probabilities
        total = sum(probabilities)
        if total == 0:
            # All probabilities are zero, select randomly
            return np.random.choice(available)

        probabilities = [p / total for p in probabilities]

        # Select node
        selected = np.random.choice(available, p=probabilities)
        return selected

    def construct_solution(
        self, pheromone: np.ndarray, heuristic: np.ndarray, alpha: float, beta: float
    ) -> Solution:
        """
        Construct complete solution by visiting all blocks.

        Each ant builds a solution by:
        1. Starting at a random node
        2. Repeatedly selecting next node based on pheromone and heuristic
        3. Stopping when all blocks have been visited (2 nodes per block)

        Args:
            pheromone: Pheromone matrix
            heuristic: Heuristic matrix
            alpha: Pheromone importance
            beta: Heuristic importance

        Returns:
            Complete solution with path and cost
        """
        self.reset()

        # Build solution by visiting 2 nodes per block
        max_steps = 2 * self.num_blocks

        for _ in range(max_steps):
            available = self.get_available_nodes()

            if not available:
                # No more available nodes (solution complete or stuck)
                break

            # Select next node
            next_node = self.select_next_node(available, pheromone, heuristic, alpha, beta)

            # Move to selected node
            self.move_to(next_node)

        # Build block sequence
        block_sequence = [self.nodes[node_idx].block_id for node_idx in self.path]

        return Solution(path=self.path.copy(), cost=self.total_cost, block_sequence=block_sequence)


class ACOSolver:
    """
    Ant Colony Optimization solver for block sequencing problem.

    Implements the ACO algorithm from Section 2.4.2:
    1. Initialize pheromone trails
    2. For each iteration:
        a. Each ant constructs a solution
        b. Evaporate pheromone
        c. Deposit pheromone on edges used by ants
        d. Apply elitist strategy (extra deposit on best solution)
    3. Return best solution found
    """

    def __init__(
        self,
        blocks: List[Block],
        nodes: List[BlockNode],
        cost_matrix: np.ndarray,
        params: Optional[ACOParameters] = None,
    ):
        """
        Initialize ACO solver.

        Args:
            blocks: List of blocks
            nodes: List of entry/exit nodes
            cost_matrix: Cost matrix for transitions
            params: ACO parameters (uses defaults if None)
        """
        self.blocks = blocks
        self.nodes = nodes
        self.cost_matrix = cost_matrix
        self.params = params or ACOParameters()

        self.num_blocks = len(blocks)
        self.num_nodes = len(nodes)

        # Initialize pheromone matrix (uniform)
        self.pheromone = np.ones((self.num_nodes, self.num_nodes))

        # Calculate heuristic matrix (inverse of cost)
        self.heuristic = np.zeros((self.num_nodes, self.num_nodes))
        for i in range(self.num_nodes):
            for j in range(self.num_nodes):
                if self.cost_matrix[i][j] > 0 and self.cost_matrix[i][j] < 1e9:
                    self.heuristic[i][j] = 1.0 / self.cost_matrix[i][j]

        # Best solution tracking
        self.best_solution: Optional[Solution] = None
        self.iteration_best_costs: List[float] = []
        self.iteration_avg_costs: List[float] = []

    def _evaporate_pheromone(self):
        """
        Evaporate pheromone on all edges.

        Implements: τ_ij = (1 - ρ) * τ_ij
        """
        self.pheromone *= (1 - self.params.rho)

    def _deposit_pheromone(self, solution: Solution):
        """
        Deposit pheromone on edges used in solution.

        Implements: Δτ_ij = q / cost
        where q is pheromone deposit constant

        Args:
            solution: Solution to deposit pheromone for
        """
        if solution.cost == 0:
            return

        deposit = self.params.q / solution.cost

        for i in range(len(solution.path) - 1):
            node_from = solution.path[i]
            node_to = solution.path[i + 1]
            self.pheromone[node_from][node_to] += deposit
            self.pheromone[node_to][node_from] += deposit  # Symmetric

    def _update_best_solution(self, solution: Solution):
        """
        Update best solution if new solution is better.

        Args:
            solution: Candidate solution
        """
        if solution.is_valid(self.num_blocks):
            if self.best_solution is None or solution.cost < self.best_solution.cost:
                self.best_solution = solution

    def solve(self, verbose: bool = True) -> Optional[Solution]:
        """
        Run ACO algorithm to find optimal block traversal sequence.

        Algorithm from Section 2.4.2:
        1. For each iteration:
            a. Each ant constructs a solution
            b. Track best solution
            c. Evaporate pheromone
            d. Deposit pheromone (all ants + elitist)
        2. Return best solution

        Args:
            verbose: Print progress information

        Returns:
            Best solution found, or None if no valid solution found
        """
        if verbose:
            print(f"Running ACO with {self.params.num_ants} ants for {self.params.num_iterations} iterations...")

        for iteration in range(self.params.num_iterations):
            # Create ants
            ants = [Ant(self.nodes, self.blocks, self.cost_matrix) for _ in range(self.params.num_ants)]

            # Each ant constructs a solution
            solutions = []
            for ant in ants:
                solution = ant.construct_solution(
                    self.pheromone, self.heuristic, self.params.alpha, self.params.beta
                )
                solutions.append(solution)

                # Update best solution
                self._update_best_solution(solution)

            # Track iteration statistics
            valid_solutions = [s for s in solutions if s.is_valid(self.num_blocks)]
            if valid_solutions:
                avg_cost = np.mean([s.cost for s in valid_solutions])
                best_cost = min(s.cost for s in valid_solutions)
                self.iteration_avg_costs.append(avg_cost)
            else:
                # No valid solutions this iteration
                if self.best_solution:
                    best_cost = self.best_solution.cost
                else:
                    best_cost = float('inf')

            if self.best_solution:
                self.iteration_best_costs.append(self.best_solution.cost)
            else:
                self.iteration_best_costs.append(float('inf'))

            # Evaporate pheromone
            self._evaporate_pheromone()

            # Deposit pheromone for all valid solutions
            for solution in valid_solutions:
                self._deposit_pheromone(solution)

            # Elitist strategy: extra pheromone for best solution
            if self.best_solution:
                for _ in range(int(self.params.elitist_weight)):
                    self._deposit_pheromone(self.best_solution)

            # Print progress
            if verbose and (iteration + 1) % 10 == 0:
                print(
                    f"  Iteration {iteration + 1}/{self.params.num_iterations}: "
                    f"Best cost = {best_cost:.2f}, "
                    f"Valid solutions = {len(valid_solutions)}/{self.params.num_ants}"
                )

        if verbose:
            if self.best_solution:
                print(f"\nACO completed. Best cost: {self.best_solution.cost:.2f}")
            else:
                print("\nACO completed. No valid solution found!")

        return self.best_solution

    def get_convergence_data(self) -> tuple[List[float], List[float]]:
        """
        Get convergence data for visualization.

        Returns:
            Tuple of (best_costs, avg_costs) for each iteration
        """
        return self.iteration_best_costs, self.iteration_avg_costs
