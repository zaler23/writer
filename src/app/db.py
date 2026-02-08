from __future__ import annotations

import os
import sqlite3
from pathlib import Path

SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS projects (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  genre TEXT,
  premise TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS project_settings (
  id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  settings_json TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY(project_id) REFERENCES projects(id)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_project_settings_project_id
ON project_settings(project_id);

CREATE TABLE IF NOT EXISTS chapters (
  id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  volume_no INTEGER NOT NULL DEFAULT 1,
  chapter_no INTEGER NOT NULL,
  title TEXT,
  status TEXT NOT NULL DEFAULT 'planned',
  needs_review INTEGER NOT NULL DEFAULT 0,
  review_reason TEXT,
  plan_json TEXT,
  traversal_profile_id TEXT,
  style_guide_id TEXT,
  lock_version INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  UNIQUE(project_id, volume_no, chapter_no),
  FOREIGN KEY(project_id) REFERENCES projects(id)
);

CREATE TABLE IF NOT EXISTS chapter_text_versions (
  id TEXT PRIMARY KEY,
  chapter_id TEXT NOT NULL,
  version_no INTEGER NOT NULL,
  stage TEXT NOT NULL,
  content_text TEXT NOT NULL,
  source_run_id TEXT,
  source_step_id TEXT,
  created_at TEXT NOT NULL,
  UNIQUE(chapter_id, version_no),
  FOREIGN KEY(chapter_id) REFERENCES chapters(id)
);

CREATE TABLE IF NOT EXISTS chapter_segments (
  id TEXT PRIMARY KEY,
  chapter_id TEXT NOT NULL,
  segment_no INTEGER NOT NULL,
  title TEXT,
  pov_node_id TEXT,
  segment_type TEXT,
  content_text TEXT,
  attrs_json TEXT,
  is_deleted INTEGER NOT NULL DEFAULT 0,
  deleted_at TEXT,
  deleted_reason TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  UNIQUE(chapter_id, segment_no),
  FOREIGN KEY(chapter_id) REFERENCES chapters(id)
);

CREATE TABLE IF NOT EXISTS chapter_reviews (
  id TEXT PRIMARY KEY,
  chapter_id TEXT NOT NULL,
  version_id TEXT NOT NULL,
  review_type TEXT NOT NULL DEFAULT 'logic',
  report_json TEXT NOT NULL,
  source_run_id TEXT,
  source_step_id TEXT,
  created_at TEXT NOT NULL,
  FOREIGN KEY(chapter_id) REFERENCES chapters(id),
  FOREIGN KEY(version_id) REFERENCES chapter_text_versions(id)
);

CREATE TABLE IF NOT EXISTS runs (
  id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  swarm_profile_id TEXT,
  run_type TEXT NOT NULL,
  target_chapter_id TEXT,
  status TEXT NOT NULL,
  input_json TEXT,
  output_json TEXT,
  budget_json TEXT,
  started_at TEXT NOT NULL,
  finished_at TEXT,
  FOREIGN KEY(project_id) REFERENCES projects(id),
  FOREIGN KEY(target_chapter_id) REFERENCES chapters(id)
);

CREATE TABLE IF NOT EXISTS run_steps (
  id TEXT PRIMARY KEY,
  run_id TEXT NOT NULL,
  step_no INTEGER NOT NULL,
  step_type TEXT NOT NULL,
  role TEXT,
  status TEXT NOT NULL,
  requires_approval INTEGER NOT NULL DEFAULT 0,
  approval_status TEXT NOT NULL DEFAULT 'n/a',
  override_payload_json TEXT,
  input_json TEXT,
  output_json TEXT,
  budget_json TEXT,
  started_at TEXT NOT NULL,
  finished_at TEXT,
  error_text TEXT,
  UNIQUE(run_id, step_no),
  FOREIGN KEY(run_id) REFERENCES runs(id)
);

CREATE TABLE IF NOT EXISTS llm_calls (
  id TEXT PRIMARY KEY,
  run_id TEXT,
  step_id TEXT,
  provider_id TEXT,
  model_id TEXT,
  purpose TEXT,
  request_hash TEXT NOT NULL,
  response_hash TEXT,
  usage_json TEXT,
  status TEXT NOT NULL,
  error_text TEXT,
  created_at TEXT NOT NULL,
  FOREIGN KEY(run_id) REFERENCES runs(id),
  FOREIGN KEY(step_id) REFERENCES run_steps(id)
);

CREATE INDEX IF NOT EXISTS idx_chapters_project_id ON chapters(project_id, id);
CREATE INDEX IF NOT EXISTS idx_chapter_segments_chapter_id ON chapter_segments(chapter_id, segment_no);
CREATE INDEX IF NOT EXISTS idx_chapter_text_versions_chapter_id ON chapter_text_versions(chapter_id, id);
CREATE INDEX IF NOT EXISTS idx_chapter_reviews_chapter_id ON chapter_reviews(chapter_id, id);
CREATE INDEX IF NOT EXISTS idx_runs_project_id ON runs(project_id, id);
CREATE INDEX IF NOT EXISTS idx_run_steps_run_id ON run_steps(run_id, step_no);
CREATE INDEX IF NOT EXISTS idx_llm_calls_run_id ON llm_calls(run_id, created_at);
"""


def _db_path() -> Path:
    raw_path = os.getenv("WRITER_DB_PATH", "data/core.db")
    return Path(raw_path)


def get_connection() -> sqlite3.Connection:
    db_path = _db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db() -> None:
    with get_connection() as conn:
        conn.executescript(SCHEMA_SQL)
        conn.commit()
