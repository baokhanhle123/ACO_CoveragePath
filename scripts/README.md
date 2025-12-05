# Scripts Directory

Utility scripts for benchmarking and performance testing.

## Structure

### `/benchmarks/`
Performance benchmarking scripts:

- `benchmark.py` - Full benchmark suite
- `quick_benchmark.py` - Quick performance test

**Usage**:
```bash
python scripts/benchmarks/benchmark.py
python scripts/benchmarks/quick_benchmark.py
```

## Note

These scripts are different from the formal test suite in `/tests/`:
- **Tests (`/tests/`)**: Unit and integration tests run with pytest (92/92 passing)
- **Scripts (`/scripts/`)**: Standalone benchmarking scripts

For formal testing, use: `pytest tests/ -v`
