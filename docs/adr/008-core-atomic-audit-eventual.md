# ADR-008 Core atomicity, audit eventual (v1.4)

## 状态
已采纳（v1.4）

## 背景
core.db 与 audit.db 分库下无法可靠保证跨库崩溃原子性。需要明确事务边界与一致性保证。

## 决策
finalize.apply 的强原子性只保证 core；审计/索引通过 outbox 派生可重建（最终一致）。

## 备选方案
1. **单库**：所有表在同一数据库，强一致
2. **分布式事务（2PC）**：跨库原子性，但复杂度高
3. **Saga 模式**：补偿事务，但实现复杂
4. **Outbox 模式**：最终一致，可重建

## 拒绝原因
- 单库：audit 数据量大，影响 core 性能
- 分布式事务：SQLite 不支持，复杂度高
- Saga 模式：实现复杂，不适合本地单人场景
- 选择 Outbox 是因为：简单可靠、可重建、符合"审计为派生数据"的语义

## 后果
- 优：避免"真相写了但审计没写全"的不一致不可恢复问题
- 负：需要 outbox 消费器与幂等处理

## 实现
- finalize.apply 在 core.db 单事务内写入：mutation_set + mutations + canonical 变更 + outbox_events
- 审计写入通过 outbox 消费器异步处理
- 消费器必须幂等（INV-015）
- 详见 F15-outbox.md
