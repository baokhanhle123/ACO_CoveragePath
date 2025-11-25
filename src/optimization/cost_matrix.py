"""
Cost matrix construction for TSP-based path optimization.

Implements cost calculation between all entry/exit nodes including:
- Euclidean distance between nodes
- Turning costs
- Within-block working distance
- Invalid transition penalties
"""

import math
from typing import List, Tuple

import numpy as np

from ..data.block import Block, BlockNode


def euclidean_distance(pos1: Tuple[float, float], pos2: Tuple[float, float]) -> float:
    """
    Calculate Euclidean distance between two points.

    Args:
        pos1: First point (x, y)
        pos2: Second point (x, y)

    Returns:
        Euclidean distance
    """
    dx = pos2[0] - pos1[0]
    dy = pos2[1] - pos1[1]
    return math.sqrt(dx * dx + dy * dy)


def node_distance(node1: BlockNode, node2: BlockNode) -> float:
    """
    Calculate Euclidean distance between two nodes.

    Args:
        node1: First node
        node2: Second node

    Returns:
        Euclidean distance between node positions
    """
    return euclidean_distance(node1.position, node2.position)


def calculate_turning_cost(
    from_node: BlockNode, to_node: BlockNode, turning_penalty: float = 0.0
) -> float:
    """
    Calculate additional cost for turning between nodes.

    In agricultural applications, turns add time and complexity.
    This can be extended to consider turning radius constraints.

    Args:
        from_node: Source node
        to_node: Destination node
        turning_penalty: Additional cost per turn (default: 0.0)

    Returns:
        Turning cost (0 if no penalty configured)
    """
    # For now, simple constant penalty
    # Could be extended to calculate based on angle between vectors
    if from_node.block_id != to_node.block_id and turning_penalty > 0:
        return turning_penalty
    return 0.0


def get_within_block_cost(block: Block, entry_node: BlockNode, exit_node: BlockNode) -> float:
    """
    Calculate cost to traverse within a block from entry to exit.

    This is the working distance - sum of track lengths.

    Args:
        block: Block to traverse
        entry_node: Entry node
        exit_node: Exit node

    Returns:
        Working distance within block
    """
    # The cost is the total working distance of the block
    # Regardless of entry/exit, all tracks must be covered
    return block.get_working_distance()


def is_valid_transition(
    from_node: BlockNode, to_node: BlockNode, blocks: List[Block]
) -> bool:
    """
    Check if transition from one node to another is valid.

    Rules:
    1. Cannot stay at same node
    2. Can enter and exit same block (covering its tracks)
    3. For same block: must use proper entry/exit pair based on parity
       - Even number of tracks: enter at first_start or last_end,
                                exit at the other
       - Odd number of tracks: enter at first_start or last_start,
                               exit at first_end or last_end respectively

    Args:
        from_node: Source node
        to_node: Destination node
        blocks: List of all blocks

    Returns:
        True if transition is valid
    """
    # Cannot stay at same node
    if from_node.index == to_node.index:
        return False

    # Different blocks - always valid (transition between blocks)
    if from_node.block_id != to_node.block_id:
        return True

    # Same block - check if this is a valid entry/exit pair
    # Get the block
    block = None
    for b in blocks:
        if b.block_id == from_node.block_id:
            block = b
            break

    if block is None:
        return False

    # For same block, we need to cover all tracks
    # Valid pairs depend on parity (odd/even tracks)
    is_even_tracks = not block.is_odd_tracks

    # Define valid entry/exit pairs
    if is_even_tracks:
        # Even tracks: enter at first_start, exit at last_end
        #           or enter at last_end, exit at first_start
        valid_pairs = [
            ("first_start", "last_end"),
            ("last_end", "first_start"),
        ]
    else:
        # Odd tracks: enter at first_start, exit at last_start
        #          or enter at last_start, exit at first_start
        #          or enter at first_end, exit at last_end
        #          or enter at last_end, exit at first_end
        valid_pairs = [
            ("first_start", "last_start"),
            ("last_start", "first_start"),
            ("first_end", "last_end"),
            ("last_end", "first_end"),
        ]

    pair = (from_node.node_type, to_node.node_type)
    return pair in valid_pairs


def build_cost_matrix(
    blocks: List[Block],
    nodes: List[BlockNode],
    turning_penalty: float = 0.0,
    invalid_cost: float = 1e9,
) -> np.ndarray:
    """
    Build cost matrix for all nodes in the TSP problem.

    Cost[i][j] = cost to transition from node i to node j

    Components:
    - Euclidean distance between node positions
    - Turning penalty (if between different blocks)
    - Working distance (if within same block)
    - Infinity for invalid transitions

    Args:
        blocks: List of all blocks
        nodes: List of all nodes (4 per block)
        turning_penalty: Additional cost for turns (default: 0.0)
        invalid_cost: Cost for invalid transitions (default: 1e9)

    Returns:
        N x N cost matrix where N = len(nodes)
    """
    n = len(nodes)
    cost_matrix = np.zeros((n, n))

    for i in range(n):
        for j in range(n):
            from_node = nodes[i]
            to_node = nodes[j]

            # Diagonal (same node) - zero cost
            if i == j:
                cost_matrix[i][j] = 0.0
                continue

            # Check if transition is valid
            if not is_valid_transition(from_node, to_node, blocks):
                cost_matrix[i][j] = invalid_cost
                continue

            # Calculate cost based on transition type
            if from_node.block_id == to_node.block_id:
                # Within same block - working distance
                block = next(b for b in blocks if b.block_id == from_node.block_id)
                cost_matrix[i][j] = get_within_block_cost(block, from_node, to_node)
            else:
                # Between different blocks - Euclidean distance + turning penalty
                distance = node_distance(from_node, to_node)
                turning_cost = calculate_turning_cost(from_node, to_node, turning_penalty)
                cost_matrix[i][j] = distance + turning_cost

    return cost_matrix


def get_cost_matrix_statistics(cost_matrix: np.ndarray) -> dict:
    """
    Calculate statistics about the cost matrix.

    Args:
        cost_matrix: Cost matrix

    Returns:
        Dictionary with statistics
    """
    # Get valid (finite) costs
    valid_costs = cost_matrix[np.isfinite(cost_matrix) & (cost_matrix > 0)]

    if len(valid_costs) == 0:
        return {
            "size": cost_matrix.shape[0],
            "min_cost": 0.0,
            "max_cost": 0.0,
            "mean_cost": 0.0,
            "num_valid": 0,
            "num_invalid": 0,
        }

    return {
        "size": cost_matrix.shape[0],
        "min_cost": float(np.min(valid_costs)),
        "max_cost": float(np.max(valid_costs)),
        "mean_cost": float(np.mean(valid_costs)),
        "num_valid": int(np.sum(np.isfinite(cost_matrix) & (cost_matrix > 0))),
        "num_invalid": int(np.sum(~np.isfinite(cost_matrix) | (cost_matrix >= 1e9))),
    }
