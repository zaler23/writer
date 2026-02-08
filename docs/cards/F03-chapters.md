# F03 — Chapters

## 职责
- 章节元信息、文本版本、分段、评审报告
- finalize preview/apply 的章节锁与版本管理

## 表
- chapters（含 lock_version）
- chapter_text_versions
- chapter_segments
- chapter_reviews
- chapter_graph_links

## API
- POST /chapters（创建章节）
- GET /chapters/{id}（获取章节详情）
- PUT /chapters/{id}（更新章节计划字段）
- GET /chapters（列出章节，支持分页）
- POST /chapters/{id}/segments（创建/更新分段）
- GET /chapters/{id}/segments（获取分段列表）
- POST /chapters/{id}/finalize/preview（预览 writeback_plan）
- POST /chapters/{id}/finalize/apply（执行 finalize，需 Idempotency-Key）
- GET /chapters/{id}/reviews（获取评审报告列表）
- GET /chapters/{id}/text-versions（获取文本版本历史）

## 不变量
- INV-003/008：finalize 单事务 + 乐观锁
- INV-001：非 finalize 不得写 canonical

## 测试
- 版本号递增
- finalize 幂等（同 key 同 hash）
- 并发 finalize 冲突测试（门禁）
