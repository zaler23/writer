# 04 — 运行策略与算法（Runtime）

## B1 预算与降级（硬规则）
预算字段适用于 run/run_step/retrieval_session/extraction_job：
- max_tokens_total / max_tokens_step
- max_cost_total
- max_revision_rounds
- step_timeout_seconds
- budget_alert_threshold
- v1.4 增补：max_inflight_calls / rate_limit_bucket / retry_budget

降级策略（触发预算/超时/限流）：
- 抽取：auto → semi(suggestions) → manual(todo)
- 写作：减少 topK、裁剪 exemplars、减少并行路数、降低审议深度
- Swarm：停止后续 revise，进入 human_override 或直接 finalize（可选）

## B2 实体消歧（Entity Resolution）
### 归一化
- 全角转半角、去空白
- 中文数字与阿拉伯数字统一（可选）
- strict_key（精确匹配）与 loose_key（召回）

### 候选召回
1) strict_key 精确匹配 node_aliases.normalized_text
2) loose_key 模糊匹配（like/编辑距离）
3) 向量匹配（name+summary embedding，可选）
4) 上下文约束：同章共现角色、关系边、POV

### 打分与阈值（可配置）
- final = 0.45*name + 0.25*context + 0.30*embedding
- >=0.85：强匹配（建议 alias_append 或 merge_propose，需确认）
- 0.70~0.85：疑似（强制人审）
- <0.70：允许新建（仍记录 resolution_run）
- v1.4：权重与阈值必须可配置（project_settings），并提供 golden cases 校准任务

## B3 图谱构建与增量更新
- 模式：Manual / Semi-auto（默认）/ Auto-lite
- finalize 后局部更新：本章涉及节点及 k-hop 邻域（k=1~2）+ 本章事件/叙事/断言
- 全局校验：每卷末/每 20 章/手动；输出 dangling edges、孤儿伏笔、未揭示暗线、冲突断言、重复实体候选

## B4 混合检索与 ContextPack（强预算 + 注意力对策）
### 两路检索
- vector_search：语义/风格/互动史
- graph_search：状态/因果/关系/时间线
- 融合：RRF（并记录可解释打分明细）

### 强制块序与 XML 标签（位置策略）
1. <PreviousChapterRecap>
2. <ImmediateContinuity>
3. <Persona>
4. <StateSnapshot>
5. <RelevantFacts>
6. <RetrievedChunks>
7. <ChapterPlan>（尾部锚定）
8. <StyleGuide>（尾部锚定）

### 动态段类型预算模板（v1.4）
按 segment_type 选择预算分配（可配置）：
- action: state↑ chunks↓
- emotion: persona↑ chunks↑
- reveal: state↑ facts↑
实现：BUDGET_PROFILES 映射 + fallbacks

### Token 计数（双轨）
- 有精确 tokenizer：精确计数
- 无 tokenizer：估算 + margin（建议 15%）
- 裁剪时预留 margin，避免超窗

## B5 Traversal 引擎
模板：
1) 线索推进（foreshadow/payoff）
2) 张力曲线
3) POV 轮转

最小规则集：
- 每章至少推进 1 条主线 Thread
- 每章至少 1 个钩子
- 每 3 章至少回收 1 个历史伏笔（早期阶段放松）
- 冷启动：graph/thread 为空输出 cold_start_plan（基于 premise/outline/style）

## B6 Swarm 编排（防死循环）
- max_revision_rounds=3
- step_timeout_seconds=300
- 并行：draft_n<=3, review_n<=2
- 人工干预点：plan_review/draft_select/assertion_confirm/任意 pause/resume
- v1.4：draft 多路自动选择策略可配置（min_issues / weighted_score / human_only）

## B7 Timeline validate（最小实现 + 增强）
- 结构层：before/after DAG 拓扑排序检测环（阻断）
- 语义层：during/overlaps/equals 有数值区间时做交集检查，否则 soft_warning
- 输出：cycles/hard_conflicts/soft_warnings/is_blocking

## B8 动态设定快照（Graph Snapshot）
- v1.4：默认 chapter_based（确定性强）
- event_based：增强开关，质量阈值达标才启用
- snapshot 输出 canonical nodes + 有效断言集合 + 冲突列表（同 subject+predicate 多值）

## B9 回收站与回滚
- 软删除不级联；关联对象标记 orphaned
- rollback：
  1) dependents 扫描 → conflict_report
  2) 无依赖：章节闭包回滚（默认）
  3) 有依赖：409 需 force_rollback（标记 needs_review）

## B10 Bootstrap
- 导入分章规则：第[一二三四五六七八九十0-9]+章 / 分隔线 / 字数阈值
- 批量抽取输出 suggestions（预算约束）
- 骨架生成：核心角色/地点/势力/thread/rules + checklist

## B11 Chat-with-Graph
- 目标：问答（不生成正文）+ sources
- 策略：snapshot → graph_search → vector_search
- 预算：5k–15k

## B12 Style
- style_guide：短、可执行
- exemplars：少量（预算不足先裁）
- anti_patterns：审查提示（不门禁）

## B13 审计冷热分层与归档
- core：只留 hash/path/usage 元信息 + outbox
- audit：热字段 + blobs；冷存仅 hash + 元信息
- 导出：JSONL.gz
