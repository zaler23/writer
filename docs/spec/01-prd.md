# 01 — 产品需求（PRD）

## 一句话定义
构建一个本地单人中国网文长篇创作系统：通过多 LLM API 组成蜂群协作，以**线索图谱（明线/暗线）+ 遍历引擎**驱动章节计划，结合**向量记忆分段 + 图谱逻辑检索**保持一致性；支持**动态设定演化**与**非线性叙事**；所有能力 API 暴露；所有世界真相写回可撤回与回滚；配套强预算与审计以防成本与死循环失控。

## 背景与核心问题
1. 长篇写作事实易遗忘与冲突（战力、时间线、动机、人设漂移）。
2. 明暗线/伏笔投放与回收节奏难控，容易线断。
3. 单模型产出逻辑漏洞难以稳定发现。
4. 非线性叙事需要结构化表达与校验。
5. 上下文窗口有限（100k–150k 有效区间），需强预算与信息编排；多智能体易死循环与 token 失控。
6. 图谱自动抽取会产生实体歧义与脏图，需要半自动与预算约束、局部更新与延迟全局校验。

## 用户画像与场景
- 用户：单人作者（本地创作）
- 场景：
  - 新书：Plan → 建骨架图谱 → 写第一章
  - 旧书续写：导入章节 → Bootstrap 抽取 → 确认骨架 → 继续写
  - 连载：每章闭环（Plan→Retrieve→Draft→Review→Revise→Validate→Finalize）
  - 写作中问答：查设定/状态/时间线/关系
  - 撤回：回滚某章节 finalize 写回影响

## 目标（Goals）
1. 章节闭环流水线可用
2. 图谱为核心事实库（Thread 统一明暗线）
3. 动态设定可建模（版本化 + 状态断言 + truth_mode）
4. 非线性时间轴（故事层 vs 叙事层）+ validate
5. 混合检索与强预算 ContextPack
6. 实体消歧与脏图治理
7. 冷启动（导入/抽取/骨架确认）
8. 人在回路（审批/覆盖/暂停点）
9. 审计可追溯与冷热分层
10. 模块化与可替换实现（API-first）

## 非目标（Non-Goals）
- Rubric 达标门禁（打分合格才 finalize）
- 平台合规/敏感词过滤/发布系统
- 多人协作与云同步（可后续扩展）

## 核心概念（Domain）
### 图谱（Graph）
- 节点：Character / Item / Rule / Thread / Clue / Event / Reveal / Location / Faction / Goal …
- 边：causes / foreshadows / advances / reveals / involves / contradicts / supports / blocks …
- Thread 统一明暗线：
  - `visibility = explicit|implicit`
  - `status = open|progressing|parked|closed`

### 动态设定（Dynamic Settings）
- Node Versioning：追加版本，current_version 指向最新
- State Assertions：在范围内成立的状态事实（境界/装备/位置/关系/情绪）
- Truth Mode：asserted（确定事实）/ rumored（传闻）/ mislead（误导）/ retconned（追溯修正）— 详见 CONVENTIONS.md

### 非线性时间轴（Two-time Model）
- Narrative（叙事层）：章节/场景呈现顺序
- Story（故事层）：事件实际发生顺序（绝对时间或偏序约束）
- 同一 story_event 可被多次 narrate（不同章节/POV/可靠度/插叙/倒叙）

### 撤回与回收站（Undo / Recycle）
- 所有删除默认软删除
- Mutation Set：记录 finalize 或批量操作的 insert/update/soft-delete/merge/redirect，可逆序回滚
- v1.4：默认只支持章节闭包 rollback；跨章节 rollback 必须人工确认并输出 conflict_report

### 混合检索与 ContextPack（Budgeted）
- Vector：语义相似、风格氛围、互动史
- Graph：结构化逻辑（因果/关系/状态/时间线）
- ContextPack 强预算 + 分块上限 + 位置策略（对抗 Lost-in-the-middle）

### 实体消歧（Entity Resolution）
- alias 一等公民
- 写入前强制 resolve（候选召回 + 打分阈值）
- 定期净化任务生成 merge proposals；合并可回滚

### 冷启动（Bootstrap）
- 导入 txt → 分章
- 批量抽取 suggestions → 人审确认
- 骨架生成 + onboarding checklist
