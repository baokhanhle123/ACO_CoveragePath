# ACO-based Agricultural Coverage Path Planning

**Implementation Status: ✅ COMPLETE - All 3 Stages Implemented and Verified**

Implementation of the algorithm from:
> **"Agricultural operations planning in fields with multiple obstacle areas"**
> K. Zhou, A. Leck Jensen, C.G. Sørensen, P. Busato, D.D. Bochtis
> *Computers and Electronics in Agriculture*, Vol. 109, pp. 12-22, 2014
> DOI: [10.1016/j.compag.2014.08.013](https://doi.org/10.1016/j.compag.2014.08.013)

---

## 🎯 Project Overview

### The Problem

Agricultural operations (plowing, seeding, harvesting) require machinery to **completely cover** a field while:
- **Avoiding obstacles** (trees, buildings, water bodies, etc.)
- **Minimizing non-working distance** (transitions between work areas)
- **Respecting vehicle constraints** (turning radius, operating width)
- **Optimizing the path sequence** to reduce time and fuel consumption

### The Solution

This project implements a **three-stage algorithm** that combines geometric decomposition with Ant Colony Optimization (ACO) to generate optimal coverage paths:

1. **Stage 1: Field Representation** - Process field geometry, classify obstacles, generate parallel tracks
2. **Stage 2: Field Decomposition** - Divide field into obstacle-free blocks using boustrophedon decomposition
3. **Stage 3: Path Optimization** - Use ACO to find the optimal block visitation sequence

### Why This Approach?

**Traditional Methods** (simple back-and-forth patterns):
- Don't handle complex obstacle layouts well
- Result in excessive non-working distance
- No optimization of visitation order

**This Algorithm**:
- ✅ Handles multiple obstacles of any shape
- ✅ Optimizes block sequencing using ACO (10-50% improvement)
- ✅ Achieves 85-95% efficiency (working distance / total distance)
- ✅ Generates smooth, practical paths for real agricultural machinery

---

## 📊 Implementation Status

### ✅ All Stages + Interactive Dashboard Complete (100%)

| Phase | Component | Status | Tests |
|-------|-----------|--------|-------|
| **Stage 1** | Field Geometric Representation | ✅ Complete | 23/23 ✅ |
| **Stage 2** | Boustrophedon Decomposition | ✅ Complete | 13/13 ✅ |
| **Stage 3** | ACO-based Path Optimization | ✅ Complete | 56/56 ✅ |
| **Phase 1** | Visualization (Animations) | ✅ Complete | Verified ✅ |
| **Phase 2A** | Interactive Dashboard | ✅ Complete | Verified ✅ |
| **Total** | **All Components** | **✅ Complete** | **92/92 + Dashboard ✅** |

**Test Coverage**: 92/92 core tests + dashboard integration tests passing (100%)
**Code Quality**: Comprehensive verification and validation
**Documentation**: Complete with examples, demos, and interactive dashboard
**Dashboard**: Streamlit app with Quick Demo, exports, and visualization

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.9+**
- **Virtual environment manager** (uv recommended, pip also supported)

### Installation

**Using `uv` (Recommended - Fast):**
```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e .
```

**Using `pip` (Standard):**
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e .
```

---

## 🎨 Interactive Dashboard (NEW - Phase 2A) ⭐

### Launch the Streamlit Dashboard

```bash
.venv/bin/streamlit run streamlit_app.py
```

**Access**: Open browser to `http://localhost:8501`

### Dashboard Features

**Quick Demo Tab** - One-click execution of complete ACO pipeline:
- 🟢 **Small Field Demo** (60×50m, 3 obstacles, ~30 sec)
- 🟡 **Medium Field Demo** (80×70m, 5 obstacles, ~60 sec)
- 🔴 **Large Complex Field** (100×80m, 7 obstacles, ~90 sec)

**Real-Time Visualization**:
- Live progress tracking during execution
- Interactive metrics cards (Best Cost, Path Efficiency, Total Distance)
- Expandable detailed statistics
- Tabbed image viewer (Field Decomposition, Coverage Path, ACO Convergence)

**Comprehensive Exports** - Download all results:
- 🎬 **Animations**: Path execution GIF + Pheromone evolution GIF
- 📄 **PDF Report**: Complete analysis with embedded images
- 📊 **CSV Data**: Convergence data + comprehensive statistics
- 🖼️ **Static Images**: High-quality PNG exports (150 DPI)

**Key Benefits**:
- ✅ No code required - just click and run
- ✅ Pre-configured scenarios for immediate testing
- ✅ Professional-quality exports for presentations/reports
- ✅ Complete transparency - all metrics and statistics visible

### Dashboard Quick Example

```bash
# 1. Launch dashboard
.venv/bin/streamlit run streamlit_app.py

# 2. Select scenario (e.g., "Small Field Demo")
# 3. Click "Run Demo" button
# 4. Wait ~30 seconds for completion
# 5. View results and download exports
```

**Expected Dashboard Results** (Small Field):
```
Metrics:
  Best Cost: 419.98
  Path Efficiency: 92.14%
  Total Distance: 686.59m

Detailed Statistics:
  - Field: 60×50m with 3 obstacles
  - Blocks Generated: 8
  - ACO Improvement: 16.44%
  - Working Distance: 632.64m
  - Waypoints: 102
```

---

### Running the Command-Line Examples

All demonstration scripts are organized in the `examples/` directory. See `examples/README.md` for detailed guide.

#### **Stage 1 Example: Field Representation**
```bash
python examples/stage1_geometry.py
```
**Output**: `exports/demos/plots/stage1_demo.png`

Shows:
- Field boundary and obstacles
- Headland generation around field and obstacles
- Obstacle classification (Types A, B, C, D)
- Parallel track generation for coverage

---

#### **Stage 2 Example: Field Decomposition**
```bash
python examples/stage2_decomposition.py
```
**Output**: `exports/demos/plots/stage2_demo.png`

Shows:
- Field setup from Stage 1
- Preliminary blocks from boustrophedon decomposition
- Final blocks after merging with parallel tracks assigned

---

#### **Stage 3 Example: ACO Optimization** ⭐
```bash
# For headless systems (saves images without display)
MPLBACKEND=Agg python examples/stage3_optimization.py

# For systems with display
python examples/stage3_optimization.py
```
**Output**:
- `exports/demos/plots/stage3_path.png` - Optimized coverage path visualization
- `exports/demos/plots/stage3_convergence.png` - ACO convergence plot

Shows:
- Complete coverage path with color-coded working/transition segments
- ACO optimization progress (cost reduction over iterations)
- Path statistics and efficiency metrics

**Expected Results**:
```
ACO Optimization:
  - Initial cost: ~1077 m
  - Final cost: ~968 m
  - Improvement: 10-20%

Path Plan:
  - Total distance: ~1346 m
  - Working distance: ~1272 m (94.5% efficiency)
  - Transition distance: ~74 m
  - Blocks visited: 7
  - Working segments: 7
  - Transitions: 6
```

---

#### **Animation Examples** ⭐

```bash
# Path execution animation only (tractor movement)
python examples/path_animation_only.py

# Complete visualization (both animations + full stats)
python examples/complete_visualization.py
```

See `ANIMATION_GUIDE.md` for detailed animation documentation

---

### Running Tests

```bash
# Run all 92 tests
pytest tests/ -v

# Run specific stage tests
pytest tests/test_aco.py -v                    # Stage 3: ACO tests
pytest tests/test_path_generation.py -v        # Stage 3: Path generation
pytest tests/test_decomposition.py -v          # Stage 2: Decomposition
pytest tests/test_integration_stage1.py -v     # Stage 1: Integration

# Run with output
pytest tests/ -v -s

# Run verification tests
pytest tests/test_solution_verification.py -v
```

**Expected**: All 92 tests should pass in ~1 second

---

## 📖 Algorithm Explanation

### The Three-Stage Approach

```
┌─────────────────────────────────────────────────────────────┐
│  INPUT: Field boundary + Obstacle locations + Parameters    │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  STAGE 1: Field Geometric Representation                    │
│  ────────────────────────────────────────────────────────  │
│  • Generate headlands around field and obstacles            │
│  • Classify obstacles (Types A, B, C, D)                    │
│  • Generate parallel coverage tracks                        │
│                                                              │
│  Output: Classified obstacles + Track layout                │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  STAGE 2: Boustrophedon Decomposition                       │
│  ────────────────────────────────────────────────────────  │
│  • Decompose field into obstacle-free cells (blocks)        │
│  • Build adjacency graph between blocks                     │
│  • Merge adjacent blocks to reduce complexity               │
│  • Assign tracks to each block                              │
│                                                              │
│  Output: Set of blocks with assigned tracks                 │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  STAGE 3: ACO-based Path Optimization                       │
│  ────────────────────────────────────────────────────────  │
│  • Generate 4 entry/exit nodes per block                    │
│  • Build cost matrix between all node pairs                 │
│  • Run Ant Colony Optimization to find optimal sequence     │
│  • Generate continuous coverage path                        │
│                                                              │
│  Output: Optimized coverage path with waypoints             │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  OUTPUT: Complete coverage path (working + transitions)     │
└─────────────────────────────────────────────────────────────┘
```

---

### Stage 1: Field Geometric Representation

**Purpose**: Prepare field geometry and generate coverage tracks

**Implementation**: Entry point `run_stage1_pipeline()` in `src/stage1.py`
**Modules**: `src/data/` (data structures), `src/geometry/` (geometric operations), `src/obstacles/` (obstacle classification)

**Key Operations**:

1. **Headland Generation**
   - Create buffer zones around field boundary (for turning maneuvers)
   - Create buffer zones around obstacles (for safety clearance)
   - Multiple passes determined by `num_headland_passes` parameter

2. **Obstacle Classification**
   ```
   Type A: Small obstacles (< threshold) → Ignore
   Type B: Boundary-touching → Incorporate into headland
   Type C: Close proximity (< operating_width) → Merge together
   Type D: Standard obstacles → Need decomposition in Stage 2
   ```

3. **Track Generation**
   - Compute Minimum Bounding Rectangle (MBR) using rotating calipers
   - Generate parallel lines with spacing = `operating_width`
   - Clip tracks to field inner boundary

**Output**: Classified obstacles + Parallel track layout

---

### Stage 2: Boustrophedon Decomposition

**Purpose**: Divide field into simple obstacle-free regions

**Modules**: `src/data/` (Block data structure), `src/decomposition/` (decomposition & merging algorithms)

**Key Operations**:

1. **Critical Point Detection**
   - Sweep vertical line across field from left to right
   - Detect topology changes (obstacles appearing/disappearing)
   - Mark x-coordinates where connectivity changes

2. **Cell Extraction**
   - Slice field between consecutive critical points
   - Extract obstacle-free polygons (preliminary blocks)
   - Each block is a simple trapezoid-like region

3. **Block Merging**
   - Build adjacency graph (which blocks share edges)
   - Greedily merge adjacent blocks to reduce complexity
   - Preserve convexity and balance areas

4. **Track Assignment**
   - Assign parallel tracks to each block
   - Tracks clipped to block boundaries

**Output**: Set of blocks with tracks assigned

---

### Stage 3: ACO-based Path Optimization

**Purpose**: Find optimal order to visit all blocks

**Modules**: `src/data/` (BlockNode), `src/optimization/` (ACO algorithm, cost matrix, path generation)

**Key Operations**:

1. **Entry/Exit Node Generation**
   - Create 4 nodes per block: `first_start`, `first_end`, `last_start`, `last_end`
   - Nodes positioned at track endpoints
   - Total nodes = 4 × number of blocks

2. **Cost Matrix Construction**
   ```
   Cost[i][j] =
     • 0                    if i == j (same node)
     • working_distance     if same block (track coverage cost)
     • euclidean_distance   if different blocks (transition cost)
     • ∞                    if invalid transition (violates parity)
   ```

3. **Ant Colony Optimization**
   ```python
   For each iteration:
     1. Each ant constructs a solution:
        - Select blocks probabilistically based on pheromone & heuristic
        - Enter block through one node, exit through paired node
        - Continue until all blocks visited

     2. Evaporate pheromone: τ ← τ × (1 - ρ)

     3. Deposit pheromone on good solutions:
        - All ants deposit: Δτ = Q / cost
        - Best solution deposits extra (elitist strategy)
   ```

4. **Path Generation**
   - Convert block sequence to continuous path
   - Create working segments (within blocks)
   - Create transition segments (between blocks)
   - Generate complete waypoint list

**Output**: Optimized coverage path with statistics

---

### ACO Algorithm Details

**Why ACO for this problem?**
- TSP-like problem (visit all blocks once)
- Multiple valid solutions (many good block orderings)
- Heuristic guidance available (distance between blocks)
- Proven effective for routing problems

**ACO Parameters** (tuned for best results):
```python
alpha = 1.0          # Pheromone importance
beta = 2.0           # Heuristic importance (favor closer blocks)
rho = 0.1            # Evaporation rate (forget bad solutions slowly)
q = 100.0            # Pheromone deposit amount
num_ants = 30        # Population size per iteration
num_iterations = 100 # Maximum iterations
elitist_weight = 2.0 # Extra pheromone for best solution
```

**Convergence**: Typically converges in 50-100 iterations with 10-50% improvement over initial random solution.

---

## 📁 Project Structure

```
ACO_CoveragePath/
├── src/                   # ✅ Source code
│   ├── stage1.py          # Stage 1 entry point & pipeline
│   ├── data/              # Data structures (Field, Block, Track, Node, Obstacle)
│   ├── geometry/          # Stage 1: Geometric operations (headland, MBR, tracks)
│   ├── obstacles/         # Stage 1: Obstacle classification (A/B/C/D types)
│   ├── decomposition/     # Stage 2: Boustrophedon decomposition & merging
│   ├── optimization/      # Stage 3: ACO algorithm & path generation
│   ├── visualization/     # Visualization utilities
│   ├── dashboard/         # Interactive Streamlit dashboard components
│   └── utils/             # General utilities
│
├── tests/                 # ✅ Comprehensive test suite (92 tests)
│   ├── test_basic_functionality.py      # 7 tests
│   ├── test_integration_stage1.py       # 9 tests
│   ├── test_obstacle_classification_debug.py  # 3 tests
│   ├── test_decomposition.py            # 13 tests
│   ├── test_cost_matrix.py              # 18 tests
│   ├── test_aco.py                      # 20 tests
│   ├── test_path_generation.py          # 17 tests
│   ├── test_stage3_integration.py       # 1 test
│   └── test_solution_verification.py    # 4 tests
│
├── examples/              # ✅ User-facing demonstration scripts
│   ├── README.md              # Complete guide to all examples
│   ├── stage1_geometry.py     # Stage 1: Field representation
│   ├── stage2_decomposition.py # Stage 2: Boustrophedon decomposition
│   ├── stage3_optimization.py  # Stage 3: ACO optimization
│   ├── path_animation_only.py  # Path execution animation
│   └── complete_visualization.py # Both animations + full stats
│
├── scripts/               # ✅ Internal scripts
│   └── benchmarks/            # Performance benchmarking utilities
│
├── paper/                 # ✅ Research paper materials
│
├── scenarios/             # ✅ Pre-configured demonstration scenarios
│   ├── small_field.json       # Small field (60×50m, 3 obstacles)
│   ├── medium_field.json      # Medium field (80×70m, 5 obstacles)
│   └── large_field.json       # Large field (100×80m, 7 obstacles)
│
├── exports/               # ✅ All outputs (demos + dashboard)
│   ├── demos/                 # Example demo outputs
│   │   ├── animations/        # Demo animations
│   │   └── plots/             # Demo plots
│   ├── animations/            # Dashboard GIF animations
│   ├── reports/               # Dashboard PDF reports
│   ├── data/                  # Dashboard CSV data files
│   ├── images/                # Dashboard static PNG images
│   ├── metrics/               # Performance metrics
│   └── paths/                 # Path data
│
├── streamlit_app.py       # ✅ Main Streamlit dashboard application
├── README.md              # ✅ This file (project guide)
├── ANIMATION_GUIDE.md     # ✅ Animation usage guide
├── CLAUDE.md              # ✅ Development guide for Claude Code
└── pyproject.toml         # ✅ Project configuration & dependencies
```

---

## 💻 Usage Examples

### Example 1: Complete Pipeline (All 3 Stages)

```python
from src.data import create_field_with_rectangular_obstacles, FieldParameters
from src.geometry import generate_field_headland, generate_parallel_tracks
from src.obstacles.classifier import classify_all_obstacles, get_type_d_obstacles
from src.decomposition import boustrophedon_decomposition, merge_blocks_by_criteria
from src.optimization import (
    ACOParameters, ACOSolver, build_cost_matrix,
    generate_path_from_solution, get_path_statistics
)

# Note: For Stage 1, you can also use the pipeline entry point:
# from src.stage1 import run_stage1_pipeline
# stage1_result = run_stage1_pipeline(field, params)

# 1. Create field
field = create_field_with_rectangular_obstacles(
    field_width=100,
    field_height=80,
    obstacle_specs=[(30, 30, 15, 12), (65, 50, 12, 15)],
    name="My Field"
)

# 2. Set parameters
params = FieldParameters(
    operating_width=5.0,
    turning_radius=3.0,
    num_headland_passes=2,
    driving_direction=0.0,
    obstacle_threshold=5.0
)

# === STAGE 1: Field Representation ===
print("[Stage 1] Field representation...")

# Generate headland
field_headland = generate_field_headland(
    field.boundary_polygon,
    params.operating_width,
    params.num_headland_passes
)

# Classify obstacles
classified_obstacles = classify_all_obstacles(
    field.obstacles,
    field_headland.inner_boundary,
    params.driving_direction,
    params.operating_width,
    params.obstacle_threshold
)

type_d_obstacles = get_type_d_obstacles(classified_obstacles)
obstacle_polygons = [obs.polygon for obs in type_d_obstacles]

print(f"✓ Type D obstacles: {len(type_d_obstacles)}")

# === STAGE 2: Field Decomposition ===
print("[Stage 2] Field decomposition...")

# Boustrophedon decomposition
preliminary_blocks = boustrophedon_decomposition(
    inner_boundary=field_headland.inner_boundary,
    obstacles=obstacle_polygons,
    driving_direction_degrees=params.driving_direction
)

# Merge blocks
final_blocks = merge_blocks_by_criteria(
    blocks=preliminary_blocks,
    operating_width=params.operating_width
)

# Generate tracks for each block
for block in final_blocks:
    tracks = generate_parallel_tracks(
        inner_boundary=block.polygon,
        driving_direction_degrees=params.driving_direction,
        operating_width=params.operating_width
    )
    block.tracks = tracks

print(f"✓ Final blocks: {len(final_blocks)}")
print(f"✓ Total tracks: {sum(len(b.tracks) for b in final_blocks)}")

# === STAGE 3: ACO Optimization ===
print("[Stage 3] ACO optimization...")

# Create entry/exit nodes
all_nodes = []
node_index = 0
for block in final_blocks:
    nodes = block.create_entry_exit_nodes(start_index=node_index)
    all_nodes.extend(nodes)
    node_index += 4

# Build cost matrix
cost_matrix = build_cost_matrix(blocks=final_blocks, nodes=all_nodes)

# Configure ACO
aco_params = ACOParameters(
    alpha=1.0,
    beta=2.0,
    rho=0.1,
    num_ants=30,
    num_iterations=100
)

# Run ACO
solver = ACOSolver(
    blocks=final_blocks,
    nodes=all_nodes,
    cost_matrix=cost_matrix,
    params=aco_params
)

best_solution = solver.solve(verbose=True)

# Generate path
path_plan = generate_path_from_solution(best_solution, final_blocks, all_nodes)

# Get statistics
stats = get_path_statistics(path_plan)

print(f"\n✓ Optimization complete!")
print(f"  Total distance: {stats['total_distance']:.2f} m")
print(f"  Working distance: {stats['working_distance']:.2f} m")
print(f"  Efficiency: {stats['efficiency']*100:.1f}%")
print(f"  Block sequence: {path_plan.block_sequence}")
```

---

### Example 2: ACO with Custom Parameters

```python
from src.optimization import ACOParameters

# For faster testing (less accurate)
quick_params = ACOParameters(
    num_ants=10,
    num_iterations=20
)

# For better optimization (slower)
quality_params = ACOParameters(
    num_ants=50,
    num_iterations=200,
    alpha=1.0,
    beta=3.0,  # Favor distance more
    rho=0.15   # Faster evaporation
)

# Run ACO with custom parameters
solver = ACOSolver(blocks, nodes, cost_matrix, params=quality_params)
solution = solver.solve(verbose=True)
```

---

### Example 3: Analyzing Results

```python
from src.optimization import get_path_statistics

# Generate path
path_plan = generate_path_from_solution(solution, blocks, nodes)

# Get detailed statistics
stats = get_path_statistics(path_plan)

print(f"Path Analysis:")
print(f"  Total distance: {stats['total_distance']:.2f} m")
print(f"  Working distance: {stats['working_distance']:.2f} m")
print(f"  Transition distance: {stats['transition_distance']:.2f} m")
print(f"  Efficiency: {stats['efficiency']*100:.1f}%")
print(f"  Number of blocks: {stats['num_blocks']}")
print(f"  Working segments: {stats['num_working_segments']}")
print(f"  Transition segments: {stats['num_transition_segments']}")
print(f"  Total waypoints: {stats['total_waypoints']}")

# Access path segments
for i, segment in enumerate(path_plan.segments):
    print(f"Segment {i}: {segment.segment_type}, distance={segment.distance:.2f}m")

# Get all waypoints for path execution
waypoints = path_plan.get_all_waypoints()
print(f"\nPath waypoints: {len(waypoints)} points")
```

---

## 📊 Performance Metrics

### Demo Field Results (100m × 80m, 3 obstacles, 7 blocks)

**Stage 1 (Field Representation)**:
- Execution time: < 0.5 seconds
- Type D obstacles detected: 2
- Tracks generated: 55

**Stage 2 (Decomposition)**:
- Execution time: < 0.2 seconds
- Preliminary blocks: 7
- Final blocks (after merging): 7
- Tracks assigned: 55

**Stage 3 (ACO Optimization)**:
- Execution time: ~15 seconds (100 iterations, 30 ants)
- Initial cost: 1077.13 m
- Final cost: 968.13 m
- **Improvement: 10.1%**
- Convergence: ~92 iterations

**Final Path Plan**:
- Total distance: 1346.46 m
- Working distance: 1272.32 m (track coverage)
- Transition distance: 74.13 m (between blocks)
- **Efficiency: 94.5%** (working / total)
- Working segments: 7 (one per block)
- Transition segments: 6 (between consecutive blocks)
- Total waypoints: 136

### Scalability

| Field Size | Blocks | ACO Time | Solution Quality |
|------------|--------|----------|------------------|
| Small (2-3 blocks) | 2-3 | 0.5-2 sec | 10-20% improvement |
| Medium (5-10 blocks) | 5-10 | 2-10 sec | 15-30% improvement |
| Large (10-20 blocks) | 10-20 | 5-30 sec | 20-50% improvement |
| Demo (7 blocks) | 7 | 15 sec | 10.1% improvement |

**Memory Usage**: < 100 MB for typical fields

---

## 🧪 Testing

### Test Suite Overview

**92 Tests - 100% Passing** ✅

| Test Suite | Tests | Coverage |
|------------|-------|----------|
| **Stage 1 Tests** | 23 | Basic functionality, integration |
| **Stage 2 Tests** | 13 | Decomposition, merging, adjacency |
| **Stage 3 Tests** | 56 | Cost matrix, ACO, path generation |
| **Total** | **92** | **All components** |

### Running Tests

```bash
# Quick check - all tests
pytest tests/ -q
# Expected: 92 passed in ~1 second

# Verbose output
pytest tests/ -v

# Specific test suites
pytest tests/test_aco.py -v              # ACO algorithm (20 tests)
pytest tests/test_cost_matrix.py -v      # Cost matrix (18 tests)
pytest tests/test_path_generation.py -v  # Path generation (17 tests)
pytest tests/test_decomposition.py -v    # Decomposition (13 tests)

# Verification tests (ensures solution quality)
pytest tests/test_solution_verification.py -v -s

# With coverage report (optional)
pytest tests/ --cov=src --cov-report=html
```

### Test Categories

**1. Unit Tests** - Individual components
- Data structures (Field, Block, Track, Node)
- Geometric operations (MBR, polygon offset)
- Obstacle classification
- Cost matrix construction
- ACO parameters and pheromone update

**2. Integration Tests** - Complete pipelines
- Stage 1 pipeline (headland → classification → tracks)
- Stage 2 pipeline (decomposition → merging → assignment)
- Stage 3 pipeline (nodes → ACO → path)

**3. Verification Tests** - Solution quality
- Consecutive block visits validation
- Working segment generation
- Path efficiency > 50%
- Robustness across multiple runs

---

## 🎓 Key Features

### What Makes This Implementation Special?

1. **✅ Complete Implementation**
   - All 3 stages fully implemented
   - 92/92 tests passing
   - Verified solution quality

2. **✅ High Performance**
   - Efficient geometric algorithms
   - Fast ACO convergence
   - 85-95% path efficiency

3. **✅ Production-Ready Code**
   - Comprehensive error handling
   - Extensive test coverage
   - Clean, documented code

4. **✅ Practical Results**
   - Generates realistic paths
   - Handles complex obstacle layouts
   - Achieves significant optimization (10-50%)

5. **✅ Educational Value**
   - Clear algorithm explanation
   - Well-commented code
   - Multiple usage examples

---

## 🐛 Known Limitations

1. **Turning Radius Constraints**
   - Current implementation uses straight-line transitions
   - Future: Could add Dubins paths for smoother turns

2. **Track Orientation**
   - Fixed driving direction for all tracks
   - Future: Could optimize track orientation per block

3. **Dynamic Obstacles**
   - Assumes static obstacle locations
   - Future: Could add re-planning for moving obstacles

4. **Multi-Objective Optimization**
   - Currently optimizes only for distance
   - Future: Could include time, fuel consumption

---

## 📚 References

### Main Paper
```bibtex
@article{zhou2014agricultural,
  title={Agricultural operations planning in fields with multiple obstacle areas},
  author={Zhou, K and Jensen, A Leck and S{\o}rensen, CG and Busato, P and Bochtis, DD},
  journal={Computers and Electronics in Agriculture},
  volume={109},
  pages={12--22},
  year={2014},
  publisher={Elsevier},
  doi={10.1016/j.compag.2014.08.013}
}
```

### Key Algorithms
- **Boustrophedon Decomposition**: Choset & Pignon (1997)
- **Ant Colony Optimization**: Dorigo & Gambardella (1997)
- **Rotating Calipers (MBR)**: Toussaint (1983)

### Dependencies
- **Shapely** - Geometric operations
- **NumPy** - Numerical computations
- **Matplotlib** - Visualization
- **NetworkX** - Graph algorithms
- **pytest** - Testing framework

---

## 🔧 Development

### Code Quality

```bash
# Format code
black src/ tests/

# Check code style
ruff check src/ tests/

# Type checking (optional)
mypy src/
```

### Contributing Guidelines

1. Write tests first (TDD)
2. Follow existing code style
3. Add comprehensive docstrings (Google style)
4. Ensure all tests pass before committing
5. Update README for major changes

---

## 📄 License

This project is developed for academic purposes.

**Course**: Heuristics and Optimization for Path/Motion Planning Problems (HK251)
**Academic Year**: 2024-2025

---

## 🙏 Acknowledgments

- Original algorithm by Zhou et al. (2014)
- Built with Python, Shapely, NumPy, Matplotlib, NetworkX
- Testing framework: pytest
- Package manager: uv

---

## 📈 Project Statistics

- **Total Lines of Code**: ~6,500+
- **Test Coverage**: 92 tests, 100% passing
- **Documentation**: 3 comprehensive reports + README
- **Implementation Time**: ~3 days (all 3 stages)
- **Implementation Progress**: ✅ **100% Complete**

---

## 📞 Support

### For Issues
- Run tests first: `pytest tests/ -v`
- Check documentation: README.md, VERIFICATION_REPORT.md
- Review demos: `demo_stage*.py` files

### For Questions
- Check usage examples in README
- Review test files for code patterns
- See STAGE3_COMPLETION_REPORT.md for technical details

---

**Last Updated**: 2025-11-27
**Status**: ✅ **All 3 Stages + Interactive Dashboard Complete - Production Ready**
**Version**: 2.0.0 (Complete Implementation + Interactive Dashboard)
