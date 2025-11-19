# ACO-based Agricultural Coverage Path Planning

Implementation of the algorithm from:
**"Agricultural operations planning in fields with multiple obstacle areas"**
by K. Zhou et al., Computers and Electronics in Agriculture, 2014.

## Overview

This project implements a complete coverage path planning system for agricultural machinery operating in fields with multiple obstacles using Ant Colony Optimization (ACO).

### Algorithm Stages

1. **Stage 1: Field Geometric Representation**
   - Headland generation around field and obstacles
   - Obstacle classification (Types A, B, C, D)
   - Parallel track generation

2. **Stage 2: Field Decomposition**
   - Boustrophedon cellular decomposition
   - Block merging via adjacency graph
   - Track clustering into blocks

3. **Stage 3: Path Optimization**
   - Entry/exit node generation
   - TSP cost matrix construction
   - ACO-based block sequencing

## Project Structure

```
src/
├── geometry/       # Geometric processing (polygons, headlands, tracks)
├── obstacles/      # Obstacle classification
├── decomposition/  # Field decomposition into blocks
├── optimization/   # ACO and TSP solvers
├── visualization/  # Plotting and animation
├── data/          # Data structures (Field, Block, Track, etc.)
└── utils/         # I/O, logging, benchmarking

experiments/       # Experiment scripts for paper results
tests/            # Unit tests
data/             # Test datasets
results/          # Output (plots, paths, metrics)
```

## Installation

Using `uv` (recommended):
```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create environment and install dependencies
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e .
```

Using pip:
```bash
python -m venv venv
source venv/bin/activate
pip install -e .
```

## Quick Start

```python
from src.data.field import Field
from src.optimization.aco import ACOPathPlanner

# Create field with obstacles
field = Field(
    boundary=[(0, 0), (100, 0), (100, 100), (0, 100)],
    obstacles=[
        [(20, 20), (30, 20), (30, 30), (20, 30)],
        [(60, 60), (70, 60), (70, 70), (60, 70)]
    ]
)

# Plan coverage path
planner = ACOPathPlanner(
    operating_width=5.0,
    turning_radius=3.0,
    num_headland_passes=2,
    driving_direction=0.0
)

solution = planner.plan(field)

# Visualize
solution.plot()
solution.save_metrics("results/metrics/")
solution.export_path("results/paths/path.csv")
```

## Running Experiments

```bash
# Generate synthetic test fields
python experiments/synthetic_fields/generate.py

# Run benchmark experiments
python experiments/benchmarks/run_all.py

# Analyze results
python experiments/benchmarks/analyze.py
```

## Testing

```bash
pytest tests/
```

## Performance Benchmarking

All experiments automatically log:
- Total effective working distance
- Non-working (turning) distance
- Block connection distance
- Computational time
- ACO convergence metrics

Results are saved to `results/metrics/` for report generation.

## Citation

```bibtex
@article{zhou2014agricultural,
  title={Agricultural operations planning in fields with multiple obstacle areas},
  author={Zhou, K and Jensen, A Leck and S{\o}rensen, CG and Busato, P and Bochtis, DD},
  journal={Computers and Electronics in Agriculture},
  volume={109},
  pages={12--22},
  year={2014},
  publisher={Elsevier}
}
```

## License

MIT License (or as per your university requirements)
