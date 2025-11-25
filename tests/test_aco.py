"""
Tests for ACO algorithm (Stage 3).

Tests:
- ACOParameters dataclass
- Ant solution construction
- Pheromone initialization and update
- ACO solver convergence
- Solution validity
"""

import numpy as np
import pytest

from src.data.block import Block, BlockNode
from src.data.track import Track
from src.optimization.aco import ACOParameters, ACOSolver, Ant, Solution


class TestACOParameters:
    """Test ACO parameter configuration."""

    def test_default_parameters(self):
        """Test default parameter values."""
        params = ACOParameters()

        assert params.alpha == 1.0
        assert params.beta == 2.0
        assert params.rho == 0.1
        assert params.q == 100.0
        assert params.num_ants == 20
        assert params.num_iterations == 100
        assert params.elitist_weight == 2.0

    def test_custom_parameters(self):
        """Test custom parameter values."""
        params = ACOParameters(
            alpha=2.0,
            beta=3.0,
            rho=0.2,
            q=50.0,
            num_ants=10,
            num_iterations=50,
            elitist_weight=1.5,
        )

        assert params.alpha == 2.0
        assert params.beta == 3.0
        assert params.rho == 0.2
        assert params.q == 50.0
        assert params.num_ants == 10
        assert params.num_iterations == 50
        assert params.elitist_weight == 1.5


class TestSolution:
    """Test Solution class."""

    def test_solution_creation(self):
        """Test creating a solution."""
        path = [0, 4, 8, 12, 16]
        cost = 100.5
        block_sequence = [0, 1, 2, 3, 4]

        solution = Solution(path=path, cost=cost, block_sequence=block_sequence)

        assert solution.path == path
        assert solution.cost == cost
        assert solution.block_sequence == block_sequence

    def test_solution_validity_all_blocks_visited(self):
        """Test valid solution with all blocks visited once (2 nodes per block)."""
        solution = Solution(
            path=[0, 3, 4, 7, 8, 11, 12, 15, 16, 19],
            cost=100.0,
            block_sequence=[0, 0, 1, 1, 2, 2, 3, 3, 4, 4],  # Each block appears twice
        )

        assert solution.is_valid(num_blocks=5)

    def test_solution_validity_missing_blocks(self):
        """Test invalid solution with missing blocks."""
        solution = Solution(
            path=[0, 4, 8],
            cost=50.0,
            block_sequence=[0, 1, 2],
        )

        assert not solution.is_valid(num_blocks=5)

    def test_solution_validity_duplicate_blocks(self):
        """Test invalid solution with duplicate blocks."""
        solution = Solution(
            path=[0, 4, 0, 8],
            cost=75.0,
            block_sequence=[0, 1, 0, 2],
        )

        assert not solution.is_valid(num_blocks=3)


class TestAnt:
    """Test Ant behavior."""

    def setup_method(self):
        """Set up test blocks and nodes."""
        from src.optimization.cost_matrix import build_cost_matrix

        # Create 2 simple blocks with 1 track each
        self.block1 = Block(
            block_id=0,
            boundary=[(0, 0), (10, 0), (10, 10), (0, 10)],
            tracks=[Track(start=(0, 5), end=(10, 5), index=0)],
        )
        self.block2 = Block(
            block_id=1,
            boundary=[(20, 0), (30, 0), (30, 10), (20, 10)],
            tracks=[Track(start=(20, 5), end=(30, 5), index=0)],
        )

        self.blocks = [self.block1, self.block2]

        # Create nodes
        self.nodes1 = self.block1.create_entry_exit_nodes(start_index=0)
        self.nodes2 = self.block2.create_entry_exit_nodes(start_index=4)
        self.nodes = self.nodes1 + self.nodes2

        # Use proper cost matrix that enforces valid entry/exit pairs
        self.cost_matrix = build_cost_matrix(self.blocks, self.nodes)

    def test_ant_initialization(self):
        """Test ant initialization."""
        ant = Ant(self.nodes, self.blocks, self.cost_matrix)

        assert ant.nodes == self.nodes
        assert ant.blocks == self.blocks
        assert ant.num_blocks == 2
        assert ant.path == []
        assert ant.visited_nodes == set()
        assert ant.current_node is None
        assert ant.total_cost == 0.0

    def test_ant_reset(self):
        """Test ant reset functionality."""
        ant = Ant(self.nodes, self.blocks, self.cost_matrix)

        # Manually set some state
        ant.path = [0, 4]
        ant.visited_nodes = {0, 4}
        ant.current_node = 4
        ant.total_cost = 100.0

        # Reset
        ant.reset()

        assert ant.path == []
        assert ant.visited_nodes == set()
        assert ant.current_node is None
        assert ant.total_cost == 0.0

    def test_ant_get_available_nodes_first_move(self):
        """Test getting available nodes for first move."""
        ant = Ant(self.nodes, self.blocks, self.cost_matrix)

        available = ant.get_available_nodes()

        # All nodes should be available initially
        assert len(available) == 8

    def test_ant_get_available_nodes_after_visit(self):
        """Test getting available nodes after visiting a block."""
        ant = Ant(self.nodes, self.blocks, self.cost_matrix)

        # Move to first node of block 0
        ant.move_to(0)

        available = ant.get_available_nodes()

        # Should not include current node
        assert 0 not in available
        # Should include nodes from unvisited block 1
        assert any(node_idx in available for node_idx in [4, 5, 6, 7])

    def test_ant_move_to(self):
        """Test ant movement."""
        ant = Ant(self.nodes, self.blocks, self.cost_matrix)

        # First move
        ant.move_to(0)

        assert ant.path == [0]
        assert ant.current_node == 0
        assert 0 in ant.visited_nodes  # Node 0 visited
        assert ant.total_cost == 0.0  # No cost for first move

        # Second move
        ant.move_to(4)

        assert ant.path == [0, 4]
        assert ant.current_node == 4
        assert 0 in ant.visited_nodes
        assert 4 in ant.visited_nodes  # Node 4 visited
        assert ant.total_cost > 0.0  # Cost added

    def test_ant_construct_solution(self):
        """Test complete solution construction."""
        ant = Ant(self.nodes, self.blocks, self.cost_matrix)

        # Create pheromone and heuristic matrices
        # Use proper heuristic (inverse of cost) for better guidance
        pheromone = np.ones((8, 8))
        heuristic = np.zeros((8, 8))
        for i in range(8):
            for j in range(8):
                if self.cost_matrix[i][j] > 0 and self.cost_matrix[i][j] < 1e9:
                    heuristic[i][j] = 1.0 / self.cost_matrix[i][j]

        solution = ant.construct_solution(pheromone, heuristic, alpha=1.0, beta=2.0)

        # Should attempt to visit 2 nodes per block (4 total)
        assert len(solution.path) == 4  # 2 blocks * 2 nodes/block
        assert len(solution.block_sequence) == 4
        assert solution.cost >= 0
        # Note: With random selection, solution may not always be valid
        # The ACO solver with multiple ants will find valid solutions


class TestACOSolver:
    """Test ACO solver."""

    def setup_method(self):
        """Set up test blocks and nodes."""
        # Create 3 simple blocks
        self.blocks = [
            Block(
                block_id=i,
                boundary=[(i*15, 0), (i*15+10, 0), (i*15+10, 10), (i*15, 10)],
                tracks=[Track(start=(i*15, 5), end=(i*15+10, 5), index=0)],
            )
            for i in range(3)
        ]

        # Create nodes
        self.nodes = []
        for i, block in enumerate(self.blocks):
            nodes = block.create_entry_exit_nodes(start_index=i*4)
            self.nodes.extend(nodes)

        # Create simple cost matrix
        n = len(self.nodes)
        self.cost_matrix = np.zeros((n, n))
        for i in range(n):
            for j in range(n):
                if i != j:
                    dx = self.nodes[j].position[0] - self.nodes[i].position[0]
                    dy = self.nodes[j].position[1] - self.nodes[i].position[1]
                    self.cost_matrix[i][j] = np.sqrt(dx*dx + dy*dy)

    def test_solver_initialization(self):
        """Test ACO solver initialization."""
        params = ACOParameters(num_ants=5, num_iterations=10)
        solver = ACOSolver(self.blocks, self.nodes, self.cost_matrix, params)

        assert solver.blocks == self.blocks
        assert solver.nodes == self.nodes
        assert solver.num_blocks == 3
        assert solver.num_nodes == 12
        assert solver.params.num_ants == 5
        assert solver.best_solution is None

    def test_pheromone_initialization(self):
        """Test pheromone matrix initialization."""
        solver = ACOSolver(self.blocks, self.nodes, self.cost_matrix)

        # Pheromone should be uniform positive values
        assert solver.pheromone.shape == (12, 12)
        assert np.all(solver.pheromone > 0)
        assert np.allclose(solver.pheromone, solver.pheromone[0, 0])

    def test_heuristic_calculation(self):
        """Test heuristic matrix calculation."""
        solver = ACOSolver(self.blocks, self.nodes, self.cost_matrix)

        # Heuristic should be inverse of cost
        assert solver.heuristic.shape == (12, 12)
        assert np.all(solver.heuristic >= 0)

        # Check inverse relationship
        for i in range(12):
            for j in range(12):
                if self.cost_matrix[i][j] > 0 and self.cost_matrix[i][j] < 1e9:
                    expected = 1.0 / self.cost_matrix[i][j]
                    assert np.isclose(solver.heuristic[i][j], expected)

    def test_pheromone_evaporation(self):
        """Test pheromone evaporation."""
        params = ACOParameters(rho=0.1)
        solver = ACOSolver(self.blocks, self.nodes, self.cost_matrix, params)

        initial_pheromone = solver.pheromone.copy()
        solver._evaporate_pheromone()

        # Pheromone should decrease by (1 - rho)
        expected = initial_pheromone * 0.9
        assert np.allclose(solver.pheromone, expected)

    def test_solver_finds_solution(self):
        """Test that solver finds a valid solution."""
        # Use very few iterations for fast test
        params = ACOParameters(num_ants=5, num_iterations=5)
        solver = ACOSolver(self.blocks, self.nodes, self.cost_matrix, params)

        solution = solver.solve(verbose=False)

        # Should find valid solution
        assert solution is not None
        assert solution.is_valid(num_blocks=3)
        assert solution.cost > 0

    def test_solver_convergence(self):
        """Test that solver improves over iterations."""
        params = ACOParameters(num_ants=10, num_iterations=20)
        solver = ACOSolver(self.blocks, self.nodes, self.cost_matrix, params)

        solution = solver.solve(verbose=False)

        # Get convergence data
        best_costs, avg_costs = solver.get_convergence_data()

        # Should have recorded costs for each iteration
        assert len(best_costs) > 0
        assert len(avg_costs) > 0

        # Best cost should not increase (monotonic improvement)
        for i in range(1, len(best_costs)):
            assert best_costs[i] <= best_costs[i-1]

    def test_solver_with_custom_parameters(self):
        """Test solver with custom ACO parameters."""
        params = ACOParameters(
            alpha=2.0,
            beta=3.0,
            rho=0.2,
            num_ants=8,
            num_iterations=10,
        )
        solver = ACOSolver(self.blocks, self.nodes, self.cost_matrix, params)

        solution = solver.solve(verbose=False)

        assert solution is not None
        assert solution.is_valid(num_blocks=3)


class TestACOConvergence:
    """Test ACO convergence properties."""

    def test_aco_convergence_small_problem(self):
        """Test ACO converges on small problem."""
        # Create 2 blocks far apart
        blocks = [
            Block(
                block_id=0,
                boundary=[(0, 0), (10, 0), (10, 10), (0, 10)],
                tracks=[Track(start=(0, 5), end=(10, 5), index=0)],
            ),
            Block(
                block_id=1,
                boundary=[(100, 0), (110, 0), (110, 10), (100, 10)],
                tracks=[Track(start=(100, 5), end=(110, 5), index=0)],
            ),
        ]

        nodes = []
        for i, block in enumerate(blocks):
            nodes.extend(block.create_entry_exit_nodes(start_index=i*4))

        # Build cost matrix
        n = len(nodes)
        cost_matrix = np.zeros((n, n))
        for i in range(n):
            for j in range(n):
                if i != j:
                    dx = nodes[j].position[0] - nodes[i].position[0]
                    dy = nodes[j].position[1] - nodes[i].position[1]
                    cost_matrix[i][j] = np.sqrt(dx*dx + dy*dy)

        # Solve with good parameters
        params = ACOParameters(num_ants=15, num_iterations=30)
        solver = ACOSolver(blocks, nodes, cost_matrix, params)
        solution = solver.solve(verbose=False)

        # Should find valid solution
        assert solution is not None
        assert solution.is_valid(num_blocks=2)

        # Check improvement
        best_costs, _ = solver.get_convergence_data()
        initial_best = best_costs[0]
        final_best = best_costs[-1]
        assert final_best <= initial_best


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
