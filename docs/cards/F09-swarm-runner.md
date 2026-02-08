# F09 — Swarm Workflow / Runner

## 职责
- plan→retrieve→draft→review→revise→validate→finalize
- 预算熔断、人审、暂停/恢复
- v1.4：显式状态机 + guard

## 表
- runs / run_steps（core）
- llm_calls（建议 audit）
- outbox_events（core）

## API
- POST /swarm/run（启动 swarm 运行，需 Idempotency-Key）
- GET /runs/{id}（获取运行状态）
- GET /runs/{id}/steps（获取运行步骤列表）
- GET /runs/{id}/steps/{step_id}（获取步骤详情）
- POST /runs/{id}/pause（暂停运行）
- POST /runs/{id}/resume（恢复运行）
- POST /runs/{id}/cancel（取消运行）
- POST /runs/{id}/steps/{step_id}/approve（批准步骤）
- POST /runs/{id}/steps/{step_id}/override（覆盖步骤输出）
- GET /runs/{id}/events（SSE 事件流，M1+）

## 不变量
- INV-001：非 finalize 不得写 canonical
- INV-011/012：预算与修订轮次上限

## 测试
- 状态转移表覆盖
- 超预算降级
- pause/resume
