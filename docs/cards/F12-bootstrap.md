# F12 — Bootstrap

## 职责
- import、extract suggestions、skeleton、checklist

## 表
- bootstrap_jobs
- graph_extraction_jobs / graph_extraction_suggestions
- onboarding_checklist_items

## API
- POST /bootstrap/import（导入 txt 文件，分章）
- POST /bootstrap/extract（批量抽取实体/关系，输出 suggestions）
- POST /bootstrap/skeleton（生成骨架图谱）
- GET /bootstrap/status（获取 bootstrap job 状态）
- GET /bootstrap/jobs（获取 bootstrap job 列表）
- GET /bootstrap/jobs/{id}（获取 bootstrap job 详情）
- GET /onboarding/checklist（获取 onboarding 检查清单）
- POST /onboarding/item/{item_id}/confirm（确认 onboarding 项目）
- GET /graph/extraction/suggestions（获取抽取建议列表）
- POST /graph/extraction/suggestions/{id}/approve（批准抽取建议）
- POST /graph/extraction/suggestions/{id}/reject（拒绝抽取建议）

## 测试
- 分章规则 golden
- budget 降级
