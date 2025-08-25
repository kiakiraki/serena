# Repository Guidelines

## Project Structure & Module Organization
- Source: `src/serena/` (core agent, CLI, tools), `src/interprompt/`, `src/solidlsp/`
- Tests: `test/` with language-specific subfolders and `__snapshots__/` for snapshot tests
- Scripts: `scripts/` (utilities and demos)
- Docs & assets: `docs/`, `resources/`, `public/`
- Config: `.serena/` project config and memories; repo config in `pyproject.toml`

## Build, Test, and Development Commands
- Env: `uv venv` then activate (`source .venv/bin/activate`)
- Install (dev): `uv pip install --all-extras -r pyproject.toml -e .`
- Run server: `uv run serena start-mcp-server [--context <ctx>]`
- Tests: `uv run poe test` (pytest; honors `PYTEST_MARKERS`)
- Lint: `uv run poe lint` (ruff + black check)
- Format: `uv run poe format` (ruff --fix + black)
- Types: `uv run poe type-check` (mypy on `src/serena`)

## Coding Style & Naming Conventions
- Python 3.11; 4-space indent; UTF-8
- Formatting: Black, line length 140; import sorting via Ruff
- Linting: Ruff with project rules in `pyproject.toml`
- Typing: Prefer explicit type hints; mypy is strict for core modules
- Names: snake_case for functions/vars, PascalCase for classes, UPPER_SNAKE for constants

## Testing Guidelines
- Framework: Pytest with markers configured in `pyproject.toml`
- Location: place tests under `test/`; name files `test_*.py`
- Snapshots: use `syrupy` and store generated files under `__snapshots__/`
- Running locally: `uv run poe test -m "not java and not rust"` (example markers)

## Commit & Pull Request Guidelines
- Commits: short imperative subject (<= 72 chars); optional scope/prefix (e.g., `fix:`, `feat:`, `docs:`); append `[ci skip]` for docs-only
- Reference issues in the body (e.g., "Closes #123") and explain rationale and impact
- Before pushing: `uv run poe format && uv run poe lint && uv run poe test && uv run poe type-check`
- PRs: include clear description, linked issues, reproduction/validation steps, and updated tests; add screenshots for CLI output or dashboard changes when helpful

## Security & Configuration Tips
- Keep secrets out of VCS; use `.env` (see `.env.example`) for local runs
- Prefer absolute paths when configuring clients; review `.serena/project.yml` before sharing
- Avoid network/file-system side effects in tests; use temp dirs and fixtures
