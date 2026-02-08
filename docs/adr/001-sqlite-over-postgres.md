# ADR-001 SQLite as default

## 状态
已采纳（v1.0）

## 背景
本地单人、API-first，优先低运维与可移植性。

## 决策
默认 SQLite（WAL + 单写多读 + 写串行化），提供迁移到 Postgres 的路径。

## 备选方案
1. **PostgreSQL**：功能更强大，但需要额外安装和运维
2. **DuckDB**：分析能力强，但写入场景不如 SQLite 成熟
3. **嵌入式 MySQL**：生态好，但本地部署复杂

## 拒绝原因
- PostgreSQL：对于本地单人场景过于重量级，增加用户安装门槛
- DuckDB：主要面向分析场景，事务支持不如 SQLite 成熟
- 嵌入式 MySQL：部署复杂度高，不符合"零依赖"目标

## 后果
- 优：零依赖、易分发、单文件备份
- 负：并发写受限（通过 WriteSerializer 缓解）；复杂 schema 迁移需谨慎

## 迁移路径
- M2+ 可评估迁移到 PostgreSQL
- 迁移时需要：Alembic 迁移脚本、pgvector 替代 sqlite-vec、连接池配置
