# M3D 实施规划 — latest 映射修正、前沿模型指标提取补强与前端状态筛选

**目标：** 修正 `~moonshotai/kimi-latest` 等 latest 标识模型与对应最新模型指标不一致的问题，提升 `opus-4.8`、`gpt-5.5-pro` 等前沿模型 benchmark 提取命中率，并补齐前端“latest/已下架”可见性控制。  
**架构：** 延续 `fetch.py -> normalize.py -> derive.py` 主链路，在 benchmark 拉取阶段增加“候选 slug + 多记录判定”策略；前端在现有 `ModelTable` 筛选层新增两个开关和“已下架”状态列。  
**技术栈：** Python 3.12、Astro、TypeScript、OpenRouter Models API、OpenRouter Internal Benchmark API。

---

## 当前基线（已确认）

1. 当前 benchmark 提取逻辑固定使用 `slug=model_id`，并且当接口返回多条记录时只取 `data[0]`。
2. 对 `~moonshotai/kimi-latest`，接口会返回多条记录，当前“取第一条”会得到与 `moonshotai/kimi-k2.6` 不一致的指数。
3. 对 `anthropic/claude-opus-4.8`，用 `model_id` 查询返回空；用 `canonical_slug`（如 `anthropic/claude-4.8-opus-20260528`）可取到指数，说明现有提取方式对新命名策略兼容不足。
4. `officially_removed` 已存在于派生数据，但前端尚未展示“已下架”列，也没有“隐藏已下架模型”开关。

---

## 待澄清问题（请审阅确认）

1. **latest 对齐口径**：`~xxx/latest` 是否必须与其对应“具体模型 ID”展示完全一致的三项指数？
2. **多记录选取策略**：当同一 slug 返回多条记录（如 high/medium/non-reasoning）时，业务上优先哪一条（默认、high、或与 `heuristic_openrouter_slug` 精确匹配）？
3. **`gpt-5.5-pro` 空指标处理**：若上游仍无指数，是否保持 `null`（前端显示 `—`），还是允许回退到同族模型指数（如 `gpt-5.5`）？
4. **前端开关默认值**：`隐藏 latest 标识模型`、`隐藏已下架模型` 是否默认开启？
5. **筛选持久化**：两个新开关是否需要写入 URL / localStorage，还是仅当前页会话生效？

---

## 实施阶段

## P1 — 指标映射规则定稿（先决策后开发）

- 固化 latest 模型与具体模型之间的映射与一致性规则。
- 固化 benchmark 多记录选取优先级与空值回退边界。
- 固化前端两个新增开关的默认行为与是否持久化。

## P2 — Benchmark 提取链路补强（后端）

- 在 normalize 阶段保留并传递 `canonical_slug`（供 derive 阶段兜底查询）。
- 在 benchmark 获取逻辑中改为候选查询策略（至少包含 `model_id` + `canonical_slug`）。
- 在多记录场景下引入可解释的选择规则（不再固定取 `data[0]`）。
- 保持与 M3B 的 benchmark 回填机制兼容（新值优先、空值回填历史值）。

## P3 — latest 标识模型指标对齐（后端）

- 对 `~` 前缀模型定义“目标记录”解析规则，避免与具体最新模型出现系统性偏差。
- 为 `~openai/gpt-latest`、`~moonshotai/kimi-latest` 等典型别名增加回归样例。

## P4 — 前端筛选与状态展示增强（前端）

- 在表格新增“已下架”列：`officially_removed=true` 显示 `✓`，否则显示 `—`。
- 新增开关：`隐藏 latest 标识模型`（过滤 `model_id` 以 `~` 开头的行）。
- 新增开关：`隐藏已下架模型`（过滤 `officially_removed=true` 的行）。
- 确保新开关与现有搜索/能力/范围/排序保持 AND 组合关系。

## P5 — 验证与回归

- 后端：补充 `tests/test_fetcher.py` 与 `tests/test_scripts.py` 的查询回退、多记录选取、latest 对齐用例。
- 前端：验证列展示、两个开关与现有筛选/计数联动逻辑。
- 运行针对性校验：`pytest`（指定测试文件） + `cd web && npm run check && npm run build`。

## P6 — 文档与交付同步

- 新增并维护 `docs/m3d/*` 文档（spec/tasks 可在规则确认后补齐）。
- 在 `docs/readme.md` 注册 `m3d` 目录定位，保证里程碑导航一致。

---

## 风险与应对

1. **风险：内部 benchmark 接口字段再次变化**
   - 应对：提取逻辑基于“候选字段 + 容错降级”，并为关键字段缺失场景补测试。
2. **风险：上游确实未提供某些模型指数（非提取缺陷）**
   - 应对：在规则中区分“提取失败”与“上游无数据”，避免误判为系统 bug。
3. **风险：新增过滤开关导致用户对“总数”理解偏差**
   - 应对：明确“显示条数/总条数”语义，并在 UI 文案中保持一致。

---

## 交付物

- `docs/m3d/m3d_plan.md`（本次）
- 后续实现阶段代码改动（`src/openrouter_watch/*`、`scripts/derive.py`、`web/src/components/ModelTable.astro`、相关测试）
- （可选）`docs/m3d/m3d_spec.md`、`docs/m3d/m3d_tasks.md`
