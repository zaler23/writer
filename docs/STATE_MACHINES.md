# 状态机定义（Runner + Idempotency）

## Run States
```mermaid
stateDiagram-v2
  [*] --> created : POST /swarm/run
  created --> running : runner.start()
  running --> paused : pause / budget_alert
  running --> completed : all steps done
  running --> failed : unrecoverable error
  paused --> running : resume
  paused --> cancelled : cancel
  failed --> [*]
  completed --> [*]
  cancelled --> [*]
```

合法转移（摘要）：
- created→running
- running→paused|completed|failed
- paused→running|cancelled

## Step States
```mermaid
stateDiagram-v2
  [*] --> pending
  pending --> running
  running --> completed
  running --> failed
  running --> pending_approval : requires_approval
  pending_approval --> approved
  pending_approval --> rejected
  approved --> completed
  rejected --> pending : override & retry
  rejected --> skipped
  failed --> pending : retry (budget allows)
  failed --> skipped
```

## Idempotency States（v1.4 租约）
```mermaid
stateDiagram-v2
  [*] --> processing
  processing --> succeeded : execute ok
  processing --> failed : execute error
  processing --> processing : lease takeover (CAS) 
  succeeded --> [*]
  failed --> [*]
```

规则：
- 同 key 同 hash：succeeded 重放返回；processing 202；lease 过期可接管
- 同 key 异 hash：409（E101_IDEMPOTENCY_CONFLICT）

## Chapter States
```mermaid
stateDiagram-v2
  [*] --> planned : POST /chapters
  planned --> drafting : run started
  drafting --> reviewing : draft completed
  reviewing --> revising : review has issues
  revising --> reviewing : revision done
  reviewing --> validating : review passed
  validating --> finalizing : validate passed
  validating --> reviewing : validate failed (soft)
  finalizing --> finalized : finalize.apply success
  finalized --> needs_review : rollback / conflict
  needs_review --> drafting : re-run
```

合法转移（摘要）：
- planned→drafting
- drafting→reviewing
- reviewing→revising|validating
- revising→reviewing
- validating→finalizing|reviewing
- finalizing→finalized
- finalized→needs_review（仅回滚/冲突时）
- needs_review→drafting

## Draft/Proposal States
```mermaid
stateDiagram-v2
  [*] --> draft : create
  draft --> approved : approve
  draft --> rejected : reject
  approved --> applied : finalize.apply
  rejected --> [*]
  applied --> [*]
```
