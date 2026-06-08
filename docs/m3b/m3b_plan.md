# M3B 实施规划 — 模型增量合并与 Benchmark 回填

**目标：** 在现有 M1 数据流水线上新增“上一版合并”能力，避免模型下架和 benchmark 空白导致的信息丢失。  
**架构：** 保持 `fetch.py -> normalize.py -> derive.py` 主链路不变，仅在 `derive.py` 增加“读取上一版 + 按 model_id 合并 + 输出”步骤。  
**技术栈：** Python 3.12、现有 `openrouter_watch` 模块、`pytest`。

---

## 实施原则

1. **最小入侵**：尽量不改 `fetch`/`normalize`，把状态合并逻辑集中在 `derive` 阶段。
2. **向后兼容**：首跑（无 `models_latest.json`）时保持当前行为。
3. **可验证**：每条规则必须有对应测试覆盖，避免“看起来正确”。

---

## 实施阶段

## P1 — 数据模型与字段清单对齐

- 在派生输出字段中新增 `officially_removed`（bool）。
- 明确 CSV/JSON 字段顺序与默认值（默认 `false`）。

## P2 — 上一版读取与模型并集合并

- 在 `derive.py` 增加读取上一版 `models_latest.json` 的逻辑（不存在则返回空映射）。
- 以 `model_id` 为键构建 `previous_map` 和 `current_map`。
- 生成最终 `merged_rows`：
  - 当前存在：以当前行为主，`officially_removed=false`
  - 仅历史存在：沿用历史行，`officially_removed=true`

## P3 — benchmark 字段回填策略

- 对三项 benchmark 字段实现逐字段 merge：
  - 当前值有效 -> 覆盖
  - 当前值空、历史值有效 -> 回填历史值
  - 两者都空 -> `null`

## P4 — 测试与回归验证

- 补充/更新单测，覆盖：
  - 移除模型标记
  - benchmark 空白回填
  - benchmark 更新覆盖
  - 首跑兼容
- 运行针对性测试（`pytest` 指定文件）。

## P5 — 文档与发布准备

- 更新 `docs/m3b/*` 与必要的 README 段落。
- 形成变更说明，供后续 M3 主线执行时引用。

---

## 风险与应对

1. **风险：旧产物字段与新字段不一致**
   - 应对：读取旧版时用容错访问（缺失 `officially_removed` 视为 `false`）。
2. **风险：benchmark “空白”来源复杂（隐藏/失败/超时）**
   - 应对：M3B 先统一按空值回填；若需细分，后续再扩展状态字段。
3. **风险：移除模型长期累积导致文件膨胀**
   - 应对：本期只保证正确性；清理策略作为后续独立决策项。

---

## 交付物

- `docs/m3b/m3b_spec.md`
- `docs/m3b/m3b_plan.md`
- `docs/m3b/m3b_tasks.md`
- 后续实现阶段对应代码与测试改动（不在本次文档提交内）
