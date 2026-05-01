# M2 任务清单

> 关联规格：`docs/m2/m2_spec.md`
> 前置条件：M1 已完成，`data/derived/models_latest.json` 存在

## T1 — Astro 项目初始化

- [ ] `cd web && npm create astro@latest` 初始化（选 minimal 模板）  
- [ ] 安装 Tailwind CSS 集成：`npx astro add tailwind`  
- [ ] 配置 `astro.config.mjs`：设置 `site` 和 `base`（base 支持从环境变量读取，本地默认 `/`）  
- [ ] 确认 `npm run dev` 和 `npm run build` 可正常运行  

## T2 — 构建时数据读取

- [ ] 在 `web/src/pages/index.astro` 中构建时 import `../../../data/derived/models_latest.json`  
- [ ] 校验 `models_latest.json` 必须存在、非空且为非空数组；否则构建失败  

## T3 — 页面骨架

- [ ] 创建 `web/src/layouts/Base.astro`：HTML 骨架，引入 Tailwind，包含 `<slot />`  
- [ ] 创建 `web/src/pages/index.astro`：引入 Base layout，import `models_latest.json`，校验数据后传给 ModelTable 组件  

## T4 — ModelTable 组件

文件：`web/src/components/ModelTable.astro`

- [ ] 接收 `models: Model[]` 作为 props，渲染厂商筛选下拉（`<select id="vendor-filter">`），选项从 `vendor_name` 动态生成  
- [ ] 渲染 M1 输出完整表格（16 列，按 spec 顺序）  
- [ ] 数值格式化：`context_length` / `max_completion_tokens` 用去尾法保留 1 位 K/M 缩写  
- [ ] null 值显示 `—`，bool 值显示 `✓` / `—`，价格 0 显示 `0`  
- [ ] 添加内联 `<script>`：监听筛选下拉变化，隐藏/显示对应行  

## T5 — 样式

- [ ] 表格横向可滚动（`overflow-x-auto`）  
- [ ] 表头固定样式（`sticky top-0`）  
- [ ] 行 hover 高亮  
- [ ] 页头展示项目名 + `fetched_at`（取数据中最新一条）  
- [ ] 页脚展示数据来源：OpenRouter API  

## T6 — GitHub Actions 部署（后续阶段）

文件：`.github/workflows/deploy.yml`

- [ ] 触发条件：push to main（`data/derived/**`）+ `workflow_dispatch`  
- [ ] 步骤：checkout → npm ci → npm run build  
- [ ] 使用 GitHub 官方 Pages Actions 发布 `web/dist/`  
- [ ] 在仓库 Settings → Pages 中设置 source 为 GitHub Actions  

> 当前先做本地开发，不提交 Pages workflow；Pages Actions 由后续部署阶段配置。

## T7 — 本地验证

- [ ] `cd web && npm run dev`：本地可访问，表格有数据  
- [ ] 厂商筛选切换后行数正确变化  
- [ ] `npm run build`：无报错，`web/dist/` 生成完整  
- [ ] 检查 `web/dist/` 中 `index.html` 引用路径正确（本地默认 base 为 `/`）  
