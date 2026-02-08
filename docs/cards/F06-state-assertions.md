# F06 — State Assertions（Dynamic Settings）

## 职责
- 状态断言（truth_mode + anchor_mode + 有效期）
- snapshot 合成（chapter_based 优先）
- truth_mode 枚举：asserted / rumored / mislead / retconned（见 CONVENTIONS.md）

## 表
- state_assertions（canonical，anchor_mode 默认 chapter_based）
- draft_state_assertions（v1.4）
- （可选）state_assertion_kv / generated columns（热字段，见 HOT_FIELDS.md）

## API
### Canonical（只读）
- GET /state/assertions（获取断言列表，支持按 subject/predicate 过滤）
- GET /state/assertions/{id}（获取断言详情）
- GET /graph/snapshot（获取指定章节的状态快照，含有效断言集合与冲突列表）

### Draft（可写草稿区）
- POST /draft/state/assertions（创建/更新草稿断言）
- GET /draft/state/assertions（获取草稿断言列表）
- DELETE /draft/state/assertions/{id}（删除草稿断言）

## 不变量
- INV-001：canonical 只能 finalize 写
- anchor_mode 默认 chapter_based（v1.4）

## 测试
- 有效期过滤
- 冲突聚合（同 subject+predicate 多值）
