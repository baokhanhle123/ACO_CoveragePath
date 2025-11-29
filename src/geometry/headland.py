"""
Headland generation for field and obstacles.

Implements Stage 1 headland generation from Zhou et al. 2014.
"""

from dataclasses import dataclass
from typing import List, Optional, Tuple

from shapely.geometry import MultiPolygon, Polygon

from .polygon import offset_polygon


@dataclass
class HeadlandResult:
    """
    Result of headland generation.

    Attributes:
        passes: List of headland passes (outer to inner)
        inner_boundary: Inner boundary between headland and field body
        total_width: Total headland width
    """

    passes: List[Polygon]
    inner_boundary: Polygon
    total_width: float


def generate_field_headland(
    field_boundary: Polygon,
    operating_width: float,
    num_passes: int,
    type_b_obstacles: Optional[List[Polygon]] = None,
) -> Optional[HeadlandResult]:
    """
    Generate headland area for the main field.

    According to the paper:
    - Distance from field boundary to first pass: w/2
    - Distance between subsequent passes: w
    - Inner boundary: w/2 from last pass
    - Type B obstacles are incorporated into the inner boundary (removed from field body)

    Args:
        field_boundary: Field boundary polygon
        operating_width: Operating width of implement (w)
        num_passes: Number of headland passes (h)
        type_b_obstacles: List of Type B obstacle polygons to incorporate into inner boundary

    Returns:
        HeadlandResult with passes and inner boundary, or None if generation fails
    """
    if num_passes == 0:
        # No headland, inner boundary is same as field boundary
        return HeadlandResult(passes=[], inner_boundary=field_boundary, total_width=0.0)

    w = operating_width
    passes = []

    # Generate first headland pass (offset inward by w/2)
    current_boundary = field_boundary
    first_pass = offset_polygon(current_boundary, w / 2, inward=True)

    if first_pass is None:
        print("Warning: Failed to generate first headland pass")
        return None

    passes.append(first_pass)
    current_boundary = first_pass

    # Generate subsequent passes (offset by w each)
    for i in range(1, num_passes):
        next_pass = offset_polygon(current_boundary, w, inward=True)

        if next_pass is None:
            print(f"Warning: Failed to generate headland pass {i + 1}")
            break

        passes.append(next_pass)
        current_boundary = next_pass

    # Generate inner boundary (offset last pass inward by w/2)
    inner_boundary = offset_polygon(current_boundary, w / 2, inward=True)

    if inner_boundary is None:
        print("Warning: Failed to generate inner boundary")
        # Use last pass as inner boundary
        inner_boundary = current_boundary

    # Incorporate Type B obstacles into inner boundary (remove them from field body)
    # According to paper: "Type B obstacles are incorporated into the inner boundary of the field"
    if type_b_obstacles:
        for type_b_obs in type_b_obstacles:
            try:
                # Subtract Type B obstacle from inner boundary
                inner_boundary = inner_boundary.difference(type_b_obs)

                # Handle MultiPolygon result (take largest piece)
                if isinstance(inner_boundary, MultiPolygon):
                    inner_boundary = max(inner_boundary.geoms, key=lambda p: p.area)

            except Exception as e:
                print(f"Warning: Failed to incorporate Type B obstacle into inner boundary: {e}")

    total_width = num_passes * w

    return HeadlandResult(passes=passes, inner_boundary=inner_boundary, total_width=total_width)


def generate_obstacle_headland(
    obstacle_boundary: Polygon, operating_width: float, num_passes: int
) -> Optional[HeadlandResult]:
    """
    Generate headland area around an obstacle.

    Similar to field headland, but offset is OUTWARD.

    Args:
        obstacle_boundary: Obstacle boundary polygon
        operating_width: Operating width (w)
        num_passes: Number of headland passes

    Returns:
        HeadlandResult with passes and outer boundary
    """
    if num_passes == 0:
        return HeadlandResult(
            passes=[], inner_boundary=obstacle_boundary, total_width=0.0  # No expansion
        )

    w = operating_width
    passes = []

    # Generate first headland pass (offset outward by w/2)
    current_boundary = obstacle_boundary
    first_pass = offset_polygon(current_boundary, w / 2, inward=False)

    if first_pass is None:
        print("Warning: Failed to generate obstacle headland pass 1")
        return None

    passes.append(first_pass)
    current_boundary = first_pass

    # Generate subsequent passes (offset outward by w each)
    for i in range(1, num_passes):
        next_pass = offset_polygon(current_boundary, w, inward=False)

        if next_pass is None:
            print(f"Warning: Failed to generate obstacle headland pass {i + 1}")
            break

        passes.append(next_pass)
        current_boundary = next_pass

    # Outer boundary (offset last pass outward by w/2)
    outer_boundary = offset_polygon(current_boundary, w / 2, inward=False)

    if outer_boundary is None:
        print("Warning: Failed to generate obstacle outer boundary")
        outer_boundary = current_boundary

    total_width = num_passes * w

    return HeadlandResult(
        passes=passes,
        inner_boundary=outer_boundary,  # For obstacles, "inner" is actually outer
        total_width=total_width,
    )


def get_headland_path_coordinates(
    headland_result: HeadlandResult,
) -> List[List[Tuple[float, float]]]:
    """
    Extract coordinates of all headland passes for visualization/export.

    Args:
        headland_result: Result from generate_field_headland or generate_obstacle_headland

    Returns:
        List of coordinate lists, one for each pass
    """
    paths = []
    for pass_polygon in headland_result.passes:
        coords = list(pass_polygon.exterior.coords)
        paths.append(coords)
    return paths


def calculate_headland_area(headland_result: HeadlandResult, original_boundary: Polygon) -> float:
    """
    Calculate total headland area.

    Args:
        headland_result: Headland generation result
        original_boundary: Original field/obstacle boundary

    Returns:
        Total headland area in square meters
    """
    headland_area = original_boundary.area - headland_result.inner_boundary.area
    return max(0.0, headland_area)  # Ensure non-negative
