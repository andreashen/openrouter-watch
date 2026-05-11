# M3 规格说明书 — 前端主表增强（字段总表不变）

## 阶段目标

在 **不改变 M1 派生模型字段总表**（`data/derived/models_latest.json` 的行字段集合不新增、不删减、不改名）的前提下，优化 M2 的主表展示与交互：

1. **展示去重**：主表仅展示 `model_id` 作为模型标识列，不再单独展示 `author` / `slug` / `vendor_name` / `name` 作为列。
2. **搜索与筛选**：新增统一搜索框 + 能力复选 + 数值范围筛选，组合逻辑为 AND。
3. **排序**：对关键数值字段提供升/降/无排序，null 始终排在最后。
4. **顶部引导信息**：在页面顶部标题区域补充部署网址入口与仓库 Star 引导入口。

> 注：原 M3 中的 rankings 采集/diff、榜单页与详情页整体延期到 M4，想法池见 `docs/m4/m4_ideas.md`。

---

## 约束与定义

### 字段总表不变

- 本阶段不修改 Python 数据管道产物字段集合。
- 主表所有交互（搜索/筛选/排序）均基于 `models_latest.json` 现有字段完成。

### “模型 id 筛选”的含义

- 主表只展示 `model_id` 列，但筛选/搜索应覆盖用户心智里的“模型相关信息”，因此统一搜索框匹配范围定义为：
  - `model_id`
  - `vendor_name`（厂商）
  - `name`（模型名称）
  - （可选）`author`、`slug` 也参与匹配，但不单独展示为列

> 上述将“厂商、模型名称筛选合并为模型 id 筛选”的诉求落为一个统一入口：**一框搜全域**。

---

## 前端增强范围

### 页面

- 保持 M2 结构：唯一页面 `/`（模型列表主表）。
- 不新增 `/rankings`、不新增 `/models/[slug]` 等页面（延期到 M4）。

### 3.1 主表列展示（去重）

- 必须展示列：
  - `model_id`
  - `context_length`
  - `max_completion_tokens`
  - `input_price_usd_per_1m`
  - `output_price_usd_per_1m`
  - `supports_reasoning`
  - `supports_tools`
  - `supports_vision`
  - `intelligence_index`
  - `coding_index`
  - `agentic_index`
  - `fetched_at`
- 不再单独展示为列（但可用于搜索匹配）：
  - `author`、`slug`、`vendor_name`、`name`

---

### 3.2 搜索与筛选（AND 组合）

#### 统一搜索框（“模型 id 筛选”入口）

- 输入实时过滤（debounce 可选）
- 大小写不敏感
- 匹配字段：`model_id`、`vendor_name`、`name`（可选含 `author`、`slug`）
- 与其它筛选条件为 AND

---

#### 能力筛选（复选框）

- Reasoning / Tools / Vision 三个复选框
- 勾选即要求对应字段为 `true`
- 多个复选框为 AND

#### 数值范围筛选（关键数值字段）

为以下字段提供 min/max（可空）：
- `context_length`
- `max_completion_tokens`
- `input_price_usd_per_1m`
- `output_price_usd_per_1m`
- `intelligence_index`
- `coding_index`
- `agentic_index`

规则：
- 空值表示“不限制”
- 行数据为 null 时：若该字段设置了 min/max，则该行不满足（即被过滤掉）
- 与搜索/能力筛选为 AND

---

### 3.3 排序（关键数值字段）

对以下字段提供排序（升 / 降 / 无）：
- `context_length`
- `max_completion_tokens`
- `input_price_usd_per_1m`
- `output_price_usd_per_1m`
- `intelligence_index`
- `coding_index`
- `agentic_index`
- `fetched_at`（按时间排序）

规则：
- 数值排序按数值比较；`null` 永远排最后
- 时间排序：无法解析的时间字符串按字符串回退比较，且仍保持 `null`/无效时间排最后
- 同值时稳定排序回退到 `model_id`（保证排序结果可预期）

---

### 3.4 UI/UX 现代化升级（科技化、前沿视觉）

为了提升数据展示的专业度与现代感，前端页面需进行深度视觉优化：
- **双主题支持**：支持亮色与深色主题无缝切换，具备持久化（localStorage）与系统偏好跟随。
  - **深色风格**：采用科技感配色（搭配蓝/紫/青色点缀），体现“前沿 AI 模型监控”的定位。
  - **亮色风格**：采用高对比度浅色模式，保持明快、干净且具备现代感的质感。
- **材质与质感**：广泛应用毛玻璃（Backdrop Blur）、微发光（Glow）、细边框与柔和阴影，打破传统数据表的枯燥感。
- **排版与字体**：
  - 数据列采用等宽字体（Monospace）以对齐数值。
  - 关键指标（如 Intelligence Index）可采用特殊高亮或进度条/徽章形式展示。
- **交互细节**：
  - 表头吸顶（Sticky Header）并带有半透明模糊效果。
  - 行悬停（Hover）高亮与过渡动画（Transitions）。
  - 筛选面板采用卡片式布局，输入框与复选框样式定制化。

---

### 3.5 顶部标题区部署入口与仓库 Star 引导

范围：`/` 页顶部标题区（即 `web/src/pages/index.astro` 的 hero/header 区域）。

#### 部署网址入口

- 在顶部标题区域提供“部署网址”展示位，默认使用可点击文本或胶囊样式链接（视觉风格与现有主题一致）。
- 部署链接固定为：`https://andreashen.github.io/openrouter-watch/`。
- 点击后在新标签页打开部署站点；必须包含安全属性：`target="_blank"` + `rel="noopener noreferrer"`。
- 文案建议包含显式提示（如“在线访问”“立即体验”），避免只展示裸链接。
- 若链接较长，允许做前端截断展示，但悬浮时应可通过 `title` 或 tooltip 查看完整 URL。

#### 仓库链接与 Star 引导

- 在顶部标题区域提供 **GitHub 图标** 按钮，点击跳转项目仓库：`https://github.com/andreashen/openrouter-watch`（新标签页打开，带同样安全属性）。
- 图标旁或按钮内部需有中文引导文案：`给项目点个 Star`，不能仅有图标无语义。
- 图标按钮在亮/暗主题下都需保持可见性与可点击反馈（hover/focus 状态）。

#### 可访问性与一致性

- 两个入口都应有清晰的可访问名称（`aria-label` 或可见文本）。
- 键盘可聚焦、可触发；焦点态与现有输入控件风格保持一致。
- 不新增页面路由，仅在现有首页头部增加外链入口。

---

## M3 完成标准

- [ ] 主表仅展示 `model_id`（不再展示 `author/slug/vendor_name/name` 列）
- [ ] 统一搜索框可用（匹配 `model_id/vendor_name/name`，与其他筛选 AND）
- [ ] 能力复选筛选可用（Reasoning/Tools/Vision，AND）
- [ ] 关键数值字段范围筛选可用（min/max，AND）
- [ ] 关键数值字段排序可用（升/降/无，null 排最后）
- [ ] **UI/UX 现代化升级**：实现科技化、美观、前沿的视觉效果（包含暗黑模式/科技感配色、毛玻璃效果、精致的排版与交互动画），并新增亮色/深色主题切换与记忆功能。
- [ ] 顶部标题区新增“部署网址”入口与“仓库 Star 引导”入口（含图标跳转、文案提示、可访问性要求）
- [ ] `cd web && npm run build` 无错误
