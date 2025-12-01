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
from src.geometry import (
    generate_field_headland,
    generate_obstacle_headland,
    generate_parallel_tracks,
)
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


def visualize_stage1_pipeline():
    """Visualize complete Stage 1 pipeline."""

    # Create field with multiple obstacles
    print("Creating field with obstacles...")
    field = create_field_with_rectangular_obstacles(
        field_width=100,
        field_height=80,
        obstacle_specs=[
            (30, 30, 15, 12),  # Obstacle 1
            (65, 50, 12, 15),  # Obstacle 2
            (20, 10, 8, 8),  # Obstacle 3 (near boundary)
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

    # Generate field headland (preliminary, to classify obstacles)
    print("\nGenerating preliminary field headland...")
    preliminary_headland = generate_field_headland(
        field_boundary=field.boundary_polygon,
        operating_width=params.operating_width,
        num_passes=params.num_headland_passes,
    )

    # Classify obstacles
    print("Classifying obstacles...")
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

    # Extract Type B obstacles
    type_b_obstacles = get_type_b_obstacles(classified_obstacles)
    type_b_polygons = [obs.polygon for obs in type_b_obstacles]

    # Regenerate field headland with Type B obstacles incorporated
    print(f"\nIncorporating {len(type_b_obstacles)} Type B obstacles into inner boundary...")
    field_headland = generate_field_headland(
        field_boundary=field.boundary_polygon,
        operating_width=params.operating_width,
        num_passes=params.num_headland_passes,
        type_b_obstacles=type_b_polygons,
    )

    # Generate obstacle headlands
    print("\nGenerating obstacle headlands...")
    type_d_obstacles = get_type_d_obstacles(classified_obstacles)
    obstacle_headlands = []

    for obs in type_d_obstacles:
        obs_headland = generate_obstacle_headland(
            obstacle_boundary=obs.polygon,
            operating_width=params.operating_width,
            num_passes=params.num_headland_passes,
        )
        if obs_headland is not None:
            obstacle_headlands.append((obs, obs_headland))

    print(f"Generated {len(obstacle_headlands)} obstacle headlands")

    # Generate tracks
    print("\nGenerating field-work tracks...")
    tracks = generate_parallel_tracks(
        inner_boundary=field_headland.inner_boundary,
        driving_direction_degrees=params.driving_direction,
        operating_width=params.operating_width,
    )

    print(f"Generated {len(tracks)} tracks")
    print(f"Total track length: {sum(t.length for t in tracks):.2f}m")

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
    colors = plt.cm.Blues(np.linspace(0.4, 0.8, len(field_headland.passes)))
    for i, pass_poly in enumerate(field_headland.passes):
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
        field_headland.inner_boundary,
        color="red",
        linewidth=2,
        linestyle=":",
        label="Inner boundary",
    )

    # Classified obstacles with headlands (color-coded by type)
    for obs in classified_obstacles:
        if obs.obstacle_type.name == "B":
            color = "orange"  # Type B - near boundary
        elif obs.obstacle_type.name == "D":
            color = "gray"    # Type D - standard
        else:
            color = "lightgray"  # Type A/C if present
        plot_filled_polygon(ax2, obs.polygon, color=color, alpha=0.4)
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
    for obs, obs_headland in obstacle_headlands:
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
        ax3, field_headland.inner_boundary, color="lightblue", alpha=0.2, label="Field body"
    )
    plot_polygon(ax3, field_headland.inner_boundary, color="blue", linewidth=2)

    # Show all physical obstacles (Type B and Type D)
    # Type B are incorporated into inner boundary but still shown for clarity
    for obs in type_b_obstacles:
        plot_filled_polygon(ax3, obs.polygon, color="orange", alpha=0.6)
        plot_polygon(ax3, obs.polygon, color="black", linewidth=1.5)
    for obs in type_d_obstacles:
        plot_filled_polygon(ax3, obs.polygon, color="gray", alpha=0.6)
        plot_polygon(ax3, obs.polygon, color="black", linewidth=1.5)

    # Tracks
    for track in tracks:
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
