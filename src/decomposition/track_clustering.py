"""
Track clustering for boustrophedon decomposition.

Implements the track clustering algorithm from Zhou et al. 2014 (Section 2.3.2):
- Takes global tracks from Stage 1 (generated ignoring obstacles)
- Subdivides tracks at block boundaries
- Clusters track segments into appropriate blocks

Reference:
    Zhou, K., Jensen, A. L., Sørensen, C. G., Busato, P., & Bochtis, D. D. (2014).
    Agricultural operations planning in fields with multiple obstacle areas.
    Computers and Electronics in Agriculture, 109, 12-22.
    Section 2.3.2: "Clustering tracks into blocks"
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


def subdivide_tracks_at_obstacles(
    blocks: List[Block],
    obstacle_polygons: List
) -> List[Block]:
    """
    Further subdivide tracks within blocks based on block polygon shape.

    This addresses the notch problem where tracks at different y-coordinates
    have different x-extents due to obstacles intruding into the block.
    Without this subdivision, boustrophedon connections can cross obstacles.

    Strategy: For each track, find the intersection of the track line with the
    block polygon boundary. If the track enters/exits the block polygon at points
    other than its start/end, subdivide it there to ensure all track segments
    respect the block's actual boundaries (including notches).

    Args:
        blocks: Blocks with initially clustered tracks
        obstacle_polygons: List of Shapely polygons representing obstacles

    Returns:
        List of blocks with tracks subdivided at block boundary transitions
    """
    from shapely.ops import unary_union

    if not obstacle_polygons:
        return blocks

    obstacles_union = unary_union(obstacle_polygons)

    for block in blocks:
        if not block.tracks:
            continue

        subdivided_tracks = []

        for track in block.tracks:
            track_line = LineString([track.start, track.end])

            # Find where the track intersects with the block's internal boundaries
            # (caused by obstacle notches)
            # We do this by finding gaps in the track when intersected with the block polygon
            track_within_block = track_line.intersection(block.polygon)

            # If the intersection is a simple LineString, the track is fully within the block
            if track_within_block.geom_type == 'LineString':
                # Check if it crosses an obstacle
                obs_intersection = track_line.intersection(obstacles_union)
                if obs_intersection.is_empty or obs_intersection.geom_type == 'Point':
                    # No obstacle crossing, keep track as is
                    subdivided_tracks.append(track)
                elif obs_intersection.geom_type in ['LineString', 'MultiLineString']:
                    # Track crosses obstacle - need to remove this track
                    # (it will be subdivided by the intersection with block polygon)
                    if hasattr(obs_intersection, 'length') and obs_intersection.length < 0.01:
                        # Just touching
                        subdivided_tracks.append(track)
                    # else: crosses obstacle, skip it
                continue

            # If intersection is MultiLineString, the track crosses in/out of the block
            # (due to obstacle notches) - subdivide into segments
            if track_within_block.geom_type == 'MultiLineString':
                for segment_geom in track_within_block.geoms:
                    if segment_geom.length < 0.01:  # Skip tiny segments
                        continue

                    coords = list(segment_geom.coords)
                    if len(coords) >= 2:
                        segment = Track(
                            start=coords[0],
                            end=coords[-1],
                            index=track.index,
                            block_id=track.block_id
                        )

                        # Double-check this segment doesn't cross obstacles
                        segment_line = LineString([segment.start, segment.end])
                        obs_check = segment_line.intersection(obstacles_union)

                        if obs_check.is_empty or obs_check.geom_type == 'Point':
                            subdivided_tracks.append(segment)
                        elif obs_check.geom_type in ['LineString', 'MultiLineString']:
                            if hasattr(obs_check, 'length') and obs_check.length < 0.01:
                                subdivided_tracks.append(segment)
                            # else: crosses obstacle, skip
                continue

            # For other geometry types (Point, empty), skip
            if not track_within_block.is_empty and track_within_block.geom_type not in ['Point', 'MultiPoint']:
                subdivided_tracks.append(track)

        # Update block's tracks with subdivided version
        block.tracks = subdivided_tracks

    return blocks


def cluster_tracks_into_blocks(
    global_tracks: List[Track],
    blocks: List[Block],
    obstacle_polygons: List = None
) -> List[Block]:
    """
    Cluster global tracks into blocks by subdivision and assignment.

    Algorithm from paper (Section 2.3.2) with enhancement:
    1. Input: Set T of global tracks (from Stage 1, ignoring obstacles)
    2. Input: Set B of block areas (from boustrophedon decomposition)
    3. For each track i ∈ T:
       a. For each block j ∈ B:
          - If track intersects block boundary, subdivide into segments
          - Check each segment: is it inside block j?
          - If yes, assign segment to block j's track set
    4. [ENHANCEMENT] Further subdivide tracks at obstacle boundaries within blocks
       to prevent inter-track connections from crossing obstacles

    Args:
        global_tracks: Tracks generated in Stage 1 (ignoring obstacles)
        blocks: Blocks from boustrophedon decomposition
        obstacle_polygons: Optional list of obstacle polygons for within-block subdivision

    Returns:
        List of blocks with tracks assigned (modifies blocks in-place)

    Notes:
        - Original global tracks may be subdivided into multiple segments
        - Each segment is assigned to exactly one block
        - Segments keep their original track index for continuity
        - Additional subdivision at obstacle boundaries prevents crossing issues
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

    # ENHANCEMENT: Further subdivide tracks at obstacle boundaries within blocks
    # This prevents boustrophedon connections from crossing obstacles
    if obstacle_polygons:
        blocks = subdivide_tracks_at_obstacles(blocks, obstacle_polygons)

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
