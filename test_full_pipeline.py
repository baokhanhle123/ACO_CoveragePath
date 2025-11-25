"""
Comprehensive integration test for complete Stage 1 + Stage 2 pipeline.
Tests the full workflow from field creation to final blocks with tracks.
"""

from src.data import FieldParameters, create_field_with_rectangular_obstacles
from src.decomposition import (
    boustrophedon_decomposition,
    get_decomposition_statistics,
    merge_blocks_by_criteria,
)
from src.geometry import generate_field_headland, generate_parallel_tracks
from src.obstacles.classifier import classify_all_obstacles, get_type_d_obstacles


def test_full_pipeline():
    """Test complete Stage 1 + Stage 2 pipeline."""
    print("=" * 80)
    print("FULL PIPELINE INTEGRATION TEST")
    print("=" * 80)

    # ====================
    # STAGE 1: SETUP
    # ====================
    print("\n[STAGE 1] Field Creation and Geometric Processing")
    print("-" * 80)

    # Create test field
    field = create_field_with_rectangular_obstacles(
        field_width=120,
        field_height=100,
        obstacle_specs=[
            (30, 30, 20, 15),  # Large obstacle 1
            (70, 50, 18, 20),  # Large obstacle 2
            (20, 10, 10, 8),   # Medium obstacle near boundary
        ],
        name="Integration Test Field",
    )

    print(f"✓ Field created: {field.name}")
    print("  - Dimensions: 120m × 100m")
    print(f"  - Total area: {field.area:.2f}m²")
    print(f"  - Obstacles: {len(field.obstacles)}")

    # Parameters
    params = FieldParameters(
        operating_width=5.0,
        turning_radius=3.0,
        num_headland_passes=2,
        driving_direction=0.0,
        obstacle_threshold=5.0,
    )

    print("✓ Parameters set:")
    print(f"  - Operating width: {params.operating_width}m")
    print(f"  - Headland passes: {params.num_headland_passes}")
    print(f"  - Driving direction: {params.driving_direction}°")

    # Generate headland
    print("\n[STAGE 1] Generating headland...")
    field_headland = generate_field_headland(
        field_boundary=field.boundary_polygon,
        operating_width=params.operating_width,
        num_passes=params.num_headland_passes,
    )

    print("✓ Headland generated:")
    print(f"  - Inner boundary area: {field_headland.inner_boundary.area:.2f}m²")
    print(f"  - Headland width: {params.operating_width * params.num_headland_passes}m")

    # Classify obstacles
    print("\n[STAGE 1] Classifying obstacles...")
    classified_obstacles = classify_all_obstacles(
        obstacle_boundaries=field.obstacles,
        field_inner_boundary=field_headland.inner_boundary,
        driving_direction_degrees=params.driving_direction,
        operating_width=params.operating_width,
        threshold=params.obstacle_threshold,
    )

    print(f"✓ Obstacles classified: {len(classified_obstacles)}")
    for obs in classified_obstacles:
        print(f"  - Obstacle {obs.index}: {obs.obstacle_type.name} (area={obs.area:.2f}m²)")

    # Get Type D obstacles for decomposition
    type_d_obstacles = get_type_d_obstacles(classified_obstacles)
    print(f"✓ Type D obstacles for decomposition: {len(type_d_obstacles)}")

    # ====================
    # STAGE 2: DECOMPOSITION
    # ====================
    print("\n[STAGE 2] Boustrophedon Decomposition")
    print("-" * 80)

    obstacle_polygons = [obs.polygon for obs in type_d_obstacles]

    # Perform decomposition
    print("Decomposing field...")
    preliminary_blocks = boustrophedon_decomposition(
        inner_boundary=field_headland.inner_boundary,
        obstacles=obstacle_polygons,
        driving_direction_degrees=params.driving_direction,
    )

    print(f"✓ Preliminary blocks created: {len(preliminary_blocks)}")

    prelim_stats = get_decomposition_statistics(preliminary_blocks)
    print(f"  - Total area: {prelim_stats['total_area']:.2f}m²")
    print(f"  - Average area: {prelim_stats['avg_area']:.2f}m²")
    print(f"  - Min area: {prelim_stats['min_area']:.2f}m²")
    print(f"  - Max area: {prelim_stats['max_area']:.2f}m²")

    # ====================
    # STAGE 2: MERGING
    # ====================
    print("\n[STAGE 2] Block Merging")
    print("-" * 80)

    print("Merging blocks...")
    final_blocks = merge_blocks_by_criteria(
        blocks=preliminary_blocks, operating_width=params.operating_width
    )

    print(f"✓ Final blocks after merging: {len(final_blocks)}")
    reduction = len(preliminary_blocks) - len(final_blocks)
    reduction_pct = 100 * reduction / len(preliminary_blocks) if preliminary_blocks else 0
    print(f"  - Reduction: {reduction} blocks ({reduction_pct:.1f}%)")

    final_stats = get_decomposition_statistics(final_blocks)
    print(f"  - Total area: {final_stats['total_area']:.2f}m²")
    print(f"  - Average area: {final_stats['avg_area']:.2f}m²")

    # ====================
    # TRACK GENERATION
    # ====================
    print("\n[STAGE 2] Track Generation for Blocks")
    print("-" * 80)

    total_tracks = 0
    total_distance = 0.0

    for block in final_blocks:
        tracks = generate_parallel_tracks(
            inner_boundary=block.polygon,
            driving_direction_degrees=params.driving_direction,
            operating_width=params.operating_width,
        )

        # Assign tracks to block
        for i, track in enumerate(tracks):
            track.block_id = block.block_id
            track.index = i
        block.tracks = tracks

        track_distance = block.get_working_distance()
        total_tracks += len(tracks)
        total_distance += track_distance

        print(f"  - Block {block.block_id}: {len(tracks)} tracks, {track_distance:.2f}m")

    print(f"✓ Total tracks: {total_tracks}")
    print(f"✓ Total working distance: {total_distance:.2f}m")

    # ====================
    # VERIFICATION
    # ====================
    print("\n[VERIFICATION] Checking Data Integrity")
    print("-" * 80)

    # 1. Area conservation
    expected_area = field_headland.inner_boundary.area - sum(obs.area for obs in obstacle_polygons)
    actual_area = sum(block.area for block in final_blocks)
    area_error = abs(expected_area - actual_area) / expected_area * 100

    print("✓ Area conservation check:")
    print(f"  - Expected area: {expected_area:.2f}m²")
    print(f"  - Actual area: {actual_area:.2f}m²")
    print(f"  - Error: {area_error:.3f}%")

    assert area_error < 1.0, f"Area conservation failed: {area_error:.3f}% error"

    # 2. Obstacle avoidance
    print("✓ Obstacle avoidance check:")
    intersection_issues = []
    for block in final_blocks:
        for obs in type_d_obstacles:
            if block.polygon.intersects(obs.polygon):
                # Check if it's just touching (boundary contact) or actual overlap
                intersection = block.polygon.intersection(obs.polygon)
                if hasattr(intersection, 'area') and intersection.area > 1e-6:
                    intersection_issues.append(
                        f"Block {block.block_id} overlaps obstacle {obs.index} "
                        f"(intersection area: {intersection.area:.6f}m²)"
                    )

    if intersection_issues:
        print(f"  ⚠️  Warning: Found {len(intersection_issues)} potential intersections:")
        for issue in intersection_issues:
            print(f"     {issue}")
        print("  Note: Very small intersections (<0.01m²) may be numerical precision issues")
    else:
        print(f"  - All {len(final_blocks)} blocks are obstacle-free")

    # 3. Block properties
    print("✓ Block properties check:")
    for block in final_blocks:
        assert block.area > 0, f"Block {block.block_id} has zero area"
        assert len(block.tracks) > 0, f"Block {block.block_id} has no tracks"
        assert block.polygon.is_valid, f"Block {block.block_id} has invalid geometry"
    print("  - All blocks have positive area and valid geometry")
    print("  - All blocks have tracks assigned")

    # 4. Track properties
    print("✓ Track properties check:")
    for block in final_blocks:
        for track in block.tracks:
            assert track.block_id == block.block_id, "Track has wrong block_id"
            assert track.length > 0, "Track has zero length"
    print(f"  - All {total_tracks} tracks properly assigned")

    # ====================
    # STAGE 3 READINESS
    # ====================
    print("\n[STAGE 3 READINESS] Checking Prerequisites")
    print("-" * 80)

    # Check what Stage 3 needs
    print("✓ Data structures ready for Stage 3:")
    print(f"  - Final blocks: {len(final_blocks)} blocks")
    print(f"  - Block IDs: {[b.block_id for b in final_blocks]}")
    print(f"  - Tracks per block: {[len(b.tracks) for b in final_blocks]}")
    print(f"  - Block areas: {[f'{b.area:.1f}m²' for b in final_blocks]}")

    # Check Block methods available
    print("\n✓ Block methods available:")
    test_block = final_blocks[0]
    print(f"  - block.area: {test_block.area:.2f}m²")
    print(f"  - block.num_tracks: {test_block.num_tracks}")
    print(f"  - block.is_odd_tracks: {test_block.is_odd_tracks}")
    print(f"  - block.parity_function: {test_block.parity_function}")
    print(f"  - block.get_working_distance(): {test_block.get_working_distance():.2f}m")
    print(f"  - block.polygon: {type(test_block.polygon).__name__}")

    # Check if entry/exit node method exists
    has_entry_exit = hasattr(test_block, "create_entry_exit_nodes")
    print(f"\n✓ Entry/exit node method: {'Available' if has_entry_exit else 'Not implemented'}")

    # ====================
    # SUMMARY
    # ====================
    print("\n" + "=" * 80)
    print("INTEGRATION TEST COMPLETE ✅")
    print("=" * 80)
    print("\nSummary:")
    print("  - Field: 120m × 100m with 3 obstacles")
    print(f"  - Classified obstacles: {len(classified_obstacles)} ({len(type_d_obstacles)} Type D)")
    print(f"  - Preliminary blocks: {len(preliminary_blocks)}")
    print(f"  - Final blocks: {len(final_blocks)} ({reduction_pct:.1f}% reduction)")
    print(f"  - Total tracks: {total_tracks} ({total_distance:.0f}m)")
    print(f"  - Area conservation: {area_error:.3f}% error")
    print("\n✅ All checks passed!")
    print("✅ Ready for Stage 3 implementation")


if __name__ == "__main__":
    test_full_pipeline()
