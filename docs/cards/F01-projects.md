# F01 — Projects & Settings

## 职责
- 项目元信息、全局配置（预算、默认 profiles、开关、消歧权重）

## 表
- projects
- project_settings

## API
- POST /projects（创建项目）
- GET /projects/{id}（获取项目详情）
- PUT /projects/{id}（更新项目）
- GET /projects（列出项目，支持分页）
- GET /projects/{id}/settings（获取项目设置）
- PUT /projects/{id}/settings（更新项目设置）

## 关键不变量
- INV-005（settings_json schema 校验）
- INV-016（所有查询必须过滤 project_id）

## 测试
- 创建/读取幂等
- settings schema 校验失败拒绝写入
