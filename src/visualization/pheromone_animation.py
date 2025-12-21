"""
Pheromone visualization and animation for ACO optimization.

Provides PheromoneAnimator class for visualizing pheromone trail evolution
during ACO optimization process.
"""

from typing import Optional
from io import BytesIO

import matplotlib.animation as animation
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

from ..data import Field, Block
from ..optimization import ACOSolver


class PheromoneAnimator:
    """
    Animates the evolution of pheromone trails during ACO optimization.

    Features:
    - Pheromone matrix visualization as heatmap
    - Node-to-node connection strengths
    - Evolution over iterations (if history is recorded)
    """

    def __init__(
        self,
        solver: ACOSolver,
        field: Field,
        blocks: list,
        figsize: tuple = (14, 10),
        fps: int = 2,
    ):
        """
        Initialize the pheromone animator.

        Args:
            solver: ACOSolver instance (should have record_history=True for animation)
            field: Field object
            blocks: List of blocks
            figsize: Figure size tuple
            fps: Frames per second for animation
        """
        self.solver = solver
        self.field = field
        self.blocks = blocks
        self.figsize = figsize
        self.fps = fps

        # Get pheromone data
        self.pheromone = solver.pheromone
        self.num_nodes = solver.num_nodes

        # Check if solver recorded history
        self.has_history = bool(getattr(solver, 'pheromone_history', None))
        self.history_iterations = getattr(solver, 'pheromone_history_iterations', None)

        # Animation state
        self.fig = None
        self.ax = None
        self.heatmap = None

    def _setup_figure(self):
        """Setup the matplotlib figure."""
        self.fig, self.ax = plt.subplots(figsize=self.figsize)

        # Initial heatmap (will be updated in animation)
        if self.has_history and self.solver.pheromone_history:
            initial_data = self.solver.pheromone_history[0]
        else:
            initial_data = self.pheromone

        self.heatmap = self.ax.imshow(
            initial_data,
            cmap='YlOrRd',
            interpolation='nearest',
            aspect='auto'
        )

        # Colorbar
        cbar = plt.colorbar(self.heatmap, ax=self.ax)
        cbar.set_label('Pheromone Intensity', fontsize=12)

        # Labels
        self.ax.set_xlabel('Node Index', fontsize=12)
        self.ax.set_ylabel('Node Index', fontsize=12)
        self.ax.set_title(
            'ACO Pheromone Matrix Evolution',
            fontsize=14,
            fontweight='bold'
        )

        # Grid
        self.ax.set_xticks(np.arange(0, self.num_nodes, 4))
        self.ax.set_yticks(np.arange(0, self.num_nodes, 4))
        self.ax.grid(True, alpha=0.3, linewidth=0.5)

        plt.tight_layout()

    def animate_frame(self, frame):
        """Update function for animation."""
        if self.has_history and frame < len(self.solver.pheromone_history):
            # Update heatmap with historical data
            data = self.solver.pheromone_history[frame]
            self.heatmap.set_data(data)

            # Update title with iteration number
            iteration_label = frame + 1
            if self.history_iterations and frame < len(self.history_iterations):
                iteration_label = self.history_iterations[frame]

            self.ax.set_title(
                (
                    'ACO Pheromone Matrix - Initial'
                    if iteration_label == 0
                    else f'ACO Pheromone Matrix - Iteration {iteration_label}'
                ),
                fontsize=14,
                fontweight='bold'
            )

            # Update color limits if needed
            vmax = np.max(data)
            self.heatmap.set_clim(vmin=0, vmax=vmax)

        return [self.heatmap]

    def create_animation(
        self,
        interval: int = None,
        repeat: bool = True
    ):
        """
        Create and return the animation.

        Args:
            interval: Milliseconds between frames (calculated from fps if None)
            repeat: Whether to loop the animation

        Returns:
            matplotlib.animation.FuncAnimation object or None if no history
        """
        # Setup figure
        self._setup_figure()

        if not self.has_history:
            # No history available, return static figure
            return None

        # Calculate interval from fps if not provided
        if interval is None:
            interval = int(1000 / self.fps)

        # Number of frames = number of recorded iterations
        num_frames = len(self.solver.pheromone_history)

        anim = animation.FuncAnimation(
            self.fig,
            self.animate_frame,
            frames=num_frames,
            interval=interval,
            repeat=repeat,
            blit=False,
        )

        return anim

    def save_animation(
        self,
        filename: str,
        fps: int = None,
        dpi: int = 100,
        writer: str = "pillow"
    ):
        """
        Save animation to file.

        Args:
            filename: Output filename (GIF or MP4)
            fps: Frames per second (uses self.fps if None)
            dpi: DPI for output
            writer: Animation writer ('pillow' for GIF, 'ffmpeg' for MP4)
        """
        if fps is None:
            fps = self.fps

        if not self.has_history:
            self._save_static_output(filename, dpi)
            return

        # Create animation
        anim = self.create_animation()

        # Save
        lowered = filename.lower()
        if lowered.endswith(".gif"):
            anim.save(filename, writer="pillow", fps=fps, dpi=dpi)
        elif lowered.endswith(".mp4"):
            anim.save(
                filename,
                writer="ffmpeg",
                fps=fps,
                dpi=dpi,
                bitrate=1800,
                extra_args=["-vcodec", "libx264"],
            )
        else:
            # Default to GIF
            anim.save(filename, writer="pillow", fps=fps, dpi=dpi)

        plt.close(self.fig)

    def _save_static_output(self, filename: str, dpi: int) -> None:
        """Save a static visualization when history is unavailable."""
        self._setup_figure()

        lowered = filename.lower()
        if lowered.endswith(".mp4"):
            plt.close(self.fig)
            raise ValueError("MP4 output requires pheromone history; enable record_history=True.")

        if lowered.endswith(".gif"):
            buffer = BytesIO()
            self.fig.savefig(buffer, format="png", dpi=dpi, bbox_inches='tight')
            buffer.seek(0)
            image = Image.open(buffer)
            image.save(filename, format="GIF", save_all=True)
            image.close()
            buffer.close()
        else:
            self.fig.savefig(filename, dpi=dpi, bbox_inches='tight')

        plt.close(self.fig)


def animate_pheromone_evolution(
    solver: ACOSolver,
    field: Field,
    blocks: list,
    fps: int = 2,
    save_path: Optional[str] = None,
):
    """
    Convenience function to create and display/save pheromone animation.

    Args:
        solver: ACOSolver instance (should have record_history=True)
        field: Field object
        blocks: List of blocks
        fps: Frames per second
        save_path: Optional path to save animation

    Returns:
        PheromoneAnimator object
    """
    animator = PheromoneAnimator(
        solver=solver,
        field=field,
        blocks=blocks,
        fps=fps,
    )

    if save_path:
        animator.save_animation(save_path, fps=fps)

    return animator
