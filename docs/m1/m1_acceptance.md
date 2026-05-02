# M1 数据验收说明

本文档对应 `docs/m1/m1_tasks.md` T8 与 `docs/m1/m1_spec.md` 中的数据与人工核对要求。

## 1. 字段与行数

- **字段齐全**：derived 每行包含 `model_id`、`author`、`slug`、`vendor_name`、`name`、上下文与价格字段、三项 `supports_*`、三项 benchmark index、`fetched_at`，与规格表一致。
- **行数一致**：同一次流水线中，raw JSON 根对象下 `.data` 数组长度与 derived（CSV/JSON）行数一致。

## 2. Benchmark

- 允许部分模型 index 为空。
- 若**全部**模型的 `intelligence_index`、`coding_index`、`agentic_index` 均为空，视为可疑，需人工复核（接口、限流、解析等）。

## 3. 浏览器抽样

抽取若干条 derived 记录，在 OpenRouter 模型页面核对：名称、context、价格、能力标签、benchmark 等与页面展示一致。

## 4. 自动化测试（离线）

```bash
ruff check .
pytest
```

## 5. 可选：Live API

对真实 OpenRouter 接口的验证（需网络，默认不参与 `pytest`）：

```bash
RUN_LIVE_API=1 pytest tests/test_live_api.py -v
```

可选设置 `OPENROUTER_API_KEY` 以提高限额。
