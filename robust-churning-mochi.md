# Plan: Convex Decomposition for Non-Convex Blocks with Type B Obstacle Holes

## Problem Statement

When Type B obstacles (boundary-touching obstacles) create holes in the field's inner boundary, the boustrophedon decomposition produces **non-convex blocks** (like B0 in the screenshot). This violates the paper's assumption of "obstacle-free convex cells" and causes:
- Block merger rejecting non-convex merges (convexity_ratio < 0.99 → infinite cost)
- Excessive block fragmentation
- Potential ACO optimization issues

## Solution Overview

Implement a **Vertical Slice Subdivision** step that detects and splits non-convex blocks into multiple convex pieces using additional sweep lines at Type B obstacle boundaries.

**Key Approach:**
- Minimal extension to existing boustrophedon algorithm (maintains paper fidelity)
- Post-decomposition convex subdivision (only affects non-convex blocks)
- Reuses existing rotation and slicing infrastructure
- Isolated change with minimal impact on other stages

## Implementation Strategy

### Algorithm: Vertical Slice Subdivision

```
PHASE 1: Standard Boustrophedon Decomposition (Existing)
  1. Rotate field + obstacles by -driving_direction (align to East)
  2. Find critical Y-coordinates (obstacle vertices)
  3. Create horizontal slices → preliminary blocks
  4. Rotate blocks back to original orientation

PHASE 2: Convex Subdivision (NEW)
  FOR EACH preliminary block:
    IF block.convexity_ratio < 0.99:
      a. Detect if block contains Type B hole (check inner_boundary.interiors)
      b. Rotate block to align with driving direction
      c. Find critical X-coordinates from Type B hole vertices
      d. Create vertical sub-slices within this block
      e. Subdivide block polygon at each X-coordinate
      f. Rotate sub-blocks back to original orientation
      g. Replace non-convex block with convex sub-blocks
    ELSE:
      Keep block as-is

PHASE 3: Block Merging (Existing - Unchanged)
  - Merge convex sub-blocks using existing adjacency-based greedy algorithm
```

**Why This Works:**
- Type B holes already exist in `inner_boundary` (from Stage 1 headland generation)
- Shapely Polygons expose `.interiors` attribute for hole detection
- Reuses existing `rotate_geometry()` and `compute_slice_polygons()` patterns
- Maintains parallel track structure within each subdivided block

## Critical Files to Modify

### 1. Create New Module: `src/decomposition/convex_subdivision.py` (~300 lines)

**Functions to implement (8 total):**

1. `is_block_convex(block, threshold=0.99)` - Check convexity using convex hull ratio
2. `has_interior_holes(polygon)` - Check if polygon has holes (Type B obstacles)
3. `extract_hole_vertices(polygon)` - Extract vertices from all interior rings
4. `find_critical_x_coordinates(block, driving_direction_degrees, inner_boundary)` - Find X-coordinates for vertical subdivision
5. `create_vertical_slice(x_left, x_right, y_min, y_max)` - Create vertical slice polygon
6. `subdivide_block_vertically(block, critical_x, rotation_angle)` - Subdivide block at X-coordinates
7. `subdivide_non_convex_block(block, driving_direction_degrees, inner_boundary, next_block_id)` - Main subdivision logic for one block
8. `subdivide_all_non_convex_blocks(blocks, driving_direction_degrees, inner_boundary)` - Batch processing entry point

**Key algorithm details:**
- Reuse `rotate_geometry()` from `boustrophedon.py`
- Mirror `compute_slice_polygons()` logic but slice vertically
- Handle MultiPolygon results (take all non-empty pieces)
- Preserve area during subdivision

### 2. Integrate into `src/decomposition/boustrophedon.py` (5 lines)

**Modification:** Add after line 280 in `boustrophedon_decomposition()`

```python
# AFTER creating preliminary blocks:
blocks = []
for block_id, poly in enumerate(block_polygons_original):
    boundary_coords = list(poly.exterior.coords[:-1])
    block = Block(block_id=block_id, boundary=boundary_coords)
    blocks.append(block)

# NEW CODE (insert here):
from .convex_subdivision import subdivide_all_non_convex_blocks

blocks = subdivide_all_non_convex_blocks(
    blocks=blocks,
    driving_direction_degrees=driving_direction_degrees,
    inner_boundary=inner_boundary
)

return blocks  # EXISTING CODE
```

### 3. Create Unit Tests: `tests/test_convex_subdivision.py` (~200 lines)

**Test Classes (15+ test cases total):**

1. **TestConvexityDetection** (3 tests):
   - `test_convex_block` - Rectangle should be detected as convex
   - `test_non_convex_block_l_shape` - L-shape should be non-convex
   - `test_nearly_convex_block` - Slight indentation should fail threshold

2. **TestHoleDetection** (2 tests):
   - `test_polygon_without_holes` - Simple polygon has no holes
   - `test_polygon_with_hole` - Polygon with interior ring detected correctly

3. **TestCriticalXCoordinates** (1 test):
   - `test_block_with_hole_boundary` - Extract X-coords from Type B holes

4. **TestBlockSubdivision** (2 tests):
   - `test_subdivide_convex_block` - Convex block not subdivided
   - `test_subdivide_non_convex_block_with_hole` - L-shape subdivided into convex pieces

5. **TestBatchSubdivision** (1 test):
   - `test_subdivide_mixed_blocks` - Mix of convex and non-convex blocks

6. **TestEdgeCases** (3 tests):
   - `test_empty_block_list` - Handle empty input
   - `test_block_with_multiple_holes` - Multiple Type B obstacles
   - `test_very_small_block` - Very small non-convex blocks

### 4. Add Integration Test to `tests/test_decomposition.py`

**Addition:** New test class `TestTypeBObstacleHandling`

**Test Case:** `test_decomposition_with_type_b_hole`
- Create field with Type B obstacle (touches inner boundary)
- Generate headland (Type B incorporated into inner_boundary)
- Run boustrophedon decomposition
- Verify all blocks have convexity_ratio ≥ 0.99
- Verify total area preserved within 5% tolerance

## Implementation Sequence

### Step 1: Core Implementation
1. Create `src/decomposition/convex_subdivision.py` with 8 functions
   - Add docstrings with paper references
   - Add type hints
   - Include detailed comments

2. Integrate into `boustrophedon_decomposition()` (5 lines)
   - Import the subdivision function
   - Call after preliminary block creation

### Step 2: Unit Testing
1. Create `tests/test_convex_subdivision.py`
   - Implement 15+ test cases across 6 test classes
   - Run: `pytest tests/test_convex_subdivision.py -v`

2. Add integration test to `tests/test_decomposition.py`
   - `TestTypeBObstacleHandling` class
   - Verify all blocks convex, area preserved

### Step 3: Regression Testing
1. Run full test suite: `pytest tests/ -v`
   - Expected: 92+ tests pass (no regressions)
   - Fix block count assertions if needed (may increase due to subdivision)

### Step 4: Visual Verification
1. Run Stage 2 demo: `MPLBACKEND=Agg python examples/stage2_decomposition.py`
   - Verify blocks appear convex (rectangles, not L-shapes)

2. Run Stage 3 demo: `MPLBACKEND=Agg python examples/stage3_optimization.py`
   - Verify ACO convergence 50-100 iterations
   - Verify path efficiency 85-95%

### Step 5: Performance Verification
1. Check Stage 2 runtime < 0.5s (current ~0.2s)
2. Check test suite runtime < 2s
3. Check ACO convergence normal

## Potential Risks & Mitigation

### Risk 1: Over-Subdivision
**Impact:** Too many small convex blocks → longer ACO runtime

**Mitigation:**
- Only subdivide blocks with convexity_ratio < 0.99
- Block merger will merge adjacent convex sub-blocks
- Optional: Add minimum sub-block area threshold (3 × operating_width²)

### Risk 2: Tracks Not Clustered Correctly
**Impact:** Missing tracks in sub-blocks, Stage 3 node creation fails

**Mitigation:**
- Add assertion in `cluster_tracks_into_blocks()` to check all blocks have tracks
- Unit test track clustering with subdivided blocks
- Debug logging for track assignment

### Risk 3: Floating Point Precision
**Impact:** Missing subdivision points or zero-width slices

**Mitigation:**
- Use `np.round(critical_x, decimals=6)` (same as existing code)
- Check `abs(x_right - x_left) < 1e-6` before creating slice
- Unit tests validate no zero-width slices

### Risk 4: Performance Degradation
**Impact:** Slower Stage 2 decomposition

**Mitigation:**
- Selective: Only check/subdivide non-convex blocks
- Early exit: If no Type B holes, skip subdivision entirely
- Expected increase: ~0.2s → ~0.3-0.5s (acceptable)

## Success Criteria

### Mandatory (Must Pass)
1. All blocks convex: convexity_ratio ≥ 0.99
2. 92+ tests pass: No regressions
3. Area preservation: Within 5% tolerance
4. Stage 3 compatibility: ACO works with subdivided blocks
5. Path efficiency: 85-95% maintained

### Desirable (Should Pass)
6. Visual verification: Plots show convex blocks
7. Performance: Stage 2 <1s, tests <2s
8. Code quality: Type hints, docstrings, <100 lines per function
9. Track clustering: All blocks have tracks

## Alternatives Considered (and Rejected)

### Alternative 1: Polygon Decomposition Algorithms (Hertel-Mehlhorn)
**Rejected:** Too complex, external dependencies, overkill for this problem

### Alternative 2: Treat Type B as Type D
**Rejected:** Violates paper specification ("Type B incorporated into inner boundary")

### Alternative 3: Convex Hull Approximation
**Rejected:** Introduces coverage errors (convex hull includes obstacle space)

## Estimation

**Implementation Complexity:** Low-Medium
- New module: ~300 lines
- Integration: 5 lines
- Tests: ~200 lines
- Total: ~500 lines of code

**Impact:** Minimal
- Single function call in existing pipeline
- No changes to Stage 1, Stage 3, track clustering, or block merging
- Isolated, reversible change

**Expected Results:**
- All blocks convex (convexity_ratio ≥ 0.99)
- 92+ tests pass
- Path efficiency 85-95% maintained
- Visual: Convex rectangular blocks

## Implementation Checklist

- [ ] Create `src/decomposition/convex_subdivision.py` (~300 lines)
  - [ ] 8 functions with docstrings and type hints

- [ ] Integrate into `boustrophedon_decomposition()` (5 lines)
  - [ ] Import and call `subdivide_all_non_convex_blocks`

- [ ] Create `tests/test_convex_subdivision.py` (~200 lines)
  - [ ] 15+ unit tests across 6 test classes

- [ ] Add integration test to `tests/test_decomposition.py`
  - [ ] `TestTypeBObstacleHandling` class

- [ ] Run regression testing
  - [ ] `pytest tests/ -v` → 92+ tests pass

- [ ] Visual verification
  - [ ] Run Stage 2 demo, check convex blocks
  - [ ] Run Stage 3 demo, check convergence and path

- [ ] Performance verification
  - [ ] Stage 2 runtime < 0.5s
  - [ ] Test suite runtime < 2s

## References

- **Paper**: Zhou et al. 2014, Section 2.3.1 "Decomposition of field body into blocks"
- **Current implementation**: [src/decomposition/boustrophedon.py](src/decomposition/boustrophedon.py)
- **Block merging**: [src/decomposition/block_merger.py](src/decomposition/block_merger.py)
- **Type B handling**: [src/geometry/headland.py](src/geometry/headland.py) lines 92-105
