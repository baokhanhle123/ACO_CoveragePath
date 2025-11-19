"""
Field decomposition modules for coverage path planning.

Implements Stage 2 of the algorithm:
- Boustrophedon cellular decomposition
- Block merging and optimization
"""

from .block_merger import (
    build_block_adjacency_graph,
    check_blocks_adjacent,
    get_merging_statistics,
    greedy_block_merging,
    merge_blocks_by_criteria,
    merge_two_blocks,
)
from .boustrophedon import (
    boustrophedon_decomposition,
    find_critical_points,
    get_decomposition_statistics,
)

__all__ = [
    # Boustrophedon decomposition
    "boustrophedon_decomposition",
    "find_critical_points",
    "get_decomposition_statistics",
    # Block merging
    "build_block_adjacency_graph",
    "check_blocks_adjacent",
    "merge_two_blocks",
    "greedy_block_merging",
    "merge_blocks_by_criteria",
    "get_merging_statistics",
]
