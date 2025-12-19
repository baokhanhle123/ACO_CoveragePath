"""
Boustrophedon cellular decomposition for coverage path planning.

Implements the *second stage* decomposition algorithm from Zhou et al. 2014
([`10.1016/j.compag.2014.08.013`](http://dx.doi.org/10.1016/j.compag.2014.08.013)),
Section 2.3:

- Slice lines are parallel to the driving direction θ
- Sweep movement is perpendicular to the driving direction θ
- Identifies critical points where connectivity of the free space changes
- Creates obstacle-free cells (preliminary blocks) between consecutive
  critical points, as illustrated in the figures of Section 2.3.1.

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
    1. Rotate field and obstacles to align driving direction horizontally (East)
    2. Project all obstacle vertices onto sweep axis (perpendicular to driving dir)
    3. Sort and deduplicate critical y-coordinates

    Args:
        inner_boundary: Field inner boundary polygon
        obstacles: List of obstacle polygons
        driving_direction_degrees: Driving direction angle

    Returns:
        Sorted list of critical y-coordinates in rotated coordinate system
    """
    # Rotate to align driving direction horizontally (East)
    # We rotate by -angle to make driving direction point East (0°)
    # After rotation, sweep lines are horizontal, sweeping vertically
    rotation_angle = -driving_direction_degrees

    # Rotate field boundary
    rotated_boundary = rotate_geometry(inner_boundary, rotation_angle)

    # Rotate obstacles
    rotated_obstacles = [rotate_geometry(obs, rotation_angle) for obs in obstacles]

    # Collect critical y-coordinates (sweep is perpendicular to driving direction)
    critical_y = []

    # Add field boundary y-coordinates (bottom and top extents)
    bounds = rotated_boundary.bounds  # (minx, miny, maxx, maxy)
    critical_y.append(bounds[1])  # Bottom boundary
    critical_y.append(bounds[3])  # Top boundary

    # Add all obstacle vertex y-coordinates
    for obs in rotated_obstacles:
        coords = list(obs.exterior.coords[:-1])  # Exclude duplicate last point
        for x, y in coords:
            critical_y.append(y)

    # Sort and remove duplicates (with small tolerance for floating point)
    critical_y = sorted(set(np.round(critical_y, decimals=6)))

    return critical_y


def create_sweep_line(y_coord: float, x_min: float, x_max: float) -> LineString:
    """
    Create a horizontal sweep line at given y-coordinate.

    The sweep line is parallel to the driving direction (after rotation to East).

    Args:
        y_coord: Y-coordinate for sweep line
        x_min: Minimum X value (left)
        x_max: Maximum X value (right)

    Returns:
        Horizontal LineString representing sweep line (parallel to driving direction)
    """
    return LineString([(x_min, y_coord), (x_max, y_coord)])


def compute_slice_polygons(
    inner_boundary: Polygon,
    obstacles: List[Polygon],
    y_bottom: float,
    y_top: float,
    x_min: float,
    x_max: float,
) -> List[Polygon]:
    """
    Compute obstacle-free polygons in a horizontal slice.

    Creates a rectangular slice (parallel to driving direction) and subtracts
    all obstacle regions, resulting in one or more obstacle-free cells.

    Args:
        inner_boundary: Field inner boundary
        obstacles: List of obstacles
        y_bottom: Bottom boundary of slice
        y_top: Top boundary of slice
        x_min: Left boundary
        x_max: Right boundary

    Returns:
        List of obstacle-free polygon cells in this slice
    """
    # Create rectangular slice (horizontal, parallel to driving direction after rotation)
    slice_box = Polygon([
        (x_min, y_bottom),
        (x_max, y_bottom),
        (x_max, y_top),
        (x_min, y_top),
    ])

    # Intersect slice with field boundary
    slice_region = slice_box.intersection(inner_boundary)

    # Handle empty intersection
    if slice_region.is_empty:
        return []

    # Handle MultiPolygon from Type B holes in inner_boundary
    # Keep ALL pieces - Type B holes can split slices into multiple regions
    if isinstance(slice_region, MultiPolygon):
        slice_pieces = [p for p in slice_region.geoms if not p.is_empty and p.area > 1e-6]
    else:
        slice_pieces = [slice_region] if not slice_region.is_empty else []

    # Subtract Type D obstacles from EACH piece independently
    all_results = []
    for piece in slice_pieces:
        result = piece
        for obstacle in obstacles:
            if result.is_empty:
                break
            if obstacle.intersects(piece):
                result = result.difference(obstacle)

        if not result.is_empty:
            # Handle MultiPolygon from obstacle subtraction
            if isinstance(result, MultiPolygon):
                all_results.extend([p for p in result.geoms if not p.is_empty and p.area > 1e-6])
            elif isinstance(result, Polygon) and result.area > 1e-6:
                all_results.append(result)

    # Clean up invalid geometries (same as before)
    cleaned_polygons = []
    for poly in all_results:
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

    # 2. Rotate geometry to align driving direction horizontally (East)
    rotation_angle = -driving_direction_degrees
    rotated_boundary = rotate_geometry(inner_boundary, rotation_angle)
    rotated_obstacles = [rotate_geometry(obs, rotation_angle) for obs in obstacles]

    # 3. Get bounding box to determine sweep range
    bounds = rotated_boundary.bounds  # (minx, miny, maxx, maxy)
    x_min, x_max = bounds[0], bounds[2]

    # 4. Find critical points (Y-coordinates for horizontal slices)
    critical_points = find_critical_points(inner_boundary, obstacles, driving_direction_degrees)

    if len(critical_points) < 2:
        # Field too small or degenerate
        return []

    # 5. Create horizontal slices between consecutive critical Y-coordinates
    block_polygons_rotated = []

    for i in range(len(critical_points) - 1):
        y_bottom = critical_points[i]
        y_top = critical_points[i + 1]

        # Skip zero-height slices
        if abs(y_top - y_bottom) < 1e-6:
            continue

        # Compute obstacle-free cells in this horizontal slice
        slice_polygons = compute_slice_polygons(
            rotated_boundary, rotated_obstacles, y_bottom, y_top, x_min, x_max
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

    # 8. Subdivide non-convex blocks (Type B obstacle holes)
    from .convex_subdivision import subdivide_all_non_convex_blocks

    blocks = subdivide_all_non_convex_blocks(
        blocks=blocks,
        driving_direction_degrees=driving_direction_degrees,
        inner_boundary=inner_boundary,
    )

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
