"""
Convex subdivision for non-convex blocks created by Type B obstacle holes.

Extends the boustrophedon decomposition to handle blocks that contain Type B
obstacles (boundary-touching obstacles that create holes). When Type B obstacles
are incorporated into the inner boundary during Stage 1, they create non-convex
blocks that violate the paper's assumption of "obstacle-free convex cells".

This module subdivides non-convex blocks into multiple convex pieces using
vertical slices at Type B obstacle boundaries, ensuring all final blocks are
convex (convexity_ratio ≥ 0.99) for optimal Stage 3 ACO performance.

Algorithm:
1. Detect non-convex blocks using convex hull ratio
2. Identify Type B hole boundaries within blocks
3. Create vertical slices at critical X-coordinates
4. Subdivide non-convex blocks into convex sub-blocks
5. Preserve block numbering and area

References:
    Zhou et al. 2014, Section 2.3.1: "Decomposition of field body into blocks"
    Extension: Convex subdivision for Type B obstacle handling
"""

from typing import List, Tuple

import numpy as np
from shapely.geometry import MultiPolygon, Polygon

from ..data.block import Block
from .boustrophedon import rotate_geometry


def is_block_convex(block: Block, threshold: float = 0.99) -> bool:
    """
    Check if a block is convex using convex hull area ratio.

    A block is considered convex if the ratio of its area to its convex hull area
    is greater than or equal to the threshold. This matches the convexity check
    used in block_merger.py (line 244-250).

    Args:
        block: Block to check for convexity
        threshold: Minimum convexity ratio (default 0.99)

    Returns:
        True if block is convex (ratio ≥ threshold), False otherwise

    Examples:
        >>> # Rectangle is convex
        >>> rect_block = Block(0, [(0,0), (10,0), (10,5), (0,5)])
        >>> is_block_convex(rect_block)
        True

        >>> # L-shape is non-convex
        >>> l_block = Block(0, [(0,0), (10,0), (10,5), (5,5), (5,10), (0,10)])
        >>> is_block_convex(l_block)
        False
    """
    poly = block.polygon

    # Handle empty or invalid polygons
    if poly.is_empty or not poly.is_valid:
        return False

    # Calculate convex hull
    convex_hull = poly.convex_hull

    # Calculate convexity ratio
    if convex_hull.area < 1e-9:
        return False

    convexity_ratio = poly.area / convex_hull.area

    return convexity_ratio >= threshold


def has_interior_holes(polygon: Polygon) -> bool:
    """
    Check if a polygon has interior holes (Type B obstacle holes).

    Shapely Polygons can have interior rings representing holes. Type B obstacles
    create these holes when they're subtracted from the inner boundary during
    Stage 1 headland generation (see headland.py lines 92-105).

    Args:
        polygon: Polygon to check

    Returns:
        True if polygon has one or more interior holes, False otherwise

    Examples:
        >>> # Simple rectangle has no holes
        >>> rect = Polygon([(0,0), (10,0), (10,5), (0,5)])
        >>> has_interior_holes(rect)
        False

        >>> # Donut shape has hole
        >>> exterior = [(0,0), (10,0), (10,10), (0,10)]
        >>> interior = [(3,3), (7,3), (7,7), (3,7)]
        >>> donut = Polygon(exterior, [interior])
        >>> has_interior_holes(donut)
        True
    """
    return len(polygon.interiors) > 0


def extract_hole_vertices(polygon: Polygon) -> List[Tuple[float, float]]:
    """
    Extract all vertices from interior holes (Type B obstacles).

    Args:
        polygon: Polygon with interior holes

    Returns:
        List of (x, y) coordinates from all interior rings

    Examples:
        >>> exterior = [(0,0), (10,0), (10,10), (0,10)]
        >>> hole1 = [(2,2), (4,2), (4,4), (2,4)]
        >>> hole2 = [(6,6), (8,6), (8,8), (6,8)]
        >>> poly = Polygon(exterior, [hole1, hole2])
        >>> vertices = extract_hole_vertices(poly)
        >>> len(vertices)
        8
    """
    all_vertices = []

    for interior_ring in polygon.interiors:
        # Get coordinates, excluding duplicate last point
        coords = list(interior_ring.coords[:-1])
        all_vertices.extend(coords)

    return all_vertices


def find_critical_x_coordinates(
    block: Block,
    driving_direction_degrees: float,
    inner_boundary: Polygon,
) -> List[float]:
    """
    Find critical X-coordinates for vertical subdivision of non-convex blocks.

    For non-convex blocks (either with Type B holes or L-shaped from Type B
    obstacle subtraction), identifies X-coordinates to create vertical slices
    (perpendicular to horizontal slices in standard boustrophedon decomposition).

    Algorithm:
    1. Rotate block to align driving direction horizontally (East)
    2. If block has convexity < 0.99, extract all vertices from block boundary
    3. Collect X-coordinates from vertices
    4. Add block boundary X-coordinates (left and right)
    5. Sort and deduplicate critical X values

    Args:
        block: Block to analyze (potentially non-convex)
        driving_direction_degrees: Driving direction angle
        inner_boundary: Field inner boundary (may contain Type B holes)

    Returns:
        Sorted list of critical X-coordinates in rotated coordinate system

    Notes:
        - Returns empty list if block is convex
        - Coordinates are in rotated space (driving direction = East)
        - Mirrors find_critical_points() from boustrophedon.py but for X-axis
    """
    # Check if block is convex first
    if is_block_convex(block, threshold=0.99):
        return []

    # Rotate block to align driving direction horizontally
    rotation_angle = -driving_direction_degrees
    rotated_block_poly = rotate_geometry(block.polygon, rotation_angle)

    # Collect critical X-coordinates
    critical_x = []

    # Get block bounds
    bounds = rotated_block_poly.bounds  # (minx, miny, maxx, maxy)
    critical_x.append(bounds[0])  # Left boundary
    critical_x.append(bounds[2])  # Right boundary

    # For non-convex blocks, extract all X-coordinates from block vertices
    # This handles both Type B holes and L-shaped blocks from Type B subtraction
    coords = list(rotated_block_poly.exterior.coords[:-1])
    for x, y in coords:
        critical_x.append(x)

    # Also check if inner boundary has holes (Type B obstacles creating interior rings)
    rotated_inner_boundary = rotate_geometry(inner_boundary, rotation_angle)
    if has_interior_holes(rotated_inner_boundary):
        # Extract hole vertices from inner boundary
        hole_vertices = extract_hole_vertices(rotated_inner_boundary)

        # Filter hole vertices that are within or near this block's bounds
        for x, y in hole_vertices:
            # Check if vertex is within block's X-range (with small tolerance)
            if bounds[0] - 1e-3 <= x <= bounds[2] + 1e-3:
                # Check if vertex is within block's Y-range
                if bounds[1] - 1e-3 <= y <= bounds[3] + 1e-3:
                    critical_x.append(x)

    # Sort and remove duplicates (with tolerance for floating point)
    critical_x = sorted(set(np.round(critical_x, decimals=6)))

    return critical_x


def create_vertical_slice(
    x_left: float, x_right: float, y_min: float, y_max: float
) -> Polygon:
    """
    Create a vertical slice polygon (perpendicular to driving direction).

    Creates a rectangular slice between two X-coordinates, extending across
    the full Y-range of the block. This is the vertical analogue of the
    horizontal slices created in compute_slice_polygons().

    Args:
        x_left: Left boundary X-coordinate
        x_right: Right boundary X-coordinate
        y_min: Bottom boundary Y-coordinate
        y_max: Top boundary Y-coordinate

    Returns:
        Rectangular polygon representing vertical slice

    Examples:
        >>> slice_poly = create_vertical_slice(0.0, 5.0, 0.0, 10.0)
        >>> slice_poly.area
        50.0
    """
    return Polygon([
        (x_left, y_min),
        (x_right, y_min),
        (x_right, y_max),
        (x_left, y_max),
    ])


def subdivide_block_vertically(
    block: Block,
    critical_x: List[float],
    rotation_angle: float,
) -> List[Polygon]:
    """
    Subdivide a block into vertical slices at critical X-coordinates.

    Creates sub-blocks by intersecting the block polygon with vertical slices
    defined by consecutive critical X-coordinates.

    Args:
        block: Block to subdivide
        critical_x: Sorted list of critical X-coordinates (in rotated space)
        rotation_angle: Rotation angle applied to block (-driving_direction_degrees)

    Returns:
        List of sub-block polygons (in rotated space, convex pieces)

    Notes:
        - Handles MultiPolygon results if slice creates multiple pieces
        - Filters out very small or empty polygons (area < 1e-6)
        - Polygons are in rotated coordinate system (caller must rotate back)
    """
    if len(critical_x) < 2:
        # Not enough critical points for subdivision
        return [block.polygon]

    # Rotate block to aligned orientation
    rotated_poly = rotate_geometry(block.polygon, rotation_angle)

    # Get Y-bounds for vertical slices
    bounds = rotated_poly.bounds  # (minx, miny, maxx, maxy)
    y_min, y_max = bounds[1], bounds[3]

    # Create vertical slices between consecutive X-coordinates
    sub_blocks = []

    for i in range(len(critical_x) - 1):
        x_left = critical_x[i]
        x_right = critical_x[i + 1]

        # Skip zero-width slices
        if abs(x_right - x_left) < 1e-6:
            continue

        # Create vertical slice polygon
        slice_poly = create_vertical_slice(x_left, x_right, y_min, y_max)

        # Intersect with block polygon
        result = rotated_poly.intersection(slice_poly)

        # Handle empty intersection
        if result.is_empty:
            continue

        # Handle MultiPolygon results
        if isinstance(result, MultiPolygon):
            # Take all non-empty pieces
            for poly in result.geoms:
                if not poly.is_empty and poly.area > 1e-6:
                    sub_blocks.append(poly)
        elif isinstance(result, Polygon):
            if result.area > 1e-6:
                sub_blocks.append(result)

    # Clean up invalid geometries
    cleaned_sub_blocks = []
    for poly in sub_blocks:
        if not poly.is_valid:
            poly = poly.buffer(0)  # Fix invalid geometry
        if poly.is_valid and not poly.is_empty and poly.area > 1e-6:
            cleaned_sub_blocks.append(poly)

    return cleaned_sub_blocks if cleaned_sub_blocks else [rotated_poly]


def subdivide_non_convex_block(
    block: Block,
    driving_direction_degrees: float,
    inner_boundary: Polygon,
    next_block_id: int,
) -> List[Block]:
    """
    Subdivide a non-convex block into convex sub-blocks.

    Main subdivision logic for a single block:
    1. Check if block is convex (if yes, return as-is)
    2. Find critical X-coordinates from Type B holes
    3. Create vertical slices at critical points
    4. Generate sub-block polygons
    5. Rotate back to original orientation
    6. Create Block objects with new IDs

    Args:
        block: Block to subdivide (potentially non-convex)
        driving_direction_degrees: Driving direction angle
        inner_boundary: Field inner boundary (may contain Type B holes)
        next_block_id: Next available block ID for sub-blocks

    Returns:
        List of Block objects (convex sub-blocks or original block if convex)

    Examples:
        >>> # Convex block returns as-is
        >>> rect_block = Block(0, [(0,0), (10,0), (10,5), (0,5)])
        >>> result = subdivide_non_convex_block(rect_block, 0.0, field_boundary, 1)
        >>> len(result)
        1

        >>> # Non-convex block subdivided
        >>> l_block = Block(0, [(0,0), (10,0), (10,5), (5,5), (5,10), (0,10)])
        >>> result = subdivide_non_convex_block(l_block, 0.0, field_boundary, 1)
        >>> len(result) > 1
        True
    """
    # Check if block is already convex
    if is_block_convex(block, threshold=0.99):
        return [block]

    # Find critical X-coordinates for vertical subdivision
    rotation_angle = -driving_direction_degrees
    critical_x = find_critical_x_coordinates(block, driving_direction_degrees, inner_boundary)

    if len(critical_x) < 2:
        # No subdivision possible, return original block
        return [block]

    # Subdivide block vertically
    sub_block_polys_rotated = subdivide_block_vertically(block, critical_x, rotation_angle)

    # Rotate sub-blocks back to original orientation
    reverse_rotation_angle = driving_direction_degrees
    sub_block_polys = [
        rotate_geometry(poly, reverse_rotation_angle) for poly in sub_block_polys_rotated
    ]

    # Create Block objects with new IDs
    sub_blocks = []
    for i, poly in enumerate(sub_block_polys):
        boundary_coords = list(poly.exterior.coords[:-1])  # Exclude duplicate last point
        sub_block = Block(block_id=next_block_id + i, boundary=boundary_coords)
        sub_blocks.append(sub_block)

    return sub_blocks


def subdivide_all_non_convex_blocks(
    blocks: List[Block],
    driving_direction_degrees: float,
    inner_boundary: Polygon,
) -> List[Block]:
    """
    Subdivide all non-convex blocks in a list into convex sub-blocks.

    Main entry point for convex subdivision. Processes each block independently,
    subdividing non-convex blocks while preserving convex blocks unchanged.

    Algorithm:
    1. For each block:
       a. Check if convex (convexity_ratio ≥ 0.99)
       b. If convex: keep as-is
       c. If non-convex: subdivide into convex pieces
    2. Renumber all blocks sequentially (0, 1, 2, ...)
    3. Return final list of convex blocks

    Args:
        blocks: List of preliminary blocks from boustrophedon decomposition
        driving_direction_degrees: Driving direction angle
        inner_boundary: Field inner boundary (may contain Type B holes)

    Returns:
        List of Block objects (all convex, convexity_ratio ≥ 0.99)

    Notes:
        - Total number of blocks may increase (non-convex blocks split)
        - Block IDs renumbered sequentially after subdivision
        - Area preserved (sum of sub-block areas = original block area)
        - Works with empty input (returns empty list)

    Examples:
        >>> # Mix of convex and non-convex blocks
        >>> blocks = [convex_block1, non_convex_block, convex_block2]
        >>> result = subdivide_all_non_convex_blocks(blocks, 0.0, inner_boundary)
        >>> all(is_block_convex(b) for b in result)
        True
    """
    if not blocks:
        return []

    # Process each block, subdividing non-convex ones
    all_blocks = []
    next_block_id = 0

    for block in blocks:
        # Subdivide block (returns list with original if convex, or sub-blocks if non-convex)
        sub_blocks = subdivide_non_convex_block(
            block, driving_direction_degrees, inner_boundary, next_block_id
        )

        all_blocks.extend(sub_blocks)
        next_block_id += len(sub_blocks)

    # Renumber blocks sequentially
    for i, block in enumerate(all_blocks):
        block.block_id = i

    return all_blocks
