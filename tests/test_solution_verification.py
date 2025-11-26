"""
Comprehensive verification tests for Stage 3 solution correctness.

These tests ensure that:
1. ACO solutions have consecutive entry/exit nodes for each block
2. Path generation correctly creates working and transition segments
3. Path statistics are accurate
4. Efficiency metrics are reasonable
"""

import pytest

from src.data import create_field_with_rectangular_obstacles, FieldParameters
from src.decomposition import boustrophedon_decomposition, merge_blocks_by_criteria
from src.geometry import generate_field_headland, generate_parallel_tracks
from src.obstacles.classifier import classify_all_obstacles, get_type_d_obstacles
from src.optimization import (
    ACOParameters,
    ACOSolver,
    build_cost_matrix,
    generate_path_from_solution,
    get_path_statistics,
)


class TestSolutionStructure:
    """Test that ACO solutions have the correct structure."""

    def setup_method(self):
        """Create a simple test field with 3 blocks."""
        field = create_field_with_rectangular_obstacles(
            field_width=60,
            field_height=50,
            obstacle_specs=[
                (15, 15, 10, 8),
                (35, 20, 8, 10),
            ],
            name="Verification Test Field",
        )

        params = FieldParameters(
            operating_width=5.0,
            turning_radius=3.0,
            num_headland_passes=2,
            driving_direction=0.0,
            obstacle_threshold=5.0,
        )

        # Generate headland
        field_headland = generate_field_headland(
            field_boundary=field.boundary_polygon,
            operating_width=params.operating_width,
            num_passes=params.num_headland_passes,
        )

        # Classify obstacles
        classified_obstacles = classify_all_obstacles(
            obstacle_boundaries=field.obstacles,
            field_inner_boundary=field_headland.inner_boundary,
            driving_direction_degrees=params.driving_direction,
            operating_width=params.operating_width,
            threshold=params.obstacle_threshold,
        )

        type_d_obstacles = get_type_d_obstacles(classified_obstacles)
        obstacle_polygons = [obs.polygon for obs in type_d_obstacles]

        # Decomposition
        preliminary_blocks = boustrophedon_decomposition(
            inner_boundary=field_headland.inner_boundary,
            obstacles=obstacle_polygons,
            driving_direction_degrees=params.driving_direction,
        )

        self.blocks = merge_blocks_by_criteria(
            blocks=preliminary_blocks, operating_width=params.operating_width
        )

        # Generate tracks
        for block in self.blocks:
            tracks = generate_parallel_tracks(
                inner_boundary=block.polygon,
                driving_direction_degrees=params.driving_direction,
                operating_width=params.operating_width,
            )
            for i, track in enumerate(tracks):
                track.block_id = block.block_id
                track.index = i
            block.tracks = tracks

        # Create nodes
        self.all_nodes = []
        node_index = 0
        for block in self.blocks:
            nodes = block.create_entry_exit_nodes(start_index=node_index)
            self.all_nodes.extend(nodes)
            node_index += 4

        # Build cost matrix
        self.cost_matrix = build_cost_matrix(
            blocks=self.blocks, nodes=self.all_nodes
        )

    def test_solution_has_consecutive_block_visits(self):
        """Test that each block's entry and exit nodes are consecutive."""
        # Run ACO
        aco_params = ACOParameters(num_ants=10, num_iterations=20)
        solver = ACOSolver(
            blocks=self.blocks,
            nodes=self.all_nodes,
            cost_matrix=self.cost_matrix,
            params=aco_params,
        )

        solution = solver.solve(verbose=False)

        assert solution is not None
        assert solution.is_valid(len(self.blocks))

        # Check that block sequence has consecutive pairs
        block_sequence = solution.block_sequence

        # Should have 2 * num_blocks entries
        assert len(block_sequence) == 2 * len(self.blocks)

        # Each block should appear exactly twice
        from collections import Counter
        block_counts = Counter(block_sequence)
        actual_block_ids = set(b.block_id for b in self.blocks)
        for block_id in actual_block_ids:
            assert block_counts[block_id] == 2, \
                f"Block {block_id} appears {block_counts[block_id]} times, expected 2"

        # Check for consecutive pairs
        consecutive_blocks = []
        for i in range(0, len(block_sequence), 2):
            # Every pair should be the same block
            if i + 1 < len(block_sequence):
                assert block_sequence[i] == block_sequence[i + 1], \
                    f"Blocks at positions {i} and {i+1} should be the same, but got {block_sequence[i]} and {block_sequence[i+1]}"
                consecutive_blocks.append(block_sequence[i])

        # All blocks should be represented
        assert set(consecutive_blocks) == actual_block_ids

    def test_path_has_working_segments(self):
        """Test that generated path has working segments."""
        # Run ACO
        aco_params = ACOParameters(num_ants=10, num_iterations=20)
        solver = ACOSolver(
            blocks=self.blocks,
            nodes=self.all_nodes,
            cost_matrix=self.cost_matrix,
            params=aco_params,
        )

        solution = solver.solve(verbose=False)
        path_plan = generate_path_from_solution(solution, self.blocks, self.all_nodes)

        # Should have working segments
        working_segments = [s for s in path_plan.segments if s.segment_type == "working"]
        assert len(working_segments) == len(self.blocks), \
            f"Expected {len(self.blocks)} working segments, got {len(working_segments)}"

        # Should have transitions between blocks
        transition_segments = [s for s in path_plan.segments if s.segment_type == "transition"]
        assert len(transition_segments) == len(self.blocks) - 1, \
            f"Expected {len(self.blocks) - 1} transitions, got {len(transition_segments)}"

        # Total segments should match
        assert len(path_plan.segments) == len(working_segments) + len(transition_segments)

    def test_path_efficiency_is_reasonable(self):
        """Test that path efficiency is > 50% (more working than transitions)."""
        # Run ACO
        aco_params = ACOParameters(num_ants=10, num_iterations=20)
        solver = ACOSolver(
            blocks=self.blocks,
            nodes=self.all_nodes,
            cost_matrix=self.cost_matrix,
            params=aco_params,
        )

        solution = solver.solve(verbose=False)
        path_plan = generate_path_from_solution(solution, self.blocks, self.all_nodes)

        stats = get_path_statistics(path_plan)

        # Working distance should be > 0
        assert stats["working_distance"] > 0, "Working distance should be positive"

        # Efficiency should be reasonable (> 50%)
        assert stats["efficiency"] > 0.5, \
            f"Efficiency should be > 50%, got {stats['efficiency']*100:.1f}%"

        # Total distance should equal working + transition
        assert abs(stats["total_distance"] - (stats["working_distance"] + stats["transition_distance"])) < 0.01

    def test_multiple_runs_produce_valid_solutions(self):
        """Test that multiple ACO runs all produce valid solutions."""
        aco_params = ACOParameters(num_ants=10, num_iterations=20)

        for run in range(5):
            solver = ACOSolver(
                blocks=self.blocks,
                nodes=self.all_nodes,
                cost_matrix=self.cost_matrix,
                params=aco_params,
            )

            solution = solver.solve(verbose=False)

            assert solution is not None, f"Run {run}: No solution found"
            assert solution.is_valid(len(self.blocks)), f"Run {run}: Invalid solution"

            # Generate path
            path_plan = generate_path_from_solution(solution, self.blocks, self.all_nodes)
            stats = get_path_statistics(path_plan)

            # Verify structure
            assert stats["num_working_segments"] == len(self.blocks), \
                f"Run {run}: Expected {len(self.blocks)} working segments"
            assert stats["efficiency"] > 0.5, \
                f"Run {run}: Efficiency too low: {stats['efficiency']*100:.1f}%"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
