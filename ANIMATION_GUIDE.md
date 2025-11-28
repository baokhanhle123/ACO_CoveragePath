# Animation Visualization Guide

The ACO Coverage Path Planning system includes two powerful animation capabilities:

## 🎬 Available Animations

### 1. Path Execution Animation (Tractor Movement)
Shows a tractor moving along the optimized coverage path

**Features:**
- 🚜 Animated tractor icon with rotation
- 📍 Trail showing covered path
- 📊 Real-time progress bar
- 📈 Statistics overlay (distance covered, efficiency, etc.)
- 🎨 Color-coded working vs. transition segments

### 2. Pheromone Evolution Animation (ACO Process)
Shows how pheromone trails evolve during ACO optimization

**Features:**
- 🧠 Pheromone graph evolution over iterations
- 📉 Convergence plot showing cost reduction
- ✨ Best path highlighting
- 📊 Statistical overlays

---

## 🚀 Quick Start Examples

### Example 1: Path Execution Animation

```python
from src.data import FieldParameters, create_field_with_rectangular_obstacles
from src.decomposition import boustrophedon_decomposition, merge_blocks_by_criteria
from src.geometry import generate_field_headland, generate_parallel_tracks
from src.obstacles.classifier import classify_all_obstacles, get_type_d_obstacles
from src.optimization import (
    ACOParameters,
    ACOSolver,
    build_cost_matrix,
    generate_path_from_solution,
)
from src.visualization import animate_path_execution

# 1. Create field and run complete pipeline (Stages 1-3)
field = create_field_with_rectangular_obstacles(
    field_width=100,
    field_height=80,
    obstacle_specs=[(20, 20, 15, 12), (55, 30, 12, 15)],
    name="Animation Demo"
)

params = FieldParameters(
    operating_width=5.0,
    turning_radius=3.0,
    num_headland_passes=2,
    driving_direction=0.0,
    obstacle_threshold=5.0
)

# Run Stages 1-3 (see demo_animation.py for complete code)
# ... (headland, classification, decomposition, ACO) ...
# Result: path_plan, final_blocks

# 2. Create Path Animation - THE KEY FUNCTION!
animate_path_execution(
    field=field,
    blocks=final_blocks,
    path_plan=path_plan,
    output_file='my_path_animation.gif',  # Output filename
    fps=30,                                 # Frames per second
    speed_multiplier=2.0,                   # 2x speed
    figsize=(16, 10)                        # Figure size
)

print("✅ Animation saved to: my_path_animation.gif")
```

**Parameters for `animate_path_execution()`:**
- `field`: Field object with boundary and obstacles
- `blocks`: List of Block objects
- `path_plan`: PathPlan object from `generate_path_from_solution()`
- `output_file`: Output filename (`.gif` or `.mp4`)
- `fps`: Frames per second (default: 30)
- `speed_multiplier`: Animation speed (1.0 = normal, 2.0 = 2x, 0.5 = slow-motion)
- `figsize`: Figure size in inches (width, height)

---

### Example 2: Pheromone Evolution Animation

```python
from src.optimization import ACOSolver, ACOParameters
from src.visualization import animate_pheromone_evolution

# 1. Run ACO with history recording enabled
aco_params = ACOParameters(
    alpha=1.0,
    beta=2.0,
    rho=0.1,
    num_ants=30,
    num_iterations=100
)

solver = ACOSolver(
    blocks=final_blocks,
    nodes=all_nodes,
    cost_matrix=cost_matrix,
    params=aco_params,
    record_history=True,  # ⭐ IMPORTANT: Must enable history!
    history_interval=10    # Record every 10 iterations
)

# Run solver
best_solution = solver.solve(verbose=True)

# 2. Create Pheromone Animation - THE KEY FUNCTION!
animate_pheromone_evolution(
    solver=solver,                          # ACOSolver with history
    field=field,
    blocks=final_blocks,
    output_file='pheromone_evolution.gif',  # Output filename
    fps=2,                                  # 2 frames/sec (slow for clarity)
    figsize=(18, 8),                        # Figure size
    dpi=100                                 # Image resolution
)

print("✅ Pheromone animation saved to: pheromone_evolution.gif")
```

**Parameters for `animate_pheromone_evolution()`:**
- `solver`: ACOSolver instance with `record_history=True`
- `field`: Field object
- `blocks`: List of Block objects
- `output_file`: Output filename (`.gif` or `.mp4`)
- `fps`: Frames per second (default: 2 for pheromone, slower is better)
- `figsize`: Figure size in inches (width, height)
- `dpi`: Image resolution (default: 100)

---

## 🎯 Complete Working Example

```python
#!/usr/bin/env python3
"""
Complete example: Generate both animations from scratch.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.data import FieldParameters, create_field_with_rectangular_obstacles
from src.decomposition import boustrophedon_decomposition, merge_blocks_by_criteria
from src.geometry import generate_field_headland, generate_parallel_tracks
from src.obstacles.classifier import classify_all_obstacles, get_type_d_obstacles
from src.optimization import (
    ACOParameters,
    ACOSolver,
    build_cost_matrix,
    generate_path_from_solution,
)
from src.visualization import animate_path_execution, animate_pheromone_evolution


def main():
    # ==================== STAGE 1: Field Setup ====================
    print("[1/5] Creating field...")

    field = create_field_with_rectangular_obstacles(
        field_width=80,
        field_height=60,
        obstacle_specs=[(20, 15, 12, 10), (50, 35, 15, 12)],
        name="Animation Example"
    )

    params = FieldParameters(
        operating_width=5.0,
        turning_radius=3.0,
        num_headland_passes=2,
        driving_direction=0.0,
        obstacle_threshold=5.0
    )

    # ==================== STAGE 1: Geometry ====================
    print("[2/5] Processing geometry...")

    field_headland = generate_field_headland(
        field_boundary=field.boundary_polygon,
        operating_width=params.operating_width,
        num_passes=params.num_headland_passes
    )

    classified_obstacles = classify_all_obstacles(
        obstacle_boundaries=field.obstacles,
        field_inner_boundary=field_headland.inner_boundary,
        driving_direction_degrees=params.driving_direction,
        operating_width=params.operating_width,
        threshold=params.obstacle_threshold
    )

    type_d_obstacles = get_type_d_obstacles(classified_obstacles)
    obstacle_polygons = [obs.polygon for obs in type_d_obstacles]

    # ==================== STAGE 2: Decomposition ====================
    print("[3/5] Running decomposition...")

    preliminary_blocks = boustrophedon_decomposition(
        inner_boundary=field_headland.inner_boundary,
        obstacles=obstacle_polygons,
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

    print(f"  Created {len(final_blocks)} blocks")

    # ==================== STAGE 3: ACO Optimization ====================
    print("[4/5] Running ACO with history recording...")

    # Create nodes
    all_nodes = []
    node_index = 0
    for block in final_blocks:
        nodes = block.create_entry_exit_nodes(start_index=node_index)
        all_nodes.extend(nodes)
        node_index += 4

    # Build cost matrix
    cost_matrix = build_cost_matrix(blocks=final_blocks, nodes=all_nodes)

    # Run ACO with history enabled
    aco_params = ACOParameters(
        alpha=1.0,
        beta=2.0,
        rho=0.1,
        num_ants=30,
        num_iterations=50  # Fewer iterations for faster demo
    )

    solver = ACOSolver(
        blocks=final_blocks,
        nodes=all_nodes,
        cost_matrix=cost_matrix,
        params=aco_params,
        record_history=True,  # ⭐ Enable for pheromone animation
        history_interval=10
    )

    best_solution = solver.solve(verbose=True)

    # Generate path
    path_plan = generate_path_from_solution(best_solution, final_blocks, all_nodes)

    print(f"  Solution cost: {best_solution.cost:.2f}")
    print(f"  Path efficiency: {path_plan.efficiency*100:.1f}%")

    # ==================== ANIMATIONS ====================
    print("[5/5] Creating animations...")

    # Animation 1: Path Execution (tractor movement)
    print("  → Generating path execution animation...")
    animate_path_execution(
        field=field,
        blocks=final_blocks,
        path_plan=path_plan,
        output_file='path_execution_demo.gif',
        fps=30,
        speed_multiplier=2.0,
        figsize=(16, 10)
    )
    print("    ✅ Saved: path_execution_demo.gif")

    # Animation 2: Pheromone Evolution (ACO process)
    print("  → Generating pheromone evolution animation...")
    animate_pheromone_evolution(
        solver=solver,
        field=field,
        blocks=final_blocks,
        output_file='pheromone_evolution_demo.gif',
        fps=2,
        figsize=(18, 8)
    )
    print("    ✅ Saved: pheromone_evolution_demo.gif")

    print()
    print("=" * 60)
    print("✅ COMPLETE! Generated 2 animations:")
    print("   1. path_execution_demo.gif - Tractor movement")
    print("   2. pheromone_evolution_demo.gif - ACO optimization")
    print("=" * 60)


if __name__ == "__main__":
    main()
```

---

## 🎨 Animation Output Formats

Both animation functions support multiple output formats:

### GIF Format (Recommended for Presentations)
```python
animate_path_execution(..., output_file='animation.gif')
# Smaller file size, good for web/presentations
```

### MP4 Format (Higher Quality)
```python
animate_path_execution(..., output_file='animation.mp4')
# Requires ffmpeg installed on system
# Better quality, larger file size
```

---

## ⚙️ Customization Options

### Path Animation Customization

```python
from src.visualization import PathAnimator

# Create custom animator for fine control
animator = PathAnimator(
    field=field,
    blocks=final_blocks,
    path_plan=path_plan,
    figsize=(20, 12),      # Larger figure
    fps=60,                # Smoother animation
    speed_multiplier=1.5   # 1.5x speed
)

# Save as GIF
animator.save_animation('custom_path.gif', writer='pillow', dpi=100)
```

### Pheromone Animation Customization

```python
from src.visualization import PheromoneAnimator

# Create custom animator
animator = PheromoneAnimator(
    solver=solver,  # Must have record_history=True
    field=field,
    blocks=final_blocks
)

# Create animation with custom settings
anim = animator.create_animation(
    figsize=(20, 10),
    fps=3                  # 3 frames/sec
)

# Save with custom settings
animator.save_animation(anim, 'custom_pheromone.gif', dpi=120)
```

---

## 🎬 Running Existing Demo Scripts

The project includes ready-to-run demo scripts in the `examples/` directory:

### Demo 1: Path Animation Only
```bash
python examples/path_animation_only.py
# Output: animations/path_execution.gif
```

### Demo 2: Complete Visualization (Both Animations)
```bash
python examples/complete_visualization.py
# Output:
#   - animations/demo_path_execution.gif
#   - animations/demo_pheromone_evolution.gif
```

See `examples/README.md` for a complete guide to all demonstration scripts.

---

## 💡 Tips for Best Results

### For Path Execution Animation:
- ✅ Use `speed_multiplier=2.0` for quick demos
- ✅ Use `speed_multiplier=0.5` for detailed analysis
- ✅ `fps=30` provides smooth animation
- ✅ Larger `figsize` for better readability

### For Pheromone Animation:
- ✅ Use `fps=2` (slow) to see evolution clearly
- ✅ **MUST** set `record_history=True` in ACOSolver constructor
- ✅ Fewer iterations (50-100) make animation more manageable
- ✅ Set `history_interval` to control snapshot frequency

### General Tips:
- 🎬 GIF format is best for presentations/web
- 🎥 MP4 format is best for high-quality videos
- 📦 Animations can be large files (10-50MB)
- ⚡ Use headless backend for servers: `MPLBACKEND=Agg`

---

## 🐛 Troubleshooting

### "No pheromone history found"
**Solution**: Set `record_history=True` in ACOSolver:
```python
solver = ACOSolver(
    blocks=blocks,
    nodes=nodes,
    cost_matrix=cost_matrix,
    params=aco_params,
    record_history=True,  # ⭐ Required for pheromone animation!
    history_interval=10
)
```

### Animation saves but looks blank
**Solution**: Ensure matplotlib backend is set correctly:
```python
import matplotlib
matplotlib.use('Agg')  # For headless systems
```

### "ffmpeg not found" error (MP4 only)
**Solution**: Install ffmpeg:
```bash
# Ubuntu/Debian
sudo apt-get install ffmpeg

# macOS
brew install ffmpeg

# Or use GIF format instead
animate_path_execution(..., output_file='animation.gif')
```

---

## 📚 API Reference

### `animate_path_execution()`
```python
def animate_path_execution(
    field,              # Field object
    blocks,             # List[Block]
    path_plan,          # PathPlan object
    output_file,        # str: output filename (.gif or .mp4)
    fps=30,             # int: frames per second
    speed_multiplier=1.0,  # float: animation speed
    figsize=(16, 10)    # tuple: figure size
) -> str:
    """
    Create animated path execution.

    Returns:
        str: Path to saved animation file
    """
```

### `animate_pheromone_evolution()`
```python
def animate_pheromone_evolution(
    solver,             # ACOSolver with record_history=True
    field,              # Field object
    blocks,             # List[Block]
    output_file,        # str: output filename (.gif or .mp4)
    fps=2,              # int: frames per second (slower for clarity)
    figsize=(18, 8),    # tuple: figure size
    dpi=100             # int: image resolution
) -> str:
    """
    Create animated pheromone evolution.

    Returns:
        str: Path to saved animation file
    """
```

---

## ✅ Summary

The ACO Coverage Path Planning system includes professional animation capabilities:

1. **Path Execution**: Shows tractor moving along optimized path
2. **Pheromone Evolution**: Shows ACO learning process

Both animations are easy to generate with simple function calls and produce publication-quality results!
