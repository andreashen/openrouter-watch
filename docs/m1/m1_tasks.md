# M1 任务清单

> 关联规格：`docs/m1/m1_spec.md`

## T1 — 项目骨架初始化

- [x] 创建目录结构：`scripts/`, `src/openrouter_watch/`, `tests/fixtures/`, `data/raw/`, `data/normalized/`, `data/derived/`
- [x] 创建 `pyproject.toml`（含 `httpx`, `pydantic`, `pandas`, `ruff`, `pytest` 依赖）
- [x] 创建 `src/openrouter_watch/__init__.py`
- [x] 创建 `.gitignore`（忽略 `data/raw/`, `data/normalized/`, `__pycache__/`, `.env`, `*.pyc`；`data/derived/` 不忽略）
- [x] 在 `data/derived/` 放 `.gitkeep`（使该目录进入 git；`data/raw/` 和 `data/normalized/` 由脚本运行时自动 mkdir -p 创建，无需 gitkeep）

## T2 — Pydantic Schema

文件：`src/openrouter_watch/schema.py`

- [x] 定义 `RawModel`（接近 API 原文，除 `id` 外字段宽松可选，允许 extra 字段）
- [x] 定义 `NormalizedModel`（类型化，含 `author`, `slug`, `vendor_name`, `supports_*` 布尔字段）

## T3 — Fetcher

文件：`src/openrouter_watch/fetcher.py`

- [x] 实现 `fetch_models()`：GET `/api/v1/models`，返回完整响应对象；后续处理从 `.data` 读取模型列表
- [x] 实现 `fetch_benchmark(model_id: str)`：GET benchmark 接口，区分 `ok`、`empty`、`http_error`、`timeout`、`network_error`、`parse_error`，每次调用 sleep 0.5s

## T4 — Normalizer

文件：`src/openrouter_watch/normalizer.py`

- [x] 实现 `normalize_model(raw: dict) -> NormalizedModel`
- [x] 覆盖所有字段转换规则（价格 Decimal 换算并最多保留 6 位小数、能力标签、author/slug 拆分、vendor_name 推导、fetched_at 继承 raw 抓取时间）

## T5 — Deriver

文件：`src/openrouter_watch/deriver.py`

- [x] 实现 `to_row(model: NormalizedModel, benchmark) -> dict`（扁平化；benchmark 失败原因不进入最终 CSV/JSON）
- [x] 实现 `write_csv(rows, path)`（utf-8-sig）
- [x] 实现 `write_json(rows, path)`（ensure_ascii=False, indent=2）

## T6 — 入口脚本

- [x] `scripts/fetch.py`：调用 models API，保存完整响应对象到 `data/raw/YYYYMMDD_HHMMSS_models.json`，并写入抓取时刻供 `fetched_at` 继承
- [x] `scripts/normalize.py`：读最新 raw 文件，逐条 normalize，保存 `data/normalized/YYYYMMDD_HHMMSS_models.json`
- [x] `scripts/derive.py`：读最新 normalized 文件，逐条拉 benchmark（含节流），按 `vendor_name`、`model_id` 排序，写 `models_YYYYMMDD_HHMMSS.csv/json` + `models_latest.json`（软链接指向最新 json）

## T7 — 测试

- [x] 准备 `tests/fixtures/models_sample.json`（从真实 API 截取 5~10 条，覆盖缺省价格、免费模型、视觉、tools、reasoning、无 `/` model_id 等边界样本）
- [x] 准备 `tests/fixtures/benchmark_sample.json`（单条 benchmark 响应）
- [x] `tests/test_fetcher.py`：mock HTTP，验证正常响应、网络异常、benchmark `ok/empty/http_error/timeout/network_error/parse_error`
- [x] `tests/test_normalizer.py`：验证 Decimal 价格换算精度、能力标签边界、无 `/` 的 model_id、vendor_name 推导、fetched_at 继承
- [x] `tests/test_deriver.py`：验证输出行数、字段完整性、排序规则、`models_latest.json` 软链指向最新 json、CSV 可被 pandas 读取
- [x] 增加 live API 验证命令或测试标记，允许手动/定时运行以覆盖最新 API 边界样本

## T8 — 配置与文档

- [x] 创建 `.env.example`（含 `OPENROUTER_API_KEY=`）
- [x] 创建 `README.md`（项目简介、本地运行方法、环境变量说明、目录结构）
- [x] 确认 `ruff check .` 零报错，`pytest` 全部通过
- [x] 编写 M1 数据验收说明：校验字段齐全、raw/derived 行数一致、benchmark 非全空、抽样浏览器核对 OpenRouter 页面数据
