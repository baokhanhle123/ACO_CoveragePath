"""
Test script to verify the merge fix works correctly.
"""

from src.data import FieldParameters, create_field_with_rectangular_obstacles
from src.decomposition import (
    boustrophedon_decomposition,
    build_block_adjacency_graph,
    merge_blocks_by_criteria,
)
from src.geometry import generate_field_headland
from src.obstacles.classifier import classify_all_obstacles, get_type_d_obstacles

# Create the same field as in the demo
field = create_field_with_rectangular_obstacles(
    field_width=220,
    field_height=220,
    obstacle_specs=[
        (80, 65, 60, 20),  # Obstacle 1
        (40, 120, 70, 20),  # Obstacle 2
        (20, 10, 40, 20),  # Obstacle 3 (near boundary)
    ],
    name="Demo Field",
)

params = FieldParameters(
    operating_width=5.0,
    turning_radius=3.0,
    num_headland_passes=2,
    driving_direction=0.0,
    obstacle_threshold=5.0,
)

# Run Stage 1
from src.stage1 import run_stage1_pipeline
stage1 = run_stage1_pipeline(field, params)

field_headland = stage1.field_headland
type_d_obstacles = stage1.type_d_obstacles
obstacle_polygons = [obs.polygon for obs in type_d_obstacles]

# Run Stage 2 decomposition
preliminary_blocks = boustrophedon_decomposition(
    inner_boundary=field_headland.inner_boundary,
    obstacles=obstacle_polygons,
    driving_direction_degrees=params.driving_direction,
)

print(f"Preliminary blocks: {len(preliminary_blocks)}")
print(f"Block IDs: {[b.block_id for b in preliminary_blocks]}")

# Check adjacency
prelim_graph = build_block_adjacency_graph(preliminary_blocks)
print("\nPreliminary block adjacency:")
for block_id in sorted(prelim_graph.adjacency.keys()):
    neighbors = prelim_graph.adjacency[block_id]
    print(f"  B{block_id} → adjacent to: {[f'B{n}' for n in neighbors]}")

# Check if B2 and B4 are adjacent
b2_adjacent = prelim_graph.get_adjacent_blocks(2)
b4_adjacent = prelim_graph.get_adjacent_blocks(4)
print(f"\nB2 adjacent to: {b2_adjacent}")
print(f"B4 adjacent to: {b4_adjacent}")
print(f"B2 and B4 are adjacent: {4 in b2_adjacent and 2 in b4_adjacent}")

# Merge blocks
print("\nMerging blocks...")
final_blocks = merge_blocks_by_criteria(
    blocks=preliminary_blocks, operating_width=params.operating_width
)

print(f"\nFinal blocks: {len(final_blocks)}")
print(f"Block IDs: {[b.block_id for b in final_blocks]}")

# Check if B2 and B4 were merged
# After merging, we should have fewer blocks
if len(final_blocks) < len(preliminary_blocks):
    print(f"\n✓ SUCCESS: Blocks were merged ({len(preliminary_blocks)} → {len(final_blocks)})")
    if len(final_blocks) == 7:
        print("✓ SUCCESS: Final count is 7 blocks as expected")
    else:
        print(f"⚠ WARNING: Expected 7 blocks, got {len(final_blocks)}")
else:
    print(f"\n❌ ERROR: No blocks were merged (still {len(final_blocks)} blocks)")

