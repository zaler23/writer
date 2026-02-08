# ADR-004 Thin repository (raw SQL) over heavy ORM

## 状态
已采纳（v1.0）

## 背景
需要选择数据访问层实现方式。考虑因素：控制力、AI 生成友好度、迁移复杂度。

## 决策
M0–M1 采用 thin repo + 参数绑定 raw SQL；M2+ 视迁移需求引入 Alembic/SQLAlchemy 2.x。

## 备选方案
1. **SQLAlchemy ORM**：功能强大，但抽象层厚
2. **Peewee**：轻量 ORM，但生态较小
3. **Tortoise ORM**：异步友好，但需要额外学习成本
4. **Raw SQL + 手动映射**：最大控制力

## 拒绝原因（M0–M1）
- SQLAlchemy ORM：抽象层厚，AI 生成样板多，调试困难
- Peewee/Tortoise：生态较小，社区支持有限
- 选择 thin repo 是因为：控制力强、AI 生成样板少、便于理解和调试

## 后果
- 优：控制力强、AI 生成样板更少、便于调试
- 负：手写迁移与约束更费工

## 迁移路径
- M2+ 视需求引入 Alembic 管理迁移
- 可选引入 SQLAlchemy 2.x Core（非 ORM）简化查询构建
