# 09 — Review Notes（Verbatim Appendix A）

> 本文件原样保留讨论记录，作为 v1.4 修订依据与溯源材料（不用于实现直接引用）。

## 一、规范本身的结构性问题（Spec-level Issues）

### 1.1 ⚠️ 文档体量与 AI 上下文窗口的矛盾

**问题**：本规范约 **25,000+ tokens**（中文计约 35k+），单次喂给 AI 编码助手已经接近"有效注意力"的边界。规范自己提到的 Module Cards（F 节）是正确的方向，但 **Cards 仍然内嵌在总文档中，没有独立成文件**。

**建议**：
- 总规范拆成 `spec/00-meta.md`、`spec/01-prd.md`、`spec/02-data-model.md`、`spec/03-runtime.md`、`spec/04-api.md`、`spec/05-milestones.md`
- 每个 Module Card 独立为 `docs/cards/F01-projects.md` ~ `docs/cards/F15-outbox.md`
- AI 编码时只喂 **当前模块卡片 + 总 DDL + 当前里程碑要求**，不超 8k tokens

### 1.2 ⚠️ M0 范围仍然偏大

**问题**：M0 包含 `mutation_sets + mutations + idempotency_keys` + finalize 两阶段 + 可回滚。对于"第一行代码到跑通"来说，这是 **过度设计的启动成本**。

**建议**：拆出 M0a 和 M0b：
- **M0a**（真骨架）：projects + chapters + chapter_text_versions + runs + run_steps。单模型 draft → 直接写 final version。无 mutation_set、无 idempotency。目标：**3 天内可 `POST /swarm/run` 跑出一章文本**。
- **M0b**（防失控闸门）：加入 mutation_sets/mutations/idempotency_keys；finalize 两阶段；回滚测试。

### 1.3 ⚠️ "硬规则"散落在多处

**问题**：A7.3 定义了 10 条硬规则，但 B/C/D/I 节又各自重申或扩展了部分规则。Vibe coding 时 AI 无法在多处重复引用中保持一致。

**建议**：抽出独立文件 `docs/INVARIANTS.md`，所有硬规则统一编号（INV-001 ~ INV-0xx），其他地方只引用编号。

### 1.4 ⚠️ API 端点 vs 实际数据流缺少时序图

**问题**：C2 给了端点总表，但没有给出**一次完整章节写作的调用时序**。Vibe coding 实现时容易产生"API 都有了但串不起来"的问题。

**建议**：补充至少 2 张 Mermaid sequence diagram：
1. 新章节写作完整调用流（happy path）
2. 回滚一章的调用流

---

## 二、数据模型问题（DDL / Schema Issues）

### 2.1 🔴 TEXT 类型的 ID 缺少生成策略约定

**问题**：所有表 `id TEXT PRIMARY KEY` 没有约定使用 UUID v7（时间有序）还是 ULID 还是自定义前缀 ID。这影响：
- 索引性能（有序 vs 随机）
- 调试可读性
- 跨表关联时的可识别性

**建议**：
```
约定：所有 ID 使用 ULID（26字符，时间有序，URL安全）
可选前缀：proj_xxxx、ch_xxxx、node_xxxx（提升调试体验）
```
推荐库：`python-ulid` 或 `ulid-py`

### 2.2 🔴 时间字段用 TEXT 而非 INTEGER/REAL

**问题**：`created_at TEXT NOT NULL` 在 SQLite 中无法高效排序和范围查询（尽管 SQLite 对 ISO8601 TEXT 有内建函数支持，但索引效率低于数值类型）。

**建议**：
- 统一使用 **ISO8601 TEXT**（可读性好，SQLite 比较函数可用），但必须约定格式为 `YYYY-MM-DDTHH:MM:SS.ffffffZ`（UTC，微秒精度，Z 结尾）
- 或使用 **INTEGER (Unix timestamp milliseconds)**，调试时用工具转换
- 至少在 `docs/CONVENTIONS.md` 中写死格式约定

### 2.3 🟡 外键不完整 / 部分 FK 缺失

**问题举例**：
- `chapter_graph_links.node_id` 没有 FK → `graph_nodes(id)`
- `narrations.chapter_id` FK → `chapters(id)` 缺失
- `narrations.segment_id` FK → `chapter_segments(id)` 缺失
- `state_assertions` 的 `story_valid_from_event_id` / `story_valid_to_event_id` 没有 FK → `story_events(id)`
- `state_assertions.valid_from_chapter_id` / `valid_to_chapter_id` 没有 FK → `chapters(id)`
- `llm_calls` 的 `provider_id`/`model_id` 有逻辑引用但无 FK

**建议**：补齐所有逻辑外键。SQLite 的 FK 检查需要 `PRAGMA foreign_keys = ON`（规范已提到但 DDL 未体现）。

### 2.4 🟡 `attrs_json` / `*_json` 字段过度使用

**问题**：规范自己在 I4 承认了这个问题，但 DDL 中有 **20+ 个 JSON 字段** 没有对应的投影方案。这些 JSON 在 M0-M2 阶段可能不成问题，但 M3+ 会成为查询瓶颈。

**建议**：
- 在每个 Module Card 中明确标注"哪些 JSON 字段内的 key 需要在 M1/M2/M3 投影为列或 KV"
- 至少以下字段需要早期投影：
  - `graph_node_versions.tags_json` → `node_tags(node_version_id, tag)` 关联表
  - `chapters.plan_json` → 不做投影（只读，不做过滤）
  - `runs.budget_json` → `budget_remaining_tokens INTEGER` 热字段
  - `run_steps.budget_json` → 同上

### 2.5 🟡 `embeddings` 表与 sqlite-vec 的冲突

**问题**：规范定义了 `embeddings` 表用 `vector_blob BLOB`，但 sqlite-vec 有自己的虚拟表 API（`CREATE VIRTUAL TABLE ... USING vec0(...)`），两者存储方式不兼容。

**建议**：
```sql
-- 方案A：使用 sqlite-vec 的虚拟表（推荐）
CREATE VIRTUAL TABLE vec_embeddings USING vec0(
  chunk_id TEXT PRIMARY KEY,
  embedding FLOAT[1536]  -- 维度按模型调整
);
-- metadata 关联仍走 embeddings 表（去掉 vector_blob 列）

-- 方案B：纯 BLOB 存储，手动 brute-force 或外接向量库
-- 保持现有 DDL
```
两种方案都可以，但必须在 Module Card F4 中明确选择，不能模糊。

### 2.6 🟡 缺少版本号/乐观锁字段

**问题**：规范 C1 要求 finalize 必须有 `expected_chapter_version_id` 乐观锁，但 `chapters` 表没有 `version` / `updated_at` 用于比较的标准字段。

**建议**：
```sql
ALTER TABLE chapters ADD COLUMN lock_version INTEGER NOT NULL DEFAULT 0;
-- finalize 时 WHERE lock_version = expected_version → UPDATE lock_version = lock_version + 1
```

### 2.7 🟡 软删除 `is_deleted` 缺少统一 CHECK 约束

**建议**：所有含 `is_deleted` 的表加 `CHECK(is_deleted IN (0, 1))`，防止脏数据。

---

## 三、运行策略与算法问题（Runtime Issues）

### 3.1 🔴 "轻 Runner" 未定义状态转移图

**问题**：B6.3 说"先用轻量 runner（step registry + 状态机）"，但没有定义 run 和 step 的**状态枚举和合法转移**。这是 vibe coding 最容易失控的地方。

**建议**：明确状态机：

```
Run States:
  created → running → [paused ⇆ running] → completed | failed | cancelled

Step States:
  pending → running → [pending_approval → approved/rejected] → completed | failed | skipped

合法转移矩阵：
  running → paused（人工/超时）
  paused → running（resume）
  paused → cancelled（人工放弃）
  running → failed（异常/超预算）
  pending_approval → approved → running（下一步）
  pending_approval → rejected → 回到 pending（修改后重试）或 failed
```

### 3.2 🔴 Entity Resolution 打分权重缺少校准基准

**问题**：B2.3 给出 `0.45*name + 0.25*context + 0.30*embedding`，但没有说明这些权重怎么来的、用什么数据校准、阈值 0.85/0.70 是否经过验证。

**建议**：
- 在 M2 中增加一个"消歧 golden test"任务：用 10-20 个已知消歧案例校准权重和阈值
- 权重写入 `project_settings` 使其可配置，不硬编码
- 记录 resolution_run 中的 score breakdown 以便后续调参

### 3.3 🟡 ContextPack 位置策略缺少"动态段类型适配"

**问题**：B4.2 定义了固定 8 段 XML 块序，但 B4.4 提到"segment_type 决定检索权重（action 偏 graph，emotion 偏 vector）"。两者没有对齐——不同 segment_type 是否应该调整块的预算分配？

**建议**：
```python
# 按 segment_type 的预算权重模板
BUDGET_PROFILES = {
    "action": {"state": 5000, "chunks": 8000, "persona": 2000},
    "emotion": {"state": 2000, "chunks": 12000, "persona": 4000},
    "reveal": {"state": 6000, "chunks": 6000, "persona": 2000},
    ...
}
```
写入 TraversalProfile 或 SwarmProfile 使其可配。

### 3.4 🟡 Timeline validate 的"环检测"不够（续）

**建议**：M3 阶段用两层校验：
1. **结构层**：before/after 边的 DAG 拓扑排序（检测环）— 这是 v1.3 最小实现
2. **语义层**：将 during/overlaps/equals 转化为区间约束，用简单的区间交集检查（不需要 OR-Tools）：
   - `A during B` → `A.start >= B.start AND A.end <= B.end`
   - `A overlaps B` → `A.start < B.end AND A.end > B.start`
   - 当 story_time_from/to 有值时做数值比较；无值时仅记录 soft_warning

3. **OR-Tools 升级**：仅当作者显式标注了大量复杂约束（几十条+）才有必要引入，M4 甚至更后

### 3.5 🟡 Swarm 的"多路草稿"选择策略未定义

**问题**：B6.1 允许 `draft_n ≤ 3`（并行多路草稿），但没有定义在**非人工选择**模式下如何自动选择最佳草稿。

**建议**：
```python
# 自动选择策略（当 requires_approval=false 时）
class DraftSelector:
    def select(self, drafts: list[Draft], reviews: list[Review]) -> Draft:
        # 策略1：review 得分最高
        # 策略2：review 问题数最少
        # 策略3：加权（一致性*0.4 + 风格*0.3 + 推进完成度*0.3）
        ...
```
在 SwarmProfile 的 step 配置中加 `select_strategy: "min_issues" | "weighted_score" | "human_only"`。

### 3.6 🟡 Token 计数的"估算"与"精确"双轨制缺少切换逻辑

**问题**：B4.5 要求 TokenCounter 支持两种模式，但没有定义**什么时候用精确、什么时候用估算**，以及**估算误差容忍度**。

**建议**：
```python
class TokenCounter:
    def count(self, text: str, model: str) -> TokenCount:
        if has_exact_tokenizer(model):  # OpenAI, Anthropic
            return exact_count(text, model)
        else:
            count = len(text) * self.CHAR_RATIO[language]  # 中文约 0.6~0.7
            return TokenCount(value=count, is_estimate=True, margin=0.15)

    # 预算裁剪时：estimate 模式预留 15% margin
    def budget_available(self, budget: int, used: TokenCount) -> int:
        margin = int(used.value * 0.15) if used.is_estimate else 0
        return budget - used.value - margin
```

---

## 四、API 设计问题（API Issues）

### 4.1 🔴 缺少错误响应的统一 Schema

**问题**：D 节定义了多个 Response Schema，但没有定义**错误响应格式**。Vibe coding 时每个模块各自发明错误格式是常见灾难。

**建议**：
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "ErrorResponse",
  "type": "object",
  "required": ["error_code", "message", "request_id"],
  "properties": {
    "error_code": {"type": "string", "description": "机器可读错误码，如 FINALIZE_CONFLICT / ENTITY_AMBIGUOUS / BUDGET_EXCEEDED"},
    "message": {"type": "string"},
    "request_id": {"type": "string"},
    "details": {"type": "object", "description": "结构化错误详情"},
    "retry_after_seconds": {"type": "integer", "description": "可重试时的建议等待"}
  }
}
```

错误码枚举至少覆盖：
- `IDEMPOTENCY_CONFLICT` — 相同 key 不同 payload
- `FINALIZE_VERSION_CONFLICT` — 乐观锁失败
- `ENTITY_AMBIGUOUS` — resolve 需要人审
- `BUDGET_EXCEEDED` — 预算超限
- `ROLLBACK_HAS_DEPENDENTS` — 回滚有依赖冲突
- `CHECKLIST_INCOMPLETE` — onboarding 未完成
- `CYCLE_DETECTED` — 时间线环
- `RUN_NOT_PAUSABLE` — 状态不允许暂停

### 4.2 🔴 分页/过滤缺少约定

**问题**：`GET /graph/search`、`GET /graph/merge_proposals`、`GET /runs/{id}/steps` 等列表端点没有定义分页参数。

**建议**：统一约定：
```
# Cursor-based 分页（推荐，ULID 天然有序）
GET /graph/nodes?project_id=xxx&limit=50&after=node_01JXX...

# Response envelope
{
  "items": [...],
  "next_cursor": "node_01JXX...",
  "has_more": true,
  "total_estimate": 1234  // 可选，expensive 时不返回
}
```

### 4.3 🟡 finalize 端点设计不够原子

**问题**：`POST /chapters/{id}/finalize` 需要携带 writeback_plan，但规范没有说明 writeback_plan 的 Schema、谁生成它、以及它是否作为 request body 传入。

**建议**：拆成两步：
```
# Step 1：生成 writeback_plan（预览，不写入）
POST /chapters/{id}/finalize/preview
Request: { "run_id": "...", "expected_chapter_version_id": "..." }
Response: { "writeback_plan": {...}, "preview_mutations": [...], "estimated_changes": 42 }

# Step 2：确认执行
POST /chapters/{id}/finalize/apply
Request: { 
  "run_id": "...", 
  "expected_chapter_version_id": "...",
  "writeback_plan_hash": "sha256:...",  // 防止 preview 到 apply 之间 plan 被篡改
  "idempotency_key": "..." 
}
Response: { "mutation_set_id": "...", "chapter_version_id": "...", "mutations_count": 42 }
```

### 4.4 🟡 Webhook / SSE 事件推送缺失

**问题**：长时间运行的 swarm run 没有实时进度反馈机制。轮询 `GET /runs/{id}` 体验差。

**建议**：
```
# SSE 端点
GET /runs/{id}/events  (text/event-stream)

事件类型：
- step_started: { step_id, step_type, step_no }
- step_completed: { step_id, output_summary }
- approval_needed: { step_id, step_type }
- budget_warning: { remaining_pct }
- run_completed: { mutation_set_id }
- run_failed: { error_code, message }
```

M0 不需要，M1+ 强烈建议，否则前端（即使是 CLI）体验极差。

### 4.5 🟡 Chat API 缺少会话概念

**问题**：`POST /chat/query` 是无状态的单次问答，但实际使用中作者通常会**追问**（"那他后来怎么了？""他和 XX 是什么关系？"）。

**建议**：
```json
{
  "project_id": "...",
  "session_id": "...",         // 可选，传入则带上历史
  "question": "...",
  "at_chapter": 50,
  "history_turns": 5,          // 携带最近 N 轮
  "mode": "quick"
}
```
`session_id` 对应一个轻量表或内存 LRU，存最近 N 轮 question/answer pair。

---

## 五、技术栈优化建议（基于 2025 最新生态）
（原文略：已在 v1.4 文档中吸收为 ADR 与建议实现）
