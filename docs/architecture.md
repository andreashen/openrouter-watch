# 架构说明

本文描述 openrouter-watch **现行**系统结构。字段权威表见 [data-schema.md](./data-schema.md)；分支与发布运维见 [ops/main_test_release_flow.md](./ops/main_test_release_flow.md) 与 [ops/github_setup.md](./ops/github_setup.md)。

## 组件总览

系统由两块组成，无数据库、无长期驻留服务：

1. **Python 数据管线**（`src/openrouter_watch/` + `scripts/`）  
   从 OpenRouter 拉取模型元数据与 benchmark，规范化后写入 committed 产物 `data/derived/models_latest.json`。  
   加权输入价由独立侧车管线维护，见下文。
2. **Astro 静态前端**（`web/`）  
   构建时读取 `models_latest.json` 与 `weighted_prices_latest.json`，生成模型信息表，部署到 GitHub Pages。

```
OpenRouter APIs
      │
      ├─ daily: fetch → normalize → derive ──► data/derived/models_latest.json
      │                                         (+ models_meta.json)
      │
      └─ weekly: fetch_weighted_prices ──────► data/derived/weighted_prices_latest.json
                                                (+ weighted_prices_meta.json)
                                                      │
                                                      ▼
                                              Astro build (web/)
                                                      │
                                                      ▼
                                    GitHub Pages: /  与  /sit/
```

## 数据分层

| 层 | 路径 | Git | 说明 |
| --- | --- | --- | --- |
| raw | `data/raw/` | 忽略 | `/api/v1/models` 原始快照；只追加 |
| normalized | `data/normalized/` | 忽略 | Pydantic 类型化记录；可由 raw 重放 |
| derived | `data/derived/` | **提交** | 前端与审计消费的稳定产物 |

派生入口：`python scripts/fetch.py` → `normalize.py` → `derive.py`。

`derive.py` 会：

- 读取上一版 `models_latest.json`，按 `model_id` 做并集合并（下架模型保留并标记 `officially_removed`）。
- 对三项 benchmark 做「新值覆盖、空白回填上一版」。
- 写入普通文件 `models_latest.json`（**不是**软链接）与 `models_meta.json`。
- 清理遗留的时间戳 `models_*.json` / `models_*.csv`。

加权价入口：`python scripts/fetch_weighted_prices.py`（或周更 workflow），只更新 sidecar，**不得**改写 `models_latest.json`。

## GitHub Actions

| Workflow | 作用 |
| --- | --- |
| `deploy-pages.yml` | `main` / `test` 推送时组合构建生产站（root）与 SIT（`/sit/`）并部署 |
| `data-refresh.yml` | 每日 / 手动：在 `main` 上跑 `fetch → normalize → derive`；另支持 `reanchor_test` |
| `weighted-price-refresh.yml` | 周更加权输入价 sidecar |

凭据与 Pages 环境配置见 [ops/github_setup.md](./ops/github_setup.md)。

## 前端行为（`web/`）

唯一页面：`/`（模型信息表）。生产 URL：`https://andreashen.github.io/openrouter-watch/`；SIT：同域 `/sit/`。

### 数据加载

- 构建时 import `data/derived/models_latest.json`（必须为非空数组，否则构建失败）。
- 同时 import `weighted_prices_latest.json`，按 `model_id` 合并列 `weighted_avg_input_price_usd_per_1m`。
- 页头「数据更新时间」优先读 `models_meta.json` 的 `refreshed_at`。

### 表格列（展示）

Model ID、上下文、最大输出、输入价、加权输入价、输出价、Intelligence / Coding / Agentic、能力（R / T / V 角标，对应 Reasoning / Tools / Vision）、知识截止、发布日期、更新时间。

`author` / `slug` / `vendor_name` / `name` 不单独成列，但参与搜索匹配。字段定义见 [data-schema.md](./data-schema.md)。

### 交互（客户端，条件 AND）

- **搜索**：匹配 `model_id`、`vendor_name`、`name`、`author`、`slug`（大小写不敏感）。
- **厂商快筛**：固定主流厂商按钮（非按数据动态扩缩）。
- **能力筛选**：Reasoning / Tools / Vision 复选，勾选即要求对应字段为 `true`。
- **数值范围**：上下文、最大输出、输入/加权输入/输出价、三项 index 的 min/max；该字段为 `null` 且设置了范围时过滤掉该行。
- **排序**：上述数值字段及知识截止 / 发布日期 / 更新时间；`null` 始终排最后；同值回退 `model_id`。
- **已下架模型**：按 `officially_removed` 控制显示（默认隐藏）；下架行可带视觉弱化 / 徽章。
- **主题**：亮色 / 深色切换，持久化到 `localStorage`，可跟随系统偏好。

### 页头外链

- 部署网址：`https://andreashen.github.io/openrouter-watch/`（新标签，`noopener noreferrer`）。
- GitHub 仓库 +「给项目点个 Star」引导。

## 本地常用命令

```bash
pip install -e ".[dev]"
ruff check .
pytest
python scripts/fetch.py && python scripts/normalize.py && python scripts/derive.py

cd web && npm install && npm run dev    # :4321
cd web && npm run build
```

可选：`OPENROUTER_API_KEY` 提高限额。Live API：`RUN_LIVE_API=1 pytest tests/test_live_api.py -v`。

最低 Python：`pyproject.toml` 为 `>=3.11`；CI 使用 3.12。前端建议 Node.js 22+。
