"""
Cost matrix construction for Stage 3 ACO optimization.

Implements Section 2.4.1 from Zhou et al. 2014:
- Node distance calculation (Euclidean)
- Entry/exit parity constraints (Fig. 9)
- Within-block costs (working distance)
- Between-block costs (transition distance)
"""

from typing import List, Tuple

import numpy as np

from ..data.block import Block, BlockNode


# Large penalty for invalid transitions (Section 2.4.1: "relatively very large number L")
INVALID_COST = 1e10


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
    return np.sqrt(dx * dx + dy * dy)


def node_distance(node1: BlockNode, node2: BlockNode) -> float:
    """
    Calculate distance between two nodes.

    Args:
        node1: First node
        node2: Second node

    Returns:
        Euclidean distance between node positions
    """
    return euclidean_distance(node1.position, node2.position)


def is_valid_transition(node1: BlockNode, node2: BlockNode, blocks: List[Block]) -> bool:
    """
    Check if transition from node1 to node2 is valid.

    Implements entry/exit parity constraints from Section 2.4.1 and Fig. 9:
    - Cannot stay at same node
    - Between different blocks: always valid
    - Within same block: depends on track parity
        - Even tracks: first_start <-> last_end, first_end <-> last_start valid
        - Odd tracks: first_start <-> last_start, first_end <-> last_end valid

    Args:
        node1: Starting node
        node2: Ending node
        blocks: List of all blocks

    Returns:
        True if transition is valid, False otherwise
    """
    # Cannot stay at same node
    if node1.index == node2.index:
        return False

    # Different blocks: always valid
    if node1.block_id != node2.block_id:
        return True

    # Same block: check parity constraints
    block = blocks[node1.block_id]
    is_odd = block.is_odd_tracks

    # Get node types
    type1 = node1.node_type
    type2 = node2.node_type

    # Nodes on same track are never valid for transitions
    if (type1 == "first_start" and type2 == "first_end") or \
       (type1 == "first_end" and type2 == "first_start") or \
       (type1 == "last_start" and type2 == "last_end") or \
       (type1 == "last_end" and type2 == "last_start"):
        return False

    # Valid transitions depend on parity (from paper Fig. 9)
    if is_odd:
        # Odd tracks: first_start <-> last_start, first_end <-> last_end
        if (type1 == "first_start" and type2 == "last_start") or \
           (type1 == "last_start" and type2 == "first_start") or \
           (type1 == "first_end" and type2 == "last_end") or \
           (type1 == "last_end" and type2 == "first_end"):
            return True
    else:
        # Even tracks: first_start <-> last_end, first_end <-> last_start
        if (type1 == "first_start" and type2 == "last_end") or \
           (type1 == "last_end" and type2 == "first_start") or \
           (type1 == "first_end" and type2 == "last_start") or \
           (type1 == "last_start" and type2 == "first_end"):
            return True

    return False


def get_within_block_cost(block: Block, node1: BlockNode, node2: BlockNode) -> float:
    """
    Calculate cost for transition within a block.

    From paper Section 2.4.1:
    - Cost equals the total working distance (sum of track lengths)
    - This represents traversing all tracks in the block

    Args:
        block: Block containing both nodes
        node1: Entry node
        node2: Exit node

    Returns:
        Total working distance in block
    """
    return block.get_working_distance()


def build_cost_matrix(
    blocks: List[Block], nodes: List[BlockNode], turning_penalty: float = 0.0
) -> np.ndarray:
    """
    Build complete cost matrix for TSP problem.

    Implements Section 2.4.1 from the paper:
    - Diagonal elements are 0 (no cost to stay at same node)
    - Within-block costs follow parity constraints (Fig. 9):
        * Valid transitions: working distance
        * Invalid transitions: very large cost (INVALID_COST)
    - Between-block costs: Euclidean distance + optional turning penalty

    Args:
        blocks: List of all blocks
        nodes: List of all entry/exit nodes (4 per block)
        turning_penalty: Optional penalty for turns between blocks (default 0)

    Returns:
        Cost matrix of shape (num_nodes, num_nodes)

    Note:
        The cost matrix represents the heuristic values for ACO.
        Invalid transitions have cost = INVALID_COST to prevent selection.
    """
    n = len(nodes)
    cost_matrix = np.zeros((n, n))

    for i in range(n):
        for j in range(n):
            if i == j:
                # Diagonal: zero cost
                cost_matrix[i][j] = 0.0
                continue

            node_i = nodes[i]
            node_j = nodes[j]

            # Check if transition is valid
            if not is_valid_transition(node_i, node_j, blocks):
                # Invalid transition: very high cost
                cost_matrix[i][j] = INVALID_COST
                continue

            # Valid transition
            if node_i.block_id == node_j.block_id:
                # Within same block: working distance
                block = blocks[node_i.block_id]
                cost_matrix[i][j] = get_within_block_cost(block, node_i, node_j)
            else:
                # Between different blocks: Euclidean distance + turning penalty
                cost_matrix[i][j] = node_distance(node_i, node_j) + turning_penalty

    return cost_matrix
