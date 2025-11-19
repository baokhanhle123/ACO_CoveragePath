"""
Basic functionality tests to verify imports and data structures work.
"""

import pytest
from shapely.geometry import Polygon

from src.data import Field, FieldParameters, create_rectangular_field
from src.geometry import generate_field_headland, generate_parallel_tracks
from src.obstacles.classifier import classify_obstacle_type_a


def test_field_creation():
    """Test basic field creation."""
    field = create_rectangular_field(100, 80, name="Test Field")

    assert field.name == "Test Field"
    assert field.area > 0
    assert len(field.boundary) == 4
    assert field.get_num_obstacles() == 0


def test_field_with_obstacles():
    """Test field with rectangular obstacles."""
    obstacles = [[(20, 20), (30, 20), (30, 30), (20, 30)], [(60, 60), (70, 60), (70, 70), (60, 70)]]

    field = Field(
        boundary=[(0, 0), (100, 0), (100, 100), (0, 100)],
        obstacles=obstacles,
        name="Field with obstacles",
    )

    assert field.get_num_obstacles() == 2
    assert field.area < 10000  # Less than full area due to obstacles


def test_field_parameters():
    """Test field parameters validation."""
    params = FieldParameters(
        operating_width=5.0,
        turning_radius=3.0,
        num_headland_passes=2,
        driving_direction=0.0,
        obstacle_threshold=5.0,
    )

    assert params.operating_width == 5.0
    assert params.turning_radius == 3.0

    # Test invalid parameters
    with pytest.raises(ValueError):
        FieldParameters(
            operating_width=-1.0,  # Invalid
            turning_radius=3.0,
            num_headland_passes=2,
            driving_direction=0.0,
            obstacle_threshold=5.0,
        )


def test_headland_generation():
    """Test headland generation."""
    field = create_rectangular_field(100, 80)
    boundary_poly = field.boundary_polygon

    result = generate_field_headland(
        field_boundary=boundary_poly, operating_width=5.0, num_passes=2
    )

    assert result is not None
    assert len(result.passes) == 2
    assert result.inner_boundary.area < boundary_poly.area


def test_track_generation():
    """Test parallel track generation."""
    field = create_rectangular_field(100, 80)

    # Generate headland first
    headland_result = generate_field_headland(
        field_boundary=field.boundary_polygon, operating_width=5.0, num_passes=1
    )

    # Generate tracks
    tracks = generate_parallel_tracks(
        inner_boundary=headland_result.inner_boundary,
        driving_direction_degrees=0.0,
        operating_width=5.0,
    )

    assert len(tracks) > 0
    assert all(track.length > 0 for track in tracks)


def test_obstacle_classification_type_a():
    """Test Type A obstacle classification."""
    # Small obstacle (should be Type A)
    small_obs = Polygon([(0, 0), (2, 0), (2, 2), (0, 2)])

    is_type_a = classify_obstacle_type_a(
        obstacle_polygon=small_obs, driving_direction_degrees=0.0, threshold=5.0
    )

    assert is_type_a

    # Large obstacle (should not be Type A)
    large_obs = Polygon([(0, 0), (20, 0), (20, 20), (0, 20)])

    is_type_a = classify_obstacle_type_a(
        obstacle_polygon=large_obs, driving_direction_degrees=0.0, threshold=5.0
    )

    assert not is_type_a


def test_imports():
    """Test that all modules can be imported."""
    import src.data
    import src.geometry
    import src.obstacles

    assert hasattr(src.data, "Field")
    assert hasattr(src.geometry, "generate_field_headland")
    assert hasattr(src.obstacles.classifier, "classify_all_obstacles")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
