"""
Path animation visualization for coverage path planning.

Provides PathAnimator class for creating animated visualizations of the
optimal coverage path from the three-stage process.
"""

from typing import Optional

import matplotlib.animation as animation
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D

from ..data import Field, Block
from ..optimization import PathPlan


class PathAnimator:
    """
    Animates the traversal of an optimal coverage path.

    Features:
    - Progressive path drawing (working vs transition segments)
    - Moving vehicle marker
    - Real-time statistics overlay
    - Current block highlighting
    """

    def __init__(
        self,
        field: Field,
        blocks: list,
        path_plan: PathPlan,
        stats: dict = None,
        figsize: tuple = (16, 10),
        speed_multiplier: float = 1.0,
        show_stats: bool = True,
        trail_gap: int = 0,
        fps: int = 30,
    ):
        """
        Initialize the path animator.

        Args:
            field: Field object with boundary and obstacles
            blocks: List of blocks from decomposition
            path_plan: PathPlan with segments and waypoints
            stats: Path statistics dictionary (optional)
            figsize: Figure size tuple
            speed_multiplier: Animation speed multiplier (1.0 = normal, >1.0 = faster)
            show_stats: Whether to show statistics overlay
            trail_gap: Number of waypoints behind vehicle to leave gap (0 = path connects exactly to vehicle)
            fps: Frames per second for animation
        """
        self.field = field
        self.blocks = blocks
        self.path_plan = path_plan
        self.stats = stats if stats is not None else self._compute_default_stats()
        self.speed_multiplier = speed_multiplier
        self.show_stats = show_stats
        self.trail_gap = max(0, int(trail_gap))
        self.fps = fps

        # Flatten all waypoints with segment information.
        # IMPORTANT: we keep *all* waypoints (including duplicates at segment
        # boundaries) so that geometry is never lost.
        self.waypoints = []
        self.waypoint_segments = []  # Track which segment each waypoint belongs to
        self.waypoint_distances = []  # Cumulative distance at each waypoint

        cumulative_distance = 0.0
        prev_waypoint = None
        for seg_idx, segment in enumerate(path_plan.segments):
            for waypoint in segment.waypoints:
                # Store geometry for animation
                self.waypoints.append(waypoint)
                self.waypoint_segments.append(seg_idx)

                # Update distance (0 added when consecutive waypoints are identical)
                if prev_waypoint is not None:
                    dx = waypoint[0] - prev_waypoint[0]
                    dy = waypoint[1] - prev_waypoint[1]
                    cumulative_distance += np.sqrt(dx * dx + dy * dy)

                self.waypoint_distances.append(cumulative_distance)
                prev_waypoint = waypoint

        # Animation state
        self.current_index = 0
        self.fig = None
        self.ax = None
        self.path_lines = {}  # Store line objects for each segment
        self.vehicle_marker = None
        self.stats_text = None
        self.current_block_highlight = None

        # Setup figure
        self._setup_figure(figsize)

    def _compute_default_stats(self):
        """Compute default statistics from path plan."""
        total_distance = self.path_plan.total_distance
        working_distance = self.path_plan.working_distance
        efficiency = (working_distance / total_distance) if total_distance > 0 else 0

        return {
            'total_distance': total_distance,
            'working_distance': working_distance,
            'transition_distance': self.path_plan.transition_distance,
            'efficiency': efficiency,
        }

    def _setup_figure(self, figsize):
        """Setup the matplotlib figure and static elements."""
        self.fig, self.ax = plt.subplots(figsize=figsize)

        # Draw field boundary
        field_x, field_y = zip(*self.field.boundary_polygon.exterior.coords)
        self.ax.plot(field_x, field_y, "k-", linewidth=2.5, label="Field Boundary", zorder=1)

        # Draw obstacles
        for i, obs in enumerate(self.field.obstacle_polygons):
            obs_x, obs_y = zip(*obs.exterior.coords)
            self.ax.fill(
                obs_x,
                obs_y,
                color="gray",
                alpha=0.5,
                edgecolor="black",
                linewidth=1.5,
                zorder=2,
            )

        # Draw blocks with different colors
        colors = plt.cm.Set3(np.linspace(0, 1, len(self.blocks)))
        self.block_colors = {}
        for i, block in enumerate(self.blocks):
            block_x, block_y = zip(*block.polygon.exterior.coords)
            color = colors[i]
            self.block_colors[block.block_id] = color
            self.ax.fill(
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
            self.ax.text(
                centroid.x,
                centroid.y,
                f"Block {block.block_id}",
                ha="center",
                va="center",
                fontsize=9,
                fontweight="bold",
                zorder=4,
            )

        # Initialize path lines (empty, will be drawn progressively)
        for seg_idx, segment in enumerate(self.path_plan.segments):
            line_style = "-" if segment.segment_type == "working" else "--"
            line_width = 2.5 if segment.segment_type == "working" else 2.0
            line_color = "blue" if segment.segment_type == "working" else "red"
            line_alpha = 0.0  # Start invisible

            line, = self.ax.plot(
                [],
                [],
                line_style,
                linewidth=line_width,
                color=line_color,
                alpha=line_alpha,
                zorder=5,
            )
            self.path_lines[seg_idx] = line

        # Mark start point
        if self.waypoints:
            start_x, start_y = self.waypoints[0]
            self.ax.plot(
                start_x,
                start_y,
                "go",
                markersize=15,
                markeredgewidth=2,
                markeredgecolor="darkgreen",
                label="Start",
                zorder=9,
            )

        # Initialize vehicle marker (tractor icon)
        self.vehicle_marker = self.ax.plot(
            [],
            [],
            marker="s",
            markersize=12,
            color="darkgreen",
            markerfacecolor="yellow",
            markeredgewidth=2,
            markeredgecolor="darkgreen",
            zorder=10,
        )[0]

        # Statistics text overlay
        if self.show_stats:
            self.stats_text = self.ax.text(
                0.02,
                0.98,
                "",
                transform=self.ax.transAxes,
                fontsize=11,
                verticalalignment="top",
                bbox=dict(boxstyle="round", facecolor="white", alpha=0.9, edgecolor="black"),
                zorder=11,
            )

        # Current block highlight
        self.current_block_highlight = None

        # Setup axes
        self.ax.set_xlabel("X (meters)", fontsize=12)
        self.ax.set_ylabel("Y (meters)", fontsize=12)
        self.ax.set_title(
            "Animated Coverage Path - Optimal Route Traversal",
            fontsize=14,
            fontweight="bold",
        )
        self.ax.grid(True, alpha=0.3)
        self.ax.set_aspect("equal")

        # Mark end point
        if self.waypoints:
            end_x, end_y = self.waypoints[-1]
            self.ax.plot(
                end_x,
                end_y,
                "rs",
                markersize=15,
                markeredgewidth=2,
                markeredgecolor="darkred",
                label="End",
                zorder=9,
            )

        # Legend
        legend_elements = [
            Line2D([0], [0], color="blue", linewidth=2.5, label="Working Path"),
            Line2D([0], [0], color="red", linestyle="--", linewidth=2, label="Transition"),
            Line2D(
                [0],
                [0],
                marker="s",
                markersize=10,
                color="darkgreen",
                markerfacecolor="yellow",
                label="Vehicle",
                linestyle="None",
            ),
        ]
        self.ax.legend(handles=legend_elements, loc="upper right", fontsize=10)

        plt.tight_layout()

    def _update_path_drawing(self, current_index):
        """Update the path drawing up to the vehicle's current position (trail effect)."""
        # Calculate the maximum waypoint index to draw
        # If trail_gap is 0, path extends exactly to vehicle position
        # If trail_gap > 0, path extends to current_index - trail_gap (leaving a gap)
        max_draw_index = max(0, current_index - self.trail_gap)

        # Determine which segments and waypoints to show
        segments_drawn = set()
        waypoints_to_draw = {}

        # Draw waypoints up to max_draw_index (extends to vehicle when trail_gap=0)
        for i in range(min(max_draw_index + 1, len(self.waypoints))):
            seg_idx = self.waypoint_segments[i]
            segments_drawn.add(seg_idx)

            if seg_idx not in waypoints_to_draw:
                waypoints_to_draw[seg_idx] = []

            waypoints_to_draw[seg_idx].append(self.waypoints[i])

        # Update each segment line
        for seg_idx, segment in enumerate(self.path_plan.segments):
            line = self.path_lines[seg_idx]

            if seg_idx in waypoints_to_draw and len(waypoints_to_draw[seg_idx]) > 1:
                # Draw this segment progressively
                wp_x, wp_y = zip(*waypoints_to_draw[seg_idx])
                line.set_data(wp_x, wp_y)
                line.set_alpha(0.8 if segment.segment_type == "working" else 0.6)
            elif seg_idx in segments_drawn:
                # Segment is complete, show fully
                seg_x, seg_y = zip(*segment.waypoints)
                line.set_data(seg_x, seg_y)
                line.set_alpha(0.8 if segment.segment_type == "working" else 0.6)
            else:
                # Segment not reached yet
                line.set_alpha(0.0)

    def _update_vehicle_position(self, current_index):
        """Update vehicle marker position."""
        if current_index < len(self.waypoints):
            x, y = self.waypoints[current_index]
            self.vehicle_marker.set_data([x], [y])

    def _update_statistics(self, current_index):
        """Update statistics overlay."""
        if not self.show_stats or self.stats_text is None:
            return

        if current_index < len(self.waypoints):
            current_distance = self.waypoint_distances[current_index]
            progress = (current_index / len(self.waypoints)) * 100 if len(self.waypoints) > 0 else 0

            # Find current segment and block
            seg_idx = self.waypoint_segments[current_index]
            current_segment = self.path_plan.segments[seg_idx]
            current_block_id = (
                current_segment.block_id if current_segment.segment_type == "working" else -1
            )

            segment_type_str = (
                f"Working (Block {current_block_id})"
                if current_segment.segment_type == "working"
                else "Transition"
            )

            stats_str = (
                f"Progress: {progress:.1f}%\n"
                f"Distance: {current_distance:.1f}m / {self.stats['total_distance']:.1f}m\n"
                f"Segment: {segment_type_str}\n"
                f"Efficiency: {self.stats['efficiency']*100:.1f}%\n"
                f"Blocks: {len(self.blocks)}\n"
                f"Segments: {len(self.path_plan.segments)}"
            )

            self.stats_text.set_text(stats_str)

    def _update_block_highlight(self, current_index):
        """Highlight the current block being worked on."""
        if current_index < len(self.waypoints):
            seg_idx = self.waypoint_segments[current_index]
            current_segment = self.path_plan.segments[seg_idx]

            if current_segment.segment_type == "working" and current_segment.block_id >= 0:
                # Find the block
                block = next(
                    (b for b in self.blocks if b.block_id == current_segment.block_id), None
                )

                if block:
                    # Remove previous highlight
                    if self.current_block_highlight is not None:
                        self.current_block_highlight.remove()

                    # Add new highlight
                    block_x, block_y = zip(*block.polygon.exterior.coords)
                    self.current_block_highlight = self.ax.fill(
                        block_x,
                        block_y,
                        color=self.block_colors[block.block_id],
                        alpha=0.5,
                        edgecolor="yellow",
                        linewidth=3,
                        zorder=3,
                    )[0]

    def animate_frame(self, frame):
        """Update function for animation."""
        # Calculate current waypoint index based on frame and speed
        max_index = len(self.waypoints) - 1
        # Use speed_multiplier to control how many waypoints per frame
        waypoints_per_frame = max(1, int(self.speed_multiplier))
        current_index = min(frame * waypoints_per_frame, max_index)

        self.current_index = current_index

        # Update all visual elements
        self._update_path_drawing(current_index)
        self._update_vehicle_position(current_index)
        self._update_statistics(current_index)
        self._update_block_highlight(current_index)

        return (
            list(self.path_lines.values())
            + [self.vehicle_marker]
            + ([self.stats_text] if self.stats_text else [])
            + ([self.current_block_highlight] if self.current_block_highlight else [])
        )

    def create_animation(
        self, interval: int = None, repeat: bool = True
    ):
        """
        Create and return the animation.

        Args:
            interval: Milliseconds between frames (calculated from fps if None)
            repeat: Whether to loop the animation

        Returns:
            matplotlib.animation.FuncAnimation object
        """
        # Calculate interval from fps if not provided
        if interval is None:
            interval = int(1000 / self.fps)

        # Calculate number of frames needed
        waypoints_per_frame = max(1, int(self.speed_multiplier))
        num_frames = (len(self.waypoints) + waypoints_per_frame - 1) // waypoints_per_frame

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
        self, filename: str, fps: int = None, dpi: int = 100, writer: str = "pillow"
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

        # Create animation
        anim = self.create_animation()

        # Save
        if filename.endswith(".gif"):
            anim.save(filename, writer="pillow", fps=fps, dpi=dpi)
        elif filename.endswith(".mp4"):
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


def animate_path_execution(
    field: Field,
    blocks: list,
    path_plan: PathPlan,
    stats: dict = None,
    speed_multiplier: float = 1.5,
    fps: int = 30,
    save_path: Optional[str] = None,
):
    """
    Convenience function to create and display/save path animation.

    Args:
        field: Field object
        blocks: List of blocks
        path_plan: PathPlan object
        stats: Path statistics dictionary (optional)
        speed_multiplier: Animation speed (1.0 = normal, >1.0 = faster)
        fps: Frames per second
        save_path: Optional path to save animation

    Returns:
        PathAnimator object
    """
    animator = PathAnimator(
        field=field,
        blocks=blocks,
        path_plan=path_plan,
        stats=stats,
        speed_multiplier=speed_multiplier,
        fps=fps,
    )

    if save_path:
        animator.save_animation(save_path, fps=fps)

    return animator
