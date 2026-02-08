# 约定（Conventions）

## ID 生成
- 约定：所有主键 ID 使用 ULID（26 字符，时间有序，URL 安全）
- 可选前缀：proj_, ch_, run_, step_, node_, ms_（提升调试体验）
- 规则：前缀仅用于可读性；**建议每张表使用固定前缀**（例如 chapters 全部为 `ch_`），则按字符串排序仍与 ULID 时间序一致。若同一表可能出现多个前缀，必须改为“前缀列 + ulid 列”或统一用 `created_at` 排序。

## 时间字段
- 推荐：统一 ISO8601 UTC：`YYYY-MM-DDTHH:MM:SS.ffffffZ`
- SQLite 中索引与范围查询：对 `created_at`/`updated_at` 高频字段可增加索引
- 允许：Unix ms INTEGER（若采用必须全局一致）

## JSON 字段治理
- 所有 JSON 配置必须 Schema 校验（INV-005）
- 任何未来会用于 WHERE/ORDER/JOIN 的 JSON key 必须投影为列或 KV/关联表（见 HOT_FIELDS.md）
- 禁止在业务查询中临时 `json_extract` 高基数字段而不建索引

## Blob Store
- hash 算法：SHA-256
- 存储路径：`blobs/ab/cd/<hash>`（前 2/2 分层）
- 写入幂等：若路径存在且内容不同（理论不应发生）必须报错

## 命名
- 表：snake_case
- 枚举：lower_snake（DB）/ PascalCase（domain）
- API：resource-oriented；写入分区：/draft/* 与 /finalize/* 明确

## Project Scope
- 所有查询必须显式 project_id 过滤（服务层注入），避免跨项目串数据（INV-016）

## 枚举值约定

### truth_mode（state_assertions）
| 值 | 含义 |
|---|---|
| asserted | 确定事实（默认） |
| rumored | 传闻/未证实 |
| mislead | 误导性信息（角色视角错误） |
| retconned | 追溯修正（后续章节覆盖） |

### anchor_mode（state_assertions）
| 值 | 含义 |
|---|---|
| chapter_based | 按章节锚定有效期（默认，确定性强） |
| event_based | 按事件锚定有效期（增强模式） |

### chapter status
| 值 | 含义 |
|---|---|
| planned | 已规划，未开始写作 |
| drafting | 草稿撰写中 |
| reviewing | 审查中 |
| revising | 修订中 |
| validating | 校验中 |
| finalizing | 定稿中 |
| finalized | 已定稿 |
| needs_review | 需要人工审查（回滚/冲突后） |

### run status
| 值 | 含义 |
|---|---|
| created | 已创建，未开始 |
| running | 运行中 |
| paused | 已暂停 |
| completed | 已完成 |
| failed | 失败 |
| cancelled | 已取消 |

### step status
| 值 | 含义 |
|---|---|
| pending | 等待执行 |
| running | 执行中 |
| completed | 已完成 |
| failed | 失败 |
| skipped | 已跳过 |
| pending_approval | 等待审批 |
| approved | 已批准 |
| rejected | 已拒绝 |

### draft/proposal status
| 值 | 含义 |
|---|---|
| draft | 草稿 |
| approved | 已批准 |
| rejected | 已拒绝 |
| applied | 已应用到 canonical |

### idempotency_keys status
| 值 | 含义 |
|---|---|
| processing | 处理中（租约有效） |
| succeeded | 成功完成 |
| failed | 失败 |

## 版本号
- 当前规范版本：v1.4
- JSON Schema 版本：1.2（兼容 v1.4 规范）
- 所有 schema_version 字段使用字符串 "1.2"
