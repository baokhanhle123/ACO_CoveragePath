"""
Path generation from ACO solution.

Converts the TSP solution (sequence of entry/exit nodes) into a complete
continuous coverage path including working segments and transitions.
"""

from dataclasses import dataclass
from typing import List, Tuple

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


def get_block_tracks_path(
    block: Block, entry_node: BlockNode, exit_node: BlockNode
) -> List[Tuple[float, float]]:
    """
    Get waypoints for traversing tracks within a block.

    Follows the tracks from entry to exit, creating a boustrophedon
    (back-and-forth) pattern.

    Args:
        block: Block to traverse
        entry_node: Entry node
        exit_node: Exit node

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


def create_working_segment(
    block: Block, entry_node: BlockNode, exit_node: BlockNode
) -> PathSegment:
    """
    Create working segment for covering a block.

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


def generate_path_from_solution(
    solution: Solution, blocks: List[Block], nodes: List[BlockNode]
) -> PathPlan:
    """
    Generate complete coverage path from ACO solution.

    Takes the TSP solution (sequence of nodes) and converts it into
    a complete path with working and transition segments.

    Args:
        solution: ACO solution with node sequence
        blocks: List of all blocks
        nodes: List of all nodes

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
            segment = create_working_segment(block, from_node, to_node)
            segments.append(segment)
            working_distance += segment.distance
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
