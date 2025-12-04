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

## Performance Expectations

- **Tests**: 92 in ~1s
- **Stages** (100×80m, 7 blocks): Stage 1 <0.5s, Stage 2 <0.2s, Stage 3 5-30s
- **ACO**: 2-3 blocks <2s, 5-10 blocks 2-10s, 10-20 blocks 5-30s
- **Quality**: 85-95% efficiency, 10-50% ACO improvement, 50-100 iter convergence
- **Memory**: <100 MB

## Academic Context

Course project (HK251) implementing Zhou et al. 2014 algorithm. Focus: **correctness > performance, clarity > optimization, reproducibility > speed**.

**Reference**: Zhou, K., et al. (2014). Agricultural operations planning in fields with multiple obstacle areas. *Computers and Electronics in Agriculture*, 109, 12-22. DOI: [10.1016/j.compag.2014.08.013](https://doi.org/10.1016/j.compag.2014.08.013)
