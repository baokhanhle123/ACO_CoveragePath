# Examples - ACO Coverage Path Planning

This directory contains demonstration scripts showing how to use the ACO Coverage Path Planning system.

## Quick Start

All examples can be run from the project root directory:

```bash
# Activate virtual environment
source .venv/bin/activate

# Run any example
python examples/<script_name>.py
```

---

## Available Examples

### 1. Complete Visualization (`complete_visualization.py`)

**Purpose**: Comprehensive demo showing ALL visualization capabilities

**Features**:
- Path execution animation (tractor movement)
- Pheromone evolution animation (ACO learning process)
- Convergence plots
- Complete statistics

**Output**:
- `animations/demo_path_execution.gif`
- `animations/demo_pheromone_evolution.gif`
- Console statistics

**Run**:
```bash
MPLBACKEND=Agg python examples/complete_visualization.py
```

**Use for**: Class presentations, comprehensive demonstrations

---

### 2. Path Animation Only (`path_animation_only.py`)

**Purpose**: Focus on path execution animation

**Features**:
- Tractor movement with rotation
- Coverage trail visualization
- Real-time progress bar
- Statistics overlay

**Output**:
- Animated GIF/MP4 of tractor moving along path

**Run**:
```bash
MPLBACKEND=Agg python examples/path_animation_only.py
```

**Use for**: Showcasing final coverage path

---

### 3. Stage 1: Geometry (`stage1_geometry.py`)

**Purpose**: Demonstrate field geometric representation (Stage 1)

**Features**:
- Headland generation
- Obstacle classification (Types A, B, C, D)
- Parallel track generation using MBR
- Visualization of geometric preprocessing

**Output**:
- `exports/demos/plots/stage1_demo.png`

**Run**:
```bash
python examples/stage1_geometry.py
```

**Use for**: Understanding geometric preprocessing and obstacle handling

---

### 4. Stage 2: Decomposition (`stage2_decomposition.py`)

**Purpose**: Demonstrate boustrophedon decomposition (Stage 2)

**Features**:
- Critical point identification
- Vertical sweep line algorithm
- Block merging strategies
- Adjacency graph construction

**Output**:
- `exports/demos/plots/stage2_demo.png`
- Console output with block statistics

**Run**:
```bash
python examples/stage2_decomposition.py
```

**Use for**: Understanding field decomposition algorithm

---

### 5. Stage 3: Optimization (`stage3_optimization.py`)

**Purpose**: Demonstrate ACO-based path optimization (Stage 3)

**Features**:
- Entry/exit node generation
- Cost matrix construction
- ACO algorithm execution
- Convergence analysis

**Outputs**:
- `exports/demos/plots/stage3_path.png`
- `exports/demos/plots/stage3_convergence.png`
- Console statistics

**Run**:
```bash
MPLBACKEND=Agg python examples/stage3_optimization.py
```

**Use for**: Understanding ACO optimization process

---

## Common Usage Patterns

### Running with Headless Backend

For SSH sessions or servers without display:

```bash
MPLBACKEND=Agg python examples/<script>.py
```

### Customizing Field Parameters

All examples use `FieldParameters` to configure the system. Edit the script to change:

```python
params = FieldParameters(
    operating_width=5.0,      # Vehicle width
    turning_radius=3.0,       # Minimum turning radius
    num_headland_passes=2,    # Headland passes
    driving_direction=0.0,    # 0° = horizontal
    obstacle_threshold=5.0    # Obstacle classification threshold
)
```

### Creating Custom Fields

Use the field creation utilities:

```python
from src.data import create_field_with_rectangular_obstacles

field = create_field_with_rectangular_obstacles(
    field_width=100,
    field_height=80,
    obstacle_specs=[
        (x1, y1, width1, height1),  # Obstacle 1
        (x2, y2, width2, height2),  # Obstacle 2
    ],
    name="My Custom Field"
)
```

---

## Output Locations

All examples save output to organized directories:

- **Animations**: `results/animations/` or `exports/animations/`
- **Plots**: `results/plots/`
- **Metrics**: `results/metrics/`
- **Data**: `exports/data/`

---

## Troubleshooting

### "ModuleNotFoundError"

Ensure you're using the virtual environment:

```bash
source .venv/bin/activate
python examples/<script>.py
```

### Animation Takes Too Long

Reduce field size or ACO iterations in the script:

```python
aco_params = ACOParameters(
    num_ants=10,           # Reduce from 30
    num_iterations=20      # Reduce from 100
)
```

### "Display not found" Error

Use headless backend:

```bash
MPLBACKEND=Agg python examples/<script>.py
```

---

## For Developers

If you're modifying the examples:

1. **Test after changes**: Run the example to ensure it still works
2. **Follow naming**: Use descriptive names like `stage<N>_<topic>.py`
3. **Include docstrings**: Add module-level docstring explaining purpose
4. **Save organized output**: Use `results/` or `exports/` directories

---

## Related Documentation

- **[ANIMATION_GUIDE.md](../ANIMATION_GUIDE.md)**: Detailed animation guide
- **[CLAUDE.md](../CLAUDE.md)**: Development guidelines
- **[README.md](../README.md)**: Project overview

---

## Example Workflow

For a complete demonstration from scratch:

```bash
# 1. Understand geometric preprocessing
python examples/stage1_geometry.py

# 2. See how decomposition works
python examples/stage2_decomposition.py

# 3. View ACO optimization
MPLBACKEND=Agg python examples/stage3_optimization.py

# 4. See complete animated visualization
MPLBACKEND=Agg python examples/complete_visualization.py
```

This workflow takes you through all three stages and produces impressive animations!
