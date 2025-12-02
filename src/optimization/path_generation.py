"""
Path generation from ACO solution.

Converts the TSP solution (sequence of entry/exit nodes) into a complete
continuous coverage path including working segments and transitions.
"""

from dataclasses import dataclass
from typing import List, Tuple

from shapely.geometry import LineString, Polygon
from shapely.ops import unary_union

from ..data.block import Block, BlockNode
from ..data.track import Track
from .aco import Solution


@dataclass
class PathSegment:
    """
    Represents a segment of the complete coverage path.

    Types:
    - 'working': Actual coverage work (following tracks within block)
    - 'transition': Non-working movement between blocks
    """

    segment_type: str  # 'working' or 'transition'
    waypoints: List[Tuple[float, float]]  # (x, y) coordinates
    block_id: int  # Block ID this segment belongs to (-1 for transitions)
    distance: float  # Length of segment


@dataclass
class PathPlan:
    """
    Complete coverage path plan.

    Contains the full sequence of working and transition segments
    that cover all blocks in the optimal order.
    """

    segments: List[PathSegment]
    total_distance: float
    working_distance: float
    transition_distance: float
    block_sequence: List[int]

    def get_all_waypoints(self) -> List[Tuple[float, float]]:
        """Get all waypoints in order as a single list."""
        waypoints = []
        for segment in self.segments:
            # Skip first waypoint if it duplicates the last waypoint
            if waypoints and segment.waypoints and waypoints[-1] == segment.waypoints[0]:
                waypoints.extend(segment.waypoints[1:])
            else:
                waypoints.extend(segment.waypoints)
        return waypoints


def calculate_segment_distance(waypoints: List[Tuple[float, float]]) -> float:
    """
    Calculate total distance along a sequence of waypoints.

    Args:
        waypoints: List of (x, y) coordinates

    Returns:
        Total Euclidean distance along path
    """
    if len(waypoints) < 2:
        return 0.0

    distance = 0.0
    for i in range(len(waypoints) - 1):
        dx = waypoints[i + 1][0] - waypoints[i][0]
        dy = waypoints[i + 1][1] - waypoints[i][1]
        distance += (dx * dx + dy * dy) ** 0.5

    return distance


def check_connection_crosses_obstacle(
    point1: Tuple[float, float],
    point2: Tuple[float, float],
    obstacles: List[Polygon],
    tolerance: float = 0.01,
) -> bool:
    """
    Check if direct line between two points crosses any obstacle.

    Args:
        point1: Start point (x, y)
        point2: End point (x, y)
        obstacles: List of obstacle polygons
        tolerance: Distance threshold for ignoring tiny touchings (default: 0.01m)

    Returns:
        True if line crosses an obstacle, False otherwise
    """
    if not obstacles:
        return False

    line = LineString([point1, point2])
    obstacles_union = unary_union(obstacles)
    intersection = line.intersection(obstacles_union)

    # Ignore tiny touchings, only flag actual crossings
    if intersection.is_empty or intersection.geom_type == "Point":
        return False
    if hasattr(intersection, "length") and intersection.length < tolerance:
        return False

    return True  # Line crosses obstacle


def find_connectable_track_groups(
    tracks: List[Track],
    entry_is_start: bool,
    exit_is_end: bool,
    obstacles: List[Polygon] = None,
) -> List[List[int]]:
    """
    Group tracks into clusters where consecutive tracks can be connected
    without crossing obstacles.

    This function identifies track groups that can be connected via
    boustrophedon pattern without crossing Type B or Type D obstacles.

    Args:
        tracks: List of tracks in the block
        entry_is_start: True if entry is at "start" side of block
        exit_is_end: True if exit is at "end" side of block
        obstacles: List of obstacle polygons to avoid

    Returns:
        List of groups, each group is list of track indices
        Example: [[0, 1, 2], [3, 4]] means tracks 0-2 connectable, 3-4 connectable
    """
    if not tracks or not obstacles:
        return [list(range(len(tracks)))]  # All tracks in one group

    groups = []
    current_group = [0]

    for i in range(len(tracks) - 1):
        track_i = tracks[i]
        track_j = tracks[i + 1]

        # Determine connection points based on boustrophedon pattern
        # Even tracks go start→end, odd tracks go end→start
        if i % 2 == 0:
            # Even track: ends at track.end, next track starts at track.end
            from_point = track_i.end
            to_point = track_j.end
        else:
            # Odd track: ends at track.start, next track starts at track.start
            from_point = track_i.start
            to_point = track_j.start

        # Check if connection crosses obstacle
        if check_connection_crosses_obstacle(from_point, to_point, obstacles):
            # Obstacle detected - start new group
            groups.append(current_group)
            current_group = [i + 1]
        else:
            # No obstacle - continue current group
            current_group.append(i + 1)

    # Add final group
    if current_group:
        groups.append(current_group)

    return groups


def get_block_tracks_path(
    block: Block,
    entry_node: BlockNode,
    exit_node: BlockNode,
    obstacles: List[Polygon] = None,
) -> List[Tuple[float, float]]:
    """
    Get waypoints for traversing tracks within a block.

    Follows the tracks from entry to exit, creating a boustrophedon
    (back-and-forth) pattern.

    NOTE: This function assumes all tracks in the block are connectable.
    For blocks with obstacles that disconnect tracks, use find_connectable_track_groups()
    first to identify valid track groups.

    Args:
        block: Block to traverse
        entry_node: Entry node
        exit_node: Exit node
        obstacles: Optional list of obstacle polygons (for future validation)

    Returns:
        List of waypoints following the tracks
    """
    if not block.tracks:
        return []

    waypoints = []

    # Determine traversal direction based on entry/exit nodes
    # Entry at start side, exit at end side: forward traversal
    # Entry at end side, exit at start side: reverse traversal

    entry_is_start = "start" in entry_node.node_type
    exit_is_end = "end" in exit_node.node_type

    if entry_is_start and exit_is_end:
        # Forward: start to end
        for i, track in enumerate(block.tracks):
            if i % 2 == 0:
                # Even track: traverse start → end
                waypoints.append(track.start)
                waypoints.append(track.end)
            else:
                # Odd track: traverse end → start
                waypoints.append(track.end)
                waypoints.append(track.start)
    else:
        # Reverse: end to start
        for i in range(len(block.tracks) - 1, -1, -1):
            track = block.tracks[i]
            if i % 2 == 0:
                # Even track: traverse end → start
                waypoints.append(track.end)
                waypoints.append(track.start)
            else:
                # Odd track: traverse start → end
                waypoints.append(track.start)
                waypoints.append(track.end)

    return waypoints


def create_transition_segment(
    from_node: BlockNode, to_node: BlockNode
) -> PathSegment:
    """
    Create transition segment between two nodes.

    For now, creates a simple straight-line transition.
    Future: Could incorporate turning radius constraints.

    Args:
        from_node: Source node
        to_node: Destination node

    Returns:
        Transition path segment
    """
    waypoints = [from_node.position, to_node.position]
    distance = calculate_segment_distance(waypoints)

    return PathSegment(
        segment_type="transition",
        waypoints=waypoints,
        block_id=-1,  # No specific block
        distance=distance,
    )


def create_transition_segment_waypoints(
    from_point: Tuple[float, float],
    to_point: Tuple[float, float],
    block_id: int = -1,
) -> PathSegment:
    """
    Create transition segment between two waypoint positions.

    Similar to create_transition_segment() but works with raw positions
    instead of BlockNode objects.

    Args:
        from_point: Source position (x, y)
        to_point: Destination position (x, y)
        block_id: Block ID for this segment (default: -1 for inter-block transitions)

    Returns:
        Transition path segment
    """
    waypoints = [from_point, to_point]
    distance = calculate_segment_distance(waypoints)

    return PathSegment(
        segment_type="transition",
        waypoints=waypoints,
        block_id=block_id,
        distance=distance,
    )


def get_block_tracks_path_for_group(
    group_tracks: List[Track],
    entry_is_start: bool,
    exit_is_end: bool,
) -> List[Tuple[float, float]]:
    """
    Get waypoints for traversing a specific group of tracks.

    Similar to get_block_tracks_path() but operates on a subset of tracks.

    Args:
        group_tracks: List of tracks in this group
        entry_is_start: True if entry is at "start" side
        exit_is_end: True if exit is at "end" side

    Returns:
        List of waypoints following the track group
    """
    if not group_tracks:
        return []

    waypoints = []

    if entry_is_start and exit_is_end:
        # Forward: start to end
        for i, track in enumerate(group_tracks):
            if i % 2 == 0:
                # Even track: traverse start → end
                waypoints.append(track.start)
                waypoints.append(track.end)
            else:
                # Odd track: traverse end → start
                waypoints.append(track.end)
                waypoints.append(track.start)
    else:
        # Reverse: end to start
        for i in range(len(group_tracks) - 1, -1, -1):
            track = group_tracks[i]
            if i % 2 == 0:
                # Even track: traverse end → start
                waypoints.append(track.end)
                waypoints.append(track.start)
            else:
                # Odd track: traverse start → end
                waypoints.append(track.start)
                waypoints.append(track.end)

    return waypoints


def create_working_segment(
    block: Block, entry_node: BlockNode, exit_node: BlockNode
) -> PathSegment:
    """
    Create working segment for covering a block.

    DEPRECATED: Use create_working_segments() instead for obstacle avoidance support.

    Args:
        block: Block to cover
        entry_node: Entry node
        exit_node: Exit node

    Returns:
        Working path segment
    """
    # Get track waypoints
    track_waypoints = get_block_tracks_path(block, entry_node, exit_node)

    # Add entry transition (from entry node to first track point)
    waypoints = [entry_node.position] + track_waypoints + [exit_node.position]

    distance = calculate_segment_distance(waypoints)

    return PathSegment(
        segment_type="working",
        waypoints=waypoints,
        block_id=block.block_id,
        distance=distance,
    )


def create_working_segments(
    block: Block,
    entry_node: BlockNode,
    exit_node: BlockNode,
    obstacles: List[Polygon] = None,
) -> List[PathSegment]:
    """
    Create working segment(s) for covering a block.

    If obstacles cause disconnected track groups, creates:
    - Multiple working segments (one per group)
    - Transition segments between groups

    Args:
        block: Block to cover
        entry_node: Entry node
        exit_node: Exit node
        obstacles: Optional list of obstacle polygons to avoid

    Returns:
        List of PathSegment (working segments + within-block transitions)
    """
    if not block.tracks:
        # Empty block - just transition from entry to exit
        return [create_transition_segment(entry_node, exit_node)]

    # Determine traversal direction
    entry_is_start = "start" in entry_node.node_type
    exit_is_end = "end" in exit_node.node_type

    # Find connectable track groups
    groups = find_connectable_track_groups(block.tracks, entry_is_start, exit_is_end, obstacles)

    if len(groups) == 1:
        # All tracks connectable - use original single-segment behavior
        track_waypoints = get_block_tracks_path(block, entry_node, exit_node, obstacles)
        waypoints = [entry_node.position] + track_waypoints + [exit_node.position]
        distance = calculate_segment_distance(waypoints)
        return [
            PathSegment(
                segment_type="working",
                waypoints=waypoints,
                block_id=block.block_id,
                distance=distance,
            )
        ]

    # Multiple groups - create segments for each + transitions between
    segments = []

    # Entry transition to first group
    first_track = block.tracks[groups[0][0]]
    first_point = first_track.start if entry_is_start else first_track.end
    segments.append(create_transition_segment_waypoints(entry_node.position, first_point, block.block_id))

    # Process each group
    for group_idx, group in enumerate(groups):
        group_tracks = [block.tracks[i] for i in group]
        group_waypoints = get_block_tracks_path_for_group(group_tracks, entry_is_start, exit_is_end)

        # Create working segment for this group
        segments.append(
            PathSegment(
                segment_type="working",
                waypoints=group_waypoints,
                block_id=block.block_id,
                distance=calculate_segment_distance(group_waypoints),
            )
        )

        # Transition to next group (if not last)
        if group_idx < len(groups) - 1:
            current_last = group_tracks[-1]
            next_first = block.tracks[groups[group_idx + 1][0]]

            # Determine connection points based on parity
            if len(group) % 2 == 1:
                # Odd number of tracks: ends at opposite end
                from_point = current_last.end if entry_is_start else current_last.start
            else:
                # Even number of tracks: ends at same end
                from_point = current_last.start if entry_is_start else current_last.end

            to_point = next_first.start if entry_is_start else next_first.end

            segments.append(create_transition_segment_waypoints(from_point, to_point, block.block_id))

    # Exit transition from last group
    last_group_tracks = [block.tracks[i] for i in groups[-1]]
    last_track = last_group_tracks[-1]

    # Determine where the last track ends based on parity
    if len(last_group_tracks) % 2 == 1:
        # Odd number of tracks in last group
        last_point = last_track.end if exit_is_end else last_track.start
    else:
        # Even number of tracks in last group
        last_point = last_track.start if exit_is_end else last_track.end

    segments.append(create_transition_segment_waypoints(last_point, exit_node.position, block.block_id))

    return segments


def generate_path_from_solution(
    solution: Solution,
    blocks: List[Block],
    nodes: List[BlockNode],
    obstacles: List[Polygon] = None,
) -> PathPlan:
    """
    Generate complete coverage path from ACO solution.

    Takes the TSP solution (sequence of nodes) and converts it into
    a complete path with working and transition segments.

    Args:
        solution: ACO solution with node sequence
        blocks: List of all blocks
        nodes: List of all nodes
        obstacles: Optional list of obstacle polygons to avoid

    Returns:
        Complete path plan
    """
    if not solution.is_valid(len(blocks)):
        raise ValueError("Solution is not valid - cannot generate path")

    segments = []
    working_distance = 0.0
    transition_distance = 0.0

    # Create lookup maps
    block_map = {block.block_id: block for block in blocks}

    # Process each consecutive pair of nodes in solution
    for i in range(len(solution.path) - 1):
        from_node_idx = solution.path[i]
        to_node_idx = solution.path[i + 1]

        from_node = nodes[from_node_idx]
        to_node = nodes[to_node_idx]

        # Check if same block (working) or different block (transition)
        if from_node.block_id == to_node.block_id:
            # Working segment - cover this block's tracks
            block = block_map[from_node.block_id]
            working_segments = create_working_segments(block, from_node, to_node, obstacles)
            segments.extend(working_segments)  # May be multiple segments if tracks disconnected
            # Calculate total working distance for all segments from this block
            for seg in working_segments:
                if seg.segment_type == "working":
                    working_distance += seg.distance
                else:  # Within-block transitions
                    transition_distance += seg.distance
        else:
            # Transition segment - move between blocks
            segment = create_transition_segment(from_node, to_node)
            segments.append(segment)
            transition_distance += segment.distance

    total_distance = working_distance + transition_distance

    return PathPlan(
        segments=segments,
        total_distance=total_distance,
        working_distance=working_distance,
        transition_distance=transition_distance,
        block_sequence=solution.block_sequence,
    )


def get_path_statistics(path_plan: PathPlan) -> dict:
    """
    Calculate statistics about the path plan.

    Args:
        path_plan: Path plan to analyze

    Returns:
        Dictionary with path statistics
    """
    num_segments = len(path_plan.segments)
    num_working = sum(1 for s in path_plan.segments if s.segment_type == "working")
    num_transitions = sum(
        1 for s in path_plan.segments if s.segment_type == "transition"
    )

    total_waypoints = sum(len(s.waypoints) for s in path_plan.segments)

    # Calculate efficiency (working distance / total distance)
    efficiency = 0.0
    if path_plan.total_distance > 0:
        efficiency = path_plan.working_distance / path_plan.total_distance

    return {
        "total_distance": path_plan.total_distance,
        "working_distance": path_plan.working_distance,
        "transition_distance": path_plan.transition_distance,
        "efficiency": efficiency,
        "num_blocks": len(path_plan.block_sequence),
        "num_segments": num_segments,
        "num_working_segments": num_working,
        "num_transition_segments": num_transitions,
        "total_waypoints": total_waypoints,
    }
