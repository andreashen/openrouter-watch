# main / test 发布与清理操作手册

## 分支职责

| 分支 | 职责 | 自动数据刷新 |
| --- | --- | --- |
| `main` | 生产页面来源；GitHub Pages root；合并后的正式代码与正式数据 | 允许；每日自动刷新；手动刷新也只写入 `main` |
| `test` | SIT 页面来源；功能与修复的验证分支 | 不允许；不跑 schedule；不接受手动刷新写入 |

## 日常开发与发布流

1. 功能分支或修复分支先合入 `test`。
2. 在 `/sit/` 页面验证 `test` 的代码改动。
3. `test` 准备提升到 `main` 前，只在这一次做必要的同步与消歧。
4. 完成同步后，走 `test` → `main` 的提升。
5. 提升完成后，`main` 继续承担正式环境的数据刷新。
6. 不做常规性的 `main` → `test` 回灌。

## main-only 数据刷新约束

1. `data-refresh.yml` 的 `schedule` 只刷新 `main`。
2. `workflow_dispatch` 不再提供目标分支选择，手动刷新默认也只写入 `main`。
3. 提交到仓库的派生产物收敛为一个稳定文件：`data/derived/models_latest.json`。
4. 派生脚本在写入新结果后，会清理旧的时间戳 `models_*.json` / `models_*.csv` 遗留文件。

## `test` 远端历史重锚操作清单

这个动作应在一次 `test` → `main` 提升完成之后执行；本轮实现不会替你静默改写远端历史。

### 仓库规则注意事项

如果仓库规则禁止人工对 `test` 直接 force-push，应优先使用 `data-refresh.yml` 的手动 `reanchor_test` 操作，由现有 GitHub App token 执行备份与带租约重锚。只有在仓库规则明确允许的情况下，才使用下面的本地 git 命令路径。

### 执行前条件

1. 提升 PR 已合并到 `main`。
2. 需要保留的 SIT 代码已经进入 `main`。
3. 操作者已经 `git fetch origin`，并确认本地没有未提交改动。

### 受控执行步骤

#### 推荐：GitHub Actions 路径

1. 记录当前远端 `test` SHA：
   - `git rev-parse origin/test`
2. 准备远端备份分支名，例如：
   - `test-backup-<YYYYMMDD-HHMMSS>`
3. 手动触发 `Refresh derived model data` workflow：
   - `operation=reanchor_test`
   - `expected_test_sha=<OLD_TEST_SHA>`
   - `backup_branch=test-backup-<YYYYMMDD-HHMMSS>`
4. workflow 会自动执行三件事：
   - 校验 `origin/test` 仍然等于 `expected_test_sha`
   - 先创建远端备份分支
   - 再用 `--force-with-lease` 把 `test` 重锚到当前 `origin/main`

#### 备选：本地 git 路径（仅当仓库规则允许时）

1. 记录当前远端 `test` 备份点：
   - `git rev-parse origin/test`
2. 创建一个远端备份分支，固定住旧的 `test` 头部：
   - `git push origin origin/test:refs/heads/test-backup-<YYYYMMDD-HHMMSS>`
3. 本地用 `main` 作为新的 `test` 基点：
   - `git checkout -B test origin/main`
4. 用带租约的 force push 重写远端 `test`：
   - `git push --force-with-lease=refs/heads/test:<OLD_TEST_SHA> origin test`

### 回滚方式

如果重锚后发现需要恢复旧历史：

1. 确认备份分支仍在远端：
   - `git ls-remote --heads origin test-backup-<YYYYMMDD-HHMMSS>`
2. 用备份分支回推 `test`：
   - `git push --force-with-lease origin refs/heads/test-backup-<YYYYMMDD-HHMMSS>:refs/heads/test`

## 合并后在线验证

以下项需要在 GitHub 上验证，无法在本地离线完全证明：

1. `Refresh derived model data` 每日调度是否按预期只在 `main` 生成提交。
2. 手动 `workflow_dispatch` 是否不再出现 `target_branch=test` 的入口。
3. `main` 上的数据刷新提交是否会触发 Pages，并保持 root 来自 `main`、`/sit/` 继续来自 `test`。
4. `test` 上的代码提交是否仍会重建组合式 Pages artifact，并让 `/sit/` 页面更新。
