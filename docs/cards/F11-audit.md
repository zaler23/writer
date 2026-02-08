# F11 — Audit & Observability

## 职责
- LLM 调用记录、使用量与成本、冷热分层、导出归档
- v1.4：审计为派生数据，通过 outbox 可重建（见 ADR-008）

## 表
- llm_calls / llm_call_blobs（建议 audit.db）
- outbox_events（core）

## API
- GET /audit/llm-calls（获取 LLM 调用记录列表）
- GET /audit/llm-calls/{id}（获取 LLM 调用详情）
- GET /audit/usage（获取使用量统计）
- POST /audit/export（导出审计数据，JSONL.gz 格式）
- POST /audit/archive（归档冷数据）

## 约束
- 大字段外置（blob store，见 CONVENTIONS.md）
- outbox 消费幂等（INV-015）
- 每次 LLM 调用必须记录（INV-013）

## 测试
- outbox 幂等消费
- 热冷迁移策略
- 使用量统计准确性
