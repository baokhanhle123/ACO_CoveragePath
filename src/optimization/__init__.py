"""
Path optimization modules for coverage path planning.

Implements Stage 3 of the algorithm:
- Cost matrix construction
- Ant Colony Optimization (ACO)
- Path generation
"""

from .aco import ACOParameters, ACOSolver, Ant, Solution
from .cost_matrix import build_cost_matrix, euclidean_distance
from .path_generation import (
    PathPlan,
    PathSegment,
    generate_path_from_solution,
    get_path_statistics,
)

__all__ = [
    "build_cost_matrix",
    "euclidean_distance",
    "ACOParameters",
    "ACOSolver",
    "Ant",
    "Solution",
    "PathPlan",
    "PathSegment",
    "generate_path_from_solution",
    "get_path_statistics",
]
