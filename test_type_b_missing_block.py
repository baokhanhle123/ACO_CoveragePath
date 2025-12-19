"""
Test script to reproduce the missing block above Type B obstacle bug.

Type B obstacle at (20, 10) with dimensions 40×20, covering X=[20, 60], Y=[10, 30]
Expected: Blocks on LEFT, RIGHT, and ABOVE the Type B obstacle
Actual: Missing block above Type B obstacle (from Y=30 to Y=65, X=[20, 60])
"""
import json
import os

from src.data import FieldParameters, create_field_with_rectangular_obstacles
from src.stage1 import run_stage1_pipeline

# Create field with Type B obstacle
field = create_field_with_rectangular_obstacles(
    field_width=220,
    field_height=220,
    obstacle_specs=[
        (20, 10, 40, 20),  # Type B obstacle: X=[20, 60], Y=[10, 30]
    ],
    name="Type B Test Field",
)

params = FieldParameters(
    operating_width=5.0,
    turning_radius=3.0,
    num_headland_passes=2,
    driving_direction=0.0,
    obstacle_threshold=5.0,
)

# Run Stage 1
stage1 = run_stage1_pipeline(field, params)

print(f"Type B obstacles: {len(stage1.type_b_obstacles)}")
print(f"Type D obstacles: {len(stage1.type_d_obstacles)}")
print(f"Inner boundary has {len(stage1.field_headland.inner_boundary.interiors)} holes")

# Run decomposition
from src.decomposition import boustrophedon_decomposition

blocks = boustrophedon_decomposition(
    inner_boundary=stage1.field_headland.inner_boundary,
    obstacles=[obs.polygon for obs in stage1.type_d_obstacles],
    driving_direction_degrees=0.0,
    type_b_obstacles=[obs.polygon for obs in stage1.type_b_obstacles],
)

print(f"\nCreated {len(blocks)} blocks")
print("\nBlock positions (bounding boxes):")
for block in blocks:
    bounds = block.polygon.bounds  # (minx, miny, maxx, maxy)
    print(f"  B{block.block_id}: x=[{bounds[0]:.1f}, {bounds[2]:.1f}], "
          f"y=[{bounds[1]:.1f}, {bounds[3]:.1f}], area={block.area:.2f}m²")

# Check for missing block above Type B obstacle (Y=[30, 65], X=[20, 60])
# The region above Type B obstacle should be covered by a block that:
# - Starts at Y=30 (top of Type B obstacle)
# - Covers X=[20, 60] (the width of the Type B obstacle)
missing_region_found = False
for block in blocks:
    bounds = block.polygon.bounds
    # Check if block covers the region above Type B obstacle
    # Block must start at Y=30 and cover X=[20, 60]
    if (bounds[1] <= 30.1 and bounds[3] >= 30 and  # Starts at or near Y=30
        bounds[0] <= 20 and bounds[2] >= 60):       # Covers X=[20, 60]
        print(f"\n✓ Found block covering region above Type B obstacle: B{block.block_id}")
        print(f"  Block bounds: x=[{bounds[0]:.1f}, {bounds[2]:.1f}], y=[{bounds[1]:.1f}, {bounds[3]:.1f}]")
        missing_region_found = True
        break

if not missing_region_found:
    print("\n✗ MISSING BLOCK: No block found covering region Y=[30, 65], X=[20, 60]")
    print("  Expected: A block starting at Y=30 that covers X=[20, 60]")

