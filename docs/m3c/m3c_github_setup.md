# M3C GitHub 平台配置清单（SIT + 数据自动刷新）

> 目标：完成 `repo/sit` 的 SIT 发布链路与数据自动刷新链路所需的 GitHub 平台配置。

## 1. 准备分支

1. 确认仓库存在 `test` 分支（用于 SIT 页面来源）。
2. 约定：
   - `main`：生产页面来源，也是唯一允许自动/手动数据刷新的分支
   - `test`：SIT 页面来源，只承载待验证的功能代码

发布与重锚操作细则见 [main_test_release_flow.md](../main_test_release_flow.md)。

---

## 2. 启用 GitHub Pages（Actions 方式）

路径：`Settings -> Pages`

1. `Source` 选择 **GitHub Actions**。
2. 不使用 “Deploy from a branch” 直连分支发布模式。
3. 首次成功部署后，确认页面 URL 可访问：
   - 生产：`https://<owner>.github.io/<repo>/`
   - SIT：`https://<owner>.github.io/<repo>/sit/`

### 2.1 环境保护规则注意事项（关键）

若你在仓库里配置了 environment protection rules（部署分支限制/审批人），需要区分两个环境：

1. `github-pages`：生产部署环境（`main` 分支触发）。
2. `github-pages-sit`：SIT 部署环境（`test` 分支触发）。

当前 workflow 已按分支自动路由到上述两个环境，避免 `test` 被 `github-pages` 的分支保护直接拒绝。

如果你之前只配置过 `github-pages` 且限制只能 `main` 部署，这是正常的；请额外确认 `github-pages-sit` 没有把 `test` 拦截掉（或按你们规范单独配置审批策略）。
---

## 3. 配置 Actions 权限

路径：`Settings -> Actions -> General`

1. `Actions permissions`：允许仓库运行 Actions。
2. `Workflow permissions`：选择 **Read and write permissions**（`data-refresh.yml` 需要把 `data/derived/*` 回写到分支）。
3. 若有额外组织级策略，确保不阻止：
   - `actions/checkout`
   - `actions/setup-python`
   - `actions/setup-node`
   - `actions/deploy-pages`

---

## 4. 配置仓库 Secrets

路径：`Settings -> Secrets and variables -> Actions`

1. 新增 Secret：`OPENROUTER_API_KEY`（推荐）。
2. 不配置也可运行，但高峰期更易受限流影响。

---

## 5. 检查分支保护策略

路径：`Settings -> Branches`

需要重点检查 `main`：

1. 若开启了 “Require pull request before merging” 且禁止直接 push：
   - 需要允许 GitHub Actions bot 对目标分支有写入能力，或
   - 改为“工作流只产物不回写”模式（不在当前方案内）。
2. 若开启 status checks，避免把“必须人工审阅 PR”强加到 bot 自动提交路径上。

`test` 不再承接数据刷新写入，因此不需要为该 workflow 保留 bot 直推权限。

---

## 6. 验证触发链路

### A. SIT 发布链路

1. 向 `test` 分支推送一个小改动（如 docs 注释）。
2. 在 `Actions` 中确认 `Deploy site to GitHub Pages` 运行成功。
3. 若失败信息包含 `not allowed to deploy`，先检查 `github-pages-sit` 环境是否允许 `test`。
4. 访问 `https://<owner>.github.io/<repo>/sit/` 验证页面更新。

### B. 数据刷新链路

1. 在 `Actions` 中手动执行 `Refresh derived model data`（`workflow_dispatch`）。
2. 确认工作流不再暴露 `target_branch` 选择，默认只刷新 `main`。
3. 确认日志依次执行：
   - `python scripts/fetch.py`
   - `python scripts/normalize.py`
   - `python scripts/derive.py`
4. 若 `data/derived` 有变化，确认自动提交只落到 `main`。

---

## 7. 运维建议

1. 保持 `data-refresh.yml` 的 `timeout-minutes: 30`（防止异常长跑）。
2. 定时任务使用 UTC；若需北京时间固定时段，按 UTC 偏移换算 cron。
3. 观察前 1 周运行情况，再决定是否需要调整每日刷新时点。
