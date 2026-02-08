# 05 — API 规范（v1.4）

> v1.4 核心：**写入分层**。除 finalize.apply（story-canonical）与少量 admin/config 写入外，任何接口不得修改世界真相（见 INV-001）。

## C1 通用约束（必须）
- 所有写操作必须支持 `Idempotency-Key`（header）
- 写响应必须返回：`request_id`、`idempotency_key`（若适用）、若产生真相写回则返回 `mutation_set_id`
- finalize 必须包含乐观锁字段：`expected_lock_version`
- 失败重试幂等：
  - 请求级：idempotency_keys 去重
  - 写回级：mutations(mutation_set_id, op_id) 去重（见 INV-006）

## C2 端点分区（v1.4）

> 方法约定：`POST=create`，`PUT=update`，`DELETE=delete`。对历史实现中的“POST upsert”可保留，但必须兼容下述规范路径。

### 1) Canonical（只读，返回世界真相视图）
- `GET /projects`
- `GET /projects/{id}`
- `GET /chapters`
- `GET /chapters/{id}`（元信息/计划字段）
- `GET /graph/search`（默认 follow redirect；不返回 redirect 节点作为实体）
- `GET /graph/nodes/{id}`（follow redirect）
- `GET /graph/nodes/{id}/versions`
- `GET /graph/nodes/{id}/edges`
- `GET /graph/snapshot`（按章节合成 StateSnapshot）
- `GET /memory/search`
- `GET /timeline/events`
- `GET /timeline/events/{id}`
- `GET /timeline/constraints`
- `GET /timeline/narrations`
- `GET /state/assertions`
- `GET /state/assertions/{id}`
- 列表端点统一 cursor 分页：`limit` + `after`

### 2) Admin/Config（允许写 canonical 的“非 story-canonical”配置表）
> 这些写入不改变“世界真相”语义，只改配置/计划元数据；仍需 Idempotency-Key（INV-002）。
- `POST /projects`
- `PUT /projects/{id}`
- `GET /projects/{id}/settings`
- `PUT /projects/{id}/settings`
- `POST /chapters`（创建章节）
- `PUT /chapters/{id}`（仅更新计划字段；章节 status/lock_version 由系统管理）
- `POST /chapters/{id}/segments`（章节分段与编辑辅助；不等同于 finalize 写回）
- `GET /chapters/{id}/segments`
- `GET /chapters/{id}/reviews`
- `GET /chapters/{id}/text-versions`

### 3) Draft（可写草稿区，不影响 canonical）
- `POST /draft/graph/nodes`
- `POST /draft/graph/edges`
- `POST /draft/graph/aliases`
- `GET /draft/graph/nodes`
- `DELETE /draft/graph/nodes/{id}`
- `POST /draft/timeline/events`
- `POST /draft/timeline/constraints`
- `POST /draft/timeline/narrations`
- `DELETE /draft/timeline/events/{id}`
- `POST /draft/memory/upsert`（建议章节归属 chapter_id）
- `POST /draft/state/assertions`
- `GET /draft/state/assertions`
- `DELETE /draft/state/assertions/{id}`
- `POST /draft/recycle/delete`
- `POST /draft/recycle/restore`
- draft 记录可被编辑、删除、审批，不影响 canonical

### 4) Proposals（提案 / 两阶段）
- `POST /graph/merge/propose`
- `GET /graph/merge_proposals`
- `POST /graph/resolve`（消歧：写入 resolution_run / suggestions，不改 canonical）

### 5) Global Apply（全局写回，独立 mutation_set）
- `POST /graph/merge/apply`（mutation_set.kind='global'；默认不在章节 finalize 内执行）

### 6) Finalize（唯一 story-canonical 真相入口）
- `POST /chapters/{id}/finalize/preview`
  - 生成 writeback_plan（不写入）
  - 返回 `writeback_plan_hash` + `preview_mutations`
- `POST /chapters/{id}/finalize/apply`
  - Request: `{ run_id, expected_lock_version, writeback_plan_hash }` + `Idempotency-Key`
  - 其中 `writeback_plan_hash` 必须等于 preview 返回的 `writeback_plan.writeback_plan_hash`
  - 行为：core.db 单事务写入 story-canonical + mutation_set + outbox
  - Response: `{ mutation_set_id, chapter_version_id, lock_version }`

### 7) Validation / Planning（只读 + 预检）
- `POST /timeline/validate`（可读 canonical；可选携带 draft 预检）
- `POST /traversal/plan`（只读 canonical + configs）
- `GET /traversal/profiles`
- `GET /traversal/profiles/{id}`

### 8) Runs / Runner / Human-in-loop
- `POST /swarm/run`
- `GET /runs/{id}`
- `GET /runs/{id}/steps`
- `GET /runs/{id}/steps/{step_id}`
- `POST /runs/{id}/pause`
- `POST /runs/{id}/resume`
- `POST /runs/{id}/cancel`
- `POST /runs/{id}/steps/{step_id}/approve`
- `POST /runs/{id}/steps/{step_id}/override`

### 9) Rollback
- `GET /mutationsets`
- `GET /mutationsets/{id}`
- `POST /mutationsets/{id}/rollback`（默认章节闭包；跨章需 force）
- `GET /mutationsets/{id}/conflict-report`

### 10) SSE（建议 M1+）
- `GET /runs/{id}/events`（text/event-stream）
  - step_started / step_completed / approval_needed / budget_warning / run_completed / run_failed

### 11) Chat
- `POST /chat/query`（支持 `session_id` + `history_turns` + `at_chapter_id`）
- `GET /chat/sessions`
- `GET /chat/sessions/{id}`
- `DELETE /chat/sessions/{id}`

### 12) Bootstrap（导入/抽取/骨架）
- `POST /bootstrap/import`
- `POST /bootstrap/extract`
- `POST /bootstrap/skeleton`
- `GET /bootstrap/status`
- `GET /bootstrap/jobs`
- `GET /bootstrap/jobs/{id}`
- `GET /graph/extraction/suggestions`
- `POST /graph/extraction/suggestions/{id}/approve`
- `POST /graph/extraction/suggestions/{id}/reject`

### 13) Onboarding
- `GET /onboarding/checklist`
- `POST /onboarding/item/{item_id}/confirm`

### 14) Config Management
- `GET /configs/prompts`
- `GET /configs/prompts/{id}`
- `POST /configs/prompts`
- `DELETE /configs/prompts/{id}`
- `GET /configs/swarm-profiles`
- `GET /configs/swarm-profiles/{id}`
- `POST /configs/swarm-profiles`
- `DELETE /configs/swarm-profiles/{id}`
- `GET /configs/traversal-profiles`
- `GET /configs/traversal-profiles/{id}`
- `POST /configs/traversal-profiles`
- `DELETE /configs/traversal-profiles/{id}`
- `GET /configs/style-guides`
- `GET /configs/style-guides/{id}`
- `POST /configs/style-guides`
- `DELETE /configs/style-guides/{id}`

### 15) Audit / Observability（建议 M1+）
- `GET /audit/llm-calls`
- `GET /audit/llm-calls/{id}`
- `GET /audit/usage`
- `POST /audit/export`
- `POST /audit/archive`


## C3 分页/过滤约定
- Cursor-based：`limit`（默认 50）+ `after=<ulid>`
- 响应 envelope：
```json
{ "items": [...], "next_cursor": "...", "has_more": true, "total_estimate": 1234 }
```

## C4 幂等语义（v1.4）
- 同 endpoint+key+request_hash：
  - succeeded：返回缓存（按 idempotency_keys.http_status + response_json）
  - processing 且 lease 未过期：返回 202（可带 retry_after_seconds）
  - processing 且 lease 过期：允许接管（CAS 更新 lease_owner/lease_until）
- 同 endpoint+key 但 request_hash 不同：409 `E101_IDEMPOTENCY_CONFLICT`

## C5 统一错误响应
见 `docs/spec/06-schemas.md` 的 ErrorResponse 与 `docs/ERROR_CODES.md`。
