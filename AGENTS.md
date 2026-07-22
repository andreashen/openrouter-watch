# AGENTS.md

## Cursor Cloud specific instructions

### Architecture

OpenRouter Watch has two components:
1. **Python data pipeline** (`src/openrouter_watch/`) — fetches model data from the OpenRouter API, normalizes it, and derives the committed dataset into `data/derived/models_latest.json`.
2. **Astro static frontend** (`web/`) — renders a model comparison table from `data/derived/models_latest.json` (and merges weighted-price sidecar at build time).

No databases, Docker, or background services are required. Living docs: `docs/architecture.md`, `docs/data-schema.md`, `docs/ops/`.

### Running the project

- **Python lint/test**: `ruff check .` and `pytest` from repo root.
- **Data pipeline**: `python3 scripts/fetch.py && python3 scripts/normalize.py && python3 scripts/derive.py` (derive fetches benchmarks for all models and takes several minutes).
- **Frontend dev server**: `cd web && npm run dev` (serves on port 4321).
- **Frontend build**: `cd web && npm run build` (outputs to `web/dist/`).
- **Frontend type check**: `cd web && npm run check`.

### Environment notes

- Python: `pyproject.toml` requires `>=3.11`; CI uses 3.12. Node.js 22+ recommended for the frontend.
- `OPENROUTER_API_KEY` env var is optional (increases rate limits).
- The frontend requires `data/derived/models_latest.json` to exist (run the pipeline first).
- `models_latest.json` is a normal committed JSON file, not a symlink or timestamp pointer.
- The `ruff check .` linter may report existing import ordering issues in the test files — these are pre-existing and not introduced by agent changes.
