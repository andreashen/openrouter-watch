# M3C 规格说明书 — test 分支 SIT 页面与数据更新自动化

> 定位：M3 的发布与运维补充步骤（CI/CD + 数据更新），用于把“改完代码后验证”与“数据拉取执行”从本地手工流程迁移到 GitHub 自动化流程。

## 阶段目标

围绕当前仓库已有的 GitHub Pages 发布链路，补充两项需求：

1. **SIT 页面自动发布**：当代码合并到 `test` 分支后，自动生成一套 SIT 页面用于验证。
2. **数据更新自动化评估**：评估并定义可行方案，把原本在开发机手工执行的 `fetch -> normalize -> derive` 流程迁移到 GitHub 侧执行。

---

## 当前状态（基线）

1. 仓库已存在 `main` 分支的 GitHub Pages 工作流（`.github/workflows/deploy-pages.yml`）。
2. 现有数据更新链路依赖本地命令执行：
   - `python3 scripts/fetch.py`
   - `python3 scripts/normalize.py`
   - `python3 scripts/derive.py`
3. `derive.py` 会逐模型请求 benchmark，整体运行时间较长，且受外部接口限流影响。

---

## 范围与非范围

### 范围（M3C 内）

- 新增或改造 GitHub Actions / Pages 配置以支持 `test` 分支 SIT 发布。
- 明确 SIT 访问链接命名规则（在原链接基础上追加 `_SIT` 后缀）。
- 输出“数据更新自动化”评估结论、推荐方案与约束。

### 非范围（M3C 不做）

- 不改动前端页面功能本身（仅发布与数据流程层面）。
- 不更换 OpenRouter 数据源协议与字段定义。
- 不引入数据库、队列或长期驻留服务。

---

## 功能需求

### R1. 合并到 test 分支后生成 SIT 页面

1. 当变更进入 `test` 分支时，必须自动触发 SIT 发布流程（推荐触发事件：`push` 到 `test`）。
2. SIT 页面链接规则：
   - 以现网链接为基准，新增 `_SIT` 后缀。
   - 例如：现网为 `https://<owner>.github.io/<repo>/`，SIT 为 `https://<owner>.github.io/<repo>_SIT/`。
3. SIT 与现网必须相互隔离，避免互相覆盖（可通过独立仓库、独立发布目标、独立 base path 等方式实现）。
4. 发布后需输出可直接访问的 URL，供开发完成后快速验收。

---

### R2. 数据更新自动化评估（替代开发机手工执行）

#### 评估问题

当前数据更新依赖开发机手工执行，目标是确认是否可迁移至 GitHub 自动化（如 GitHub Actions）。

#### 评估结论

**结论：可行，且 GitHub Actions 是当前最小改造成本的首选方案。**

#### 推荐方案（优先级最高）

1. 新增 `data-refresh.yml` 工作流，由 GitHub Actions 执行：
   - 安装 Python 依赖；
   - 运行 `fetch -> normalize -> derive`；
   - 将 `data/derived/models_latest.json` 与时间戳产物提交回指定分支（如 `test` 或 `main`）。
2. 触发策略建议组合：
   - `workflow_dispatch`（手动触发，便于紧急刷新）；
   - `schedule`（定时刷新，如每日/每 12 小时）；
   - 可选 `push`（仅对数据相关文件或脚本变更触发）。
3. 凭据策略：
   - 使用 `OPENROUTER_API_KEY` 作为 GitHub Actions Secret（可选但推荐，提高限额稳定性）。

#### 备选方案（不作为首选）

1. **外部定时器 + GitHub API 触发**：可行，但系统复杂度和维护成本更高。
2. **仅构建时临时拉取，不落库到仓库**：可减少提交噪声，但不利于审计与历史对比。

#### 约束与风险

1. 外部 API 速率限制与短时失败可能导致数据不完整；需在工作流内记录日志并允许重试。
2. benchmark 抓取耗时较长，需关注 Actions 执行时长与并发策略。
3. 若采用“自动提交产物”，需避免工作流互相触发导致循环（通过路径过滤或 commit message 约定规避）。

---

## 验收标准（M3C）

- [ ] `test` 分支有新提交后，可自动产出并访问 SIT 页面。
- [ ] SIT URL 符合“原链接 + `_SIT` 后缀”规则，且不覆盖现网页面。
- [ ] 已形成“数据更新自动化”明确结论：GitHub Actions 可承担数据拉取与派生任务。
- [ ] 已明确推荐触发方式、密钥配置、失败重试与防循环策略。
- [ ] 团队可不依赖开发机手工执行，即可完成数据刷新流程。

---

## 待澄清事项

1. SIT 页面是否必须使用“独立仓库名后缀 `_SIT`”实现，还是允许用同仓库不同路径模拟该后缀语义？
2. 自动化数据刷新后的提交目标分支是 `test`、`main`，还是双分支分别维护？
3. 产物提交策略是“每次都提交时间戳文件 + latest”，还是仅保留 `models_latest.json`？
