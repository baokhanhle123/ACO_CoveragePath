"""
Comprehensive test script for animation module.

Tests all components step-by-step to ensure everything works perfectly.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import numpy as np

print("=" * 80)
print("ANIMATION MODULE VERIFICATION")
print("=" * 80)
print()

# ====================
# Test 1: Module Imports
# ====================
print("[Test 1/7] Testing module imports...")
try:
    from src.data import FieldParameters, create_field_with_rectangular_obstacles
    from src.decomposition import boustrophedon_decomposition, merge_blocks_by_criteria
    from src.geometry import generate_field_headland, generate_parallel_tracks
    from src.obstacles.classifier import classify_all_obstacles, get_type_d_obstacles
    from src.optimization import (
        ACOParameters,
        ACOSolver,
        build_cost_matrix,
        generate_path_from_solution,
        get_path_statistics,
    )
    print("  ✓ All core modules imported successfully")
except ImportError as e:
    print(f"  ✗ Import error: {e}")
    sys.exit(1)

try:
    from src.visualization import PathAnimator, animate_path_execution
    from src.visualization.plot_utils import create_field_plot, plot_path_plan
    print("  ✓ Visualization module imported successfully")
except ImportError as e:
    print(f"  ✗ Visualization import error: {e}")
    sys.exit(1)

print()

# ====================
# Test 2: Field Creation
# ====================
print("[Test 2/7] Testing field creation...")
try:
    field = create_field_with_rectangular_obstacles(
        field_width=50,
        field_height=40,
        obstacle_specs=[(15, 15, 10, 8)],
        name="Test Field",
    )

    # Verify field attributes
    assert hasattr(field, 'boundary_polygon'), "Missing boundary_polygon"
    assert hasattr(field, 'obstacle_polygons'), "Missing obstacle_polygons"
    assert field.boundary_polygon is not None, "boundary_polygon is None"
    assert len(field.obstacle_polygons) > 0, "No obstacles created"

    print(f"  ✓ Field created: {field.name}")
    print(f"  ✓ Boundary polygon: {field.boundary_polygon.bounds}")
    print(f"  ✓ Obstacles: {len(field.obstacle_polygons)}")
except Exception as e:
    print(f"  ✗ Field creation error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()

# ====================
# Test 3: Complete Pipeline
# ====================
print("[Test 3/7] Testing complete pipeline (small field)...")
try:
    params = FieldParameters(
        operating_width=5.0,
        turning_radius=3.0,
        num_headland_passes=1,
        driving_direction=0.0,
        obstacle_threshold=5.0,
    )

    # Stage 1
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

    type_d_obstacles = get_type_d_obstacles(classified_obstacles)
    obstacle_polygons = [obs.polygon for obs in type_d_obstacles]

    # Stage 2
    preliminary_blocks = boustrophedon_decomposition(
        inner_boundary=field_headland.inner_boundary,
        obstacles=obstacle_polygons,
        driving_direction_degrees=params.driving_direction,
    )

    final_blocks = merge_blocks_by_criteria(
        blocks=preliminary_blocks,
        operating_width=params.operating_width
    )

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

    # Stage 3
    all_nodes = []
    node_index = 0
    for block in final_blocks:
        nodes = block.create_entry_exit_nodes(start_index=node_index)
        all_nodes.extend(nodes)
        node_index += 4

    cost_matrix = build_cost_matrix(blocks=final_blocks, nodes=all_nodes)

    aco_params = ACOParameters(
        alpha=1.0, beta=2.0, rho=0.1, q=100.0,
        num_ants=10, num_iterations=20, elitist_weight=2.0,
    )

    solver = ACOSolver(
        blocks=final_blocks,
        nodes=all_nodes,
        cost_matrix=cost_matrix,
        params=aco_params,
    )

    best_solution = solver.solve(verbose=False)

    assert best_solution is not None, "No solution found"
    assert best_solution.is_valid(len(final_blocks)), "Invalid solution"

    path_plan = generate_path_from_solution(best_solution, final_blocks, all_nodes)
    stats = get_path_statistics(path_plan)

    print(f"  ✓ Pipeline completed successfully")
    print(f"  ✓ Blocks: {len(final_blocks)}")
    print(f"  ✓ Nodes: {len(all_nodes)}")
    print(f"  ✓ Solution cost: {best_solution.cost:.2f}")
    print(f"  ✓ Path efficiency: {stats['efficiency']*100:.1f}%")
    print(f"  ✓ Waypoints: {stats['total_waypoints']}")

except Exception as e:
    print(f"  ✗ Pipeline error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()

# ====================
# Test 4: PathAnimator Initialization
# ====================
print("[Test 4/7] Testing PathAnimator initialization...")
try:
    animator = PathAnimator(
        field=field,
        blocks=final_blocks,
        path_plan=path_plan,
        figsize=(12, 8),
        fps=30,
        speed_multiplier=1.0
    )

    # Check animator attributes
    assert animator.waypoints is not None, "Waypoints not set"
    assert len(animator.waypoints) > 0, "No waypoints"
    assert len(animator.segment_boundaries) > 0, "No segment boundaries"

    print(f"  ✓ PathAnimator initialized")
    print(f"  ✓ Waypoints: {len(animator.waypoints)}")
    print(f"  ✓ Segments: {len(animator.segment_boundaries)}")

except Exception as e:
    print(f"  ✗ PathAnimator initialization error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()

# ====================
# Test 5: Tractor Icon Creation
# ====================
print("[Test 5/7] Testing tractor icon creation...")
try:
    tractor_patch = animator.create_tractor_icon(
        x=25.0,
        y=20.0,
        heading=np.pi/4,  # 45 degrees
        size=3.0,
        color='red'
    )

    assert tractor_patch is not None, "Tractor patch not created"

    print(f"  ✓ Tractor icon created successfully")
    print(f"  ✓ Patch type: {type(tractor_patch).__name__}")

except Exception as e:
    print(f"  ✗ Tractor icon error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()

# ====================
# Test 6: Static Plot Creation
# ====================
print("[Test 6/7] Testing static plot creation...")
try:
    # Test field plot
    fig1, ax1 = plt.subplots(figsize=(8, 6))
    ax1 = create_field_plot(field, ax=ax1)
    assert ax1 is not None, "Field plot failed"
    plt.close(fig1)

    # Test path plan plot
    fig2, ax2 = plot_path_plan(
        field=field,
        blocks=final_blocks,
        path_plan=path_plan,
        title="Test Path Plan"
    )
    assert fig2 is not None, "Path plan plot failed"
    plt.close(fig2)

    print(f"  ✓ Static plots created successfully")

except Exception as e:
    print(f"  ✗ Static plot error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()

# ====================
# Test 7: Animation Creation (Quick Test)
# ====================
print("[Test 7/7] Testing animation creation (quick test)...")
try:
    import os
    os.makedirs('test_output', exist_ok=True)

    # Create a very short animation for testing (only 10 frames)
    test_animator = PathAnimator(
        field=field,
        blocks=final_blocks,
        path_plan=path_plan,
        figsize=(10, 8),
        fps=10,
        speed_multiplier=len(animator.waypoints) / 10  # Only 10 frames
    )

    test_animator.save_animation(
        filename='test_output/test_animation.gif',
        dpi=50,  # Low DPI for speed
        writer='pillow'
    )

    # Check file was created
    assert os.path.exists('test_output/test_animation.gif'), "Animation file not created"

    file_size = os.path.getsize('test_output/test_animation.gif')
    print(f"  ✓ Test animation created successfully")
    print(f"  ✓ File: test_output/test_animation.gif")
    print(f"  ✓ Size: {file_size / 1024:.1f} KB")

    # Cleanup
    os.remove('test_output/test_animation.gif')
    os.rmdir('test_output')

except Exception as e:
    print(f"  ✗ Animation creation error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()

# ====================
# Summary
# ====================
print("=" * 80)
print("✓ ALL TESTS PASSED!")
print("=" * 80)
print()
print("Animation module is working perfectly:")
print("  ✓ All imports successful")
print("  ✓ Field objects structured correctly")
print("  ✓ Complete pipeline functional")
print("  ✓ PathAnimator initializes correctly")
print("  ✓ Tractor icon creation works")
print("  ✓ Static plots generate successfully")
print("  ✓ Animation creation and export works")
print()
print("Ready to proceed with full animations and dashboard!")
print("=" * 80)
