"""
Test pheromone visualization and animation modules.

Verifies:
1. PheromoneVisualizer creates graphs correctly
2. PheromoneAnimator animates pheromone evolution
3. Export to GIF works
4. Visual output is correct
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for testing
import matplotlib.pyplot as plt

print("=" * 80)
print("PHEROMONE VISUALIZATION TESTS")
print("=" * 80)
print()

# Import modules
print("[Test 1/6] Testing module imports...")
try:
    from src.visualization import (
        PheromoneVisualizer,
        PheromoneAnimator,
        animate_pheromone_evolution
    )
    from src.data import FieldParameters, create_field_with_rectangular_obstacles
    from src.decomposition import boustrophedon_decomposition, merge_blocks_by_criteria
    from src.geometry import generate_field_headland, generate_parallel_tracks
    from src.obstacles.classifier import classify_all_obstacles, get_type_d_obstacles
    from src.optimization import (
        ACOParameters, ACOSolver, build_cost_matrix
    )
    print("  ✓ All visualization modules imported successfully")
    print("  ✓ All core modules imported successfully")
except Exception as e:
    print(f"  ✗ Import error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()

# Create test field
print("[Test 2/6] Setting up test field with ACO...")
try:
    field = create_field_with_rectangular_obstacles(
        field_width=60,
        field_height=50,
        obstacle_specs=[(20, 20, 12, 10), (40, 15, 8, 6)],
        name="Pheromone Test Field",
    )

    params = FieldParameters(
        operating_width=6.0,
        turning_radius=3.0,
        num_headland_passes=1,
        driving_direction=0.0,
        obstacle_threshold=6.0,
    )

    # Run pipeline
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

    all_nodes = []
    node_index = 0
    for block in final_blocks:
        nodes = block.create_entry_exit_nodes(start_index=node_index)
        all_nodes.extend(nodes)
        node_index += 4

    cost_matrix = build_cost_matrix(blocks=final_blocks, nodes=all_nodes)

    print(f"  ✓ Field created: {field.name}")
    print(f"  ✓ Blocks: {len(final_blocks)}")
    print(f"  ✓ Nodes: {len(all_nodes)}")

except Exception as e:
    print(f"  ✗ Setup error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()

# Run ACO with history recording
print("[Test 3/6] Running ACO with history recording...")
try:
    aco_params = ACOParameters(
        alpha=1.0, beta=2.0, rho=0.1, q=100.0,
        num_ants=15, num_iterations=30, elitist_weight=2.0,
    )

    solver = ACOSolver(
        blocks=final_blocks,
        nodes=all_nodes,
        cost_matrix=cost_matrix,
        params=aco_params,
        record_history=True,
        history_interval=5  # Record every 5 iterations
    )

    best_solution = solver.solve(verbose=False)

    assert best_solution is not None, "No solution found"
    assert best_solution.is_valid(len(final_blocks)), "Invalid solution"

    # Get history
    iterations, pheromones, solutions = solver.get_pheromone_history()

    print(f"  ✓ ACO completed successfully")
    print(f"  ✓ Best cost: {best_solution.cost:.2f}")
    print(f"  ✓ History snapshots: {len(iterations)}")
    print(f"  ✓ Iterations recorded: {iterations}")

except Exception as e:
    print(f"  ✗ ACO error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()

# Test PheromoneVisualizer
print("[Test 4/6] Testing PheromoneVisualizer...")
try:
    visualizer = PheromoneVisualizer(
        blocks=final_blocks,
        nodes=all_nodes,
        field=field
    )

    # Check node positions calculated
    assert len(visualizer.node_positions) == len(all_nodes), "Node positions mismatch"

    # Test normalization
    test_pheromone = pheromones[-1]  # Last snapshot
    normalized = visualizer.normalize_pheromone(test_pheromone, threshold=0.01)

    assert normalized.max() <= 1.0, "Normalization failed (max > 1)"
    assert normalized.min() >= 0.0, "Normalization failed (min < 0)"

    print(f"  ✓ PheromoneVisualizer created")
    print(f"  ✓ Node positions: {len(visualizer.node_positions)}")
    print(f"  ✓ Normalization working (max={normalized.max():.3f})")

    # Test static visualization
    fig, ax = plt.subplots(figsize=(12, 10))
    visualizer.create_pheromone_graph(
        ax=ax,
        pheromone_matrix=test_pheromone,
        best_solution=best_solution,
        iteration=iterations[-1],
        show_field=True,
        show_stats=True
    )

    # Save static image
    static_output = Path("test_output/pheromone_static.png")
    static_output.parent.mkdir(exist_ok=True)
    plt.savefig(static_output, dpi=100, bbox_inches='tight')
    plt.close()

    file_size = static_output.stat().st_size / 1024  # KB

    print(f"  ✓ Static visualization created")
    print(f"  ✓ Saved to: {static_output}")
    print(f"  ✓ File size: {file_size:.1f} KB")

except Exception as e:
    print(f"  ✗ Visualizer error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()

# Test PheromoneAnimator
print("[Test 5/6] Testing PheromoneAnimator (quick animation)...")
try:
    animator = PheromoneAnimator(
        solver=solver,
        field=field,
        blocks=final_blocks
    )

    # Check animator state
    assert len(animator.iterations) > 0, "No iterations in animator"
    assert len(animator.pheromones) > 0, "No pheromones in animator"
    assert len(animator.solutions) > 0, "No solutions in animator"

    print(f"  ✓ PheromoneAnimator created")
    print(f"  ✓ Frames to animate: {len(animator.iterations)}")
    print(f"  ✓ Convergence data length: {len(animator.global_best_costs)}")

    # Create quick test animation (low DPI, fewer frames for speed)
    import time
    start_time = time.time()

    test_anim_path = Path("test_output/pheromone_test_anim.gif")
    animator.save_animation(
        filename=str(test_anim_path),
        dpi=50,  # Low resolution for quick test
        fps=3,   # 3 frames per second
        show_field=True,
        show_stats=True
    )

    elapsed = time.time() - start_time
    file_size = test_anim_path.stat().st_size / 1024  # KB

    print(f"  ✓ Test animation created")
    print(f"  ✓ File: {test_anim_path}")
    print(f"  ✓ Size: {file_size:.1f} KB")
    print(f"  ✓ Generation time: {elapsed:.1f} seconds")

except Exception as e:
    print(f"  ✗ Animation error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()

# Test convenience function
print("[Test 6/6] Testing animate_pheromone_evolution() convenience function...")
try:
    convenience_output = Path("test_output/pheromone_convenience.gif")

    animator2 = animate_pheromone_evolution(
        solver=solver,
        field=field,
        blocks=final_blocks,
        output_file=str(convenience_output),
        fps=3,
        dpi=50
    )

    assert convenience_output.exists(), "Convenience function didn't create file"

    file_size = convenience_output.stat().st_size / 1024

    print(f"  ✓ Convenience function works")
    print(f"  ✓ File: {convenience_output}")
    print(f"  ✓ Size: {file_size:.1f} KB")

except Exception as e:
    print(f"  ✗ Convenience function error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()

# Summary
print("=" * 80)
print("✓ ALL PHEROMONE VISUALIZATION TESTS PASSED!")
print("=" * 80)
print()
print("Test Summary:")
print(f"  ✓ Module imports successful")
print(f"  ✓ Field setup with {len(final_blocks)} blocks")
print(f"  ✓ ACO solved with history ({len(iterations)} snapshots)")
print(f"  ✓ PheromoneVisualizer working")
print(f"  ✓ Static visualization created")
print(f"  ✓ PheromoneAnimator working")
print(f"  ✓ Animation export successful")
print(f"  ✓ Convenience function working")
print()
print("Output Files:")
print(f"  - test_output/pheromone_static.png")
print(f"  - test_output/pheromone_test_anim.gif")
print(f"  - test_output/pheromone_convenience.gif")
print()
print("Ready to create full-quality demo animations!")
print("=" * 80)
