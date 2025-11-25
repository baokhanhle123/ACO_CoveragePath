"""
Integration test for Stage 3: ACO-based path optimization.

Tests the complete pipeline from field creation through ACO optimization.
"""

from src.data import FieldParameters, create_field_with_rectangular_obstacles
from src.decomposition import boustrophedon_decomposition, merge_blocks_by_criteria
from src.geometry import generate_field_headland, generate_parallel_tracks
from src.obstacles.classifier import classify_all_obstacles, get_type_d_obstacles
from src.optimization import ACOParameters, ACOSolver, build_cost_matrix


def test_full_stage3_pipeline():
    """Test complete Stage 1 + 2 + 3 pipeline with ACO optimization."""
    print("\n" + "=" * 80)
    print("STAGE 3 INTEGRATION TEST: Full Pipeline")
    print("=" * 80)

    # ====================
    # STAGE 1 & 2: Setup
    # ====================
    print("\n[STAGE 1+2] Field Setup and Decomposition")
    print("-" * 80)

    # Create test field (smaller for faster testing)
    field = create_field_with_rectangular_obstacles(
        field_width=60,
        field_height=50,
        obstacle_specs=[
            (15, 15, 10, 8),  # Obstacle 1
            (35, 25, 10, 10),  # Obstacle 2
        ],
        name="Stage 3 Test Field",
    )

    params = FieldParameters(
        operating_width=5.0,
        turning_radius=3.0,
        num_headland_passes=2,
        driving_direction=0.0,
        obstacle_threshold=5.0,
    )

    # Generate headland
    field_headland = generate_field_headland(
        field_boundary=field.boundary_polygon,
        operating_width=params.operating_width,
        num_passes=params.num_headland_passes,
    )

    # Classify obstacles
    classified_obstacles = classify_all_obstacles(
        obstacle_boundaries=field.obstacles,
        field_inner_boundary=field_headland.inner_boundary,
        driving_direction_degrees=params.driving_direction,
        operating_width=params.operating_width,
        threshold=params.obstacle_threshold,
    )

    type_d_obstacles = get_type_d_obstacles(classified_obstacles)
    obstacle_polygons = [obs.polygon for obs in type_d_obstacles]

    print(f" Field created: {field.name}")
    print(f" Type D obstacles: {len(type_d_obstacles)}")

    # Boustrophedon decomposition
    preliminary_blocks = boustrophedon_decomposition(
        inner_boundary=field_headland.inner_boundary,
        obstacles=obstacle_polygons,
        driving_direction_degrees=params.driving_direction,
    )

    print(f" Preliminary blocks: {len(preliminary_blocks)}")

    # Block merging
    final_blocks = merge_blocks_by_criteria(
        blocks=preliminary_blocks, operating_width=params.operating_width
    )

    print(f" Final blocks after merging: {len(final_blocks)}")

    # Generate tracks for each block
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

    print(f" Tracks generated for all blocks")

    # ====================
    # STAGE 3: Entry/Exit Nodes
    # ====================
    print("\n[STAGE 3] Entry/Exit Node Generation")
    print("-" * 80)

    # Create entry/exit nodes for all blocks
    all_nodes = []
    node_index = 0

    for block in final_blocks:
        nodes = block.create_entry_exit_nodes(start_index=node_index)
        all_nodes.extend(nodes)
        node_index += 4

    print(f" Created {len(all_nodes)} nodes (4 per block)")

    # ====================
    # STAGE 3: Cost Matrix
    # ====================
    print("\n[STAGE 3] Cost Matrix Construction")
    print("-" * 80)

    cost_matrix = build_cost_matrix(blocks=final_blocks, nodes=all_nodes, turning_penalty=0.0)

    print(f" Cost matrix built: {cost_matrix.shape}")
    print(f"  - Matrix size: {cost_matrix.shape[0]} x {cost_matrix.shape[1]}")

    # Verify cost matrix properties
    assert cost_matrix.shape == (len(all_nodes), len(all_nodes))
    assert cost_matrix[0][0] == 0.0  # Diagonal should be zero

    print(f" Cost matrix validated")

    # ====================
    # STAGE 3: ACO Optimization
    # ====================
    print("\n[STAGE 3] ACO Optimization")
    print("-" * 80)

    # Create ACO solver with reduced iterations for testing
    aco_params = ACOParameters(
        alpha=1.0,
        beta=2.0,
        rho=0.1,
        q=100.0,
        num_ants=10,  # Reduced for faster testing
        num_iterations=20,  # Reduced for faster testing
        elitist_weight=2.0,
    )

    solver = ACOSolver(
        blocks=final_blocks, nodes=all_nodes, cost_matrix=cost_matrix, params=aco_params
    )

    print(f" ACO Solver initialized")
    print(f"  - Blocks: {len(final_blocks)}")
    print(f"  - Nodes: {len(all_nodes)}")
    print(f"  - Ants: {aco_params.num_ants}")
    print(f"  - Iterations: {aco_params.num_iterations}")

    # Run ACO
    print("\n[STAGE 3] Running ACO...")
    best_solution = solver.solve(verbose=True)

    # ====================
    # VERIFICATION
    # ====================
    print("\n[VERIFICATION] Solution Quality")
    print("-" * 80)

    if best_solution is not None:
        print(f" Best solution found!")
        print(f"  - Path length: {len(best_solution.path)} nodes")
        print(f"  - Total cost: {best_solution.cost:.2f}")
        print(f"  - Block sequence: {best_solution.block_sequence}")
        print(f"  - Blocks visited: {len(set(best_solution.block_sequence))}")

        # Verify solution validity
        assert best_solution.is_valid(len(final_blocks)), "Solution is not valid!"
        assert len(best_solution.path) > 0, "Solution path is empty!"
        assert best_solution.cost > 0, "Solution cost must be positive!"

        print(f" Solution is valid")

        # Check convergence
        best_costs, avg_costs = solver.get_convergence_data()
        if len(best_costs) > 0:
            initial_best = best_costs[0]
            final_best = best_costs[-1]
            improvement = ((initial_best - final_best) / initial_best) * 100

            print(f"\n[CONVERGENCE] ACO Performance")
            print(f"  - Initial best: {initial_best:.2f}")
            print(f"  - Final best: {final_best:.2f}")
            print(f"  - Improvement: {improvement:.1f}%")

            assert final_best <= initial_best, "Best solution should not get worse!"
    else:
        print(" No valid solution found!")
        assert False, "ACO failed to find a valid solution!"

    # ====================
    # SUCCESS
    # ====================
    print("\n" + "=" * 80)
    print("STAGE 3 INTEGRATION TEST PASSED ")
    print("=" * 80)
    print("\n All stages working correctly:")
    print(f"  - Stage 1: Field representation ")
    print(f"  - Stage 2: Boustrophedon decomposition ")
    print(f"  - Stage 3: ACO optimization ")


if __name__ == "__main__":
    test_full_stage3_pipeline()
