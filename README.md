# OpenRouter Watch

Python pipeline fetches OpenRouter model metadata, normalizes it, and derives the committed dataset under `data/derived/models_latest.json`. The Astro site in `web/` renders the model table from that stable file.

English | [中文](#中文说明)

## Quick Start

```bash
pip install -e ".[dev]"

python scripts/fetch.py
python scripts/normalize.py
python scripts/derive.py
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENROUTER_API_KEY` | No | Increases API rate limits when set |

Copy `.env.example` to `.env` and fill in your key if needed.

## Directory Structure

```
scripts/                 # Entry-point scripts (fetch, normalize, derive, weighted prices)
src/openrouter_watch/    # Core library (fetcher, normalizer, deriver, schema, weighted prices)
tests/                   # pytest tests
data/raw/                # Raw API snapshots (gitignored)
data/normalized/         # Pydantic-validated records (gitignored)
data/derived/            # Stable committed dataset (models_latest.json + weighted sidecar)
web/                     # Astro frontend for the model table
docs/                    # Living architecture, schema, and ops runbooks
```

## Documentation

| Doc | Description |
| --- | --- |
| [docs/architecture.md](docs/architecture.md) | System architecture, data flow, frontend behavior |
| [docs/data-schema.md](docs/data-schema.md) | Field reference for derived datasets |
| [docs/ops/main_test_release_flow.md](docs/ops/main_test_release_flow.md) | `main` / `test` branch roles, release flow, re-anchor |
| [docs/ops/github_setup.md](docs/ops/github_setup.md) | GitHub Pages, Secrets, and workflow verification |
| [docs/readme.md](docs/readme.md) | Docs index |

## Development

```bash
# Run tests (offline; no network)
pytest

# Optional: live OpenRouter HTTP checks (set OPENROUTER_API_KEY if needed)
RUN_LIVE_API=1 pytest tests/test_live_api.py -v

# Lint / format
ruff check .
ruff format .
```

## Frontend

```bash
cd web
npm install
npm run dev
npm run build
```

## Data Source

See [NOTICE](NOTICE) for data sources and third-party terms.

Weighted Avg Input Price is stored in the sidecar `data/derived/weighted_prices_latest.json` and refreshed by a separate weekly workflow (not the daily `data-refresh` pipeline).

## License

The source code of this project is licensed under the Apache License 2.0.

---

## 中文说明

OpenRouter Watch 从 OpenRouter 拉取模型数据，经规范化与派生后产出稳定维护的 `data/derived/models_latest.json`，并由 `web/` 中的 Astro 站点读取它来展示模型表。

### 快速开始

```bash
pip install -e ".[dev]"

python scripts/fetch.py
python scripts/normalize.py
python scripts/derive.py
```

`derive.py` 会为每个模型请求 benchmark 接口并节流，完整运行可能需数分钟。系统结构与前端行为见 [docs/architecture.md](docs/architecture.md)；字段定义见 [docs/data-schema.md](docs/data-schema.md)。

### 文档

| 文档 | 说明 |
| --- | --- |
| [docs/architecture.md](docs/architecture.md) | 架构、数据流、前端行为 |
| [docs/data-schema.md](docs/data-schema.md) | 派生产物字段权威表 |
| [docs/ops/main_test_release_flow.md](docs/ops/main_test_release_flow.md) | `main` / `test` 分支职责、发布流与重锚 |
| [docs/ops/github_setup.md](docs/ops/github_setup.md) | GitHub Pages、Secrets 与触发验证 |
| [docs/readme.md](docs/readme.md) | 文档索引 |

### 数据来源

数据来源与第三方条款说明详见 [NOTICE](NOTICE)。

加权输入价（Weighted Avg Input Price）以侧车文件 `data/derived/weighted_prices_latest.json` 维护，由独立周更 workflow 刷新，不并入每日 `data-refresh` 全量模型管线。

### 许可证

本项目源代码采用 Apache License 2.0 开源。
