# M3C 任务清单

> 关联文档：`docs/m3c/m3c_spec.md`、`docs/m3c/m3c_plan.md`  
> 前置条件：现有 `main` 分支 Pages 工作流可正常构建与发布

---

## T1 — SIT 发布目标与链接规则确认

文件：
- `docs/m3c/m3c_spec.md`
- （后续实现）`.github/workflows/deploy-pages-sit.yml` 或 `.github/workflows/deploy-pages.yml`

任务：
- [ ] 明确 `test` 分支作为 SIT 触发分支。
- [ ] 明确 SIT 链接“原链接 + `/sit/` 子路径”的实现映射。
- [ ] 明确 SIT 与现网隔离方式（独立目标或独立路径）。

---

## T2 — SIT Pages 工作流配置

文件：
- （后续实现）`.github/workflows/deploy-pages-sit.yml`（推荐新增）
- （可选）`.github/workflows/deploy-pages.yml`（若采用单工作流扩展）

任务：
- [ ] 配置 `push` 到 `test` 的触发条件。
- [ ] 复用现有 Astro 构建流程并注入 SIT 站点参数。
- [ ] 发布完成后输出 SIT URL 供验证。

---

## T3 — 数据刷新工作流（自动替代手工执行）

文件：
- （后续实现）`.github/workflows/data-refresh.yml`
- `scripts/fetch.py`
- `scripts/normalize.py`
- `scripts/derive.py`

任务：
- [ ] 新增工作流执行 `python3 scripts/fetch.py && python3 scripts/normalize.py && python3 scripts/derive.py`。
- [ ] 配置触发策略：`workflow_dispatch` + `schedule`（可选补充 `push`）。
- [ ] 配置 `OPENROUTER_API_KEY` Secret（可选但推荐）。

---

## T4 — 回写策略与防循环

文件：
- （后续实现）`.github/workflows/data-refresh.yml`
- （可选）`.github/workflows/deploy-pages*.yml`

任务：
- [ ] 确定回写文件范围（`models_latest.json` 与时间戳产物）。
- [ ] 自动提交到目标分支并保留可审计记录。
- [ ] 增加防循环策略（路径过滤/条件判断/提交标识）。

---

## T5 — 验证与文档同步

文件：
- `docs/m3c/m3c_spec.md`
- `docs/m3c/m3c_plan.md`
- `docs/m3c/m3c_tasks.md`
- `docs/readme.md`

任务：
- [ ] 验证 `test` 分支触发后 SIT 页面可访问。
- [ ] 验证数据刷新工作流可独立执行并产出更新。
- [ ] 同步文档中的结论、约束与待澄清项，确保团队可直接执行。

---

## M3C 完成标准

- [ ] SIT 发布链路已定义并可从 `test` 分支触发。
- [ ] SIT 链接规则符合“原链接 + `/sit/` 子路径”要求。
- [ ] 数据更新自动化结论明确：GitHub Actions 可替代开发机手工流程。
- [ ] 已定义触发、密钥、回写、防循环与验证策略。
