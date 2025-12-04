"""
Track clustering for boustrophedon decomposition.

Implements the “clustering tracks into blocks” step of Zhou et al. 2014
([`10.1016/j.compag.2014.08.013`](http://dx.doi.org/10.1016/j.compag.2014.08.013)),
Section 2.3.2:

- Takes global tracks from Stage 1 (generated ignoring obstacles)
- Subdivides tracks at block boundaries
- Assigns each resulting segment to exactly one block.

This corresponds to the second-stage operation where the continuous
Stage‑1 guidance lines are partitioned and associated with the block
areas resulting from the boustrophedon decomposition, as described in
the equations and figures in Section 2.3.2 of the paper.
"""

from typing import List, Tuple

from shapely.geometry import LineString, Point

from ..data.block import Block
from ..data.track import Track


def subdivide_track_at_block(track: Track, block: Block) -> List[Track]:
    """
    Subdivide a track into segments based on intersection with a block.

    Algorithm from paper (Section 2.3.2):
    1. Check if track intersects block boundary
    2. If yes, subdivide track into segments at intersection points
    3. Return segments (both inside and outside the block)

    Args:
        track: Original track (LineString from start to end)
        block: Block polygon to check against

    Returns:
        List of track segments (may include the original track if no subdivision needed)
    """
    # Create LineString from track
    track_line = LineString([track.start, track.end])

    # Check if track intersects the block
    if not track_line.intersects(block.polygon):
        # No intersection - track is completely outside this block
        return [track]

    # Get intersection points with block boundary
    intersection = track_line.intersection(block.polygon.boundary)

    # Handle different intersection types
    intersection_points = []

    if intersection.is_empty:
        # Track might be completely inside the block (no boundary crossing)
        return [track]

    if intersection.geom_type == 'Point':
        intersection_points = [intersection]
    elif intersection.geom_type == 'MultiPoint':
        intersection_points = list(intersection.geoms)
    elif intersection.geom_type == 'LineString':
        # Track runs along the boundary - treat endpoints as intersection points
        coords = list(intersection.coords)
        if coords:
            intersection_points = [Point(coords[0]), Point(coords[-1])]
    elif intersection.geom_type == 'MultiLineString':
        # Multiple segments along boundary
        for line in intersection.geoms:
            coords = list(line.coords)
            if coords:
                intersection_points.extend([Point(coords[0]), Point(coords[-1])])
    else:
        # Fallback - no subdivision
        return [track]

    if not intersection_points:
        return [track]

    # Sort intersection points along the track direction
    # Project each point onto the track line to get its position along the track
    points_with_distance = []
    track_start_point = Point(track.start)

    for pt in intersection_points:
        # Distance from track start to this intersection point
        dist = track_start_point.distance(pt)
        points_with_distance.append((dist, (pt.x, pt.y)))

    # Sort by distance along track
    points_with_distance.sort(key=lambda x: x[0])

    # Build list of subdivision points: start -> intersections -> end
    subdivision_points = [track.start]
    for _, pt_coords in points_with_distance:
        # Avoid duplicate points (very close to existing)
        if all(
            ((pt_coords[0] - existing[0])**2 + (pt_coords[1] - existing[1])**2) > 1e-6
            for existing in subdivision_points
        ):
            subdivision_points.append(pt_coords)
    subdivision_points.append(track.end)

    # Remove duplicates that are too close
    cleaned_points = [subdivision_points[0]]
    for i in range(1, len(subdivision_points)):
        prev = cleaned_points[-1]
        curr = subdivision_points[i]
        dist_sq = (curr[0] - prev[0])**2 + (curr[1] - prev[1])**2
        if dist_sq > 1e-6:  # Not a duplicate
            cleaned_points.append(curr)

    subdivision_points = cleaned_points

    # Create track segments
    segments = []
    for i in range(len(subdivision_points) - 1):
        segment = Track(
            start=subdivision_points[i],
            end=subdivision_points[i + 1],
            index=track.index,  # Keep original track index
            block_id=None  # Will be assigned later
        )
        segments.append(segment)

    return segments if segments else [track]


def is_track_inside_block(track: Track, block: Block, tolerance: float = 0.1) -> bool:
    """
    Check if a track segment is located inside a block.

    Args:
        track: Track segment to check
        block: Block polygon
        tolerance: Distance tolerance for boundary checking

    Returns:
        True if track is inside the block
    """
    # Check if midpoint of track is inside block
    midpoint = Point(track.midpoint)

    # Use a small buffer to handle numerical precision issues
    return block.polygon.buffer(tolerance).contains(midpoint)


def cluster_tracks_into_blocks(
    global_tracks: List[Track],
    blocks: List[Block]
) -> List[Block]:
    """
    Cluster global tracks into blocks by subdivision and assignment.

    Algorithm from paper (Section 2.3.2):
    1. Input: Set T of global tracks (from Stage 1, ignoring obstacles)
    2. Input: Set B of block areas (from boustrophedon decomposition)
    3. For each track i ∈ T:
       a. For each block j ∈ B:
          - If track intersects block boundary, subdivide into segments
          - Check each segment: is it inside block j?
          - If yes, assign segment to block j's track set

    Args:
        global_tracks: Tracks generated in Stage 1 (ignoring obstacles)
        blocks: Blocks from boustrophedon decomposition

    Returns:
        List of blocks with tracks assigned (modifies blocks in-place)

    Notes:
        - Original global tracks may be subdivided into multiple segments
        - Each segment is assigned to exactly one block
        - Segments keep their original track index for continuity
    """
    # Initialize each block's track list
    for block in blocks:
        block.tracks = []

    # Process each global track
    for track in global_tracks:
        # Track segments that haven't been assigned yet
        unassigned_segments = [track]

        # Try to assign segments to each block
        for block in blocks:
            newly_unassigned = []

            for segment in unassigned_segments:
                # Subdivide segment at this block's boundary
                subsegments = subdivide_track_at_block(segment, block)

                for subseg in subsegments:
                    # Check if this subsegment is inside the block
                    if is_track_inside_block(subseg, block):
                        # Assign to this block
                        subseg.block_id = block.block_id
                        block.tracks.append(subseg)
                    else:
                        # Keep for next block
                        newly_unassigned.append(subseg)

            unassigned_segments = newly_unassigned

    # Re-index tracks within each block for sequential ordering
    for block in blocks:
        # Sort tracks by their original index (maintains field sequence)
        block.tracks.sort(key=lambda t: (t.index, t.start[0], t.start[1]))

        # Assign new within-block indices
        for i, track in enumerate(block.tracks):
            # Keep original index in a different way if needed
            # For now, just update the index to be sequential within block
            track.block_id = block.block_id
            # Note: We keep the original track.index to maintain global track sequence

    return blocks


def get_track_clustering_statistics(blocks: List[Block], global_tracks: List[Track]) -> dict:
    """
    Calculate statistics about track clustering results.

    Args:
        blocks: Blocks with clustered tracks
        global_tracks: Original global tracks

    Returns:
        Dictionary with statistics
    """
    total_segments = sum(len(block.tracks) for block in blocks)
    total_length_blocks = sum(
        sum(track.length for track in block.tracks)
        for block in blocks
    )
    total_length_global = sum(track.length for track in global_tracks)

    return {
        "num_global_tracks": len(global_tracks),
        "num_blocks": len(blocks),
        "total_segments": total_segments,
        "avg_segments_per_track": total_segments / len(global_tracks) if global_tracks else 0,
        "total_length_global": total_length_global,
        "total_length_clustered": total_length_blocks,
        "length_preservation": (
            total_length_blocks / total_length_global if total_length_global > 0 else 0
        ),
    }
