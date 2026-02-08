# 02 — 架构与工程原则

> 先读 `docs/INVARIANTS.md`（硬规则）与 `docs/CONVENTIONS.md`（约定）。

## 分层（目标形态）
- domain：纯领域模型（Pydantic v2 / dataclasses），不依赖 DB/Web
- services：用例层（组合 repo/store，执行业务）
- infrastructure：SQLite / 向量扩展 / 文件存储 / LLM 调用实现
- app/api：FastAPI routers + 中间件（错误格式化、幂等、request_id）
- workflows：轻 runner（显式状态机 + step registry）；未来可替换 LangGraph，但不改变 run/step/audit 契约

## v1.4 关键架构修订：Draft vs Canonical
- Canonical world state 表：只允许 finalize.apply 写入（见 INV-001/003）
- Draft / staging 表：允许编辑式写入（draft API），但不会影响 canonical
- Proposal 表：merge_proposals 等只写提案不执行
- Finalize：从 draft 生成 writeback_plan（事务外），在 core.db 单事务 apply 写入 canonical，并写 outbox 用于审计/索引同步

## Repo 结构（建议）
见项目根目录 `README` 约定；docs 只规定 `docs/`。

## 关键工程护栏（引用不变量）
- 写入控制：INV-001/003/007/008
- canonical 化：INV-004
- JSON/Schema 校验：INV-005
- 幂等：INV-002/006
- 审计与冷热：INV-013/014

## ADR（架构决策记录）
在 `docs/adr/`，每条 ADR 必须说明：
- 背景
- 决策
- 备选方案与拒绝原因
- 后果（正/负）
