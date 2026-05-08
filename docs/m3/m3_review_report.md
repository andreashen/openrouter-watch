# M3 文档审阅报告（基于已闭环的 M1 / M2 与当前实现）

> 约束：M1、M2 文档已定稿，不修改；本报告仅对 M3 进行检查/校对并提出前端展示新增建议。
>
> 证据来源（仓库现状）：
> - M1 已闭环并有验收说明：`docs/m1/m1_acceptance.md`
> - M2 spec 限定只做“主表 + 厂商筛选”：`docs/m2/m2_spec.md`
> - 当前前端仅有 `/` 与 `ModelTable`：`web/src/pages/index.astro`、`web/src/components/ModelTable.astro`
> - `data/derived/` 中当前仅见 `models_*.json`，未见 `rankings*.json`

---

## 1. M3 与现状不一致/需要校对的点

### 1.1 “description 字段”在现有派生产物中不存在

- M3 spec 要求详情页展示 `description`（原 `3.6`）。
- 但当前 `data/derived/models_*.json` 行内字段不含 `description`；`web/src` 类型定义也未包含该字段。
- 结论：在“字段总表不变”的前提下，M3 不应再要求 `description`；如未来确需该字段，需作为 **M4+ 新增数据加工**（不回改 M1/M2 文档）。

### 1.2 M3 原文的 rankings 后端 + 榜单/详情页与本轮 M3 目标冲突

- 你已明确本轮 M3 选 **只做主表增强（选 C）**，并将 rankings 延期到 M4。
- 因此 M3 spec/tasks 中关于：
  - rankings 采集、diff、脚本、测试
  - `/rankings` 页面
  - `/models/[slug]` 详情页
  均应从 M3 移除，避免里程碑目标发散。

### 1.3 “筛选维度”与“去重展示”需要重写为一致的交互模型

你新增的核心诉求是：
- 主表增加搜索与筛选特性
- 关键数值类字段提供筛选与排序
- 列展示去重：不再同时展示 `model_id`/`slug`/`author`/`厂商`/`模型名称`，主表只展示 `model_id`；厂商、模型名称筛选合并为“模型 id 筛选”

这与 M3 原文“保留厂商下拉 + 能力复选 + 搜索框（model_id/name）”的表述不一致，需要在 M3 spec 中明确：
- **主表列**：只保留 `model_id` 作为唯一标识列
- **统一搜索框**：承载 `model_id` + `vendor_name` + `name` 的匹配（即“模型 id 筛选”的集合入口）
- **能力复选**：Reasoning/Tools/Vision 继续作为结构化筛选（AND）
- **数值筛选**：对 context/max output/价格/index 等提供范围筛选（AND）

### 1.4 “排序”需细化：字段类型、null 排序、稳定性

当前 M3 原文仅提“数值列按数值排序；null 排最后”。建议补齐：
- 允许排序的字段清单（数值/布尔/时间）
- null/NaN 处理（统一排末尾）
- 同值时的稳定排序规则（例如回退到 `model_id`）

---

## 2. 对 M3 的前端展示新需求建议（在字段总表不变前提下）

### 2.1 “一框搜全域” + 结构化筛选

- **一个搜索框**：输入任意关键词，匹配以下字段（大小写不敏感）：
  - `model_id`
  - `vendor_name`
  - `name`
- **结构化筛选**（与搜索 AND）：
  - 能力：Reasoning/Tools/Vision（复选 AND）
  - 数值范围：context/max output/输入价/输出价/三项 index（min/max）

### 2.2 列展示极简化（只展示 `model_id`）

- 表格左侧仅保留 `model_id`
- 其余识别信息（vendor/name/author/slug）不作为独立列展示
- 如需要“看一眼知道是什么”，可把 `model_id` 做成两行/带副标题的展示（仍算单列）

### 2.3 快捷筛选 chips（不新增字段、只用现有布尔/数值）

- 预设快捷条件，一键启用并可叠加：
  - “支持 Tools”
  - “支持 Reasoning”
  - “支持 Vision”
  - “有 benchmark（任一 index 非空）”
  - “免费/低价（输入/输出价 = 0 或低于阈值）”

### 2.4 筛选结果统计与可分享状态（可选）

- 显示：`显示 X / 总数`
- 可选：把筛选状态编码进 URL query（便于分享与复现）

---

## 3. 本次修订结论

- 本轮 M3 目标应收敛为：**字段总表不变** + **主表体验增强（搜索/筛选/排序/去重展示）**。
- 原 M3 中 rankings + 榜单/详情页整体迁移到 `docs/m4/m4_ideas.md`。

