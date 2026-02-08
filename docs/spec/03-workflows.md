# 03 — 工作流与调用时序

## 新书 Onboarding（简）
1. `POST /projects`
2. `GET /onboarding/checklist`
3. 填写并 `POST /onboarding/item/{item_id}/confirm`
4. 可选：`POST /bootstrap/skeleton` 生成骨架（写入 draft/proposal）
5. 进入章节闭环

## 旧书续写 Bootstrap（简）
1. `POST /bootstrap/import`（导入 txt 分章 → chapters + imported text_versions）
2. `POST /bootstrap/extract`（输出 suggestions）
3. 人工确认核心骨架（写入 draft/proposal）
4. 继续章节闭环

## 章节闭环（v1.4：draft → finalize）
- Plan → Retrieve → Draft → Review → Revise → Validate → Finalize
- 世界真相只在 finalize.apply 写入；其他步骤只写 runs/steps/audit/draft

### Happy Path — Mermaid 时序图
```mermaid
sequenceDiagram
  autonumber
  participant U as User/CLI
  participant API as FastAPI
  participant R as Runner
  participant D as DraftStore
  participant C as CoreDB(canonical)
  participant O as Outbox
  participant A as Audit/Blob

  U->>API: POST /swarm/run (chapter_id)
  API->>C: create run + steps (light)
  API->>R: start(run_id)
  R->>API: execute step: plan/retrieve/draft/review/revise/validate
  R->>A: write llm_calls + blobs (best-effort)
  R->>D: POST /draft/* (draft mutations)
  R->>API: POST /chapters/{id}/finalize/preview
  API->>C: build writeback_plan (no write)
  U->>API: POST /chapters/{id}/finalize/apply (Idempotency-Key + expected_lock_version + writeback_plan_hash)
  API->>C: BEGIN; apply canonical mutations; write mutation_set+mutations; write outbox; COMMIT
  API-->>U: 200 {mutation_set_id, chapter_version_id}
  O-->>A: async consume(outbox)补写审计/索引
```

### Rollback — Mermaid 时序图（章节闭包）
```mermaid
sequenceDiagram
  autonumber
  participant U as User/CLI
  participant API as FastAPI
  participant C as CoreDB
  participant O as Outbox
  participant A as Audit/Blob

  U->>API: POST /mutationsets/{id}/rollback (force=false)
  API->>C: compute dependents + conflict_report
  alt no dependents
    API->>C: BEGIN; apply inverse mutations; mark chapter needs_review; write outbox; COMMIT
    API-->>U: 200 {rolled_back:true}
  else has dependents
    API-->>U: 409 E205_ROLLBACK_DEPENDENTS + conflict_report
  end
  O-->>A: consume(outbox)补写审计/索引
```

## Runner 状态机
完整定义见 `docs/STATE_MACHINES.md`。
