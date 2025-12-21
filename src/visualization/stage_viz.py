"""
Stage-specific visualization functions for the 3-stage pipeline.

Provides dedicated visualization functions for each stage of the coverage
path planning process, suitable for use in dashboards and reports.
"""

from typing import List, Tuple

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.figure import Figure
from shapely.geometry import Polygon

from ..data import Field, Block
from ..stage1 import Stage1Result
from ..optimization import PathPlan, ACOSolver


def plot_filled_polygon(ax, polygon: Polygon, **kwargs):
    """Helper: Plot filled polygon."""
    x, y = polygon.exterior.xy
    ax.fill(x, y, **kwargs)


def plot_polygon(ax, polygon: Polygon, **kwargs):
    """Helper: Plot polygon outline."""
    x, y = polygon.exterior.xy
    ax.plot(x, y, **kwargs)


def plot_stage1_result(
    stage1_result: Stage1Result,
    figsize: Tuple[int, int] = (18, 6)
) -> Figure:
    """
    Create 3-panel visualization for Stage 1 (Field Geometric Representation).

    Panel 1: Field with obstacles
    Panel 2: Headlands and obstacle classification
    Panel 3: Global tracks

    Args:
        stage1_result: Stage1Result from run_stage1_pipeline()
        figsize: Figure size tuple

    Returns:
        matplotlib Figure object
    """
    fig, axes = plt.subplots(1, 3, figsize=figsize)

    # Panel 1: Field with obstacles
    ax1 = axes[0]
    ax1.set_title("1. Field with Obstacles", fontsize=12, fontweight="bold")
    ax1.set_aspect("equal")

    # Field boundary
    plot_filled_polygon(
        ax1,
        stage1_result.field.boundary_polygon,
        color="lightgreen",
        alpha=0.3,
        label="Field"
    )
    plot_polygon(
        ax1,
        stage1_result.field.boundary_polygon,
        color="darkgreen",
        linewidth=2
    )

    # Obstacles
    for i, obs_coords in enumerate(stage1_result.field.obstacles):
        obs_poly = Polygon(obs_coords)
        plot_filled_polygon(ax1, obs_poly, color="gray", alpha=0.6)
        plot_polygon(ax1, obs_poly, color="black", linewidth=1.5)
        centroid = obs_poly.centroid
        ax1.text(
            centroid.x,
            centroid.y,
            f"O{i+1}",
            ha="center",
            va="center",
            fontweight="bold",
            color="white",
        )

    ax1.set_xlabel("X (m)")
    ax1.set_ylabel("Y (m)")
    ax1.grid(True, alpha=0.3)
    ax1.legend()

    # Panel 2: Headlands and classification
    ax2 = axes[1]
    ax2.set_title("2. Headlands & Classification", fontsize=12, fontweight="bold")
    ax2.set_aspect("equal")

    # Field boundary
    plot_polygon(
        ax2,
        stage1_result.field.boundary_polygon,
        color="darkgreen",
        linewidth=2,
        label="Field boundary"
    )

    # Inner boundary (after headland)
    plot_polygon(
        ax2,
        stage1_result.field_headland.inner_boundary,
        color="red",
        linewidth=2,
        linestyle=":",
        label="Inner boundary"
    )

    # Classified obstacles with type labels
    for obs in stage1_result.classified_obstacles:
        plot_filled_polygon(ax2, obs.polygon, color="gray", alpha=0.4)
        plot_polygon(ax2, obs.polygon, color="black", linewidth=1.5)

        # Label with type
        centroid = obs.polygon.centroid
        ax2.text(
            centroid.x,
            centroid.y,
            f"Type {obs.obstacle_type.name}",
            ha="center",
            va="center",
            fontsize=8,
            fontweight="bold",
            color="darkred",
        )

    # Obstacle headlands (Type D)
    for obs, headland in stage1_result.obstacle_headlands:
        plot_polygon(
            ax2,
            headland.inner_boundary,
            color="orange",
            linewidth=1.5,
            linestyle="--",
            alpha=0.7
        )

    ax2.set_xlabel("X (m)")
    ax2.set_ylabel("Y (m)")
    ax2.grid(True, alpha=0.3)
    ax2.legend()

    # Panel 3: Global tracks
    ax3 = axes[2]
    ax3.set_title(f"3. Global Tracks ({len(stage1_result.tracks)} tracks)", fontsize=12, fontweight="bold")
    ax3.set_aspect("equal")

    # Inner boundary
    plot_filled_polygon(
        ax3,
        stage1_result.field_headland.inner_boundary,
        color="lightblue",
        alpha=0.2,
        label="Field body"
    )
    plot_polygon(
        ax3,
        stage1_result.field_headland.inner_boundary,
        color="blue",
        linewidth=2
    )

    # Type D obstacles only
    for obs in stage1_result.type_d_obstacles:
        plot_filled_polygon(ax3, obs.polygon, color="gray", alpha=0.5)
        plot_polygon(ax3, obs.polygon, color="black", linewidth=1.5)

    # Global tracks
    for track in stage1_result.tracks:
        ax3.plot(
            [track.start[0], track.end[0]],
            [track.start[1], track.end[1]],
            'g-',
            linewidth=2,
            alpha=0.7
        )
        # Mark endpoints
        ax3.plot(*track.start, 'go', markersize=4)
        ax3.plot(*track.end, 'ro', markersize=4)

    ax3.set_xlabel("X (m)")
    ax3.set_ylabel("Y (m)")
    ax3.grid(True, alpha=0.3)
    ax3.legend()

    plt.tight_layout()
    return fig


def plot_stage2_result(
    stage1_result: Stage1Result,
    preliminary_blocks: List[Block],
    final_blocks: List[Block],
    figsize: Tuple[int, int] = (18, 6)
) -> Figure:
    """
    Create 3-panel visualization for Stage 2 (Boustrophedon Decomposition).

    Panel 1: Preliminary decomposition (before merging)
    Panel 2: Final blocks after merging
    Panel 3: Blocks with clustered tracks

    Args:
        stage1_result: Stage1Result from Stage 1
        preliminary_blocks: Blocks before merging
        final_blocks: Blocks after merging with tracks
        figsize: Figure size tuple

    Returns:
        matplotlib Figure object
    """
    fig, axes = plt.subplots(1, 3, figsize=figsize)

    # Panel 1: Preliminary decomposition
    ax1 = axes[0]
    ax1.set_title(f"1. Preliminary Decomposition ({len(preliminary_blocks)} blocks)", fontsize=12, fontweight="bold")
    ax1.set_aspect("equal")

    # Inner boundary
    plot_polygon(
        ax1,
        stage1_result.field_headland.inner_boundary,
        color="blue",
        linewidth=2,
        linestyle="--",
        label="Inner boundary"
    )

    # Preliminary blocks with colors
    colors = plt.cm.Set3(np.linspace(0, 1, len(preliminary_blocks)))
    for i, block in enumerate(preliminary_blocks):
        plot_filled_polygon(ax1, block.polygon, color=colors[i], alpha=0.6)
        plot_polygon(ax1, block.polygon, color=colors[i], linewidth=2)

        # Block label
        centroid = block.polygon.centroid
        ax1.text(
            centroid.x,
            centroid.y,
            f"B{block.block_id}",
            ha="center",
            va="center",
            fontsize=10,
            fontweight="bold",
        )

    # Type D obstacles
    for obs in stage1_result.type_d_obstacles:
        plot_filled_polygon(ax1, obs.polygon, color="red", alpha=0.7)
        plot_polygon(ax1, obs.polygon, color="darkred", linewidth=1.5)

    ax1.set_xlabel("X (m)")
    ax1.set_ylabel("Y (m)")
    ax1.grid(True, alpha=0.3)
    ax1.legend()

    # Panel 2: Final blocks after merging
    ax2 = axes[1]
    reduction = len(preliminary_blocks) - len(final_blocks)
    ax2.set_title(f"2. Final Blocks ({len(final_blocks)} blocks, reduced by {reduction})", fontsize=12, fontweight="bold")
    ax2.set_aspect("equal")

    # Final blocks with colors
    colors = plt.cm.Set3(np.linspace(0, 1, len(final_blocks)))
    for i, block in enumerate(final_blocks):
        plot_filled_polygon(ax2, block.polygon, color=colors[i], alpha=0.4)
        plot_polygon(ax2, block.polygon, color="black", linewidth=2)

        # Block label
        centroid = block.polygon.centroid
        ax2.text(
            centroid.x,
            centroid.y,
            f"B{block.block_id}",
            ha="center",
            va="center",
            fontsize=10,
            fontweight="bold",
        )

    # Type D obstacles
    for obs in stage1_result.type_d_obstacles:
        plot_filled_polygon(ax2, obs.polygon, color="red", alpha=0.6)
        plot_polygon(ax2, obs.polygon, color="darkred", linewidth=1.5)

    ax2.set_xlabel("X (m)")
    ax2.set_ylabel("Y (m)")
    ax2.grid(True, alpha=0.3)

    # Panel 3: Blocks with clustered tracks
    ax3 = axes[2]
    total_track_segments = sum(len(b.tracks) for b in final_blocks)
    ax3.set_title(f"3. Blocks with Tracks ({total_track_segments} segments)", fontsize=12, fontweight="bold")
    ax3.set_aspect("equal")

    # Blocks with lighter colors
    colors = plt.cm.Set3(np.linspace(0, 1, len(final_blocks)))
    for i, block in enumerate(final_blocks):
        plot_filled_polygon(ax3, block.polygon, color=colors[i], alpha=0.25)
        plot_polygon(ax3, block.polygon, color=colors[i], linewidth=2)

        # Clustered tracks for this block
        for track in block.tracks:
            ax3.plot(
                [track.start[0], track.end[0]],
                [track.start[1], track.end[1]],
                color="darkgreen",
                linewidth=1.5,
                alpha=0.7
            )

        # Block label with track count
        centroid = block.polygon.centroid
        ax3.text(
            centroid.x,
            centroid.y,
            f"B{block.block_id}\n{len(block.tracks)}T",
            ha="center",
            va="center",
            fontsize=9,
            fontweight="bold",
        )

    # Type D obstacles
    for obs in stage1_result.type_d_obstacles:
        plot_filled_polygon(ax3, obs.polygon, color="red", alpha=0.6)
        plot_polygon(ax3, obs.polygon, color="darkred", linewidth=1.5)

    ax3.set_xlabel("X (m)")
    ax3.set_ylabel("Y (m)")
    ax3.grid(True, alpha=0.3)

    plt.tight_layout()
    return fig


def plot_stage3_result(
    field: Field,
    blocks: List[Block],
    path_plan: PathPlan,
    solver: ACOSolver,
    figsize: Tuple[int, int] = (18, 6)
) -> Tuple[Figure, Figure]:
    """
    Create visualizations for Stage 3 (ACO Path Optimization).

    Returns two figures:
    - Figure 1: Coverage path visualization
    - Figure 2: ACO convergence plot

    Args:
        field: Field object
        blocks: Final blocks with tracks
        path_plan: PathPlan from optimization
        solver: ACOSolver instance
        figsize: Figure size tuple

    Returns:
        Tuple of (path_figure, convergence_figure)
    """
    # Figure 1: Coverage path
    fig_path, ax_path = plt.subplots(figsize=(14, 10))

    # Field boundary
    field_x, field_y = zip(*field.boundary_polygon.exterior.coords)
    ax_path.plot(field_x, field_y, "k-", linewidth=2, label="Field Boundary")

    # Obstacles
    for obs in field.obstacle_polygons:
        obs_x, obs_y = zip(*obs.exterior.coords)
        ax_path.fill(
            obs_x,
            obs_y,
            color="gray",
            alpha=0.5,
            edgecolor="black",
            linewidth=1.5,
        )

    # Blocks (lighter)
    colors = plt.cm.Set3(np.linspace(0, 1, len(blocks)))
    for i, block in enumerate(blocks):
        block_x, block_y = zip(*block.polygon.exterior.coords)
        ax_path.fill(
            block_x,
            block_y,
            color=colors[i],
            alpha=0.3,
            edgecolor=colors[i],
            linewidth=1.5,
        )
        # Block label
        centroid = block.polygon.centroid
        ax_path.text(
            centroid.x,
            centroid.y,
            f"B{block.block_id}",
            ha="center",
            va="center",
            fontsize=9,
            fontweight="bold",
        )

    # Coverage path
    for segment in path_plan.segments:
        if segment.segment_type == "working":
            # Working segments (blue)
            seg_x, seg_y = zip(*segment.waypoints)
            ax_path.plot(seg_x, seg_y, "b-", linewidth=2.5, alpha=0.8)
        else:
            # Transition segments (red dashed)
            seg_x, seg_y = zip(*segment.waypoints)
            ax_path.plot(seg_x, seg_y, "r--", linewidth=2.0, alpha=0.6)

    # Start and end markers
    all_waypoints = path_plan.get_all_waypoints()
    if all_waypoints:
        start_x, start_y = all_waypoints[0]
        end_x, end_y = all_waypoints[-1]
        ax_path.plot(start_x, start_y, "go", markersize=15, markeredgewidth=2, markeredgecolor="darkgreen", label="Start")
        ax_path.plot(end_x, end_y, "rs", markersize=15, markeredgewidth=2, markeredgecolor="darkred", label="End")

    # Calculate efficiency
    efficiency = (path_plan.working_distance / path_plan.total_distance) * 100 if path_plan.total_distance > 0 else 0

    ax_path.set_xlabel("X (meters)", fontsize=12)
    ax_path.set_ylabel("Y (meters)", fontsize=12)
    ax_path.set_title(
        f"Coverage Path (Efficiency: {efficiency:.1f}%)",
        fontsize=14,
        fontweight="bold"
    )
    ax_path.grid(True, alpha=0.3)
    ax_path.set_aspect("equal")
    ax_path.legend(loc="upper right", fontsize=10)

    plt.tight_layout()

    # Figure 2: ACO convergence
    fig_conv, ax_conv = plt.subplots(figsize=(10, 6))

    # Get convergence data
    best_costs, avg_costs = solver.get_convergence_data()

    iterations = list(range(1, len(best_costs) + 1))

    # Plot convergence
    ax_conv.plot(iterations, best_costs, "g-", linewidth=2, label="Best Cost", marker='o', markersize=4)
    ax_conv.plot(iterations, avg_costs, "b--", linewidth=1.5, alpha=0.7, label="Average Cost")

    # Calculate improvement
    if len(best_costs) > 0:
        initial_cost = best_costs[0]
        final_cost = best_costs[-1]
        improvement_pct = ((initial_cost - final_cost) / initial_cost) * 100 if initial_cost > 0 else 0

        # Add improvement annotation
        ax_conv.text(
            0.98, 0.98,
            f"Improvement: {improvement_pct:.1f}%\n"
            f"Initial: {initial_cost:.2f}m\n"
            f"Final: {final_cost:.2f}m",
            transform=ax_conv.transAxes,
            fontsize=10,
            verticalalignment="top",
            horizontalalignment="right",
            bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.5)
        )

    ax_conv.set_xlabel("Iteration", fontsize=12)
    ax_conv.set_ylabel("Cost (distance, m)", fontsize=12)
    ax_conv.set_title("ACO Convergence", fontsize=14, fontweight="bold")
    ax_conv.grid(True, alpha=0.3)
    ax_conv.legend(loc="upper right", fontsize=10)

    plt.tight_layout()

    return fig_path, fig_conv
