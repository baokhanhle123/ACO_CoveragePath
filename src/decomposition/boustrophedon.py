"""
Boustrophedon cellular decomposition for coverage path planning.

Implements the *second stage* decomposition algorithm from Zhou et al. 2014
([`10.1016/j.compag.2014.08.013`](http://dx.doi.org/10.1016/j.compag.2014.08.013)),
Section 2.3:

- Sweeps perpendicular to the driving direction θ
- Identifies critical points where connectivity of the free space changes
- Creates obstacle-free cells (preliminary blocks) between consecutive
  critical points, as illustrated in the figures of Section 2.3.

This module corresponds conceptually to the boustrophedon decomposition
step that transforms the field body (inner boundary minus Type B obstacles
from Stage 1) and Type D obstacles into a set of obstacle-free blocks
prior to block merging and track clustering.
"""

from typing import List, Tuple

import numpy as np
from shapely import affinity
from shapely.geometry import LineString, MultiPolygon, Polygon

from ..data.block import Block


def find_critical_points(
    inner_boundary: Polygon,
    obstacles: List[Polygon],
    driving_direction_degrees: float,
) -> List[float]:
    """
    Find critical points along the sweep direction.

    Critical points occur where:
    - Obstacle vertices align with sweep line (connectivity changes)
    - Sweep line enters/exits obstacle regions

    Algorithm:
    1. Rotate field and obstacles to align with sweep direction (vertical)
    2. Project all obstacle vertices onto sweep axis
    3. Sort and deduplicate critical x-coordinates

    Args:
        inner_boundary: Field inner boundary polygon
        obstacles: List of obstacle polygons
        driving_direction_degrees: Driving direction angle

    Returns:
        Sorted list of critical x-coordinates in rotated coordinate system
    """
    # Rotate to align driving direction horizontally (sweep vertically)
    # We rotate by -angle to make driving direction point East (0°)
    rotation_angle = -driving_direction_degrees

    # Rotate field boundary
    rotated_boundary = rotate_geometry(inner_boundary, rotation_angle)

    # Rotate obstacles
    rotated_obstacles = [rotate_geometry(obs, rotation_angle) for obs in obstacles]

    # Collect critical x-coordinates
    critical_x = []

    # Add field boundary x-coordinates (left and right extents)
    bounds = rotated_boundary.bounds  # (minx, miny, maxx, maxy)
    critical_x.append(bounds[0])  # Left boundary
    critical_x.append(bounds[2])  # Right boundary

    # Add all obstacle vertex x-coordinates
    for obs in rotated_obstacles:
        coords = list(obs.exterior.coords[:-1])  # Exclude duplicate last point
        for x, y in coords:
            critical_x.append(x)

    # Sort and remove duplicates (with small tolerance for floating point)
    critical_x = sorted(set(np.round(critical_x, decimals=6)))

    return critical_x


def create_sweep_line(x_coord: float, y_min: float, y_max: float) -> LineString:
    """
    Create a vertical sweep line at given x-coordinate.

    Args:
        x_coord: X-coordinate for sweep line
        y_min: Minimum Y value (bottom)
        y_max: Maximum Y value (top)

    Returns:
        Vertical LineString representing sweep line
    """
    return LineString([(x_coord, y_min), (x_coord, y_max)])


def compute_slice_polygons(
    inner_boundary: Polygon,
    obstacles: List[Polygon],
    x_left: float,
    x_right: float,
    y_min: float,
    y_max: float,
) -> List[Polygon]:
    """
    Compute obstacle-free polygons in a vertical slice.

    Creates a rectangular slice and subtracts all obstacle regions,
    resulting in one or more obstacle-free cells.

    Args:
        inner_boundary: Field inner boundary
        obstacles: List of obstacles
        x_left: Left boundary of slice
        x_right: Right boundary of slice
        y_min: Bottom boundary
        y_max: Top boundary

    Returns:
        List of obstacle-free polygon cells in this slice
    """
    # Create rectangular slice
    slice_box = Polygon([
        (x_left, y_min),
        (x_right, y_min),
        (x_right, y_max),
        (x_left, y_max),
    ])

    # Intersect slice with field boundary
    slice_region = slice_box.intersection(inner_boundary)

    # Handle empty intersection
    if slice_region.is_empty:
        return []

    # Ensure we have a Polygon (not MultiPolygon from intersection)
    if isinstance(slice_region, MultiPolygon):
        # Take the largest part if multiple
        slice_region = max(slice_region.geoms, key=lambda p: p.area)

    # Subtract all obstacles that intersect this slice
    result = slice_region
    for obstacle in obstacles:
        if result.is_empty:
            break
        if obstacle.intersects(slice_region):
            result = result.difference(obstacle)

    # Handle empty result
    if result.is_empty:
        return []

    # Handle MultiPolygon results (obstacles split the slice)
    if isinstance(result, MultiPolygon):
        # Return all non-empty polygons
        polygons = [p for p in result.geoms if not p.is_empty and p.area > 1e-6]
    elif isinstance(result, Polygon):
        polygons = [result] if result.area > 1e-6 else []
    else:
        # Handle other geometry types (shouldn't happen, but be safe)
        polygons = []

    # Clean up invalid geometries
    cleaned_polygons = []
    for poly in polygons:
        if not poly.is_valid:
            poly = poly.buffer(0)  # Fix invalid geometry
        if poly.is_valid and not poly.is_empty and poly.area > 1e-6:
            cleaned_polygons.append(poly)

    return cleaned_polygons


def rotate_geometry(
    geometry: Polygon, angle_degrees: float, origin: Tuple[float, float] = (0, 0)
) -> Polygon:
    """
    Rotate geometry by given angle around origin.

    Args:
        geometry: Polygon to rotate
        angle_degrees: Rotation angle in degrees (positive = counter-clockwise)
        origin: Rotation center point

    Returns:
        Rotated polygon
    """
    return affinity.rotate(geometry, angle_degrees, origin=origin)


def boustrophedon_decomposition(
    inner_boundary: Polygon,
    obstacles: List[Polygon],
    driving_direction_degrees: float,
) -> List[Block]:
    """
    Perform boustrophedon cellular decomposition.

    Main algorithm from paper:
    1. Align field with driving direction (rotate if needed)
    2. Find critical points where connectivity changes
    3. Create sweep slices between critical points
    4. Generate obstacle-free cells in each slice
    5. Create Block objects with preliminary IDs

    Args:
        inner_boundary: Field inner boundary (after headland)
        obstacles: List of Type D obstacle polygons requiring decomposition
        driving_direction_degrees: Driving direction angle (0° = East, 90° = North)

    Returns:
        List of preliminary Block objects (before merging)

    Notes:
        - Blocks at this stage may be very narrow
        - Block merging (next step) will combine adjacent blocks
        - Each block should be obstacle-free and convex
    """
    # 1. Validate inputs
    if inner_boundary.is_empty or not inner_boundary.is_valid:
        return []

    # 2. Rotate geometry to align with sweep direction
    rotation_angle = -driving_direction_degrees
    rotated_boundary = rotate_geometry(inner_boundary, rotation_angle)
    rotated_obstacles = [rotate_geometry(obs, rotation_angle) for obs in obstacles]

    # 3. Get bounding box to determine sweep range
    bounds = rotated_boundary.bounds  # (minx, miny, maxx, maxy)
    y_min, y_max = bounds[1], bounds[3]

    # 4. Find critical points
    critical_points = find_critical_points(inner_boundary, obstacles, driving_direction_degrees)

    if len(critical_points) < 2:
        # Field too small or degenerate
        return []

    # 5. Create slices between consecutive critical points
    block_polygons_rotated = []

    for i in range(len(critical_points) - 1):
        x_left = critical_points[i]
        x_right = critical_points[i + 1]

        # Skip zero-width slices
        if abs(x_right - x_left) < 1e-6:
            continue

        # Compute obstacle-free cells in this slice
        slice_polygons = compute_slice_polygons(
            rotated_boundary, rotated_obstacles, x_left, x_right, y_min, y_max
        )

        # Add to results
        block_polygons_rotated.extend(slice_polygons)

    # 6. Rotate blocks back to original orientation
    reverse_rotation_angle = driving_direction_degrees
    block_polygons_original = [
        rotate_geometry(poly, reverse_rotation_angle) for poly in block_polygons_rotated
    ]

    # 7. Create Block objects with preliminary IDs
    blocks = []
    for block_id, poly in enumerate(block_polygons_original):
        # Get boundary coordinates
        boundary_coords = list(poly.exterior.coords[:-1])  # Exclude duplicate last point

        # Create Block
        block = Block(block_id=block_id, boundary=boundary_coords)
        blocks.append(block)

    return blocks


def get_decomposition_statistics(blocks: List[Block]) -> dict:
    """
    Calculate statistics about decomposition results.

    Args:
        blocks: List of blocks from decomposition

    Returns:
        Dictionary with statistics:
        - num_blocks: Number of blocks
        - total_area: Sum of block areas
        - avg_area: Average block area
        - min_area: Smallest block area
        - max_area: Largest block area
        - total_tracks: Sum of tracks across all blocks
    """
    if not blocks:
        return {
            "num_blocks": 0,
            "total_area": 0.0,
            "avg_area": 0.0,
            "min_area": 0.0,
            "max_area": 0.0,
            "total_tracks": 0,
        }

    areas = [block.area for block in blocks]
    track_counts = [block.num_tracks for block in blocks]

    return {
        "num_blocks": len(blocks),
        "total_area": sum(areas),
        "avg_area": np.mean(areas),
        "min_area": min(areas),
        "max_area": max(areas),
        "total_tracks": sum(track_counts),
    }
