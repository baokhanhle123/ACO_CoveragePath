"""
Utility functions for creating professional static plots.

Provides reusable plotting functions for:
- Field representations
- Path plans
- Block visualizations
- Statistical plots
"""

import matplotlib.pyplot as plt
import numpy as np
from typing import List, Optional, Tuple


def create_field_plot(field, ax=None, show_obstacles=True, show_boundary=True):
    """
    Create basic field plot with boundary and obstacles.

    Args:
        field: Field object
        ax: Matplotlib axes (creates new if None)
        show_obstacles: Whether to draw obstacles
        show_boundary: Whether to draw field boundary

    Returns:
        Matplotlib axes object
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=(10, 8))

    # Field boundary
    if show_boundary:
        field_x, field_y = zip(*field.boundary_polygon.exterior.coords)
        ax.plot(field_x, field_y, 'k-', linewidth=2, label='Field Boundary')

    # Obstacles
    if show_obstacles:
        for i, obs in enumerate(field.obstacle_polygons):
            obs_x, obs_y = zip(*obs.exterior.coords)
            ax.fill(
                obs_x, obs_y,
                color='gray',
                alpha=0.5,
                edgecolor='black',
                linewidth=1.5
            )
            if i == 0:
                ax.plot([], [], 's', color='gray', alpha=0.5, label='Obstacles')

    ax.set_xlabel('X (meters)')
    ax.set_ylabel('Y (meters)')
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.3)

    return ax


def plot_path_plan(
    field,
    blocks,
    path_plan,
    title="Coverage Path Plan",
    figsize=(14, 10),
    show_blocks=True,
    show_waypoints=False
):
    """
    Create comprehensive path plan visualization.

    Args:
        field: Field object
        blocks: List of blocks
        path_plan: PathPlan object
        title: Plot title
        figsize: Figure size
        show_blocks: Whether to show block coloring
        show_waypoints: Whether to show individual waypoints

    Returns:
        Figure and axes objects
    """
    fig, ax = plt.subplots(figsize=figsize)

    # Draw field
    create_field_plot(field, ax=ax)

    # Draw blocks
    if show_blocks:
        colors = plt.cm.Set3(np.linspace(0, 1, len(blocks)))
        for i, block in enumerate(blocks):
            block_x, block_y = zip(*block.polygon.exterior.coords)
            ax.fill(
                block_x, block_y,
                color=colors[i],
                alpha=0.2,
                edgecolor=colors[i],
                linewidth=1.5
            )
            # Add block label
            centroid = block.polygon.centroid
            ax.text(
                centroid.x, centroid.y,
                f"B{block.block_id}",
                ha='center', va='center',
                fontsize=10,
                fontweight='bold',
                bbox=dict(boxstyle='circle', facecolor='white', alpha=0.7)
            )

    # Draw path segments
    for segment in path_plan.segments:
        seg_x, seg_y = zip(*segment.waypoints)

        if segment.segment_type == 'working':
            ax.plot(
                seg_x, seg_y,
                'b-',
                linewidth=2.5,
                alpha=0.8,
                label='Working' if 'Working' not in [l.get_label() for l in ax.lines] else ''
            )
        else:
            ax.plot(
                seg_x, seg_y,
                'r--',
                linewidth=2,
                alpha=0.6,
                label='Transition' if 'Transition' not in [l.get_label() for l in ax.lines] else ''
            )

    # Mark start and end
    all_waypoints = path_plan.get_all_waypoints()
    if all_waypoints:
        ax.plot(
            all_waypoints[0][0], all_waypoints[0][1],
            'go', markersize=15, label='Start', zorder=10
        )
        ax.plot(
            all_waypoints[-1][0], all_waypoints[-1][1],
            'rs', markersize=15, label='End', zorder=10
        )

    # Show waypoints if requested
    if show_waypoints and all_waypoints:
        wp_x, wp_y = zip(*all_waypoints)
        ax.plot(wp_x, wp_y, 'k.', markersize=2, alpha=0.3)

    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.legend(loc='upper right')

    plt.tight_layout()

    return fig, ax
