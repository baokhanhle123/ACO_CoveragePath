# Repository Guidelines

## Project Structure & Module Organization
- `src/` contains the core Python package: `data/` (domain models), `geometry/`, `obstacles/`,
  `decomposition/`, `optimization/`, `visualization/`, and `dashboard/`. `src/stage1.py` is the
  Stage 1 entry point.
- `tests/` holds pytest suites by stage (for example, `tests/test_decomposition.py`,
  `tests/test_aco.py`).
- `examples/` provides runnable demos; most outputs land in `exports/`.
- `streamlit_app.py` launches the Streamlit dashboard; `scenarios/` stores JSON presets.
- `exports/` is for generated plots, animations, and reports; avoid committing large artifacts
  unless explicitly tracked.

## Build, Test, and Development Commands
- `uv venv && source .venv/bin/activate && uv pip install -e .` sets up the environment.
- `uv pip install -e '.[dev]'` installs developer tools (`black`, `ruff`, `mypy`).
- `pytest tests/ -v` runs the full suite; run a focused test first when possible,
  e.g., `pytest tests/test_aco.py -v`.
- `python examples/stage3_optimization.py` runs the Stage 3 demo; use `MPLBACKEND=Agg` for
  headless runs.
- `.venv/bin/streamlit run streamlit_app.py` launches the dashboard.

## Coding Style & Naming Conventions
- Use 4-space indentation, type hints, and docstrings for public APIs.
- Format with `black` (line length 100) and lint with `ruff` (E/F/I rules).
- Prefer `snake_case` for modules/functions, `CamelCase` for classes, and `UPPER_SNAKE` for
  constants.

## Testing Guidelines
- Tests follow `test_*.py` and `test_*` naming (see `pyproject.toml`).
- Add or update tests alongside algorithm changes; keep fixtures deterministic.
- For stochastic ACO changes, rerun the relevant tests to confirm stability.

## Commit & Pull Request Guidelines
- Commit history favors short, imperative summaries (e.g., “Fix missing block error”,
  “Add pheromone evolution”).
- PRs should include a concise summary, tests run, and sample outputs (plots/animations) when
  visualization or dashboard behavior changes.
- Update `README.md` or `examples/README.md` when adding new demos or commands.

## Configuration & Outputs
- Scenario presets live in `scenarios/*.json`; keep new presets small and documented.
- Generated assets should stay under `exports/` per `.gitignore` to avoid accidental commits.
