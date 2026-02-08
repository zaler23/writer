# 08 — 里程碑（M0a → M4，v1.4）

> v1.4 将原 M0 拆为 M0a/M0b，降低启动成本并将"防失控闸门"显式化。

## M0a — 最小可运行骨架（3–5天）
目标：`POST /swarm/run` 能用单模型跑出一章文本（无检索/无图谱/无回滚）
- 表：projects, chapters, chapter_text_versions, runs, run_steps, llm_calls
- 流程：draft → 直接写 final version（不做 writeback_plan，不做 mutation_set）
- 阶段说明：M0a 允许临时豁免 `INV-002/003/006/008`（无 finalize 两阶段、无写回级幂等、无章节乐观锁）；进入 M0b 后必须全部补齐并通过门禁测试
- 依赖：CONVENTIONS.md（ID/时间格式）、STATE_MACHINES.md（run/step 状态）
- 测试（必须）：
  - run 创建/完成状态流转
  - chapter 状态流转（planned → drafting → finalized）
  - LLM mock 测试（结构化输出可选）
  - 基本 API 端点可用性

## M0b — 防失控闸门（2–3天）
目标：幂等 finalize + mutation 可回滚 + 并发/崩溃抗事故
- 加表：mutation_sets, mutations(op_id), idempotency_keys(lease), outbox_events
- finalize：preview → apply（core.db 单事务）
- 依赖：INVARIANTS.md（INV-002/003/006/007/008）
- 测试（必须，门禁）：
  1) 并发 finalize 冲突测试（双 apply 竞争，预期一个成功一个 409）
  2) 崩溃恢复测试（apply 中断后重启一致）
  3) mutation op_id 去重测试（幂等重放/接管不重复写）
  4) 幂等 key 冲突测试（同 key 异 hash 返回 409）

## M1 — 记忆与 ContextPack（5–7天）
目标：检索增强写作（XML 标签 + 预算裁剪 + 尾部锚定）
- 加表：memory_chunks, (vec_embeddings or embeddings), retrieval_sessions, context_pack_items, draft_memory_chunks
- 输出：ContextPack 可复现（记录 items/token/placement/裁剪原因）
- 依赖：INVARIANTS.md（INV-014/018/019）、HOT_FIELDS.md
- 测试（必须）：
  - budget trimmer 规则（plan/style 尾部永保留）
  - token 计数双轨 + margin（15%）
  - outbox 幂等消费测试
  - 向量检索基本可用

## M2 — 图谱核心（7–10天）
目标：实体可管理、可检索、可消歧（但 merge/apply 仍可谨慎）
- 加表：graph_nodes, graph_node_versions, graph_edges, node_aliases, entity_resolution_runs, merge_proposals, draft_graph_*, node_tags
- 强制：写入前 resolve；canonical follow redirect；redirect 防环
- 依赖：INVARIANTS.md（INV-004/010A）
- 测试：
  - resolve golden cases（10–20 个已知消歧案例）
  - redirect follow + 防环触发器
  - 消歧权重可配置（project_settings）
  - draft → canonical 流程

## M3 — 一致性核心（7–10天）
目标：状态可断言、时间线可校验、快照可查
- 加表：state_assertions(默认 chapter_based), story_*, narrations, timeline_validation_reports, draft_state/timeline
- validate：before/after DAG 环检测（阻断）+ 区间一致性软告警
- 依赖：CONVENTIONS.md（truth_mode/anchor_mode 枚举）
- 测试：
  - cycle 检测（E204_CYCLE_DETECTED）
  - snapshot 有效期过滤
  - needs_review 标记策略
  - 冲突聚合（同 subject+predicate 多值）

## M4 — 高级能力（10–15天）
目标：bootstrap、回滚冲突检测增强、chat-with-graph、并行 swarm + 审批点、cleaning job、event_based 增强、SSE
- 加表：bootstrap_*, extraction_*, onboarding_*, recycle_bin, rollback_conflicts, chat_sessions, chat_turns
- 依赖：所有 INVARIANTS
- 测试：
  - 分章规则 golden
  - cold_start_plan golden
  - 回滚冲突报告（E205_ROLLBACK_DEPENDENTS）
  - SSE 事件流
  - chat 会话持久化
