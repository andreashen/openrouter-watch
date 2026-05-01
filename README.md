# OpenRouter Watch

**Status:** Work in progress — implementation not available yet.

Track OpenRouter model metadata, pricing, rankings, and historical changes, then publish them as a static website.

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
scripts/           # Entry-point scripts (fetch, normalize, derive)
src/openrouter_tracker/  # Core library
tests/             # pytest tests
data/raw/          # Raw API snapshots (gitignored)
data/normalized/   # Pydantic-validated records (gitignored)
data/derived/      # CSV + JSON products (committed)
web/               # Astro frontend for the model table
docs/              # Milestone specs and task lists
```

## Development

```bash
# Run tests
pytest

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

OpenRouter Watch 是一个用于监控 OpenRouter 模型数据的工具，它可以自动从 OpenRouter 获取模型数据，记录模型的元数据、定价、排名和历史变化，然后将这些数据发布为一个静态网站。

### 快速开始

### 数据来源

数据来源与第三方条款说明详见 [NOTICE](NOTICE)。

### 许可证

本项目源代码采用 Apache License 2.0 开源。
