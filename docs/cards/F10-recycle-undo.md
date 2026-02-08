# F10 — Recycle & Undo

## 职责
- 软删除统一入口
- mutation_set 回滚（章节闭包默认）
- 冲突报告与 needs_review 标记

## 表
- recycle_bin
- mutation_sets / mutations(op_id)
- rollback_conflicts

## API
- GET /mutationsets（获取 mutation_set 列表）
- GET /mutationsets/{id}（获取 mutation_set 详情，含 mutations 列表）
- POST /mutationsets/{id}/rollback（回滚 mutation_set，需 Idempotency-Key）
  - 参数：`force=false`（默认），若有依赖冲突返回 409 + conflict_report
  - 参数：`force=true`，强制回滚并标记相关章节 needs_review
- GET /mutationsets/{id}/conflict-report（预览回滚冲突报告）
- POST /draft/recycle/delete（软删除 draft 记录）
- POST /draft/recycle/restore（恢复 draft 记录）

> 说明：对 story-canonical 的删除/恢复，默认由 `finalize.apply()` 在 core.db 单事务内写入 mutations + recycle_bin 快照，不开放直接写 canonical 的公共 /recycle 端点。

## 不变量
- INV-009：章节闭包 rollback 默认
- INV-010：软删除不级联

## 测试
- 回滚可逆
- dependents 冲突报告
