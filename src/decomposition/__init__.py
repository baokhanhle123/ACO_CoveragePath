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
from .track_clustering import (
    cluster_tracks_into_blocks,
    get_track_clustering_statistics,
    is_track_inside_block,
    subdivide_track_at_block,
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
    # Track clustering
    "cluster_tracks_into_blocks",
    "subdivide_track_at_block",
    "is_track_inside_block",
    "get_track_clustering_statistics",
]
