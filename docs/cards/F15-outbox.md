# F15 — Outbox / Projection Sync

## 职责
- core 真相源变更投影到可重建索引（向量库/FTS/审计）
- 处理失败重试与幂等消费
- 保证审计最终一致性（见 ADR-008）

## 表
- outbox_events

## 事件类型枚举
| event_type | 含义 | 消费者 |
|---|---|---|
| FINALIZE_APPLIED | finalize.apply 完成 | 审计、向量索引 |
| CONTEXTPACK_BUILT | ContextPack 组装完成 | 审计 |
| LLM_CALL_LOGGED | LLM 调用记录 | 审计 |
| VECTOR_UPSERT | 向量需要更新 | 向量索引 |
| INDEX_REBUILD | 索引需要重建 | FTS/向量索引 |
| CHUNK_CREATED | memory_chunk 创建 | 向量索引 |
| NODE_UPDATED | graph_node 更新 | 向量索引 |

## API（内部）
- 无公开 API，通过后台消费器处理
- 消费器实现见 services/outbox_consumer

## 不变量
- INV-015：消费幂等；可重复消费而不重复写
- 消费失败必须记录 last_error 并增加 attempts

## 测试
- 幂等消费测试（同事件多次消费）
- 失败重试次数与 backoff
- 崩溃恢复后继续消费
