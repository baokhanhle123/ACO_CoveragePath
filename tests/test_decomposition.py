"""
Tests for Stage 2: Boustrophedon Decomposition and Block Merging.

Test coverage:
1. Critical point detection
2. Sweep line slicing
3. Boustrophedon decomposition
4. Block adjacency graph construction
5. Block merging algorithms
6. Integration with Stage 1
"""

import numpy as np
from shapely.geometry import Polygon

from src.data import FieldParameters, create_field_with_rectangular_obstacles
from src.data.block import Block
from src.decomposition.block_merger import (
    build_block_adjacency_graph,
    check_blocks_adjacent,
    merge_blocks_by_criteria,
    merge_two_blocks,
)
from src.decomposition.boustrophedon import (
    boustrophedon_decomposition,
    find_critical_points,
    get_decomposition_statistics,
)
from src.geometry import generate_field_headland
from src.obstacles.classifier import classify_all_obstacles, get_type_d_obstacles


class TestCriticalPoints:
    """Test critical point detection for sweep line algorithm."""

    def test_simple_field_no_obstacles(self):
        """Test critical points for simple rectangular field without obstacles."""
        # Simple rectangle should only have critical points at boundaries
        field = Polygon([(0, 0), (100, 0), (100, 80), (0, 80)])
        obstacles = []

        critical_points = find_critical_points(field, obstacles, driving_direction_degrees=0.0)

        # Should have 2 critical points (left and right boundaries)
        assert len(critical_points) == 2
        assert np.isclose(critical_points[0], 0.0)
        assert np.isclose(critical_points[1], 100.0)

    def test_single_obstacle(self):
        """Test critical points with one rectangular obstacle."""
        field = Polygon([(0, 0), (100, 0), (100, 80), (0, 80)])
        obstacle = Polygon([(30, 30), (50, 30), (50, 50), (30, 50)])
        obstacles = [obstacle]

        critical_points = find_critical_points(field, obstacles, driving_direction_degrees=0.0)

        # Should have field boundaries + obstacle boundaries
        # Field: x=0, x=100
        # Obstacle: x=30, x=50
        # Total: 4 critical points
        assert len(critical_points) == 4
        assert 0.0 in critical_points
        assert 30.0 in critical_points
        assert 50.0 in critical_points
        assert 100.0 in critical_points


class TestBoustrophedonDecomposition:
    """Test boustrophedon decomposition algorithm."""

    def test_decomposition_no_obstacles(self):
        """Test decomposition of field without obstacles."""
        field = Polygon([(0, 0), (100, 0), (100, 80), (0, 80)])
        obstacles = []

        blocks = boustrophedon_decomposition(field, obstacles, driving_direction_degrees=0.0)

        # Without obstacles, should get 1 block covering entire field
        assert len(blocks) == 1
        assert np.isclose(blocks[0].area, 8000.0, rtol=0.01)

    def test_decomposition_single_obstacle(self):
        """Test decomposition with single obstacle."""
        field = Polygon([(0, 0), (100, 0), (100, 80), (0, 80)])
        obstacle = Polygon([(40, 30), (60, 30), (60, 50), (40, 50)])
        obstacles = [obstacle]

        blocks = boustrophedon_decomposition(field, obstacles, driving_direction_degrees=0.0)

        # Should get multiple blocks (at least 3: left, right, top, bottom of obstacle)
        assert len(blocks) >= 3

        # Total area should equal field area minus obstacle area
        total_block_area = sum(block.area for block in blocks)
        expected_area = field.area - obstacle.area
        assert np.isclose(total_block_area, expected_area, rtol=0.01)

    def test_decomposition_multiple_obstacles(self):
        """Test decomposition with multiple obstacles."""
        field = create_field_with_rectangular_obstacles(
            field_width=100,
            field_height=80,
            obstacle_specs=[(30, 30, 10, 10), (60, 50, 10, 10)],
            name="Test Field",
        )

        # Get inner boundary after headland
        headland = generate_field_headland(
            field_boundary=field.boundary_polygon, operating_width=5.0, num_passes=2
        )

        # Classify obstacles
        classified = classify_all_obstacles(
            obstacle_boundaries=field.obstacles,
            field_inner_boundary=headland.inner_boundary,
            driving_direction_degrees=0.0,
            operating_width=5.0,
            threshold=5.0,
        )

        type_d_obstacles = get_type_d_obstacles(classified)
        obstacle_polygons = [obs.polygon for obs in type_d_obstacles]

        blocks = boustrophedon_decomposition(
            headland.inner_boundary, obstacle_polygons, driving_direction_degrees=0.0
        )

        # Should get multiple blocks
        assert len(blocks) > 0

        # All blocks should be within field boundary
        for block in blocks:
            assert headland.inner_boundary.contains(
                block.polygon
            ) or headland.inner_boundary.covers(block.polygon)


class TestBlockAdjacency:
    """Test block adjacency graph construction."""

    def test_adjacent_blocks(self):
        """Test detection of adjacent blocks."""
        # Two adjacent rectangular blocks
        block1 = Block(block_id=0, boundary=[(0, 0), (50, 0), (50, 80), (0, 80)])
        block2 = Block(block_id=1, boundary=[(50, 0), (100, 0), (100, 80), (50, 80)])

        # They share an edge at x=50
        assert check_blocks_adjacent(block1, block2)

    def test_non_adjacent_blocks(self):
        """Test detection of non-adjacent blocks."""
        block1 = Block(block_id=0, boundary=[(0, 0), (40, 0), (40, 80), (0, 80)])
        block2 = Block(block_id=1, boundary=[(60, 0), (100, 0), (100, 80), (60, 80)])

        # They don't share an edge (gap at x=40 to x=60)
        assert not check_blocks_adjacent(block1, block2)

    def test_build_adjacency_graph(self):
        """Test building adjacency graph for multiple blocks."""
        blocks = [
            Block(block_id=0, boundary=[(0, 0), (30, 0), (30, 80), (0, 80)]),
            Block(block_id=1, boundary=[(30, 0), (60, 0), (60, 80), (30, 80)]),
            Block(block_id=2, boundary=[(60, 0), (100, 0), (100, 80), (60, 80)]),
        ]

        graph = build_block_adjacency_graph(blocks)

        # Block 0 adjacent to Block 1
        assert 1 in graph.get_adjacent_blocks(0)
        assert 0 in graph.get_adjacent_blocks(1)

        # Block 1 adjacent to Block 2
        assert 2 in graph.get_adjacent_blocks(1)
        assert 1 in graph.get_adjacent_blocks(2)

        # Block 0 NOT adjacent to Block 2
        assert 2 not in graph.get_adjacent_blocks(0)
        assert 0 not in graph.get_adjacent_blocks(2)


class TestBlockMerging:
    """Test block merging algorithms."""

    def test_merge_two_blocks(self):
        """Test merging two adjacent blocks."""
        block1 = Block(block_id=0, boundary=[(0, 0), (50, 0), (50, 80), (0, 80)])
        block2 = Block(block_id=1, boundary=[(50, 0), (100, 0), (100, 80), (50, 80)])

        merged = merge_two_blocks(block1, block2, new_block_id=10)

        # Merged block should cover combined area
        assert np.isclose(merged.area, block1.area + block2.area, rtol=0.01)

        # Should have new ID
        assert merged.block_id == 10

    def test_merge_blocks_by_criteria(self):
        """Test high-level merging with criteria."""
        # Create small blocks that should be merged
        # With operating_width=5.0, default min_width=15m, min_area=75m²
        blocks = [
            Block(block_id=0, boundary=[(0, 0), (5, 0), (5, 10), (0, 10)]),  # 50m² - small
            Block(block_id=1, boundary=[(5, 0), (10, 0), (10, 10), (5, 10)]),  # 50m² - small
            Block(block_id=2, boundary=[(10, 0), (100, 0), (100, 80), (10, 80)]),  # Large
        ]

        merged_blocks = merge_blocks_by_criteria(blocks, operating_width=5.0)

        # Should have fewer blocks after merging (small blocks should merge)
        assert len(merged_blocks) < len(blocks)
        # Should have at most 2 blocks (merged small + large)
        assert len(merged_blocks) <= 2


class TestStage2Integration:
    """Integration tests for complete Stage 2 pipeline."""

    def test_full_stage2_pipeline(self):
        """Test complete Stage 2: decomposition + merging."""
        # 1. Create field with obstacles (Stage 1)
        field = create_field_with_rectangular_obstacles(
            field_width=100,
            field_height=80,
            obstacle_specs=[(30, 30, 15, 12), (65, 50, 12, 15)],
            name="Integration Test Field",
        )

        params = FieldParameters(
            operating_width=5.0,
            turning_radius=3.0,
            num_headland_passes=2,
            driving_direction=0.0,
            obstacle_threshold=5.0,
        )

        # 2. Generate headland
        headland = generate_field_headland(
            field_boundary=field.boundary_polygon,
            operating_width=params.operating_width,
            num_passes=params.num_headland_passes,
        )

        # 3. Classify obstacles
        classified = classify_all_obstacles(
            obstacle_boundaries=field.obstacles,
            field_inner_boundary=headland.inner_boundary,
            driving_direction_degrees=params.driving_direction,
            operating_width=params.operating_width,
            threshold=params.obstacle_threshold,
        )

        type_d_obstacles = get_type_d_obstacles(classified)
        obstacle_polygons = [obs.polygon for obs in type_d_obstacles]

        # 4. Boustrophedon decomposition (Stage 2)
        preliminary_blocks = boustrophedon_decomposition(
            headland.inner_boundary, obstacle_polygons, driving_direction_degrees=0.0
        )

        assert len(preliminary_blocks) > 0
        print(f"Preliminary blocks: {len(preliminary_blocks)}")

        # 5. Block merging (Stage 2)
        final_blocks = merge_blocks_by_criteria(preliminary_blocks, operating_width=5.0)

        assert len(final_blocks) > 0
        assert len(final_blocks) <= len(preliminary_blocks)
        print(f"Final blocks after merging: {len(final_blocks)}")

        # 6. Verify coverage
        total_area = sum(block.area for block in final_blocks)
        expected_area = headland.inner_boundary.area - sum(
            obs.area for obs in obstacle_polygons
        )
        assert np.isclose(total_area, expected_area, rtol=0.05)


class TestDecompositionStatistics:
    """Test statistics and reporting functions."""

    def test_empty_blocks_statistics(self):
        """Test statistics with empty block list."""
        stats = get_decomposition_statistics([])

        assert stats["num_blocks"] == 0
        assert stats["total_area"] == 0.0
        assert stats["total_tracks"] == 0

    def test_decomposition_statistics(self):
        """Test statistics calculation."""
        blocks = [
            Block(block_id=0, boundary=[(0, 0), (50, 0), (50, 80), (0, 80)]),
            Block(block_id=1, boundary=[(50, 0), (100, 0), (100, 80), (50, 80)]),
        ]

        stats = get_decomposition_statistics(blocks)

        assert stats["num_blocks"] == 2
        assert stats["total_area"] == 8000.0
        assert stats["avg_area"] == 4000.0
        assert stats["min_area"] == 4000.0
        assert stats["max_area"] == 4000.0
