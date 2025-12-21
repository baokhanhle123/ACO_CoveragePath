"""
Pheromone visualization utilities for ACO optimization.

Provides static visualization tools for pheromone matrices.
"""

import matplotlib.pyplot as plt
import numpy as np

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
