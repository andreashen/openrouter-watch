# 文档索引

本目录存放 **现行** 架构、数据契约与运维手册。历史 milestone 规格已移除，不再作为真相源。

| 文档 | 用途 |
| --- | --- |
| [architecture.md](./architecture.md) | 系统结构、数据流、Actions、前端行为 |
| [data-schema.md](./data-schema.md) | `models_latest` / 加权价 sidecar 字段权威表 |
| [ops/main_test_release_flow.md](./ops/main_test_release_flow.md) | `main` / `test` 职责、发布流、`test` 重锚 |
| [ops/github_setup.md](./ops/github_setup.md) | Pages、Secrets、分支保护与触发验证 |

建议阅读顺序：`architecture` → `data-schema` → 按需打开 `ops/*`。
