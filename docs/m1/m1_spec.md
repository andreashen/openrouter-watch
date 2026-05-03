# M1 规格说明书 — 模型信息抓取

## 阶段目标

从 OpenRouter 抓取全量模型信息，输出两个带时间戳的产物文件（CSV + JSON），每次运行都保留独立历史。
不涉及前端、不涉及排行榜、不涉及 endpoints 数据。

---

## 数据来源

| 接口 | 用途 |
|------|------|
| `GET https://openrouter.ai/api/v1/models` | 模型基础信息（必选） |
| `GET https://openrouter.ai/api/internal/v1/artificial-analysis-benchmarks?slug=<model_id>` | intelligence / coding / agentic index（可选，失败留空） |

---

## 输出字段（模型信息表）

| 字段名 | 来源 | 类型 | 说明 |
|--------|------|------|------|
| `model_id` | models API `.id` | str | 原始 id，如 `openai/gpt-4o` |
| `author` | 从 model_id 拆分 | str | `/` 左侧 |
| `slug` | 从 model_id 拆分 | str | `/` 右侧 |
| `vendor_name` | `.name` / `author` | str | 优先取 `.name` 冒号前缀；无冒号时回退到 `author` |
| `name` | `.name` | str | 展示名 |
| `context_length` | `.context_length` | int\|null | token 数 |
| `max_completion_tokens` | `.top_provider.max_completion_tokens` | int\|null | |
| `input_price_usd_per_1m` | `.pricing.prompt` | float\|null | Decimal 换算：原值 × 1,000,000，输出数值最多保留 6 位小数并去掉多余 0 |
| `output_price_usd_per_1m` | `.pricing.completion` | float\|null | Decimal 换算：原值 × 1,000,000，输出数值最多保留 6 位小数并去掉多余 0 |
| `supports_reasoning` | `.supported_parameters` | bool | 含 `reasoning` 或 `include_reasoning` |
| `supports_tools` | `.supported_parameters` | bool | 含 `tools` 或 `tool_choice` |
| `supports_vision` | `.architecture.modality` | bool | 含 `image` |
| `intelligence_index` | benchmark API | float\|null | 失败则留空 |
| `coding_index` | benchmark API | float\|null | 失败则留空 |
| `agentic_index` | benchmark API | float\|null | 失败则留空 |
| `fetched_at` | fetch API 时生成 | str | 原始抓取 API 的 UTC 时间，ISO8601 格式，如 `2026-04-17T02:00:00Z` |

---

## 产物文件

```
data/
  raw/                                # gitignored；脚本首次运行时自动创建
    YYYYMMDD_HHMMSS_models.json       # /api/v1/models 完整原始响应对象，含 fetched_at 元数据
  normalized/                         # gitignored；脚本首次运行时自动创建
    YYYYMMDD_HHMMSS_models.json       # NormalizedModel list（已类型化）
  derived/                            # committed；含 .gitkeep
    models_YYYYMMDD_HHMMSS.csv        # 单次运行模型信息表（人可读）
    models_YYYYMMDD_HHMMSS.json       # 单次运行模型信息表（前端/程序使用）
    models_latest.json                # 软链接：指向最新一份 models_*.json
```

---

## 代码结构

```
src/openrouter_watch/
  __init__.py
  fetcher.py        # fetch_models() -> dict（完整响应对象）
                    # fetch_benchmark(model_id) -> BenchmarkFetchResult
  schema.py         # Pydantic: RawModel, NormalizedModel
  normalizer.py     # normalize_model(raw) -> NormalizedModel
  deriver.py        # to_row(m: NormalizedModel) -> dict（扁平化，供 CSV/JSON 用）
scripts/
  fetch.py          # 拉取 raw → 保存 raw/
  normalize.py      # raw/ → normalized/
  derive.py         # normalized/ + benchmark → derived/
tests/
  fixtures/         # 离线 JSON fixture（从真实响应截取）
  test_fetcher.py
  test_normalizer.py
  test_deriver.py
```

---

## 关键实现规则

### fetcher.py
- 请求 models API 时携带 `User-Agent: Mozilla/5.0`（避免 403）
- 支持可选环境变量 `OPENROUTER_API_KEY`，设置时加入 `Authorization: Bearer` header
- `fetch_models()` 返回 `/api/v1/models` 完整响应对象；脚本保存时附加本次 API 抓取时间 `fetched_at`
- `fetch_benchmark(model_id)` 对所有模型调用，每次请求间隔 ≥ 0.5s（模块级 sleep）
- benchmark 抓取内部需区分状态：`ok`、`empty`、`http_error`、`timeout`、`network_error`、`parse_error`
- benchmark 接口返回 `200 {"data":[]}` 时记为 `empty`，表示无可用 benchmark 数据；最终 derived 文件不输出失败原因

### normalizer.py
- `author/slug` 拆分：`id.split("/", 1)`，无 `/` 时 author="" slug=id
- `vendor_name`：优先取 `name` 中第一个 `:` 之前的文本并 trim；无冒号或为空时回退到 `author`
- 价格换算：使用 `Decimal(pricing["prompt"]) * Decimal("1000000")`（API 单位是 USD/token），输出数值最多保留 6 位小数并去掉多余 0；`null`、空字符串、非数字转为 `null`
- `supports_reasoning`：`supported_parameters` 含 `"reasoning"` 或 `"include_reasoning"`
- `supports_tools`：含 `"tools"` 或 `"tool_choice"`
- `supports_vision`：`architecture.modality` 字符串含 `"image"`

### deriver.py
- 合并 NormalizedModel 与 benchmark 结果，输出扁平 dict
- 输出行顺序：先按 `vendor_name` 升序，再按 `model_id` 升序
- 写 CSV（utf-8-sig，方便 Excel 打开）
- 写 JSON（`ensure_ascii=False`，indent=2）
- 写 `models_latest.json`（创建/更新软链接，指向本次生成的 `models_*.json`）

---

## 数据分层约定

| 层 | 目录 | 内容 | 修改规则 | Git |
|----|------|------|----------|-----|
| raw | `data/raw/` | API 原始响应，不做任何处理 | 只追加，不修改 | **gitignored**（体积大） |
| normalized | `data/normalized/` | Pydantic 验证后的类型化记录 | 只追加，不修改 | **gitignored**（可由 raw 重新生成） |
| derived | `data/derived/` | 最终产物（CSV / JSON） | 每次运行按时间戳追加 + latest 覆盖写 | **committed**（历史追踪主体） |

M1 代码确认交付后，每日自动运行可将新的 derived 产物自动提交；M1 开发阶段只要求脚本正确生成产物。

---

## 环境变量

| 变量 | 必填 | 说明 |
|------|------|------|
| `OPENROUTER_API_KEY` | 否 | 设置后提升 API 限额，不设置以匿名方式请求 |

---

## 测试要求

- 单元测试优先使用本地 fixture / mock，保持稳定、快速
- 允许增加 live API 验证，用于覆盖最新 API 边界样本；live 测试应与默认单元测试分离，避免日常测试依赖网络
- `test_fetcher.py`：mock HTTP，验证字段提取和异常处理
- `test_normalizer.py`：验证价格换算、能力标签判断、author/slug 拆分边界情况
- `test_deriver.py`：验证 CSV/JSON 行数与字段完整性
- fixture 需覆盖最新 API 边界样本，包括缺失/异常 pricing、无 `/` 的 model_id、视觉模型、工具模型、reasoning 模型、benchmark 空数据

---

## M1 完成标准

- [x] `pytest` 默认测试全部通过，不依赖网络
- [x] `python scripts/fetch.py` 生成 `data/raw/YYYYMMDD_*.json`
- [x] `python scripts/normalize.py` 生成 `data/normalized/YYYYMMDD_*.json`
- [x] `python scripts/derive.py` 生成 `data/derived/models_YYYYMMDD_HHMMSS.csv` + `.json` + `models_latest.json`
- [x] derived 字段齐全，行数与 raw `.data` 一致，`models_latest.json` 软链接指向最新时间戳 JSON 文件
- [x] benchmark 允许部分为空；如果全部模型的 `intelligence_index`、`coding_index`、`agentic_index` 都为空，需标记为可疑并人工复核
- [x] 抽取若干 derived 记录，用浏览器访问 OpenRouter 模型页，核对网页展示与提取数据一致（名称、context、价格、能力标签、benchmark）
- [x] `ruff check .` 零报错
