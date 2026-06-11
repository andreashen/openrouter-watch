# M3B 任务清单

> 关联文档：`docs/m3b/m3b_spec.md`、`docs/m3b/m3b_plan.md`  
> 前置条件：M1 流水线可运行，`scripts/derive.py` 为当前派生入口

---

## T1 — 输出字段扩展（officially_removed）

文件：
- `src/openrouter_watch/deriver.py`
- `tests/test_deriver.py`

任务：
- [x] 在派生字段列表中新增 `officially_removed`（bool）。
- [x] 默认输出 `officially_removed=false`（当前模型路径）。
- [x] 更新字段完整性测试，断言新字段存在且类型符合预期。

---

## T2 — 读取上一版产物并建立索引

文件：
- `scripts/derive.py`
- `tests/test_scripts.py`

任务：
- [x] 在 `derive.py` 增加读取 `data/derived/models_latest.json` 的逻辑（不存在时返回空）。
- [x] 构建 `previous_map[model_id]` 与 `current_map[model_id]`。
- [x] 为“无上一版文件”的首跑场景补充测试，确保行为兼容当前版本。

---

## T3 — 模型并集与移除标记

文件：
- `scripts/derive.py`
- `tests/test_scripts.py`

任务：
- [x] 按 `model_id` 做并集合并当前/历史模型。
- [x] 仅历史存在的模型写入结果并标记 `officially_removed=true`。
- [x] 当前存在（含重新出现）的模型标记 `officially_removed=false`。
- [x] 增加“模型被移除/重新出现”测试用例。

---

## T4 — Benchmark 回填与覆盖

文件：
- `scripts/derive.py`
- （必要时）`src/openrouter_watch/deriver.py`
- `tests/test_scripts.py`

任务：
- [x] 对 `intelligence_index`、`coding_index`、`agentic_index` 实现逐字段 merge。
- [x] 新值有效时覆盖旧值。
- [x] 新值空白且旧值有效时保留旧值。
- [x] 两者均空时写 `null`。
- [x] 增加“空白回填 + 数值覆盖”测试用例。

---

## T5 — 验证与文档同步

文件：
- `docs/m3b/m3b_spec.md`
- `docs/m3b/m3b_plan.md`
- `docs/m3b/m3b_tasks.md`
- （可选）`README.md`

任务：
- [x] 运行针对性测试并记录结果（优先 `tests/test_scripts.py` 与 `tests/test_deriver.py`）。
- [x] 确认 `models_latest.json` 链接行为不回归。
- [x] 文档补充已决策的澄清项（保留时长、字段命名、前端展示策略）。

---

## M3B 完成标准

- [x] 规格中的 R1（模型移除标记）规则通过测试验证。
- [x] 规格中的 R2（benchmark 空白回填/更新覆盖）规则通过测试验证。
- [x] 首跑兼容、排序稳定、latest 软链接逻辑不回归。

---

## 已决策澄清项（2026-06-08）

1. **移除模型保留时长**：本期永久保留于 `models_latest.json`，不做自动清理。
2. **字段命名**：固定使用 `officially_removed`。
3. **空白判定**：`null`/缺失统一视为可回填空白，不区分隐藏与请求失败。
4. **前端展示**：M3B 不改前端；M3 阶段再决定是否默认隐藏或提供筛选。
