# M3 任务清单

> 关联规格：`docs/m3/m3_spec.md`
> 前置条件：M1、M2 均已完成

---

## 后端任务

## T1 — Rankings Fetcher

文件：`src/openrouter_watch/rankings_fetcher.py`

- [ ] 实现 `fetch_rankings() -> list[dict]`：抓取 `https://openrouter.ai/rankings`，带浏览器 UA  
- [ ] 提取 Top N 榜单：slug、排名、token 量（保留原始字符串）  
- [ ] 提取 `week_start`（本周周一日期，从页面或当前日期推算）  
- [ ] 实现 slug 映射：精确匹配 → 去日期后缀匹配 → 兜底保留原始（标记 `unmatched: true`）  
- [ ] 准备 `tests/fixtures/rankings_sample.html`（真实页面 HTML 片段）  
- [ ] `tests/test_rankings_fetcher.py`：mock HTTP，验证提取与映射逻辑  

## T2 — Rankings Differ

文件：`src/openrouter_watch/rankings_differ.py`

- [ ] 实现 `diff_rankings(current: list[dict], previous: list[dict]) -> list[dict]`  
- [ ] 覆盖 5 种变化类型：`new_entry`, `dropped`, `rank_up`, `rank_down`, `rank_unchanged`  
- [ ] 准备 `tests/fixtures/rankings_prev.json` 和 `rankings_curr.json`  
- [ ] `tests/test_rankings_differ.py`：验证各变化类型判断、边界情况（首次运行无上周数据）  

## T3 — Rankings 入口脚本

- [ ] `scripts/fetch_rankings.py`：调用 `fetch_rankings()`，保存 `data/derived/rankings_YYYYMMDD.json` + `rankings_latest.json`  
- [ ] `scripts/diff_rankings.py`：读最新两份 rankings 文件，生成 `rankings_diff_YYYYMMDD.json` + `rankings_diff_latest.json`；若只有一份则跳过（首次运行）  

---

## 前端任务

## T4 — 主表格增强

文件：`web/src/components/ModelTable.astro`

- [ ] 列排序：点击表头切换 升/降/无，数值列按数值排序，null 排最后，表头显示 ↑↓ 指示符  
- [ ] 多条件筛选：新增 Reasoning / Tools / Vision 三个复选框，与厂商筛选 AND 组合  
- [ ] 搜索框：实时过滤 `model_id` 和 `name`（大小写不敏感），与其他筛选 AND 组合  

## T5 — 榜单页

文件：`web/src/pages/rankings.astro`、`web/src/components/RankingsTable.astro`

- [ ] 读取 `rankings_latest.json` + `rankings_diff_latest.json`  
- [ ] 展示 Top N 表格：排名 / 模型名 / token 量 / 环比变化  
- [ ] 环比变化样式：新进 → 绿色 `NEW`；上升 → 绿色 `↑N`；下降 → 红色 `↓N`；不变 → `—`  
- [ ] 页头展示当前周榜日期（`week_start`）  

## T6 — 模型详情页

文件：`web/src/pages/models/[slug].astro`、`web/src/components/ModelDetail.astro`

- [ ] `getStaticPaths()` 遍历 `models_latest.json`，URL 规则：`openai/gpt-4o` → `openai--gpt-4o`  
- [ ] 展示所有 M1 字段（完整，不截断），`description` 字段完整展示  
- [ ] 若该模型在 `rankings_latest.json` 中，展示当前排名与 token 量  
- [ ] 主表格中模型名可点击跳转详情页  

## T7 — 数据复制脚本更新

文件：`scripts/copy_data.py`

- [ ] 同步复制 `rankings_latest.json` 和 `rankings_diff_latest.json` 到 `web/public/data/`  

## T8 — 验收

- [ ] `pytest` 全量通过（含 M1 原有测试）  
- [ ] `python scripts/fetch_rankings.py && python scripts/diff_rankings.py` 无报错  
- [ ] `cd web && npm run build` 无报错，`/rankings` 和 `/models/[slug]` 页面可访问  
- [ ] 主表格排序 / 筛选 / 搜索组合使用正常  
- [ ] `ruff check .` 零报错  
