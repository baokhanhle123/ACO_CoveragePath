"""
Demo for Stage 3: ACO-based Path Optimization.

Demonstrates complete pipeline:
1. Field creation with obstacles
2. Stage 1: Geometric representation (headland, obstacles, tracks)
3. Stage 2: Boustrophedon decomposition and merging
4. Stage 3: ACO optimization and path generation
5. Visualization of optimized coverage path
"""

import matplotlib.pyplot as plt
import numpy as np

from src.data import FieldParameters, create_field_with_rectangular_obstacles
from src.decomposition import (
    boustrophedon_decomposition,
    cluster_tracks_into_blocks,
    merge_blocks_by_criteria,
)
from src.geometry import generate_field_headland, generate_parallel_tracks
from src.obstacles.classifier import classify_all_obstacles, get_type_b_obstacles, get_type_d_obstacles
from src.optimization import (
    ACOParameters,
    ACOSolver,
    build_cost_matrix,
    generate_path_from_solution,
    get_path_statistics,
)


def visualize_path(field, blocks, path_plan, classified_obstacles=None, title="ACO-Optimized Coverage Path"):
    """
    Visualize the complete coverage path.

    Shows:
    - Field boundary
    - All physical obstacles (Type B and Type D)
    - Blocks (colored, created around all obstacles)
    - Optimized coverage path

    Args:
        field: Field object
        blocks: List of blocks
        path_plan: PathPlan object
        classified_obstacles: List of classified obstacles (for labeling)
        title: Plot title
    """
    fig, ax = plt.subplots(figsize=(14, 10))

    # Draw field boundary
    field_x, field_y = zip(*field.boundary_polygon.exterior.coords)
    ax.plot(field_x, field_y, "k-", linewidth=2, label="Field Boundary")

    # Draw ALL physical obstacles (Type B and Type D)
    # Both types are included in decomposition to ensure paths avoid them
    if classified_obstacles:
        from src.obstacles.classifier import get_type_b_obstacles, get_type_d_obstacles
        type_b_obstacles = get_type_b_obstacles(classified_obstacles)
        type_d_obstacles = get_type_d_obstacles(classified_obstacles)

        # Draw Type D obstacles (gray)
        for i, obs in enumerate(type_d_obstacles):
            obs_x, obs_y = zip(*obs.polygon.exterior.coords)
            ax.fill(obs_x, obs_y, color="gray", alpha=0.5, edgecolor="black", linewidth=1.5)
            if i == 0:
                ax.plot([], [], "s", color="gray", alpha=0.5, label="Type D Obstacles")

        # Draw Type B obstacles (orange - near boundary)
        for i, obs in enumerate(type_b_obstacles):
            obs_x, obs_y = zip(*obs.polygon.exterior.coords)
            ax.fill(obs_x, obs_y, color="orange", alpha=0.5, edgecolor="black", linewidth=1.5)
            if i == 0:
                ax.plot([], [], "s", color="orange", alpha=0.5, label="Type B Obstacles")
    else:
        # Fallback: show all obstacles if classification not provided
        for i, obs in enumerate(field.obstacle_polygons):
            obs_x, obs_y = zip(*obs.exterior.coords)
            ax.fill(obs_x, obs_y, color="gray", alpha=0.5, edgecolor="black", linewidth=1.5)
            if i == 0:
                ax.plot([], [], "s", color="gray", alpha=0.5, label="Obstacles")

    # Draw blocks with different colors
    colors = plt.cm.Set3(np.linspace(0, 1, len(blocks)))
    for i, block in enumerate(blocks):
        block_x, block_y = zip(*block.polygon.exterior.coords)
        ax.fill(
            block_x,
            block_y,
            color=colors[i],
            alpha=0.3,
            edgecolor=colors[i],
            linewidth=2,
        )
        # Add block label
        centroid = block.polygon.centroid
        ax.text(
            centroid.x,
            centroid.y,
            f"Block {block.block_id}",
            ha="center",
            va="center",
            fontsize=10,
            fontweight="bold",
        )

    # Draw coverage path
    all_waypoints = path_plan.get_all_waypoints()
    if all_waypoints:
        path_x, path_y = zip(*all_waypoints)

        # Draw path with different styles for working vs transition
        prev_type = None
        segment_start = 0

        for i, segment in enumerate(path_plan.segments):
            segment_waypoints = segment.waypoints
            seg_x, seg_y = zip(*segment_waypoints)

            if segment.segment_type == "working":
                ax.plot(
                    seg_x,
                    seg_y,
                    "b-",
                    linewidth=2.5,
                    alpha=0.8,
                    label="Working Path" if prev_type != "working" else "",
                )
            else:  # transition
                ax.plot(
                    seg_x,
                    seg_y,
                    "r--",
                    linewidth=2,
                    alpha=0.6,
                    label="Transition" if prev_type != "transition" else "",
                )

            prev_type = segment.segment_type

        # Mark start and end
        ax.plot(
            path_x[0], path_y[0], "go", markersize=15, label="Start", zorder=10
        )
        ax.plot(path_x[-1], path_y[-1], "rs", markersize=15, label="End", zorder=10)

    ax.set_xlabel("X (meters)", fontsize=12)
    ax.set_ylabel("Y (meters)", fontsize=12)
    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.legend(loc="upper right", fontsize=10)
    ax.grid(True, alpha=0.3)
    ax.set_aspect("equal")

    plt.tight_layout()
    return fig


def visualize_convergence(solver, title="ACO Convergence"):
    """
    Visualize ACO convergence over iterations.

    Shows:
    - Best cost per iteration
    - Average cost per iteration
    """
    best_costs, avg_costs = solver.get_convergence_data()

    if not best_costs:
        print("No convergence data available")
        return None

    fig, ax = plt.subplots(figsize=(10, 6))

    iterations = range(len(best_costs))

    ax.plot(iterations, best_costs, "b-", linewidth=2, label="Best Solution", marker="o")
    ax.plot(iterations, avg_costs, "r--", linewidth=1.5, label="Average Solution", alpha=0.7)

    ax.set_xlabel("Iteration", fontsize=12)
    ax.set_ylabel("Path Cost", fontsize=12)
    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)

    # Add improvement annotation
    if len(best_costs) > 0:
        initial_best = best_costs[0]
        final_best = best_costs[-1]
        improvement = ((initial_best - final_best) / initial_best) * 100
        ax.text(
            0.02,
            0.98,
            f"Improvement: {improvement:.1f}%\nInitial: {initial_best:.2f}\nFinal: {final_best:.2f}",
            transform=ax.transAxes,
            fontsize=10,
            verticalalignment="top",
            bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.8),
        )

    plt.tight_layout()
    return fig


def print_summary(field, blocks, path_plan, solver):
    """Print summary statistics."""
    print("\n" + "=" * 80)
    print("STAGE 3 DEMO: ACO-based Coverage Path Optimization")
    print("=" * 80)

    print("\n[FIELD SETUP]")
    print(f"  Field: {field.name}")
    print(f"  Dimensions: {field.boundary_polygon.bounds}")
    print(f"  Obstacles: {len(field.obstacles)}")

    print("\n[DECOMPOSITION]")
    print(f"  Blocks: {len(blocks)}")
    total_tracks = sum(len(block.tracks) for block in blocks)
    print(f"  Total tracks: {total_tracks}")

    print("\n[ACO OPTIMIZATION]")
    best_costs, _ = solver.get_convergence_data()
    if best_costs:
        initial_best = best_costs[0]
        final_best = best_costs[-1]
        improvement = ((initial_best - final_best) / initial_best) * 100
        print(f"  Initial best cost: {initial_best:.2f}")
        print(f"  Final best cost: {final_best:.2f}")
        print(f"  Improvement: {improvement:.1f}%")
        print(f"  Iterations: {len(best_costs)}")

    print("\n[PATH PLAN]")
    stats = get_path_statistics(path_plan)
    print(f"  Total distance: {stats['total_distance']:.2f} m")
    print(f"  Working distance: {stats['working_distance']:.2f} m")
    print(f"  Transition distance: {stats['transition_distance']:.2f} m")
    print(f"  Efficiency: {stats['efficiency']*100:.1f}%")
    print(f"  Block sequence: {path_plan.block_sequence}")
    print(f"  Segments: {stats['num_working_segments']} working + {stats['num_transition_segments']} transitions")
    print(f"  Total waypoints: {stats['total_waypoints']}")

    print("\n" + "=" * 80)


def run_demo():
    """Run complete Stage 3 demonstration."""
    print("Starting Stage 3 Demo...")

    # ====================
    # STAGE 1: Field Setup
    # ====================
    print("\n[1/5] Creating field with obstacles...")

    field = create_field_with_rectangular_obstacles(
        field_width=100,
        field_height=80,
        obstacle_specs=[
            (30, 30, 15, 12),  # Obstacle 1 (same as Stage 1 & 2)
            (65, 50, 12, 15),  # Obstacle 2 (same as Stage 1 & 2)
            (20, 10, 8, 8),    # Obstacle 3 (same as Stage 1 & 2)
        ],
        name="Stage 3 Demo Field",
    )

    params = FieldParameters(
        operating_width=5.0,
        turning_radius=3.0,
        num_headland_passes=2,
        driving_direction=0.0,
        obstacle_threshold=5.0,
    )

    # Generate preliminary headland (to classify obstacles)
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

    # Extract Type B and Type D obstacles
    type_b_obstacles = get_type_b_obstacles(classified_obstacles)
    type_b_polygons = [obs.polygon for obs in type_b_obstacles]
    type_d_obstacles = get_type_d_obstacles(classified_obstacles)
    type_d_polygons = [obs.polygon for obs in type_d_obstacles]

    # Regenerate headland with Type B obstacles incorporated
    # Type B obstacles are incorporated into inner boundary to prevent tracks from squeezing
    # between obstacle and field boundary, but they STILL participate in decomposition
    # to ensure transitions avoid them
    field_headland = generate_field_headland(
        field_boundary=field.boundary_polygon,
        operating_width=params.operating_width,
        num_passes=params.num_headland_passes,
        type_b_obstacles=type_b_polygons,
    )

    print(f"  ✓ Field created with {len(type_b_obstacles)} Type B obstacles (incorporated into boundary)")
    print(f"  ✓ {len(type_d_obstacles)} Type D obstacles")
    print(f"  ✓ All {len(type_b_obstacles) + len(type_d_obstacles)} physical obstacles will be used for decomposition")

    # Generate global tracks (Stage 1 - ignoring obstacles)
    print("\n[1.5/5] Generating global tracks (ignoring obstacles)...")
    global_tracks = generate_parallel_tracks(
        inner_boundary=field_headland.inner_boundary,
        driving_direction_degrees=params.driving_direction,
        operating_width=params.operating_width,
    )
    print(f"  ✓ Generated {len(global_tracks)} global tracks")

    # ====================
    # STAGE 2: Decomposition
    # ====================
    print("\n[2/5] Running boustrophedon decomposition...")

    # Include BOTH Type B and Type D obstacles in decomposition
    # Type B obstacles are physical obstacles that must be avoided by ALL paths (working + transitions)
    # They are incorporated into inner boundary to avoid track squeezing, but still need decomposition
    all_obstacles = type_b_polygons + type_d_polygons

    preliminary_blocks = boustrophedon_decomposition(
        inner_boundary=field_headland.inner_boundary,
        obstacles=all_obstacles,  # Both Type B and Type D
        driving_direction_degrees=params.driving_direction,
    )

    final_blocks = merge_blocks_by_criteria(
        blocks=preliminary_blocks, operating_width=params.operating_width
    )

    # Cluster global tracks into blocks (Section 2.3.2)
    # Pass all_obstacles to enable subdivision at obstacle boundaries within blocks
    print(f"\n[2.5/5] Clustering {len(global_tracks)} global tracks into {len(final_blocks)} blocks...")
    final_blocks = cluster_tracks_into_blocks(global_tracks, final_blocks, all_obstacles)

    total_track_segments = sum(len(block.tracks) for block in final_blocks)
    print(f"  ✓ Created {total_track_segments} track segments across {len(final_blocks)} blocks")

    # ====================
    # STAGE 3: Entry/Exit Nodes
    # ====================
    print("\n[3/5] Creating entry/exit nodes...")

    all_nodes = []
    node_index = 0

    for block in final_blocks:
        nodes = block.create_entry_exit_nodes(start_index=node_index)
        all_nodes.extend(nodes)
        node_index += 4

    print(f"  ✓ Created {len(all_nodes)} nodes")

    # ====================
    # STAGE 3: ACO Optimization
    # ====================
    print("\n[4/5] Running ACO optimization...")

    # Build cost matrix
    cost_matrix = build_cost_matrix(
        blocks=final_blocks, nodes=all_nodes, turning_penalty=0.0
    )

    # Create ACO solver with parameters from Zhou et al. 2014 (Section 2.4.2, page 18)
    # Paper specifies: α=1, β=5, ρ=0.5, num_ants=n (number of nodes)
    aco_params = ACOParameters(
        alpha=1.0,      # Pheromone importance (paper: α=1)
        beta=5.0,       # Heuristic importance (paper: β=5, NOT 2!)
        rho=0.5,        # Evaporation rate (paper: ρ=0.5)
        q=100.0,        # Pheromone deposit constant
        num_ants=len(all_nodes),  # Paper: num_ants = n (number of nodes)
        num_iterations=100,       # Sufficient for convergence
        elitist_weight=2.0,       # Elitist strategy weight
    )

    solver = ACOSolver(
        blocks=final_blocks,
        nodes=all_nodes,
        cost_matrix=cost_matrix,
        params=aco_params,
    )

    # Run optimization
    best_solution = solver.solve(verbose=True)

    if best_solution is None or not best_solution.is_valid(len(final_blocks)):
        print("  ✗ Failed to find valid solution!")
        return

    print(f"  ✓ Found optimal solution with cost {best_solution.cost:.2f}")

    # ====================
    # STAGE 3: Path Generation
    # ====================
    print("\n[5/5] Generating complete coverage path...")

    path_plan = generate_path_from_solution(best_solution, final_blocks, all_nodes)

    print(f"  ✓ Generated path with {len(path_plan.segments)} segments")

    # ====================
    # Results and Visualization
    # ====================
    print_summary(field, final_blocks, path_plan, solver)

    # Create visualizations
    print("\nGenerating visualizations...")

    fig1 = visualize_path(field, final_blocks, path_plan, classified_obstacles)
    fig2 = visualize_convergence(solver)

    # Save figures to results/plots directory
    import os
    os.makedirs("results/plots", exist_ok=True)

    fig1.savefig("results/plots/stage3_path.png", dpi=150, bbox_inches="tight")
    fig2.savefig("results/plots/stage3_convergence.png", dpi=150, bbox_inches="tight")

    print("\n✓ Visualizations saved:")
    print("  - results/plots/stage3_path.png")
    print("  - results/plots/stage3_convergence.png")

    plt.show()

    print("\nStage 3 Demo Complete!")


if __name__ == "__main__":
    run_demo()
