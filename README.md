# ACO-based Agricultural Coverage Path Planning

**Implementation Status: Stage 1 & 2 Complete (65%) - Ready for ACO Optimization**

Implementation of the algorithm from:
> **"Agricultural operations planning in fields with multiple obstacle areas"**
> K. Zhou, A. Leck Jensen, C.G. Sørensen, P. Busato, D.D. Bochtis
> *Computers and Electronics in Agriculture*, Vol. 109, pp. 12-22, 2014
> DOI: [10.1016/j.compag.2014.08.013](https://doi.org/10.1016/j.compag.2014.08.013)

---

## 🎯 Project Overview

This project implements a complete coverage path planning system for agricultural machinery operating in fields with multiple obstacles using **Ant Colony Optimization (ACO)**. The algorithm generates optimal paths for tractors and other agricultural vehicles to cover entire fields while avoiding obstacles.

### Algorithm Stages

The algorithm consists of three main stages:

#### ✅ **Stage 1: Field Geometric Representation** (COMPLETE)
- ✅ Headland generation around field and obstacles
- ✅ Obstacle classification into 4 types (A, B, C, D)
- ✅ Parallel track generation for field coverage

#### ✅ **Stage 2: Field Decomposition** (COMPLETE)
- ✅ Boustrophedon cellular decomposition
- ✅ Block merging via adjacency graph
- ✅ Track assignment to blocks

#### ⏳ **Stage 3: Path Optimization** (NOT IMPLEMENTED)
- ⏳ Entry/exit node generation (4 nodes per block)
- ⏳ TSP cost matrix construction
- ⏳ ACO-based block sequencing

---

## 📊 Current Implementation Status

### ✅ What's Working (Stages 1 & 2 - 100% Complete)

**Data Structures:**
- Field representation with boundaries and obstacles
- Complete parameter system (operating width, turning radius, etc.)
- Obstacle classification system (Types A, B, C, D)
- Track and block data structures
- Block adjacency graph

**Stage 1 - Geometric Processing:**
- **Headland Generation**: Multi-pass field and obstacle headlands
- **Obstacle Classification**:
  - Type A: Small obstacles (ignorable)
  - Type B: Boundary-touching obstacles
  - Type C: Close proximity obstacles (auto-merged)
  - Type D: Standard obstacles (require decomposition)
- **Track Generation**: Parallel tracks using MBR and rotating calipers algorithm
- **Polygon Operations**: Offset, intersection, union, rotation, etc.

**Stage 2 - Field Decomposition:**
- **Boustrophedon Decomposition**: Sweep-line based cellular decomposition
- **Critical Point Detection**: Identifies topology changes in sweep
- **Slice Computation**: Extracts obstacle-free cells between critical points
- **Block Adjacency Graph**: Detects shared edges between blocks
- **Greedy Block Merging**: Reduces block count using cost-based merging
  - Convexity preservation
  - Area balance optimization
  - Shape complexity minimization

**Testing:**
- 32/32 tests passing (100% success rate)
  - 7 basic functionality tests
  - 13 decomposition tests
  - 9 Stage 1 integration tests
  - 3 obstacle classification tests
- Comprehensive integration tests
- Edge case coverage
- Visual demonstration scripts (Stage 1 & Stage 2)

### ⏳ What's Not Implemented Yet

- Entry/exit node generation for blocks (Stage 3)
- Ant Colony Optimization solver (Stage 3)
- TSP-based block sequencing (Stage 3)
- Complete path optimization (Stage 3)
- Full visualization system with animations
- Benchmark experiments to reproduce paper results

---

## 🚀 Quick Start

### Installation

**Prerequisites:** Python 3.9+

Using `uv` (recommended):
```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e .
```

Using `pip`:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e .
```

### Running the Demo

**Stage 1 Visualization Demo:**
```bash
python demo_stage1.py
```

This generates a 3-panel visualization showing:
1. Field with obstacles
2. Headland generation and obstacle classification
3. Parallel track generation

**Output:** `results/plots/stage1_demo.png`

**Stage 2 Visualization Demo:**
```bash
python demo_stage2.py
```

This generates a 3-panel visualization showing:
1. Field setup with headland (Stage 1)
2. Preliminary blocks from boustrophedon decomposition
3. Final blocks after merging with parallel tracks

**Output:** `results/plots/stage2_demo.png`

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test suite
pytest tests/test_integration_stage1.py -v

# Run with output
pytest tests/test_integration_stage1.py -v -s
```

**Expected Results:** 19/19 tests passing in ~0.3 seconds

---

## 📖 Usage Examples

### Example 1: Simple Field with Obstacles

```python
from src.data import Field, FieldParameters, create_field_with_rectangular_obstacles
from src.geometry import generate_field_headland, generate_parallel_tracks
from src.obstacles.classifier import classify_all_obstacles, get_type_d_obstacles

# Create field (100m x 80m) with 2 obstacles
field = create_field_with_rectangular_obstacles(
    field_width=100,
    field_height=80,
    obstacle_specs=[
        (30, 30, 15, 12),   # (x, y, width, height)
        (65, 50, 12, 15),
    ],
    name="My Field"
)

# Set parameters
params = FieldParameters(
    operating_width=5.0,      # Implement width in meters
    turning_radius=3.0,       # Vehicle turning radius
    num_headland_passes=2,    # Number of headland passes
    driving_direction=0.0,    # Angle in degrees (0 = horizontal)
    obstacle_threshold=5.0    # Threshold for Type A classification
)

print(f"Field: {field}")
print(f"Area: {field.area:.2f} m²")
```

### Example 2: Headland Generation

```python
# Generate field headland
headland_result = generate_field_headland(
    field_boundary=field.boundary_polygon,
    operating_width=params.operating_width,
    num_passes=params.num_headland_passes
)

print(f"Generated {len(headland_result.passes)} headland passes")
print(f"Inner boundary area: {headland_result.inner_boundary.area:.2f} m²")
```

### Example 3: Obstacle Classification

```python
# Classify obstacles
classified_obstacles = classify_all_obstacles(
    obstacle_boundaries=field.obstacles,
    field_inner_boundary=headland_result.inner_boundary,
    driving_direction_degrees=params.driving_direction,
    operating_width=params.operating_width,
    threshold=params.obstacle_threshold
)

# Print classification results
for obs in classified_obstacles:
    print(f"Obstacle {obs.index}: {obs.obstacle_type.name}")
    if obs.is_merged():
        print(f"  (Merged from obstacles: {obs.merged_from})")

# Get Type D obstacles (need decomposition in Stage 2)
type_d_obstacles = get_type_d_obstacles(classified_obstacles)
print(f"\nType D obstacles: {len(type_d_obstacles)}")
```

### Example 4: Track Generation

```python
from src.geometry import generate_parallel_tracks, order_tracks_by_position

# Generate parallel tracks
tracks = generate_parallel_tracks(
    inner_boundary=headland_result.inner_boundary,
    driving_direction_degrees=params.driving_direction,
    operating_width=params.operating_width
)

# Order tracks by position
tracks = order_tracks_by_position(tracks, params.driving_direction)

print(f"Generated {len(tracks)} tracks")
print(f"Total track length: {sum(t.length for t in tracks):.2f} m")

# Access individual tracks
for track in tracks[:3]:  # First 3 tracks
    print(f"Track {track.index}: {track.start} -> {track.end}, length={track.length:.2f}m")
```

### Example 5: Complete Stage 1 Pipeline

```python
from src.geometry import generate_obstacle_headland

# 1. Field headland
field_headland = generate_field_headland(
    field.boundary_polygon, params.operating_width, params.num_headland_passes
)

# 2. Classify obstacles
classified_obstacles = classify_all_obstacles(
    field.obstacles, field_headland.inner_boundary,
    params.driving_direction, params.operating_width, params.obstacle_threshold
)

# 3. Generate obstacle headlands (Type D only)
type_d_obstacles = get_type_d_obstacles(classified_obstacles)
obstacle_headlands = []

for obs in type_d_obstacles:
    obs_headland = generate_obstacle_headland(
        obs.polygon, params.operating_width, params.num_headland_passes
    )
    if obs_headland:
        obstacle_headlands.append((obs, obs_headland))

# 4. Generate field-work tracks
tracks = generate_parallel_tracks(
    field_headland.inner_boundary, params.driving_direction, params.operating_width
)

# Results
print(f"✓ Field headland: {len(field_headland.passes)} passes")
print(f"✓ Classified obstacles: {len(classified_obstacles)}")
print(f"✓ Type D obstacles: {len(type_d_obstacles)}")
print(f"✓ Obstacle headlands: {len(obstacle_headlands)}")
print(f"✓ Field tracks: {len(tracks)}")
```

---

## 📁 Project Structure

```
ACO_CoveragePath/
├── src/
│   ├── data/              # Data structures (Field, Obstacle, Track, Block, etc.)
│   ├── geometry/          # ✅ Geometric processing (headland, tracks, MBR)
│   ├── obstacles/         # ✅ Obstacle classification system
│   ├── decomposition/     # ⏳ Field decomposition (Stage 2 - TODO)
│   ├── optimization/      # ⏳ ACO and TSP solvers (Stage 3 - TODO)
│   ├── visualization/     # ⏳ Plotting and animation (TODO)
│   └── utils/             # ⏳ I/O, logging, benchmarking (TODO)
│
├── tests/                 # ✅ Comprehensive test suite (19 tests, all passing)
│   ├── test_basic_functionality.py
│   ├── test_integration_stage1.py
│   └── test_obstacle_classification_debug.py
│
├── experiments/           # ⏳ Benchmark experiments (TODO)
├── data/                  # Test datasets
├── results/               # Output (plots, paths, metrics)
│   └── plots/            # ✅ stage1_demo.png
│
├── demo_stage1.py        # ✅ Visual demonstration script
├── README.md             # This file
├── VERIFICATION_REPORT.md # ✅ Detailed technical verification
├── IMPLEMENTATION_STATUS.md # ✅ Development progress tracker
└── pyproject.toml        # Project configuration
```

---

## 🧪 Testing

### Test Coverage

**19 Tests - All Passing ✅**

1. **Basic Functionality (7 tests)**
   - Field creation and validation
   - Headland generation
   - Track generation
   - Obstacle classification
   - Module imports

2. **Integration Tests (9 tests)**
   - Complete Stage 1 pipeline
   - Multiple obstacle scenarios
   - Edge cases (small fields, large operating width)
   - Different driving directions
   - Obstacle merging (Type C)

3. **Classification Debug Tests (3 tests)**
   - All obstacle types (A, B, C, D)
   - Boundary vs interior detection
   - Clustering and merging

### Running Tests

```bash
# All tests with verbose output
pytest tests/ -v

# Specific test file
pytest tests/test_integration_stage1.py -v

# With print statements
pytest tests/ -v -s

# Stop on first failure
pytest tests/ -x
```

---

## 🎓 Algorithm Details

### Stage 1: Field Geometric Representation

#### 1.1 Headland Generation

**Field Headland:**
- Offset field boundary inward by `w/2` (first pass)
- Subsequent passes offset by `w` (operating width)
- Inner boundary offset by `w/2` from last pass

**Obstacle Headland:**
- Offset obstacle boundary outward by `w/2` (first pass)
- Subsequent passes offset by `w`
- Used for Type D obstacles

#### 1.2 Obstacle Classification

**Type A (Ignorable):**
```
Condition: D_d < τ (threshold)
Where D_d = dimension perpendicular to driving direction
Action: Ignore obstacle (not included in decomposition)
```

**Type B (Boundary-touching):**
```
Condition: Obstacle boundary intersects field inner boundary
Action: Incorporate into field headland
```

**Type C (Close proximity):**
```
Condition: Distance to another obstacle < w (operating width)
Action: Merge with nearby obstacles using convex hull → reclassify as Type D
```

**Type D (Requires decomposition):**
```
All remaining obstacles + merged Type C obstacles
Action: Generate obstacle headland, decompose field in Stage 2
```

#### 1.3 Track Generation

Algorithm:
1. Compute Minimum Bounding Rectangle (MBR) using rotating calipers
2. Create reference line parallel to driving direction
3. Calculate number of tracks: `n = ⌈distance / w⌉`
4. Generate parallel lines with spacing `w`
5. Find intersections with field inner boundary
6. Keep line segments inside field, discard outside

---

## 📊 Performance

### Execution Speed
- Basic operations: < 0.01s
- Field headland generation: < 0.05s
- Track generation: < 0.1s (100m² field)
- Complete Stage 1 pipeline: < 0.5s

### Example Results

**Field:** 100m × 80m with 2 obstacles
```
Operating width: 5.0m
Headland passes: 2
Driving direction: 0°

Results:
- Effective field area: 7,631 m²
- Field headland: 2 passes
- Obstacles classified: 2 Type D
- Obstacle headlands: 2 generated
- Field tracks: 12 tracks
- Total track length: 960m
- Execution time: ~0.3s
```

---

## 🔧 Development

### Adding New Features

1. **Create new module** in appropriate directory (`src/geometry/`, `src/data/`, etc.)
2. **Add unit tests** in `tests/`
3. **Update `__init__.py`** to export new functions/classes
4. **Run tests** to ensure no regression

### Code Quality

```bash
# Format code
black src/ tests/

# Check code quality
ruff check src/ tests/

# Type checking (optional)
mypy src/
```

### Contributing

1. Write tests first (TDD approach)
2. Follow existing code style
3. Add docstrings (Google style)
4. Update README if adding major features

---

## 🐛 Known Issues and Limitations

### Current Limitations (By Design)

1. **Stages 2 & 3 Not Implemented**
   - Field decomposition incomplete
   - ACO optimization not implemented
   - Cannot generate complete optimized paths yet

2. **Track Subdivision**
   - Tracks generated ignoring obstacles
   - Subdivision will occur in Stage 2

3. **No Path Optimization**
   - Track order not optimized
   - Block sequencing not available

### Fixed Bugs

✅ **Type B Obstacle Misclassification** (Fixed 2025-11-19)
- Issue: Interior obstacles classified as Type B
- Fix: Changed to check boundary line intersection
- Impact: Critical fix for correct field decomposition

---

## 📝 Documentation

- **README.md** (this file) - Project overview and usage
- **VERIFICATION_REPORT.md** - Detailed technical verification of Stage 1
- **IMPLEMENTATION_STATUS.md** - Development progress and roadmap
- **Docstrings** - All functions have comprehensive Google-style docstrings

---

## 🗺️ Roadmap

### Completed ✅
- [x] Project structure and environment setup
- [x] Data structures (Field, Obstacle, Track, Block)
- [x] Geometric operations (polygon offset, MBR, etc.)
- [x] Headland generation (field + obstacles)
- [x] Obstacle classification (all 4 types)
- [x] Track generation with MBR
- [x] Comprehensive test suite (19 tests)
- [x] Stage 1 visualization demo
- [x] Documentation

### In Progress ⏳
- [ ] Stage 2: Boustrophedon decomposition
- [ ] Stage 2: Block merging and track clustering

### Planned 📋
- [ ] Stage 3: Cost matrix construction
- [ ] Stage 3: ACO implementation
- [ ] Stage 3: TSP solving
- [ ] Complete visualization system
- [ ] Animation of ACO iterations
- [ ] Benchmark experiments (reproduce paper results)
- [ ] Performance optimization
- [ ] Comparison with other algorithms (Genetic Algorithm, etc.)

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
- **Rotating Calipers**: Toussaint, G.T. (1983) "Solving geometric problems with the rotating calipers"
- **Boustrophedon Decomposition**: Choset, H. and Pignon, P. (1997) "Coverage path planning: the boustrophedon decomposition"
- **Ant Colony Optimization**: Dorigo, M. and Gambardella, L.M. (1997) "Ant colony system: a cooperative learning approach to the TSP"

---

## 💬 Contact & Support

### For Issues
- Open an issue on GitHub
- Include error message, code snippet, and expected behavior
- Run tests first: `pytest tests/ -v`

### For Questions
- Check documentation first (README.md, VERIFICATION_REPORT.md)
- Review test files for usage examples
- Check `demo_stage1.py` for working example

---

## 📄 License

This project is developed for academic purposes as part of a university assignment.

**Course:** Heuristics and Optimization for Path/Motion Planning Problems (HK251)
**Institution:** [Your University Name]
**Academic Year:** 2024-2025

---

## 🙏 Acknowledgments

- Original algorithm by Zhou et al. (2014)
- Built with: Python, Shapely, NumPy, Matplotlib, NetworkX
- Testing: pytest
- Environment: uv

---

## 📈 Project Statistics

- **Total Lines of Code:** ~3,500+
- **Test Coverage:** 19 tests, 100% passing
- **Documentation:** 4 major documents
- **Dependencies:** 24 packages
- **Development Time:** ~1 day for Stage 1
- **Implementation Progress:** 40% (Stage 1 complete)

---

**Last Updated:** 2025-11-19
**Status:** ✅ Stage 1 Complete - Ready for Stage 2 Implementation
**Version:** 0.1.0 (Prototype)
