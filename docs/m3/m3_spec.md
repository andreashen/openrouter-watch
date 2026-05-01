# M3 规格说明书 — 后端增强 + 前端完善

## 阶段目标

1. **后端**：新增 Rankings 数据采集，实现周榜周环比 diff
2. **前端**：新增列排序、多条件筛选、搜索框、模型详情页、独立榜单页

---

## 后端增强

### 3.1 Rankings 采集

**数据来源**：`https://openrouter.ai/rankings`（需带浏览器 UA，否则 403）

**采集内容**：
| 字段 | 说明 |
|------|------|
| `week_start` | 本周周一日期，格式 `YYYYMMDD` |
| `rank` | 当前榜单排名（1-N） |
| `model_id` | 映射后的完整 model id（如 `openai/gpt-4o`） |
| `token_volume` | 页面原始字符串（如 `1.75T`、`890B`） |
| `fetched_at` | 采集时间 UTC |

**slug 映射规则**（页面上是 slug，需还原为 model_id）：
1. 精确匹配 `data/derived/models_latest.json` 中的 model_id
2. 去掉日期后缀后匹配（如 `gpt-4o-20260211` → `gpt-4o`）
3. 按 author + name 相似度兜底；匹配失败则保留原始 slug，标记 `unmatched: true`

**产物文件**：
```
data/derived/
  rankings_YYYYMMDD.json     # 当周榜单（按采集日期命名）
  rankings_latest.json       # 覆盖写：始终为最新一份
```

---

### 3.2 Rankings 周环比 Diff

**触发时机**：每次采集 rankings 后自动计算

**对比逻辑**：当前运行结果与上一个 `rankings_*.json`（按文件名排序最新）做对比

**Diff 内容**：
| 变化类型 | 说明 |
|----------|------|
| `new_entry` | 本周新进榜（上周不存在） |
| `dropped` | 本周跌出榜单（上周存在，本周无） |
| `rank_up` | 排名上升（数字变小） |
| `rank_down` | 排名下降（数字变大） |
| `rank_unchanged` | 排名不变 |

**产物文件**：
```
data/derived/
  rankings_diff_YYYYMMDD.json   # 本次 diff 结果
  rankings_diff_latest.json     # 覆盖写：始终为最新一份
```

---

### 3.3 代码结构新增

```
src/openrouter_watch/
  rankings_fetcher.py   # fetch_rankings() -> list[dict]（含 slug 映射）
  rankings_differ.py    # diff_rankings(current, previous) -> list[dict]
scripts/
  fetch_rankings.py     # 采集 rankings → 保存 raw + derived
  diff_rankings.py      # 读最新两份 rankings，生成 diff
tests/
  test_rankings_fetcher.py
  test_rankings_differ.py
  fixtures/
    rankings_sample.html    # rankings 页面 HTML 片段（离线测试用）
    rankings_prev.json      # 上周榜单 fixture
    rankings_curr.json      # 本周榜单 fixture
```

---

## 前端完善

### 新增页面

| 路由 | 说明 |
|------|------|
| `/rankings` | 独立榜单页 |
| `/models/[model_id]` | 模型详情页（动态路由，Astro SSG） |

---

### 3.4 主表格新增特性

#### 列排序
- 点击任意列表头切换升序 / 降序 / 无排序
- 数值列（价格、context、benchmark index）按数值排序；null 排最后
- 当前排序列表头显示 ↑ / ↓ 指示符

#### 多条件筛选
- 厂商下拉（原有，保留）
- Reasoning / Tools / Vision 三个复选框，勾选则只显示该能力为 `true` 的行
- 多个筛选条件为 AND 关系

#### 搜索框
- 输入时实时过滤
- 匹配范围：`model_id`、`name`（大小写不敏感）
- 与厂商/能力筛选为 AND 关系

---

### 3.5 榜单页 `/rankings`

```
┌──────────────────────────────────┐
│  页头：周榜（周一日期）            │
├──────────────────────────────────┤
│  本周 Top N 表格：                 │
│  排名 | 模型名 | token量 | 环比变化 │
├──────────────────────────────────┤
│  环比变化说明（新进/跌出/涨跌幅）   │
└──────────────────────────────────┘
```

数据来源：`rankings_latest.json` + `rankings_diff_latest.json`

环比变化展示：
- 新进榜：绿色 `NEW`
- 跌出：不在表格中（或灰色标记）
- 排名上升：绿色 `↑N`（N 为上升位数）
- 排名下降：红色 `↓N`
- 不变：`—`

---

### 3.6 模型详情页 `/models/[model_id]`

**路由生成**：Astro `getStaticPaths()` 遍历 `models_latest.json`

**展示内容**：
- 所有 M1 字段（完整展示，不截断）
- `description` 字段完整展示（主表格中可能被截断）
- 如果该模型在最新榜单中，显示当前排名与 token 量

**URL 规则**：`model_id` 中的 `/` 替换为 `--`，如 `openai/gpt-4o` → `/models/openai--gpt-4o`

---

### 前端新增文件

```
web/src/
  pages/
    rankings.astro              # 榜单页
    models/
      [slug].astro              # 模型详情页（动态路由）
  components/
    ModelTable.astro            # 原有，增加排序/筛选/搜索逻辑
    RankingsTable.astro         # 新增：榜单表格
    ModelDetail.astro           # 新增：详情页内容区
```

---

## 数据分层新增产物

| 文件 | 层 | Git | 说明 |
|------|----|-----|------|
| `data/derived/rankings_YYYYMMDD.json` | derived | committed | 当周榜单快照 |
| `data/derived/rankings_latest.json` | derived | committed | 最新榜单 |
| `data/derived/rankings_diff_YYYYMMDD.json` | derived | committed | 周环比 diff |
| `data/derived/rankings_diff_latest.json` | derived | committed | 最新 diff |

---

## M3 完成标准

- [ ] `python scripts/fetch_rankings.py` 生成 `rankings_*.json`
- [ ] `python scripts/diff_rankings.py` 生成 `rankings_diff_*.json`，内容正确
- [ ] `pytest tests/test_rankings_fetcher.py tests/test_rankings_differ.py` 全部通过
- [ ] `/rankings` 页面正常展示榜单与环比变化
- [ ] `/models/[slug]` 详情页正常展示，description 完整
- [ ] 主表格列排序、多条件筛选、搜索框可用
- [ ] `ruff check .` 零报错，`npm run build` 无错误
