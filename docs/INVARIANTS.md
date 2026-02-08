# 系统不变量（Hard Invariants）

所有模块实现与 code review 必须对照本文件。违反任何一条即为 P0 bug。

## 写入控制
- **INV-001**：除 `finalize.apply()` 外，任何 step/service 禁止修改 **story-canonical（世界真相）** 表  
  - story-canonical（受保护）：`chapter_text_versions(stage='final')`、`graph_nodes/graph_node_versions/graph_edges/node_aliases`（含 redirect）、`state_assertions`、`story_events/event_order_constraints/narrations`、`memory_chunks`（以及 embeddings/vec_embeddings 如被纳入 core）
  - 允许非 finalize 写入（admin/config，不属于 story-canonical）：`projects/project_settings`、`prompt_templates`、`swarm_profiles/traversal_profiles/style_guides`、`outlines`、`chapters`（仅计划字段：title/plan_json/profile refs；**status/lock_version 由系统管理**）、`chapter_segments`、`chapter_reviews`、`onboarding_checklist_items` 等配置/运营表
  - 允许写（运行/派生/草稿）：`runs/run_steps`、`llm_calls`、`retrieval_sessions/context_pack_items`、`jobs/*`、`proposals/*`、`draft_*`（v1.4）
- **INV-002**：所有写 API 必须支持 `Idempotency-Key`
- **INV-003**：`finalize.apply()` 必须在 **core.db 单事务**中执行：写 mutation_set + mutations(op_id) + canonical 变更 + outbox  
  - v1.4：审计/大字段不纳入强原子性（派生可重建），但必须通过 outbox 保证最终一致
- **INV-003A**：finalize preview 不得写 canonical（只生成计划与哈希）

## 幂等与重试
- **INV-004**：对**包含** `is_deleted` 列的表，读取默认过滤 `is_deleted=0`；graph 查询必须 follow redirect（不得把 redirect 节点当作实体返回）。未实现软删列的表默认 append-only（如需删除，必须先补齐软删列与迁移）
- **INV-005**：所有 profile/style/prompt/schema 类 JSON 入库前必须 Schema 校验；运行时再次校验
- **INV-006**：mutations 每条必须有 `op_id`，且在同一 `mutation_set_id` 内唯一；写回级去重键 = (`mutation_set_id`, `op_id`)
- **INV-006A**：同 `Idempotency-Key` 不同 request_hash 必须返回 409（见 ERROR_CODES）
- **INV-006B**：processing 超时必须通过租约接管（lease）

## 并发控制
- **INV-007**：SQLite 写操作必须通过全局 WriteSerializer 串行化（WAL + 单写多读）
- **INV-008**：finalize 必须携带乐观锁 `expected_lock_version`；不匹配返回 `E102_VERSION_CONFLICT`

## 回滚边界
- **INV-009**：默认只支持章节闭包 rollback；跨章节 rollback 必须人工确认 + 输出 conflict_report
- **INV-009A**：章节 finalize 默认禁止执行 merge/redirect apply（仅 proposal）；跨章操作必须独立 mutation_set(kind='global')

## 数据完整性
- **INV-010**：软删除不级联；关联对象标记 orphaned；hard purge 才物理删除
- **INV-010A**：redirect 禁止自指、必须防环（DB trigger），并建议定期压平多跳

## 预算控制
- **INV-011**：每个 run/step 必须有预算上限；超限触发降级或暂停
- **INV-012**：revision rounds 上限 = max_revision_rounds（默认 3）
- **INV-012A**：并发/速率/重试预算必须生效（max_inflight_calls / rate_limit_bucket / retry_budget）

## 审计与可复现
- **INV-013**：每次 LLM 调用必须记录 llm_calls（含 request_hash、usage_json）；大字段存 audit.db 或 blob store
- **INV-014**：ContextPack 组装过程必须完整记录（retrieval_session + context_pack_items：token_estimate、placement、裁剪原因）
- **INV-015**：outbox 消费必须幂等；重复消费不得造成重复写或状态漂移

## 项目隔离
- **INV-016**：所有查询必须显式 project_id 过滤（服务层注入），避免跨项目串数据
- **INV-017**：跨项目资源访问必须返回 403（E303_PROJECT_SCOPE_VIOLATION）

## 位置策略（ContextPack）
- **INV-018**：plan/style 块必须尾部锚定，裁剪时永远保留（对抗 Lost-in-the-middle）
- **INV-019**：token 估算模式必须预留 margin（建议 15%），避免超窗
