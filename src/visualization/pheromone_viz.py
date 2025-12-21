"""
Pheromone visualization utilities for ACO optimization.

Provides static visualization tools for pheromone matrices.
"""

from typing import List, Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.figure import Figure
from matplotlib.lines import Line2D

from ..data import Field, Block, BlockNode
from ..optimization import ACOSolver


class PheromoneVisualizer:
    """
    Static visualization of pheromone matrices from ACO optimization.

    Provides tools for visualizing pheromone trail intensities as heatmaps.
    """

    def __init__(self, solver: ACOSolver):
        """
        Initialize the pheromone visualizer.

        Args:
            solver: ACOSolver instance with pheromone matrix
        """
        self.solver = solver
        self.pheromone = solver.pheromone
        self.num_nodes = solver.num_nodes

    def plot_pheromone_matrix(
        self,
        ax=None,
        figsize=(10, 8),
        cmap='YlOrRd',
        title='ACO Pheromone Matrix'
    ):
        """
        Plot the pheromone matrix as a heatmap.

        Args:
            ax: Matplotlib axes (creates new if None)
            figsize: Figure size if creating new figure
            cmap: Colormap for heatmap
            title: Plot title

        Returns:
            Matplotlib axes object
        """
        if ax is None:
            fig, ax = plt.subplots(figsize=figsize)

        # Create heatmap
        im = ax.imshow(
            self.pheromone,
            cmap=cmap,
            interpolation='nearest',
            aspect='auto'
        )

        # Colorbar
        plt.colorbar(im, ax=ax, label='Pheromone Intensity')

        # Labels
        ax.set_xlabel('Node Index', fontsize=12)
        ax.set_ylabel('Node Index', fontsize=12)
        ax.set_title(title, fontsize=14, fontweight='bold')

        # Grid
        ax.set_xticks(np.arange(0, self.num_nodes, 4))
        ax.set_yticks(np.arange(0, self.num_nodes, 4))
        ax.grid(True, alpha=0.3, linewidth=0.5)

        return ax


def plot_pheromone_trails_at_iteration(
    field: Field,
    blocks: List[Block],
    nodes: List[BlockNode],
    solver: ACOSolver,
    cost_matrix: np.ndarray,
    iteration_index: int,
    figsize: Tuple[int, int] = (16, 10),
    min_pheromone_threshold: float = 0.01,
    max_edges: Optional[int] = None,
) -> Figure:
    """
    Plot pheromone trails on field map for a specific ACO iteration.

    Shows pheromone intensity as lines connecting nodes, with thickness and color
    based on pheromone strength. Similar to PheromoneTrailAnimator but for static
    visualization at a single iteration.

    Args:
        field: Field object with boundary and obstacles
        blocks: List of blocks from decomposition
        nodes: List of BlockNode objects (entry/exit nodes)
        solver: ACOSolver instance with pheromone_history recorded
        cost_matrix: Cost matrix for filtering valid edges
        iteration_index: Index into pheromone_history (0 = initial, -1 = final)
        figsize: Figure size tuple
        min_pheromone_threshold: Minimum normalized pheromone to display (default 0.01)
        max_edges: Maximum number of edges to show (None = all valid edges)

    Returns:
        matplotlib Figure object

    Raises:
        ValueError: If solver doesn't have pheromone_history or iteration_index is invalid
    """
    # Check if solver has history
    has_history = bool(getattr(solver, 'pheromone_history', None))
    if not has_history:
        raise ValueError("Solver must have record_history=True to visualize pheromone evolution")

    pheromone_history = solver.pheromone_history
    history_iterations = getattr(solver, 'pheromone_history_iterations', None)

    # Validate iteration index
    if iteration_index < 0:
        iteration_index = len(pheromone_history) + iteration_index
    if iteration_index >= len(pheromone_history):
        raise ValueError(f"Iteration index {iteration_index} out of range [0, {len(pheromone_history)})")

    # Get pheromone matrix for this iteration
    pheromone_matrix = pheromone_history[iteration_index]

    # Get iteration number (may differ from index if history_interval > 1)
    iteration_num = iteration_index
    if history_iterations and iteration_index < len(history_iterations):
        iteration_num = history_iterations[iteration_index]
    total_iterations = solver.params.num_iterations

    # Extract node positions
    node_positions = [node.position for node in nodes]
    num_nodes = len(nodes)

    # Filter valid edges (exclude infinite cost transitions)
    valid_edges = []
    for i in range(num_nodes):
        for j in range(i + 1, num_nodes):  # Only upper triangle (symmetric matrix)
            if cost_matrix[i][j] < 1e9:  # Valid transition
                valid_edges.append((i, j))

    # Limit edges if requested
    if max_edges is not None and len(valid_edges) > max_edges:
        # Keep edges with highest average pheromone (use current iteration)
        edge_scores = []
        for i, j in valid_edges:
            avg_pheromone = (pheromone_matrix[i][j] + pheromone_matrix[j][i]) / 2.0
            edge_scores.append((avg_pheromone, (i, j)))
        edge_scores.sort(reverse=True)
        valid_edges = [edge for _, edge in edge_scores[:max_edges]]

    # Calculate global pheromone range for normalization
    global_pheromone_max = 0.0
    for pm in pheromone_history:
        global_pheromone_max = max(global_pheromone_max, np.max(pm))
    # Add small epsilon to avoid division by zero
    if global_pheromone_max < 1e-10:
        global_pheromone_max = 1.0

    # Visual parameters
    min_line_width = 0.5
    max_line_width = 6.0
    min_alpha = 0.2
    max_alpha = 1.0
    colormap = plt.cm.YlOrRd  # Yellow-Orange-Red colormap

    # Create figure
    fig, ax = plt.subplots(figsize=figsize)

    # Draw field boundary
    field_x, field_y = zip(*field.boundary_polygon.exterior.coords)
    ax.plot(field_x, field_y, "k-", linewidth=2.5, label="Field Boundary", zorder=1)

    # Draw obstacles
    for i, obs in enumerate(field.obstacle_polygons):
        obs_x, obs_y = zip(*obs.exterior.coords)
        ax.fill(
            obs_x,
            obs_y,
            color="gray",
            alpha=0.5,
            edgecolor="black",
            linewidth=1.5,
            zorder=2,
        )

    # Draw blocks with different colors
    colors = plt.cm.Set3(np.linspace(0, 1, len(blocks)))
    for i, block in enumerate(blocks):
        block_x, block_y = zip(*block.polygon.exterior.coords)
        color = colors[i]
        ax.fill(
            block_x,
            block_y,
            color=color,
            alpha=0.25,
            edgecolor=color,
            linewidth=1.5,
            zorder=3,
        )
        # Add block label
        centroid = block.polygon.centroid
        ax.text(
            centroid.x,
            centroid.y,
            f"Block {block.block_id}",
            ha="center",
            va="center",
            fontsize=9,
            fontweight="bold",
            zorder=4,
        )

    # Draw pheromone trails
    for i, j in valid_edges:
        # Get average pheromone (symmetric matrix)
        avg_pheromone = (pheromone_matrix[i][j] + pheromone_matrix[j][i]) / 2.0
        normalized = avg_pheromone / global_pheromone_max

        # Skip if below threshold
        if normalized < min_pheromone_threshold:
            continue

        # Map to visual properties
        line_width = min_line_width + normalized * (max_line_width - min_line_width)
        line_alpha = min_alpha + normalized * (max_alpha - min_alpha)
        line_color = colormap(normalized)

        # Get node positions
        pos_i = node_positions[i]
        pos_j = node_positions[j]

        # Draw line
        ax.plot(
            [pos_i[0], pos_j[0]],
            [pos_i[1], pos_j[1]],
            color=line_color,
            linewidth=line_width,
            alpha=line_alpha,
            zorder=5,
        )

    # Draw nodes as small markers
    for node in nodes:
        x, y = node.position
        ax.plot(
            x, y,
            marker="o",
            markersize=4,
            color="black",
            zorder=6,
        )

    # Add colorbar
    sm = plt.cm.ScalarMappable(
        cmap=colormap,
        norm=plt.Normalize(vmin=0, vmax=global_pheromone_max)
    )
    sm.set_array([])
    colorbar = plt.colorbar(sm, ax=ax, label='Pheromone Intensity', pad=0.02)
    colorbar.ax.tick_params(labelsize=9)

    # Setup axes
    ax.set_xlabel("X (meters)", fontsize=12)
    ax.set_ylabel("Y (meters)", fontsize=12)
    ax.set_title(
        f"ACO Pheromone Evolution - Iteration {iteration_num}/{total_iterations}",
        fontsize=14,
        fontweight="bold",
    )
    ax.grid(True, alpha=0.3)
    ax.set_aspect("equal")

    # Legend
    legend_elements = [
        Line2D(
            [0], [0],
            color=colormap(0.8),
            linewidth=max_line_width,
            label="Strong Trail (High Pheromone)",
        ),
        Line2D(
            [0], [0],
            color=colormap(0.4),
            linewidth=(min_line_width + max_line_width) / 2,
            label="Weak Trail (Low Pheromone)",
        ),
    ]
    ax.legend(handles=legend_elements, loc="upper right", fontsize=10)

    plt.tight_layout()

    return fig
