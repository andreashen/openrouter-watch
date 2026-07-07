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
scripts/                 # Entry-point scripts (fetch, normalize, derive)
src/openrouter_watch/    # Core library (fetcher, normalizer, deriver, schema)
tests/                   # pytest tests
data/raw/                # Raw API snapshots (gitignored)
data/normalized/         # Pydantic-validated records (gitignored)
data/derived/            # Stable committed dataset (models_latest.json)
web/                     # Astro frontend for the model table
docs/                    # Milestone specs, task lists, and release runbooks
```

**About `docs/m1/`, `m2/`, …:** The **`m` prefix means milestone** (e.g. `m1` = Milestone 1). Higher numbers usually build on earlier milestones. Full wording: [docs/readme.md](docs/readme.md).

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

`derive.py` 会为每个模型请求 benchmark 接口并节流，完整运行可能需数分钟。M1 数据验收与闭环说明见 [docs/m1/m1_acceptance.md](docs/m1/m1_acceptance.md)。

**关于 `docs/m1/`、`m2/` 等目录：** 前缀 **`m` 表示 milestone（里程碑）**（如 `m1` 即第 1 个里程碑）；数字越大通常越靠后、并可能依赖前置里程碑的交付物。完整说明见 [docs/readme.md](docs/readme.md)。

### 数据来源

数据来源与第三方条款说明详见 [NOTICE](NOTICE)。

### 许可证

本项目源代码采用 Apache License 2.0 开源。
