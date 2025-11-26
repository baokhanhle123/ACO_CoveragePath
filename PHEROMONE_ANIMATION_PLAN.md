# Pheromone Heatmap Animation Implementation Plan

**Goal**: Create impressive animation showing ACO pheromone trails evolving over iterations

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                   ACO Solver (Modified)                      │
│  - Records pheromone matrix at key iterations                │
│  - Stores best solution at each snapshot                     │
│  - Returns history for visualization                         │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              Pheromone Visualizer                           │
│  - Creates node layout (using actual field positions)        │
│  - Draws edges with thickness = pheromone strength           │
│  - Colors edges by pheromone level (heatmap)                 │
│  - Highlights best path at each iteration                    │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│           Pheromone Animator                                │
│  - Animates pheromone evolution over iterations              │
│  - Shows convergence plot alongside                          │
│  - Exports to GIF/MP4                                        │
└─────────────────────────────────────────────────────────────┘
```

---

## Implementation Steps

### Step 1: Modify ACOSolver ✓ PLANNED

**File**: `src/optimization/aco.py`

**Changes**:
```python
class ACOSolver:
    def __init__(self, ..., record_history=False, history_interval=10):
        # Add history tracking
        self.record_history = record_history
        self.history_interval = history_interval
        self.pheromone_history = []  # List of pheromone snapshots
        self.history_iterations = []  # Iterations where snapshots taken
        self.history_best_solutions = []  # Best solution at each snapshot

    def solve(self, verbose=False):
        for iteration in range(self.params.num_iterations):
            # ... existing code ...

            # NEW: Record history
            if self.record_history and iteration % self.history_interval == 0:
                self.pheromone_history.append(self.pheromone.copy())
                self.history_iterations.append(iteration)
                if self.best_solution:
                    self.history_best_solutions.append(self.best_solution)

    def get_pheromone_history(self):
        """Return (iterations, pheromone_matrices, best_solutions)."""
        return (self.history_iterations, self.pheromone_history,
                self.history_best_solutions)
```

**Risk**: Low - Non-invasive addition, doesn't change existing behavior

---

### Step 2: Create Pheromone Visualization Module ✓ PLANNED

**File**: `src/visualization/pheromone_viz.py`

**Class**: `PheromoneVisualizer`

**Key Methods**:
```python
class PheromoneVisualizer:
    def __init__(self, blocks, nodes, field):
        # Store block/node layout
        self.node_positions = self._calculate_node_positions(nodes)

    def _calculate_node_positions(self, nodes):
        """Use actual field coordinates for nodes."""
        return {node.index: (node.x, node.y) for node in nodes}

    def create_pheromone_graph(self, pheromone_matrix, best_solution=None):
        """
        Create pheromone graph visualization.

        - Draw nodes at field positions
        - Draw edges with width/color = pheromone strength
        - Highlight best path if provided
        """

    def normalize_pheromone(self, pheromone_matrix):
        """Normalize pheromone for visualization."""
        # Filter out invalid edges (pheromone ~ 0)
        # Normalize to [0, 1] for colormapping
```

**Visualization Strategy**:
- Nodes: Draw as circles at actual field coordinates
- Edges: Draw with:
  - Width ∝ pheromone strength
  - Color: Blue (low) → Yellow → Red (high) using colormap
  - Alpha: Transparent for weak pheromone, opaque for strong
- Best Path: Thick green line overlay

---

### Step 3: Create Pheromone Animator ✓ PLANNED

**File**: `src/visualization/pheromone_animation.py`

**Class**: `PheromoneAnimator`

**Features**:
```python
class PheromoneAnimator:
    def __init__(self, solver, field, blocks):
        # Get pheromone history from solver
        self.iterations, self.pheromones, self.solutions = solver.get_pheromone_history()

    def create_animation(self):
        """
        Create multi-panel animation:

        Layout:
        ┌──────────────┬────────────┐
        │              │            │
        │  Pheromone   │ Convergence│
        │  Graph       │   Plot     │
        │  (main)      │  (small)   │
        └──────────────┴────────────┘
        """

    def animate_frame(self, frame_idx):
        # Update pheromone visualization
        # Update convergence plot
        # Update iteration counter
```

---

### Step 4: Integration and Testing ✓ PLANNED

**Demo Script**: `demo_pheromone.py`

**Test Cases**:
1. Small field (3-4 blocks) - Quick generation
2. Medium field (7 blocks) - Full demo
3. Verify pheromone values make sense
4. Check animation smoothness
5. Test export to GIF

---

## Visualization Design

### Color Scheme
- **Pheromone Strength**:
  - Low (< 0.3): Light blue, thin line
  - Medium (0.3-0.7): Yellow, medium line
  - High (> 0.7): Red, thick line

- **Best Path**: Bright green, very thick (zorder=100)

- **Nodes**:
  - White circles with black border
  - Label with block ID

### Layout
- Main Panel (70%): Pheromone graph
- Side Panel (30%): Convergence plot
- Top: Iteration counter and best cost

---

## Expected Output

**Animation Features**:
- Duration: ~10-20 seconds (depending on iterations)
- FPS: 10-15 (slower to appreciate changes)
- Resolution: 1920×1080 (HD)
- Format: GIF (primary), MP4 (optional)

**Visual Effect**:
- Initially: Weak pheromone everywhere (uniform blue)
- Over time: Strong trails emerge (red paths)
- Best path: Stands out prominently
- Convergence: Shows cost decreasing

---

## Testing Strategy

### Unit Tests
1. ACOSolver history recording
2. Node position calculation
3. Pheromone normalization
4. Graph visualization creation

### Integration Tests
1. Full pipeline with history
2. Animation generation
3. File export

### Visual Tests
1. Verify pheromone values reasonable
2. Check best path highlights correctly
3. Ensure smooth animation

---

## Estimated Timeline

- Modify ACOSolver: 30 minutes
- Create PheromoneVisualizer: 90 minutes
- Create PheromoneAnimator: 90 minutes
- Testing and debugging: 60 minutes
- **Total: ~4.5 hours**

---

## Risk Mitigation

**Risk 1**: Pheromone matrix too complex to visualize
- **Mitigation**: Filter edges with low pheromone, focus on strong trails

**Risk 2**: Too many edges (N²) creates visual clutter
- **Mitigation**: Only draw edges with pheromone > threshold

**Risk 3**: Animation too slow with many iterations
- **Mitigation**: Sample iterations (e.g., every 10), use higher FPS

**Risk 4**: Node positions overlap
- **Mitigation**: Use actual field coordinates (naturally spaced)

---

## Success Criteria

- ✅ ACOSolver records history without errors
- ✅ Pheromone graph visualizes correctly
- ✅ Best path clearly visible
- ✅ Animation shows evolution over time
- ✅ Convergence plot updates correctly
- ✅ Export to GIF works
- ✅ No crashes or memory leaks
- ✅ Visually impressive and educational

---

**Status**: PLANNED - Ready for implementation
**Next**: Modify ACOSolver to add history recording
