# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## ⚠️ CRITICAL: Read This First

**When working with this codebase, ALWAYS:**

1. 🧠 **Plan before executing** - Understand impact, read relevant files first, identify affected stages
2. 📋 **Think step-by-step** - One change at a time, test incrementally, validate assumptions
3. ❓ **Ask when uncertain** - Multiple approaches? Ambiguous requirements? Trade-offs? **Ask the user**
4. ✅ **Validate thoroughly** - Run affected tests → full test suite → visual demo → check quality
5. 🔄 **Re-execute to confirm** - **Never stop after first success**. Re-run tests, verify output consistency, confirm solution works perfectly
6. 🔒 **Respect critical constraints** - Node indexing, entry/exit parity, coordinate rotation, test coverage, algorithm fidelity

**Key principle**: This is a 3-stage pipeline where Stage 1 → Stage 2 → Stage 3. Changes cascade downstream. All 92 tests must pass. **Always verify twice.**

See detailed **Working Principles** section below ↓

---

## Project Overview

**ACO-based Agricultural Coverage Path Planning** - An implementation of Zhou et al. 2014's algorithm for optimal coverage path planning in fields with multiple obstacles.

**Current Status**: Production-ready (v2.0.0) - All 3 stages + interactive Streamlit dashboard complete
**Test Coverage**: 92/92 tests passing in ~1 second
**Academic Context**: Course project (HK251) implementing research paper algorithm
**DOI**: [10.1016/j.compag.2014.08.013](https://doi.org/10.1016/j.compag.2014.08.013)

## Working Principles

**IMPORTANT**: When working with this codebase, always follow these principles:

### 1. Plan Before Executing

**Before making any changes**, understand the impact:
- **Identify affected components**: Changes to Stage 1 → affect Stages 2 & 3. Changes to Stage 2 → affect Stage 3. Stage 3 is independent.
- **Read relevant files first**: Never propose changes to code you haven't read. Understand existing implementation before modifying.
- **Check dependencies**: What tests will need to pass? What critical constraints must be preserved?
- **Estimate scope**: Is this a simple fix or does it require architectural changes?

**Example**: If modifying `boustrophedon_decomposition`, first read:
- `src/decomposition/boustrophedon.py` (the function)
- `tests/test_decomposition.py` (how it's tested)
- `demo_stage2.py` (how it's used downstream)

### 2. Think Step-by-Step

**Execute methodically**:
- **One logical change at a time**: Don't bundle multiple unrelated changes
- **Understand before modifying**: Read the current implementation, understand why it works that way
- **Test incrementally**: After each change, run affected tests (`pytest tests/test_*.py -v`)
- **Validate assumptions**: If you think "this should work", verify it with a test

**Example workflow** for adding a new ACO parameter:
1. Read `src/optimization/aco.py` to understand ACOParameters
2. Add parameter to dataclass with default value
3. Update ACOSolver.__init__ to use it
4. Add test in `tests/test_aco.py`
5. Run: `pytest tests/test_aco.py -v`
6. Run full suite: `pytest tests/ -v`
7. Document in code comments if non-obvious

### 3. Ask When Uncertain

**Don't guess - ask the user** when:
- **Multiple valid approaches exist**: "Should I use approach A (faster) or B (more maintainable)?"
- **Requirements are ambiguous**: "Do you want this to apply to all obstacle types or just Type D?"
- **Trade-offs need decisions**: "This will improve performance but reduce readability. Proceed?"
- **Breaking changes are needed**: "This requires changing the API. Should I maintain backward compatibility?"
- **Unclear expectations**: "Should this preserve the existing behavior or replace it entirely?"

**Example questions to ask**:
- "I found 3 ways to implement this. Which fits your needs best: [options]?"
- "Should the new feature work with existing scenarios or only new ones?"
- "This change affects ACO convergence. Do you want me to retune the default parameters?"

### 4. Validate Thoroughly

**Every change must be validated**:
- **Run affected tests**: After modifying Stage 2, run `pytest tests/test_decomposition.py tests/test_stage3_integration.py -v`
- **Run full test suite before completing**: All 92 tests must pass (`pytest tests/ -v`)
- **Check solution quality**: For ACO changes, verify efficiency is still 85-95%
- **Verify visually**: Run demo to see if results look correct: `MPLBACKEND=Agg python demo_stage3.py`
- **No silent failures**: If a test fails, fix it. Don't ignore or skip tests.

**Validation checklist**:
```bash
# 1. Affected tests pass
pytest tests/test_[relevant].py -v

# 2. Full suite passes
pytest tests/ -v  # Must see: 92 passed

# 3. Demo runs without errors
MPLBACKEND=Agg python demo_stage3.py

# 4. Quality maintained (check output)
# - Path efficiency: 85-95%
# - ACO improvement: 10-50%
# - No warnings or errors
```

### 5. Re-Execute to Confirm (CRITICAL)

**Never declare success after a single test run**. Always re-execute to confirm your solution works perfectly:

**Why re-execution matters**:
- **Flaky tests**: Some tests may pass by chance (especially ACO with randomness)
- **Cached results**: First run might use stale data
- **Hidden state**: Code might work once but fail on repeated execution
- **Integration issues**: Individual components pass but pipeline fails
- **Randomness in ACO**: Solutions vary between runs - need consistent quality

**Mandatory re-execution protocol**:

1. **After fixing a bug**:
   ```bash
   # First run
   pytest tests/test_[relevant].py -v
   # ✓ Passes

   # RE-RUN to confirm fix is stable
   pytest tests/test_[relevant].py -v
   # ✓ Still passes? Good.

   # Run full suite TWICE
   pytest tests/ -v  # Should see: 92 passed
   pytest tests/ -v  # Should still see: 92 passed
   ```

2. **After modifying ACO algorithm**:
   ```bash
   # Run demo MULTIPLE times (ACO is stochastic)
   MPLBACKEND=Agg python demo_stage3.py  # Run 1
   # Check: Path efficiency = 89.2%

   MPLBACKEND=Agg python demo_stage3.py  # Run 2
   # Check: Path efficiency = 91.5%

   MPLBACKEND=Agg python demo_stage3.py  # Run 3
   # Check: Path efficiency = 90.8%

   # ✓ Consistent quality across runs (85-95%)? Good.
   # ✗ Varies wildly (50-95%)? Problem!
   ```

3. **After making any change**:
   ```bash
   # Immediate verification
   pytest tests/test_modified_component.py -v

   # Re-run after 1 minute (catch timing issues)
   pytest tests/test_modified_component.py -v

   # Final confirmation - full suite
   pytest tests/ -v  # All 92 pass
   pytest tests/ -v  # Still all 92 pass
   ```

4. **Visual verification (for Stage 3 changes)**:
   ```bash
   # Generate output
   MPLBACKEND=Agg python demo_stage3.py
   # Output: stage3_path.png, stage3_convergence.png

   # Verify visually:
   # ✓ Path covers all blocks?
   # ✓ No overlapping segments?
   # ✓ Convergence plot shows improvement?
   # ✓ Efficiency 85-95%?

   # Delete outputs and regenerate to confirm
   rm stage3_*.png
   MPLBACKEND=Agg python demo_stage3.py
   # Output regenerated successfully? Good.
   ```

**What "works perfectly" means**:
- ✅ All 92 tests pass **consistently** (run twice minimum)
- ✅ No warnings or errors in output
- ✅ Solution quality maintained: efficiency 85-95%, ACO improvement 10-50%
- ✅ Output is **reproducible** (same inputs → similar outputs for stochastic algorithms)
- ✅ Visual output looks correct (no artifacts, proper coverage)
- ✅ Performance acceptable: tests complete in ~1 second, demo in < 60 seconds

**RED FLAGS that require more testing**:
- 🚩 Tests pass sometimes but fail on re-run
- 🚩 Path efficiency varies wildly (60% one run, 95% next run)
- 🚩 Warnings appear intermittently
- 🚩 Output looks different each time (beyond expected ACO variation)
- 🚩 Performance degrades significantly (tests now take 5+ seconds)

**Before declaring "DONE"**:
```bash
# FINAL VERIFICATION PROTOCOL
# 1. Clean slate
git status  # Check what changed
pytest tests/ -v  # Full suite: 92 passed

# 2. Re-run for confirmation
pytest tests/ -v  # Still 92 passed

# 3. Test affected components specifically
pytest tests/test_[your_changes].py -v -s  # Detailed output

# 4. Visual demo (if applicable)
MPLBACKEND=Agg python demo_stage3.py
# Check output quality

# 5. Final sanity check
pytest tests/test_solution_verification.py -v -s
# All quality checks pass

# ✓ ALL steps passed? NOW you can declare success.
```

**Example of proper re-execution**:
```
❌ BAD:
- Fix bug
- Run test once
- "It passes! Done!"
- (Doesn't actually work)

✅ GOOD:
- Fix bug
- Run affected tests: pytest tests/test_aco.py -v → PASS
- Re-run immediately: pytest tests/test_aco.py -v → PASS
- Run full suite: pytest tests/ -v → 92 passed
- Re-run full suite: pytest tests/ -v → 92 passed
- Run demo: MPLBACKEND=Agg python demo_stage3.py → Efficiency 89%
- Re-run demo: MPLBACKEND=Agg python demo_stage3.py → Efficiency 91%
- ✓ Consistent quality, now truly done!
```

### 6. Respect Critical Constraints

**These constraints are NON-NEGOTIABLE**:
- ✅ **Node indexing**: Must be consecutive across blocks (0-3, 4-7, 8-11, ...)
- ✅ **Entry/exit parity**: Invalid transitions must have infinite cost
- ✅ **Coordinate rotation**: Boustrophedon must rotate geometry and rotate back
- ✅ **Test coverage**: All 92 tests must pass
- ✅ **Algorithm fidelity**: Implementation must match Zhou et al. 2014 paper

**If you need to break a constraint**, ask first.

## Quick Start

```bash
# Setup environment
uv venv && source .venv/bin/activate && uv pip install -e .

# Verify everything works
pytest tests/ -v  # Should see: 92 passed in ~1s

# Run complete demo
MPLBACKEND=Agg python demo_stage3.py

# Launch interactive dashboard
.venv/bin/streamlit run streamlit_app.py
```

## Architecture: The Three-Stage Pipeline

This is the **most important** thing to understand about the codebase. The algorithm processes a field through three sequential stages:

```
INPUT: Field boundary + Obstacles + Parameters
   ↓
┌─────────────────────────────────────────┐
│ STAGE 1: Field Representation          │
│ Location: src/geometry/, src/obstacles/ │
│                                         │
│ Input:  Field boundary polygon         │
│         Obstacle polygons               │
│         FieldParameters                 │
│                                         │
│ Process:                                │
│  1. Generate headlands (buffer zones)  │
│  2. Classify obstacles (A/B/C/D types) │
│  3. Generate parallel tracks (MBR)     │
│                                         │
│ Output: HeadlandResult                  │
│         List[ClassifiedObstacle]        │
│         List[Track] (parallel lines)    │
└─────────────────────────────────────────┘
   ↓
┌─────────────────────────────────────────┐
│ STAGE 2: Boustrophedon Decomposition   │
│ Location: src/decomposition/            │
│                                         │
│ Input:  Inner boundary (from Stage 1)  │
│         Type D obstacles only           │
│         Driving direction               │
│                                         │
│ Process:                                │
│  1. Find critical points (sweep line)  │
│  2. Extract obstacle-free cells        │
│  3. Merge adjacent blocks              │
│  4. Assign tracks to each block        │
│                                         │
│ Output: List[Block] with adjacency      │
│         Each block has tracks assigned  │
└─────────────────────────────────────────┘
   ↓
┌─────────────────────────────────────────┐
│ STAGE 3: ACO Path Optimization          │
│ Location: src/optimization/             │
│                                         │
│ Input:  List[Block] (from Stage 2)     │
│         ACOParameters                   │
│                                         │
│ Process:                                │
│  1. Create 4 nodes per block           │
│  2. Build cost matrix (working/trans)  │
│  3. Run ACO to find optimal sequence   │
│  4. Generate continuous path           │
│                                         │
│ Output: Solution (best tour)            │
│         PathPlan (complete waypoints)   │
└─────────────────────────────────────────┘
   ↓
OUTPUT: Complete coverage path with 85-95% efficiency
```

### Stage 1: Field Geometric Representation

**Purpose**: Transform raw field geometry into a structured representation with classified obstacles and coverage tracks.

**Key Operations**:

1. **Headland Generation** (`src/geometry/headland.py`)
   - Creates buffer zones around field boundary for turning maneuvers
   - Creates buffer zones around obstacles for safety clearance
   - Number of passes controlled by `FieldParameters.num_headland_passes`
   - Returns `HeadlandResult` with `inner_boundary` (working area) and `headland_zones`

2. **Obstacle Classification** (`src/obstacles/classifier.py`)
   ```
   Type A: Too small (< obstacle_threshold) → Ignore completely
   Type B: Touches boundary → Incorporate into field headland
   Type C: Too close to others (< operating_width) → Merge into single obstacle
   Type D: Standard obstacles → Require decomposition in Stage 2
   ```
   - **Only Type D obstacles** proceed to Stage 2
   - Classification based on size, position, and proximity
   - Returns `List[ClassifiedObstacle]` with type annotations

3. **Parallel Track Generation** (`src/geometry/tracks.py`)
   - Uses **Minimum Bounding Rectangle (MBR)** with rotating calipers algorithm
   - Finds optimal orientation to minimize number of tracks
   - Spacing = `FieldParameters.operating_width` (vehicle width)
   - Tracks are clipped to field `inner_boundary`
   - Returns `List[Track]` (each track is a LineString)

**Important**: Stage 1 output determines everything downstream. If headland or tracks are wrong, all subsequent stages will produce incorrect results.

### Stage 2: Boustrophedon Cellular Decomposition

**Purpose**: Divide the field into simple, obstacle-free regions (blocks) that can be covered independently.

**Key Operations**:

1. **Critical Point Detection** (`src/decomposition/boustrophedon.py:find_critical_points`)
   - Sweeps perpendicular to driving direction (vertical line moving left→right)
   - **Critical points**: x-coordinates where topology changes
     - Obstacle appears/disappears
     - Connectivity between regions changes
   - **Coordinate system rotation**: Geometry rotated by `-driving_direction_degrees` so driving direction points East (0°)
   - Returns sorted list of x-coordinates in rotated space

2. **Cell Extraction** (`src/decomposition/boustrophedon.py:boustrophedon_decomposition`)
   - For each pair of consecutive critical points:
     - Create vertical slice through field
     - Extract obstacle-free regions
   - Each extracted region becomes a **preliminary block**
   - Blocks are simple trapezoid-like polygons
   - Geometry rotated back to original coordinate system
   - Returns `List[Block]` (preliminary blocks)

3. **Block Merging** (`src/decomposition/block_merger.py`)
   - Builds adjacency graph: which blocks share edges
   - Greedily merges adjacent blocks to reduce complexity
   - Criteria: preserve convexity, balance areas, maintain simple geometry
   - Reduces number of blocks by 20-50% typically
   - Returns `List[Block]` (final merged blocks)

4. **Track Assignment**
   - Each final block gets tracks from Stage 1 clipped to block boundary
   - Tracks stored in `Block.tracks` attribute
   - Track order determines in-block coverage pattern

**Important Constraint**: The coordinate rotation/de-rotation is critical. All decomposition logic works in rotated space (driving direction = East), but output must be in original coordinates.

### Stage 3: ACO-based Path Optimization

**Purpose**: Find the optimal order to visit all blocks (TSP-like problem) using Ant Colony Optimization.

**Key Operations**:

1. **Entry/Exit Node Generation** (`src/data/block.py:Block.create_entry_exit_nodes`)
   - Each block generates exactly **4 nodes**:
     ```
     first_start:  Start of first track
     first_end:    End of first track
     last_start:   Start of last track
     last_end:     End of last track
     ```
   - Nodes indexed consecutively: Block 0 → nodes 0-3, Block 1 → nodes 4-7, etc.
   - Node positions = track endpoints
   - Total nodes = 4 × num_blocks

2. **Cost Matrix Construction** (`src/optimization/cost_matrix.py:build_cost_matrix`)
   - **Dimensions**: N×N where N = total nodes
   - **Cost calculation**:
     ```python
     if i == j:
         cost = 0  # Same node
     elif same_block(i, j):
         cost = working_distance(i, j)  # Track coverage distance
     else:
         if valid_transition(i, j):
             cost = euclidean_distance(i, j)  # Straight-line transition
         else:
             cost = inf  # Invalid (violates entry/exit parity)
     ```

   **Entry/Exit Parity Constraint** (CRITICAL):
   - Valid: enter through `first_start` → exit through `first_end` or `last_end`
   - Valid: enter through `last_start` → exit through `first_start` or `last_end`
   - Invalid: enter and exit through same node type
   - Invalid: unpaired transitions (e.g., `first_start` → `last_start` in same block)
   - Enforced by setting cost = infinity for invalid transitions

3. **ACO Algorithm** (`src/optimization/aco.py:ACOSolver`)

   **Algorithm Overview**:
   ```python
   Initialize pheromone matrix (uniform values)

   For iteration in range(num_iterations):
       solutions = []

       # Construction phase
       for ant in range(num_ants):
           solution = ant.construct_solution()  # Probabilistic
           solutions.append(solution)

       # Update phase
       evaporate_pheromone(rho)  # τ ← τ × (1 - rho)

       for solution in solutions:
           deposit_pheromone(solution, amount=Q/cost)

       # Elitist strategy
       if solution is best_so_far:
           deposit_pheromone(solution, amount=elitist_weight * Q/cost)

       # Check convergence
       if no_improvement_for_N_iterations:
           break

   return best_solution
   ```

   **Probabilistic Selection** (how ants choose next block):
   ```python
   # Probability of selecting block j from block i
   P[i][j] = (pheromone[i][j]^alpha × heuristic[i][j]^beta) / sum_of_all_choices

   where:
       pheromone[i][j] = learned value (higher = better historical performance)
       heuristic[i][j] = 1 / distance[i][j] (closer blocks preferred)
       alpha = pheromone importance (default: 1.0)
       beta = heuristic importance (default: 2.0)
   ```

   **ACO Parameters** (`ACOParameters`):
   - `alpha=1.0`: Pheromone trail importance (how much to trust learned paths)
   - `beta=2.0`: Heuristic importance (how much to favor nearby blocks)
   - `rho=0.1`: Evaporation rate (forget bad solutions slowly)
   - `q=100.0`: Pheromone deposit amount
   - `num_ants=30`: Population size per iteration
   - `num_iterations=100`: Maximum iterations (usually converges in 50-100)
   - `elitist_weight=2.0`: Extra pheromone for best solution

   **Convergence Behavior**:
   - Typical improvement: 10-50% over initial random solution
   - Early convergence (< 20 iters): Increase `num_ants` or `num_iterations`
   - Poor solutions: Increase `beta` (favor distance more) or decrease `rho`
   - Slow convergence: Increase `alpha` (trust pheromone more)

4. **Path Generation** (`src/optimization/path_generation.py:generate_path_from_solution`)
   - Takes ACO solution (block sequence) and generates continuous path
   - Creates two types of segments:
     - **Working segments**: Coverage within a block (follows tracks)
     - **Transition segments**: Straight-line movement between blocks
   - Returns `PathPlan` with:
     - `segments`: List of PathSegment (working/transition)
     - `block_sequence`: Order blocks were visited
     - `total_distance`, `working_distance`, `transition_distance`
     - `efficiency`: working_distance / total_distance (typically 85-95%)

**Important**: The ACO solution is a sequence of nodes, not blocks. Each block appears twice in the solution (entry and exit). Convert node sequence → block sequence for path generation.

## Core Data Structures

Understanding these is essential for making modifications:

### Field & Parameters (`src/data/field.py`)

```python
@dataclass
class Field:
    boundary_polygon: Polygon          # Field outer boundary
    obstacles: List[Obstacle]          # All obstacles in field
    name: str                          # Field identifier

@dataclass
class FieldParameters:
    operating_width: float             # Vehicle/implement width (meters)
    turning_radius: float              # Minimum turning radius (meters)
    num_headland_passes: int           # Headland buffer iterations (typically 2)
    driving_direction: float           # Track angle in degrees (0° = East)
    obstacle_threshold: float          # Min obstacle size to consider (meters)
```

### Obstacles (`src/data/obstacle.py`)

```python
class ObstacleType(Enum):
    TYPE_A = "A"  # Too small, ignore
    TYPE_B = "B"  # Boundary-touching
    TYPE_C = "C"  # Close proximity, merge
    TYPE_D = "D"  # Standard, needs decomposition

@dataclass
class Obstacle:
    polygon: Polygon                   # Obstacle geometry
    obstacle_type: ObstacleType        # Classification result
    original_index: int                # Index in original list
```

### Blocks (`src/data/block.py`)

```python
@dataclass
class Block:
    polygon: Polygon                   # Block boundary
    block_id: int                      # Unique identifier
    tracks: List[Track]                # Assigned coverage tracks
    adjacent_blocks: Set[int]          # IDs of adjacent blocks

    def create_entry_exit_nodes(self, start_index: int) -> List[BlockNode]:
        """Creates 4 nodes: first_start, first_end, last_start, last_end"""

class BlockNode:
    node_id: int                       # Global node index
    block_id: int                      # Which block this belongs to
    position: Point                    # Spatial location (x, y)
    node_type: str                     # "first_start"|"first_end"|"last_start"|"last_end"
```

### Tracks (`src/data/track.py`)

```python
@dataclass
class Track:
    line: LineString                   # Track geometry (start → end)
    track_id: int                      # Identifier
    length: float                      # Track length in meters
```

### ACO Solution & Path (`src/optimization/`)

```python
@dataclass
class Solution:
    path: List[int]                    # Node indices in visit order
    cost: float                        # Total cost
    block_sequence: List[int]          # Block IDs in visit order

    def is_valid(self, num_blocks: int) -> bool:
        """Validates all blocks visited exactly once"""

@dataclass
class PathSegment:
    segment_type: str                  # "working" | "transition"
    waypoints: List[Point]             # Path points
    distance: float                    # Segment length
    block_id: Optional[int]            # For working segments

@dataclass
class PathPlan:
    segments: List[PathSegment]        # All path segments
    total_distance: float              # Total path length
    working_distance: float            # Sum of working segments
    transition_distance: float         # Sum of transitions
    block_sequence: List[int]          # Block visit order
    efficiency: float                  # working / total (0.0-1.0)
```

## Key Algorithms Explained

### Minimum Bounding Rectangle (MBR) - `src/geometry/mbr.py`

**Purpose**: Find optimal track orientation to minimize coverage distance.

**Algorithm** (Rotating Calipers):
1. Compute convex hull of field boundary
2. For each edge of convex hull:
   - Compute bounding rectangle aligned with that edge
   - Calculate area of rectangle
3. Select rectangle with minimum area
4. Track direction = long axis of minimal rectangle

**Why it matters**: Optimal track orientation can reduce coverage distance by 10-30% compared to arbitrary orientation.

**Returns**: `MBRResult` with angle, dimensions, and corner points.

### Boustrophedon Decomposition - `src/decomposition/boustrophedon.py`

**Purpose**: Decompose complex field into simple obstacle-free cells.

**Algorithm** (Vertical Sweep Line):
```
1. Rotate geometry so driving direction = East (0°)
   rotation_angle = -driving_direction_degrees

2. Find critical x-coordinates:
   - Field left/right boundaries
   - All obstacle vertex x-coordinates
   - Sort and deduplicate

3. For each pair of adjacent critical points:
   a. Create vertical slice at x = critical_point[i]
   b. Intersect slice with field boundary
   c. Subtract obstacles from intersection
   d. Extract resulting polygons as blocks

4. Rotate blocks back to original coordinate system
   rotation_angle = +driving_direction_degrees

5. Return List[Block] (preliminary blocks)
```

**Why coordinate rotation**: Sweep line logic assumes vertical sweep (x-axis). Rotation aligns any driving direction to this assumption.

**Critical Points Example**:
```
Field: x ∈ [0, 100]
Obstacle 1: vertices at x = 20, 40
Obstacle 2: vertices at x = 60, 75

Critical points: [0, 20, 40, 60, 75, 100]
Slices: [0-20], [20-40], [40-60], [60-75], [75-100]
Each slice → extract obstacle-free regions
```

### Block Merging - `src/decomposition/block_merger.py`

**Purpose**: Reduce number of blocks by merging compatible adjacent blocks.

**Algorithm** (Greedy Adjacency-Based):
```
1. Build adjacency graph:
   for each pair of blocks:
       if blocks.share_edge():
           graph.add_edge(block_i, block_j)

2. Merge blocks greedily:
   for each block in sorted_by_area():
       for each adjacent_block:
           if can_merge(block, adjacent_block):
               merged = merge(block, adjacent_block)
               update_graph(merged)
               break

3. Return merged blocks
```

**Merge criteria**:
- Blocks must be adjacent (share edge)
- Merged polygon must be convex (or nearly convex)
- Area difference < threshold (balanced merging)
- Must maintain simple geometry (no complex shapes)

**Impact**: Typically reduces blocks by 20-50%, which significantly speeds up ACO (fewer nodes).

### Cost Matrix Construction - `src/optimization/cost_matrix.py`

**Purpose**: Precompute all pairwise transition costs between nodes.

**Algorithm**:
```python
def build_cost_matrix(blocks, nodes):
    N = len(nodes)
    cost_matrix = np.zeros((N, N))

    for i in range(N):
        for j in range(N):
            node_i, node_j = nodes[i], nodes[j]

            if i == j:
                cost_matrix[i][j] = 0

            elif node_i.block_id == node_j.block_id:
                # Same block: working distance
                cost_matrix[i][j] = compute_working_distance(
                    block=blocks[node_i.block_id],
                    start_node=node_i,
                    end_node=node_j
                )

                # Enforce entry/exit parity
                if not is_valid_transition(node_i, node_j):
                    cost_matrix[i][j] = np.inf

            else:
                # Different blocks: transition distance
                cost_matrix[i][j] = euclidean_distance(
                    node_i.position,
                    node_j.position
                )

    return cost_matrix
```

**Working Distance Calculation**:
- Sum of track lengths between start and end nodes
- Example: `first_start` → `last_end` = all tracks in block
- Example: `first_start` → `first_end` = just first track

**Entry/Exit Parity Rules**:
```
Valid transitions within same block:
  first_start → first_end  ✓
  first_start → last_end   ✓
  last_start → first_end   ✓
  last_start → last_end    ✓

Invalid (set cost = inf):
  first_start → first_start  ✗ (same node)
  first_start → last_start   ✗ (both starts)
  first_end → last_end       ✗ (both ends)
```

**Why infinity costs**: Forces ACO to respect physical constraints (can't exit where you entered).

## Development Workflow

### Running Tests

```bash
# Full test suite (should take ~1 second)
pytest tests/ -v

# Expected output:
# tests/test_basic_functionality.py::... PASSED (7 tests)
# tests/test_integration_stage1.py::... PASSED (9 tests)
# tests/test_decomposition.py::... PASSED (13 tests)
# tests/test_cost_matrix.py::... PASSED (18 tests)
# tests/test_aco.py::... PASSED (20 tests)
# tests/test_path_generation.py::... PASSED (17 tests)
# tests/test_solution_verification.py::... PASSED (4 tests)
# ... 92 passed in 0.95s

# Stage-specific tests
pytest tests/test_aco.py -v                    # ACO algorithm only
pytest tests/test_decomposition.py -v          # Stage 2 only
pytest tests/test_integration_stage1.py -v     # Stage 1 pipeline

# With verbose output (see print statements)
pytest tests/test_aco.py -v -s

# Single test
pytest tests/test_aco.py::test_aco_solver_convergence -v

# Verification tests (solution quality checks)
pytest tests/test_solution_verification.py -v -s
```

**Test Organization**:
- `test_basic_functionality.py`: Core data structures
- `test_integration_stage1.py`: Stage 1 complete pipeline
- `test_decomposition.py`: Stage 2 decomposition and merging
- `test_cost_matrix.py`: Cost matrix construction and validation
- `test_aco.py`: ACO algorithm behavior
- `test_path_generation.py`: Path generation from solutions
- `test_solution_verification.py`: End-to-end quality validation

**When to run tests**:
- After any code change: `pytest tests/ -v`
- Before committing: `pytest tests/ -v` (all must pass)
- After modifying ACO: `pytest tests/test_aco.py tests/test_solution_verification.py -v`
- After modifying decomposition: `pytest tests/test_decomposition.py tests/test_stage3_integration.py -v`

### Running Demos

```bash
# Stage 1: Field representation
python demo_stage1.py
# Output: results/plots/stage1_demo.png
# Shows: headlands, classified obstacles, parallel tracks

# Stage 2: Decomposition
python demo_stage2.py
# Output: results/plots/stage2_demo.png
# Shows: preliminary blocks, merged blocks, track assignment

# Stage 3: ACO optimization (IMPORTANT: use MPLBACKEND for headless)
MPLBACKEND=Agg python demo_stage3.py
# Output: stage3_path.png (coverage path), stage3_convergence.png (ACO progress)
# Shows: optimized path, working/transition segments, convergence plot

# Animation demos
python demo_animation.py  # Path execution animation
python demo_complete_visualization.py  # All visualizations
```

**Why MPLBACKEND=Agg**: Prevents matplotlib from trying to open GUI windows in headless environments (SSH, CI/CD, WSL without X11).

### Dashboard

```bash
# Launch Streamlit dashboard
.venv/bin/streamlit run streamlit_app.py

# Runs on http://localhost:8501
# Features:
#  - Quick Demo tab with pre-configured scenarios
#  - One-click execution of complete pipeline
#  - Real-time progress tracking
#  - Export animations, PDFs, CSVs, PNGs

# Test dashboard components
python test_dashboard_components.py
python test_pipeline_integration.py
```

### Code Quality

```bash
# Format code (100-char line length per pyproject.toml)
black src/ tests/

# Lint code
ruff check src/ tests/

# Type checking (optional)
mypy src/
```

## Code Patterns

### Creating and Processing a Field

```python
from src.data import create_field_with_rectangular_obstacles, FieldParameters
from src.geometry import generate_field_headland, generate_parallel_tracks
from src.obstacles.classifier import classify_all_obstacles, get_type_d_obstacles
from src.decomposition import boustrophedon_decomposition, merge_blocks_by_criteria
from src.optimization import ACOParameters, ACOSolver, build_cost_matrix, generate_path_from_solution

# 1. Create field
field = create_field_with_rectangular_obstacles(
    field_width=100,
    field_height=80,
    obstacle_specs=[(x, y, width, height), ...],  # List of (x, y, w, h) tuples
    name="Demo Field"
)

# 2. Set parameters
params = FieldParameters(
    operating_width=5.0,           # Vehicle width
    turning_radius=3.0,            # Min turning radius
    num_headland_passes=2,         # Headland iterations
    driving_direction=0.0,         # Track angle (0° = East)
    obstacle_threshold=5.0         # Min obstacle size
)

# === STAGE 1 ===
headland = generate_field_headland(
    field.boundary_polygon,
    params.operating_width,
    params.num_headland_passes
)

classified_obstacles = classify_all_obstacles(
    field.obstacles,
    headland.inner_boundary,
    params.driving_direction,
    params.operating_width,
    params.obstacle_threshold
)

type_d_obstacles = get_type_d_obstacles(classified_obstacles)

# === STAGE 2 ===
preliminary_blocks = boustrophedon_decomposition(
    inner_boundary=headland.inner_boundary,
    obstacles=[obs.polygon for obs in type_d_obstacles],
    driving_direction_degrees=params.driving_direction
)

final_blocks = merge_blocks_by_criteria(
    blocks=preliminary_blocks,
    operating_width=params.operating_width
)

# Assign tracks to blocks
for block in final_blocks:
    tracks = generate_parallel_tracks(
        inner_boundary=block.polygon,
        driving_direction_degrees=params.driving_direction,
        operating_width=params.operating_width
    )
    block.tracks = tracks

# === STAGE 3 ===
all_nodes = []
for block in final_blocks:
    nodes = block.create_entry_exit_nodes(start_index=len(all_nodes))
    all_nodes.extend(nodes)

cost_matrix = build_cost_matrix(blocks=final_blocks, nodes=all_nodes)

solver = ACOSolver(
    blocks=final_blocks,
    nodes=all_nodes,
    cost_matrix=cost_matrix,
    params=ACOParameters(num_ants=30, num_iterations=100)
)

solution = solver.solve(verbose=True)
path_plan = generate_path_from_solution(solution, final_blocks, all_nodes)

print(f"Efficiency: {path_plan.efficiency*100:.1f}%")
print(f"Total distance: {path_plan.total_distance:.2f}m")
```

### Modifying ACO Parameters

```python
# Quick testing (faster but less optimal)
quick_params = ACOParameters(
    num_ants=10,
    num_iterations=20
)

# High quality (slower but better)
quality_params = ACOParameters(
    num_ants=50,
    num_iterations=200,
    beta=3.0,      # Favor distance more
    rho=0.15       # Faster evaporation
)

# Balanced (default)
balanced_params = ACOParameters()  # Uses defaults
```

### Accessing Results

```python
# Get path statistics
from src.optimization import get_path_statistics

stats = get_path_statistics(path_plan)
# Returns: {
#   'total_distance': float,
#   'working_distance': float,
#   'transition_distance': float,
#   'efficiency': float,
#   'num_blocks': int,
#   'num_working_segments': int,
#   'num_transition_segments': int,
#   'total_waypoints': int
# }

# Access segments
for segment in path_plan.segments:
    if segment.segment_type == "working":
        print(f"Covering block {segment.block_id}: {segment.distance:.2f}m")
    else:
        print(f"Transition: {segment.distance:.2f}m")

# Get all waypoints for vehicle control
waypoints = path_plan.get_all_waypoints()  # List[Point]
```

## Important Constraints & Gotchas

### Node Indexing (CRITICAL)

Nodes are indexed **consecutively across blocks**:
```
Block 0: nodes 0, 1, 2, 3
Block 1: nodes 4, 5, 6, 7
Block 2: nodes 8, 9, 10, 11
...
```

Each block has exactly 4 nodes in this order:
1. `first_start` (start of first track)
2. `first_end` (end of first track)
3. `last_start` (start of last track)
4. `last_end` (end of last track)

**When creating nodes**:
```python
all_nodes = []
start_index = 0
for block in blocks:
    nodes = block.create_entry_exit_nodes(start_index=start_index)
    all_nodes.extend(nodes)
    start_index += 4  # IMPORTANT: increment by 4
```

### Entry/Exit Parity (CRITICAL)

**Valid block visitation**:
- Enter through one node, exit through a *compatible* node
- Compatible pairs: (start, end) or (start, different_end)

**Invalid transitions** (enforced via infinite cost):
- Enter and exit through same node
- Enter through start, exit through different start
- Enter through end, exit through different end

**Example**:
```python
# Valid
first_start → first_end    # Cover just first track
first_start → last_end     # Cover all tracks
last_start → first_end     # Cover all tracks in reverse

# Invalid (cost = infinity)
first_start → first_start  # Can't exit where you entered
first_start → last_start   # Both are starts
first_end → last_end       # Both are ends
```

### Coordinate System Rotation

**In boustrophedon decomposition**:
- All geometry rotated by `-driving_direction_degrees`
- This makes driving direction point East (0°)
- Sweep line algorithm assumes vertical sweep (perpendicular to East)
- **Must rotate results back** by `+driving_direction_degrees`

**Pattern**:
```python
rotation_angle = -driving_direction_degrees
rotated_geometry = rotate_geometry(original, rotation_angle)
# ... process in rotated space ...
final_geometry = rotate_geometry(processed, -rotation_angle)  # Rotate back
```

**Common bug**: Forgetting to rotate back → blocks in wrong orientation.

### ACO Convergence Issues

**Problem**: ACO converges too quickly (< 20 iterations)
**Solution**: Increase `num_ants` (try 50) or `num_iterations` (try 200)

**Problem**: Poor solution quality (< 70% efficiency)
**Solution**:
- Increase `beta` to 3.0 (favor distance more)
- Decrease `rho` to 0.05 (slower evaporation)
- Increase `num_ants` to 50

**Problem**: Slow convergence (> 100 iterations)
**Solution**:
- Increase `alpha` to 1.5 (trust pheromone more)
- Increase `rho` to 0.2 (faster evaporation)

**Problem**: Stagnation (no improvement)
**Solution**: Restart with different random seed or increase `num_ants`

### Testing Requirements

**Before committing**:
1. Run full test suite: `pytest tests/ -v`
2. All 92 tests must pass
3. No new warnings

**After modifying algorithms**:
1. Run relevant tests (e.g., `pytest tests/test_aco.py -v`)
2. Run verification tests: `pytest tests/test_solution_verification.py -v`
3. Manually run demo: `MPLBACKEND=Agg python demo_stage3.py`
4. Check output quality visually

## Project Structure

```
src/
├── data/                  # Core data structures
│   ├── field.py          # Field, FieldParameters
│   ├── obstacle.py       # Obstacle, ObstacleType
│   ├── block.py          # Block, BlockNode, BlockGraph
│   └── track.py          # Track
│
├── geometry/              # Stage 1 geometric operations
│   ├── headland.py       # Headland generation
│   ├── tracks.py         # Parallel track generation
│   ├── mbr.py            # Minimum Bounding Rectangle
│   └── polygon.py        # Polygon utilities (offset, rotation)
│
├── obstacles/             # Stage 1 obstacle processing
│   └── classifier.py     # Obstacle classification (A/B/C/D)
│
├── decomposition/         # Stage 2 field decomposition
│   ├── boustrophedon.py  # Cellular decomposition
│   └── block_merger.py   # Block merging logic
│
├── optimization/          # Stage 3 path optimization
│   ├── aco.py            # ACO algorithm (core)
│   ├── cost_matrix.py    # Cost matrix construction
│   └── path_generation.py # Path generation from solution
│
├── visualization/         # Plotting and animation
│   ├── plot_utils.py     # Common plotting functions
│   ├── path_animation.py # PathAnimator (GIF)
│   └── pheromone_animation.py # PheromoneAnimator (GIF)
│
└── dashboard/             # Streamlit dashboard
    ├── config_manager.py # Scenario configuration
    ├── export_utils.py   # PDF/CSV/PNG export
    └── quick_demo.py     # Quick Demo tab

tests/                     # 92 comprehensive tests
scenarios/                 # Pre-configured field scenarios (JSON)
exports/                   # Dashboard output directory
demo_*.py                  # Command-line demonstrations
streamlit_app.py           # Main dashboard entry point
```

## Common Tasks

### Adding a New Test

1. Choose appropriate test file:
   - Stage 1: `tests/test_integration_stage1.py`
   - Stage 2: `tests/test_decomposition.py`
   - Stage 3: `tests/test_aco.py`, `test_cost_matrix.py`, `test_path_generation.py`

2. Use existing fixtures or create new ones:
```python
import pytest
from src.data import create_field_with_rectangular_obstacles

@pytest.fixture
def simple_field():
    return create_field_with_rectangular_obstacles(
        field_width=50,
        field_height=40,
        obstacle_specs=[(20, 15, 10, 8)],
        name="Simple Test Field"
    )

def test_my_new_feature(simple_field):
    # Your test here
    assert ...
```

3. Run test: `pytest tests/test_file.py::test_my_new_feature -v`

### Adding a New ACO Parameter

1. Update `ACOParameters` in `src/optimization/aco.py`:
```python
@dataclass
class ACOParameters:
    # ... existing params ...
    my_new_param: float = 1.0  # Add with default
```

2. Update `ACOSolver` to use it:
```python
def __init__(self, blocks, nodes, cost_matrix, params):
    # ... existing code ...
    self.my_new_param = params.my_new_param
```

3. Add test in `tests/test_aco.py`:
```python
def test_new_parameter():
    params = ACOParameters(my_new_param=2.0)
    assert params.my_new_param == 2.0
```

4. Run tests: `pytest tests/test_aco.py -v`

### Adding a New Scenario

1. Create JSON in `scenarios/`:
```json
{
  "field_width": 100,
  "field_height": 80,
  "obstacles": [
    {"x": 30, "y": 30, "width": 15, "height": 12},
    {"x": 65, "y": 50, "width": 12, "height": 15}
  ],
  "parameters": {
    "operating_width": 5.0,
    "turning_radius": 3.0,
    "num_headland_passes": 2,
    "driving_direction": 0.0,
    "obstacle_threshold": 5.0
  }
}
```

2. Update `src/dashboard/config_manager.py` if needed

3. Test with dashboard: `.venv/bin/streamlit run streamlit_app.py`

### Modifying an Algorithm

1. **Identify affected components**:
   - Modifying Stage 1 (geometry)? → Affects Stages 2 & 3
   - Modifying Stage 2 (decomposition)? → Affects Stage 3 only
   - Modifying Stage 3 (ACO)? → Independent

2. **Make changes** in appropriate `src/` file

3. **Update tests** to reflect changes

4. **Run affected tests**:
```bash
# Stage 1 change
pytest tests/test_integration_stage1.py tests/test_decomposition.py tests/test_stage3_integration.py -v

# Stage 2 change
pytest tests/test_decomposition.py tests/test_stage3_integration.py -v

# Stage 3 change
pytest tests/test_aco.py tests/test_path_generation.py tests/test_solution_verification.py -v
```

5. **Run full test suite**: `pytest tests/ -v`

6. **Validate visually**: `MPLBACKEND=Agg python demo_stage3.py`

### Debugging a Failed Test

1. **Run with verbose output**:
```bash
pytest tests/test_file.py::test_name -v -s
```

2. **Add debug prints** in code:
```python
print(f"DEBUG: value = {value}")
import pdb; pdb.set_trace()  # Breakpoint
```

3. **Check test fixtures** - ensure test data is valid

4. **Run just that test** until it passes

5. **Run full suite** to ensure no regressions

## Performance Expectations

**Test Suite**: 92 tests in ~1 second (all should pass)

**Stage Timings** (100m × 80m field, 7 blocks):
- Stage 1: < 0.5 seconds
- Stage 2: < 0.2 seconds
- Stage 3: 5-30 seconds (depends on ACO parameters)

**ACO Performance**:
- Small fields (2-3 blocks): 0.5-2 seconds
- Medium fields (5-10 blocks): 2-10 seconds
- Large fields (10-20 blocks): 5-30 seconds

**Solution Quality**:
- Path efficiency: 85-95% (working/total distance)
- ACO improvement: 10-50% over initial random solution
- Convergence: 50-100 iterations typically

**Memory Usage**: < 100 MB for typical fields

## Academic Context

This is a course project (HK251: Heuristics and Optimization for Path/Motion Planning Problems) implementing a research paper algorithm.

**Focus on**:
- Correctness over performance
- Clarity over optimization
- Reproducibility over speed
- Algorithm fidelity to paper

**Reference Paper**:
> Zhou, K., Jensen, A. L., Sørensen, C. G., Busato, P., & Bochtis, D. D. (2014).
> Agricultural operations planning in fields with multiple obstacle areas.
> *Computers and Electronics in Agriculture*, 109, 12-22.
> DOI: [10.1016/j.compag.2014.08.013](https://doi.org/10.1016/j.compag.2014.08.013)
