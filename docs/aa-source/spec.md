# Artificial Analysis 直连规格说明

## 背景 / 问题

OpenRouter 转载的 Artificial Analysis 分数会滞后，并且可能只更新其中一项。主榜上同一模型的 Intelligence / Coding / Agentic 因此对不上，不同模型也不一定来自同一套指数。

## 目标 & 非目标

- 目标：内部能抓取 AA 语言型号列表、写成不可变快照，并用冻结映射把 OpenRouter 模型连到 AA UUID。一对多分组成员必须带可复核身份依据。
- 目标：公开展示和 OpenRouter benchmark 采集保持原状，直到书面授权或 Commercial 合同以及其余切流闸门全部通过。
- 非目标：本轮不切换公开主榜，不把 AA 分数写入 `models_latest.json`，不停采 OpenRouter benchmark，不展示历史快照，不展开全部子评测。

## 用户与场景

维护者用内部快照和 mapping report 核对映射。访客仍看 OpenRouter 转载分。

## 需求详述

1. `rules` 只表达一对一。`one_to_many` 是一对多的唯一来源。同一个 OpenRouter id 不能同时出现在两边。
2. 每个 group 声明 `match`：`manual_override`、`openrouter_api_id` 或 `canonical_identity`。`exact_slug` 不能充当 group 的身份依据。
3. 证据要么逐成员覆盖，要么一条 `covers: all_members` 的共同证据。每条证据有非空 `ref` 和 `note`。`ref` 是 http(s) URL、`snapshot:` 定位，或 `pro-field:openrouter_api_id`。
4. `openrouter_api_id` 只能证明一个成员，而且当前快照必须真的带上这个字段并等于该成员。Free 响应没有该字段时，这种依据失败。
5. 一次抓取要页码、总页数、`has_more` 和 AA UUID 都稳定。任一失败不写快照，连续成功计数清零。
6. 一行三项只来自同一个快照。当前快照里的空值保持为空。
7. 列名版本、旧版本徽章、空值「不可比」、排序排除旧分，实现在未接入主榜的显示模块里。

## 技术方案概述

Python 模块 `aa_mapping`、`aa_fetch`、`aa_snapshot`、`aa_join`、`aa_gates`、`aa_version`。提交的开关在 `data/aa_join/publication.json`。快照目录不入库。

## 依赖与约束

官方 Data API，请求头 `x-api-key`。内部验证用 Free 端点。公开转载不由 Free 档位页授予。

## 风险与替代方案

错映射会让榜单再次不可比，所以没有身份依据的 group 整份拒绝。许可未到就切公开页会违反转载限制，所以开关失败时仍返回 OpenRouter 行，并继续采集。
