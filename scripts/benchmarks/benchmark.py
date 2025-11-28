"""
Benchmark Script for Validating Implementation Against Zhou et al. 2014

This script implements the three test cases from Table 2 of:
"Agricultural operations planning in fields with multiple obstacle areas"
Zhou et al., Computers and Electronics in Agriculture 109 (2014) 12-22

Test Cases:
- Field (a): 20.21 ha, 3 obstacles
- Field (b): 56.54 ha, 4 obstacles
- Field (c): 4.81 ha, 5 obstacles

The script compares our implementation results with the paper's reported values.
"""

import time
from typing import Dict, List, Tuple

import matplotlib.pyplot as plt
import numpy as np

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


def create_field_a():
    """
    Create Field (a) from Table 2.

    Parameters from paper:
    - Area: 20.21 ha = 202,100 m²
    - Obstacles: 3
    - Driving angle: 105°
    - Operating width: 9 m
    - Turning radius: 6 m
    - Headland passes: 1

    Creating a field of approximately 500m x 404m ≈ 202,000 m²
    Figure 15(a) shows ~10 blocks, so create larger obstacles
    """
    # Approximate dimensions for 20.21 ha
    field_width = 500
    field_height = 404

    # Create 3 larger rectangular obstacles to get ~10 blocks like in paper
    obstacle_specs = [
        (100, 100, 120, 90),   # Obstacle 1 (larger)
        (300, 150, 100, 80),   # Obstacle 2 (larger)
        (170, 240, 110, 85),   # Obstacle 3 (larger)
    ]

    field = create_field_with_rectangular_obstacles(
        field_width=field_width,
        field_height=field_height,
        obstacle_specs=obstacle_specs,
        name="Field (a) - 20.21 ha, 3 obstacles",
    )

    params = FieldParameters(
        operating_width=9.0,
        turning_radius=6.0,
        num_headland_passes=1,
        driving_direction=105.0,
        obstacle_threshold=9.0,
    )

    return field, params


def create_field_b():
    """
    Create Field (b) from Table 2.

    Parameters from paper:
    - Area: 56.54 ha = 565,400 m²
    - Obstacles: 4
    - Driving angle: 108.2°
    - Operating width: 12 m
    - Turning radius: 6 m
    - Headland passes: 1

    Creating a field of approximately 800m x 707m ≈ 565,600 m²
    Figure 15(b) shows ~13 blocks, so create larger obstacles
    """
    field_width = 800
    field_height = 707

    # Create 4 larger rectangular obstacles to get ~13 blocks like in paper
    obstacle_specs = [
        (150, 150, 160, 120),   # Obstacle 1 (larger)
        (400, 180, 140, 110),   # Obstacle 2 (larger)
        (280, 420, 150, 100),   # Obstacle 3 (larger)
        (550, 440, 130, 105),   # Obstacle 4 (larger)
    ]

    field = create_field_with_rectangular_obstacles(
        field_width=field_width,
        field_height=field_height,
        obstacle_specs=obstacle_specs,
        name="Field (b) - 56.54 ha, 4 obstacles",
    )

    params = FieldParameters(
        operating_width=12.0,
        turning_radius=6.0,
        num_headland_passes=1,
        driving_direction=108.2,
        obstacle_threshold=12.0,
    )

    return field, params


def create_field_c():
    """
    Create Field (c) from Table 2.

    Parameters from paper:
    - Area: 4.81 ha = 48,100 m²
    - Obstacles: 5
    - Driving angle: 31.8°
    - Operating width: 15 m
    - Turning radius: 6 m
    - Headland passes: 1

    Creating a field of approximately 280m x 172m ≈ 48,160 m²
    Figure 15(c) shows ~16 blocks, so create moderately sized obstacles
    """
    field_width = 280
    field_height = 172

    # Create 5 rectangular obstacles to get ~16 blocks like in paper
    obstacle_specs = [
        (40, 40, 45, 35),      # Obstacle 1
        (110, 38, 42, 32),     # Obstacle 2
        (180, 50, 38, 34),     # Obstacle 3
        (70, 105, 48, 28),     # Obstacle 4
        (155, 110, 45, 30),    # Obstacle 5
    ]

    field = create_field_with_rectangular_obstacles(
        field_width=field_width,
        field_height=field_height,
        obstacle_specs=obstacle_specs,
        name="Field (c) - 4.81 ha, 5 obstacles",
    )

    params = FieldParameters(
        operating_width=15.0,
        turning_radius=6.0,
        num_headland_passes=1,
        driving_direction=31.8,
        obstacle_threshold=15.0,
    )

    return field, params


def run_pipeline(field, params, num_iterations: int, verbose: bool = False) -> Tuple[Dict, float, int]:
    """
    Run complete pipeline from field to optimized path.

    Returns:
        - Statistics dictionary
        - Processing time (seconds)
        - Number of blocks
    """
    start_time = time.time()

    # Stage 1: Geometric representation
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

    # Stage 2: Decomposition
    preliminary_blocks = boustrophedon_decomposition(
        inner_boundary=field_headland.inner_boundary,
        obstacles=obstacle_polygons,
        driving_direction_degrees=params.driving_direction,
    )

    final_blocks = merge_blocks_by_criteria(
        blocks=preliminary_blocks, operating_width=params.operating_width
    )

    # Generate tracks
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

    # Create entry/exit nodes
    all_nodes = []
    node_index = 0
    for block in final_blocks:
        nodes = block.create_entry_exit_nodes(start_index=node_index)
        all_nodes.extend(nodes)
        node_index += 4

    # Build cost matrix
    cost_matrix = build_cost_matrix(blocks=final_blocks, nodes=all_nodes)

    # Stage 3: ACO optimization with paper parameters
    aco_params = ACOParameters(
        alpha=1.0,
        beta=5.0,      # Paper uses β=5
        rho=0.5,       # Paper uses ρ=0.5
        q=100.0,
        num_ants=len(all_nodes),  # Paper uses m=n (number of nodes)
        num_iterations=num_iterations,
        elitist_weight=2.0,
    )

    solver = ACOSolver(
        blocks=final_blocks,
        nodes=all_nodes,
        cost_matrix=cost_matrix,
        params=aco_params,
    )

    best_solution = solver.solve(verbose=verbose)

    # Check if solution found
    if best_solution is None or not best_solution.is_valid(len(final_blocks)):
        # No valid solution found - return None to indicate failure
        return None, None, None

    # Generate path
    path_plan = generate_path_from_solution(best_solution, final_blocks, all_nodes)
    stats = get_path_statistics(path_plan)

    # Add block connection distance (transition distance)
    stats['block_connection_distance'] = stats['transition_distance']

    end_time = time.time()
    processing_time = end_time - start_time

    return stats, processing_time, len(final_blocks)


def run_benchmark():
    """Run complete benchmark against paper results."""
    print("=" * 100)
    print("BENCHMARK: Validating Implementation Against Zhou et al. 2014")
    print("=" * 100)
    print()

    # Paper results from Table 2
    paper_results = {
        'a': {
            'area_ha': 20.21,
            'num_obstacles': 3,
            'results': {
                20: {'connection': 386.5, 'time': 3.7},
                100: {'connection': 371.5, 'time': 27.5},
                200: {'connection': 371.5, 'time': 55.1},
                400: {'connection': 371.5, 'time': 109.3},
            },
            'working_distance': 21823,
            'non_working_distance': 2973.9,
        },
        'b': {
            'area_ha': 56.54,
            'num_obstacles': 4,
            'results': {
                40: {'connection': 788.4, 'time': 22.3},
                100: {'connection': 765.1, 'time': 69.4},
                200: {'connection': 765.1, 'time': 118.3},
                400: {'connection': 765.1, 'time': 233.7},
            },
            'working_distance': 46020,
            'non_working_distance': 1790.7,
        },
        'c': {
            'area_ha': 4.81,
            'num_obstacles': 5,
            'results': {
                50: {'connection': 864.6, 'time': 57.1},
                100: {'connection': 856.4, 'time': 123.3},
                200: {'connection': 856.4, 'time': 235.5},
                400: {'connection': 856.4, 'time': 465.8},
            },
            'working_distance': 31680,
            'non_working_distance': 1573.2,
        },
    }

    # Create test fields
    fields = {
        'a': create_field_a(),
        'b': create_field_b(),
        'c': create_field_c(),
    }

    # Run benchmarks
    all_results = {}

    for field_id in ['a', 'b', 'c']:
        print(f"\n{'=' * 100}")
        print(f"FIELD ({field_id}): {paper_results[field_id]['area_ha']} ha, "
              f"{paper_results[field_id]['num_obstacles']} obstacles")
        print(f"{'=' * 100}")

        field, params = fields[field_id]
        field_area_m2 = field.boundary_polygon.area
        print(f"Created field area: {field_area_m2/10000:.2f} ha ({field_area_m2:.0f} m²)")
        print(f"Parameters: w={params.operating_width}m, θ={params.driving_direction}°, "
              f"c={params.turning_radius}m, h={params.num_headland_passes}")
        print()

        results = {}
        iteration_counts = sorted(paper_results[field_id]['results'].keys())

        for num_iter in iteration_counts:
            print(f"  Running with {num_iter} iterations...")

            # Run multiple times and take average
            target_runs = 3
            max_attempts = 10
            all_stats = []
            all_times = []
            num_blocks = None

            attempts = 0
            while len(all_stats) < target_runs and attempts < max_attempts:
                attempts += 1
                stats, proc_time, n_blocks = run_pipeline(field, params, num_iter, verbose=False)
                if stats is None:
                    print(f"      Attempt {attempts}: Failed to find valid solution - retrying...")
                    continue
                all_stats.append(stats)
                all_times.append(proc_time)
                num_blocks = n_blocks

            # Skip if no successful runs
            if not all_stats:
                print(f"    ✗ All attempts failed for {num_iter} iterations - skipping")
                continue

            if len(all_stats) < target_runs:
                print(f"    ⚠ Only {len(all_stats)}/{target_runs} successful runs")

            # Average results
            avg_connection = np.mean([s['block_connection_distance'] for s in all_stats])
            avg_time = np.mean(all_times)
            avg_working = np.mean([s['working_distance'] for s in all_stats])
            avg_non_working = np.mean([s['transition_distance'] for s in all_stats])

            # Get paper results
            paper_connection = paper_results[field_id]['results'][num_iter]['connection']
            paper_time = paper_results[field_id]['results'][num_iter]['time']

            # Calculate differences
            connection_diff = ((avg_connection - paper_connection) / paper_connection) * 100
            time_diff = ((avg_time - paper_time) / paper_time) * 100

            results[num_iter] = {
                'our_connection': avg_connection,
                'paper_connection': paper_connection,
                'connection_diff_%': connection_diff,
                'our_time': avg_time,
                'paper_time': paper_time,
                'time_diff_%': time_diff,
                'num_blocks': num_blocks,
            }

            print(f"    Blocks: {num_blocks}")
            print(f"    Connection distance: {avg_connection:.1f} m (Paper: {paper_connection:.1f} m, "
                  f"Diff: {connection_diff:+.1f}%)")
            print(f"    Processing time: {avg_time:.1f} s (Paper: {paper_time:.1f} s, "
                  f"Diff: {time_diff:+.1f}%)")
            print()

        all_results[field_id] = results

    # Print summary comparison
    print("\n" + "=" * 100)
    print("SUMMARY COMPARISON")
    print("=" * 100)
    print()

    for field_id in ['a', 'b', 'c']:
        print(f"\nField ({field_id}):")
        print(f"  {'Iterations':<12} {'Our Conn.':<15} {'Paper Conn.':<15} {'Diff %':<12} "
              f"{'Our Time':<12} {'Paper Time':<12} {'Diff %':<12}")
        print(f"  {'-' * 95}")

        for num_iter, result in all_results[field_id].items():
            print(f"  {num_iter:<12} "
                  f"{result['our_connection']:<15.1f} "
                  f"{result['paper_connection']:<15.1f} "
                  f"{result['connection_diff_%']:<+12.1f} "
                  f"{result['our_time']:<12.1f} "
                  f"{result['paper_time']:<12.1f} "
                  f"{result['time_diff_%']:<+12.1f}")

    print("\n" + "=" * 100)
    print("NOTES:")
    print("  - Connection distance = block connection distance (transitions between blocks)")
    print("  - Results are averaged over 3 runs")
    print("  - Synthetic fields approximate the paper's area and obstacle count")
    print("  - Exact field geometries not provided in paper, so results may vary")
    print("=" * 100)

    return all_results


if __name__ == "__main__":
    results = run_benchmark()
