# F07 — Timeline（Story vs Narrative）

## 职责
- 事件、约束、叙事映射、validate
- v1.4：timeline 写入走 draft，canonical 走 finalize

## 表
- story_timelines / story_events / event_order_constraints / narrations / timeline_validation_reports
- draft_story_events / draft_event_order_constraints / draft_narrations（v1.4）

## API
### Canonical（只读）
- GET /timeline/events（获取事件列表）
- GET /timeline/events/{id}（获取事件详情）
- GET /timeline/constraints（获取约束列表）
- GET /timeline/narrations（获取叙事映射列表）

### Draft（可写草稿区）
- POST /draft/timeline/events（创建/更新草稿事件）
- POST /draft/timeline/constraints（创建/更新草稿约束）
- POST /draft/timeline/narrations（创建/更新草稿叙事映射）
- DELETE /draft/timeline/events/{id}（删除草稿事件）

### Validation
- POST /timeline/validate（校验时间线，可读 canonical + 可选带 draft 预检）

## 算法
- before/after DAG 环检测（阻断）
- 区间关系软校验（有数值时）

## 测试
- cycle 检测输出一致
- hard_conflicts 阻断
