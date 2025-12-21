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
from .pheromone_viz import PheromoneVisualizer, plot_pheromone_trails_at_iteration
from .pheromone_animation import PheromoneAnimator, animate_pheromone_evolution
from .stage_viz import plot_stage1_result, plot_stage2_result, plot_stage3_result

__all__ = [
    "PathAnimator",
    "animate_path_execution",
    "create_field_plot",
    "plot_path_plan",
    "PheromoneVisualizer",
    "plot_pheromone_trails_at_iteration",
    "PheromoneAnimator",
    "animate_pheromone_evolution",
    "plot_stage1_result",
    "plot_stage2_result",
    "plot_stage3_result",
]
