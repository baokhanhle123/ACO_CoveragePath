"""
Demo script to visualize Stage 1 of the coverage path planning algorithm.

This demonstrates:
1. Field with obstacles
2. Headland generation
3. Obstacle classification
4. Track generation
"""

import matplotlib.pyplot as plt
import numpy as np
from shapely.geometry import Polygon

from src.data import FieldParameters, create_field_with_rectangular_obstacles
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


def visualize_stage1_pipeline():
    """
    Visualize the complete Stage 1 pipeline.

    This function is a faithful, didactic implementation of the first
    stage described in Zhou et al. 2014, "Agricultural operations
    planning in fields with multiple obstacle areas"
    [`10.1016/j.compag.2014.08.013`], Section 2.2 ("First stage").
    The three subplots roughly correspond to the geometric steps
    illustrated in the figures of that section:
        - field and obstacles,
        - headlands and obstacle types,
        - field body and parallel tracks.

    1. Represent the field and obstacles as polygons.
    2. Generate a preliminary field headland.
    3. Classify obstacles into Types A–D.
    4. Regenerate the field headland with Type B obstacles incorporated
       into the inner boundary.
    5. Generate obstacle headlands (for Type D obstacles).
    6. Generate parallel field-work tracks on the field body, ignoring
       in-field obstacles (handled in later stages).
    """

    # Create field with multiple obstacles
    print("Creating field with obstacles...")
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

    # Parameters
    params = FieldParameters(
        operating_width=5.0,
        turning_radius=3.0,
        num_headland_passes=2,
        driving_direction=0.0,
        obstacle_threshold=5.0,
    )

    print(f"Field: {field}")
    print(
        f"Parameters: operating_width={params.operating_width}m, "
        f"headland_passes={params.num_headland_passes}"
    )

    # Run the core Stage 1 pipeline (Section 2.2 of the paper)
    print("\nRunning Stage 1 pipeline (Zhou et al. 2014, Sec. 2.2)...")
    result: Stage1Result = run_stage1_pipeline(field, params)

    print(f"\nClassified {len(result.classified_obstacles)} obstacles:")
    for obs in result.classified_obstacles:
        print(f"  - {obs}")

    print(f"\nType B obstacles (incorporated into inner boundary): {len(result.type_b_obstacles)}")
    print(f"Type D obstacles (including merged Type C clusters): {len(result.type_d_obstacles)}")
    if result.type_c_clusters:
        print("Type C proximity clusters (original obstacle indices):")
        for cluster in result.type_c_clusters:
            print(f"  - {cluster}")
    else:
        print("No Type C proximity clusters detected.")
    print(f"Generated {len(result.obstacle_headlands)} obstacle headlands")

    print(f"\nGenerated {len(result.tracks)} tracks")
    print(f"Total track length: {sum(t.length for t in result.tracks):.2f}m")

    # Create visualization
    print("\nCreating visualization...")
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))

    # Plot 1: Field with obstacles
    ax1 = axes[0]
    ax1.set_title("1. Field with Obstacles", fontsize=12, fontweight="bold")
    ax1.set_aspect("equal")

    # Field boundary
    plot_filled_polygon(ax1, field.boundary_polygon, color="lightgreen", alpha=0.3, label="Field")
    plot_polygon(ax1, field.boundary_polygon, color="darkgreen", linewidth=2)

    # Obstacles
    for i, obs_coords in enumerate(field.obstacles):
        obs_poly = Polygon(obs_coords)
        plot_filled_polygon(ax1, obs_poly, color="gray", alpha=0.6)
        plot_polygon(ax1, obs_poly, color="black", linewidth=1.5)
        centroid = obs_poly.centroid
        ax1.text(
            centroid.x,
            centroid.y,
            f"O{i+1}",
            ha="center",
            va="center",
            fontweight="bold",
            color="white",
        )

    ax1.set_xlabel("X (m)")
    ax1.set_ylabel("Y (m)")
    ax1.grid(True, alpha=0.3)
    ax1.legend()

    # Plot 2: Headland generation
    ax2 = axes[1]
    ax2.set_title("2. Headland Generation", fontsize=12, fontweight="bold")
    ax2.set_aspect("equal")

    # Field boundary
    plot_polygon(
        ax2, field.boundary_polygon, color="darkgreen", linewidth=2, label="Field boundary"
    )

    # Field headland passes
    colors = plt.cm.Blues(np.linspace(0.4, 0.8, len(result.field_headland.passes)))
    for i, pass_poly in enumerate(result.field_headland.passes):
        plot_polygon(
            ax2,
            pass_poly,
            color=colors[i],
            linewidth=2,
            linestyle="--",
            label=f"Headland pass {i+1}",
        )

    # Inner boundary
    plot_polygon(
        ax2,
        result.field_headland.inner_boundary,
        color="red",
        linewidth=2,
        linestyle=":",
        label="Inner boundary",
    )

    # Classified obstacles with headlands
    for obs in result.classified_obstacles:
        plot_filled_polygon(ax2, obs.polygon, color="gray", alpha=0.4)
        plot_polygon(ax2, obs.polygon, color="black", linewidth=1.5)

        # Label with type
        centroid = obs.polygon.centroid
        ax2.text(
            centroid.x,
            centroid.y,
            obs.obstacle_type.name,
            ha="center",
            va="center",
            fontsize=8,
            fontweight="bold",
            bbox=dict(boxstyle="round", facecolor="white", alpha=0.8),
        )

    # Obstacle headlands (Type D only)
    for obs, obs_headland in result.obstacle_headlands:
        for pass_poly in obs_headland.passes:
            plot_polygon(ax2, pass_poly, color="orange", linewidth=1.5, linestyle="--", alpha=0.7)

    ax2.set_xlabel("X (m)")
    ax2.set_ylabel("Y (m)")
    ax2.grid(True, alpha=0.3)
    ax2.legend(fontsize=8)

    # Plot 3: Track generation
    ax3 = axes[2]
    ax3.set_title("3. Field-work Tracks", fontsize=12, fontweight="bold")
    ax3.set_aspect("equal")

    # Inner boundary
    plot_filled_polygon(
        ax3, result.field_headland.inner_boundary, color="lightblue", alpha=0.2, label="Field body"
    )
    plot_polygon(ax3, result.field_headland.inner_boundary, color="blue", linewidth=2)

    # Only show Type D obstacles (Type B are incorporated into inner boundary)
    for obs in result.type_d_obstacles:
        plot_filled_polygon(ax3, obs.polygon, color="gray", alpha=0.6)
        plot_polygon(ax3, obs.polygon, color="black", linewidth=1.5)

    # Tracks
    for track in result.tracks:
        ax3.plot(
            [track.start[0], track.end[0]],
            [track.start[1], track.end[1]],
            color="green",
            linewidth=2,
            alpha=0.7,
        )

        # Mark track endpoints
        ax3.plot(track.start[0], track.start[1], "go", markersize=4)
        ax3.plot(track.end[0], track.end[1], "ro", markersize=4)

    ax3.set_xlabel("X (m)")
    ax3.set_ylabel("Y (m)")
    ax3.grid(True, alpha=0.3)
    ax3.legend()

    plt.tight_layout()

    # Save figure
    output_path = "results/plots/stage1_demo.png"
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    print(f"\n✓ Visualization saved to: {output_path}")

    # Also try to show (will work if display available)
    try:
        plt.show()
    except Exception:
        print("  (Display not available - check saved file)")

    print("\n" + "=" * 80)
    print("STAGE 1 DEMO COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    visualize_stage1_pipeline()
