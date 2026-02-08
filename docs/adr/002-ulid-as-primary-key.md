# ADR-002 ULID as primary key

## 状态
已采纳（v1.0）

## 背景
需要选择主键生成策略，考虑因素：时间有序性、索引性能、可读性、URL 安全。

## 决策
所有对象 ID 使用 ULID（可选前缀），提升索引局部性与调试可读性。

## 备选方案
1. **UUID v4**：随机，无序
2. **UUID v7**：时间有序，但较长（36字符）
3. **自增 INTEGER**：简单，但不适合分布式
4. **Snowflake ID**：时间有序，但需要 worker_id 配置

## 拒绝原因
- UUID v4：随机插入导致 B-Tree 抖动，索引效率低
- UUID v7：较长，URL 不友好
- 自增 INTEGER：不适合未来分布式扩展
- Snowflake ID：需要额外配置，对单机场景过于复杂

## 后果
- 优：有序插入减少 B-Tree 抖动、26字符 URL 安全、可读性好
- 负：需要统一生成库与测试固定化

## 实现
- 推荐库：`python-ulid` 或 `ulid-py`
- 前缀约定见 CONVENTIONS.md
