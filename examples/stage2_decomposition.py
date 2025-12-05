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
from src.stage1 import Stage1Result, run_stage1_pipeline


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
    """
    Visualize complete Stage 2 pipeline with decomposition.

    This demo corresponds to the *second stage* in Zhou et al. 2014,
    "Agricultural operations planning in fields with multiple obstacle
    areas" ([`10.1016/j.compag.2014.08.013`](http://dx.doi.org/10.1016/j.compag.2014.08.013)),
    Section 2.3:

    1. Start from Stage 1 outputs (inner boundary, Type D obstacles,
       and global tracks).
    2. Perform boustrophedon cellular decomposition of the field body
       around Type D obstacles (Sec. 2.3.1).
    3. Merge adjacent preliminary blocks to reduce their number while
       avoiding very narrow cells (Sec. 2.3.2).
    4. Cluster global tracks into the final blocks by subdividing them
       at block boundaries and assigning segments to blocks, following
       the “clustering tracks into blocks” description in Sec. 2.3.2.
    """

    print("=" * 80)
    print("STAGE 2 DEMO: BOUSTROPHEDON DECOMPOSITION")
    print("=" * 80)

    # ========== STAGE 1 SETUP (via Stage1Result) ==========
    print("\n[Stage 1] Setting up field and running Stage 1 pipeline...")

    # Create field with multiple obstacles
    field = create_field_with_rectangular_obstacles(
        field_width=220,
        field_height=220,
        obstacle_specs=[
            (80, 65, 60, 20),  # Obstacle 1
            (40, 120, 70, 20),  # Obstacle 2
            (20, 10, 40, 20),  # Obstacle 3 (near boundary)
        ],
        name="Demo Field",
    )

    # Parameters (same as Stage 1 demo for consistency)
    params = FieldParameters(
        operating_width=5.0,
        turning_radius=3.0,
        num_headland_passes=2,
        driving_direction=0.0,
        obstacle_threshold=5.0,
    )

    print(f"Field: {field}")
    print(f"Operating width: {params.operating_width}m")

    # Run full Stage 1 pipeline (Section 2.2 of Zhou et al. 2014)
    stage1: Stage1Result = run_stage1_pipeline(field, params)

    classified_obstacles = stage1.classified_obstacles
    type_d_obstacles = stage1.type_d_obstacles
    field_headland = stage1.field_headland
    global_tracks = stage1.tracks

    print(f"\n[Stage 1] Classified {len(classified_obstacles)} obstacles:")
    for obs in classified_obstacles:
        print(f"  - {obs}")

    print(f"\n[Stage 1] Type B obstacles (incorporated into inner boundary): "
          f"{len(stage1.type_b_obstacles)}")
    print(f"[Stage 1] Type D obstacles requiring decomposition: {len(type_d_obstacles)}")
    print(
        f"[Stage 1] Inner boundary area (after Type B removal): "
        f"{field_headland.inner_boundary.area:.2f}m²"
    )
    print(f"[Stage 1] Generated {len(global_tracks)} global tracks "
          f"(total length={sum(t.length for t in global_tracks):.2f}m)")

    # ========== STAGE 2: DECOMPOSITION ==========
    print("\n" + "=" * 80)
    print("[Stage 2] Boustrophedon Decomposition")
    print("=" * 80)

    try:
        obstacle_polygons = [obs.polygon for obs in type_d_obstacles]

        # Perform boustrophedon decomposition
        print("\nDecomposing field into preliminary blocks...")

        # Debug: Show critical points
        from src.decomposition import find_critical_points
        critical_points = find_critical_points(
            field_headland.inner_boundary,
            obstacle_polygons,
            params.driving_direction
        )
        print(f"Critical points (sweep perpendicular to driving direction {params.driving_direction}°):")
        print(f"  {len(critical_points)} critical x-coordinates: {[f'{x:.1f}' for x in critical_points[:10]]}")

        preliminary_blocks = boustrophedon_decomposition(
            inner_boundary=field_headland.inner_boundary,
            obstacles=obstacle_polygons,
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

        # Obstacles
        for obs in classified_obstacles:
            color = "red" if obs.obstacle_type.name == "D" else "gray"
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

        # Obstacles
        for obs in type_d_obstacles:
            plot_filled_polygon(ax2, obs.polygon, color="red", alpha=0.7)

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

        # Obstacles
        for obs in type_d_obstacles:
            plot_filled_polygon(ax3, obs.polygon, color="red", alpha=0.6)

        ax3.set_xlabel("X (m)")
        ax3.set_ylabel("Y (m)")
        ax3.grid(True, alpha=0.3)

        plt.tight_layout()

        # Save figure
        output_path = "exports/demos/plots/stage2_demo.png"
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
