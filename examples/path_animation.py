"""
Animated visualization of the optimal coverage path from the three-stage process.

This script demonstrates:
1. Complete 3-stage pipeline (field setup, decomposition, ACO optimization)
2. Animated path traversal with moving vehicle
3. Real-time statistics overlay
4. Visual differentiation of working vs transition segments

The animation shows the optimal path being traversed step-by-step, making it
easy to understand the coverage strategy and path efficiency.
"""

import os
import sys
from typing import Optional, Tuple

import matplotlib.animation as animation
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

from src.data import FieldParameters, create_field_with_rectangular_obstacles
from src.decomposition import boustrophedon_decomposition, merge_blocks_by_criteria
from src.geometry import generate_field_headland, generate_parallel_tracks
from src.obstacles.classifier import (
    classify_all_obstacles,
    get_type_b_obstacles,
    get_type_d_obstacles,
)
from src.optimization import (
    ACOParameters,
    ACOSolver,
    build_cost_matrix,
    generate_path_from_solution,
    get_path_statistics,
)


def run_full_pipeline(seed: Optional[int] = None):
    """
    Run the complete 3-stage pipeline and return all results.

    Returns:
        Tuple of (field, params, final_blocks, path_plan, solver, stats)
    """
    print("=" * 80)
    print("PATH ANIMATION: Running 3-Stage Pipeline")
    print("=" * 80)

    if seed is not None:
        np.random.seed(seed)
        print(f"Using random seed: {seed}")

    # ====================
    # STAGE 1: Field Setup
    # ====================
    print("\n[Stage 1] Creating field with obstacles...")

    field = create_field_with_rectangular_obstacles(
        field_width=100,
        field_height=80,
        obstacle_specs=[
            (30, 30, 15, 12),  # Obstacle 1
            (65, 50, 12, 15),  # Obstacle 2
            (20, 10, 8, 8),  # Obstacle 3
        ],
        name="Animation Demo Field",
    )

    params = FieldParameters(
        operating_width=5.0,
        turning_radius=3.0,
        num_headland_passes=2,
        driving_direction=0.0,
        obstacle_threshold=5.0,
    )

    # Generate preliminary headland
    preliminary_headland = generate_field_headland(
        field_boundary=field.boundary_polygon,
        operating_width=params.operating_width,
        num_passes=params.num_headland_passes,
    )

    # Classify obstacles
    classified_obstacles = classify_all_obstacles(
        obstacle_boundaries=field.obstacles,
        field_inner_boundary=preliminary_headland.inner_boundary,
        driving_direction_degrees=params.driving_direction,
        operating_width=params.operating_width,
        threshold=params.obstacle_threshold,
    )

    type_b_obstacles = get_type_b_obstacles(classified_obstacles)
    type_b_polygons = [obs.polygon for obs in type_b_obstacles]
    type_d_obstacles = get_type_d_obstacles(classified_obstacles)
    obstacle_polygons = [obs.polygon for obs in type_d_obstacles]

    # Regenerate headland with Type B obstacles
    field_headland = generate_field_headland(
        field_boundary=field.boundary_polygon,
        operating_width=params.operating_width,
        num_passes=params.num_headland_passes,
        type_b_obstacles=type_b_polygons,
    )

    print(f"  ✓ {len(type_b_obstacles)} Type B obstacles (incorporated)")
    print(f"  ✓ {len(type_d_obstacles)} Type D obstacles (for decomposition)")

    # ====================
    # STAGE 2: Decomposition
    # ====================
    print("\n[Stage 2] Running boustrophedon decomposition...")

    preliminary_blocks = boustrophedon_decomposition(
        inner_boundary=field_headland.inner_boundary,
        obstacles=obstacle_polygons,
        driving_direction_degrees=params.driving_direction,
    )

    final_blocks = merge_blocks_by_criteria(
        blocks=preliminary_blocks, operating_width=params.operating_width
    )

    # Generate tracks for each block
    for block in final_blocks:
        tracks = generate_parallel_tracks(
            inner_boundary=block.polygon,
            driving_direction_degrees=params.driving_direction,
            operating_width=params.operating_width,
            obstacles_to_avoid=type_b_polygons if type_b_polygons else None,
        )
        for i, track in enumerate(tracks):
            track.block_id = block.block_id
            track.index = i
        block.tracks = tracks

    print(f"  ✓ Created {len(final_blocks)} blocks")

    # ====================
    # STAGE 3: ACO Optimization
    # ====================
    print("\n[Stage 3] Running ACO optimization...")

    # Create nodes
    all_nodes = []
    node_index = 0
    for block in final_blocks:
        nodes = block.create_entry_exit_nodes(start_index=node_index)
        all_nodes.extend(nodes)
        node_index += 4

    # Build cost matrix
    cost_matrix = build_cost_matrix(
        blocks=final_blocks, nodes=all_nodes, turning_penalty=0.0
    )

    num_nodes = len(all_nodes)
    num_ants = min(max(num_nodes, 10), 40)

    aco_params = ACOParameters(
        alpha=1.0,
        beta=2.0,
        rho=0.1,
        q=100.0,
        num_ants=num_ants,
        num_iterations=100,
        elitist_weight=2.0,
    )

    solver = ACOSolver(
        blocks=final_blocks,
        nodes=all_nodes,
        cost_matrix=cost_matrix,
        params=aco_params,
    )

    # Run optimization
    best_solution = solver.solve(verbose=False)

    if best_solution is None or not best_solution.is_valid(len(final_blocks)):
        raise RuntimeError("Failed to find valid solution!")

    print(f"  ✓ Found optimal solution (cost: {best_solution.cost:.2f})")

    # Generate path
    path_plan = generate_path_from_solution(best_solution, final_blocks, all_nodes)
    stats = get_path_statistics(path_plan)

    print(f"  ✓ Generated path ({stats['total_distance']:.2f}m total)")
    print(f"    Efficiency: {stats['efficiency']*100:.1f}%")

    return field, params, final_blocks, path_plan, solver, stats


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
        field,
        blocks,
        path_plan,
        stats,
        figsize=(16, 10),
        speed_factor=1.0,
        show_stats=True,
        trail_gap=0,
    ):
        """
        Initialize the path animator.

        Args:
            field: Field object with boundary and obstacles
            blocks: List of blocks from decomposition
            path_plan: PathPlan with segments and waypoints
            stats: Path statistics dictionary
            figsize: Figure size tuple
            speed_factor: Animation speed multiplier (1.0 = normal, >1.0 = faster)
            show_stats: Whether to show statistics overlay
            trail_gap: Number of waypoints behind vehicle to leave gap (0 = path connects exactly to vehicle, default: 0)
        """
        self.field = field
        self.blocks = blocks
        self.path_plan = path_plan
        self.stats = stats
        self.speed_factor = speed_factor
        self.show_stats = show_stats
        self.trail_gap = max(0, int(trail_gap))  # Ensure non-negative integer

        # Flatten all waypoints with segment information.
        # IMPORTANT: we keep *all* waypoints (including duplicates at segment
        # boundaries) so that geometry is never lost. Zero-length steps simply
        # contribute 0 to the cumulative distance.
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
        from matplotlib.lines import Line2D

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
        # The trail effect comes from only showing traveled path (no path ahead), not from leaving a gap
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

            # Optional: Rotate vehicle based on direction
            if current_index > 0:
                prev_x, prev_y = self.waypoints[current_index - 1]
                dx = x - prev_x
                dy = y - prev_y
                # Could add rotation here if needed

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
        # Use speed_factor to control how many waypoints per frame
        waypoints_per_frame = max(1, int(self.speed_factor))
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
        self, interval=50, repeat=True, save_path=None, fps=20, bitrate=1800
    ):
        """
        Create and return the animation.

        Args:
            interval: Milliseconds between frames
            repeat: Whether to loop the animation
            save_path: Optional path to save animation (GIF or MP4)
            fps: Frames per second for saved video
            bitrate: Bitrate for MP4 encoding

        Returns:
            matplotlib.animation.FuncAnimation object
        """
        # Calculate number of frames needed
        waypoints_per_frame = max(1, int(self.speed_factor))
        num_frames = (len(self.waypoints) + waypoints_per_frame - 1) // waypoints_per_frame

        print(f"\nCreating animation:")
        print(f"  - Total waypoints: {len(self.waypoints)}")
        print(f"  - Animation frames: {num_frames}")
        print(f"  - Speed factor: {self.speed_factor}x")
        print(f"  - Duration: ~{num_frames * interval / 1000:.1f}s")

        anim = animation.FuncAnimation(
            self.fig,
            self.animate_frame,
            frames=num_frames,
            interval=interval,
            repeat=repeat,
            blit=False,  # Set to False for better compatibility
        )

        # Save animation if requested
        if save_path:
            print(f"\nSaving animation to: {save_path}")
            try:
                if save_path.endswith(".gif"):
                    anim.save(
                        save_path,
                        writer="pillow",
                        fps=fps,
                        dpi=100,
                    )
                elif save_path.endswith(".mp4"):
                    anim.save(
                        save_path,
                        writer="ffmpeg",
                        fps=fps,
                        bitrate=bitrate,
                        extra_args=["-vcodec", "libx264"],
                    )
                else:
                    print(f"  ⚠ Unknown file format, defaulting to GIF")
                    save_path_gif = save_path + ".gif"
                    anim.save(save_path_gif, writer="pillow", fps=fps, dpi=100)
                    save_path = save_path_gif

                print(f"  ✓ Animation saved successfully!")
            except Exception as e:
                print(f"  ✗ Error saving animation: {e}")
                print(f"    (Animation will still display if possible)")

        return anim


def main():
    """Main function to run the path animation."""
    import argparse

    parser = argparse.ArgumentParser(description="Animate optimal coverage path")
    parser.add_argument(
        "--seed", type=int, default=None, help="Random seed for reproducibility"
    )
    parser.add_argument(
        "--speed",
        type=float,
        default=2.0,
        help="Animation speed factor (default: 2.0)",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=50,
        help="Milliseconds between frames (default: 50)",
    )
    parser.add_argument(
        "--save",
        type=str,
        default=None,
        help="Path to save animation (GIF or MP4)",
    )
    parser.add_argument(
        "--fps", type=int, default=20, help="Frames per second for saved video (default: 20)"
    )
    parser.add_argument(
        "--no-stats", action="store_true", help="Hide statistics overlay"
    )
    parser.add_argument(
        "--trail-gap",
        type=int,
        default=0,
        help="Number of waypoints behind vehicle to leave gap (0 = path connects exactly to vehicle, default: 0)",
    )

    args = parser.parse_args()

    # Run pipeline
    try:
        field, params, blocks, path_plan, solver, stats = run_full_pipeline(seed=args.seed)
    except Exception as e:
        print(f"\n✗ Error running pipeline: {e}")
        sys.exit(1)

    # Create animator
    animator = PathAnimator(
        field=field,
        blocks=blocks,
        path_plan=path_plan,
        stats=stats,
        speed_factor=args.speed,
        show_stats=not args.no_stats,
        trail_gap=args.trail_gap,
    )

    # Determine save path
    save_path = args.save
    if save_path is None:
        # Default: save to exports/demos/animations/
        os.makedirs("exports/demos/animations", exist_ok=True)
        save_path = "exports/demos/animations/path_animation.gif"

    # Create animation
    anim = animator.create_animation(
        interval=args.interval, save_path=save_path, fps=args.fps
    )

    print("\n" + "=" * 80)
    print("Animation created successfully!")
    print("=" * 80)
    print(f"\nTo view the animation:")
    print(f"  1. It should display automatically if display is available")
    print(f"  2. Or check the saved file: {save_path}")

    # Try to show
    try:
        plt.show()
    except Exception:
        print("\n  (Display not available - check saved file)")

    return anim


if __name__ == "__main__":
    main()

