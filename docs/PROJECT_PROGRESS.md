# 项目进度（Project Progress）

## 更新规则
- 每完成一个模块，立即更新本文件中的“模块看板”和“更新日志”。
- 状态仅使用：`Not Started`、`In Progress`、`Done`、`Blocked`。
- 每次更新必须包含日期（YYYY-MM-DD）和可验证产物（文件路径或测试）。

## 里程碑看板
| Milestone | Status | Notes |
|---|---|---|
| M0a 最小可运行骨架 | Done | F01/F03/F09 已完成：`POST /swarm/run` 可同步产出章节 final text |
| M0b 防失控闸门 | Not Started | finalize 幂等与回滚门禁 |
| M1 记忆与 ContextPack | Not Started | 检索与预算裁剪 |
| M2 图谱核心 | Not Started | resolve / merge 提案 |
| M3 一致性核心 | Not Started | state/timeline validate |
| M4 高级能力 | Not Started | bootstrap/chat/SSE |

## 模块看板（当前聚焦 M0b）
| Module | Scope | Status | Last Update | Evidence |
|---|---|---|---|---|
| F01 Projects & Settings | 项目与设置 API + SQLite 持久化 | Done | 2026-02-08 | `src/app/main.py`, `src/app/db.py`, `tests/test_projects_api.py` |
| F03 Chapters | 章节与文本版本（M0a 范围） | Done | 2026-02-08 | `src/app/main.py`, `src/app/schemas.py`, `src/app/db.py`, `tests/test_chapters_api.py` |
| F09 Swarm Runner | run/step 状态机与运行接口（M0a 单步 draft） | Done | 2026-02-08 | `src/app/main.py`, `src/app/db.py`, `src/app/schemas.py`, `tests/test_swarm_runner_api.py` |
| Docs Frontend | 文档站点 IA/页面/构建计划 | In Progress | 2026-02-08 | `docs/spec/11-docs-frontend.md` |

## 更新日志
- 2026-02-08: 初始化进度文档；完成 F01 首模块实现（项目 CRUD、settings 读写、分页列表、基础测试），`python -m pytest -q` 通过（3 passed）。
- 2026-02-08: 启动第一步构建（F03）；新增 chapters/segments/reviews/text-versions API 与数据表，补充 `tests/test_chapters_api.py`，`python -m pytest -q` 通过（7 passed）。finalize preview/apply 计划在 M0b 完成。
- 2026-02-08: 完成 F09（Swarm Runner M0a 最小闭环）；新增 `runs/run_steps/llm_calls` 表、`/swarm/run` 与 `/runs/*` 系列接口、step approve/override、章节 `planned -> drafting -> finalized` 状态流，补充 `tests/test_swarm_runner_api.py`；`uv run --extra dev pytest -q` 通过（11 passed）。
- 2026-02-08: 补充文档前端构建计划与 IA，记录 Docs Frontend 模块进度（`docs/spec/11-docs-frontend.md`）。
