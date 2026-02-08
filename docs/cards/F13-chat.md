# F13 — Chat-with-Graph

## 职责
- 问答（不生成正文）+ sources
- 支持 session_id + history_turns（v1.4 建议）

## 表
- 可复用 retrieval_sessions/context_pack_items
- chat_sessions / chat_turns（用于持久化历史）

### DDL（v1.4）

```sql
-- Chat 会话表
CREATE TABLE chat_sessions (
  id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  title TEXT,
  mode TEXT NOT NULL DEFAULT 'qa',  -- 'qa' | 'explore'
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY(project_id) REFERENCES projects(id)
);

-- Chat 对话轮次
CREATE TABLE chat_turns (
  id TEXT PRIMARY KEY,
  session_id TEXT NOT NULL,
  turn_no INTEGER NOT NULL,
  role TEXT NOT NULL,  -- 'user' | 'assistant'
  content_text TEXT NOT NULL,
  meta_json TEXT,  -- 可存储 sources、tokens 等元信息
  created_at TEXT NOT NULL,
  FOREIGN KEY(session_id) REFERENCES chat_sessions(id),
  UNIQUE(session_id, turn_no)
);
CREATE INDEX idx_chat_turns_session ON chat_turns(session_id, turn_no);
```

> 完整 DDL 参见 `docs/spec/07-data-model.md` 基线 DDL 第 E3.1 节。

## API
- POST /chat/query（发送问题，返回答案 + sources）
  - 支持 session_id（可选，传入则带上历史）
  - 支持 history_turns（携带最近 N 轮）
  - 支持 mode: quick / precise
  - 支持 include_sources: true / false
- GET /chat/sessions（获取会话列表）
- GET /chat/sessions/{id}（获取会话详情，含历史轮次）
- DELETE /chat/sessions/{id}（删除会话）

## 测试
- include_sources
- quick/precise 模式
