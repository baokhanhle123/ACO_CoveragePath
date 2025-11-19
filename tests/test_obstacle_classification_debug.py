"""
Debug obstacle classification to ensure Type D detection works correctly.
"""

import pytest
from shapely.geometry import Polygon

from src.data import Field
from src.geometry import generate_field_headland
from src.obstacles.classifier import (
    classify_all_obstacles,
    classify_obstacle_type_b,
    get_type_d_obstacles,
)


def test_type_d_obstacle_detection():
    """Test that obstacles in field body are correctly classified as Type D."""
    # Create field 100x80
    field_boundary = [(0, 0), (100, 0), (100, 80), (0, 80)]
    _ = Field(boundary=field_boundary, obstacles=[], name="Test")  # For reference

    # Generate headland with 2 passes, width 5m
    # Total headland width = 2 * 5m = 10m
    # Inner boundary should be roughly: (10, 10) to (90, 70)
    field_poly = Polygon(field_boundary)
    headland = generate_field_headland(field_boundary=field_poly, operating_width=5.0, num_passes=2)

    print(f"\nField boundary: {field_poly.bounds}")
    print(f"Inner boundary: {headland.inner_boundary.bounds}")
    print(f"Inner boundary coords: {list(headland.inner_boundary.exterior.coords)[:5]}...")

    # Create obstacle well inside the field body (should be Type D)
    # Place it at center: (50, 40) with size 15x15
    obstacle_interior = [(45, 35), (60, 35), (60, 50), (45, 50)]

    # Create obstacle near boundary (should be Type B)
    obstacle_boundary = [(5, 5), (15, 5), (15, 15), (5, 15)]

    obstacles = [obstacle_interior, obstacle_boundary]

    # Classify
    classified = classify_all_obstacles(
        obstacle_boundaries=obstacles,
        field_inner_boundary=headland.inner_boundary,
        driving_direction_degrees=0.0,
        operating_width=5.0,
        threshold=5.0,
    )

    print("\nClassification results:")
    for i, obs in enumerate(classified):
        print(f"  Obstacle {obs.index}: {obs.obstacle_type.name}")
        poly = Polygon(obstacles[obs.index])
        is_type_b = classify_obstacle_type_b(poly, headland.inner_boundary)
        print(f"    Intersects inner boundary: {is_type_b}")
        print(f"    Distance to inner boundary: {poly.distance(headland.inner_boundary):.2f}")

    # Get Type D obstacles
    type_d = get_type_d_obstacles(classified)
    print(f"\nType D obstacles: {len(type_d)}")

    # We should have at least one Type D (the interior one)
    assert len(type_d) >= 1, "Should have at least one Type D obstacle"


def test_isolated_obstacle_far_from_boundary():
    """Test obstacle that is definitely far from boundary."""
    # Large field
    field_boundary = [(0, 0), (200, 0), (200, 200), (0, 200)]
    _ = Field(boundary=field_boundary, obstacles=[])  # For reference

    field_poly = Polygon(field_boundary)

    # Headland: 2 passes, 10m width each = 20m total
    headland = generate_field_headland(
        field_boundary=field_poly, operating_width=10.0, num_passes=2
    )

    print("\nLarge field test:")
    print(f"Field boundary: {field_poly.bounds}")
    print(f"Inner boundary: {headland.inner_boundary.bounds}")

    # Obstacle right in the center
    center_x, center_y = 100, 100
    obstacle_size = 20
    obstacle_center = [
        (center_x - obstacle_size / 2, center_y - obstacle_size / 2),
        (center_x + obstacle_size / 2, center_y - obstacle_size / 2),
        (center_x + obstacle_size / 2, center_y + obstacle_size / 2),
        (center_x - obstacle_size / 2, center_y + obstacle_size / 2),
    ]

    obstacles = [obstacle_center]

    classified = classify_all_obstacles(
        obstacle_boundaries=obstacles,
        field_inner_boundary=headland.inner_boundary,
        driving_direction_degrees=0.0,
        operating_width=10.0,
        threshold=10.0,
    )

    print(f"Classification: {[obs.obstacle_type.name for obs in classified]}")

    type_d = get_type_d_obstacles(classified)
    print(f"Type D obstacles: {len(type_d)}")

    assert len(type_d) == 1, "Center obstacle should be Type D"


def test_all_obstacle_types():
    """Test that we can generate all 4 types of obstacles."""
    # Large field
    field_boundary = [(0, 0), (200, 0), (200, 150), (0, 150)]
    field_poly = Polygon(field_boundary)

    headland = generate_field_headland(
        field_boundary=field_poly, operating_width=10.0, num_passes=2
    )

    print("\nAll types test:")
    print(f"Inner boundary bounds: {headland.inner_boundary.bounds}")

    obstacles = [
        # Type A: Small obstacle (< threshold perpendicular to driving direction)
        [(100, 75), (102, 75), (102, 76), (100, 76)],  # Only 1m tall
        # Type B: Near/touching boundary
        [(15, 15), (25, 15), (25, 25), (15, 25)],
        # Type D: Interior obstacle
        [(100, 75), (115, 75), (115, 90), (100, 90)],
        # Type C candidates: Two close obstacles
        [(150, 60), (160, 60), (160, 70), (150, 70)],
        [(162, 60), (172, 60), (172, 70), (162, 70)],  # 2m apart
    ]

    classified = classify_all_obstacles(
        obstacle_boundaries=obstacles,
        field_inner_boundary=headland.inner_boundary,
        driving_direction_degrees=0.0,
        operating_width=10.0,
        threshold=5.0,
    )

    print(f"\nClassified {len(classified)} obstacles:")
    for obs in classified:
        print(f"  {obs}")

    # Count by type
    from src.data.obstacle import ObstacleType

    type_counts = {t: 0 for t in ObstacleType}
    for obs in classified:
        type_counts[obs.obstacle_type] += 1

    print("\nCounts by type:")
    for t, count in type_counts.items():
        if count > 0:
            print(f"  {t.name}: {count}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
