# F08 — Traversal

## 职责
- 从图谱状态 + profile 生成 ChapterPlan（推进/投放/回收 + 检索权重）
- 线索推进（foreshadow/payoff）、张力曲线、POV 轮转

## 表
- traversal_profiles
- chapters.plan_json（可缓存 plan）

## API
- POST /traversal/plan（生成章节计划）
  - 输入：chapter_id, traversal_profile_id（可选）
  - 输出：ChapterPlan（见 06-schemas.md）
- GET /traversal/profiles（获取 traversal profile 列表）
- GET /traversal/profiles/{id}（获取 traversal profile 详情）

## 关键策略
- cold_start_plan：图谱为空也输出计划（基于 premise/outline/style）
- early_stage_plan：节点数低放松回收约束
- 最小规则集（见 04-runtime.md B5）：
  - 每章至少推进 1 条主线 Thread
  - 每章至少 1 个钩子
  - 每 3 章至少回收 1 个历史伏笔（早期阶段放松）

## 不变量
- 只读 canonical + configs，不写入任何表

## 测试
- cold_start_plan golden cases
- 回收约束校验
