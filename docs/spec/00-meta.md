# Local Novel Swarm System — Modular Spec (v1.4)
- 基线：v1.3 Consolidated（含 PRD + 架构 + 数据模型 + 运行策略 + API/Schema + 里程碑）
- 本次：v1.4 Hard Patch（修复：draft/canonical 分层、事务/审计自洽、幂等租约、章节回滚闭包、redirect DB 级护栏、anchor_mode 默认值、热字段清单、并发/崩溃/出站测试门禁）
- 日期：2026-02-07
- 范围约定：
  - 本地单人、API-first
  - 默认 SQLite（可迁移 Postgres）
  - LLM 有效注意力按 100k–150k 约束设计


本目录拆分了 v1.3 全量规范，并融合 v1.4 修订。配合 `docs/cards/*` 作为 vibe coding 的最小上下文切片。


## 版本变更摘要（v1.3 → v1.4 Hard Patch）

### P0 修复
1. **写入分层**：引入 **草稿区（draft / staging）** 与 **世界真相（canonical）** 两套写入语义；世界真相只允许 `finalize.apply()` 写入（保持 v1.3 A7.3#1 的硬规则），所有“编辑式写接口”迁移到 `/draft/*`（或写 proposal）。
2. **事务边界自洽**：`finalize.apply()` 的强原子性只保证 `core.db`；审计/大字段（audit.db + blob store）改为**派生可重建**，通过 `outbox_events` 重放修复“真相已写但审计未写全”的崩溃不一致。
3. **幂等完整语义**：补齐 `Idempotency-Key` 的三分支：
   - 同 key 同 request_hash：重放返回缓存（或 202 processing）
   - 同 key 异 request_hash：409 `E101_IDEMPOTENCY_CONFLICT`
   - processing 超时：租约（lease）过期可接管（CAS 更新 lease_owner/lease_until）
4. **错误响应统一**：新增 `ErrorResponse` Schema 与 `ERROR_CODES.md`，中间件统一格式化错误。

### P1 修复
5. **章节回滚闭包**：章节级 rollback 只回“章内闭包”，并引入 `created_in_chapter_id` / `origin_chapter_id` 等归属字段以便依赖分析；禁止章节 finalize 内执行 `merge/redirect apply`（仅 proposal），跨章操作单独 mutation_set(kind='global')。
6. **canonical 保护**：redirect 禁止自指、触发器防环、查询层强制 follow redirect、定期压平多跳。
7. **anchor_mode 默认值一致**：`state_assertions.anchor_mode` 默认改为 `chapter_based`；`event_based` 作为增强开关。

### P2 增强
8. **热字段治理前置**：新增 `HOT_FIELDS.md`，M1 起明确哪些 JSON key 必须投影（generated column / KV / 关联表）。
9. **预算扩展**：在 token/cost 外新增并发/速率/重试预算：`max_inflight_calls`、`rate_limit_bucket`、`retry_budget`。
10. **测试门禁抗事故**：M0b 起强制：并发 finalize 冲突测试、崩溃恢复测试、mutation op_id 去重测试；M1+ 加 outbox 幂等消费测试。


## 文档阅读顺序
1. `docs/INVARIANTS.md`（先读：所有硬规则统一编号）
2. `docs/CONVENTIONS.md`（ID/时间/JSON/Blob/枚举约定）
3. `docs/STATE_MACHINES.md`（runner/step/chapter/幂等租约状态机）
4. `docs/ERROR_CODES.md`（统一错误码枚举）
5. `docs/spec/01-prd.md` → `02-architecture.md` → `03-workflows.md`
6. `docs/spec/04-runtime.md`（算法与策略）
7. `docs/spec/05-api.md`（端点与一致性语义）
8. `docs/spec/06-schemas.md`（JSON Schema）
9. `docs/spec/07-data-model.md`（DDL + 索引 + 分库/冷热/草稿表）
10. `docs/spec/08-milestones.md`（M0a→M4 + 门禁测试）
11. `docs/HOT_FIELDS.md`（JSON 热字段投影清单）
12. `docs/spec/11-docs-frontend.md`（文档前端与构建计划）
13. `docs/cards/*`（模块卡片，按需阅读）
14. `docs/adr/*`（架构决策记录，按需阅读）
