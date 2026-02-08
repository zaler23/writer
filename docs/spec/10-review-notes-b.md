# 10 — Review Notes（Verbatim Appendix B）

## 主要问题（按严重性）
- `P0` 规则冲突：`A7.3#1` 规定“只有 finalize 能写世界状态”，但 `C2` 里 `graph/*`、`timeline/*`、`memory/upsert` 都是直接写接口；需要明确“编辑草稿区(staging)写入”与“canonical 世界状态写入”是两套表或两套命令。
- `P0` 事务边界不自洽：`I1` 要求 finalize 单事务 + 可重放，但 `E0/E2` 又建议 core/audit 分库；SQLite 跨库原子性与崩溃恢复语义容易不一致，导致“写了世界状态但没写全审计”。
- `P0` 幂等规范缺关键分支：`E3.1` 有 `idempotency_keys`，但没定义“同 key 不同 request_hash”怎么处理（应 409）、“processing 超时接管”怎么做（租约/过期重入）。
- `P1` rollback 粒度与 mutation_set 作用域冲突：`A6.4/B9` 默认章节级回滚，但 merge/redirect、state/timeline 可能跨章节；若不先做依赖闭包分析，很容易回滚出半残状态。
- `P1` canonical 规则缺防护：有 `redirected_to_node_id`，但缺“重定向环检测”“唯一 canonical 约束”“查询层强制 follow redirect”的数据库级护栏，业务约定容易失守。
- `P1` 动态设定默认值矛盾：`state_assertions.anchor_mode` 默认 `event_based`，而 `B8.2` 强制先 chapter_based；默认值会让早期实现行为偏离预期。
- `P1` schema 演进风险：大量 JSON 字段 + 后置 generated/KV 投影（`E3.4`），如果不在 M1 就定“热字段清单”，后续查询性能和迁移到 Postgres 会很痛。
- `P2` 预算策略只管 token/cost，缺并发/速率预算：多 provider 下还应有 `max_inflight_calls`、`rate_limit_bucket`、`retry_budget`，否则 swarm 高峰会抖动。
- `P2` 测试门禁不够“抗事故”：里程碑有 contract/golden，但缺“并发 finalize 冲突测试”“崩溃恢复测试”“outbox 幂等消费测试”。

## 技术栈优化建议（本地单人、API-first、可迁移）
- 数据层：按 ADR-004，M0–M1 采用 thin repo（raw SQL + 参数绑定）为主；在确有迁移/复杂迁移需求时（M2+）再引入 SQLAlchemy 2.x/Alembic。向量优先 `sqlite-vec`（本地零依赖），迁移 Postgres 时切 `pgvector`。
- 工作流层：先保留轻 runner，但补一个最小状态机引擎（显式状态迁移表 + guard）；不要过早上重型编排器。
- LLM 结构化：按 ADR-006，`LiteLLM + Instructor` 为默认；`PydanticAI` 仅作为未来候选。再加“响应 schema 失败自动降级模板”与“语义缓存（按 prompt+sources hash）”。
- 审计观测：引入 OpenTelemetry（trace run/step/call），并把大字段统一 blob store（hash 路径）+ 生命周期任务，不要双写文本到 DB。
- API 防护：统一中间件处理 `Idempotency-Key`、请求哈希、重复返回；所有写接口默认要求 `expected_version`（不仅 finalize）。
- 检索融合：RRF 保留，新增“可解释打分明细”落库（vector 分、graph 分、裁剪原因），方便后续调参与回归测试。

## 我建议你先改的 5 条硬修订
- 明确两类写入：`/draft/*`（可变草稿） vs `/finalize`（唯一世界状态入口）。
- 定义幂等冲突语义：同 key 同 hash 重放返回；同 key 异 hash 409；processing 超时可接管。
- `state_assertions.anchor_mode` 默认改为 `chapter_based`，event_based 作为增强开关。
- 给 redirect/merge 加约束与巡检：禁止环、禁止多跳未压平、查询强制 canonical。
- 在 M0 增加并发与崩溃测试：双 finalize 竞争、事务中断恢复、mutation op_id 去重。
