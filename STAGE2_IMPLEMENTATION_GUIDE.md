# Stage 2 Implementation Guide
**Boustrophedon Decomposition & Block Merging**

---

## Overview

Stage 2 implements the boustrophedon cellular decomposition algorithm to partition the field body into obstacle-free blocks. This is a critical step that enables efficient coverage path planning.

**Status:** 🚧 **READY FOR IMPLEMENTATION** - Starter files created, tests prepared

**Reference:** Zhou et al. 2014, Section 2.3

---

## Implementation Checklist

### Phase 1: Boustrophedon Decomposition (Core Algorithm)

**File:** `src/decomposition/boustrophedon.py`

- [ ] **Geometry Rotation** (`rotate_geometry`)
  - Implement rotation using shapely affinity or manual transformation
  - Test with simple rectangles and polygons
  - Verify reverse rotation returns original geometry

- [ ] **Critical Point Detection** (`find_critical_points`)
  - Rotate field and obstacles to align sweep with Y-axis
  - Extract all obstacle vertex x-coordinates
  - Add field boundary intersection points
  - Sort and return unique critical x-coordinates
  - Test: Simple field → 2 critical points (boundaries)
  - Test: Field + 1 obstacle → 4 critical points

- [ ] **Sweep Line Creation** (`create_sweep_line`)
  - Already has basic structure
  - Add validation for y_min < y_max
  - Test creation and intersection

- [ ] **Slice Polygon Computation** (`compute_slice_polygons`)
  - Create rectangular slice between two x-coordinates
  - Intersect with field inner boundary
  - Subtract all obstacles in this slice
  - Handle multi-polygon results (when obstacles split the slice)
  - Return list of obstacle-free cells
  - Test: Empty slice → 1 polygon
  - Test: Slice with obstacle → 2+ polygons

- [ ] **Main Decomposition** (`boustrophedon_decomposition`)
  - Implement full pipeline:
    1. Validate inputs
    2. Rotate geometry to align with sweep direction
    3. Get bounding box for sweep range
    4. Find critical points
    5. For each consecutive pair of critical points:
       - Create slice
       - Compute obstacle-free polygons
       - Create Block objects
    6. Rotate blocks back to original orientation
    7. Assign preliminary block IDs
  - Test with simple cases first (no obstacles)
  - Test with increasing complexity

### Phase 2: Block Adjacency Graph

**File:** `src/decomposition/block_merger.py`

- [ ] **Adjacency Check** (`check_blocks_adjacent`)
  - Get intersection of block boundaries
  - Check if intersection is a LineString (not just Point)
  - Measure intersection length
  - Return True if length > threshold
  - Test: Adjacent blocks → True
  - Test: Touching at corner → False
  - Test: Separated blocks → False

- [ ] **Build Adjacency Graph** (`build_block_adjacency_graph`)
  - Create BlockGraph with all blocks
  - For each pair of blocks:
    - Check adjacency
    - Add edge if adjacent
  - Test: 3 sequential blocks → correct edges
  - Test: Complex arrangements

### Phase 3: Block Merging

**File:** `src/decomposition/block_merger.py`

- [ ] **Merge Cost Calculation** (`calculate_merge_cost`)
  - Define cost metrics:
    - Track count uniformity
    - Convexity measure
    - Aspect ratio
    - Perimeter simplicity
  - Return normalized cost (0-1 or similar scale)
  - Test: Good merges → low cost
  - Test: Bad merges → high cost

- [ ] **Two-Block Merge** (`merge_two_blocks`)
  - Union block polygons
  - Simplify boundary if needed
  - Merge track lists (sort by position)
  - Create new Block with merged data
  - Test: Simple adjacent blocks
  - Test: Complex shapes

- [ ] **Greedy Merging Algorithm** (`greedy_block_merging`)
  - Implement iterative merging:
    1. Find smallest block below threshold
    2. Get adjacent blocks
    3. Calculate merge cost for each
    4. Merge with best candidate
    5. Update graph
    6. Repeat until convergence
  - Test: Narrow blocks get merged
  - Test: Good blocks stay separate
  - Test: Convergence guaranteed

### Phase 4: Integration & Testing

- [ ] **Unit Tests** (`tests/test_decomposition.py`)
  - Uncomment all @pytest.mark.skip decorators
  - Run each test individually
  - Fix implementation until all pass
  - Add edge case tests as needed

- [ ] **Integration Test**
  - Run full Stage 1 + Stage 2 pipeline
  - Verify area conservation
  - Verify obstacle avoidance
  - Check block quality metrics

- [ ] **Demo Visualization** (`demo_stage2.py`)
  - Run demo script
  - Verify visualization quality
  - Check statistics output
  - Test with various field configurations

---

## Algorithm Details

### Boustrophedon Decomposition

**Concept:** Sweep a vertical line perpendicular to driving direction. At "critical points" where connectivity changes, create cell boundaries.

**Steps:**
1. **Align geometry:** Rotate so sweep direction is vertical (Y-axis)
2. **Find critical points:** x-coordinates where topology changes
   - Obstacle vertices
   - Field boundary intersections
3. **Sweep:** For each interval [x_i, x_{i+1}]:
   - Create vertical slice
   - Subtract obstacles
   - Result: 1+ obstacle-free cells
4. **Create blocks:** Each cell becomes a preliminary Block
5. **Rotate back:** Return to original orientation

**Example:**
```
Field with 1 obstacle:

|          [Obs]          |
|                         |
|                         |

Critical points: x=0 (left), x=30 (obs left), x=50 (obs right), x=100 (right)

Slices:
- [0, 30]: Full height rectangle (Block 1)
- [30, 50]: Split into top + bottom (Blocks 2, 3)
- [50, 100]: Full height rectangle (Block 4)

Result: 4 preliminary blocks
```

### Block Merging

**Concept:** Preliminary blocks may be very narrow. Merge adjacent blocks to:
- Reduce total number
- Improve coverage efficiency
- Maintain convexity

**Greedy Strategy:**
1. Identify "bad" blocks (too small/narrow)
2. For each bad block:
   - Find adjacent blocks
   - Calculate merge cost with each
   - Merge with lowest cost neighbor
3. Update adjacency graph
4. Repeat until all blocks meet criteria

**Merge Cost Factors:**
- **Convexity:** Prefer merges that maintain convex shapes
- **Uniformity:** Similar track counts → easier optimization
- **Simplicity:** Lower perimeter → simpler shapes

---

## Testing Strategy

### Level 1: Unit Tests (Isolated Functions)
- Test each function with minimal inputs
- Verify edge cases (empty, single element)
- Check mathematical correctness

### Level 2: Component Tests
- Test decomposition on simple fields
- Test merging on simple block sets
- Verify geometric properties

### Level 3: Integration Tests
- Full Stage 1 + Stage 2 pipeline
- Various field configurations
- Verify end-to-end correctness

### Level 4: Visual Verification
- Run demo scripts
- Inspect plots manually
- Check for geometric errors

---

## Implementation Order (Recommended)

1. **Start with rotation:** Get `rotate_geometry()` working first
2. **Critical points:** Implement detection and test thoroughly
3. **Slice computation:** This is the core - spend time here
4. **Main decomposition:** Combine pieces
5. **Adjacency:** Should be straightforward with Shapely
6. **Simple merging:** Get two-block merge working
7. **Greedy algorithm:** Build on top of simple merge
8. **Testing:** Uncomment tests one by one
9. **Demo:** Visualize results

---

## Common Pitfalls

### 1. Coordinate System Confusion
- **Problem:** Mixing rotated and original coordinates
- **Solution:** Always track which coordinate system you're in
- **Tip:** Use descriptive variable names (`rotated_polygon`, `original_boundary`)

### 2. Degenerate Geometries
- **Problem:** Slicing creates empty or invalid polygons
- **Solution:** Check `polygon.is_valid` and `polygon.is_empty` after operations
- **Tip:** Use `buffer(0)` to fix minor invalid geometries

### 3. Floating Point Precision
- **Problem:** Critical points at nearly same x-coordinate
- **Solution:** Use `np.unique()` with tolerance, or round to reasonable precision
- **Tip:** Consider using `np.isclose()` for comparisons

### 4. Obstacle Intersection
- **Problem:** Obstacles partially in slice
- **Solution:** Use `.intersection()` to get only the part in the slice
- **Tip:** Handle MultiPolygon results from difference operations

### 5. Block Ordering
- **Problem:** Blocks in random order after decomposition
- **Solution:** Sort by centroid position or sweep order
- **Tip:** Consistent ordering helps debugging

---

## Validation Metrics

After implementation, verify these properties:

### Geometric Correctness
- [ ] Total block area = field area - obstacle area (±1%)
- [ ] No blocks overlap
- [ ] All blocks are obstacle-free
- [ ] Blocks cover entire field body

### Quality Metrics
- [ ] Block count reasonable (not too many tiny blocks)
- [ ] Most blocks are convex or near-convex
- [ ] Block sizes relatively uniform after merging

### Performance
- [ ] Decomposition completes in < 1 second for typical field
- [ ] Merging completes in < 1 second
- [ ] No memory issues with complex fields

---

## Debugging Tips

### Visualization is Key
Add debug plots at each step:
```python
import matplotlib.pyplot as plt

def debug_plot(geometry, title):
    plt.figure()
    # Plot geometry
    plt.title(title)
    plt.show()
```

### Print Intermediate Results
```python
print(f"Critical points: {critical_points}")
print(f"Slice [{x1}, {x2}]: {len(slice_polygons)} polygons")
```

### Use Simple Test Cases
Start with:
1. Empty field (no obstacles) → 1 block
2. Field with 1 obstacle → few blocks
3. Gradually increase complexity

### Check Shapely Operations
```python
polygon = result_of_operation()
if not polygon.is_valid:
    print(f"Invalid polygon: {polygon}")
    polygon = polygon.buffer(0)  # Try to fix
```

---

## Next Steps After Stage 2

Once Stage 2 is complete and tested:

1. **Generate tracks for blocks** (may already work with existing `generate_parallel_tracks`)
2. **Create entry/exit nodes** for each block (use `Block.create_entry_exit_nodes()`)
3. **Proceed to Stage 3:** ACO-based path optimization

Stage 2 provides the foundation for Stage 3. Quality of decomposition directly impacts path optimization results.

---

## Resources

### Key Files
- **Implementation:** `src/decomposition/boustrophedon.py`, `src/decomposition/block_merger.py`
- **Tests:** `tests/test_decomposition.py`
- **Demo:** `demo_stage2.py`
- **Data structures:** `src/data/block.py`

### Reference Paper
Zhou, K., Jensen, A. L., Sørensen, C. G., Busato, P., & Bothtis, D. D. (2014).
Agricultural operations planning in fields with multiple obstacle areas.
*Computers and Electronics in Agriculture*, 109, 12-22.

**Relevant sections:**
- Section 2.3: Field Decomposition
- Figure 3: Boustrophedon decomposition example
- Section 2.3.2: Block merging algorithm

### Shapely Documentation
- Geometric operations: https://shapely.readthedocs.io/en/stable/manual.html
- Affinity transformations: https://shapely.readthedocs.io/en/stable/manual.html#affine-transformations

---

## Status Tracking

Update this section as you implement:

- [ ] Phase 1: Boustrophedon Decomposition - **NOT STARTED**
- [ ] Phase 2: Block Adjacency - **NOT STARTED**
- [ ] Phase 3: Block Merging - **NOT STARTED**
- [ ] Phase 4: Integration & Testing - **NOT STARTED**

**Estimated time:** 8-12 hours for complete implementation and testing

---

**Last Updated:** 2025-11-19
**Status:** Ready for implementation
