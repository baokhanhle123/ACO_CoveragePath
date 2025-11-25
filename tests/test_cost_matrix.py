"""
Tests for cost matrix construction (Stage 3).

Tests:
- Euclidean distance calculation
- Node distance calculation
- Valid/invalid transitions
- Within-block costs
- Cost matrix construction
- Matrix properties (symmetry, diagonal, etc.)
"""

import numpy as np
import pytest

from src.data.block import Block, BlockNode
from src.data.track import Track
from src.optimization.cost_matrix import (
    build_cost_matrix,
    euclidean_distance,
    get_within_block_cost,
    is_valid_transition,
    node_distance,
)


class TestEuclideanDistance:
    """Test Euclidean distance calculation."""

    def test_distance_zero(self):
        """Test distance between same point is zero."""
        pos = (10.0, 20.0)
        dist = euclidean_distance(pos, pos)
        assert dist == 0.0

    def test_distance_horizontal(self):
        """Test horizontal distance."""
        pos1 = (0.0, 0.0)
        pos2 = (10.0, 0.0)
        dist = euclidean_distance(pos1, pos2)
        assert dist == 10.0

    def test_distance_vertical(self):
        """Test vertical distance."""
        pos1 = (0.0, 0.0)
        pos2 = (0.0, 10.0)
        dist = euclidean_distance(pos1, pos2)
        assert dist == 10.0

    def test_distance_diagonal(self):
        """Test diagonal distance (Pythagorean)."""
        pos1 = (0.0, 0.0)
        pos2 = (3.0, 4.0)
        dist = euclidean_distance(pos1, pos2)
        assert dist == 5.0  # 3-4-5 triangle

    def test_distance_symmetric(self):
        """Test distance is symmetric."""
        pos1 = (10.0, 20.0)
        pos2 = (30.0, 40.0)
        dist1 = euclidean_distance(pos1, pos2)
        dist2 = euclidean_distance(pos2, pos1)
        assert dist1 == dist2


class TestNodeDistance:
    """Test node distance calculation."""

    def test_node_distance(self):
        """Test distance between two nodes."""
        node1 = BlockNode(position=(0.0, 0.0), block_id=0, node_type="first_start", index=0)
        node2 = BlockNode(position=(3.0, 4.0), block_id=1, node_type="first_start", index=4)
        dist = node_distance(node1, node2)
        assert dist == 5.0


class TestValidTransitions:
    """Test transition validity checking."""

    def test_same_node_invalid(self):
        """Test that staying at same node is invalid."""
        node = BlockNode(position=(0.0, 0.0), block_id=0, node_type="first_start", index=0)
        blocks = []
        assert not is_valid_transition(node, node, blocks)

    def test_different_blocks_valid(self):
        """Test that transitions between different blocks are valid."""
        node1 = BlockNode(position=(0.0, 0.0), block_id=0, node_type="first_start", index=0)
        node2 = BlockNode(position=(10.0, 10.0), block_id=1, node_type="first_start", index=4)
        blocks = []
        assert is_valid_transition(node1, node2, blocks)

    def test_same_block_even_tracks_valid(self):
        """Test valid transitions within block with even tracks."""
        # Create block with 4 tracks (even)
        block = Block(
            block_id=0,
            boundary=[(0, 0), (10, 0), (10, 10), (0, 10)],
            tracks=[
                Track(start=(0, 2), end=(10, 2), index=0),
                Track(start=(0, 4), end=(10, 4), index=1),
                Track(start=(0, 6), end=(10, 6), index=2),
                Track(start=(0, 8), end=(10, 8), index=3),
            ],
        )

        # Create entry/exit nodes
        nodes = block.create_entry_exit_nodes(start_index=0)
        blocks = [block]

        # For even tracks: first_start ’ last_end should be valid
        node1 = nodes[0]  # first_start
        node2 = nodes[3]  # last_end
        assert is_valid_transition(node1, node2, blocks)

        # Reverse should also be valid
        assert is_valid_transition(node2, node1, blocks)

        # first_start ’ first_end should be invalid (not a valid pair)
        node3 = nodes[1]  # first_end
        assert not is_valid_transition(node1, node3, blocks)

    def test_same_block_odd_tracks_valid(self):
        """Test valid transitions within block with odd tracks."""
        # Create block with 3 tracks (odd)
        block = Block(
            block_id=0,
            boundary=[(0, 0), (10, 0), (10, 10), (0, 10)],
            tracks=[
                Track(start=(0, 2), end=(10, 2), index=0),
                Track(start=(0, 5), end=(10, 5), index=1),
                Track(start=(0, 8), end=(10, 8), index=2),
            ],
        )

        nodes = block.create_entry_exit_nodes(start_index=0)
        blocks = [block]

        # For odd tracks: first_start ’ last_start should be valid
        node1 = nodes[0]  # first_start
        node2 = nodes[2]  # last_start
        assert is_valid_transition(node1, node2, blocks)

        # first_end ’ last_end should also be valid
        node3 = nodes[1]  # first_end
        node4 = nodes[3]  # last_end
        assert is_valid_transition(node3, node4, blocks)


class TestWithinBlockCost:
    """Test within-block cost calculation."""

    def test_within_block_cost(self):
        """Test that within-block cost equals working distance."""
        block = Block(
            block_id=0,
            boundary=[(0, 0), (10, 0), (10, 10), (0, 10)],
            tracks=[
                Track(start=(0, 2), end=(10, 2), index=0),  # length 10
                Track(start=(0, 5), end=(10, 5), index=1),  # length 10
                Track(start=(0, 8), end=(10, 8), index=2),  # length 10
            ],
        )

        nodes = block.create_entry_exit_nodes(start_index=0)
        working_dist = block.get_working_distance()

        # Cost should equal total working distance
        cost = get_within_block_cost(block, nodes[0], nodes[2])
        assert cost == working_dist
        assert cost == 30.0  # 3 tracks * 10 length each


class TestCostMatrixConstruction:
    """Test cost matrix construction."""

    def test_diagonal_is_zero(self):
        """Test that diagonal elements are zero."""
        # Create simple block
        block = Block(
            block_id=0,
            boundary=[(0, 0), (10, 0), (10, 10), (0, 10)],
            tracks=[Track(start=(0, 5), end=(10, 5), index=0)],
        )
        nodes = block.create_entry_exit_nodes(start_index=0)
        blocks = [block]

        cost_matrix = build_cost_matrix(blocks, nodes)

        # Diagonal should be zero
        for i in range(len(nodes)):
            assert cost_matrix[i][i] == 0.0

    def test_matrix_size(self):
        """Test that matrix has correct size."""
        # Create 2 blocks with 4 nodes each = 8 nodes total
        block1 = Block(
            block_id=0,
            boundary=[(0, 0), (10, 0), (10, 10), (0, 10)],
            tracks=[Track(start=(0, 5), end=(10, 5), index=0)],
        )
        block2 = Block(
            block_id=1,
            boundary=[(20, 0), (30, 0), (30, 10), (20, 10)],
            tracks=[Track(start=(20, 5), end=(30, 5), index=0)],
        )

        nodes1 = block1.create_entry_exit_nodes(start_index=0)
        nodes2 = block2.create_entry_exit_nodes(start_index=4)
        nodes = nodes1 + nodes2
        blocks = [block1, block2]

        cost_matrix = build_cost_matrix(blocks, nodes)

        # Should be 8×8
        assert cost_matrix.shape == (8, 8)

    def test_invalid_transitions_have_high_cost(self):
        """Test that invalid transitions have very high cost."""
        block = Block(
            block_id=0,
            boundary=[(0, 0), (10, 0), (10, 10), (0, 10)],
            tracks=[
                Track(start=(0, 2), end=(10, 2), index=0),
                Track(start=(0, 8), end=(10, 8), index=1),
            ],  # Even tracks
        )
        nodes = block.create_entry_exit_nodes(start_index=0)
        blocks = [block]

        cost_matrix = build_cost_matrix(blocks, nodes)

        # first_start (0) ’ first_end (1) should be invalid (high cost)
        assert cost_matrix[0][1] >= 1e9

        # first_start (0) ’ last_end (3) should be valid (finite cost)
        assert cost_matrix[0][3] < 1e9

    def test_between_block_costs(self):
        """Test costs between different blocks are Euclidean distances."""
        block1 = Block(
            block_id=0,
            boundary=[(0, 0), (10, 0), (10, 10), (0, 10)],
            tracks=[Track(start=(0, 5), end=(10, 5), index=0)],
        )
        block2 = Block(
            block_id=1,
            boundary=[(20, 0), (30, 0), (30, 10), (20, 10)],
            tracks=[Track(start=(20, 5), end=(30, 5), index=0)],
        )

        # Manually set node positions for predictable distances
        nodes1 = [
            BlockNode(position=(0.0, 5.0), block_id=0, node_type="first_start", index=0),
            BlockNode(position=(10.0, 5.0), block_id=0, node_type="first_end", index=1),
            BlockNode(position=(0.0, 5.0), block_id=0, node_type="last_start", index=2),
            BlockNode(position=(10.0, 5.0), block_id=0, node_type="last_end", index=3),
        ]
        nodes2 = [
            BlockNode(position=(20.0, 5.0), block_id=1, node_type="first_start", index=4),
            BlockNode(position=(30.0, 5.0), block_id=1, node_type="first_end", index=5),
            BlockNode(position=(20.0, 5.0), block_id=1, node_type="last_start", index=6),
            BlockNode(position=(30.0, 5.0), block_id=1, node_type="last_end", index=7),
        ]

        nodes = nodes1 + nodes2
        blocks = [block1, block2]

        cost_matrix = build_cost_matrix(blocks, nodes)

        # Cost from block1 first_end (10, 5) to block2 first_start (20, 5)
        # Should be Euclidean distance = 10
        cost = cost_matrix[1][4]
        assert np.isclose(cost, 10.0)

    def test_within_block_costs_are_working_distance(self):
        """Test that within-block costs equal working distance."""
        block = Block(
            block_id=0,
            boundary=[(0, 0), (10, 0), (10, 10), (0, 10)],
            tracks=[
                Track(start=(0, 2), end=(10, 2), index=0),
                Track(start=(0, 8), end=(10, 8), index=1),
            ],  # Even tracks, total length = 20
        )

        nodes = block.create_entry_exit_nodes(start_index=0)
        blocks = [block]

        cost_matrix = build_cost_matrix(blocks, nodes)

        # first_start ’ last_end (valid for even tracks)
        # Should equal working distance
        working_dist = block.get_working_distance()
        cost = cost_matrix[0][3]
        assert cost == working_dist
        assert cost == 20.0


class TestCostMatrixProperties:
    """Test mathematical properties of cost matrix."""

    def test_all_costs_non_negative(self):
        """Test that all finite costs are non-negative."""
        block = Block(
            block_id=0,
            boundary=[(0, 0), (10, 0), (10, 10), (0, 10)],
            tracks=[Track(start=(0, 5), end=(10, 5), index=0)],
        )
        nodes = block.create_entry_exit_nodes(start_index=0)
        blocks = [block]

        cost_matrix = build_cost_matrix(blocks, nodes)

        # All finite costs should be >= 0
        finite_costs = cost_matrix[np.isfinite(cost_matrix)]
        assert np.all(finite_costs >= 0)

    def test_no_nan_values(self):
        """Test that matrix contains no NaN values."""
        block = Block(
            block_id=0,
            boundary=[(0, 0), (10, 0), (10, 10), (0, 10)],
            tracks=[Track(start=(0, 5), end=(10, 5), index=0)],
        )
        nodes = block.create_entry_exit_nodes(start_index=0)
        blocks = [block]

        cost_matrix = build_cost_matrix(blocks, nodes)

        # Should have no NaN values
        assert not np.any(np.isnan(cost_matrix))
