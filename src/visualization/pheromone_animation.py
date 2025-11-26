"""
Pheromone evolution animation for ACO algorithm.

Creates impressive animations showing:
- Pheromone trails evolving over iterations
- Best path emerging
- Convergence plot alongside
- Statistical overlays
"""

import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
from typing import Optional
import time

from .pheromone_viz import PheromoneVisualizer


class PheromoneAnimator:
    """
    Animates ACO pheromone evolution over iterations.

    Creates multi-panel animations showing:
    - Pheromone graph evolution (main panel)
    - Convergence plot (side panel)
    - Best path highlighting
    """

    def __init__(self, solver, field, blocks):
        """
        Initialize pheromone animator.

        Args:
            solver: ACOSolver instance with record_history=True
            field: Field object
            blocks: List of Block objects

        Raises:
            ValueError: If solver doesn't have history recorded
        """
        # Get pheromone history from solver
        self.iterations, self.pheromones, self.solutions = solver.get_pheromone_history()

        if len(self.iterations) == 0:
            raise ValueError("No pheromone history found. Ensure record_history=True when running solver.")

        self.field = field
        self.blocks = blocks
        self.nodes = solver.nodes

        # Create visualizer
        self.visualizer = PheromoneVisualizer(blocks, self.nodes, field)

        # Get convergence data
        self.global_best_costs, self.avg_costs = solver.get_convergence_data()

        # Animation state
        self.fig = None
        self.ax_pheromone = None
        self.ax_convergence = None

    def create_animation(
        self,
        figsize=(18, 8),
        fps=2,
        show_field=True,
        show_stats=True
    ):
        """
        Create animation with dual panels.

        Layout:
        ┌────────────────────┬──────────┐
        │                    │          │
        │  Pheromone Graph   │Convergence│
        │     (main)         │  Plot    │
        │                    │          │
        └────────────────────┴──────────┘

        Args:
            figsize: Figure size (width, height)
            fps: Frames per second (recommended: 1-3 for clarity)
            show_field: Show field boundary and obstacles
            show_stats: Show statistics overlay

        Returns:
            matplotlib.animation.FuncAnimation object
        """
        # Create figure with two subplots
        self.fig = plt.figure(figsize=figsize)

        # Create grid: 70% for pheromone, 30% for convergence
        gs = self.fig.add_gridspec(1, 2, width_ratios=[7, 3], hspace=0.3, wspace=0.3)

        self.ax_pheromone = self.fig.add_subplot(gs[0, 0])
        self.ax_convergence = self.fig.add_subplot(gs[0, 1])

        # Store display options
        self.show_field = show_field
        self.show_stats = show_stats

        # Calculate interval
        interval = 1000 / fps

        # Create animation
        anim = animation.FuncAnimation(
            self.fig,
            self.animate_frame,
            init_func=self.init_animation,
            frames=len(self.iterations),
            interval=interval,
            blit=False,
            repeat=True
        )

        return anim

    def init_animation(self):
        """Initialize animation (first frame setup)."""
        # Clear both axes
        self.ax_pheromone.clear()
        self.ax_convergence.clear()
        return []

    def animate_frame(self, frame_idx):
        """
        Animate single frame.

        Args:
            frame_idx: Frame index (corresponds to snapshot index)

        Returns:
            List of artists (empty for blit=False)
        """
        # Get data for this frame
        iteration = self.iterations[frame_idx]
        pheromone = self.pheromones[frame_idx]
        solution = self.solutions[frame_idx]

        # Update pheromone graph (left panel)
        self.visualizer.create_pheromone_graph(
            self.ax_pheromone,
            pheromone_matrix=pheromone,
            best_solution=solution,
            iteration=iteration,
            show_field=self.show_field,
            show_stats=self.show_stats
        )

        # Update convergence plot (right panel)
        self._update_convergence_plot(frame_idx, iteration)

        return []

    def _update_convergence_plot(self, current_frame_idx, current_iteration):
        """
        Update convergence plot with current progress.

        Args:
            current_frame_idx: Current frame index
            current_iteration: Current iteration number
        """
        ax = self.ax_convergence
        ax.clear()

        # Get data up to current iteration
        iterations_so_far = list(range(len(self.global_best_costs)))

        # Plot full convergence curves (show complete evolution)
        ax.plot(
            iterations_so_far, self.global_best_costs,
            'g-',
            linewidth=2.5,
            label='Best Cost',
            zorder=2
        )

        ax.plot(
            iterations_so_far, self.avg_costs,
            'b--',
            linewidth=1.5,
            alpha=0.6,
            label='Avg Cost',
            zorder=1
        )

        # Highlight current iteration
        if current_iteration < len(self.global_best_costs):
            # Vertical line at current iteration
            ax.axvline(
                current_iteration,
                color='red',
                linestyle='--',
                linewidth=2,
                alpha=0.5,
                label=f'Current (Iter {current_iteration})',
                zorder=3
            )

            # Marker on best cost curve
            ax.plot(
                current_iteration,
                self.global_best_costs[current_iteration],
                'ro',
                markersize=10,
                zorder=10,
                markeredgecolor='darkred',
                markeredgewidth=2
            )

        # Styling
        ax.set_xlabel('Iteration', fontsize=11)
        ax.set_ylabel('Cost', fontsize=11)
        ax.set_title('ACO Convergence', fontsize=12, fontweight='bold')
        ax.legend(loc='upper right', fontsize=9, framealpha=0.9)
        ax.grid(True, alpha=0.3)

        # Set y-axis limits with some padding
        if len(self.global_best_costs) > 0:
            y_min = min(min(self.global_best_costs), min(self.avg_costs))
            y_max = max(max(self.global_best_costs), max(self.avg_costs))
            y_range = y_max - y_min
            ax.set_ylim(y_min - y_range * 0.1, y_max + y_range * 0.1)

        # Add improvement statistics
        if len(self.global_best_costs) > 0:
            initial_cost = self.global_best_costs[0]
            current_cost = self.global_best_costs[min(current_iteration, len(self.global_best_costs) - 1)]
            improvement = ((initial_cost - current_cost) / initial_cost) * 100

            stats_text = (
                f"Initial: {initial_cost:.1f}\n"
                f"Current: {current_cost:.1f}\n"
                f"Improvement: {improvement:.1f}%"
            )

            ax.text(
                0.05, 0.05,
                stats_text,
                transform=ax.transAxes,
                fontsize=9,
                verticalalignment='bottom',
                bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8),
                family='monospace'
            )

    def save_animation(
        self,
        filename,
        dpi=100,
        fps=2,
        show_field=True,
        show_stats=True
    ):
        """
        Create and save animation to file.

        Args:
            filename: Output filename (.gif or .mp4)
            dpi: Resolution (100 recommended for GIF, 150 for MP4)
            fps: Frames per second (1-3 recommended)
            show_field: Show field background
            show_stats: Show statistics overlays
        """
        print(f"Creating pheromone animation with {len(self.iterations)} frames...")
        start_time = time.time()

        # Create animation
        anim = self.create_animation(
            fps=fps,
            show_field=show_field,
            show_stats=show_stats
        )

        # Determine writer
        if filename.endswith('.mp4'):
            writer = 'ffmpeg'
        else:
            writer = 'pillow'

        print(f"Saving to {filename}...")
        try:
            anim.save(filename, writer=writer, dpi=dpi)
            elapsed = time.time() - start_time
            print(f"✓ Pheromone animation saved to {filename} ({elapsed:.1f} seconds)")
        except Exception as e:
            print(f"✗ Error saving animation: {e}")
            if writer == 'ffmpeg':
                print("  Hint: Install ffmpeg for MP4 support, or use .gif extension")
        finally:
            plt.close()


def animate_pheromone_evolution(
    solver,
    field,
    blocks,
    output_file='pheromone_evolution.gif',
    fps=2,
    dpi=100,
    figsize=(18, 8)
):
    """
    Convenience function to create pheromone animation.

    Args:
        solver: ACOSolver with history recorded
        field: Field object
        blocks: List of blocks
        output_file: Output filename (.gif recommended)
        fps: Frames per second (1-3 recommended for clarity)
        dpi: Resolution
        figsize: Figure size

    Returns:
        PheromoneAnimator instance
    """
    animator = PheromoneAnimator(solver, field, blocks)
    animator.save_animation(output_file, dpi=dpi, fps=fps)
    return animator
