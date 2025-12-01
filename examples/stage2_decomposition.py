"""
Demo script for Stage 2: Boustrophedon Decomposition and Block Merging.

This demonstrates:
1. Field setup (from Stage 1)
2. Headland generation (from Stage 1)
3. Obstacle classification (from Stage 1)
4. Boustrophedon decomposition (NEW - Stage 2)
5. Block merging (NEW - Stage 2)
6. Visualization of decomposed field

NOTE: This demo will only work after Stage 2 implementation is complete.
"""

import matplotlib.pyplot as plt
import numpy as np

from src.data import FieldParameters, create_field_with_rectangular_obstacles
from src.decomposition import (
    boustrophedon_decomposition,
    cluster_tracks_into_blocks,
    get_decomposition_statistics,
    get_track_clustering_statistics,
    merge_blocks_by_criteria,
)
from src.geometry import generate_field_headland, generate_parallel_tracks
from src.obstacles.classifier import classify_all_obstacles, get_type_b_obstacles, get_type_d_obstacles


def plot_polygon(ax, polygon, **kwargs):
    """Plot a Shapely polygon."""
    if polygon.is_empty:
        return
    x, y = polygon.exterior.xy
    ax.plot(x, y, **kwargs)


def plot_filled_polygon(ax, polygon, **kwargs):
    """Plot a filled Shapely polygon."""
    if polygon.is_empty:
        return
    x, y = polygon.exterior.xy
    ax.fill(x, y, **kwargs)


def visualize_stage2_pipeline():
    """Visualize complete Stage 2 pipeline with decomposition."""

    print("=" * 80)
    print("STAGE 2 DEMO: BOUSTROPHEDON DECOMPOSITION")
    print("=" * 80)

    # ========== STAGE 1 SETUP ==========
    print("\n[Stage 1] Setting up field...")

    # Create field with multiple obstacles
    field = create_field_with_rectangular_obstacles(
        field_width=100,
        field_height=80,
        obstacle_specs=[
            (30, 30, 15, 12),  # Large obstacle 1
            (65, 50, 12, 15),  # Large obstacle 2
            (20, 10, 8, 8),  # Small obstacle near boundary
        ],
        name="Stage 2 Demo Field",
    )

    # Parameters
    params = FieldParameters(
        operating_width=5.0,
        turning_radius=3.0,
        num_headland_passes=2,
        driving_direction=0.0,
        obstacle_threshold=5.0,
    )

    print(f"Field: {field}")
    print(f"Operating width: {params.operating_width}m")

    # Generate preliminary headland (to classify obstacles)
    print("\n[Stage 1] Generating preliminary headland...")
    preliminary_headland = generate_field_headland(
        field_boundary=field.boundary_polygon,
        operating_width=params.operating_width,
        num_passes=params.num_headland_passes,
    )

    # Classify obstacles
    print("\n[Stage 1] Classifying obstacles...")
    classified_obstacles = classify_all_obstacles(
        obstacle_boundaries=field.obstacles,
        field_inner_boundary=preliminary_headland.inner_boundary,
        driving_direction_degrees=params.driving_direction,
        operating_width=params.operating_width,
        threshold=params.obstacle_threshold,
    )

    print(f"Classified {len(classified_obstacles)} obstacles:")
    for obs in classified_obstacles:
        print(f"  - {obs}")

    # Get Type B and Type D obstacles
    type_b_obstacles = get_type_b_obstacles(classified_obstacles)
    type_b_polygons = [obs.polygon for obs in type_b_obstacles]
    type_d_obstacles = get_type_d_obstacles(classified_obstacles)
    type_d_polygons = [obs.polygon for obs in type_d_obstacles]

    print(f"Type B obstacles (incorporated into boundary, also used in decomposition): {len(type_b_obstacles)}")
    print(f"Type D obstacles: {len(type_d_obstacles)}")
    print(f"All {len(type_b_obstacles) + len(type_d_obstacles)} physical obstacles participate in decomposition")

    # Regenerate headland with Type B obstacles incorporated
    print("\n[Stage 1] Incorporating Type B obstacles into inner boundary...")
    field_headland = generate_field_headland(
        field_boundary=field.boundary_polygon,
        operating_width=params.operating_width,
        num_passes=params.num_headland_passes,
        type_b_obstacles=type_b_polygons,
    )
    print(f"Inner boundary area (after Type B removal): {field_headland.inner_boundary.area:.2f}m²")

    # Generate global tracks (ignoring obstacles) - Stage 1
    print("\n[Stage 1] Generating global field-work tracks (ignoring obstacles)...")
    global_tracks = generate_parallel_tracks(
        inner_boundary=field_headland.inner_boundary,
        driving_direction_degrees=params.driving_direction,
        operating_width=params.operating_width,
    )
    print(f"Generated {len(global_tracks)} global tracks")
    print(f"Total track length: {sum(t.length for t in global_tracks):.2f}m")

    # ========== STAGE 2: DECOMPOSITION ==========
    print("\n" + "=" * 80)
    print("[Stage 2] Boustrophedon Decomposition")
    print("=" * 80)

    try:
        # Include BOTH Type B and Type D obstacles in decomposition
        # Type B obstacles are physical obstacles that must be avoided by ALL paths
        all_obstacles = type_b_polygons + type_d_polygons

        # Perform boustrophedon decomposition
        print("\nDecomposing field into preliminary blocks...")

        # Debug: Show critical points
        from src.decomposition import find_critical_points
        critical_points = find_critical_points(
            field_headland.inner_boundary,
            all_obstacles,
            params.driving_direction
        )
        print(f"Critical points (sweep perpendicular to driving direction {params.driving_direction}°):")
        print(f"  {len(critical_points)} critical x-coordinates: {[f'{x:.1f}' for x in critical_points[:10]]}")

        preliminary_blocks = boustrophedon_decomposition(
            inner_boundary=field_headland.inner_boundary,
            obstacles=all_obstacles,  # Both Type B and Type D
            driving_direction_degrees=params.driving_direction,
        )

        print(f"\nCreated {len(preliminary_blocks)} preliminary blocks")

        # Debug: Show block positions
        print("\nBlock positions (bounding boxes):")
        for block in preliminary_blocks:
            bounds = block.polygon.bounds  # (minx, miny, maxx, maxy)
            print(f"  B{block.block_id}: x=[{bounds[0]:.1f}, {bounds[2]:.1f}], "
                  f"y=[{bounds[1]:.1f}, {bounds[3]:.1f}], area={block.area:.2f}m²")

        # Get decomposition statistics
        prelim_stats = get_decomposition_statistics(preliminary_blocks)
        print("\nPreliminary blocks statistics:")
        print(f"  - Total blocks: {prelim_stats['num_blocks']}")
        print(f"  - Total area: {prelim_stats['total_area']:.2f}m²")
        print(f"  - Average area: {prelim_stats['avg_area']:.2f}m²")
        print(f"  - Min area: {prelim_stats['min_area']:.2f}m²")
        print(f"  - Max area: {prelim_stats['max_area']:.2f}m²")

        # ========== STAGE 2: BLOCK MERGING ==========
        print("\n" + "=" * 80)
        print("[Stage 2] Block Merging")
        print("=" * 80)

        # Show adjacency information before merging
        from src.decomposition import build_block_adjacency_graph
        prelim_graph = build_block_adjacency_graph(preliminary_blocks)
        print("\nPreliminary block adjacency:")
        for block_id in sorted(prelim_graph.adjacency.keys()):
            neighbors = prelim_graph.adjacency[block_id]
            print(f"  B{block_id} → adjacent to: {[f'B{n}' for n in neighbors]}")

        print("\nMerging blocks to reduce total count...")
        final_blocks = merge_blocks_by_criteria(
            blocks=preliminary_blocks, operating_width=params.operating_width
        )

        print(f"Merged to {len(final_blocks)} final blocks")
        print(f"Reduction: {len(preliminary_blocks) - len(final_blocks)} blocks")

        # Get final statistics
        final_stats = get_decomposition_statistics(final_blocks)
        print("\nFinal blocks statistics:")
        print(f"  - Total blocks: {final_stats['num_blocks']}")
        print(f"  - Total area: {final_stats['total_area']:.2f}m²")
        print(f"  - Average area: {final_stats['avg_area']:.2f}m²")

        # ========== STAGE 2: TRACK CLUSTERING ==========
        print("\n" + "=" * 80)
        print("[Stage 2] Clustering Global Tracks into Blocks")
        print("=" * 80)

        print("\nClustering tracks from Stage 1 into blocks...")
        print(f"  - Global tracks: {len(global_tracks)}")
        print(f"  - Blocks: {len(final_blocks)}")

        # Cluster global tracks into blocks (Section 2.3.2 of paper)
        final_blocks = cluster_tracks_into_blocks(global_tracks, final_blocks)

        # Get clustering statistics
        clustering_stats = get_track_clustering_statistics(final_blocks, global_tracks)
        print("\nTrack clustering statistics:")
        print(f"  - Total track segments: {clustering_stats['total_segments']}")
        print(f"  - Avg segments per global track: {clustering_stats['avg_segments_per_track']:.2f}")
        print(f"  - Length preservation: {clustering_stats['length_preservation']*100:.1f}%")

        # Display per-block results
        print("\nTracks per block:")
        for block in final_blocks:
            print(
                f"  Block {block.block_id}: {len(block.tracks)} track segments, "
                f"{block.get_working_distance():.2f}m total"
            )

        # ========== VISUALIZATION ==========
        print("\n" + "=" * 80)
        print("Creating visualization...")
        print("=" * 80)

        fig, axes = plt.subplots(1, 3, figsize=(20, 7))

        # Plot 1: Field with obstacles and headland
        ax1 = axes[0]
        ax1.set_title("1. Field Setup (Stage 1)", fontsize=12, fontweight="bold")
        ax1.set_aspect("equal")

        # Field boundary
        plot_filled_polygon(
            ax1, field.boundary_polygon, color="lightgreen", alpha=0.3, label="Field"
        )
        plot_polygon(ax1, field.boundary_polygon, color="darkgreen", linewidth=2)

        # Headland inner boundary
        plot_polygon(
            ax1,
            field_headland.inner_boundary,
            color="blue",
            linewidth=2,
            linestyle="--",
            label="Inner boundary",
        )

        # Obstacles - show all physical obstacles (Type B and Type D)
        for obs in classified_obstacles:
            if obs.obstacle_type.name == "B":
                color = "orange"  # Type B - near boundary
            elif obs.obstacle_type.name == "D":
                color = "gray"    # Type D - standard
            else:
                color = "lightgray"  # Type A/C if present
            plot_filled_polygon(ax1, obs.polygon, color=color, alpha=0.5)
            plot_polygon(ax1, obs.polygon, color="black", linewidth=1.5)

        ax1.set_xlabel("X (m)")
        ax1.set_ylabel("Y (m)")
        ax1.grid(True, alpha=0.3)
        ax1.legend()

        # Plot 2: Preliminary blocks (before merging)
        ax2 = axes[1]
        ax2.set_title(
            f"2. Preliminary Blocks ({len(preliminary_blocks)})", fontsize=12, fontweight="bold"
        )
        ax2.set_aspect("equal")

        # Draw blocks with different colors
        colors = plt.cm.Set3(np.linspace(0, 1, len(preliminary_blocks)))
        for i, block in enumerate(preliminary_blocks):
            plot_filled_polygon(ax2, block.polygon, color=colors[i], alpha=0.6)
            plot_polygon(ax2, block.polygon, color="black", linewidth=1.5)

            # Label block
            centroid = block.polygon.centroid
            ax2.text(
                centroid.x,
                centroid.y,
                f"B{block.block_id}",
                ha="center",
                va="center",
                fontsize=8,
                fontweight="bold",
            )

        # All physical obstacles (Type B and Type D)
        for obs in type_b_obstacles:
            plot_filled_polygon(ax2, obs.polygon, color="orange", alpha=0.7)
        for obs in type_d_obstacles:
            plot_filled_polygon(ax2, obs.polygon, color="gray", alpha=0.7)

        ax2.set_xlabel("X (m)")
        ax2.set_ylabel("Y (m)")
        ax2.grid(True, alpha=0.3)

        # Plot 3: Final blocks with tracks
        ax3 = axes[2]
        ax3.set_title(
            f"3. Final Blocks ({len(final_blocks)}) + Tracks", fontsize=12, fontweight="bold"
        )
        ax3.set_aspect("equal")

        # Draw blocks with different colors
        colors = plt.cm.Set3(np.linspace(0, 1, len(final_blocks)))
        for i, block in enumerate(final_blocks):
            plot_filled_polygon(ax3, block.polygon, color=colors[i], alpha=0.4)
            plot_polygon(ax3, block.polygon, color="black", linewidth=2)

            # Draw tracks
            for track in block.tracks:
                ax3.plot(
                    [track.start[0], track.end[0]],
                    [track.start[1], track.end[1]],
                    color="darkgreen",
                    linewidth=1.5,
                    alpha=0.7,
                )

            # Label block
            centroid = block.polygon.centroid
            ax3.text(
                centroid.x,
                centroid.y,
                f"B{block.block_id}\n{len(block.tracks)}T",
                ha="center",
                va="center",
                fontsize=9,
                fontweight="bold",
                bbox=dict(boxstyle="round", facecolor="white", alpha=0.8),
            )

        # All physical obstacles (Type B and Type D)
        for obs in type_b_obstacles:
            plot_filled_polygon(ax3, obs.polygon, color="orange", alpha=0.6)
        for obs in type_d_obstacles:
            plot_filled_polygon(ax3, obs.polygon, color="gray", alpha=0.6)

        ax3.set_xlabel("X (m)")
        ax3.set_ylabel("Y (m)")
        ax3.grid(True, alpha=0.3)

        plt.tight_layout()

        # Save figure
        output_path = "results/plots/stage2_demo.png"
        plt.savefig(output_path, dpi=150, bbox_inches="tight")
        print(f"\n✓ Visualization saved to: {output_path}")

        # Try to show
        try:
            plt.show()
        except Exception:
            print("  (Display not available - check saved file)")

        print("\n" + "=" * 80)
        print("STAGE 2 DEMO COMPLETE")
        print("=" * 80)

    except NotImplementedError as e:
        print(f"\n⚠ Cannot run demo: {e}")
        print("\nStage 2 implementation is pending. This demo will work after:")
        print("  1. Implementing boustrophedon_decomposition()")
        print("  2. Implementing merge_blocks_by_criteria()")
        print("\nSee src/decomposition/ for implementation templates.")


if __name__ == "__main__":
    visualize_stage2_pipeline()
