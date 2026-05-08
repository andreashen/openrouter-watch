# M2 规格说明书 — 模型信息表前端

## 阶段目标

基于 M1 产出的 `data/derived/models_latest.json`，构建一个可部署到 GitHub Pages 的静态网站，展示 M1 输出的完整模型信息表，支持按厂商筛选。

M2 严格限定为模型表和厂商筛选；搜索、排序、多条件筛选、模型详情页、榜单页均留到 M3。

---

## 技术选型

| 项目 | 选择 | 说明 |
|------|------|------|
| 框架 | Astro | 静态优先，零 JS 默认，适合 GitHub Pages |
| 样式 | Tailwind CSS | 与 Astro 官方集成，原子化类名 |
| 数据加载 | 构建时 import JSON | 在 `.astro` 文件中直接 import `data/derived/models_latest.json`，无运行时请求 |
| 部署 | GitHub Pages | 本地开发先完成；部署阶段使用 GitHub 官方 Pages Actions |

---

## 数据来源

构建时从 `data/derived/models_latest.json` 读取（路径相对于仓库根）。Astro 页面在 `web/` 目录内，读取路径为 `../../../data/derived/models_latest.json`。

如果 `models_latest.json` 缺失、为空或 JSON 格式错误，构建必须失败。

---

## 页面结构

### 唯一页面：`/`（模型列表）

```
┌─────────────────────────────────────────────┐
│  页头：项目名 + 数据更新时间                   │
├─────────────────────────────────────────────┤
│  筛选栏：厂商下拉（全部 / 各 vendor_name）      │
├─────────────────────────────────────────────┤
│  模型表格（全部 M1 字段，横向滚动）              │
├─────────────────────────────────────────────┤
│  页脚：数据来源说明                            │
└─────────────────────────────────────────────┘
```

---

## 表格字段（展示顺序）

| # | 字段名 | 展示名 | 备注 |
|---|--------|--------|------|
| 1 | `model_id` | Model ID | 等宽字体 |
| 2 | `author` | Author | |
| 3 | `slug` | Slug | |
| 4 | `vendor_name` | 厂商 | 筛选字段 |
| 5 | `name` | 模型名称 | |
| 6 | `context_length` | 上下文 | 去尾法保留 1 位缩写，如 `128000` → `128.0K` |
| 7 | `max_completion_tokens` | 最大输出 | 去尾法保留 1 位缩写 |
| 8 | `input_price_usd_per_1m` | 输入价 ($/1M) | 最多保留 4 位小数；`0` 显示 `0`；null 显示 `—` |
| 9 | `output_price_usd_per_1m` | 输出价 ($/1M) | 最多保留 4 位小数；`0` 显示 `0`；null 显示 `—` |
| 10 | `supports_reasoning` | Reasoning | ✓ / — |
| 11 | `supports_tools` | Tools | ✓ / — |
| 12 | `supports_vision` | Vision | ✓ / — |
| 13 | `intelligence_index` | Intelligence | 保留 1 位小数；null 显示 `—` |
| 14 | `coding_index` | Coding | 保留 1 位小数；null 显示 `—` |
| 15 | `agentic_index` | Agentic | 保留 1 位小数；null 显示 `—` |
| 16 | `fetched_at` | 更新时间 | 每行展示为 `YYYY-MM-DD HH:mm UTC` |

---

## 交互功能

### 厂商筛选（下拉）
- 选项从数据中动态生成（去重排序后的 `vendor_name` 列表）
- 第一项为"全部"
- 切换时过滤表格行，无需重新请求（原生前端 JS）

---

## Astro 项目结构

```
web/
  astro.config.mjs      # base 路径配置
  package.json
  tailwind.config.mjs
  src/
    pages/
      index.astro       # 唯一页面
    components/
      ModelTable.astro  # 表格组件（含筛选逻辑）
    layouts/
      Base.astro        # HTML 骨架 + head
```

---

## 构建流程

1. `web/src/pages/index.astro` 构建时 import `data/derived/models_latest.json`
2. `cd web && npm run build` 生成 `web/dist/`
3. 后续部署阶段由 GitHub 官方 Pages Actions 发布 `web/dist/`

---

## GitHub Pages 配置

```js
// astro.config.mjs
export default defineConfig({
  site: 'https://<username>.github.io',
  base: '/<repo-name>/',
  integrations: [tailwind()],
})
```

`site` 是 GitHub Pages 域名；`base` 是普通项目仓库在域名下的路径前缀。两者在 GitHub Actions 部署时通过环境变量注入，本地开发默认 `base: "/"`。

---

## GitHub Actions（后续部署阶段）

### `.github/workflows/deploy-pages.yml`

触发条件：
- `data/derived/` 目录有新 commit 推送到 `main`
- 手动触发（`workflow_dispatch`）

步骤：
1. checkout
2. `cd web && npm ci && npm run build`
3. 使用 GitHub 官方 Pages Actions 上传并部署 `web/dist/`

> 当前仓库已提交 Pages workflow；仓库 Settings → Pages 需由维护者设置为 GitHub Actions。

---

## M2 完成标准

- [x] `cd web && npm run build` 成功生成 `web/dist/`
- [x] 本地 `npm run dev` 可正常访问，表格有数据
- [x] 基于 `vendor_name` 的厂商下拉筛选可用
- [x] `null` 值正确显示为 `—`，bool 值显示为 `✓` / `—`
- [x] `models_latest.json` 缺失、为空或 JSON 错误时构建失败
- [x] 后续部署阶段 GitHub Pages 地址可真实访问
