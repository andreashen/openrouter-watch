# M4 Ideas — Rankings & 详情页（从 M3 延期）

> 来源：原 `docs/m3/m3_spec.md` / `docs/m3/m3_tasks.md` 中的 rankings 与详情/榜单页内容，按最新决策整体延期到 M4。
> 约束：**不回改** M1、M2 既定文档；M4 如需新增数据产物或字段，应明确为 M4 新增要求。

---

## 1. 后端：Rankings 采集（原 M3 3.1）

- **数据来源**：`https://openrouter.ai/rankings`（需带浏览器 UA，否则 403）
- **采集字段**：
  - `week_start`：本周周一日期，格式 `YYYYMMDD`
  - `rank`：排名（1-N）
  - `model_id`：映射后的完整 model id（如 `openai/gpt-4o`）
  - `token_volume`：页面原始字符串（如 `1.75T`、`890B`）
  - `fetched_at`：UTC 采集时间
- **slug → model_id 映射规则**：
  1. 精确匹配 `data/derived/models_latest.json` 中的 `model_id`
  2. 去掉日期后缀后匹配（如 `gpt-4o-20260211` → `gpt-4o`）
  3. 兜底：保留原始 slug，并标记 `unmatched: true`（原文档提到“相似度兜底”，可在 M4 再决定是否引入）
- **产物**（建议沿用原 M3）：
  - `data/derived/rankings_YYYYMMDD.json`
  - `data/derived/rankings_latest.json`

## 2. 后端：Rankings 周环比 Diff（原 M3 3.2）

- **对比逻辑**：当前运行结果 vs 上一个 `rankings_*.json`（按文件名排序最新）
- **变化类型**：
  - `new_entry`、`dropped`、`rank_up`、`rank_down`、`rank_unchanged`
- **产物**：
  - `data/derived/rankings_diff_YYYYMMDD.json`
  - `data/derived/rankings_diff_latest.json`

## 3. 前端：榜单页与模型详情页（原 M3 3.5 / 3.6）

> M3 已明确仅优化主表；如需继续丰富体验，可在 M4 以 rankings 数据为依托补齐页面体系。

- **页面**：
  - `/rankings`：榜单页（Top N + 环比变化展示）
  - `/models/[slug]`：模型详情页（完整字段展示 + 若在榜单则展示 rank/token）
- **数据来源**：
  - `models_latest.json`（现有）
  - `rankings_latest.json`、`rankings_diff_latest.json`（M4 新增）

## 4. 工程任务清单（从 M3 迁移）

- 后端
  - `src/openrouter_watch/rankings_fetcher.py`
  - `src/openrouter_watch/rankings_differ.py`
  - `scripts/fetch_rankings.py`
  - `scripts/diff_rankings.py`
  - `tests/test_rankings_fetcher.py`
  - `tests/test_rankings_differ.py`
  - `tests/fixtures/rankings_sample.html`
  - `tests/fixtures/rankings_prev.json`
  - `tests/fixtures/rankings_curr.json`
- 前端
  - `web/src/pages/rankings.astro`
  - `web/src/components/RankingsTable.astro`
  - `web/src/pages/models/[slug].astro`
  - `web/src/components/ModelDetail.astro`

