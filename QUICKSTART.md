# Quick Start Guide

This is a **5-minute guide** to get the ACO Coverage Path Planning system running.

---

## Installation (1 minute)

```bash
# Clone or navigate to the project
cd ACO_CoveragePath

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
uv pip install -e .
```

**Alternative with pip**:
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

---

## Run Demos (3 minutes)

### Stage 1: Field Representation
```bash
python demo_stage1.py
```
**Output**: `results/plots/stage1_demo.png`
- Shows field, obstacles, headland, and tracks

### Stage 2: Field Decomposition
```bash
python demo_stage2.py
```
**Output**: `results/plots/stage2_demo.png`
- Shows boustrophedon decomposition into blocks

### Stage 3: ACO Optimization ⭐
```bash
MPLBACKEND=Agg python demo_stage3.py
```
**Output**: `stage3_path.png` and `stage3_convergence.png`
- Shows optimized coverage path
- **Expected: 94.5% efficiency, 10-20% cost improvement**

---

## Verify Installation (1 minute)

```bash
# Run all 92 tests (should complete in ~1 second)
pytest tests/ -q

# Expected output:
# ........................................................................ [ 78%]
# ....................                                                     [100%]
# 92 passed in 0.73s
```

---

## What You Get

After running the demos, you'll have:

✅ **Complete coverage paths** for agricultural fields with obstacles
✅ **High efficiency** (85-95% working distance vs total distance)
✅ **Optimized block sequencing** using Ant Colony Optimization
✅ **Visual outputs** showing the entire planning process

---

## Expected Results

**Demo Field** (100m × 80m, 3 obstacles, 7 blocks):

```
ACO Optimization Results:
  - Initial cost: ~1077 m
  - Optimized cost: ~968 m
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

## Troubleshooting

**Tests fail?**
```bash
# Check Python version (requires 3.9+)
python --version

# Reinstall dependencies
pip install -e .
```

**Display issues (headless system)?**
```bash
# Use AGG backend for matplotlib
MPLBACKEND=Agg python demo_stage3.py
```

**Need more details?**
- See full `README.md` for comprehensive documentation
- Check `VERIFICATION_REPORT.md` for technical details
- Review code examples in `README.md` usage section

---

## Next Steps

**To use in your own code**:
```python
from src.data import create_field_with_rectangular_obstacles, FieldParameters
from src.geometry import generate_field_headland
from src.obstacles.classifier import classify_all_obstacles
from src.decomposition import boustrophedon_decomposition
from src.optimization import ACOSolver, build_cost_matrix

# See README.md "Usage Examples" for complete code
```

**For more information**:
- 📖 `README.md` - Full documentation
- 🔬 `VERIFICATION_REPORT.md` - Verification details
- 📊 `STAGE3_COMPLETION_REPORT.md` - Technical report

---

**You're all set! The system is ready to generate optimized coverage paths.** ✅
