"""
Animated path execution visualization with tractor icon.

Creates impressive animations showing:
- Tractor/robot moving along coverage path
- Rotation based on movement direction
- Trail showing covered path
- Progress bar and statistics
- Working vs transition segments highlighted
"""

import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.patches import Rectangle, FancyArrow, Polygon as MPLPolygon
import numpy as np
from typing import List, Tuple, Optional
import time


class PathAnimator:
    """
    Animator for coverage path execution.

    Creates professional animations with:
    - Moving tractor icon
    - Path trail
    - Progress indicators
    - Statistics overlay
    """

    def __init__(
        self,
        field,
        blocks,
        path_plan,
        figsize=(16, 10),
        fps=30,
        speed_multiplier=1.0
    ):
        """
        Initialize path animator.

        Args:
            field: Field object with boundary and obstacles
            blocks: List of blocks
            path_plan: PathPlan object with segments and waypoints
            figsize: Figure size (width, height)
            fps: Frames per second for animation
            speed_multiplier: Speed factor (1.0 = normal, 2.0 = 2x speed)
        """
        self.field = field
        self.blocks = blocks
        self.path_plan = path_plan
        self.figsize = figsize
        self.fps = fps
        self.speed_multiplier = speed_multiplier

        # Get all waypoints
        self.waypoints = path_plan.get_all_waypoints()

        # Calculate segment boundaries for coloring
        self.segment_boundaries = []
        cumulative = 0
        for segment in path_plan.segments:
            self.segment_boundaries.append({
                'start': cumulative,
                'end': cumulative + len(segment.waypoints) - 1,
                'type': segment.segment_type
            })
            cumulative += len(segment.waypoints) - 1

        # Animation state
        self.current_frame = 0
        self.trail_points = []

    def create_tractor_icon(self, x, y, heading, size=3.0, color='red'):
        """
        Create tractor icon as a collection of patches.

        Args:
            x, y: Position
            heading: Direction in radians
            size: Size of tractor
            color: Color of tractor

        Returns:
            List of matplotlib patches
        """
        # Simple tractor representation: triangle pointing in direction
        # Create triangle vertices
        front = size
        back = -size * 0.5
        width = size * 0.7

        # Triangle points (before rotation)
        points = np.array([
            [front, 0],      # Front (nose)
            [back, width],   # Back left
            [back, -width],  # Back right
        ])

        # Rotate based on heading
        cos_h = np.cos(heading)
        sin_h = np.sin(heading)
        rotation_matrix = np.array([
            [cos_h, -sin_h],
            [sin_h, cos_h]
        ])

        rotated_points = points @ rotation_matrix.T

        # Translate to position
        rotated_points[:, 0] += x
        rotated_points[:, 1] += y

        # Create polygon patch
        tractor_patch = MPLPolygon(
            rotated_points,
            facecolor=color,
            edgecolor='darkred',
            linewidth=2,
            zorder=100  # Draw on top
        )

        return tractor_patch

    def get_segment_type_at_waypoint(self, waypoint_idx):
        """Get segment type (working/transition) for waypoint index."""
        for seg_info in self.segment_boundaries:
            if seg_info['start'] <= waypoint_idx <= seg_info['end']:
                return seg_info['type']
        return 'unknown'

    def init_animation(self):
        """Initialize animation frame."""
        # Clear previous elements
        for artist in self.dynamic_artists:
            artist.remove()
        self.dynamic_artists = []

        # Reset trail
        self.trail_points = []

        return self.dynamic_artists

    def animate_frame(self, frame):
        """
        Animate single frame.

        Args:
            frame: Frame number

        Returns:
            List of artists to update
        """
        # Calculate waypoint index based on frame and speed
        waypoint_idx = int(frame * self.speed_multiplier)

        # Check if animation complete
        if waypoint_idx >= len(self.waypoints) - 1:
            waypoint_idx = len(self.waypoints) - 1

        # Get current and next waypoint
        current_wp = self.waypoints[waypoint_idx]

        # Calculate heading (direction to next waypoint)
        if waypoint_idx < len(self.waypoints) - 1:
            next_wp = self.waypoints[waypoint_idx + 1]
            dx = next_wp[0] - current_wp[0]
            dy = next_wp[1] - current_wp[1]
            heading = np.arctan2(dy, dx)
        else:
            # Last waypoint, keep previous heading
            if len(self.trail_points) > 1:
                prev_wp = self.trail_points[-1]
                dx = current_wp[0] - prev_wp[0]
                dy = current_wp[1] - prev_wp[1]
                heading = np.arctan2(dy, dx)
            else:
                heading = 0

        # Clear previous dynamic artists
        for artist in self.dynamic_artists:
            artist.remove()
        self.dynamic_artists = []

        # Add current waypoint to trail
        if len(self.trail_points) == 0 or self.trail_points[-1] != current_wp:
            self.trail_points.append(current_wp)

        # Draw trail (path covered so far)
        if len(self.trail_points) > 1:
            trail_x = [p[0] for p in self.trail_points]
            trail_y = [p[1] for p in self.trail_points]

            # Color trail by segment type
            trail_line, = self.ax.plot(
                trail_x, trail_y,
                color='blue',
                linewidth=3,
                alpha=0.6,
                zorder=50
            )
            self.dynamic_artists.append(trail_line)

        # Draw tractor icon
        segment_type = self.get_segment_type_at_waypoint(waypoint_idx)
        tractor_color = 'green' if segment_type == 'working' else 'orange'

        tractor = self.create_tractor_icon(
            current_wp[0], current_wp[1],
            heading,
            size=4.0,
            color=tractor_color
        )
        self.ax.add_patch(tractor)
        self.dynamic_artists.append(tractor)

        # Update progress text
        progress_pct = (waypoint_idx / len(self.waypoints)) * 100
        distance_covered = sum(
            np.hypot(
                self.trail_points[i+1][0] - self.trail_points[i][0],
                self.trail_points[i+1][1] - self.trail_points[i][1]
            )
            for i in range(len(self.trail_points) - 1)
        )

        progress_text = (
            f"Progress: {progress_pct:.1f}%\n"
            f"Distance: {distance_covered:.1f} m\n"
            f"Waypoint: {waypoint_idx + 1}/{len(self.waypoints)}\n"
            f"Mode: {segment_type.upper()}"
        )

        text_artist = self.ax.text(
            0.02, 0.98,
            progress_text,
            transform=self.ax.transAxes,
            fontsize=12,
            verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.8),
            zorder=1000
        )
        self.dynamic_artists.append(text_artist)

        # Update progress bar
        self.progress_bar_fill.set_width(progress_pct)

        return self.dynamic_artists

    def create_animation(self, interval=None):
        """
        Create matplotlib animation.

        Args:
            interval: Milliseconds between frames (default: 1000/fps)

        Returns:
            matplotlib.animation.FuncAnimation object
        """
        if interval is None:
            interval = 1000 / self.fps

        # Create figure
        self.fig, self.ax = plt.subplots(figsize=self.figsize)

        # Draw static elements (field, obstacles, blocks)
        self._draw_static_elements()

        # Add progress bar at top
        self._add_progress_bar()

        # Initialize dynamic artists list
        self.dynamic_artists = []

        # Calculate number of frames
        num_frames = int(len(self.waypoints) / self.speed_multiplier)

        # Create animation
        anim = animation.FuncAnimation(
            self.fig,
            self.animate_frame,
            init_func=self.init_animation,
            frames=num_frames,
            interval=interval,
            blit=False,
            repeat=True
        )

        return anim

    def _draw_static_elements(self):
        """Draw field boundary, obstacles, and blocks."""
        # Field boundary
        field_x, field_y = zip(*self.field.boundary_polygon.exterior.coords)
        self.ax.plot(field_x, field_y, 'k-', linewidth=2, label='Field Boundary')

        # Obstacles
        for i, obs in enumerate(self.field.obstacle_polygons):
            obs_x, obs_y = zip(*obs.exterior.coords)
            self.ax.fill(
                obs_x, obs_y,
                color='gray',
                alpha=0.5,
                edgecolor='black',
                linewidth=1.5
            )
            if i == 0:
                self.ax.plot([], [], 's', color='gray', alpha=0.5, label='Obstacles')

        # Blocks (light background)
        colors = plt.cm.Set3(np.linspace(0, 1, len(self.blocks)))
        for i, block in enumerate(self.blocks):
            block_x, block_y = zip(*block.polygon.exterior.coords)
            self.ax.fill(
                block_x, block_y,
                color=colors[i],
                alpha=0.15,
                edgecolor=colors[i],
                linewidth=1
            )

        # Complete path (light gray, will be covered by trail)
        all_waypoints = self.waypoints
        path_x = [p[0] for p in all_waypoints]
        path_y = [p[1] for p in all_waypoints]
        self.ax.plot(
            path_x, path_y,
            color='lightgray',
            linewidth=1,
            alpha=0.3,
            linestyle='--',
            label='Planned Path'
        )

        # Styling
        self.ax.set_xlabel('X (meters)', fontsize=12)
        self.ax.set_ylabel('Y (meters)', fontsize=12)
        self.ax.set_title(
            'Coverage Path Execution Animation',
            fontsize=16,
            fontweight='bold',
            pad=20
        )
        self.ax.legend(loc='upper right', fontsize=10)
        self.ax.grid(True, alpha=0.3)
        self.ax.set_aspect('equal')

        # Add legend for colors
        from matplotlib.lines import Line2D
        custom_lines = [
            Line2D([0], [0], color='green', lw=4),
            Line2D([0], [0], color='orange', lw=4),
        ]
        legend2 = self.ax.legend(
            custom_lines,
            ['Working', 'Transition'],
            loc='lower right',
            fontsize=10,
            title='Tractor Mode'
        )
        self.ax.add_artist(legend2)

    def _add_progress_bar(self):
        """Add progress bar at top of plot."""
        # Progress bar background
        bar_y = self.ax.get_ylim()[1] * 1.08
        bar_height = (self.ax.get_ylim()[1] - self.ax.get_ylim()[0]) * 0.02
        bar_width = self.ax.get_xlim()[1] - self.ax.get_xlim()[0]

        # Background
        self.progress_bar_bg = Rectangle(
            (self.ax.get_xlim()[0], bar_y),
            bar_width,
            bar_height,
            facecolor='lightgray',
            edgecolor='black',
            linewidth=1,
            transform=self.ax.transData,
            zorder=999
        )
        self.ax.add_patch(self.progress_bar_bg)

        # Fill (will be updated)
        self.progress_bar_fill = Rectangle(
            (self.ax.get_xlim()[0], bar_y),
            0,  # Start at 0 width
            bar_height,
            facecolor='green',
            edgecolor='darkgreen',
            linewidth=1,
            transform=self.ax.transData,
            zorder=1000
        )
        self.ax.add_patch(self.progress_bar_fill)

        # Label
        self.ax.text(
            0.5, 1.12,
            'Coverage Progress',
            transform=self.ax.transAxes,
            fontsize=12,
            fontweight='bold',
            ha='center'
        )

    def save_animation(self, filename, dpi=150, writer='pillow'):
        """
        Save animation to file.

        Args:
            filename: Output filename (.mp4 or .gif)
            dpi: Resolution
            writer: 'ffmpeg' for mp4, 'pillow' for gif
        """
        print(f"Creating animation... (this may take a minute)")
        start_time = time.time()

        anim = self.create_animation()

        print(f"Saving to {filename}...")
        anim.save(filename, writer=writer, dpi=dpi)

        elapsed = time.time() - start_time
        print(f"✓ Animation saved to {filename} ({elapsed:.1f} seconds)")

        plt.close()


def animate_path_execution(
    field,
    blocks,
    path_plan,
    output_file='path_animation.gif',
    fps=30,
    speed_multiplier=1.0,
    figsize=(16, 10)
):
    """
    Convenience function to create and save path animation.

    Args:
        field: Field object
        blocks: List of blocks
        path_plan: PathPlan object
        output_file: Output filename (.gif or .mp4)
        fps: Frames per second
        speed_multiplier: Animation speed (1.0 = normal)
        figsize: Figure size
    """
    animator = PathAnimator(
        field=field,
        blocks=blocks,
        path_plan=path_plan,
        figsize=figsize,
        fps=fps,
        speed_multiplier=speed_multiplier
    )

    # Determine writer based on file extension
    if output_file.endswith('.mp4'):
        writer = 'ffmpeg'
    else:
        writer = 'pillow'

    animator.save_animation(output_file, writer=writer)

    return animator
