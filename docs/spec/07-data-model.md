# 07 — 数据模型（SQLite DDL + 索引 + 分库/冷热 + v1.4 Draft/Canonical）

## 分库与存储策略
- `core.db`：世界真相（canonical world state）+ mutation_sets + outbox + 幂等键（最小必一致集合）
- `audit.db`：审计、运行中间产物、大字段 blobs（可缺失但可通过 outbox 重建）
- 大文本（prompt/response/step output）默认落文件系统（blob store）：hash→path；DB 仅存 hash/path/usage


- **分库建议（单库模式可忽略）**
  - 本文 E1/E3 DDL 默认按“单库”展示（便于直接建库与演示）
  - 建议放 **core.db**（必须强一致）：projects/project_settings、outlines、chapters/chapter_segments/chapter_text_versions、graph_nodes/graph_node_versions/graph_edges/node_aliases、state_assertions、story_timelines/story_events/event_order_constraints/narrations、memory_chunks（+ embeddings/vec_embeddings 若检索要求强一致）、merge_proposals、mutation_sets/mutations、rollback_conflicts、recycle_bin、idempotency_keys、outbox_events、draft_*、（可选）chat_sessions/chat_turns
  - 建议放 **audit.db**（可重放重建）：runs/run_steps、llm_calls/llm_call_blobs、retrieval_sessions/context_pack_items、entity_resolution_runs、timeline_validation_reports、bootstrap_jobs、graph_extraction_jobs/suggestions、onboarding_checklist_items 等
  - 分库注意：跨库不要建立 FK；跨库关联只能在应用层 join（或用 outbox 再落索引表）
  - 分库落地细则：若某表迁移到 `audit.db`，其指向 `core.db` 的 FK 需改为“逻辑外键”（保留 `*_id` 文本列，不建 FK），并由 service 层做 project_id + existence 校验

> v1.4：finalize.apply 的强原子性只保证 core.db。审计一致性通过 outbox 重放保证最终一致。

---

## E1/E3 基线 DDL（v1.4 Consolidated）
```sql
-- core.db — v1.4 基线（新库建库脚本；升级旧库需执行下方 Hard Patch）
-- 说明：基线尽量包含 v1.4 列；对 SQLite 已存在表的“补列/重建”迁移，见后半部分 Hard Patch。
-- 提示：若采用 core/audit 分库，audit 表请在 audit.db 执行（见“分库与存储策略”）。

-- E1.1 基础与配置
CREATE TABLE projects (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  genre TEXT,
  premise TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE project_settings (
  id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  settings_json TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY(project_id) REFERENCES projects(id)
);

CREATE TABLE prompt_templates (
  id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  name TEXT NOT NULL,
  role TEXT NOT NULL,
  template_text TEXT NOT NULL,
  variables_json TEXT,
  version_no INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY(project_id) REFERENCES projects(id)
);

CREATE TABLE llm_providers (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  base_url TEXT,
  config_json TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE llm_models (
  id TEXT PRIMARY KEY,
  provider_id TEXT NOT NULL,
  model_name TEXT NOT NULL,
  capabilities_json TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY(provider_id) REFERENCES llm_providers(id)
);

CREATE TABLE swarm_profiles (
  id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  name TEXT NOT NULL,
  schema_version TEXT NOT NULL DEFAULT '1.2',
  profile_version TEXT NOT NULL DEFAULT '1.0.0',
  profile_json TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY(project_id) REFERENCES projects(id)
);

CREATE TABLE traversal_profiles (
  id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  name TEXT NOT NULL,
  schema_version TEXT NOT NULL DEFAULT '1.2',
  profile_version TEXT NOT NULL DEFAULT '1.0.0',
  profile_json TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY(project_id) REFERENCES projects(id)
);

CREATE TABLE style_guides (
  id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  name TEXT NOT NULL,
  schema_version TEXT NOT NULL DEFAULT '1.2',
  guide_version TEXT NOT NULL DEFAULT '1.0.0',
  guide_json TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY(project_id) REFERENCES projects(id)
);

-- E1.2 大纲与章节
CREATE TABLE outlines (
  id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  version INTEGER NOT NULL,
  outline_json TEXT NOT NULL,
  created_at TEXT NOT NULL,
  FOREIGN KEY(project_id) REFERENCES projects(id)
);

CREATE TABLE chapters (
  id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  volume_no INTEGER DEFAULT 1,
  chapter_no INTEGER NOT NULL,
  title TEXT,
  status TEXT NOT NULL DEFAULT 'planned',  -- planned|drafting|reviewing|revising|validating|finalizing|finalized|needs_review
  needs_review INTEGER NOT NULL DEFAULT 0,
  review_reason TEXT,
  plan_json TEXT,
  traversal_profile_id TEXT,
  style_guide_id TEXT,
  lock_version INTEGER NOT NULL DEFAULT 0,  -- v1.4: 乐观锁版本
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  UNIQUE(project_id, volume_no, chapter_no),
  FOREIGN KEY(project_id) REFERENCES projects(id),
  FOREIGN KEY(traversal_profile_id) REFERENCES traversal_profiles(id),
  FOREIGN KEY(style_guide_id) REFERENCES style_guides(id)
);

-- v1.4: chapter status 枚举约束
CREATE TRIGGER IF NOT EXISTS trg_chapters_status_enum_ins
BEFORE INSERT ON chapters
WHEN NEW.status NOT IN ('planned', 'drafting', 'reviewing', 'revising', 'validating', 'finalizing', 'finalized', 'needs_review')
BEGIN
  SELECT RAISE(ABORT, 'chapters.status must be valid enum value');
END;

CREATE TRIGGER IF NOT EXISTS trg_chapters_status_enum_upd
BEFORE UPDATE OF status ON chapters
WHEN NEW.status NOT IN ('planned', 'drafting', 'reviewing', 'revising', 'validating', 'finalizing', 'finalized', 'needs_review')
BEGIN
  SELECT RAISE(ABORT, 'chapters.status must be valid enum value');
END;

CREATE TABLE chapter_text_versions (
  id TEXT PRIMARY KEY,
  chapter_id TEXT NOT NULL,
  version_no INTEGER NOT NULL,
  stage TEXT NOT NULL,
  content_text TEXT NOT NULL,
  source_run_id TEXT,
  source_step_id TEXT,
  created_at TEXT NOT NULL,
  FOREIGN KEY(chapter_id) REFERENCES chapters(id)
);

CREATE TABLE chapter_segments (
  id TEXT PRIMARY KEY,
  chapter_id TEXT NOT NULL,
  segment_no INTEGER NOT NULL,
  title TEXT,
  pov_node_id TEXT,
  segment_type TEXT,
  content_text TEXT,
  attrs_json TEXT,
  is_deleted INTEGER NOT NULL DEFAULT 0,
  deleted_at TEXT,
  deleted_reason TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  UNIQUE(chapter_id, segment_no),
  FOREIGN KEY(chapter_id) REFERENCES chapters(id)
);

CREATE TABLE chapter_reviews (
  id TEXT PRIMARY KEY,
  chapter_id TEXT NOT NULL,
  version_id TEXT NOT NULL,
  review_type TEXT NOT NULL DEFAULT 'logic',
  report_json TEXT NOT NULL,
  source_run_id TEXT,
  source_step_id TEXT,
  created_at TEXT NOT NULL,
  FOREIGN KEY(chapter_id) REFERENCES chapters(id),
  FOREIGN KEY(version_id) REFERENCES chapter_text_versions(id)
);

CREATE TABLE chapter_graph_links (
  id TEXT PRIMARY KEY,
  chapter_id TEXT NOT NULL,
  node_id TEXT NOT NULL,
  relation TEXT NOT NULL,
  note TEXT,
  created_at TEXT NOT NULL,
  FOREIGN KEY(chapter_id) REFERENCES chapters(id),
  FOREIGN KEY(node_id) REFERENCES graph_nodes(id)  -- v1.4: 补齐 FK
);

-- E1.3 图谱
CREATE TABLE graph_nodes (
  id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  node_type TEXT NOT NULL,
  current_version_id TEXT,
  visibility TEXT NOT NULL DEFAULT 'explicit',
  status TEXT NOT NULL DEFAULT 'open',
  is_deleted INTEGER NOT NULL DEFAULT 0,
  deleted_at TEXT,
  deleted_reason TEXT,
  redirected_to_node_id TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY(project_id) REFERENCES projects(id)
);

CREATE TABLE graph_node_versions (
  id TEXT PRIMARY KEY,
  node_id TEXT NOT NULL,
  version_no INTEGER NOT NULL,
  title TEXT,
  summary TEXT,
  tags_json TEXT,
  attrs_json TEXT,
  created_at TEXT NOT NULL,
  created_by_run_id TEXT,
  note TEXT,
  FOREIGN KEY(node_id) REFERENCES graph_nodes(id),
  UNIQUE(node_id, version_no)
);

CREATE TABLE graph_edges (
  id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  edge_type TEXT NOT NULL,
  src_node_id TEXT NOT NULL,
  dst_node_id TEXT NOT NULL,
  weight REAL DEFAULT 1.0,
  attrs_json TEXT,
  is_deleted INTEGER NOT NULL DEFAULT 0,
  deleted_at TEXT,
  deleted_reason TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY(project_id) REFERENCES projects(id),
  FOREIGN KEY(src_node_id) REFERENCES graph_nodes(id),  -- v1.4: 补齐 FK
  FOREIGN KEY(dst_node_id) REFERENCES graph_nodes(id)   -- v1.4: 补齐 FK
);

CREATE TABLE node_aliases (
  id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  node_id TEXT NOT NULL,
  alias_text TEXT NOT NULL,
  normalized_text TEXT NOT NULL,
  alias_type TEXT NOT NULL DEFAULT 'name',
  created_at TEXT NOT NULL,
  FOREIGN KEY(project_id) REFERENCES projects(id),
  FOREIGN KEY(node_id) REFERENCES graph_nodes(id)
);

CREATE TABLE entity_resolution_runs (
  id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  input_json TEXT NOT NULL,
  candidates_json TEXT NOT NULL,
  decision_json TEXT NOT NULL,
  created_at TEXT NOT NULL,
  FOREIGN KEY(project_id) REFERENCES projects(id)
);

CREATE TABLE merge_proposals (
  id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  node_a_id TEXT NOT NULL,
  node_b_id TEXT NOT NULL,
  score REAL NOT NULL,
  evidence_json TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'proposed',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY(project_id) REFERENCES projects(id),
  FOREIGN KEY(node_a_id) REFERENCES graph_nodes(id),  -- v1.4: 补齐 FK
  FOREIGN KEY(node_b_id) REFERENCES graph_nodes(id)   -- v1.4: 补齐 FK
);

-- E1.4 动态设定（v1.4 重建）
CREATE TABLE state_assertions (
  id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  subject_node_id TEXT NOT NULL,
  predicate TEXT NOT NULL,
  object_json TEXT NOT NULL,
  truth_mode TEXT NOT NULL DEFAULT 'asserted',
  anchor_mode TEXT NOT NULL DEFAULT 'chapter_based',  -- v1.4: 修正默认值
  story_valid_from_event_id TEXT,
  story_valid_to_event_id TEXT,
  valid_from_chapter_id TEXT,
  valid_to_chapter_id TEXT,
  created_in_chapter_id TEXT,  -- v1.4: 新增，用于回滚闭包分析
  introduced_in_version_id TEXT,
  attrs_json TEXT,
  created_at TEXT NOT NULL,
  FOREIGN KEY(project_id) REFERENCES projects(id),
  FOREIGN KEY(subject_node_id) REFERENCES graph_nodes(id),
  FOREIGN KEY(story_valid_from_event_id) REFERENCES story_events(id),
  FOREIGN KEY(story_valid_to_event_id) REFERENCES story_events(id),
  FOREIGN KEY(valid_from_chapter_id) REFERENCES chapters(id),
  FOREIGN KEY(valid_to_chapter_id) REFERENCES chapters(id),
  FOREIGN KEY(created_in_chapter_id) REFERENCES chapters(id),
  FOREIGN KEY(introduced_in_version_id) REFERENCES graph_node_versions(id)
);

-- v1.4: 强制新写入必须有 created_in_chapter_id
CREATE TRIGGER IF NOT EXISTS trg_state_assertions_created_in_chapter_required
BEFORE INSERT ON state_assertions
WHEN NEW.created_in_chapter_id IS NULL OR NEW.created_in_chapter_id = ''
BEGIN
  SELECT RAISE(ABORT, 'created_in_chapter_id is required (v1.4)');
END;

-- E1.5 时间线
CREATE TABLE story_timelines (
  id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  name TEXT NOT NULL,
  attrs_json TEXT,
  created_at TEXT NOT NULL,
  FOREIGN KEY(project_id) REFERENCES projects(id)
);

CREATE TABLE story_events (
  id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  timeline_id TEXT,
  title TEXT NOT NULL,
  summary TEXT,
  story_time_from REAL,
  story_time_to REAL,
  time_precision TEXT DEFAULT 'unknown',
  attrs_json TEXT,
  created_at TEXT NOT NULL,
  FOREIGN KEY(project_id) REFERENCES projects(id),
  FOREIGN KEY(timeline_id) REFERENCES story_timelines(id)
);

CREATE TABLE event_order_constraints (
  id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  event_a_id TEXT NOT NULL,
  relation TEXT NOT NULL,
  event_b_id TEXT NOT NULL,
  constraint_strength TEXT NOT NULL DEFAULT 'hard',
  justification TEXT,
  created_at TEXT NOT NULL,
  FOREIGN KEY(project_id) REFERENCES projects(id),
  FOREIGN KEY(event_a_id) REFERENCES story_events(id),  -- v1.4: 补齐 FK
  FOREIGN KEY(event_b_id) REFERENCES story_events(id)   -- v1.4: 补齐 FK
);

CREATE TABLE narrations (
  id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  event_id TEXT NOT NULL,
  chapter_id TEXT,
  segment_id TEXT,
  pov_node_id TEXT,
  narration_mode TEXT NOT NULL DEFAULT 'normal',
  reliability REAL DEFAULT 1.0,
  text_span_json TEXT,
  created_at TEXT NOT NULL,
  FOREIGN KEY(project_id) REFERENCES projects(id),
  FOREIGN KEY(event_id) REFERENCES story_events(id),     -- v1.4: 补齐 FK
  FOREIGN KEY(chapter_id) REFERENCES chapters(id),       -- v1.4: 补齐 FK
  FOREIGN KEY(segment_id) REFERENCES chapter_segments(id), -- v1.4: 补齐 FK
  FOREIGN KEY(pov_node_id) REFERENCES graph_nodes(id)    -- v1.4: 补齐 FK
);

CREATE TABLE timeline_validation_reports (
  id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  run_id TEXT,
  chapter_id TEXT,
  conflicts_json TEXT NOT NULL,
  is_blocking INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL,
  FOREIGN KEY(project_id) REFERENCES projects(id),
  FOREIGN KEY(run_id) REFERENCES runs(id),       -- v1.4: 补齐 FK
  FOREIGN KEY(chapter_id) REFERENCES chapters(id) -- v1.4: 补齐 FK
);

-- E1.6 记忆库
CREATE TABLE memory_chunks (
  id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  chapter_id TEXT,
  source_version_id TEXT,
  chunk_type TEXT NOT NULL,
  content_text TEXT NOT NULL,
  summary TEXT,
  visibility TEXT DEFAULT 'explicit',
  tags_json TEXT,
  meta_json TEXT,
  created_at TEXT NOT NULL,
  FOREIGN KEY(project_id) REFERENCES projects(id)
);

CREATE TABLE embeddings (
  id TEXT PRIMARY KEY,
  chunk_id TEXT NOT NULL,
  embedding_model TEXT NOT NULL,
  dims INTEGER NOT NULL,
  storage_mode TEXT NOT NULL DEFAULT 'vec', -- 'vec' | 'blob'
  vector_blob BLOB,                         -- storage_mode='blob' 时必填；'vec' 时通常为 NULL
  created_at TEXT NOT NULL,
  UNIQUE(chunk_id, embedding_model),
  FOREIGN KEY(chunk_id) REFERENCES memory_chunks(id)
);

CREATE TABLE retrieval_sessions (
  id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  chapter_id TEXT,
  run_id TEXT,
  mode TEXT NOT NULL DEFAULT 'write',
  query_json TEXT NOT NULL,
  created_at TEXT NOT NULL,
  FOREIGN KEY(project_id) REFERENCES projects(id)
);

CREATE TABLE context_pack_items (
  id TEXT PRIMARY KEY,
  retrieval_session_id TEXT NOT NULL,
  item_type TEXT NOT NULL,
  source_ref_json TEXT NOT NULL,
  token_estimate INTEGER NOT NULL DEFAULT 0,
  importance REAL NOT NULL DEFAULT 0.5,
  placement TEXT NOT NULL DEFAULT 'middle',
  created_at TEXT NOT NULL,
  FOREIGN KEY(retrieval_session_id) REFERENCES retrieval_sessions(id)
);

-- E1.7 运行与审计（基线保留）
CREATE TABLE runs (
  id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  swarm_profile_id TEXT,
  run_type TEXT NOT NULL,
  target_chapter_id TEXT,
  status TEXT NOT NULL,
  input_json TEXT,
  output_json TEXT,
  budget_json TEXT,
  started_at TEXT NOT NULL,
  finished_at TEXT,
  FOREIGN KEY(project_id) REFERENCES projects(id)
);

CREATE TABLE run_steps (
  id TEXT PRIMARY KEY,
  run_id TEXT NOT NULL,
  step_no INTEGER NOT NULL,
  step_type TEXT NOT NULL,
  role TEXT,
  status TEXT NOT NULL,
  requires_approval INTEGER NOT NULL DEFAULT 0,
  approval_status TEXT NOT NULL DEFAULT 'n/a',
  override_payload_json TEXT,
  input_json TEXT,
  output_json TEXT,
  budget_json TEXT,
  started_at TEXT NOT NULL,
  finished_at TEXT,
  error_text TEXT,
  FOREIGN KEY(run_id) REFERENCES runs(id)
);

CREATE TABLE llm_calls (
  id TEXT PRIMARY KEY,
  run_id TEXT,
  step_id TEXT,
  provider_id TEXT,
  model_id TEXT,
  purpose TEXT,
  request_hash TEXT NOT NULL,
  response_hash TEXT,
  usage_json TEXT,
  status TEXT NOT NULL,
  error_text TEXT,
  created_at TEXT NOT NULL
);

CREATE TABLE llm_call_blobs (
  id TEXT PRIMARY KEY,
  llm_call_id TEXT NOT NULL,
  storage_tier TEXT NOT NULL DEFAULT 'hot',
  request_json TEXT,
  response_text TEXT,
  created_at TEXT NOT NULL,
  FOREIGN KEY(llm_call_id) REFERENCES llm_calls(id)
);

-- E1.8 事实抽取
CREATE TABLE extracted_facts (
  id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  chapter_id TEXT,
  version_id TEXT,
  fact_type TEXT NOT NULL,
  fact_text TEXT NOT NULL,
  entities_json TEXT,
  confidence REAL DEFAULT 0.7,
  source_span_json TEXT,
  created_at TEXT NOT NULL,
  FOREIGN KEY(project_id) REFERENCES projects(id)
);

-- E1.9 回收站与回滚
CREATE TABLE recycle_bin (
  id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  object_type TEXT NOT NULL,
  object_id TEXT NOT NULL,
  snapshot_json TEXT NOT NULL,
  deleted_at TEXT NOT NULL,
  deleted_reason TEXT,
  restore_hint_json TEXT,
  FOREIGN KEY(project_id) REFERENCES projects(id)
);

CREATE TABLE mutation_sets (
  id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  run_id TEXT,
  chapter_id TEXT,  -- v1.4: 新增
  kind TEXT NOT NULL DEFAULT 'chapter',  -- v1.4: 新增 ('chapter' | 'global')
  name TEXT,
  created_at TEXT NOT NULL,
  FOREIGN KEY(project_id) REFERENCES projects(id),
  FOREIGN KEY(chapter_id) REFERENCES chapters(id)
);

-- v1.4: kind 枚举约束
CREATE TRIGGER IF NOT EXISTS trg_mutation_sets_kind_enum_ins
BEFORE INSERT ON mutation_sets
WHEN NEW.kind NOT IN ('chapter', 'global')
BEGIN
  SELECT RAISE(ABORT, 'mutation_sets.kind must be chapter|global');
END;

CREATE TRIGGER IF NOT EXISTS trg_mutation_sets_kind_enum_upd
BEFORE UPDATE OF kind ON mutation_sets
WHEN NEW.kind NOT IN ('chapter', 'global')
BEGIN
  SELECT RAISE(ABORT, 'mutation_sets.kind must be chapter|global');
END;

CREATE TABLE mutations (
  id TEXT PRIMARY KEY,
  mutation_set_id TEXT NOT NULL,
  op_id TEXT NOT NULL,  -- v1.4: 直接包含（原 v1.3 补丁）
  object_type TEXT NOT NULL,
  object_id TEXT NOT NULL,
  action TEXT NOT NULL,
  before_json TEXT,
  after_json TEXT,
  created_at TEXT NOT NULL,
  FOREIGN KEY(mutation_set_id) REFERENCES mutation_sets(id)
);
CREATE UNIQUE INDEX idx_mutations_op_id ON mutations(mutation_set_id, op_id);

-- v1.4: op_id 必填
CREATE TRIGGER IF NOT EXISTS trg_mutations_op_id_required
BEFORE INSERT ON mutations
WHEN NEW.op_id IS NULL OR NEW.op_id = ''
BEGIN
  SELECT RAISE(ABORT, 'mutations.op_id is required');
END;

CREATE TABLE rollback_conflicts (
  id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  mutation_set_id TEXT NOT NULL,
  conflict_report_json TEXT NOT NULL,
  resolution TEXT NOT NULL DEFAULT 'pending',
  created_at TEXT NOT NULL,
  FOREIGN KEY(project_id) REFERENCES projects(id),
  FOREIGN KEY(mutation_set_id) REFERENCES mutation_sets(id)  -- v1.4: 补齐 FK
);

-- E1.10 图谱抽取与 Bootstrap
CREATE TABLE graph_extraction_jobs (
  id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  mode TEXT NOT NULL,
  scope_json TEXT NOT NULL,
  budget_json TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'queued',
  result_summary_json TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY(project_id) REFERENCES projects(id)
);

CREATE TABLE graph_extraction_suggestions (
  id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  job_id TEXT,
  suggestion_type TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'proposed',
  resolution_json TEXT,
  approved_by TEXT,
  approved_at TEXT,
  created_at TEXT NOT NULL,
  FOREIGN KEY(project_id) REFERENCES projects(id)
);

CREATE TABLE bootstrap_jobs (
  id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  job_type TEXT NOT NULL,
  input_json TEXT NOT NULL,
  budget_json TEXT,
  status TEXT NOT NULL DEFAULT 'queued',
  output_json TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY(project_id) REFERENCES projects(id)
);

CREATE TABLE onboarding_checklist_items (
  id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  item_key TEXT NOT NULL,
  title TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'todo',
  required INTEGER NOT NULL DEFAULT 1,
  evidence_ref_json TEXT,
  updated_at TEXT NOT NULL,
  FOREIGN KEY(project_id) REFERENCES projects(id)
);

-- E3 v1.3 新增：idempotency_keys / outbox_events / JSON 热字段示例
-- Note: mutations op_id 已合并到基线 DDL
CREATE TABLE idempotency_keys (
  id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  endpoint TEXT NOT NULL,
  idempotency_key TEXT NOT NULL,
  request_hash TEXT NOT NULL,
  status TEXT NOT NULL,          -- processing/succeeded/failed
  lease_owner TEXT,              -- 用于 processing 接管
  lease_until TEXT,              -- ISO8601 UTC
  http_status INTEGER,           -- succeeded 时缓存原始 HTTP 状态码
  response_json TEXT,            -- succeeded 时缓存响应体
  response_hash TEXT,            -- succeeded 时可选：响应哈希（便于一致性检查）
  error_text TEXT,               -- failed 时缓存错误
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  UNIQUE(project_id, endpoint, idempotency_key),
  FOREIGN KEY(project_id) REFERENCES projects(id)
);
CREATE INDEX IF NOT EXISTS idx_idem_lookup ON idempotency_keys(project_id, endpoint, idempotency_key);
CREATE INDEX IF NOT EXISTS idx_idem_lease ON idempotency_keys(status, lease_until);

CREATE TABLE outbox_events (
  id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  event_type TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'queued',
  attempts INTEGER NOT NULL DEFAULT 0,
  last_error TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY(project_id) REFERENCES projects(id)
);
CREATE INDEX idx_outbox_status ON outbox_events(project_id, status, created_at);

-- E3.1 Chat 会话表（v1.4 基线）
CREATE TABLE chat_sessions (
  id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  title TEXT,
  mode TEXT NOT NULL DEFAULT 'qa',  -- 'qa' | 'explore'
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY(project_id) REFERENCES projects(id)
);

CREATE TABLE chat_turns (
  id TEXT PRIMARY KEY,
  session_id TEXT NOT NULL,
  turn_no INTEGER NOT NULL,
  role TEXT NOT NULL,  -- 'user' | 'assistant'
  content_text TEXT NOT NULL,
  meta_json TEXT,  -- 可存储 sources、tokens 等元信息
  created_at TEXT NOT NULL,
  FOREIGN KEY(session_id) REFERENCES chat_sessions(id),
  UNIQUE(session_id, turn_no)
);
CREATE INDEX idx_chat_turns_session ON chat_turns(session_id, turn_no);

```

---

## v1.4 Hard Patch（必须执行的补丁迁移）
```sql
-- v1.4 Hard Patch migrations (must apply)

-- 0) SQLite pragmas (runtime)
PRAGMA foreign_keys=ON;
PRAGMA journal_mode=WAL;
PRAGMA busy_timeout=5000;

-- 1) ID conventions handled in app layer (ULID + optional prefix) — see docs/CONVENTIONS.md

-- 2) Chapters optimistic lock - 已合并到基线 DDL (lock_version 列)

-- 3) Fix FK gaps (selected critical)
-- chapter_graph_links.node_id -> graph_nodes - 已合并到基线 DDL
-- narrations FK - 已合并到基线 DDL
-- event_order_constraints FK - 已合并到基线 DDL
-- NOTE: 对于已存在的表，需通过"重建表迁移"补齐 FK

-- 4) state_assertions 重建 - 已合并到基线 DDL
-- anchor_mode 默认值改为 'chapter_based'
-- 新增 created_in_chapter_id 列
-- 所有 FK 已补齐

-- 5) idempotency_keys lease fields (for processing takeover, 仅升级旧库需要；新库基线已包含)
ALTER TABLE idempotency_keys ADD COLUMN lease_owner TEXT;
ALTER TABLE idempotency_keys ADD COLUMN lease_until TEXT;
ALTER TABLE idempotency_keys ADD COLUMN http_status INTEGER;
ALTER TABLE idempotency_keys ADD COLUMN response_hash TEXT;
CREATE INDEX IF NOT EXISTS idx_idem_lookup ON idempotency_keys(project_id, endpoint, idempotency_key);
CREATE INDEX IF NOT EXISTS idx_idem_lease ON idempotency_keys(status, lease_until);

-- 6) Redirect protections on graph_nodes (使用 TRIGGER 替代 CHECK)
-- 注意：SQLite 不支持 ALTER TABLE ADD CONSTRAINT，使用 TRIGGER 实现
CREATE TRIGGER IF NOT EXISTS trg_graph_nodes_redirect_no_self
BEFORE UPDATE OF redirected_to_node_id ON graph_nodes
WHEN NEW.redirected_to_node_id = NEW.id
BEGIN
  SELECT RAISE(ABORT, 'Redirect cannot point to self');
END;

CREATE TRIGGER IF NOT EXISTS trg_graph_nodes_redirect_no_cycle
BEFORE UPDATE OF redirected_to_node_id ON graph_nodes
WHEN NEW.redirected_to_node_id IS NOT NULL
BEGIN
  WITH RECURSIVE chain(id) AS (
    SELECT NEW.redirected_to_node_id
    UNION ALL
    SELECT g.redirected_to_node_id
    FROM graph_nodes g
    JOIN chain c ON g.id = c.id
    WHERE g.redirected_to_node_id IS NOT NULL
  )
  SELECT CASE
    WHEN EXISTS(SELECT 1 FROM chain WHERE id = NEW.id)
    THEN RAISE(ABORT, 'redirect cycle detected')
  END;
END;

CREATE INDEX idx_nodes_redirect ON graph_nodes(project_id, redirected_to_node_id);

-- 7) Soft-delete CHECK constraints (new tables should include; legacy requires rebuild)
-- CHECK(is_deleted IN (0,1))

-- 8) Draft tables (staging area)
CREATE TABLE draft_graph_nodes (
  id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  chapter_id TEXT NOT NULL,
  node_type TEXT NOT NULL,
  title TEXT,
  summary TEXT,
  attrs_json TEXT,
  based_on_node_id TEXT,
  status TEXT NOT NULL DEFAULT 'draft', -- draft/approved/rejected
  source TEXT NOT NULL DEFAULT 'llm',   -- llm/human/import
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY(project_id) REFERENCES projects(id),
  FOREIGN KEY(chapter_id) REFERENCES chapters(id)
);

CREATE TABLE draft_graph_edges (
  id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  chapter_id TEXT NOT NULL,
  edge_type TEXT NOT NULL,
  src_node_ref TEXT NOT NULL, -- may reference draft or canonical id
  dst_node_ref TEXT NOT NULL,
  attrs_json TEXT,
  status TEXT NOT NULL DEFAULT 'draft',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY(project_id) REFERENCES projects(id),
  FOREIGN KEY(chapter_id) REFERENCES chapters(id)
);

CREATE TABLE draft_node_aliases (
  id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  chapter_id TEXT NOT NULL,
  alias_text TEXT NOT NULL,
  normalized_text TEXT NOT NULL,
  node_ref TEXT NOT NULL, -- draft or canonical id
  status TEXT NOT NULL DEFAULT 'draft',
  source TEXT NOT NULL DEFAULT 'llm',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY(project_id) REFERENCES projects(id),
  FOREIGN KEY(chapter_id) REFERENCES chapters(id)
);
CREATE INDEX idx_draft_alias_norm ON draft_node_aliases(project_id, normalized_text);
CREATE INDEX idx_draft_alias_node ON draft_node_aliases(project_id, node_ref);

CREATE TABLE draft_state_assertions (
  id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  chapter_id TEXT NOT NULL,
  subject_node_ref TEXT NOT NULL,
  predicate TEXT NOT NULL,
  object_json TEXT NOT NULL,
  truth_mode TEXT NOT NULL DEFAULT 'asserted',
  anchor_mode TEXT NOT NULL DEFAULT 'chapter_based',
  status TEXT NOT NULL DEFAULT 'draft',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY(project_id) REFERENCES projects(id),
  FOREIGN KEY(chapter_id) REFERENCES chapters(id)
);

CREATE TABLE draft_story_events (
  id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  chapter_id TEXT NOT NULL,
  timeline_id TEXT,
  title TEXT NOT NULL,
  summary TEXT,
  story_time_from REAL,
  story_time_to REAL,
  time_precision TEXT DEFAULT 'unknown',
  attrs_json TEXT,
  status TEXT NOT NULL DEFAULT 'draft',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY(project_id) REFERENCES projects(id),
  FOREIGN KEY(chapter_id) REFERENCES chapters(id)
);

CREATE TABLE draft_event_order_constraints (
  id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  chapter_id TEXT NOT NULL,
  event_a_ref TEXT NOT NULL,   -- draft or canonical
  relation TEXT NOT NULL,      -- before/after/overlap/contain...
  event_b_ref TEXT NOT NULL,   -- draft or canonical
  constraint_strength TEXT NOT NULL DEFAULT 'hard',
  justification TEXT,
  status TEXT NOT NULL DEFAULT 'draft',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY(project_id) REFERENCES projects(id),
  FOREIGN KEY(chapter_id) REFERENCES chapters(id)
);
CREATE INDEX idx_draft_constraints_chapter ON draft_event_order_constraints(project_id, chapter_id);

CREATE TABLE draft_narrations (
  id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  chapter_id TEXT NOT NULL,
  event_ref TEXT NOT NULL,   -- draft or canonical
  segment_id TEXT,
  pov_node_ref TEXT,
  narration_mode TEXT NOT NULL DEFAULT 'normal',
  reliability REAL DEFAULT 1.0,
  text_span_json TEXT,
  status TEXT NOT NULL DEFAULT 'draft',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY(project_id) REFERENCES projects(id),
  FOREIGN KEY(chapter_id) REFERENCES chapters(id)
);

CREATE TABLE draft_memory_chunks (
  id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  chapter_id TEXT NOT NULL,
  chunk_type TEXT NOT NULL,
  content_text TEXT NOT NULL,
  summary TEXT,
  tags_json TEXT,
  meta_json TEXT,
  status TEXT NOT NULL DEFAULT 'draft',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY(project_id) REFERENCES projects(id),
  FOREIGN KEY(chapter_id) REFERENCES chapters(id)
);

-- 9) Outbox: finalize apply must emit events; consumer writes audit/indices
-- Outbox already exists in v1.3 baseline; keep.

-- 10) Minimal indexes (additions beyond v1.3 minimal set)
CREATE INDEX idx_draft_nodes_chapter ON draft_graph_nodes(project_id, chapter_id, node_type);
CREATE INDEX idx_draft_edges_chapter ON draft_graph_edges(project_id, chapter_id, edge_type);
CREATE INDEX idx_draft_assertions_chapter ON draft_state_assertions(project_id, chapter_id, predicate);
CREATE INDEX idx_draft_events_chapter ON draft_story_events(project_id, chapter_id);
CREATE INDEX idx_draft_chunks_chapter ON draft_memory_chunks(project_id, chapter_id, chunk_type);

-- 11) 热字段投影表（v1.4）
CREATE TABLE node_tags (
  node_version_id TEXT NOT NULL,
  tag TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  PRIMARY KEY(node_version_id, tag),
  FOREIGN KEY(node_version_id) REFERENCES graph_node_versions(id)
);
CREATE INDEX idx_node_tags_tag ON node_tags(tag);

CREATE TABLE chunk_tags (
  chunk_id TEXT NOT NULL,
  tag TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  PRIMARY KEY(chunk_id, tag),
  FOREIGN KEY(chunk_id) REFERENCES memory_chunks(id)
);
CREATE INDEX idx_chunk_tags_tag ON chunk_tags(tag);

-- 12) 向量存储（v1.4 - 方案 A: sqlite-vec）
-- 注意：需要加载 sqlite-vec 扩展
-- 维度按模型调整：text-embedding-3-small=1536, text-embedding-ada-002=1536
CREATE VIRTUAL TABLE vec_embeddings USING vec0(
  chunk_id TEXT PRIMARY KEY,
  embedding FLOAT[1536]
);
-- 方案 B（备选）：不使用 sqlite-vec，改用 embeddings.storage_mode='blob' + vector_blob（或外接向量库）
-- 选择方案后在 ADR-003 固化决策

-- 13) Chat 会话表 - 已合并到基线 DDL（E3.1），此处仅供升级旧库参考
-- 新库无需执行以下语句（基线已包含）
-- CREATE TABLE chat_sessions (...);
-- CREATE TABLE chat_turns (...);

```

---

## v1.4 索引最小集（建议）
（除 v1.3 E4 外，新增 draft 与幂等租约索引已在补丁中体现）

---

## 向量存储选择（必须二选一）
- 方案 A（推荐）：sqlite-vec 虚拟表 `vec0(...)` 存 embedding，metadata 另表
- 方案 B：现有 embeddings.vector_blob（BLOB）+ brute-force 或外接向量库

v1.4 建议：M0–M1 选 A（sqlite-vec），并在 `docs/adr/003-vector-store-choice.md` 固化决策。

> DDL 已在上方 v1.4 补丁第 12 节定义。

---

## 外键完整性说明
SQLite 对新增外键限制较多，v1.4 要求：
- 对关键表通过“重建表迁移”补齐 FK（并在 migration 中严格 `PRAGMA foreign_keys=ON`）。
- 所有业务写入路径必须通过 Service/Repo 封装，保证 project_id scope 与 canonical follow（INV-004）。
