"""
Boustrophedon cellular decomposition for coverage path planning.

Implements the decomposition algorithm from Zhou et al. 2014 (Section 2.3):
- Sweeps perpendicular to driving direction
- Identifies critical points where connectivity changes
- Creates obstacle-free cells (preliminary blocks)

Reference:
    Zhou, K., Jensen, A. L., Sørensen, C. G., Busato, P., & Bothtis, D. D. (2014).
    Agricultural operations planning in fields with multiple obstacle areas.
    Computers and Electronics in Agriculture, 109, 12-22.
"""

from typing import List, Tuple

import numpy as np
from shapely.geometry import LineString, Polygon

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
    # TODO: Implement critical point detection
    # 1. Rotate geometry to align sweep with Y-axis
    # 2. Extract all obstacle vertex x-coordinates
    # 3. Add field boundary intersection points
    # 4. Sort and return unique critical points
    raise NotImplementedError("Critical point detection not yet implemented")


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
    # TODO: Implement slice polygon computation
    # 1. Create rectangular slice [x_left, x_right] × [y_min, y_max]
    # 2. Intersect with field inner boundary
    # 3. Subtract all obstacles that intersect this slice
    # 4. Handle multi-polygon results (split by obstacles)
    raise NotImplementedError("Slice polygon computation not yet implemented")


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
    # TODO: Implement geometry rotation
    # Use shapely affinity.rotate or manual transformation
    raise NotImplementedError("Geometry rotation not yet implemented")


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
    # TODO: Implement main boustrophedon algorithm
    # Main steps:
    # 1. Validate inputs (non-empty field, valid obstacles)
    # 2. Rotate field and obstacles to align with sweep direction
    # 3. Get field bounding box to determine sweep range
    # 4. Find all critical points
    # 5. For each pair of consecutive critical points:
    #    a. Create vertical slice
    #    b. Compute obstacle-free polygons in slice
    #    c. Create Block object for each polygon
    # 6. Rotate blocks back to original orientation
    # 7. Assign preliminary block IDs
    # 8. Return list of blocks

    raise NotImplementedError("Boustrophedon decomposition not yet implemented")


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
