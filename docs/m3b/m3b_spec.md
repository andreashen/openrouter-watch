# M3B 规格说明书 — 模型信息增量合并与 Benchmark 保留

> 定位：M3 前的临时准备步骤（数据层），用于保证 `models_latest.json` 在平台字段波动下可持续维护。

## 阶段目标

在不改变整体流水线（`fetch -> normalize -> derive`）结构的前提下，引入“基于上一版产物增量更新”的能力，解决两类问题：

1. **模型下架可追踪**：当模型从 OpenRouter 最新模型列表中消失时，不直接丢失历史记录，而是在最新产物中标记“官方已移除”。
2. **Benchmark 空白不回退**：当最新 benchmark 某项被隐藏或返回空值时，保留上一版已成功提取的值；当最新值存在且更新时，覆盖旧值。

---

## 术语定义

- **上一版本**：本次运行前 `data/derived/models_latest.json` 指向的 JSON 文件。
- **当前版本**：本次运行中由最新 API 数据和 benchmark 结果生成的候选行集合。
- **官方已移除模型**：`model_id` 存在于上一版本，但不存在于当前 OpenRouter models API 返回列表中。
- **Benchmark 空白**：某 benchmark 指标字段在本次运行中为 `null` / 缺失（无论由隐藏、解析不到或临时失败导致）。

---

## 范围与非范围

### 范围（M3B 内）

- `data/derived/models_latest.json` 的合并更新策略。
- benchmark 三项字段的“新值覆盖 + 空白继承”策略：
  - `intelligence_index`
  - `coding_index`
  - `agentic_index`
- 相关测试与文档更新。

### 非范围（M3B 不做）

- 前端展示与交互改造（M3 主表交互仍按既有 M3 文档执行）。
- 新增额外 benchmark 字段或重做 benchmark 抓取接口。
- 历史产物清理策略（仅定义新增合并行为，不定义归档清理）。

---

## 功能需求

### R1. 模型信息表增量更新（含“官方移除”标记）

1. 本次产物构建时，必须读取上一版本 `models_latest.json`（若不存在则按首跑逻辑处理）。
2. 结果集合按 `model_id` 做并集：
   - 当前版本存在的模型：使用当前版本字段为主。
   - 仅上一版本存在的模型：保留上一版本记录，并标记为已移除。
3. 在产物中新增布尔字段：`officially_removed`。
   - 当前版本存在：`officially_removed = false`
   - 仅上一版本存在：`officially_removed = true`
4. 若某模型历史上被标记移除，但在当前版本重新出现，则恢复为 `officially_removed = false`，并按当前版本数据更新其字段。

---

### R2. Benchmark 指标合并策略（防空白覆盖）

对每个模型、每个 benchmark 指标字段，按以下优先级合并：

1. **当前值为有效数值**：覆盖上一版本对应字段。
2. **当前值为空白，上一版本为有效数值**：保留上一版本值（不被空白覆盖）。
3. **当前值与上一版本都为空白**：结果为 `null`。

补充规则：

- 对“官方已移除模型”，benchmark 字段沿用上一版本值（无当前值可覆盖）。
- 仅三项 benchmark 字段使用该回填逻辑，其他字段仍按当前版本优先或移除继承规则处理。

---

## 数据产物约束

1. `models_YYYYMMDD_HHMMSS.json/.csv` 与 `models_latest.json` 继续保持现有命名与输出方式。
2. 字段集合在原有 M1 字段基础上新增 `officially_removed`。
3. 排序规则维持现状（`vendor_name`, `model_id`），除非后续里程碑另行调整。

---

## 验收标准（M3B）

- [x] 当模型从最新 API 消失时，`models_latest.json` 仍保留该模型行且 `officially_removed=true`。
- [x] 当模型仍存在于最新 API 时，`officially_removed=false`。
- [x] benchmark 某项在本次为空、上次有值时，产物保留上次值。
- [x] benchmark 某项本次有更新值时，产物覆盖旧值。
- [x] benchmark 某项两次都为空时，产物为 `null`。
- [x] 相关测试覆盖“新增模型 / 移除模型 / benchmark 空白 / benchmark 更新”四类路径。

---

## 已决策澄清项

1. **移除模型保留时长**：永久保留于最新产物，清理策略留待后续里程碑。
2. **字段命名**：固定为 `officially_removed`。
3. **“空白”判定粒度**：`null`/缺失统一视为可回填，不区分来源。
4. **前端默认展示策略**：M3B 不改前端；M3 再定筛选/隐藏策略。
