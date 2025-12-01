# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## ⚠️ CRITICAL: Read This First

**When working with this codebase, ALWAYS:**

1. 🧠 **Plan before executing** - Understand impact, read relevant files first, identify affected stages
2. 📋 **Think step-by-step** - One change at a time, test incrementally, validate assumptions
3. ❓ **Ask when uncertain** - Multiple approaches? Ambiguous requirements? Trade-offs? **Ask the user**
4. ✅ **Validate thoroughly** - Run affected tests → full test suite → visual demo → check quality
5. 🔄 **Re-execute to confirm** - **Never stop after first success**. Re-run tests twice minimum to confirm stability
6. 🔒 **Respect critical constraints** - Node indexing, entry/exit parity, coordinate rotation, test coverage, algorithm fidelity

**Key principle**: This is a 3-stage pipeline where Stage 1 → Stage 2 → Stage 3. Changes cascade downstream. All 92 tests must pass. **Always verify twice.**

---

## Project Overview

**ACO-based Agricultural Coverage Path Planning** - Implementation of Zhou et al. 2014's algorithm for optimal coverage path planning in fields with multiple obstacles.

- **Status**: Production-ready (v2.0.0) - All 3 stages + interactive Streamlit dashboard
- **Tests**: 92/92 passing in ~1 second
- **Context**: Course project (HK251) implementing research paper algorithm
- **DOI**: [10.1016/j.compag.2014.08.013](https://doi.org/10.1016/j.compag.2014.08.013)

## Quick Start

```bash
# Setup
uv venv && source .venv/bin/activate && uv pip install -e .

# Verify (must see: 92 passed)
pytest tests/ -v

# Run demo
MPLBACKEND=Agg python examples/stage3_optimization.py

# Dashboard
.venv/bin/streamlit run streamlit_app.py
```

## Working Principles

### 1-3. Plan, Execute Methodically, Ask When Uncertain

**Before making changes:**
- Identify affected stages (Stage 1 → affects 2 & 3; Stage 2 → affects 3; Stage 3 is independent)
- Read relevant files first (implementation, tests, examples)
- Check dependencies and estimate scope
- **Ask the user** when multiple approaches exist, requirements are ambiguous, or trade-offs need decisions

**Execute methodically:**
- One logical change at a time
- Understand current implementation before modifying
- Test incrementally: `pytest tests/test_*.py -v`
- Validate assumptions with tests

### 4. Validate Thoroughly

**Every change must be validated:**
```bash
# 1. Run affected tests
pytest tests/test_[relevant].py -v

# 2. Run full suite (must see: 92 passed)
pytest tests/ -v

# 3. Visual check
MPLBACKEND=Agg python examples/stage3_optimization.py

# 4. Verify quality (efficiency 85-95%, no warnings)
```

### 5. Re-Execute to Confirm (CRITICAL)

**Why:** ACO is stochastic, tests can be flaky, cached results can mislead.

**Mandatory protocol:**
```bash
# After ANY change, run tests TWICE minimum
pytest tests/test_[relevant].py -v  # First run
pytest tests/test_[relevant].py -v  # Confirm stable

# Full suite TWICE before declaring done
pytest tests/ -v  # 92 passed
pytest tests/ -v  # Still 92 passed

# For ACO changes, run demo 2-3 times to verify consistent quality (85-95% efficiency)
MPLBACKEND=Agg python examples/stage3_optimization.py
```

**Success criteria:**
- ✅ All 92 tests pass **consistently** (minimum 2 runs)
- ✅ No warnings or errors
- ✅ Solution quality maintained: efficiency 85-95%, ACO improvement 10-50%
- ✅ Performance acceptable: tests ~1s, demo <60s

**RED FLAGS requiring more testing:**
- 🚩 Tests pass sometimes but fail on re-run
- 🚩 Path efficiency varies wildly (60% vs 95%)
- 🚩 Intermittent warnings

### 6. Respect Critical Constraints (NON-NEGOTIABLE)

- ✅ **Node indexing**: Consecutive across blocks (0-3, 4-7, 8-11, ...)
- ✅ **Entry/exit parity**: Invalid transitions have infinite cost
- ✅ **Coordinate rotation**: Boustrophedon rotates geometry and rotates back
- ✅ **Test coverage**: All 92 tests must pass
- ✅ **Algorithm fidelity**: Match Zhou et al. 2014 paper

**If you need to break a constraint, ask first.**

## Architecture: The Three-Stage Pipeline

```
INPUT: Field boundary + Obstacles + Parameters
   ↓
┌──────────────────────────────────────────┐
│ STAGE 1: Field Representation           │
│ src/geometry/, src/obstacles/           │
│ • Generate headlands (buffer zones)     │
│ • Classify obstacles (A/B/C/D types)    │
│ • Generate parallel tracks (MBR)        │
│ Output: HeadlandResult, Obstacles, Tracks│
└──────────────────────────────────────────┘
   ↓
┌──────────────────────────────────────────┐
│ STAGE 2: Boustrophedon Decomposition    │
│ src/decomposition/                       │
│ • Find critical points (sweep line)     │
│ • Extract obstacle-free cells           │
│ • Merge adjacent blocks                 │
│ • Cluster global tracks into blocks     │
│ Output: List[Block] with tracks          │
└──────────────────────────────────────────┘
   ↓
┌──────────────────────────────────────────┐
│ STAGE 3: ACO Path Optimization           │
│ src/optimization/                        │
│ • Create 4 nodes per block              │
│ • Build cost matrix (working/trans)     │
│ • Run ACO to find optimal sequence      │
│ • Generate continuous path              │
│ Output: Solution, PathPlan (85-95% eff.) │
└──────────────────────────────────────────┘
```

### Stage Details

**Stage 1: Field Geometric Representation** (`src/geometry/`, `src/obstacles/`)
- **Headlands**: Buffer zones via `generate_field_headland()` → inner boundary
- **Obstacle classification**: A (tiny, ignore), B (boundary, merge), C (close, merge), D (standard, decompose)
- **Tracks**: Parallel lines via MBR (rotating calipers) → optimal orientation
- **Critical**: Only Type D obstacles proceed to Stage 2

**Stage 2: Boustrophedon Decomposition** (`src/decomposition/`)
- **Critical points**: Sweep perpendicular to driving direction, find topology changes
- **Coordinate rotation**: Rotate by `-driving_direction` (make East=0°), then rotate back
- **Cell extraction**: Vertical slices → obstacle-free blocks
- **Block merging**: Adjacency-based greedy merging (reduces blocks 20-50%)
- **Track clustering**: Subdivide global tracks from Stage 1 and assign to blocks (Section 2.3.2)
- **Critical**: Must rotate geometry back; only merge adjacent blocks

**Stage 3: ACO Path Optimization** (`src/optimization/`)
- **Nodes**: Each block → 4 nodes (first_start, first_end, last_start, last_end)
- **Cost matrix**: Working distance (same block) vs transition distance (different blocks)
- **Entry/exit parity**: Invalid transitions (e.g., first_start → last_start) have cost=∞
- **ACO**: Probabilistic selection, pheromone update, elitist strategy
- **Path generation**: Convert node sequence → continuous path with segments
- **Critical**: ACO solution is nodes, not blocks. Each block visited twice (entry+exit).

## Core Data Structures

```python
# Field & Parameters (src/data/field.py)
Field(boundary_polygon, obstacles, name)
FieldParameters(operating_width, turning_radius, num_headland_passes, driving_direction, obstacle_threshold)

# Obstacles (src/data/obstacle.py)
ObstacleType: TYPE_A (tiny), TYPE_B (boundary), TYPE_C (close), TYPE_D (standard)
Obstacle(polygon, obstacle_type, original_index)

# Blocks (src/data/block.py)
Block(polygon, block_id, tracks, adjacent_blocks)
BlockNode(node_id, block_id, position, node_type)

# ACO (src/optimization/)
Solution(path, cost, block_sequence)
PathPlan(segments, total_distance, working_distance, transition_distance, efficiency)
PathSegment(segment_type, waypoints, distance, block_id)
```

## Key Algorithms

**MBR** (`src/geometry/mbr.py`): Rotating calipers on convex hull → optimal track orientation (10-30% reduction)

**Boustrophedon** (`src/decomposition/boustrophedon.py`):
1. Rotate geometry by `-driving_direction` (East=0°)
2. Find critical x-coords (obstacle vertices, boundaries)
3. Vertical slices → extract obstacle-free polygons
4. Rotate back by `+driving_direction`

**Track Clustering** (`src/decomposition/track_clustering.py`):
1. Generate global tracks in Stage 1 (ignoring obstacles)
2. For each track: subdivide at block boundaries
3. Assign track segments to blocks based on containment
4. Maintains global track indices for continuity

**Cost Matrix** (`src/optimization/cost_matrix.py`):
- Same node: 0
- Same block: working distance (track sum) OR ∞ (invalid parity)
- Different blocks: euclidean distance

**Entry/Exit Parity**:
```
Valid:   first_start → first_end ✓  |  first_start → last_end ✓
Invalid: first_start → first_start ✗  |  first_start → last_start ✗
```

**ACO** (`src/optimization/aco.py`):
- Selection: `P[i][j] = (τ^α × η^β) / Σ` where τ=pheromone, η=1/distance
- Parameters: `alpha=1.0, beta=2.0, rho=0.1, num_ants=30, num_iterations=100`
- Convergence: typically 50-100 iterations, 10-50% improvement

## Development Workflow

### Running Tests

```bash
# Full suite (~1s, expect 92 passed)
pytest tests/ -v

# Stage-specific
pytest tests/test_aco.py -v                    # ACO only
pytest tests/test_decomposition.py -v          # Stage 2
pytest tests/test_integration_stage1.py -v     # Stage 1

# With output
pytest tests/test_aco.py -v -s

# Single test
pytest tests/test_aco.py::test_aco_solver_convergence -v
```

**When to run:**
- After any change: `pytest tests/ -v`
- Before committing: `pytest tests/ -v` (all must pass)
- After Stage 2 change: `pytest tests/test_decomposition.py tests/test_stage3_integration.py -v`
- After ACO change: `pytest tests/test_aco.py tests/test_solution_verification.py -v`

### Running Examples

```bash
# Stages 1-3
python examples/stage1_geometry.py        # Headlands, obstacles, tracks
python examples/stage2_decomposition.py   # Blocks, merging
MPLBACKEND=Agg python examples/stage3_optimization.py  # ACO path

# Animations
python examples/path_animation_only.py
python examples/complete_visualization.py
```

### Dashboard

```bash
.venv/bin/streamlit run streamlit_app.py  # http://localhost:8501
```

## Code Pattern: Complete Pipeline

```python
from src.data import create_field_with_rectangular_obstacles, FieldParameters
from src.geometry import generate_field_headland, generate_parallel_tracks
from src.obstacles.classifier import classify_all_obstacles, get_type_b_obstacles, get_type_d_obstacles
from src.decomposition import boustrophedon_decomposition, merge_blocks_by_criteria, cluster_tracks_into_blocks
from src.optimization import ACOParameters, ACOSolver, build_cost_matrix, generate_path_from_solution

# Create field
field = create_field_with_rectangular_obstacles(100, 80, [(x, y, w, h), ...], "Demo")
params = FieldParameters(operating_width=5.0, turning_radius=3.0, num_headland_passes=2,
                         driving_direction=0.0, obstacle_threshold=5.0)

# STAGE 1
headland = generate_field_headland(field.boundary_polygon, params.operating_width, params.num_headland_passes)
classified = classify_all_obstacles(field.obstacles, headland.inner_boundary, params.driving_direction,
                                    params.operating_width, params.obstacle_threshold)
type_b = get_type_b_obstacles(classified)
type_d = get_type_d_obstacles(classified)

# Regenerate headland with Type B obstacles
headland = generate_field_headland(field.boundary_polygon, params.operating_width, params.num_headland_passes,
                                   type_b_obstacles=[o.polygon for o in type_b])

# Generate global tracks (ignoring obstacles)
global_tracks = generate_parallel_tracks(headland.inner_boundary, params.driving_direction, params.operating_width)

# STAGE 2
prelim = boustrophedon_decomposition(headland.inner_boundary, [o.polygon for o in type_d], params.driving_direction)
blocks = merge_blocks_by_criteria(prelim, params.operating_width)
blocks = cluster_tracks_into_blocks(global_tracks, blocks)  # Cluster tracks into blocks

# STAGE 3
all_nodes = []
for block in blocks:
    all_nodes.extend(block.create_entry_exit_nodes(start_index=len(all_nodes)))

cost_matrix = build_cost_matrix(blocks, all_nodes)
solver = ACOSolver(blocks, all_nodes, cost_matrix, ACOParameters(num_ants=30, num_iterations=100))
solution = solver.solve(verbose=True)
path = generate_path_from_solution(solution, blocks, all_nodes)

print(f"Efficiency: {path.efficiency*100:.1f}%, Distance: {path.total_distance:.2f}m")
```

## Critical Constraints & Gotchas

### Node Indexing
```python
# Nodes indexed consecutively: Block 0→0-3, Block 1→4-7, Block 2→8-11
all_nodes = []
for block in blocks:
    nodes = block.create_entry_exit_nodes(start_index=len(all_nodes))  # CRITICAL: len(all_nodes)
    all_nodes.extend(nodes)
```

### Entry/Exit Parity
```python
# Valid: enter start → exit end (or different end)
first_start → first_end ✓  # Just first track
first_start → last_end ✓   # All tracks

# Invalid: cost=∞
first_start → first_start ✗  # Same node
first_start → last_start ✗   # Both starts
```

### Coordinate Rotation (Boustrophedon)
```python
# MUST rotate and rotate back
rotated = rotate_geometry(original, -driving_direction_degrees)
# ... process in rotated space ...
final = rotate_geometry(processed, +driving_direction_degrees)  # MUST rotate back
```

### Block Merging Adjacency
```python
# ONLY merge blocks that share a common edge (adjacency graph)
# Blocks are adjacent if: boundary1.intersection(boundary2).length > threshold
# Paper requirement (Section 2.3.1): "two connected blocks have a common edge"
```

### ACO Convergence Tuning
- **Converges too fast (<20 iters)**: ↑ `num_ants` or `num_iterations`
- **Poor quality (<70% eff)**: ↑ `beta=3.0`, ↓ `rho=0.05`, ↑ `num_ants=50`
- **Slow convergence (>100 iters)**: ↑ `alpha=1.5`, ↑ `rho=0.2`

### Testing Requirements
**Before committing:**
1. `pytest tests/ -v` → 92 passed
2. No new warnings
3. Visual check: `MPLBACKEND=Agg python examples/stage3_optimization.py`

## Project Structure

```
src/
├── data/                  # Field, Obstacle, Block, Track
├── geometry/              # Headland, Tracks, MBR, Polygon utils
├── obstacles/             # Obstacle classification (A/B/C/D)
├── decomposition/         # Boustrophedon, Block merging
├── optimization/          # ACO, Cost matrix, Path generation
├── visualization/         # Plotting, Animation
└── dashboard/             # Streamlit config, export

tests/                     # 92 comprehensive tests
scenarios/                 # Pre-configured JSON scenarios
examples/                  # Stage demos, animations
```

## Common Tasks

**Add test**: Choose file (test_aco.py, test_decomposition.py, etc.), use fixtures, run `pytest tests/test_file.py::test_name -v`

**Add ACO parameter**: Update `ACOParameters` dataclass, use in `ACOSolver.__init__`, add test, run `pytest tests/test_aco.py -v`

**Add scenario**: Create JSON in `scenarios/`, update `config_manager.py`, test with dashboard

**Modify algorithm**:
1. Identify affected stages (1→2&3, 2→3, 3=independent)
2. Make changes, update tests
3. Run affected tests, then full suite
4. Visual validation

**Debug test**: `pytest tests/test_file.py::test_name -v -s`, add debug prints, check fixtures

## Performance Expectations

- **Tests**: 92 in ~1s
- **Stages** (100×80m, 7 blocks): Stage 1 <0.5s, Stage 2 <0.2s, Stage 3 5-30s
- **ACO**: 2-3 blocks <2s, 5-10 blocks 2-10s, 10-20 blocks 5-30s
- **Quality**: 85-95% efficiency, 10-50% ACO improvement, 50-100 iter convergence
- **Memory**: <100 MB

## Academic Context

Course project (HK251) implementing Zhou et al. 2014 algorithm. Focus: **correctness > performance, clarity > optimization, reproducibility > speed**.

**Reference**: Zhou, K., et al. (2014). Agricultural operations planning in fields with multiple obstacle areas. *Computers and Electronics in Agriculture*, 109, 12-22. DOI: [10.1016/j.compag.2014.08.013](https://doi.org/10.1016/j.compag.2014.08.013)
