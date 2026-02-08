# F02 — Configs（Prompts / Profiles / Styles）

## 职责
- 配置即代码：prompts / swarm_profiles / traversal_profiles / style_guides
- 版本化、入库校验、运行时校验
- JSON Schema 定义见 06-schemas.md

## 表
- prompt_templates
- swarm_profiles
- traversal_profiles
- style_guides

## API
### Prompt Templates
- GET /configs/prompts（获取 prompt 模板列表）
- GET /configs/prompts/{id}（获取 prompt 模板详情）
- POST /configs/prompts（创建/更新 prompt 模板）
- DELETE /configs/prompts/{id}（删除 prompt 模板）

### Swarm Profiles
- GET /configs/swarm-profiles（获取 swarm profile 列表）
- GET /configs/swarm-profiles/{id}（获取 swarm profile 详情）
- POST /configs/swarm-profiles（创建/更新 swarm profile）
- DELETE /configs/swarm-profiles/{id}（删除 swarm profile）

### Traversal Profiles
- GET /configs/traversal-profiles（获取 traversal profile 列表）
- GET /configs/traversal-profiles/{id}（获取 traversal profile 详情）
- POST /configs/traversal-profiles（创建/更新 traversal profile）
- DELETE /configs/traversal-profiles/{id}（删除 traversal profile）

### Style Guides
- GET /configs/style-guides（获取 style guide 列表）
- GET /configs/style-guides/{id}（获取 style guide 详情）
- POST /configs/style-guides（创建/更新 style guide）
- DELETE /configs/style-guides/{id}（删除 style guide）

## 不变量
- INV-005：入库前 JSON Schema 校验
- 配置同步策略：configs/ 文件 → DB（source=file），API 修改标记 source=api（不回写文件）

## 测试
- 非法 schema 拒绝写入（E207_SCHEMA_INVALID）
- 运行时加载校验失败阻断 run
