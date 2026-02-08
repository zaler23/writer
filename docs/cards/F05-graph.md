# F05 — Graph（Canonical + Draft）

## 职责
- canonical：nodes/edges/versions/aliases 只读查询（默认 follow redirect）
- draft：/draft/graph/* 编辑式写入
- resolve：写入前消歧；merge：proposal 两阶段

## 表
- graph_nodes / graph_node_versions / graph_edges / node_aliases
- entity_resolution_runs
- merge_proposals
- draft_graph_nodes / draft_graph_edges / draft_node_aliases（v1.4）

## API
### Canonical（只读）
- GET /graph/search（搜索节点/边，默认 follow redirect）
- GET /graph/nodes/{id}（获取节点详情，follow redirect）
- GET /graph/nodes/{id}/versions（获取节点版本历史）
- GET /graph/nodes/{id}/edges（获取节点关联边）
- GET /graph/snapshot（获取指定章节的图谱快照）

### Draft（可写草稿区）
- POST /draft/graph/nodes（创建/更新草稿节点）
- POST /draft/graph/edges（创建/更新草稿边）
- POST /draft/graph/aliases（创建/更新草稿别名）
- GET /draft/graph/nodes（获取草稿节点列表）
- DELETE /draft/graph/nodes/{id}（删除草稿节点）

### Resolve & Merge
- POST /graph/resolve（实体消歧，返回候选与决策）
- POST /graph/merge/propose（创建合并提案）
- GET /graph/merge_proposals（获取合并提案列表）
- POST /graph/merge/apply（执行合并，全局操作，需 Idempotency-Key）

## 不变量
- INV-004：canonical follow redirect
- INV-010A：redirect 防环 + 禁止自指（DB 级护栏）

## 测试
- redirect follow
- redirect cycle trigger
- resolve golden cases
