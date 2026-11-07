# Artificial Analysis 直连验收清单

## 功能验收

- [x] 同一 OpenRouter id 出现在 rule 和 group 时映射被拒绝，且不产生边
- [x] group 在 UUID 和 slug 都真实、但缺少成员依据或依据未覆盖时失败
- [x] 共同证据可以覆盖全部成员；`openrouter_api_id` 不能作为共同证据
- [x] 分页总页数变化、`has_more` 异常、重复 UUID 不写快照
- [x] 当前快照的空分不会被另一份快照填上
- [x] 没有 G0 记录时，公开展示仍是 OpenRouter，停采请求也不会停采
- [x] 主榜页面不引用 AA 显示模块
- [x] 提交的 `publication.json` 保持展示源 `openrouter` 且继续采集

## 质量验收

- [x] `pytest`（不含 live API）与相关 `ruff check` 通过
- [x] `python scripts/validate_aa_mapping.py` 通过
- [x] 前端 `node --test src/lib/aaScoreDisplay.test.js` 通过
- [x] 错误时丢弃整次抓取，不写半份快照
- [x] 文档写明公开路径未切换

## 交付

- [x] 规格、任务和 ADR 与映射契约一致
- [x] 分支名为 `feat/aa-direct-benchmarks`
