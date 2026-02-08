# ADR-007 Draft vs Canonical split (v1.4)

## 状态
已采纳（v1.4）

## 背景
v1.3 硬规则"只有 finalize 能写世界状态"与 API 端点存在冲突。需要明确"编辑草稿区写入"与"canonical 世界状态写入"的边界。

## 决策
引入 draft/staging 表与 `/draft/*` 写入区；canonical 表只允许 finalize.apply 写入。

## 备选方案
1. **单表 + status 字段**：简单，但查询复杂
2. **版本化表**：所有变更追加版本，但存储开销大
3. **分表（draft_* + canonical）**：清晰分离，查询简单

## 拒绝原因
- 单表 + status：查询需要额外过滤，容易遗漏
- 版本化表：存储开销大，查询复杂
- 选择分表是因为：结构性约束强、查询简单、便于理解

## 后果
- 优：强化不变量（结构性约束）、查询简单、便于理解
- 负：增加一些表与迁移成本

## 实现
- draft 表：draft_graph_nodes, draft_graph_edges, draft_state_assertions, draft_story_events, draft_narrations, draft_memory_chunks
- API 分区：/draft/* 写草稿，/finalize/* 写 canonical
- 详见 INVARIANTS.md INV-001
