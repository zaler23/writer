# F04 — Memory（Hybrid Retrieval）

## 职责
- chunk 分段、embedding、检索会话、ContextPack 记录、预算裁剪
- v1.4：draft_memory_chunks 作为草稿区写入

## 表
- memory_chunks（canonical）
- embeddings / vec_embeddings（择一）
- retrieval_sessions
- context_pack_items
- draft_memory_chunks（v1.4）

## API
- GET /memory/search（只读 canonical）
- POST /draft/memory/upsert（写 draft，建议章节归属 chapter_id）

## 算法
- RRF 融合 + 可解释打分明细落库
- XML 块序 + end-anchoring + budget profiles

## 不变量
- INV-014：ContextPack 可复现

## 测试
- budget trimmer 顺序正确
- plan/style 尾部永保留
