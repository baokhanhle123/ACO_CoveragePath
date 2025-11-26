"""
Pheromone visualization for ACO algorithm.

Creates impressive visualizations showing:
- Pheromone trails as colored edges
- Strength indicated by color and thickness
- Best path highlighted
- Evolution over iterations
"""

import matplotlib.pyplot as plt
import numpy as np
from typing import Dict, List, Optional, Tuple
from matplotlib.patches import FancyArrowPatch


class PheromoneVisualizer:
    """
    Visualizes ACO pheromone trails on field layout.

    Creates graph-based visualizations showing:
    - Nodes at actual field coordinates
    - Edges colored/sized by pheromone strength
    - Best path highlighted
    """

    def __init__(self, blocks, nodes, field):
        """
        Initialize pheromone visualizer.

        Args:
            blocks: List of Block objects
            nodes: List of BlockNode objects
            field: Field object with boundary and obstacles
        """
        self.blocks = blocks
        self.nodes = nodes
        self.field = field

        # Calculate node positions from field coordinates
        self.node_positions = self._calculate_node_positions()

    def _calculate_node_positions(self) -> Dict[int, Tuple[float, float]]:
        """
        Extract node positions from field coordinates.

        Returns:
            Dictionary mapping node index to (x, y) position
        """
        positions = {}
        for i, node in enumerate(self.nodes):
            positions[i] = node.position  # position is already a (x, y) tuple
        return positions

    def normalize_pheromone(
        self,
        pheromone_matrix: np.ndarray,
        threshold: float = 0.01
    ) -> np.ndarray:
        """
        Normalize pheromone values for visualization.

        Args:
            pheromone_matrix: Raw pheromone matrix
            threshold: Minimum normalized value to display (filters weak trails)

        Returns:
            Normalized pheromone matrix [0, 1]
        """
        # Get max pheromone
        max_pheromone = pheromone_matrix.max()
        if max_pheromone == 0:
            return pheromone_matrix.copy()

        # Normalize to [0, 1]
        normalized = pheromone_matrix / max_pheromone

        # Filter weak pheromone (set to 0 if below threshold)
        normalized[normalized < threshold] = 0

        return normalized

    def create_pheromone_graph(
        self,
        ax,
        pheromone_matrix: np.ndarray,
        best_solution=None,
        iteration: Optional[int] = None,
        show_field: bool = True,
        show_stats: bool = True
    ):
        """
        Create pheromone graph visualization.

        Args:
            ax: Matplotlib axes to draw on
            pheromone_matrix: Current pheromone matrix
            best_solution: Optional Solution object to highlight
            iteration: Optional iteration number for title
            show_field: Whether to show field/obstacles background
            show_stats: Whether to show statistics
        """
        # Clear axes
        ax.clear()

        # Draw field background if requested
        if show_field:
            self._draw_field_background(ax)

        # Normalize pheromone
        normalized_pheromone = self.normalize_pheromone(pheromone_matrix)

        # Draw edges with pheromone strength
        self._draw_pheromone_edges(ax, normalized_pheromone)

        # Draw nodes
        self._draw_nodes(ax)

        # Highlight best path if provided
        if best_solution:
            self._highlight_best_path(ax, best_solution)

        # Add statistics if requested
        if show_stats and best_solution:
            self._add_statistics(ax, pheromone_matrix, best_solution, iteration)

        # Styling
        ax.set_xlabel('X (meters)', fontsize=11)
        ax.set_ylabel('Y (meters)', fontsize=11)

        if iteration is not None:
            title = f'Pheromone Distribution - Iteration {iteration}'
            if best_solution:
                title += f' (Cost: {best_solution.cost:.1f})'
        else:
            title = 'Pheromone Distribution'

        ax.set_title(title, fontsize=13, fontweight='bold')
        ax.set_aspect('equal')
        ax.grid(True, alpha=0.2)

    def _draw_field_background(self, ax):
        """Draw field boundary and obstacles (light background)."""
        # Field boundary (light)
        field_x, field_y = zip(*self.field.boundary_polygon.exterior.coords)
        ax.plot(field_x, field_y, 'k-', linewidth=1, alpha=0.3)

        # Obstacles (very light)
        for obs in self.field.obstacle_polygons:
            obs_x, obs_y = zip(*obs.exterior.coords)
            ax.fill(
                obs_x, obs_y,
                color='gray',
                alpha=0.1,
                edgecolor='gray',
                linewidth=0.5,
                linestyle='--'
            )

    def _draw_pheromone_edges(self, ax, normalized_pheromone: np.ndarray):
        """
        Draw edges with width and color based on pheromone strength.

        Uses YlOrRd colormap: Yellow (medium) -> Orange -> Red (high)
        """
        # Use colormap: Yellow-Orange-Red for heat effect
        cmap = plt.cm.YlOrRd

        # Track drawn edges to avoid duplicates
        drawn_edges = set()

        # Draw edges with significant pheromone
        for i in range(len(self.nodes)):
            for j in range(len(self.nodes)):
                if i >= j:  # Skip duplicate edges (undirected graph visualization)
                    continue

                # Get bidirectional pheromone (max of both directions)
                pheromone = max(
                    normalized_pheromone[i][j],
                    normalized_pheromone[j][i]
                )

                if pheromone > 0:  # Only draw if pheromone exists
                    x1, y1 = self.node_positions[i]
                    x2, y2 = self.node_positions[j]

                    # Map pheromone to color (use sqrt for better visual distribution)
                    color_intensity = np.sqrt(pheromone)
                    color = cmap(color_intensity)

                    # Map pheromone to line width (0.3 to 3.5)
                    width = 0.3 + pheromone * 3.2

                    # Draw edge
                    ax.plot(
                        [x1, x2], [y1, y2],
                        color=color,
                        linewidth=width,
                        alpha=0.6,
                        zorder=1,
                        solid_capstyle='round'
                    )

    def _draw_nodes(self, ax):
        """Draw nodes as labeled circles."""
        for i, (x, y) in self.node_positions.items():
            # Draw node circle
            ax.plot(
                x, y, 'o',
                color='white',
                markersize=10,
                markeredgecolor='black',
                markeredgewidth=1.5,
                zorder=10
            )

            # Add label (block ID)
            block_id = self.nodes[i].block_id
            ax.text(
                x, y, str(block_id),
                fontsize=7,
                ha='center',
                va='center',
                zorder=11,
                fontweight='bold'
            )

    def _highlight_best_path(self, ax, best_solution):
        """Highlight best solution path with thick green line."""
        path_indices = best_solution.path

        if len(path_indices) < 2:
            return

        # Draw path segments
        for i in range(len(path_indices) - 1):
            from_idx = path_indices[i]
            to_idx = path_indices[i + 1]

            x1, y1 = self.node_positions[from_idx]
            x2, y2 = self.node_positions[to_idx]

            # Draw thick green line with arrow
            ax.plot(
                [x1, x2], [y1, y2],
                color='lime',
                linewidth=4,
                alpha=0.8,
                zorder=100,
                solid_capstyle='round',
                label='Best Path' if i == 0 else ''
            )

            # Add small arrow to show direction
            if i % 2 == 0:  # Add arrows every other segment to avoid clutter
                dx = x2 - x1
                dy = y2 - y1
                ax.arrow(
                    x1 + dx * 0.5, y1 + dy * 0.5,
                    dx * 0.1, dy * 0.1,
                    head_width=1.5,
                    head_length=1.0,
                    fc='darkgreen',
                    ec='darkgreen',
                    alpha=0.7,
                    zorder=101
                )

        # Add legend
        if len(path_indices) > 0:
            ax.legend(loc='upper right', fontsize=10, framealpha=0.9)

    def _add_statistics(self, ax, pheromone_matrix, best_solution, iteration):
        """Add statistics text overlay."""
        # Calculate statistics
        max_pheromone = pheromone_matrix.max()
        avg_pheromone = pheromone_matrix[pheromone_matrix > 0].mean() if pheromone_matrix.max() > 0 else 0
        num_edges_with_pheromone = np.sum(pheromone_matrix > 0.01)

        stats_text = (
            f"Max Pheromone: {max_pheromone:.2f}\n"
            f"Avg Pheromone: {avg_pheromone:.2f}\n"
            f"Active Edges: {num_edges_with_pheromone}\n"
            f"Best Cost: {best_solution.cost:.1f}"
        )

        ax.text(
            0.02, 0.02,
            stats_text,
            transform=ax.transAxes,
            fontsize=9,
            verticalalignment='bottom',
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.85),
            zorder=1000,
            family='monospace'
        )

    def create_colorbar(self, ax, label='Pheromone Strength'):
        """
        Create colorbar showing pheromone intensity scale.

        Args:
            ax: Axes to attach colorbar to
            label: Label for colorbar
        """
        import matplotlib.cm as cm
        from matplotlib.colors import Normalize

        # Create colormap
        cmap = cm.YlOrRd
        norm = Normalize(vmin=0, vmax=1)

        # Create colorbar
        sm = cm.ScalarMappable(cmap=cmap, norm=norm)
        sm.set_array([])

        cbar = plt.colorbar(sm, ax=ax, orientation='vertical', pad=0.02, shrink=0.8)
        cbar.set_label(label, fontsize=10)

        return cbar
