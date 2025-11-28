# Scripts Directory

Utility scripts for validation, benchmarking, and testing.

## Structure

### `/validation/`
Integration and validation scripts for testing complete pipelines:

- `test_dashboard_components.py` - Dashboard component verification
- `test_pipeline_integration.py` - Full pipeline integration test
- `test_final_validation.py` - Complete Phase 2A validation
- `test_streamlit_launch.py` - Streamlit app launch test
- `test_animation.py` - Animation module comprehensive test
- `test_edge_cases.py` - Edge case robustness testing
- `test_pheromone_history.py` - Pheromone tracking validation
- `test_pheromone_viz.py` - Pheromone visualization test

**Usage**:
```bash
python scripts/validation/test_pipeline_integration.py
python scripts/validation/test_dashboard_components.py
```

### `/benchmarks/`
Performance benchmarking scripts:

- `benchmark.py` - Full benchmark suite
- `quick_benchmark.py` - Quick performance test
- `benchmark_results.txt` - Benchmark results

**Usage**:
```bash
python scripts/benchmarks/benchmark.py
python scripts/benchmarks/quick_benchmark.py
```

## Note

These scripts are different from the formal test suite in `/tests/`:
- **Tests (`/tests/`)**: Unit and integration tests run with pytest
- **Scripts (`/scripts/`)**: Standalone validation and benchmarking scripts

For formal testing, use: `pytest tests/ -v`
