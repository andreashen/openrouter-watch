# AGENTS.md

## Cursor Cloud specific instructions

### Architecture

OpenRouter Watch is a monorepo with two components:
1. **Python data pipeline** (`src/openrouter_tracker/`, `scripts/`) — ETL that fetches, normalizes, and derives model data from the OpenRouter API.
2. **Astro static frontend** (`web/`) — reads derived JSON/CSV and renders a model comparison table.

No databases, Docker, or background services required.

### Package name mapping

The Python package source is at `src/openrouter_tracker/` but all imports use `openrouter_watch`. A symlink (`src/openrouter_watch -> openrouter_tracker`) must exist for editable installs to work. The update script handles this automatically.

### Commands

- **Python tests:** `pytest` (from repo root)
- **Python lint:** `ruff check .` and `ruff format --check .` (from repo root)
- **Frontend type-check:** `npm run check` (from `web/`)
- **Frontend dev server:** `npm run dev` (from `web/`, serves at `http://localhost:4321`)
- **Frontend build:** `npm run build` (from `web/`)
- **Data pipeline:** `python3 scripts/fetch.py && python3 scripts/normalize.py && python3 scripts/derive.py` (from repo root)

### Gotchas

- `scripts/derive.py` fetches benchmark data for every model (~371 HTTP calls) and can take several minutes. Tests mock this with `pytest-httpx`.
- `OPENROUTER_API_KEY` env var is optional but increases API rate limits for `scripts/fetch.py`.
- The Astro frontend reads from `data/derived/models_latest.json` (a symlink). This file must exist for the site to render data.
- Node.js >= 22.12.0 required (check `web/package.json` engines field).
- Python >= 3.11 required (check `pyproject.toml` requires-python).
