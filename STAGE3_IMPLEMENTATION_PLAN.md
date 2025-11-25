# Stage 3 Implementation Plan
**ACO-based Path Optimization**

**Date:** 2025-11-26
**Status:** 🚀 READY TO START
**Estimated Time:** 19-27 hours

---

## Overview

Stage 3 implements the Ant Colony Optimization (ACO) algorithm to solve the Traveling Salesman Problem (TSP) for optimal block sequencing. This is the final and most complex stage of the algorithm.

**Reference:** Zhou et al. 2014, Section 2.4

---

## Algorithm Understanding

### The Problem

Given:
- N blocks (from Stage 2 decomposition)
- Each block has 4 entry/exit nodes
- Need to find optimal sequence to visit all blocks

Find:
- Optimal block visitation order
- Entry/exit node selection for each block
- Complete coverage path

### The Solution (ACO-TSP)

**ACO Basics:**
- Population of "ants" construct solutions
- Ants follow pheromone trails and heuristic information
- Good solutions deposit more pheromone
- Iterative improvement through pheromone evaporation and reinforcement

**For Our Problem:**
- Nodes: Entry/exit points of all blocks (4N nodes)
- Constraints: Must visit exactly 2 nodes per block
- Objective: Minimize total path length

---

## Implementation Phases

### Phase 1: Entry/Exit Node Generation ✅ (Already exists)

**Status:** Method exists in `Block.create_entry_exit_nodes()`

**Tasks:**
- [x] Review existing implementation
- [ ] Create global node numbering function
- [ ] Test node generation for multiple blocks
- [ ] Verify node positioning

**Expected Output:**
```python
# For 5 blocks: 20 nodes total (4 per block)
nodes = [
    BlockNode(pos=(x1, y1), block_id=0, type="first_start", index=0),
    BlockNode(pos=(x2, y2), block_id=0, type="first_end", index=1),
    BlockNode(pos=(x3, y3), block_id=0, type="last_start", index=2),
    BlockNode(pos=(x4, y4), block_id=0, type="last_end", index=3),
    # ... nodes for blocks 1-4
]
```

### Phase 2: Cost Matrix Construction (3-4 hours)

**Files to Create:**
- `src/optimization/cost_matrix.py`

**Key Functions:**
```python
def euclidean_distance(node1: BlockNode, node2: BlockNode) -> float
def turning_cost(from_node: BlockNode, to_node: BlockNode) -> float
def calculate_transition_cost(from_node: BlockNode, to_node: BlockNode) -> float
def build_cost_matrix(nodes: List[BlockNode], blocks: List[Block]) -> np.ndarray
```

**Cost Components:**
1. **Within-block cost:** Working distance (track coverage)
2. **Between-block cost:** Euclidean distance + turning penalty
3. **Invalid transitions:** Infinity (can't enter/exit same block endpoint twice)

**Matrix Structure:**
```
Cost[i][j] = cost to transition from node i to node j

For 5 blocks (20 nodes):
  - Matrix size: 20 × 20
  - Diagonal: 0 (no cost to stay at same node)
  - Within block: Working distance
  - Between blocks: Euclidean + turn cost
  - Invalid: ∞
```

**Constraints to Encode:**
- Can't go from a block's entry to its own exit without covering tracks
- Must enter and exit each block exactly once
- Parity constraint: Odd blocks exit from opposite side

### Phase 3: ACO Algorithm (6-8 hours) **MOST COMPLEX**

**Files to Create:**
- `src/optimization/aco.py`
- `src/optimization/ant.py`
- `src/optimization/pheromone.py`

**Core Classes:**

```python
@dataclass
class ACOParameters:
    """ACO algorithm parameters from paper."""
    alpha: float = 1.0      # Pheromone importance
    beta: float = 2.0       # Heuristic importance
    rho: float = 0.1        # Evaporation rate
    q: float = 100.0        # Pheromone deposit constant
    num_ants: int = 20      # Population size
    num_iterations: int = 100

@dataclass
class Ant:
    """Single ant for ACO."""
    current_node: int
    visited_blocks: Set[int]
    path: List[int]         # Node sequence
    path_length: float

    def can_visit(self, node: int, blocks: List[Block]) -> bool
    def select_next_node(self, pheromone, heuristic, alpha, beta) -> int
    def complete_tour(self) -> float

class ACOSolver:
    def __init__(self, nodes, blocks, cost_matrix, params)
    def initialize_pheromone(self) -> np.ndarray
    def calculate_heuristic(self) -> np.ndarray
    def run_iteration(self) -> Solution
    def update_pheromone(self, solutions: List[Solution])
    def solve(self) -> Solution
```

**Algorithm Steps:**

1. **Initialize:**
   ```python
   pheromone[i][j] = 1.0  # Equal initial pheromone
   heuristic[i][j] = 1.0 / cost[i][j]  # Inverse distance
   ```

2. **For each iteration:**
   ```python
   for ant in ants:
       # Start at random node
       while not ant.tour_complete():
           # Probabilistic selection
           next_node = select_by_probability(pheromone, heuristic, alpha, beta)
           ant.move_to(next_node)

       # Record solution
       solutions.append(ant.path)

   # Update pheromone
   evaporate_pheromone(rho)
   deposit_pheromone(solutions)
   ```

3. **Selection Probability:**
   ```python
   p[i][j] = (pheromone[i][j]^alpha * heuristic[i][j]^beta) / sum_k(...)
   ```

4. **Pheromone Update:**
   ```python
   # Evaporation
   pheromone[i][j] *= (1 - rho)

   # Deposit (best solutions only)
   for edge in best_solution:
       pheromone[i][j] += q / solution_length
   ```

**Constraints Handling:**

The tricky part: ensure each block visited exactly once with valid entry/exit pairs.

**Approach 1: State Space Restriction**
- Track which blocks have been visited
- Only allow transitions that complete blocks properly
- Use parity function to determine valid exit nodes

**Approach 2: Penalty Method**
- Allow any transitions
- Add huge penalty for invalid solutions
- Let ACO naturally avoid bad solutions

**Recommendation:** Use Approach 1 (cleaner, faster convergence)

### Phase 4: Path Generation (2-3 hours)

**Files to Create:**
- `src/optimization/path_generator.py`

**Key Functions:**
```python
def solution_to_block_sequence(solution: List[int], blocks: List[Block]) -> List[int]
def generate_block_path(block: Block, entry_node: BlockNode, exit_node: BlockNode) -> Path
def generate_complete_path(solution: Solution, blocks: List[Block]) -> CompletePath
```

**Path Structure:**
```python
@dataclass
class PathSegment:
    type: str  # "track", "transition", "headland"
    start: Tuple[float, float]
    end: Tuple[float, float]
    block_id: Optional[int]

@dataclass
class CompletePath:
    segments: List[PathSegment]
    total_length: float
    block_sequence: List[int]
```

**Path Generation Logic:**

For each block in sequence:
1. Enter at specified entry node
2. Cover all tracks in correct order (based on parity)
3. Exit at specified exit node
4. Transition to next block's entry node

**Example:**
```
Block 0 (even tracks=4):
  Entry: n_01 (first_start)
  Tracks: T0 → T1 → T2 → T3
  Exit: n_04 (last_end)

Transition: n_04 → n_11 (via headland)

Block 1 (odd tracks=3):
  Entry: n_11 (first_start)
  Tracks: T0 → T1 → T2
  Exit: n_12 (last_start)  # Note: odd blocks exit from opposite side

...
```

### Phase 5: Testing (3-5 hours)

**Test Files to Create:**
- `tests/test_cost_matrix.py`
- `tests/test_aco.py`
- `tests/test_path_generation.py`
- `tests/test_stage3_integration.py`

**Unit Tests:**

**Cost Matrix:**
- [ ] Euclidean distance calculation
- [ ] Symmetric matrix (cost[i][j] == cost[j][i])
- [ ] Diagonal is zero
- [ ] Invalid transitions are infinity
- [ ] Within-block costs are working distances

**ACO:**
- [ ] Pheromone initialization
- [ ] Heuristic calculation
- [ ] Ant movement logic
- [ ] Valid solution generation (all blocks visited once)
- [ ] Pheromone update
- [ ] Convergence (improves over iterations)

**Path Generation:**
- [ ] Block sequence extraction
- [ ] Path continuity
- [ ] All blocks covered
- [ ] Total distance matches TSP solution

**Integration Test:**
- [ ] Full pipeline (Stage 1 + 2 + 3)
- [ ] Multiple field configurations
- [ ] Comparison with greedy baseline

### Phase 6: Visualization (3-4 hours)

**Files to Create:**
- `demo_stage3.py`
- `src/visualization/path_plotter.py` (optional)

**Visualizations Needed:**

1. **Static Path Visualization:**
   - Field with obstacles
   - Blocks color-coded
   - Optimized path drawn
   - Node positions marked
   - Block sequence labeled

2. **ACO Convergence Plot:**
   - Best solution length vs iteration
   - Average solution length vs iteration
   - Show improvement over time

3. **Comparison Plot:**
   - ACO solution vs greedy
   - Show path difference
   - Report % improvement

4. **Animation (optional):**
   - Ant exploration process
   - Pheromone evolution
   - Best path discovery

---

## Implementation Order (Recommended)

**Week 1: Foundation (8-10 hours)**
1. ✅ Phase 1: Verify node generation (1 hour)
2. ⏳ Phase 2: Cost matrix (3-4 hours)
3. ⏳ Phase 3.1: Basic ACO structure (2-3 hours)
4. ⏳ Phase 3.2: Ant logic (2-3 hours)

**Week 2: Core Algorithm (8-10 hours)**
5. ⏳ Phase 3.3: Pheromone update (2-3 hours)
6. ⏳ Phase 3.4: Complete ACO solver (3-4 hours)
7. ⏳ Phase 4: Path generation (2-3 hours)

**Week 3: Testing & Visualization (5-7 hours)**
8. ⏳ Phase 5: Testing (3-5 hours)
9. ⏳ Phase 6: Visualization (3-4 hours)
10. ⏳ Benchmarking and tuning (2-3 hours)

**Total: 19-27 hours**

---

## Key Challenges and Solutions

### Challenge 1: Valid Solution Constraints

**Problem:** ACO must ensure each block visited exactly once with proper entry/exit.

**Solution:**
- Track visited blocks in ant state
- Filter available next nodes to only valid options
- Use parity function to determine correct exit node

### Challenge 2: Pheromone Initialization

**Problem:** Initial uniform pheromone may not guide ants effectively.

**Solution:**
- Start with greedy solution pheromone boost
- Or use construction heuristic for initial trail

### Challenge 3: Large State Space

**Problem:** 4N nodes creates large state space.

**Solution:**
- Use block-level thinking (reduce to N blocks)
- Only track entry/exit selection within blocks
- Reduce complexity from O(4N!) to manageable level

### Challenge 4: Convergence Speed

**Problem:** ACO may take many iterations to converge.

**Solution:**
- Use elitist strategy (only best ants deposit pheromone)
- Increase beta (heuristic) for faster initial convergence
- Reduce rho (slower evaporation) for exploitation

### Challenge 5: Local Optima

**Problem:** ACO may get stuck in local optima.

**Solution:**
- Use multiple ant colonies (parallel runs)
- Add pheromone trail smoothing
- Restart mechanism if no improvement for N iterations

---

## Parameters to Tune

From paper and ACO literature:

**Pheromone Parameters:**
- α (alpha): 1.0 - Weight of pheromone trail
  - Higher α: More exploitation (follow trails)
  - Lower α: More exploration
  - Typical range: 0.5 - 2.0

**Heuristic Parameters:**
- β (beta): 2.0 - Weight of heuristic information
  - Higher β: More greedy (follow nearest)
  - Lower β: More random
  - Typical range: 1.0 - 5.0

**Evaporation:**
- ρ (rho): 0.1 - Pheromone evaporation rate
  - Higher ρ: Faster forgetting (more exploration)
  - Lower ρ: Longer memory (more exploitation)
  - Typical range: 0.01 - 0.5

**Deposit:**
- Q: 100.0 - Pheromone deposit constant
  - Scale factor for pheromone amounts
  - Adjust based on path lengths

**Population:**
- num_ants: 20 - Number of ants per iteration
  - More ants: Better exploration, slower
  - Fewer ants: Faster, may miss solutions
  - Typical: 10-50

**Iterations:**
- num_iterations: 100 - Maximum iterations
  - More iterations: Better convergence
  - Use early stopping if no improvement

---

## Success Criteria

Stage 3 will be considered successful when:

1. **Functionality:**
   - [ ] All blocks visited exactly once
   - [ ] Valid entry/exit node pairs
   - [ ] Continuous path generated
   - [ ] No self-intersections

2. **Optimization:**
   - [ ] ACO converges (solution improves over iterations)
   - [ ] Final solution better than greedy baseline
   - [ ] Solution within 10% of known optimum (if available)

3. **Code Quality:**
   - [ ] All unit tests passing
   - [ ] Integration test passing
   - [ ] Zero linting errors
   - [ ] Well-documented code

4. **Performance:**
   - [ ] Solves 10-block problem in < 10 seconds
   - [ ] Solves 20-block problem in < 30 seconds
   - [ ] Memory usage reasonable (< 100MB)

5. **Visualization:**
   - [ ] Path clearly visible
   - [ ] Block sequence understandable
   - [ ] Convergence plot shows improvement

---

## File Structure

```
src/
  optimization/           # NEW - Stage 3
    __init__.py
    cost_matrix.py        # Cost calculation
    ant.py                # Ant class
    aco.py                # ACO solver
    path_generator.py     # Path generation

tests/
  test_cost_matrix.py     # NEW
  test_aco.py             # NEW
  test_path_generation.py # NEW
  test_stage3_integration.py  # NEW

demo_stage3.py            # NEW - Stage 3 demo
```

---

## Next Steps

**Immediate Actions:**
1. Create `src/optimization/` directory
2. Create stub files with function signatures
3. Implement Phase 1 (node generation verification)
4. Implement Phase 2 (cost matrix)
5. Begin Phase 3 (ACO core)

**Before Starting Each Phase:**
- Review paper section
- Understand algorithm details
- Write tests first (TDD approach)
- Implement incrementally
- Test frequently

---

## References

**Primary:**
- Zhou et al. 2014, Section 2.4 "Path planning based on ACO algorithm"

**ACO Background:**
- Dorigo & Stützle (2004). "Ant Colony Optimization"
- ACO for TSP: Classic application

**Implementation Tips:**
- Start simple (basic ACO)
- Add complexity gradually
- Visualize intermediate results
- Compare with greedy baseline

---

**Plan Created:** 2025-11-26
**Status:** 📋 READY TO IMPLEMENT
**Next:** Create file structure and begin Phase 1
