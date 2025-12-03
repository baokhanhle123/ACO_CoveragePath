"""
Path generation from ACO solution.

Converts the optimized node sequence into a continuous coverage path with:
- Working segments (covering tracks within blocks)
- Transition segments (moving between blocks)
- Waypoints for navigation
"""

from dataclasses import dataclass, field
from typing import List, Tuple

import numpy as np

from ..data.block import Block, BlockNode


@dataclass
class PathSegment:
    """
    Represents a segment of the coverage path.

    Attributes:
        segment_type: "working" (covering field) or "transition" (moving between blocks)
        waypoints: List of (x, y) coordinates along segment
        block_id: Block ID for working segments, -1 for transitions
        distance: Total distance of segment
    """

    segment_type: str  # "working" or "transition"
    waypoints: List[Tuple[float, float]]
    block_id: int  # Block ID for working segments, -1 for transitions
    distance: float = 0.0

    def __post_init__(self):
        """Calculate distance if not provided."""
        if self.distance == 0.0 and self.waypoints:
            self.distance = calculate_segment_distance(self.waypoints)


@dataclass
class PathPlan:
    """
    Complete coverage path plan.

    Attributes:
        segments: List of path segments (working and transition)
        total_distance: Total path distance
        working_distance: Distance spent working (covering field)
        transition_distance: Distance spent in transitions
        block_sequence: Sequence of blocks visited
    """

    segments: List[PathSegment] = field(default_factory=list)
    total_distance: float = 0.0
    working_distance: float = 0.0
    transition_distance: float = 0.0
    block_sequence: List[int] = field(default_factory=list)

    def get_all_waypoints(self) -> List[Tuple[float, float]]:
        """
        Get all waypoints in order.

        Returns:
            List of all waypoints from all segments
        """
        waypoints = []
        for segment in self.segments:
            waypoints.extend(segment.waypoints)
        return waypoints


def calculate_segment_distance(waypoints: List[Tuple[float, float]]) -> float:
    """
    Calculate total distance along waypoint sequence.

    Args:
        waypoints: List of (x, y) coordinates

    Returns:
        Total distance traveled along waypoints
    """
    if len(waypoints) < 2:
        return 0.0

    total_distance = 0.0
    for i in range(len(waypoints) - 1):
        dx = waypoints[i + 1][0] - waypoints[i][0]
        dy = waypoints[i + 1][1] - waypoints[i][1]
        total_distance += np.sqrt(dx * dx + dy * dy)

    return total_distance


def get_block_tracks_path(block: Block, entry_node: BlockNode, exit_node: BlockNode) -> List[Tuple[float, float]]:
    """
    Generate waypoints for traversing all tracks in a block.

    Creates a continuous path through the block following the
    boustrophedon (back-and-forth) pattern.

    Strategy:
    1. Determine entry and exit tracks from node types
    2. Traverse tracks in order from entry to exit
    3. Alternate direction on each track (back-and-forth)

    Args:
        block: Block to traverse
        entry_node: Entry node
        exit_node: Exit node

    Returns:
        List of waypoints traversing all tracks in block
    """
    if not block.tracks:
        return []

    waypoints = []

    # Determine entry and exit positions
    entry_type = entry_node.node_type
    exit_type = exit_node.node_type

    # Determine track traversal order
    # Entry node determines starting track
    if "first" in entry_type:
        # Start from first track
        start_idx = 0
        end_idx = len(block.tracks) - 1
        forward = True
    else:
        # Start from last track
        start_idx = len(block.tracks) - 1
        end_idx = 0
        forward = False

    # Determine initial direction
    if "start" in entry_type:
        start_from_start = True
    else:
        start_from_start = False

    # Traverse tracks
    current_direction = start_from_start

    if forward:
        # Traverse tracks forward (first to last)
        for i in range(start_idx, end_idx + 1):
            track = block.tracks[i]
            if current_direction:
                # Traverse start -> end
                waypoints.append(track.start)
                waypoints.append(track.end)
            else:
                # Traverse end -> start
                waypoints.append(track.end)
                waypoints.append(track.start)
            # Alternate direction for next track
            current_direction = not current_direction
    else:
        # Traverse tracks backward (last to first)
        for i in range(start_idx, end_idx - 1, -1):
            track = block.tracks[i]
            if current_direction:
                # Traverse start -> end
                waypoints.append(track.start)
                waypoints.append(track.end)
            else:
                # Traverse end -> start
                waypoints.append(track.end)
                waypoints.append(track.start)
            # Alternate direction for next track
            current_direction = not current_direction

    return waypoints


def create_transition_segment(node_from: BlockNode, node_to: BlockNode) -> PathSegment:
    """
    Create transition segment between two nodes.

    A transition segment connects the exit node of one block
    to the entry node of another block.

    Args:
        node_from: Exit node of previous block
        node_to: Entry node of next block

    Returns:
        Transition path segment
    """
    waypoints = [node_from.position, node_to.position]
    distance = calculate_segment_distance(waypoints)

    return PathSegment(segment_type="transition", waypoints=waypoints, block_id=-1, distance=distance)


def create_working_segment(block: Block, entry_node: BlockNode, exit_node: BlockNode) -> PathSegment:
    """
    Create working segment for covering a block.

    Args:
        block: Block to cover
        entry_node: Entry node
        exit_node: Exit node

    Returns:
        Working path segment with all waypoints
    """
    # Get waypoints for traversing block tracks
    track_waypoints = get_block_tracks_path(block, entry_node, exit_node)

    # Build waypoints: entry + track waypoints + exit
    # Keep all points to ensure proper path representation
    waypoints = [entry_node.position]

    if track_waypoints:
        waypoints.extend(track_waypoints)

    waypoints.append(exit_node.position)

    distance = calculate_segment_distance(waypoints)

    return PathSegment(segment_type="working", waypoints=waypoints, block_id=block.block_id, distance=distance)


def generate_path_from_solution(solution, blocks: List[Block], nodes: List[BlockNode]) -> PathPlan:
    """
    Generate complete coverage path from ACO solution.

    Converts the optimized node sequence into a continuous path with:
    1. Working segments for each block (covering all tracks)
    2. Transition segments between blocks

    Algorithm:
    1. Validate solution
    2. Group consecutive nodes by block
    3. For each block pair:
        a. Create working segment for block
        b. Create transition segment to next block (if any)
    4. Calculate statistics

    Args:
        solution: ACO solution with node sequence
        blocks: List of all blocks
        nodes: List of all nodes

    Returns:
        Complete path plan with segments and statistics

    Raises:
        ValueError: If solution is invalid
    """
    # Validate solution
    if not solution.is_valid(len(blocks)):
        raise ValueError(f"Solution is not valid for {len(blocks)} blocks")

    # Build path segments
    segments = []
    working_distance = 0.0
    transition_distance = 0.0

    # Process node pairs (entry and exit for each block)
    i = 0
    while i < len(solution.path):
        # Get current node
        node_idx = solution.path[i]
        current_node = nodes[node_idx]
        block_id = current_node.block_id
        block = blocks[block_id]

        # Find matching exit node (next node with same block_id)
        if i + 1 < len(solution.path):
            next_node_idx = solution.path[i + 1]
            next_node = nodes[next_node_idx]

            if next_node.block_id == block_id:
                # Found exit node for this block
                exit_node = next_node

                # Create working segment
                working_seg = create_working_segment(block, current_node, exit_node)
                segments.append(working_seg)
                working_distance += working_seg.distance

                # Check if there's a next block (transition needed)
                if i + 2 < len(solution.path):
                    next_block_node_idx = solution.path[i + 2]
                    next_block_node = nodes[next_block_node_idx]

                    # Create transition segment
                    transition_seg = create_transition_segment(exit_node, next_block_node)
                    segments.append(transition_seg)
                    transition_distance += transition_seg.distance

                # Move to next block
                i += 2
            else:
                # Unexpected: consecutive nodes from different blocks
                # Skip this node
                i += 1
        else:
            # Last node, no exit pair
            i += 1

    # Calculate total distance
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
    Calculate statistics for path plan.

    Args:
        path_plan: Complete path plan

    Returns:
        Dictionary with statistics:
        - total_distance: Total path distance
        - working_distance: Distance covering field
        - transition_distance: Distance in transitions
        - efficiency: working_distance / total_distance
        - num_blocks: Number of blocks visited
        - num_segments: Total number of segments
        - num_working_segments: Number of working segments
        - num_transition_segments: Number of transition segments
        - total_waypoints: Total number of waypoints
    """
    working_segments = [s for s in path_plan.segments if s.segment_type == "working"]
    transition_segments = [s for s in path_plan.segments if s.segment_type == "transition"]

    efficiency = 0.0
    if path_plan.total_distance > 0:
        efficiency = path_plan.working_distance / path_plan.total_distance

    all_waypoints = path_plan.get_all_waypoints()

    return {
        "total_distance": path_plan.total_distance,
        "working_distance": path_plan.working_distance,
        "transition_distance": path_plan.transition_distance,
        "efficiency": efficiency,
        "num_blocks": len(path_plan.block_sequence),
        "num_segments": len(path_plan.segments),
        "num_working_segments": len(working_segments),
        "num_transition_segments": len(transition_segments),
        "total_waypoints": len(all_waypoints),
    }
