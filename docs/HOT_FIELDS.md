# JSON 热字段清单（M1 起强制维护）

规则：任何会用于 WHERE / ORDER BY / JOIN 的 JSON key 必须投影（generated column / KV / 关联表）。

## 投影表 DDL（v1.4）

```sql
-- node_tags: 从 graph_node_versions.tags_json 投影
CREATE TABLE node_tags (
  node_version_id TEXT NOT NULL,
  tag TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  PRIMARY KEY(node_version_id, tag),
  FOREIGN KEY(node_version_id) REFERENCES graph_node_versions(id)
);
CREATE INDEX idx_node_tags_tag ON node_tags(tag);

-- chunk_tags: 从 memory_chunks.tags_json 投影
CREATE TABLE chunk_tags (
  chunk_id TEXT NOT NULL,
  tag TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  PRIMARY KEY(chunk_id, tag),
  FOREIGN KEY(chunk_id) REFERENCES memory_chunks(id)
);
CREATE INDEX idx_chunk_tags_tag ON chunk_tags(tag);
```

> 完整 DDL 参见 `docs/spec/07-data-model.md` 的 v1.4 Hard Patch 迁移脚本中 `11) 热字段投影表`。

---

## Graph
- graph_node_versions.tags_json：投影到 `node_tags(node_version_id, tag)`
- graph_node_versions.attrs_json：
  - 若用于过滤（如 realm/level/faction_id），必须投影（generated column 或 node_attr_kv）

## Chapters
- chapters.plan_json：默认不投影（只读）
- chapters.review_reason：可直接列

## Runs
- runs.budget_json：若需要查询剩余预算，投影字段：
  - budget_remaining_tokens INTEGER
  - budget_remaining_cost REAL
- run_steps.budget_json：同上

## State Assertions
- state_assertions.object_json：按 predicate 定热字段
  - 常用：realm / location / possession / relationship_status
  - 建议：state_assertion_kv 或 generated columns

### state_assertion_kv DDL（可选投影表）
```sql
-- 当需要按 object_json 内的特定 key 过滤/排序时使用
CREATE TABLE state_assertion_kv (
  assertion_id TEXT NOT NULL,
  key TEXT NOT NULL,
  value_text TEXT,
  value_num REAL,
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  PRIMARY KEY(assertion_id, key),
  FOREIGN KEY(assertion_id) REFERENCES state_assertions(id)
);
CREATE INDEX idx_assertion_kv_key ON state_assertion_kv(key, value_text);
CREATE INDEX idx_assertion_kv_num ON state_assertion_kv(key, value_num);
```

## Memory
- memory_chunks.tags_json：如需按 tag 过滤，投影 `chunk_tags(chunk_id, tag)`
- meta_json：仅在明确需要过滤时投影

## Timeline
- story_events.attrs_json：如需按 arc/scene_type 过滤，投影

---

### Runs（可选投影 DDL）

> 仅当你确实需要按预算字段查询/排序时再做；否则保留 JSON 即可。  
> SQLite 生成列需要较新版本；不确定版本时，用“普通列 + 应用层写入”最稳妥。

**方案 A：普通列（推荐，版本无关）**
```sql
ALTER TABLE runs ADD COLUMN budget_remaining_tokens INTEGER;
ALTER TABLE runs ADD COLUMN budget_remaining_cost REAL;
ALTER TABLE run_steps ADD COLUMN budget_remaining_tokens INTEGER;
ALTER TABLE run_steps ADD COLUMN budget_remaining_cost REAL;

CREATE INDEX idx_runs_budget_tokens ON runs(project_id, budget_remaining_tokens);
CREATE INDEX idx_run_steps_budget_tokens ON run_steps(run_id, budget_remaining_tokens);
```

**方案 B：Generated Columns（SQLite 支持时可用）**
```sql
-- 示例 key：$.remaining_tokens / $.remaining_cost
ALTER TABLE runs ADD COLUMN budget_remaining_tokens INTEGER
  GENERATED ALWAYS AS (json_extract(budget_json, '$.remaining_tokens')) VIRTUAL;
ALTER TABLE runs ADD COLUMN budget_remaining_cost REAL
  GENERATED ALWAYS AS (json_extract(budget_json, '$.remaining_cost')) VIRTUAL;
```

