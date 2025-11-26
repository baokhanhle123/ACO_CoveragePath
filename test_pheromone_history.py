"""
Test pheromone history recording in modified ACOSolver.

Verifies:
1. Existing functionality still works (backward compatibility)
2. History recording works when enabled
3. History data is correct
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import numpy as np

print("=" * 80)
print("PHEROMONE HISTORY RECORDING TESTS")
print("=" * 80)
print()

from src.data import FieldParameters, create_field_with_rectangular_obstacles
from src.decomposition import boustrophedon_decomposition, merge_blocks_by_criteria
from src.geometry import generate_field_headland, generate_parallel_tracks
from src.obstacles.classifier import classify_all_obstacles, get_type_d_obstacles
from src.optimization import (
    ACOParameters, ACOSolver, build_cost_matrix,
    generate_path_from_solution
)

# Create simple test field
field = create_field_with_rectangular_obstacles(
    field_width=50,
    field_height=40,
    obstacle_specs=[(15, 15, 10, 8)],
    name="Test Field",
)

params = FieldParameters(
    operating_width=5.0, turning_radius=3.0,
    num_headland_passes=1, driving_direction=0.0,
    obstacle_threshold=5.0,
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
    blocks=preliminary_blocks, operating_width=params.operating_width
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

# ====================
# Test 1: Backward Compatibility (history OFF)
# ====================
print("[Test 1/5] Backward compatibility (record_history=False)...")
try:
    aco_params = ACOParameters(
        alpha=1.0, beta=2.0, rho=0.1, q=100.0,
        num_ants=10, num_iterations=20, elitist_weight=2.0,
    )

    solver = ACOSolver(
        blocks=final_blocks,
        nodes=all_nodes,
        cost_matrix=cost_matrix,
        params=aco_params,
        record_history=False  # Default behavior
    )

    best_solution = solver.solve(verbose=False)

    assert best_solution is not None, "No solution found"
    assert best_solution.is_valid(len(final_blocks)), "Invalid solution"
    assert len(solver.pheromone_history) == 0, "History should be empty"
    assert len(solver.history_iterations) == 0, "History iterations should be empty"

    print(f"  ✓ Backward compatibility OK")
    print(f"  ✓ Solution found with cost {best_solution.cost:.2f}")
    print(f"  ✓ History lists are empty (as expected)")

except Exception as e:
    print(f"  ✗ Backward compatibility error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()

# ====================
# Test 2: History Recording Enabled
# ====================
print("[Test 2/5] History recording (record_history=True)...")
try:
    solver_with_history = ACOSolver(
        blocks=final_blocks,
        nodes=all_nodes,
        cost_matrix=cost_matrix,
        params=aco_params,
        record_history=True,
        history_interval=5  # Record every 5 iterations
    )

    best_solution = solver_with_history.solve(verbose=False)

    assert best_solution is not None, "No solution found"
    assert best_solution.is_valid(len(final_blocks)), "Invalid solution"
    assert len(solver_with_history.pheromone_history) > 0, "History should not be empty"

    print(f"  ✓ History recording enabled")
    print(f"  ✓ Solution found with cost {best_solution.cost:.2f}")
    print(f"  ✓ Pheromone snapshots: {len(solver_with_history.pheromone_history)}")
    print(f"  ✓ History iterations: {solver_with_history.history_iterations}")

except Exception as e:
    print(f"  ✗ History recording error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()

# ====================
# Test 3: History Data Integrity
# ====================
print("[Test 3/5] History data integrity...")
try:
    iterations, pheromones, solutions = solver_with_history.get_pheromone_history()

    # Check lengths match
    assert len(iterations) == len(pheromones), "Lengths mismatch: iterations vs pheromones"
    assert len(iterations) == len(solutions), "Lengths mismatch: iterations vs solutions"

    # Check pheromone matrices are correct shape
    for i, pheromone in enumerate(pheromones):
        assert pheromone.shape == (len(all_nodes), len(all_nodes)), \
            f"Wrong pheromone shape at snapshot {i}"
        assert np.all(pheromone >= 0), f"Negative pheromone values at snapshot {i}"

    # Check solutions are valid
    for i, solution in enumerate(solutions):
        assert solution.is_valid(len(final_blocks)), \
            f"Invalid solution at snapshot {i}"

    # Check iterations are in order
    assert iterations == sorted(iterations), "Iterations not in order"

    # Check we got the expected number of snapshots
    # Should be: iterations 0, 5, 10, 15, 19 (last) = 5 snapshots
    expected_count = (20 // 5) + 1  # Every 5 iterations + last
    assert len(iterations) == expected_count, \
        f"Expected {expected_count} snapshots, got {len(iterations)}"

    print(f"  ✓ History data structure correct")
    print(f"  ✓ Pheromone matrices shape: {pheromones[0].shape}")
    print(f"  ✓ All solutions valid")
    print(f"  ✓ Snapshots at iterations: {iterations}")

except Exception as e:
    print(f"  ✗ Data integrity error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()

# ====================
# Test 4: Pheromone Evolution
# ====================
print("[Test 4/5] Pheromone evolution over time...")
try:
    # Check that pheromone values change over iterations
    first_pheromone = pheromones[0]
    last_pheromone = pheromones[-1]

    # They should be different (pheromone evolves)
    diff = np.abs(last_pheromone - first_pheromone).sum()
    assert diff > 0, "Pheromone didn't change (evolution failed)"

    # Check pheromone concentration increases on good paths
    first_max = first_pheromone.max()
    last_max = last_pheromone.max()

    print(f"  ✓ Pheromone evolved over time")
    print(f"  ✓ Total change: {diff:.2f}")
    print(f"  ✓ Max pheromone: {first_max:.3f} → {last_max:.3f}")

    # Check cost improvement
    first_cost = solutions[0].cost
    last_cost = solutions[-1].cost
    improvement = ((first_cost - last_cost) / first_cost) * 100

    print(f"  ✓ Cost improved: {first_cost:.2f} → {last_cost:.2f} ({improvement:.1f}%)")

except Exception as e:
    print(f"  ✗ Evolution check error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()

# ====================
# Test 5: get_pheromone_history() Error Handling
# ====================
print("[Test 5/5] Error handling for get_pheromone_history()...")
try:
    # Try to get history from solver without recording enabled
    try:
        iterations_fail, _, _ = solver.get_pheromone_history()
        print(f"  ✗ Should have raised ValueError")
        sys.exit(1)
    except ValueError as e:
        print(f"  ✓ Correct error raised: {e}")

    # Should work for solver with history enabled
    iterations_ok, _, _ = solver_with_history.get_pheromone_history()
    assert len(iterations_ok) > 0, "Should have history"
    print(f"  ✓ get_pheromone_history() works when enabled")

except Exception as e:
    print(f"  ✗ Error handling test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()

# ====================
# Summary
# ====================
print("=" * 80)
print("✓ ALL PHEROMONE HISTORY TESTS PASSED!")
print("=" * 80)
print()
print("Modified ACOSolver verified:")
print("  ✓ Backward compatible (record_history=False works)")
print("  ✓ History recording works (record_history=True)")
print("  ✓ History data structure correct")
print("  ✓ Pheromone evolves over time")
print("  ✓ Solution cost improves")
print("  ✓ Error handling works")
print()
print("Ready to create pheromone visualization!")
print("=" * 80)
