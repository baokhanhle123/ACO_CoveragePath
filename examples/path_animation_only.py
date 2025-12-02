"""
Demo: Animated Path Execution with Tractor Icon

This demo creates an impressive animation showing:
- Tractor moving along the coverage path
- Rotation based on movement direction
- Trail showing path covered
- Progress bar and real-time statistics
- Working vs transition segments highlighted

Output: Saves animated GIF and MP4 video
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.data import FieldParameters, create_field_with_rectangular_obstacles
from src.decomposition import (
    boustrophedon_decomposition,
    cluster_tracks_into_blocks,
    merge_blocks_by_criteria,
)
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
from src.visualization import animate_path_execution


def main():
    print("=" * 80)
    print("ANIMATED PATH EXECUTION DEMO")
    print("=" * 80)
    print()

    # ====================
    # Create Field
    # ====================
    print("[1/6] Creating field with obstacles...")

    field = create_field_with_rectangular_obstacles(
        field_width=100,
        field_height=80,
        obstacle_specs=[
            (20, 20, 15, 12),  # Obstacle 1
            (55, 30, 12, 15),  # Obstacle 2
            (35, 60, 18, 10),  # Obstacle 3
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

    print(f"  ✓ Field created: {field.name}")
    print(f"  ✓ Dimensions: {field.boundary_polygon.bounds}")
    print()

    # ====================
    # Stage 1: Geometric Representation
    # ====================
    print("[2/6] Generating headland and classifying obstacles...")

    field_headland = generate_field_headland(
        field_boundary=field.boundary_polygon,
        operating_width=params.operating_width,
        num_passes=params.num_headland_passes,
    )

    classified_obstacles = classify_all_obstacles(
        obstacle_boundaries=field.obstacles,
        field_inner_boundary=field_headland.inner_boundary,
        driving_direction_degrees=params.driving_direction,
        operating_width=params.operating_width,
        threshold=params.obstacle_threshold,
    )

    # Extract Type B and Type D obstacles
    type_b_obstacles = get_type_b_obstacles(classified_obstacles)
    type_d_obstacles = get_type_d_obstacles(classified_obstacles)
    type_b_polygons = [obs.polygon for obs in type_b_obstacles]
    type_d_polygons = [obs.polygon for obs in type_d_obstacles]

    print(f"  ✓ Type B obstacles (incorporated into boundary): {len(type_b_obstacles)}")
    print(f"  ✓ Type D obstacles (for decomposition): {len(type_d_obstacles)}")

    # Regenerate headland with Type B obstacles incorporated
    field_headland = generate_field_headland(
        field_boundary=field.boundary_polygon,
        operating_width=params.operating_width,
        num_passes=params.num_headland_passes,
        type_b_obstacles=type_b_polygons,
    )

    # All physical obstacles must be avoided by paths
    all_physical_obstacles = type_b_polygons + type_d_polygons
    obstacle_polygons = type_d_polygons  # Only Type D for decomposition
    print()

    # ====================
    # Stage 2: Decomposition
    # ====================
    # Generate global tracks (ignoring obstacles)
    print("[2.5/6] Generating global field-work tracks...")
    global_tracks = generate_parallel_tracks(
        inner_boundary=field_headland.inner_boundary,
        driving_direction_degrees=params.driving_direction,
        operating_width=params.operating_width,
    )
    print(f"  ✓ Generated {len(global_tracks)} global tracks")
    print()

    print("[3/6] Running boustrophedon decomposition...")

    preliminary_blocks = boustrophedon_decomposition(
        inner_boundary=field_headland.inner_boundary,
        obstacles=obstacle_polygons,
        driving_direction_degrees=params.driving_direction,
    )

    final_blocks = merge_blocks_by_criteria(
        blocks=preliminary_blocks, operating_width=params.operating_width
    )

    # Cluster global tracks into blocks
    print(f"\nClustering {len(global_tracks)} global tracks into {len(final_blocks)} blocks...")
    final_blocks = cluster_tracks_into_blocks(
        global_tracks,
        final_blocks,
        all_physical_obstacles
    )
    total_track_segments = sum(len(block.tracks) for block in final_blocks)
    print(f"  ✓ Created {total_track_segments} track segments")
    print()

    # ====================
    # Stage 3: ACO Optimization
    # ====================
    print("[4/6] Running ACO optimization...")

    # Create entry/exit nodes
    all_nodes = []
    node_index = 0
    for block in final_blocks:
        nodes = block.create_entry_exit_nodes(start_index=node_index)
        all_nodes.extend(nodes)
        node_index += 4

    # Build cost matrix
    cost_matrix = build_cost_matrix(blocks=final_blocks, nodes=all_nodes)

    # Run ACO
    aco_params = ACOParameters(
        alpha=1.0,
        beta=2.0,
        rho=0.1,
        q=100.0,
        num_ants=30,
        num_iterations=100,
        elitist_weight=2.0,
    )

    solver = ACOSolver(
        blocks=final_blocks,
        nodes=all_nodes,
        cost_matrix=cost_matrix,
        params=aco_params,
    )

    best_solution = solver.solve(verbose=True)

    if best_solution is None or not best_solution.is_valid(len(final_blocks)):
        print("  ✗ Failed to find valid solution!")
        return

    print(f"  ✓ Found solution with cost {best_solution.cost:.2f}")
    print()

    # ====================
    # Generate Path
    # ====================
    print("[5/6] Generating complete coverage path...")

    path_plan = generate_path_from_solution(
        best_solution,
        final_blocks,
        all_nodes,
        obstacles=all_physical_obstacles  # Pass all physical obstacles
    )
    stats = get_path_statistics(path_plan)

    print(f"  ✓ Total distance: {stats['total_distance']:.2f} m")
    print(f"  ✓ Working distance: {stats['working_distance']:.2f} m ({stats['efficiency']*100:.1f}%)")
    print(f"  ✓ Segments: {stats['num_working_segments']} working + {stats['num_transition_segments']} transitions")
    print(f"  ✓ Waypoints: {stats['total_waypoints']}")
    print()

    # ====================
    # Create Animation
    # ====================
    print("[6/6] Creating animated path execution...")
    print()

    # Create output directory
    import os
    os.makedirs('animations', exist_ok=True)

    # Create GIF animation (smaller file, good for presentations)
    print("Creating GIF animation (optimized for presentations)...")
    animate_path_execution(
        field=field,
        blocks=final_blocks,
        path_plan=path_plan,
        output_file='animations/path_execution.gif',
        fps=30,
        speed_multiplier=2.0,  # 2x speed for faster demo
        figsize=(16, 10)
    )

    # Create MP4 animation (higher quality, good for videos)
    print("\nCreating MP4 video (high quality)...")
    try:
        animate_path_execution(
            field=field,
            blocks=final_blocks,
            path_plan=path_plan,
            output_file='animations/path_execution.mp4',
            fps=30,
            speed_multiplier=2.0,
            figsize=(16, 10)
        )
    except Exception as e:
        print(f"  ⚠ Could not create MP4 (ffmpeg not installed): {e}")
        print(f"  ℹ GIF animation is available at animations/path_execution.gif")

    print()
    print("=" * 80)
    print("ANIMATION DEMO COMPLETE!")
    print("=" * 80)
    print()
    print("Output files:")
    print("  - animations/path_execution.gif (for presentations)")
    if os.path.exists('animations/path_execution.mp4'):
        print("  - animations/path_execution.mp4 (high quality video)")
    print()
    print("Features in animation:")
    print("  ✓ Tractor icon moving along path")
    print("  ✓ Rotation based on movement direction")
    print("  ✓ Trail showing covered path")
    print("  ✓ Progress bar at top")
    print("  ✓ Real-time statistics (distance, waypoint, mode)")
    print("  ✓ Color-coded: Green=Working, Orange=Transition")
    print()


if __name__ == "__main__":
    main()
