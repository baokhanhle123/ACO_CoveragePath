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

from typing import List, Optional, Tuple
import json
import os

import numpy as np
from shapely import affinity
from shapely.geometry import LineString, MultiPolygon, Polygon

from ..data.block import Block

# #region agent log
LOG_PATH = "/home/khanhle/ACO_CoveragePath/.cursor/debug.log"
# #endregion


def find_critical_points(
    inner_boundary: Polygon,
    obstacles: List[Polygon],
    driving_direction_degrees: float,
    type_b_obstacles: Optional[List[Polygon]] = None,
) -> List[float]:
    """
    Find critical points along the sweep direction.

    Critical points occur where:
    - Obstacle vertices align with sweep line (connectivity changes)
    - Sweep line enters/exits obstacle regions
    - Type B obstacle vertices (even if incorporated into inner boundary)

    Algorithm:
    1. Rotate field and obstacles to align driving direction horizontally (East)
    2. Project all obstacle vertices onto sweep axis (perpendicular to driving dir)
    3. Include Type B obstacle vertices (they still create connectivity changes)
    4. Sort and deduplicate critical y-coordinates

    Args:
        inner_boundary: Field inner boundary polygon
        obstacles: List of Type D obstacle polygons
        driving_direction_degrees: Driving direction angle
        type_b_obstacles: Optional list of Type B obstacle polygons (for critical points)

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

    # #region agent log
    try:
        with open(LOG_PATH, "a") as f:
            log_entry = {
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": "A",
                "location": "boustrophedon.py:find_critical_points:entry",
                "message": "Finding critical points",
                "data": {
                    "num_obstacles": len(obstacles),
                    "num_type_b_obstacles": len(type_b_obstacles) if type_b_obstacles else 0,
                    "inner_boundary_num_interiors": len(inner_boundary.interiors),
                    "inner_boundary_bounds": list(inner_boundary.bounds),
                },
                "timestamp": int(os.times().elapsed * 1000),
            }
            f.write(json.dumps(log_entry) + "\n")
    except Exception:
        pass
    # #endregion

    # Collect critical y-coordinates (sweep is perpendicular to driving direction)
    critical_y = []

    # Add field boundary y-coordinates (bottom and top extents)
    bounds = rotated_boundary.bounds  # (minx, miny, maxx, maxy)
    critical_y.append(bounds[1])  # Bottom boundary
    critical_y.append(bounds[3])  # Top boundary

    # Add all Type D obstacle vertex y-coordinates
    for obs in rotated_obstacles:
        coords = list(obs.exterior.coords[:-1])  # Exclude duplicate last point
        for x, y in coords:
            critical_y.append(y)

    # FIX: Add Type B obstacle vertex y-coordinates
    # Type B obstacles are incorporated into inner boundary but still create
    # connectivity changes at their boundaries (top/bottom edges)
    type_b_vertices_y = []
    if type_b_obstacles:
        rotated_type_b = [rotate_geometry(obs, rotation_angle) for obs in type_b_obstacles]
        for obs in rotated_type_b:
            coords = list(obs.exterior.coords[:-1])  # Exclude duplicate last point
            for x, y in coords:
                type_b_vertices_y.append(y)
                critical_y.append(y)

    # #region agent log
    try:
        with open(LOG_PATH, "a") as f:
            log_entry = {
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": "A",
                "location": "boustrophedon.py:find_critical_points:after_type_b",
                "message": "Critical Y after adding Type B obstacle vertices",
                "data": {
                    "type_b_vertices_y": [float(y) for y in type_b_vertices_y],
                    "critical_y_after_type_b": [float(y) for y in critical_y],
                },
                "timestamp": int(os.times().elapsed * 1000),
            }
            f.write(json.dumps(log_entry) + "\n")
    except Exception:
        pass
    # #endregion

    # #region agent log
    # HYPOTHESIS A: Missing Type B hole vertices from inner_boundary.interiors
    hole_vertices_y = []
    for interior in rotated_boundary.interiors:
        coords = list(interior.coords[:-1])  # Exclude duplicate last point
        for x, y in coords:
            hole_vertices_y.append(y)
    try:
        with open(LOG_PATH, "a") as f:
            log_entry = {
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": "A",
                "location": "boustrophedon.py:find_critical_points:before_hole_vertices",
                "message": "Critical Y before adding Type B hole vertices",
                "data": {
                    "critical_y_before_holes": [float(y) for y in critical_y],
                    "num_interiors": len(rotated_boundary.interiors),
                    "hole_vertices_y_found": [float(y) for y in hole_vertices_y],
                },
                "timestamp": int(os.times().elapsed * 1000),
            }
            f.write(json.dumps(log_entry) + "\n")
    except Exception:
        pass
    # #endregion

    # Also add Type B hole vertices from inner_boundary.interiors (if any)
    for interior in rotated_boundary.interiors:
        coords = list(interior.coords[:-1])  # Exclude duplicate last point
        for x, y in coords:
            critical_y.append(y)

    # Sort and remove duplicates (with small tolerance for floating point)
    critical_y = sorted(set(np.round(critical_y, decimals=6)))

    # #region agent log
    try:
        with open(LOG_PATH, "a") as f:
            log_entry = {
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": "A",
                "location": "boustrophedon.py:find_critical_points:exit",
                "message": "Final critical Y coordinates",
                "data": {
                    "final_critical_y": [float(y) for y in critical_y],
                    "num_critical_points": len(critical_y),
                },
                "timestamp": int(os.times().elapsed * 1000),
            }
            f.write(json.dumps(log_entry) + "\n")
    except Exception:
        pass
    # #endregion

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
    type_b_obstacles: Optional[List[Polygon]] = None,
) -> List[Polygon]:
    """
    Compute obstacle-free polygons in a horizontal slice.

    Creates a rectangular slice (parallel to driving direction) and subtracts
    all obstacle regions, resulting in one or more obstacle-free cells.

    Args:
        inner_boundary: Field inner boundary
        obstacles: List of Type D obstacles
        y_bottom: Bottom boundary of slice
        y_top: Top boundary of slice
        x_min: Left boundary
        x_max: Right boundary
        type_b_obstacles: Optional list of Type B obstacles (still physically exist)

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

    # #region agent log
    try:
        with open(LOG_PATH, "a") as f:
            log_entry = {
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": "C",
                "location": "boustrophedon.py:compute_slice_polygons:after_intersection",
                "message": "Slice region after intersection with inner_boundary",
                "data": {
                    "y_bottom": float(y_bottom),
                    "y_top": float(y_top),
                    "slice_region_type": type(slice_region).__name__,
                    "num_slice_pieces": len(slice_pieces),
                    "slice_piece_areas": [float(p.area) for p in slice_pieces],
                    "slice_piece_bounds": [[float(b) for b in p.bounds] for p in slice_pieces],
                },
                "timestamp": int(os.times().elapsed * 1000),
            }
            f.write(json.dumps(log_entry) + "\n")
    except Exception:
        pass
    # #endregion

    # Subtract Type D obstacles from EACH piece independently
    all_results = []
    for piece in slice_pieces:
        result = piece
        for obstacle in obstacles:
            if result.is_empty:
                break
            if obstacle.intersects(piece):
                result = result.difference(obstacle)

        # Also subtract Type B obstacles (they still physically exist)
        if type_b_obstacles:
            for type_b_obs in type_b_obstacles:
                if result.is_empty:
                    break
                if type_b_obs.intersects(piece):
                    result = result.difference(type_b_obs)

        if not result.is_empty:
            # Handle MultiPolygon from obstacle subtraction
            if isinstance(result, MultiPolygon):
                all_results.extend([p for p in result.geoms if not p.is_empty and p.area > 1e-6])
            elif isinstance(result, Polygon) and result.area > 1e-6:
                all_results.append(result)

    # #region agent log
    try:
        with open(LOG_PATH, "a") as f:
            log_entry = {
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": "C",
                "location": "boustrophedon.py:compute_slice_polygons:after_obstacle_subtraction",
                "message": "Results after subtracting Type D obstacles",
                "data": {
                    "y_bottom": float(y_bottom),
                    "y_top": float(y_top),
                    "num_results": len(all_results),
                    "result_areas": [float(p.area) for p in all_results],
                    "result_bounds": [[float(b) for b in p.bounds] for p in all_results],
                },
                "timestamp": int(os.times().elapsed * 1000),
            }
            f.write(json.dumps(log_entry) + "\n")
    except Exception:
        pass
    # #endregion

    # Clean up invalid geometries (same as before)
    cleaned_polygons = []
    for poly in all_results:
        if not poly.is_valid:
            poly = poly.buffer(0)  # Fix invalid geometry
        if poly.is_valid and not poly.is_empty and poly.area > 1e-6:
            cleaned_polygons.append(poly)

    # #region agent log
    try:
        with open(LOG_PATH, "a") as f:
            log_entry = {
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": "E",
                "location": "boustrophedon.py:compute_slice_polygons:exit",
                "message": "Final cleaned polygons",
                "data": {
                    "y_bottom": float(y_bottom),
                    "y_top": float(y_top),
                    "num_cleaned": len(cleaned_polygons),
                    "cleaned_areas": [float(p.area) for p in cleaned_polygons],
                    "cleaned_bounds": [[float(b) for b in p.bounds] for p in cleaned_polygons],
                },
                "timestamp": int(os.times().elapsed * 1000),
            }
            f.write(json.dumps(log_entry) + "\n")
    except Exception:
        pass
    # #endregion

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
    type_b_obstacles: Optional[List[Polygon]] = None,
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
        type_b_obstacles: Optional list of Type B obstacle polygons (for critical points)

    Returns:
        List of preliminary Block objects (before merging)

    Notes:
        - Blocks at this stage may be very narrow
        - Block merging (next step) will combine adjacent blocks
        - Each block should be obstacle-free and convex
        - Type B obstacles are incorporated into inner boundary but still create
          connectivity changes that require critical points
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
    # Include Type B obstacles to capture connectivity changes at their boundaries
    critical_points = find_critical_points(
        inner_boundary, obstacles, driving_direction_degrees, type_b_obstacles=type_b_obstacles
    )

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

        # #region agent log
        try:
            with open(LOG_PATH, "a") as f:
                log_entry = {
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "B",
                    "location": "boustrophedon.py:boustrophedon_decomposition:slice",
                    "message": "Creating slice",
                    "data": {
                        "slice_index": i,
                        "y_bottom": float(y_bottom),
                        "y_top": float(y_top),
                        "slice_height": float(y_top - y_bottom),
                    },
                    "timestamp": int(os.times().elapsed * 1000),
                }
                f.write(json.dumps(log_entry) + "\n")
        except Exception:
            pass
        # #endregion

        # Compute obstacle-free cells in this horizontal slice
        rotated_type_b = (
            [rotate_geometry(obs, rotation_angle) for obs in type_b_obstacles]
            if type_b_obstacles
            else None
        )
        slice_polygons = compute_slice_polygons(
            rotated_boundary, rotated_obstacles, y_bottom, y_top, x_min, x_max, rotated_type_b
        )

        # #region agent log
        try:
            with open(LOG_PATH, "a") as f:
                log_entry = {
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "B",
                    "location": "boustrophedon.py:boustrophedon_decomposition:slice_result",
                    "message": "Slice polygons created",
                    "data": {
                        "slice_index": i,
                        "y_bottom": float(y_bottom),
                        "y_top": float(y_top),
                        "num_polygons": len(slice_polygons),
                        "polygon_areas": [float(p.area) for p in slice_polygons],
                        "polygon_bounds": [[float(b) for b in p.bounds] for p in slice_polygons],
                    },
                    "timestamp": int(os.times().elapsed * 1000),
                }
                f.write(json.dumps(log_entry) + "\n")
        except Exception:
            pass
        # #endregion

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

    # #region agent log
    try:
        with open(LOG_PATH, "a") as f:
            log_entry = {
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": "D",
                "location": "boustrophedon.py:boustrophedon_decomposition:before_subdivision",
                "message": "Blocks before convex subdivision",
                "data": {
                    "num_blocks": len(blocks),
                    "block_areas": [float(b.area) for b in blocks],
                    "block_bounds": [[float(bnd) for bnd in b.polygon.bounds] for b in blocks],
                },
                "timestamp": int(os.times().elapsed * 1000),
            }
            f.write(json.dumps(log_entry) + "\n")
    except Exception:
        pass
    # #endregion

    # 8. Subdivide non-convex blocks (Type B obstacle holes)
    from .convex_subdivision import subdivide_all_non_convex_blocks

    blocks = subdivide_all_non_convex_blocks(
        blocks=blocks,
        driving_direction_degrees=driving_direction_degrees,
        inner_boundary=inner_boundary,
    )

    # #region agent log
    try:
        with open(LOG_PATH, "a") as f:
            log_entry = {
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": "D",
                "location": "boustrophedon.py:boustrophedon_decomposition:after_subdivision",
                "message": "Blocks after convex subdivision",
                "data": {
                    "num_blocks": len(blocks),
                    "block_areas": [float(b.area) for b in blocks],
                    "block_bounds": [[float(bnd) for bnd in b.polygon.bounds] for b in blocks],
                },
                "timestamp": int(os.times().elapsed * 1000),
            }
            f.write(json.dumps(log_entry) + "\n")
    except Exception:
        pass
    # #endregion

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
