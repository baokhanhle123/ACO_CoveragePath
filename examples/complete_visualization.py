"""
Complete Visualization Demo - ACO Coverage Path Planning

This demo showcases all visualization capabilities:
1. Path execution animation with moving tractor
2. Pheromone evolution animation showing ACO learning
3. Convergence plots and statistics

Perfect for class presentations and demonstrations!
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import time

print("=" * 80)
print("COMPLETE VISUALIZATION DEMO")
print("ACO-Based Agricultural Coverage Path Planning")
print("=" * 80)
print()

# Import all required modules
print("Importing modules...")
from src.data import FieldParameters, create_field_with_rectangular_obstacles
from src.decomposition import boustrophedon_decomposition, merge_blocks_by_criteria
from src.geometry import generate_field_headland, generate_parallel_tracks
from src.obstacles.classifier import classify_all_obstacles, get_type_d_obstacles
from src.optimization import (
    ACOParameters, ACOSolver, build_cost_matrix,
    generate_path_from_solution
)
from src.visualization import (
    PathAnimator,
    PheromoneAnimator,
    animate_path_execution,
    animate_pheromone_evolution
)
print("✓ All modules imported successfully\n")

# ============================================================================
# STAGE 1: Field Setup
# ============================================================================
print("=" * 80)
print("STAGE 1: Field Setup")
print("=" * 80)
print()

# Create demonstration field with multiple obstacles
field = create_field_with_rectangular_obstacles(
    field_width=100,
    field_height=80,
    obstacle_specs=[
        (25, 25, 15, 12),  # Large obstacle
        (65, 20, 12, 10),  # Medium obstacle
        (50, 55, 10, 8),   # Small obstacle
    ],
    name="Demo Field - Complete Visualization"
)

params = FieldParameters(
    operating_width=5.0,
    turning_radius=3.0,
    num_headland_passes=1,
    driving_direction=0.0,
    obstacle_threshold=5.0,
)

print(f"Field created: {field.name}")
min_x, min_y, max_x, max_y = field.bounds
width = max_x - min_x
height = max_y - min_y
print(f"  Dimensions: {width:.1f} × {height:.1f} m")
print(f"  Obstacles: {len(field.obstacles)}")
print(f"  Operating width: {params.operating_width} m")
print()

# ============================================================================
# STAGE 2: Decomposition
# ============================================================================
print("=" * 80)
print("STAGE 2: Field Decomposition")
print("=" * 80)
print()

# Generate headland
field_headland = generate_field_headland(
    field_boundary=field.boundary_polygon,
    operating_width=params.operating_width,
    num_passes=params.num_headland_passes,
)
print("✓ Headland generated")

# Classify obstacles
classified_obstacles = classify_all_obstacles(
    obstacle_boundaries=field.obstacles,
    field_inner_boundary=field_headland.inner_boundary,
    driving_direction_degrees=params.driving_direction,
    operating_width=params.operating_width,
    threshold=params.obstacle_threshold,
)
print(f"✓ Obstacles classified")

# Get Type D obstacles
type_d_obstacles = get_type_d_obstacles(classified_obstacles)
obstacle_polygons = [obs.polygon for obs in type_d_obstacles]
print(f"✓ Type D obstacles: {len(type_d_obstacles)}")

# Boustrophedon decomposition
preliminary_blocks = boustrophedon_decomposition(
    inner_boundary=field_headland.inner_boundary,
    obstacles=obstacle_polygons,
    driving_direction_degrees=params.driving_direction,
)
print(f"✓ Preliminary blocks: {len(preliminary_blocks)}")

# Merge blocks
final_blocks = merge_blocks_by_criteria(
    blocks=preliminary_blocks,
    operating_width=params.operating_width
)
print(f"✓ Final blocks after merging: {len(final_blocks)}")

# Generate tracks for each block
print("\nGenerating tracks...")
for block in final_blocks:
    tracks = generate_parallel_tracks(
        inner_boundary=block.polygon,
        driving_direction_degrees=params.driving_direction,
        operating_width=params.operating_width,
    )
    for i, track in enumerate(tracks):
        track.block_id = block.block_id
        track.index = i
    block.tracks = tracks
    print(f"  Block {block.block_id}: {len(tracks)} tracks")

print()

# ============================================================================
# STAGE 3: ACO Optimization (WITH HISTORY RECORDING)
# ============================================================================
print("=" * 80)
print("STAGE 3: ACO Optimization with History Recording")
print("=" * 80)
print()

# Create nodes
all_nodes = []
node_index = 0
for block in final_blocks:
    nodes = block.create_entry_exit_nodes(start_index=node_index)
    all_nodes.extend(nodes)
    node_index += 4

print(f"Total nodes: {len(all_nodes)} ({len(final_blocks)} blocks × 4 nodes/block)")

# Build cost matrix
cost_matrix = build_cost_matrix(blocks=final_blocks, nodes=all_nodes)
print(f"Cost matrix: {cost_matrix.shape[0]}×{cost_matrix.shape[1]}")
print()

# Configure ACO parameters
aco_params = ACOParameters(
    alpha=1.0,
    beta=2.0,
    rho=0.1,
    q=100.0,
    num_ants=20,
    num_iterations=50,  # More iterations for better demo
    elitist_weight=2.0,
)

print("ACO Parameters:")
print(f"  Ants per iteration: {aco_params.num_ants}")
print(f"  Total iterations: {aco_params.num_iterations}")
print(f"  Alpha (pheromone): {aco_params.alpha}")
print(f"  Beta (heuristic): {aco_params.beta}")
print(f"  Rho (evaporation): {aco_params.rho}")
print()

# Run ACO with history recording
print("Running ACO optimization...")
start_time = time.time()

solver = ACOSolver(
    blocks=final_blocks,
    nodes=all_nodes,
    cost_matrix=cost_matrix,
    params=aco_params,
    record_history=True,      # ENABLE HISTORY RECORDING
    history_interval=5,       # Record every 5 iterations
)

best_solution = solver.solve(verbose=True)

elapsed = time.time() - start_time
print(f"\n✓ ACO completed in {elapsed:.1f} seconds")

if best_solution:
    print(f"\nBest Solution Found:")
    print(f"  Total cost: {best_solution.cost:.2f}")
    print(f"  Block sequence: {best_solution.block_sequence}")

    # Get history info
    iterations, pheromones, solutions = solver.get_pheromone_history()
    print(f"\nHistory Recorded:")
    print(f"  Snapshots: {len(iterations)}")
    print(f"  Iterations: {iterations}")

    # Calculate improvement
    initial_cost = solutions[0].cost
    final_cost = solutions[-1].cost
    improvement = ((initial_cost - final_cost) / initial_cost) * 100
    print(f"\nCost Improvement:")
    print(f"  Initial: {initial_cost:.2f}")
    print(f"  Final: {final_cost:.2f}")
    print(f"  Improvement: {improvement:.1f}%")
else:
    print("✗ No valid solution found!")
    sys.exit(1)

print()

# ============================================================================
# STAGE 4: Path Planning
# ============================================================================
print("=" * 80)
print("STAGE 4: Path Planning")
print("=" * 80)
print()

# Generate complete path
path_plan = generate_path_from_solution(
    solution=best_solution,
    blocks=final_blocks,
    nodes=all_nodes
)

# Get statistics
all_waypoints = path_plan.get_all_waypoints()
total_distance = path_plan.total_distance
working_distance = path_plan.working_distance
transition_distance = path_plan.transition_distance
efficiency = (working_distance / total_distance) * 100 if total_distance > 0 else 0

print("Path Plan Generated:")
print(f"  Total segments: {len(path_plan.segments)}")
print(f"  Total waypoints: {len(all_waypoints)}")
print(f"  Total distance: {total_distance:.2f} m")
print(f"  Working distance: {working_distance:.2f} m")
print(f"  Transition distance: {transition_distance:.2f} m")
print(f"  Path efficiency: {efficiency:.1f}%")
print()

# ============================================================================
# STAGE 5: Animation Creation
# ============================================================================
print("=" * 80)
print("STAGE 5: Creating Visualizations")
print("=" * 80)
print()

# Create output directory
output_dir = Path("animations")
output_dir.mkdir(exist_ok=True)

# 1. Path Execution Animation
print("[1/2] Creating path execution animation...")
print("  (Tractor moving along coverage path)")

path_anim_file = output_dir / "demo_path_execution.gif"
start_time = time.time()

path_animator = PathAnimator(
    field=field,
    blocks=final_blocks,
    path_plan=path_plan,
    figsize=(16, 10),
    fps=30,
    speed_multiplier=1.5  # Slightly faster for demo
)

path_animator.save_animation(
    filename=str(path_anim_file),
    dpi=150,
    writer='pillow'
)

elapsed = time.time() - start_time
file_size = path_anim_file.stat().st_size / (1024 * 1024)  # MB

print(f"  ✓ Path animation complete")
print(f"  ✓ File: {path_anim_file}")
print(f"  ✓ Size: {file_size:.2f} MB")
print(f"  ✓ Time: {elapsed:.1f} seconds")
print()

# 2. Pheromone Evolution Animation
print("[2/2] Creating pheromone evolution animation...")
print("  (ACO learning process visualization)")

pheromone_anim_file = output_dir / "demo_pheromone_evolution.gif"
start_time = time.time()

pheromone_animator = PheromoneAnimator(
    solver=solver,
    field=field,
    blocks=final_blocks
)

pheromone_animator.save_animation(
    filename=str(pheromone_anim_file),
    dpi=120,
    fps=2,  # Slower to appreciate pheromone changes
    show_field=True,
    show_stats=True
)

elapsed = time.time() - start_time
file_size = pheromone_anim_file.stat().st_size / (1024 * 1024)  # MB

print(f"  ✓ Pheromone animation complete")
print(f"  ✓ File: {pheromone_anim_file}")
print(f"  ✓ Size: {file_size:.2f} MB")
print(f"  ✓ Time: {elapsed:.1f} seconds")
print()

# ============================================================================
# SUMMARY
# ============================================================================
print("=" * 80)
print("DEMO COMPLETE - ALL VISUALIZATIONS CREATED!")
print("=" * 80)
print()

print("Field Configuration:")
print(f"  ✓ {len(final_blocks)} blocks covering {width}×{height}m field")
print(f"  ✓ {len(field.obstacles)} obstacles")
print(f"  ✓ {len(all_waypoints)} waypoints in coverage path")
print()

print("Optimization Results:")
print(f"  ✓ ACO converged in {aco_params.num_iterations} iterations")
print(f"  ✓ Best cost: {best_solution.cost:.2f}")
print(f"  ✓ Path efficiency: {efficiency:.1f}%")
print(f"  ✓ Cost improved by {improvement:.1f}%")
print()

print("Output Files:")
print(f"  1. Path Execution Animation:")
print(f"     {path_anim_file}")
print(f"     Shows: Tractor moving along optimized path")
print()
print(f"  2. Pheromone Evolution Animation:")
print(f"     {pheromone_anim_file}")
print(f"     Shows: ACO learning process with convergence")
print()

print("Ready for presentation!")
print("=" * 80)
