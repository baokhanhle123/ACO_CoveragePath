"""
Ant Colony Optimization (ACO) for TSP-based block sequencing.

Implements the ACO algorithm from Zhou et al. 2014 (Section 2.4)
for finding optimal order to visit all blocks in the field.
"""

import random
from dataclasses import dataclass, field
from typing import List, Optional, Set, Tuple

import numpy as np

from ..data.block import Block, BlockNode


@dataclass
class ACOParameters:
    """
    ACO algorithm parameters from Zhou et al. 2014.

    Attributes:
        alpha: Pheromone importance weight (default: 1.0)
        beta: Heuristic importance weight (default: 2.0)
        rho: Pheromone evaporation rate (default: 0.1)
        q: Pheromone deposit constant (default: 100.0)
        num_ants: Number of ants per iteration (default: 20)
        num_iterations: Maximum iterations (default: 100)
        elitist_weight: Weight for best solution pheromone (default: 2.0)
    """

    alpha: float = 1.0
    beta: float = 2.0
    rho: float = 0.1
    q: float = 100.0
    num_ants: int = 20
    num_iterations: int = 100
    elitist_weight: float = 2.0


@dataclass
class Solution:
    """
    Represents a complete solution (tour) for the TSP problem.

    Attributes:
        path: List of node indices in visit order
        cost: Total cost of the path
        block_sequence: List of block IDs in visit order
    """

    path: List[int]
    cost: float
    block_sequence: List[int] = field(default_factory=list)

    def is_valid(self, num_blocks: int) -> bool:
        """
        Check if solution is valid (all blocks visited exactly once).

        A valid solution visits each block exactly twice (entry and exit nodes),
        for a total of 2 * num_blocks nodes.
        """
        # Check that we visited 2 nodes per block
        if len(self.block_sequence) != 2 * num_blocks:
            return False

        # Check that each block appears exactly twice
        from collections import Counter
        block_counts = Counter(self.block_sequence)

        # All blocks must appear exactly twice
        if len(block_counts) != num_blocks:
            return False

        for count in block_counts.values():
            if count != 2:
                return False

        return True


class Ant:
    """
    Single ant for ACO algorithm.

    An ant constructs a solution by probabilistically selecting nodes
    based on pheromone trails and heuristic information.
    """

    def __init__(self, nodes: List[BlockNode], blocks: List[Block], cost_matrix: np.ndarray):
        """
        Initialize ant.

        Args:
            nodes: List of all nodes
            blocks: List of all blocks
            cost_matrix: Cost matrix between nodes
        """
        self.nodes = nodes
        self.blocks = blocks
        self.cost_matrix = cost_matrix
        self.num_blocks = len(blocks)

        # Solution state
        self.path: List[int] = []
        self.visited_nodes: Set[int] = set()  # Track visited nodes, not blocks
        self.current_node: Optional[int] = None
        self.total_cost: float = 0.0

    def reset(self):
        """Reset ant to initial state."""
        self.path = []
        self.visited_nodes = set()
        self.current_node = None
        self.total_cost = 0.0

    def get_available_nodes(self) -> List[int]:
        """
        Get list of nodes that can be visited next.

        A node is available if:
        1. It hasn't been visited yet
        2. The transition cost is valid (finite)

        Returns:
            List of valid next node indices
        """
        available = []

        for node_idx in range(len(self.nodes)):
            # Skip if already visited
            if node_idx in self.visited_nodes:
                continue

            # Skip if cost is invalid (infinity)
            if self.current_node is not None:
                if self.cost_matrix[self.current_node][node_idx] >= 1e9:
                    continue

            available.append(node_idx)

        return available

    def select_next_node(
        self, pheromone: np.ndarray, heuristic: np.ndarray, alpha: float, beta: float
    ) -> Optional[int]:
        """
        Select next node using ACO probability formula.

        Probability: p[i][j] = (pheromone[i][j]^alpha * heuristic[i][j]^beta) / sum

        Args:
            pheromone: Pheromone matrix
            heuristic: Heuristic matrix
            alpha: Pheromone weight
            beta: Heuristic weight

        Returns:
            Index of selected node, or None if no valid nodes
        """
        if self.current_node is None:
            # First node - select randomly
            available = self.get_available_nodes()
            if not available:
                return None
            return random.choice(available)

        # Get available nodes
        available = self.get_available_nodes()
        if not available:
            return None

        # Calculate probabilities
        probabilities = []
        for node_idx in available:
            tau = pheromone[self.current_node][node_idx]
            eta = heuristic[self.current_node][node_idx]

            # ACO formula: tau^alpha * eta^beta
            prob = (tau ** alpha) * (eta ** beta)
            probabilities.append(prob)

        # Normalize probabilities
        total = sum(probabilities)
        if total == 0:
            # Fallback to uniform random
            return random.choice(available)

        probabilities = [p / total for p in probabilities]

        # Select node based on probabilities
        selected = np.random.choice(available, p=probabilities)
        return int(selected)

    def move_to(self, node_idx: int):
        """
        Move ant to specified node.

        Args:
            node_idx: Index of node to move to
        """
        # Add to path
        self.path.append(node_idx)

        # Update cost
        if self.current_node is not None:
            self.total_cost += self.cost_matrix[self.current_node][node_idx]

        # Mark node as visited
        self.visited_nodes.add(node_idx)

        # Update current position
        self.current_node = node_idx

    def construct_solution(
        self, pheromone: np.ndarray, heuristic: np.ndarray, alpha: float, beta: float
    ) -> Solution:
        """
        Construct complete solution.

        A complete solution visits exactly 2 nodes per block (entry and exit),
        for a total of 2 * num_blocks nodes.

        Args:
            pheromone: Pheromone matrix
            heuristic: Heuristic matrix
            alpha: Pheromone weight
            beta: Heuristic weight

        Returns:
            Complete solution
        """
        self.reset()

        # Construct path by visiting 2 nodes per block (entry and exit)
        target_nodes = 2 * self.num_blocks

        while len(self.path) < target_nodes:
            next_node = self.select_next_node(pheromone, heuristic, alpha, beta)

            if next_node is None:
                # No valid next node - solution is invalid
                break

            self.move_to(next_node)

        # Extract block sequence
        block_sequence = [self.nodes[node_idx].block_id for node_idx in self.path]

        return Solution(path=self.path.copy(), cost=self.total_cost, block_sequence=block_sequence)


class ACOSolver:
    """
    Ant Colony Optimization solver for block sequencing problem.
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
            blocks: List of blocks to sequence
            nodes: List of all entry/exit nodes
            cost_matrix: Cost matrix between nodes
            params: ACO parameters (default: use defaults)
        """
        self.blocks = blocks
        self.nodes = nodes
        self.cost_matrix = cost_matrix
        self.params = params or ACOParameters()

        self.num_nodes = len(nodes)
        self.num_blocks = len(blocks)

        # Initialize pheromone and heuristic matrices
        self.pheromone = self._initialize_pheromone()
        self.heuristic = self._calculate_heuristic()

        # Best solution tracking
        self.best_solution: Optional[Solution] = None
        self.iteration_best_costs: List[float] = []  # Best found in each iteration
        self.global_best_costs: List[float] = []  # Global best at each iteration
        self.iteration_avg_costs: List[float] = []

    def _initialize_pheromone(self) -> np.ndarray:
        """
        Initialize pheromone matrix with uniform values.

        Returns:
            Initial pheromone matrix
        """
        # Start with small uniform pheromone on all edges
        tau0 = 1.0
        pheromone = np.full((self.num_nodes, self.num_nodes), tau0)
        return pheromone

    def _calculate_heuristic(self) -> np.ndarray:
        """
        Calculate heuristic matrix (inverse of cost).

        Returns:
            Heuristic matrix
        """
        heuristic = np.zeros((self.num_nodes, self.num_nodes))

        for i in range(self.num_nodes):
            for j in range(self.num_nodes):
                if self.cost_matrix[i][j] > 0 and self.cost_matrix[i][j] < 1e9:
                    heuristic[i][j] = 1.0 / self.cost_matrix[i][j]
                else:
                    heuristic[i][j] = 0.0

        return heuristic

    def _evaporate_pheromone(self):
        """Evaporate pheromone on all edges."""
        self.pheromone *= (1.0 - self.params.rho)

    def _deposit_pheromone(self, solutions: List[Solution]):
        """
        Deposit pheromone based on solution quality.

        Uses elitist strategy: best solution deposits more pheromone.

        Args:
            solutions: List of solutions from this iteration
        """
        # Regular ants deposit pheromone
        for solution in solutions:
            if solution.cost > 0 and solution.is_valid(self.num_blocks):
                delta_tau = self.params.q / solution.cost

                # Deposit on all edges in path
                for i in range(len(solution.path) - 1):
                    from_node = solution.path[i]
                    to_node = solution.path[i + 1]
                    self.pheromone[from_node][to_node] += delta_tau

        # Best solution (elitist) deposits extra pheromone
        if self.best_solution is not None:
            delta_tau_best = self.params.elitist_weight * self.params.q / self.best_solution.cost

            for i in range(len(self.best_solution.path) - 1):
                from_node = self.best_solution.path[i]
                to_node = self.best_solution.path[i + 1]
                self.pheromone[from_node][to_node] += delta_tau_best

    def solve(self, verbose: bool = False) -> Solution:
        """
        Run ACO algorithm to find best solution.

        Args:
            verbose: Print progress information

        Returns:
            Best solution found
        """
        if verbose:
            print(f"Starting ACO with {self.num_blocks} blocks, {self.num_nodes} nodes")
            print(f"Parameters: alpha={self.params.alpha}, beta={self.params.beta}, "
                  f"rho={self.params.rho}, ants={self.params.num_ants}")

        for iteration in range(self.params.num_iterations):
            # Create ants
            ants = [Ant(self.nodes, self.blocks, self.cost_matrix) for _ in range(self.params.num_ants)]

            # Construct solutions
            solutions = []
            for ant in ants:
                solution = ant.construct_solution(
                    self.pheromone, self.heuristic, self.params.alpha, self.params.beta
                )
                if solution.is_valid(self.num_blocks):
                    solutions.append(solution)

            # Update best solution
            if solutions:
                iteration_best = min(solutions, key=lambda s: s.cost)

                if self.best_solution is None or iteration_best.cost < self.best_solution.cost:
                    self.best_solution = iteration_best

                # Track statistics
                self.iteration_best_costs.append(iteration_best.cost)
                self.global_best_costs.append(self.best_solution.cost)  # Track global best
                avg_cost = sum(s.cost for s in solutions) / len(solutions)
                self.iteration_avg_costs.append(avg_cost)

                if verbose and iteration % 10 == 0:
                    print(f"Iteration {iteration}: Best={self.best_solution.cost:.2f}, "
                          f"Iter Best={iteration_best.cost:.2f}, Avg={avg_cost:.2f}")

            # Update pheromone
            self._evaporate_pheromone()
            if solutions:
                self._deposit_pheromone(solutions)

        if verbose:
            if self.best_solution:
                print(f"\nFinal best solution: {self.best_solution.cost:.2f}")
                print(f"Block sequence: {self.best_solution.block_sequence}")
            else:
                print("\nNo valid solution found!")

        return self.best_solution

    def get_convergence_data(self) -> Tuple[List[float], List[float]]:
        """
        Get convergence data for plotting.

        Returns:
            Tuple of (global_best_costs, avg_costs_per_iteration)
            - global_best_costs: Best solution cost at each iteration (monotonically decreasing)
            - avg_costs_per_iteration: Average solution cost in each iteration
        """
        return (self.global_best_costs, self.iteration_avg_costs)
