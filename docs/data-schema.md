# 数据 Schema（现行）

权威字段表。实现以 `src/openrouter_watch/deriver.py` 的 `_FIELDS` 与 `src/openrouter_watch/weighted_prices.py` 的 `WEIGHTED_FIELDS` 为准；本文与代码冲突时以代码为准并应回写本文。

架构与管线说明见 [architecture.md](./architecture.md)。

## 产物文件

| 文件 | 写入方 | 说明 |
| --- | --- | --- |
| `data/derived/models_latest.json` | `scripts/derive.py`（日更 / 手动） | 模型行数组；普通 committed 文件，非软链接 |
| `data/derived/models_meta.json` | 同上 | 例如 `{"refreshed_at": "<ISO8601 UTC>"}` |
| `data/derived/weighted_prices_latest.json` | `scripts/fetch_weighted_prices.py`（周更） | 加权输入价 sidecar |
| `data/derived/weighted_prices_meta.json` | 同上 | 抓取统计与时间戳 |

遗留的时间戳 `models_*.json` / `models_*.csv` 在 derive 成功写入后会被清理。

---

## `models_latest.json` 行字段

顺序与 `deriver._FIELDS` 一致。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `model_id` | string | OpenRouter 模型 id，如 `openai/gpt-4o` |
| `author` | string | `model_id` 中 `/` 左侧；无 `/` 时为空 |
| `slug` | string | `model_id` 中 `/` 右侧；无 `/` 时为整段 id |
| `vendor_name` | string | 优先取展示名中第一个 `:` 前缀；否则回退 `author` |
| `name` | string | 展示名 |
| `openrouter_model_url` | string \| null | OpenRouter 模型页 URL（若可得） |
| `context_length` | number \| null | 上下文长度（token） |
| `max_completion_tokens` | number \| null | 最大输出 token |
| `input_price_usd_per_1m` | number \| null | 输入价 USD / 1M tokens（由 API per-token 价 × 1e6） |
| `output_price_usd_per_1m` | number \| null | 输出价 USD / 1M tokens |
| `supports_reasoning` | boolean | `supported_parameters` 含 `reasoning` 或 `include_reasoning` |
| `supports_tools` | boolean | 含 `tools` 或 `tool_choice` |
| `supports_vision` | boolean | `architecture.modality` 含 `image` |
| `intelligence_index` | number \| null | Artificial Analysis intelligence；可合并回填 |
| `coding_index` | number \| null | coding index；可合并回填 |
| `agentic_index` | number \| null | agentic index；可合并回填 |
| `knowledge_cutoff` | string \| null | 知识截止日期 `YYYY-MM-DD` |
| `released_at` | string \| null | 发布日 `YYYY-MM-DD`（UTC，由 API `created` 推导） |
| `officially_removed` | boolean | 当前 models API 已不返回该 id，但历史行仍保留 |
| `fetched_at` | string | 本行关联的 models API 抓取时间（ISO8601 UTC） |
| `updated_at` | string | 相对上一版有实质字段变更时记为本次 `refreshed_at`，否则继承上一版 `updated_at`/`fetched_at`（追踪字段不含 `fetched_at`/`updated_at`/pointer 元数据） |
| `is_pointer` | boolean | 是否为 rolling / tilde 等指针类 model id |
| `pointer_target_id` | string \| null | 解析到的具体版本 `model_id`（若有） |
| `pointer_kind` | string \| null | 如 `tilde_latest` / `slug_latest` |

### 增量合并规则（derive）

1. **并集**：当前 API 有的模型以当前行为主，`officially_removed=false`；仅上一版有的保留，`officially_removed=true`。
2. **重新出现**：曾标记移除后又出现在 API 中 → `officially_removed=false`，字段按当前版更新。
3. **Benchmark 三项**（`intelligence_index` / `coding_index` / `agentic_index`）：
   - 当前值为有效数值 → 覆盖；
   - 当前空白且上一版有效 → 保留上一版；
   - 两者皆空 → `null`。
4. **首跑**：无上一版 `models_latest.json` 时按当前行写入，默认 `officially_removed=false`。

排序：`vendor_name` 升序，再 `model_id` 升序。

---

## `weighted_prices_latest.json` 行字段

与 `models_latest` **分离**；前端构建时按 `model_id` join。数据源为 OpenRouter 前端 Effective Pricing 接口（非官方 Models API 契约），详见根目录 [NOTICE](../NOTICE)。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `model_id` | string | 与模型表对齐的 id |
| `weighted_avg_input_price_usd_per_1m` | number \| null | 加权平均输入价 USD / 1M；≤0 或缺失视为 `null`；最多 4 位小数 |
| `weighted_price_fetched_at` | string \| null | 本次侧车抓取时间（ISO8601 UTC） |
| `weighted_price_source` | string | 固定标记，如 `openrouter_frontend_effective_pricing` |
| `permaslug` | string \| null | catalog 解析出的 permaslug（抓取用） |

合并策略概要：新有效价在超过相对/绝对阈值时覆盖旧值；空白不抹掉上一版有效价（与 benchmark 回填类似）。具体阈值见 `weighted_prices.price_changed`。

---

## 前端合并视图

页面行 = `models_latest` 行 + 可选列 `weighted_avg_input_price_usd_per_1m`（来自 sidecar；无匹配则为 `null`）。  
加权价**不是** `models_latest.json` 的持久字段。
