# ADR-003 Vector store choice

## 状态
已采纳（v1.0），M2+ 待评估

## 背景
需要选择向量存储方案，支持语义检索。考虑因素：本地部署、零依赖、性能、迁移路径。

## 决策（M0–M1）
优先 sqlite-vec（vec0 虚拟表）作为本地零依赖向量检索。

## 备选方案
1. **Chroma**：功能丰富，但需要额外进程
2. **LanceDB**：性能好，但生态较新
3. **Qdrant**：生产级，但需要服务部署
4. **pgvector**：PostgreSQL 扩展，迁移 Postgres 时使用
5. **FAISS**：高性能，但需要额外依赖

## 拒绝原因（M0–M1）
- Chroma/Qdrant：需要额外进程，不符合"零依赖"目标
- LanceDB：生态较新，稳定性待验证
- pgvector：需要 PostgreSQL
- FAISS：需要额外依赖，部署复杂

## 后果
- 优：小规模向量性能足够、零依赖、单文件
- 负：大规模需评估索引能力与过滤能力

## 迁移路径
- M2+ 评估 Chroma / LanceDB
- 迁移 Postgres 时切 pgvector

## DDL
见 07-data-model.md v1.4 补丁第 12 节
