"""
Visualization module for coverage path planning.

Provides tools for:
- Animated path execution
- Pheromone heatmap visualization
- Interactive dashboards
- Professional static plots
"""

from .path_animation import PathAnimator, animate_path_execution
from .plot_utils import create_field_plot, plot_path_plan

__all__ = [
    "PathAnimator",
    "animate_path_execution",
    "create_field_plot",
    "plot_path_plan",
]
