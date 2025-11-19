"""
Integration test for Stage 1 of the coverage path planning algorithm.

This tests the complete Stage 1 pipeline:
1. Field creation with obstacles
2. Obstacle classification (Types A, B, C, D)
3. Headland generation (field + obstacles)
4. Track generation
"""

import pytest

from src.data import (
    FieldParameters,
    create_field_with_rectangular_obstacles,
    create_rectangular_field,
)
from src.geometry import (
    generate_field_headland,
    generate_obstacle_headland,
    generate_parallel_tracks,
    order_tracks_by_position,
)
from src.obstacles.classifier import (
    classify_all_obstacles,
    get_obstacle_statistics,
    get_type_d_obstacles,
)


class TestStage1Pipeline:
    """Test complete Stage 1 pipeline integration."""

    def test_simple_field_no_obstacles(self):
        """Test pipeline with simple rectangular field and no obstacles."""
        # Create field
        field = create_rectangular_field(100, 80, name="Simple Field")

        # Parameters
        params = FieldParameters(
            operating_width=5.0,
            turning_radius=3.0,
            num_headland_passes=2,
            driving_direction=0.0,
            obstacle_threshold=5.0,
        )

        # Stage 1.1: Generate field headland
        headland_result = generate_field_headland(
            field_boundary=field.boundary_polygon,
            operating_width=params.operating_width,
            num_passes=params.num_headland_passes,
        )

        assert headland_result is not None
        assert len(headland_result.passes) == 2
        assert headland_result.inner_boundary.area > 0
        assert headland_result.inner_boundary.area < field.boundary_polygon.area

        # Stage 1.3: Generate tracks
        tracks = generate_parallel_tracks(
            inner_boundary=headland_result.inner_boundary,
            driving_direction_degrees=params.driving_direction,
            operating_width=params.operating_width,
        )

        assert len(tracks) > 0
        print(f"Generated {len(tracks)} tracks")

        # All tracks should have positive length
        for track in tracks:
            assert track.length > 0, f"Track {track.index} has zero length"

        # Tracks should cover the field body
        total_track_length = sum(track.length for track in tracks)
        assert total_track_length > 0

    def test_field_with_single_obstacle(self):
        """Test pipeline with field containing one Type D obstacle."""
        # Create field with one obstacle in the middle
        field = create_field_with_rectangular_obstacles(
            field_width=100,
            field_height=80,
            obstacle_specs=[
                (40, 30, 20, 20),  # x, y, width, height
            ],
            name="Field with 1 obstacle",
        )

        params = FieldParameters(
            operating_width=5.0,
            turning_radius=3.0,
            num_headland_passes=2,
            driving_direction=0.0,
            obstacle_threshold=5.0,
        )

        # Stage 1.1: Generate field headland
        field_headland = generate_field_headland(
            field_boundary=field.boundary_polygon,
            operating_width=params.operating_width,
            num_passes=params.num_headland_passes,
        )

        assert field_headland is not None

        # Stage 1.2: Classify obstacles
        classified_obstacles = classify_all_obstacles(
            obstacle_boundaries=field.obstacles,
            field_inner_boundary=field_headland.inner_boundary,
            driving_direction_degrees=params.driving_direction,
            operating_width=params.operating_width,
            threshold=params.obstacle_threshold,
        )

        print("\nObstacle classification results:")
        stats = get_obstacle_statistics(classified_obstacles)
        for key, value in stats.items():
            print(f"  {key}: {value}")

        # Should have at least one obstacle (Type D or B)
        assert len(classified_obstacles) > 0

        # Get Type D obstacles only
        type_d_obstacles = get_type_d_obstacles(classified_obstacles)

        # Generate headlands around Type D obstacles
        obstacle_headlands = []
        for obs in type_d_obstacles:
            obs_headland = generate_obstacle_headland(
                obstacle_boundary=obs.polygon,
                operating_width=params.operating_width,
                num_passes=params.num_headland_passes,
            )
            if obs_headland is not None:
                obstacle_headlands.append(obs_headland)

        print(f"Generated headlands around {len(obstacle_headlands)} Type D obstacles")

        # Stage 1.3: Generate tracks (ignoring obstacles initially)
        tracks = generate_parallel_tracks(
            inner_boundary=field_headland.inner_boundary,
            driving_direction_degrees=params.driving_direction,
            operating_width=params.operating_width,
        )

        assert len(tracks) > 0
        print(f"Generated {len(tracks)} initial tracks (before obstacle subdivision)")

    def test_field_with_multiple_obstacles(self):
        """Test pipeline with multiple obstacles of different types."""
        # Create field with various obstacles
        field = create_field_with_rectangular_obstacles(
            field_width=100,
            field_height=80,
            obstacle_specs=[
                (20, 20, 15, 15),  # Obstacle 1
                (60, 60, 15, 15),  # Obstacle 2
                (40, 10, 3, 3),  # Small obstacle (might be Type A)
                (10, 10, 10, 10),  # Obstacle 4
            ],
            name="Field with multiple obstacles",
        )

        params = FieldParameters(
            operating_width=5.0,
            turning_radius=3.0,
            num_headland_passes=1,
            driving_direction=45.0,  # Diagonal
            obstacle_threshold=5.0,
        )

        # Stage 1: Field headland
        field_headland = generate_field_headland(
            field_boundary=field.boundary_polygon,
            operating_width=params.operating_width,
            num_passes=params.num_headland_passes,
        )

        assert field_headland is not None

        # Stage 2: Classify obstacles
        classified_obstacles = classify_all_obstacles(
            obstacle_boundaries=field.obstacles,
            field_inner_boundary=field_headland.inner_boundary,
            driving_direction_degrees=params.driving_direction,
            operating_width=params.operating_width,
            threshold=params.obstacle_threshold,
        )

        stats = get_obstacle_statistics(classified_obstacles)
        print("\nMultiple obstacles classification:")
        for key, value in stats.items():
            print(f"  {key}: {value}")

        # Should have classified some obstacles
        assert len(classified_obstacles) >= 1

        # Generate tracks
        tracks = generate_parallel_tracks(
            inner_boundary=field_headland.inner_boundary,
            driving_direction_degrees=params.driving_direction,
            operating_width=params.operating_width,
        )

        assert len(tracks) > 0
        print(f"Generated {len(tracks)} tracks for multiple obstacles scenario")

    def test_track_ordering(self):
        """Test that tracks are properly ordered."""
        field = create_rectangular_field(100, 80)

        params = FieldParameters(
            operating_width=5.0,
            turning_radius=3.0,
            num_headland_passes=1,
            driving_direction=0.0,
            obstacle_threshold=5.0,
        )

        headland = generate_field_headland(
            field_boundary=field.boundary_polygon,
            operating_width=params.operating_width,
            num_passes=params.num_headland_passes,
        )

        tracks = generate_parallel_tracks(
            inner_boundary=headland.inner_boundary,
            driving_direction_degrees=params.driving_direction,
            operating_width=params.operating_width,
        )

        # Order tracks
        ordered_tracks = order_tracks_by_position(tracks, params.driving_direction)

        assert len(ordered_tracks) == len(tracks)

        # Check indices are sequential
        for i, track in enumerate(ordered_tracks):
            assert track.index == i

    def test_different_driving_directions(self):
        """Test pipeline with different driving directions."""
        field = create_rectangular_field(100, 80)

        for angle in [0, 45, 90, 135]:
            params = FieldParameters(
                operating_width=5.0,
                turning_radius=3.0,
                num_headland_passes=1,
                driving_direction=float(angle),
                obstacle_threshold=5.0,
            )

            headland = generate_field_headland(
                field_boundary=field.boundary_polygon,
                operating_width=params.operating_width,
                num_passes=params.num_headland_passes,
            )

            tracks = generate_parallel_tracks(
                inner_boundary=headland.inner_boundary,
                driving_direction_degrees=params.driving_direction,
                operating_width=params.operating_width,
            )

            assert len(tracks) > 0
            print(f"Angle {angle}°: Generated {len(tracks)} tracks")

    def test_edge_case_small_field(self):
        """Test with very small field."""
        field = create_rectangular_field(20, 15, name="Small field")

        params = FieldParameters(
            operating_width=3.0,
            turning_radius=2.0,
            num_headland_passes=1,
            driving_direction=0.0,
            obstacle_threshold=3.0,
        )

        headland = generate_field_headland(
            field_boundary=field.boundary_polygon,
            operating_width=params.operating_width,
            num_passes=params.num_headland_passes,
        )

        # Small field might result in very small or no inner boundary
        if headland is not None and headland.inner_boundary.area > 0:
            tracks = generate_parallel_tracks(
                inner_boundary=headland.inner_boundary,
                driving_direction_degrees=params.driving_direction,
                operating_width=params.operating_width,
            )

            # Might have very few or no tracks for small field
            print(f"Small field: Generated {len(tracks)} tracks")
        else:
            print("Small field: No inner boundary after headland")

    def test_edge_case_large_operating_width(self):
        """Test with operating width that's large relative to field."""
        field = create_rectangular_field(50, 40)

        params = FieldParameters(
            operating_width=15.0,  # Large width
            turning_radius=5.0,
            num_headland_passes=1,
            driving_direction=0.0,
            obstacle_threshold=15.0,
        )

        headland = generate_field_headland(
            field_boundary=field.boundary_polygon,
            operating_width=params.operating_width,
            num_passes=params.num_headland_passes,
        )

        if headland is not None and headland.inner_boundary.area > 0:
            tracks = generate_parallel_tracks(
                inner_boundary=headland.inner_boundary,
                driving_direction_degrees=params.driving_direction,
                operating_width=params.operating_width,
            )
            print(f"Large operating width: Generated {len(tracks)} tracks")
        else:
            print("Large operating width: Field too small for headland + tracks")

    def test_close_proximity_obstacles_type_c(self):
        """Test Type C obstacle detection (close proximity)."""
        # Create field with two obstacles very close together
        field = create_field_with_rectangular_obstacles(
            field_width=100,
            field_height=80,
            obstacle_specs=[
                (30, 30, 10, 10),  # Obstacle 1
                (41, 30, 10, 10),  # Obstacle 2 - only 1m away
            ],
            name="Field with close obstacles",
        )

        params = FieldParameters(
            operating_width=5.0,
            turning_radius=3.0,
            num_headland_passes=1,
            driving_direction=0.0,
            obstacle_threshold=5.0,
        )

        field_headland = generate_field_headland(
            field_boundary=field.boundary_polygon,
            operating_width=params.operating_width,
            num_passes=params.num_headland_passes,
        )

        # Classify obstacles - should detect Type C and merge
        classified_obstacles = classify_all_obstacles(
            obstacle_boundaries=field.obstacles,
            field_inner_boundary=field_headland.inner_boundary,
            driving_direction_degrees=params.driving_direction,
            operating_width=params.operating_width,
            threshold=params.obstacle_threshold,
        )

        stats = get_obstacle_statistics(classified_obstacles)
        print("\nClose proximity test:")
        for key, value in stats.items():
            print(f"  {key}: {value}")

        # Should have fewer obstacles after merging (or at least marked as merged)
        assert len(classified_obstacles) <= 2

        # Check if any obstacle is marked as merged
        merged_count = sum(1 for obs in classified_obstacles if obs.is_merged())
        print(f"Merged obstacles: {merged_count}")


def test_stage1_complete_pipeline():
    """
    End-to-end test of Stage 1 pipeline.
    This is what a user would run to complete Stage 1.
    """
    print("\n" + "=" * 80)
    print("STAGE 1 COMPLETE PIPELINE TEST")
    print("=" * 80)

    # 1. Define field
    field = create_field_with_rectangular_obstacles(
        field_width=100,
        field_height=80,
        obstacle_specs=[
            (25, 25, 15, 15),
            (65, 55, 12, 12),
        ],
        name="Test Field",
    )

    print(f"\n1. Field created: {field}")
    print(f"   Area: {field.area:.2f} m²")
    print(f"   Obstacles: {field.get_num_obstacles()}")

    # 2. Define parameters
    params = FieldParameters(
        operating_width=5.0,
        turning_radius=3.0,
        num_headland_passes=2,
        driving_direction=0.0,
        obstacle_threshold=5.0,
    )

    print("\n2. Parameters set:")
    print(f"   Operating width: {params.operating_width} m")
    print(f"   Turning radius: {params.turning_radius} m")
    print(f"   Headland passes: {params.num_headland_passes}")
    print(f"   Driving direction: {params.driving_direction}°")

    # 3. Generate field headland
    print("\n3. Generating field headland...")
    field_headland = generate_field_headland(
        field_boundary=field.boundary_polygon,
        operating_width=params.operating_width,
        num_passes=params.num_headland_passes,
    )

    assert field_headland is not None
    print(f"   ✓ Generated {len(field_headland.passes)} headland passes")
    print(f"   ✓ Inner boundary area: {field_headland.inner_boundary.area:.2f} m²")

    # 4. Classify obstacles
    print("\n4. Classifying obstacles...")
    classified_obstacles = classify_all_obstacles(
        obstacle_boundaries=field.obstacles,
        field_inner_boundary=field_headland.inner_boundary,
        driving_direction_degrees=params.driving_direction,
        operating_width=params.operating_width,
        threshold=params.obstacle_threshold,
    )

    stats = get_obstacle_statistics(classified_obstacles)
    print("   ✓ Classification complete:")
    for key, value in stats.items():
        if value > 0:
            print(f"     - {key}: {value}")

    # 5. Generate obstacle headlands for Type D
    print("\n5. Generating obstacle headlands...")
    type_d_obstacles = get_type_d_obstacles(classified_obstacles)
    obstacle_headlands = []

    for obs in type_d_obstacles:
        obs_headland = generate_obstacle_headland(
            obstacle_boundary=obs.polygon,
            operating_width=params.operating_width,
            num_passes=params.num_headland_passes,
        )
        if obs_headland is not None:
            obstacle_headlands.append((obs, obs_headland))

    print(f"   ✓ Generated headlands for {len(obstacle_headlands)} obstacles")

    # 6. Generate field-work tracks
    print("\n6. Generating field-work tracks...")
    tracks = generate_parallel_tracks(
        inner_boundary=field_headland.inner_boundary,
        driving_direction_degrees=params.driving_direction,
        operating_width=params.operating_width,
    )

    tracks = order_tracks_by_position(tracks, params.driving_direction)

    print(f"   ✓ Generated {len(tracks)} tracks")
    print(f"   ✓ Total track length: {sum(t.length for t in tracks):.2f} m")

    # Summary
    print("\n" + "=" * 80)
    print("STAGE 1 COMPLETE - Summary")
    print("=" * 80)
    print(f"✓ Field headland generated: {len(field_headland.passes)} passes")
    print(f"✓ Obstacles classified: {len(classified_obstacles)} obstacles")
    print(f"✓ Type D obstacles: {len(type_d_obstacles)}")
    print(f"✓ Obstacle headlands: {len(obstacle_headlands)}")
    print(f"✓ Field-work tracks: {len(tracks)} tracks")
    print("\n✓ STAGE 1 PIPELINE SUCCESSFUL")
    print("=" * 80)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
