"""Test script to understand the geometry of B4, B5, and B7."""

from test_merge_fix import *
from shapely.geometry import LineString

# Get blocks
b4 = [b for b in preliminary_blocks if b.block_id == 4][0]
b5 = [b for b in preliminary_blocks if b.block_id == 5][0]
b7 = [b for b in preliminary_blocks if b.block_id == 7][0]

# Get intersections
boundary4 = b4.polygon.exterior
boundary5 = b5.polygon.exterior
boundary7 = b7.polygon.exterior

intersection_4_7 = boundary4.intersection(boundary7)
intersection_5_7 = boundary5.intersection(boundary7)

print('B4-B7 intersection length:', intersection_4_7.length if hasattr(intersection_4_7, 'length') else 'N/A')
print('B5-B7 intersection length:', intersection_5_7.length if hasattr(intersection_5_7, 'length') else 'N/A')

# Get B7's left edge (the edge that should be shared by both B4 and B5)
# B7's boundary coordinates
b7_coords = list(boundary7.coords)
print(f'\nB7 has {len(b7_coords)} boundary points')

# Check if B4-B7 and B5-B7 intersections are on the same edge of B7
# They should both be on B7's left edge
if hasattr(intersection_4_7, 'coords') and hasattr(intersection_5_7, 'coords'):
    coords_4_7 = list(intersection_4_7.coords)
    coords_5_7 = list(intersection_5_7.coords)
    
    print(f'\nB4-B7 intersection: {coords_4_7[0]} to {coords_4_7[-1]}')
    print(f'B5-B7 intersection: {coords_5_7[0]} to {coords_5_7[-1]}')
    
    # Check if they're adjacent (share an endpoint)
    if coords_4_7 and coords_5_7:
        if coords_4_7[-1] == coords_5_7[0] or coords_4_7[0] == coords_5_7[-1]:
            print('\n✓ These segments are ADJACENT on B7\'s boundary!')
            print('  This means B7\'s left edge is shared by both B4 and B5')
            print('  So B5 and B7 should NOT have an exclusive edge')
        else:
            print('\nThese segments are separate on B7\'s boundary')

