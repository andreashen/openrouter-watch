# M3 任务清单

> 关联规格：`docs/m3/m3_spec.md`
> 前置条件：M1、M2 均已完成

---

## 前端任务（仅主表增强）

## T4 — 主表格增强

文件：`web/src/components/ModelTable.astro`

### T4.1 — 列展示去重

- [ ] 主表列删除：`author` / `slug` / `vendor_name` / `name`（仅保留 `model_id` 作为模型标识列）
- [ ] 保留其余数值列与能力列（context/max output/价格/能力/index/更新时间）

### T4.2 — 统一搜索框（“模型 id 筛选”入口）

- [ ] 新增搜索框：输入实时过滤（大小写不敏感）
- [ ] 匹配字段至少包含：`model_id`、`vendor_name`、`name`
- [ ] 与能力筛选、数值范围筛选为 AND 关系

### T4.3 — 能力筛选（AND）

- [ ] Reasoning / Tools / Vision 三个复选框
- [ ] 勾选则只显示该能力为 `true` 的行
- [ ] 多个复选框 AND

### T4.4 — 关键数值字段范围筛选（AND）

- [ ] 为以下字段提供 min/max：`context_length`、`max_completion_tokens`、`input_price_usd_per_1m`、`output_price_usd_per_1m`、`intelligence_index`、`coding_index`、`agentic_index`
- [ ] 行数据为 null 且该字段设置了 min/max 时，该行不满足（过滤掉）

### T4.5 — 关键数值字段排序

- [ ] 对以下字段提供升/降/无：`context_length`、`max_completion_tokens`、输入/输出价、三项 index、`fetched_at`
- [ ] null 始终排最后；同值回退到 `model_id`

### T4.6 — UI/UX 现代化升级

- [ ] **全局主题**：升级为科技感配色（深色/高对比度），添加全局渐变背景或网格背景。
- [ ] **表格视觉**：实现表头吸顶+毛玻璃效果，数据行 Hover 过渡动画，数值字体等宽化。
- [ ] **组件美化**：优化搜索框、下拉框、范围输入框的边框、阴影与聚焦状态（Focus Ring）。
- [ ] **状态展示**：将布尔值（Reasoning/Tools/Vision）转换为美观的徽章（Badge）或图标。

## T8 — 验收

- [ ] `cd web && npm run build` 无报错
- [ ] 主表仅展示 `model_id`（列去重达成）
- [ ] 搜索 + 能力复选 + 数值范围 + 排序可组合使用（AND），且结果数统计正确
- [ ] 页面视觉达到现代、科技化、美观、前沿的标准

---

## 延期到 M4 的内容（不属于本轮 M3）

Rankings 采集/diff、榜单页、详情页整体迁移到 `docs/m4/m4_ideas.md`。
