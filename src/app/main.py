from __future__ import annotations

import json
import hashlib
import sqlite3
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Generator

from fastapi import Depends, FastAPI, HTTPException, Query

from app.db import get_connection, init_db
from app.schemas import (
    ChapterCreate,
    ChapterListResponse,
    ChapterOut,
    ChapterReviewListResponse,
    ChapterReviewOut,
    ChapterSegmentListResponse,
    ChapterSegmentOut,
    ChapterSegmentUpsert,
    ChapterTextVersionListResponse,
    ChapterTextVersionOut,
    ChapterUpdate,
    ProjectCreate,
    ProjectListResponse,
    ProjectOut,
    ProjectSettingsOut,
    ProjectSettingsUpdate,
    ProjectUpdate,
    RunOut,
    RunStepListResponse,
    RunStepOut,
    RunStepOverride,
    SwarmRunCreate,
)
from app.ulid import new_ulid


@asynccontextmanager
async def app_lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title="Writer API", version="0.1.0-m0a", lifespan=app_lifespan)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def db_session() -> Generator[sqlite3.Connection, None, None]:
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()


def _project_from_row(row: sqlite3.Row) -> ProjectOut:
    return ProjectOut(
        id=row["id"],
        name=row["name"],
        genre=row["genre"],
        premise=row["premise"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _project_exists(conn: sqlite3.Connection, project_id: str) -> bool:
    row = conn.execute("SELECT 1 FROM projects WHERE id = ?", (project_id,)).fetchone()
    return row is not None


def _ensure_settings(
    conn: sqlite3.Connection, project_id: str, now: str | None = None
) -> sqlite3.Row:
    row = conn.execute(
        "SELECT id, project_id, settings_json, created_at, updated_at "
        "FROM project_settings WHERE project_id = ?",
        (project_id,),
    ).fetchone()
    if row:
        return row

    timestamp = now or utc_now_iso()
    settings_id = new_ulid("pset")
    conn.execute(
        "INSERT INTO project_settings (id, project_id, settings_json, created_at, updated_at) "
        "VALUES (?, ?, ?, ?, ?)",
        (settings_id, project_id, "{}", timestamp, timestamp),
    )
    conn.commit()
    return conn.execute(
        "SELECT id, project_id, settings_json, created_at, updated_at "
        "FROM project_settings WHERE project_id = ?",
        (project_id,),
    ).fetchone()


def _loads_optional_json(raw: str | None) -> dict[str, object] | None:
    if raw is None:
        return None
    return json.loads(raw)


def _chapter_row_or_404(conn: sqlite3.Connection, chapter_id: str) -> sqlite3.Row:
    row = conn.execute(
        "SELECT id, project_id, volume_no, chapter_no, title, status, needs_review, review_reason, "
        "plan_json, traversal_profile_id, style_guide_id, lock_version, created_at, updated_at "
        "FROM chapters WHERE id = ?",
        (chapter_id,),
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Chapter not found.")
    return row


def _chapter_from_row(row: sqlite3.Row) -> ChapterOut:
    return ChapterOut(
        id=row["id"],
        project_id=row["project_id"],
        volume_no=row["volume_no"],
        chapter_no=row["chapter_no"],
        title=row["title"],
        status=row["status"],
        needs_review=bool(row["needs_review"]),
        review_reason=row["review_reason"],
        plan_json=_loads_optional_json(row["plan_json"]),
        traversal_profile_id=row["traversal_profile_id"],
        style_guide_id=row["style_guide_id"],
        lock_version=row["lock_version"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _chapter_segment_from_row(row: sqlite3.Row) -> ChapterSegmentOut:
    return ChapterSegmentOut(
        id=row["id"],
        chapter_id=row["chapter_id"],
        segment_no=row["segment_no"],
        title=row["title"],
        pov_node_id=row["pov_node_id"],
        segment_type=row["segment_type"],
        content_text=row["content_text"],
        attrs_json=_loads_optional_json(row["attrs_json"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _chapter_review_from_row(row: sqlite3.Row) -> ChapterReviewOut:
    return ChapterReviewOut(
        id=row["id"],
        chapter_id=row["chapter_id"],
        version_id=row["version_id"],
        review_type=row["review_type"],
        report_json=json.loads(row["report_json"]),
        source_run_id=row["source_run_id"],
        source_step_id=row["source_step_id"],
        created_at=row["created_at"],
    )


def _chapter_text_version_from_row(row: sqlite3.Row) -> ChapterTextVersionOut:
    return ChapterTextVersionOut(
        id=row["id"],
        chapter_id=row["chapter_id"],
        version_no=row["version_no"],
        stage=row["stage"],
        content_text=row["content_text"],
        source_run_id=row["source_run_id"],
        source_step_id=row["source_step_id"],
        created_at=row["created_at"],
    )


@app.post("/projects", response_model=ProjectOut)
def create_project(payload: ProjectCreate, conn: sqlite3.Connection = Depends(db_session)) -> ProjectOut:
    now = utc_now_iso()
    project_id = new_ulid("proj")
    conn.execute(
        "INSERT INTO projects (id, name, genre, premise, created_at, updated_at) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (project_id, payload.name, payload.genre, payload.premise, now, now),
    )
    conn.execute(
        "INSERT INTO project_settings (id, project_id, settings_json, created_at, updated_at) "
        "VALUES (?, ?, ?, ?, ?)",
        (new_ulid("pset"), project_id, "{}", now, now),
    )
    conn.commit()
    row = conn.execute(
        "SELECT id, name, genre, premise, created_at, updated_at FROM projects WHERE id = ?",
        (project_id,),
    ).fetchone()
    return _project_from_row(row)


@app.get("/projects/{project_id}", response_model=ProjectOut)
def get_project(project_id: str, conn: sqlite3.Connection = Depends(db_session)) -> ProjectOut:
    row = conn.execute(
        "SELECT id, name, genre, premise, created_at, updated_at FROM projects WHERE id = ?",
        (project_id,),
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Project not found.")
    return _project_from_row(row)


@app.get("/projects", response_model=ProjectListResponse)
def list_projects(
    limit: int = Query(default=20, ge=1, le=100),
    after: str | None = Query(default=None),
    conn: sqlite3.Connection = Depends(db_session),
) -> ProjectListResponse:
    if after:
        rows = conn.execute(
            "SELECT id, name, genre, premise, created_at, updated_at "
            "FROM projects WHERE id > ? ORDER BY id LIMIT ?",
            (after, limit + 1),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT id, name, genre, premise, created_at, updated_at "
            "FROM projects ORDER BY id LIMIT ?",
            (limit + 1,),
        ).fetchall()

    has_more = len(rows) > limit
    page_rows = rows[:limit]
    items = [_project_from_row(row) for row in page_rows]
    next_after = page_rows[-1]["id"] if has_more and page_rows else None
    return ProjectListResponse(items=items, next_after=next_after)


@app.put("/projects/{project_id}", response_model=ProjectOut)
def update_project(
    project_id: str,
    payload: ProjectUpdate,
    conn: sqlite3.Connection = Depends(db_session),
) -> ProjectOut:
    row = conn.execute(
        "SELECT id, name, genre, premise, created_at, updated_at FROM projects WHERE id = ?",
        (project_id,),
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Project not found.")

    fields: list[str] = []
    values: list[object] = []
    if payload.name is not None:
        fields.append("name = ?")
        values.append(payload.name)
    if payload.genre is not None:
        fields.append("genre = ?")
        values.append(payload.genre)
    if payload.premise is not None:
        fields.append("premise = ?")
        values.append(payload.premise)

    values.extend([utc_now_iso(), project_id])
    sql = f"UPDATE projects SET {', '.join(fields)}, updated_at = ? WHERE id = ?"
    conn.execute(sql, values)
    conn.commit()

    updated = conn.execute(
        "SELECT id, name, genre, premise, created_at, updated_at FROM projects WHERE id = ?",
        (project_id,),
    ).fetchone()
    return _project_from_row(updated)


@app.get("/projects/{project_id}/settings", response_model=ProjectSettingsOut)
def get_project_settings(
    project_id: str, conn: sqlite3.Connection = Depends(db_session)
) -> ProjectSettingsOut:
    if not _project_exists(conn, project_id):
        raise HTTPException(status_code=404, detail="Project not found.")

    row = _ensure_settings(conn, project_id)
    return ProjectSettingsOut(
        id=row["id"],
        project_id=row["project_id"],
        settings_json=json.loads(row["settings_json"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


@app.put("/projects/{project_id}/settings", response_model=ProjectSettingsOut)
def put_project_settings(
    project_id: str,
    payload: ProjectSettingsUpdate,
    conn: sqlite3.Connection = Depends(db_session),
) -> ProjectSettingsOut:
    if not _project_exists(conn, project_id):
        raise HTTPException(status_code=404, detail="Project not found.")

    now = utc_now_iso()
    conn.execute(
        "INSERT INTO project_settings (id, project_id, settings_json, created_at, updated_at) "
        "VALUES (?, ?, ?, ?, ?) "
        "ON CONFLICT(project_id) DO UPDATE SET "
        "settings_json = excluded.settings_json, "
        "updated_at = excluded.updated_at",
        (
            new_ulid("pset"),
            project_id,
            json.dumps(payload.settings_json, ensure_ascii=True, sort_keys=True),
            now,
            now,
        ),
    )
    conn.commit()
    row = conn.execute(
        "SELECT id, project_id, settings_json, created_at, updated_at "
        "FROM project_settings WHERE project_id = ?",
        (project_id,),
    ).fetchone()
    return ProjectSettingsOut(
        id=row["id"],
        project_id=row["project_id"],
        settings_json=json.loads(row["settings_json"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


@app.post("/chapters", response_model=ChapterOut)
def create_chapter(payload: ChapterCreate, conn: sqlite3.Connection = Depends(db_session)) -> ChapterOut:
    if not _project_exists(conn, payload.project_id):
        raise HTTPException(status_code=404, detail="Project not found.")

    now = utc_now_iso()
    chapter_id = new_ulid("ch")
    try:
        conn.execute(
            "INSERT INTO chapters ("
            "id, project_id, volume_no, chapter_no, title, status, needs_review, review_reason, "
            "plan_json, traversal_profile_id, style_guide_id, lock_version, created_at, updated_at"
            ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                chapter_id,
                payload.project_id,
                payload.volume_no,
                payload.chapter_no,
                payload.title,
                "planned",
                0,
                None,
                (
                    json.dumps(payload.plan_json, ensure_ascii=True, sort_keys=True)
                    if payload.plan_json is not None
                    else None
                ),
                payload.traversal_profile_id,
                payload.style_guide_id,
                0,
                now,
                now,
            ),
        )
    except sqlite3.IntegrityError as exc:
        message = str(exc).lower()
        if "unique" in message and "chapters.project_id, chapters.volume_no, chapters.chapter_no" in message:
            raise HTTPException(
                status_code=409,
                detail="Chapter number already exists in this project volume.",
            ) from exc
        raise

    conn.commit()
    row = conn.execute(
        "SELECT id, project_id, volume_no, chapter_no, title, status, needs_review, review_reason, "
        "plan_json, traversal_profile_id, style_guide_id, lock_version, created_at, updated_at "
        "FROM chapters WHERE id = ?",
        (chapter_id,),
    ).fetchone()
    return _chapter_from_row(row)


@app.get("/chapters/{chapter_id}", response_model=ChapterOut)
def get_chapter(chapter_id: str, conn: sqlite3.Connection = Depends(db_session)) -> ChapterOut:
    row = _chapter_row_or_404(conn, chapter_id)
    return _chapter_from_row(row)


@app.get("/chapters", response_model=ChapterListResponse)
def list_chapters(
    project_id: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    after: str | None = Query(default=None),
    conn: sqlite3.Connection = Depends(db_session),
) -> ChapterListResponse:
    filters: list[str] = []
    values: list[object] = []
    if project_id is not None:
        filters.append("project_id = ?")
        values.append(project_id)
    if after is not None:
        filters.append("id > ?")
        values.append(after)

    where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""
    query = (
        "SELECT id, project_id, volume_no, chapter_no, title, status, needs_review, review_reason, "
        "plan_json, traversal_profile_id, style_guide_id, lock_version, created_at, updated_at "
        f"FROM chapters {where_clause} ORDER BY id LIMIT ?"
    )
    rows = conn.execute(query, (*values, limit + 1)).fetchall()

    has_more = len(rows) > limit
    page_rows = rows[:limit]
    items = [_chapter_from_row(row) for row in page_rows]
    next_after = page_rows[-1]["id"] if has_more and page_rows else None
    return ChapterListResponse(items=items, next_after=next_after)


@app.put("/chapters/{chapter_id}", response_model=ChapterOut)
def update_chapter(
    chapter_id: str,
    payload: ChapterUpdate,
    conn: sqlite3.Connection = Depends(db_session),
) -> ChapterOut:
    _chapter_row_or_404(conn, chapter_id)

    fields: list[str] = []
    values: list[object] = []
    if payload.title is not None:
        fields.append("title = ?")
        values.append(payload.title)
    if payload.plan_json is not None:
        fields.append("plan_json = ?")
        values.append(json.dumps(payload.plan_json, ensure_ascii=True, sort_keys=True))
    if payload.traversal_profile_id is not None:
        fields.append("traversal_profile_id = ?")
        values.append(payload.traversal_profile_id)
    if payload.style_guide_id is not None:
        fields.append("style_guide_id = ?")
        values.append(payload.style_guide_id)

    values.extend([utc_now_iso(), chapter_id])
    query = f"UPDATE chapters SET {', '.join(fields)}, updated_at = ? WHERE id = ?"
    conn.execute(query, values)
    conn.commit()

    updated = _chapter_row_or_404(conn, chapter_id)
    return _chapter_from_row(updated)


@app.post("/chapters/{chapter_id}/segments", response_model=ChapterSegmentOut)
def upsert_chapter_segment(
    chapter_id: str,
    payload: ChapterSegmentUpsert,
    conn: sqlite3.Connection = Depends(db_session),
) -> ChapterSegmentOut:
    _chapter_row_or_404(conn, chapter_id)

    now = utc_now_iso()
    conn.execute(
        "INSERT INTO chapter_segments ("
        "id, chapter_id, segment_no, title, pov_node_id, segment_type, content_text, attrs_json, "
        "is_deleted, deleted_at, deleted_reason, created_at, updated_at"
        ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, NULL, NULL, ?, ?) "
        "ON CONFLICT(chapter_id, segment_no) DO UPDATE SET "
        "title = excluded.title, "
        "pov_node_id = excluded.pov_node_id, "
        "segment_type = excluded.segment_type, "
        "content_text = excluded.content_text, "
        "attrs_json = excluded.attrs_json, "
        "is_deleted = 0, "
        "deleted_at = NULL, "
        "deleted_reason = NULL, "
        "updated_at = excluded.updated_at",
        (
            new_ulid("chseg"),
            chapter_id,
            payload.segment_no,
            payload.title,
            payload.pov_node_id,
            payload.segment_type,
            payload.content_text,
            (
                json.dumps(payload.attrs_json, ensure_ascii=True, sort_keys=True)
                if payload.attrs_json is not None
                else None
            ),
            now,
            now,
        ),
    )
    conn.commit()
    row = conn.execute(
        "SELECT id, chapter_id, segment_no, title, pov_node_id, segment_type, content_text, attrs_json, "
        "created_at, updated_at "
        "FROM chapter_segments WHERE chapter_id = ? AND segment_no = ? AND is_deleted = 0",
        (chapter_id, payload.segment_no),
    ).fetchone()
    return _chapter_segment_from_row(row)


@app.get("/chapters/{chapter_id}/segments", response_model=ChapterSegmentListResponse)
def list_chapter_segments(
    chapter_id: str, conn: sqlite3.Connection = Depends(db_session)
) -> ChapterSegmentListResponse:
    _chapter_row_or_404(conn, chapter_id)
    rows = conn.execute(
        "SELECT id, chapter_id, segment_no, title, pov_node_id, segment_type, content_text, attrs_json, "
        "created_at, updated_at "
        "FROM chapter_segments WHERE chapter_id = ? AND is_deleted = 0 ORDER BY segment_no",
        (chapter_id,),
    ).fetchall()
    return ChapterSegmentListResponse(items=[_chapter_segment_from_row(row) for row in rows])


@app.get("/chapters/{chapter_id}/reviews", response_model=ChapterReviewListResponse)
def list_chapter_reviews(
    chapter_id: str,
    limit: int = Query(default=50, ge=1, le=100),
    after: str | None = Query(default=None),
    conn: sqlite3.Connection = Depends(db_session),
) -> ChapterReviewListResponse:
    _chapter_row_or_404(conn, chapter_id)
    if after:
        rows = conn.execute(
            "SELECT id, chapter_id, version_id, review_type, report_json, source_run_id, source_step_id, created_at "
            "FROM chapter_reviews WHERE chapter_id = ? AND id > ? ORDER BY id LIMIT ?",
            (chapter_id, after, limit + 1),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT id, chapter_id, version_id, review_type, report_json, source_run_id, source_step_id, created_at "
            "FROM chapter_reviews WHERE chapter_id = ? ORDER BY id LIMIT ?",
            (chapter_id, limit + 1),
        ).fetchall()

    has_more = len(rows) > limit
    page_rows = rows[:limit]
    items = [_chapter_review_from_row(row) for row in page_rows]
    next_after = page_rows[-1]["id"] if has_more and page_rows else None
    return ChapterReviewListResponse(items=items, next_after=next_after)


@app.get("/chapters/{chapter_id}/text-versions", response_model=ChapterTextVersionListResponse)
def list_chapter_text_versions(
    chapter_id: str,
    limit: int = Query(default=50, ge=1, le=100),
    after: str | None = Query(default=None),
    conn: sqlite3.Connection = Depends(db_session),
) -> ChapterTextVersionListResponse:
    _chapter_row_or_404(conn, chapter_id)
    if after:
        rows = conn.execute(
            "SELECT id, chapter_id, version_no, stage, content_text, source_run_id, source_step_id, created_at "
            "FROM chapter_text_versions WHERE chapter_id = ? AND id > ? ORDER BY id LIMIT ?",
            (chapter_id, after, limit + 1),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT id, chapter_id, version_no, stage, content_text, source_run_id, source_step_id, created_at "
            "FROM chapter_text_versions WHERE chapter_id = ? ORDER BY id LIMIT ?",
            (chapter_id, limit + 1),
        ).fetchall()

    has_more = len(rows) > limit
    page_rows = rows[:limit]
    items = [_chapter_text_version_from_row(row) for row in page_rows]
    next_after = page_rows[-1]["id"] if has_more and page_rows else None
    return ChapterTextVersionListResponse(items=items, next_after=next_after)


def _run_row_or_404(conn: sqlite3.Connection, run_id: str) -> sqlite3.Row:
    row = conn.execute(
        "SELECT id, project_id, swarm_profile_id, run_type, target_chapter_id, status, "
        "input_json, output_json, budget_json, started_at, finished_at "
        "FROM runs WHERE id = ?",
        (run_id,),
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Run not found.")
    return row


def _run_step_row_or_404(conn: sqlite3.Connection, run_id: str, step_id: str) -> sqlite3.Row:
    row = conn.execute(
        "SELECT id, run_id, step_no, step_type, role, status, requires_approval, approval_status, "
        "override_payload_json, input_json, output_json, budget_json, started_at, finished_at, error_text "
        "FROM run_steps WHERE run_id = ? AND id = ?",
        (run_id, step_id),
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Run step not found.")
    return row


def _first_run_step(conn: sqlite3.Connection, run_id: str) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT id, run_id, step_no, step_type, role, status, requires_approval, approval_status, "
        "override_payload_json, input_json, output_json, budget_json, started_at, finished_at, error_text "
        "FROM run_steps WHERE run_id = ? ORDER BY step_no LIMIT 1",
        (run_id,),
    ).fetchone()


def _run_from_row(row: sqlite3.Row) -> RunOut:
    return RunOut(
        id=row["id"],
        project_id=row["project_id"],
        swarm_profile_id=row["swarm_profile_id"],
        run_type=row["run_type"],
        target_chapter_id=row["target_chapter_id"],
        status=row["status"],
        input_json=_loads_optional_json(row["input_json"]),
        output_json=_loads_optional_json(row["output_json"]),
        budget_json=_loads_optional_json(row["budget_json"]),
        started_at=row["started_at"],
        finished_at=row["finished_at"],
    )


def _run_step_from_row(row: sqlite3.Row) -> RunStepOut:
    return RunStepOut(
        id=row["id"],
        run_id=row["run_id"],
        step_no=row["step_no"],
        step_type=row["step_type"],
        role=row["role"],
        status=row["status"],
        requires_approval=bool(row["requires_approval"]),
        approval_status=row["approval_status"],
        override_payload_json=_loads_optional_json(row["override_payload_json"]),
        input_json=_loads_optional_json(row["input_json"]),
        output_json=_loads_optional_json(row["output_json"]),
        budget_json=_loads_optional_json(row["budget_json"]),
        started_at=row["started_at"],
        finished_at=row["finished_at"],
        error_text=row["error_text"],
    )


def _default_llm_generate(request_payload: dict[str, object]) -> dict[str, object]:
    chapter_title = request_payload.get("chapter_title")
    if not isinstance(chapter_title, str) or not chapter_title.strip():
        chapter_title = f"Chapter {request_payload.get('chapter_no', 'X')}"

    input_json = request_payload.get("input_json")
    prompt_text = ""
    if isinstance(input_json, dict):
        raw_prompt = input_json.get("prompt")
        if isinstance(raw_prompt, str):
            prompt_text = raw_prompt.strip()

    base_text = prompt_text or "M0a draft generated by the built-in mock runner."
    content_text = f"{chapter_title}\n\n{base_text}"
    return {
        "content_text": content_text,
        "provider_id": "mock",
        "model_id": "mock-writer-v1",
    }


def _invoke_llm_for_step(
    conn: sqlite3.Connection,
    run_row: sqlite3.Row,
    step_row: sqlite3.Row,
    chapter_row: sqlite3.Row,
) -> str:
    run_input = _loads_optional_json(run_row["input_json"]) or {}
    request_payload: dict[str, object] = {
        "project_id": run_row["project_id"],
        "chapter_id": chapter_row["id"],
        "chapter_title": chapter_row["title"],
        "volume_no": chapter_row["volume_no"],
        "chapter_no": chapter_row["chapter_no"],
        "run_id": run_row["id"],
        "step_id": step_row["id"],
        "input_json": run_input,
    }
    request_text = json.dumps(request_payload, ensure_ascii=True, sort_keys=True)
    request_hash = hashlib.sha256(request_text.encode("utf-8")).hexdigest()
    call_id = new_ulid("llm")
    now = utc_now_iso()

    provider_id = "mock"
    model_id = "mock-writer-v1"
    usage_payload: dict[str, object] = {}
    try:
        generator = getattr(app.state, "llm_generate", None)
        if callable(generator):
            generated = generator(request_payload)
        else:
            generated = _default_llm_generate(request_payload)

        if isinstance(generated, str):
            content_text = generated
        elif isinstance(generated, dict):
            raw_content = generated.get("content_text")
            if not isinstance(raw_content, str):
                raise ValueError("LLM mock must return content_text as string.")
            content_text = raw_content
            if isinstance(generated.get("provider_id"), str):
                provider_id = generated["provider_id"]
            if isinstance(generated.get("model_id"), str):
                model_id = generated["model_id"]
            raw_usage = generated.get("usage_json")
            if isinstance(raw_usage, dict):
                usage_payload = raw_usage
        else:
            raise ValueError("LLM mock must return either a string or a dict.")

        if not content_text.strip():
            raise ValueError("LLM mock returned empty content.")

        if not usage_payload:
            usage_payload = {
                "prompt_tokens": max(1, len(request_text) // 4),
                "completion_tokens": max(1, len(content_text) // 4),
            }
        response_text = json.dumps({"content_text": content_text}, ensure_ascii=True, sort_keys=True)
        response_hash = hashlib.sha256(response_text.encode("utf-8")).hexdigest()

        conn.execute(
            "INSERT INTO llm_calls ("
            "id, run_id, step_id, provider_id, model_id, purpose, request_hash, response_hash, usage_json, "
            "status, error_text, created_at"
            ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                call_id,
                run_row["id"],
                step_row["id"],
                provider_id,
                model_id,
                step_row["step_type"],
                request_hash,
                response_hash,
                json.dumps(usage_payload, ensure_ascii=True, sort_keys=True),
                "succeeded",
                None,
                now,
            ),
        )
        return content_text
    except Exception as exc:
        conn.execute(
            "INSERT INTO llm_calls ("
            "id, run_id, step_id, provider_id, model_id, purpose, request_hash, response_hash, usage_json, "
            "status, error_text, created_at"
            ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                call_id,
                run_row["id"],
                step_row["id"],
                provider_id,
                model_id,
                step_row["step_type"],
                request_hash,
                None,
                None,
                "failed",
                str(exc),
                now,
            ),
        )
        raise


def _complete_run_with_content(
    conn: sqlite3.Connection,
    run_row: sqlite3.Row,
    step_row: sqlite3.Row,
    chapter_row: sqlite3.Row,
    content_text: str,
    approval_status: str,
) -> None:
    now = utc_now_iso()
    version_no = (
        conn.execute(
            "SELECT COALESCE(MAX(version_no), 0) + 1 FROM chapter_text_versions WHERE chapter_id = ?",
            (chapter_row["id"],),
        ).fetchone()[0]
    )
    version_id = new_ulid("chv")
    conn.execute(
        "INSERT INTO chapter_text_versions ("
        "id, chapter_id, version_no, stage, content_text, source_run_id, source_step_id, created_at"
        ") VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (
            version_id,
            chapter_row["id"],
            version_no,
            "final",
            content_text,
            run_row["id"],
            step_row["id"],
            now,
        ),
    )

    step_output = _loads_optional_json(step_row["output_json"]) or {}
    if not isinstance(step_output, dict):
        step_output = {}
    step_output["content_text"] = content_text
    step_output["chapter_version_id"] = version_id
    step_output["version_no"] = version_no
    conn.execute(
        "UPDATE run_steps SET status = ?, approval_status = ?, output_json = ?, finished_at = ?, error_text = NULL "
        "WHERE id = ?",
        (
            "completed",
            approval_status,
            json.dumps(step_output, ensure_ascii=True, sort_keys=True),
            now,
            step_row["id"],
        ),
    )

    run_output = {
        "chapter_id": chapter_row["id"],
        "chapter_version_id": version_id,
        "step_id": step_row["id"],
    }
    conn.execute(
        "UPDATE runs SET status = ?, output_json = ?, finished_at = ? WHERE id = ?",
        (
            "completed",
            json.dumps(run_output, ensure_ascii=True, sort_keys=True),
            now,
            run_row["id"],
        ),
    )
    conn.execute(
        "UPDATE chapters SET status = ?, needs_review = 0, review_reason = NULL, updated_at = ? WHERE id = ?",
        ("finalized", now, chapter_row["id"]),
    )


def _execute_run_until_stable(conn: sqlite3.Connection, run_id: str) -> sqlite3.Row:
    run_row = _run_row_or_404(conn, run_id)
    if run_row["status"] in {"completed", "failed", "cancelled"}:
        return run_row
    if run_row["status"] == "paused":
        return run_row

    if run_row["target_chapter_id"] is None:
        raise HTTPException(status_code=409, detail="Run has no target chapter.")

    chapter_row = _chapter_row_or_404(conn, run_row["target_chapter_id"])
    if chapter_row["project_id"] != run_row["project_id"]:
        raise HTTPException(status_code=403, detail="Chapter does not belong to run project.")

    if run_row["status"] == "created":
        now = utc_now_iso()
        conn.execute("UPDATE runs SET status = ? WHERE id = ?", ("running", run_id))
        conn.execute(
            "UPDATE chapters SET status = ?, needs_review = 0, review_reason = NULL, updated_at = ? WHERE id = ?",
            ("drafting", now, chapter_row["id"]),
        )
        run_row = _run_row_or_404(conn, run_id)

    step_row = _first_run_step(conn, run_id)
    if step_row is None:
        now = utc_now_iso()
        conn.execute(
            "UPDATE runs SET status = ?, output_json = ?, finished_at = ? WHERE id = ?",
            ("completed", "{}", now, run_id),
        )
        return _run_row_or_404(conn, run_id)

    if step_row["status"] == "pending":
        conn.execute("UPDATE run_steps SET status = ? WHERE id = ?", ("running", step_row["id"]))
        step_row = _run_step_row_or_404(conn, run_id, step_row["id"])

    if step_row["status"] == "pending_approval":
        pause_output = {"waiting_for_approval_step_id": step_row["id"]}
        conn.execute(
            "UPDATE runs SET status = ?, output_json = ? WHERE id = ?",
            ("paused", json.dumps(pause_output, ensure_ascii=True, sort_keys=True), run_id),
        )
        return _run_row_or_404(conn, run_id)

    if step_row["status"] == "approved":
        step_output = _loads_optional_json(step_row["output_json"]) or {}
        if not isinstance(step_output, dict):
            step_output = {}
        content_text = step_output.get("content_text") or step_output.get("generated_content_text")
        if not isinstance(content_text, str) or not content_text.strip():
            now = utc_now_iso()
            error = "Approved step has no content."
            conn.execute(
                "UPDATE run_steps SET status = ?, error_text = ?, finished_at = ? WHERE id = ?",
                ("failed", error, now, step_row["id"]),
            )
            conn.execute(
                "UPDATE runs SET status = ?, output_json = ?, finished_at = ? WHERE id = ?",
                (
                    "failed",
                    json.dumps({"error": error}, ensure_ascii=True, sort_keys=True),
                    now,
                    run_id,
                ),
            )
            conn.execute(
                "UPDATE chapters SET needs_review = 1, review_reason = ?, updated_at = ? WHERE id = ?",
                (error, now, chapter_row["id"]),
            )
            return _run_row_or_404(conn, run_id)

        _complete_run_with_content(
            conn=conn,
            run_row=run_row,
            step_row=step_row,
            chapter_row=chapter_row,
            content_text=content_text,
            approval_status="approved",
        )
        return _run_row_or_404(conn, run_id)

    if step_row["status"] != "running":
        return _run_row_or_404(conn, run_id)

    try:
        content_text = _invoke_llm_for_step(
            conn=conn,
            run_row=run_row,
            step_row=step_row,
            chapter_row=chapter_row,
        )
    except Exception as exc:
        now = utc_now_iso()
        error = str(exc)
        conn.execute(
            "UPDATE run_steps SET status = ?, error_text = ?, finished_at = ? WHERE id = ?",
            ("failed", error, now, step_row["id"]),
        )
        conn.execute(
            "UPDATE runs SET status = ?, output_json = ?, finished_at = ? WHERE id = ?",
            (
                "failed",
                json.dumps({"error": error}, ensure_ascii=True, sort_keys=True),
                now,
                run_id,
            ),
        )
        conn.execute(
            "UPDATE chapters SET needs_review = 1, review_reason = ?, updated_at = ? WHERE id = ?",
            (error, now, chapter_row["id"]),
        )
        return _run_row_or_404(conn, run_id)

    if step_row["requires_approval"]:
        now = utc_now_iso()
        step_output = {"generated_content_text": content_text}
        conn.execute(
            "UPDATE run_steps SET status = ?, approval_status = ?, output_json = ?, finished_at = ? WHERE id = ?",
            (
                "pending_approval",
                "pending",
                json.dumps(step_output, ensure_ascii=True, sort_keys=True),
                now,
                step_row["id"],
            ),
        )
        pause_output = {"waiting_for_approval_step_id": step_row["id"]}
        conn.execute(
            "UPDATE runs SET status = ?, output_json = ? WHERE id = ?",
            ("paused", json.dumps(pause_output, ensure_ascii=True, sort_keys=True), run_id),
        )
        return _run_row_or_404(conn, run_id)

    _complete_run_with_content(
        conn=conn,
        run_row=run_row,
        step_row=step_row,
        chapter_row=chapter_row,
        content_text=content_text,
        approval_status="n/a",
    )
    return _run_row_or_404(conn, run_id)


@app.post("/swarm/run", response_model=RunOut)
def create_swarm_run(
    payload: SwarmRunCreate,
    conn: sqlite3.Connection = Depends(db_session),
) -> RunOut:
    if not _project_exists(conn, payload.project_id):
        raise HTTPException(status_code=404, detail="Project not found.")

    chapter_row = _chapter_row_or_404(conn, payload.chapter_id)
    if chapter_row["project_id"] != payload.project_id:
        raise HTTPException(status_code=403, detail="Chapter does not belong to this project.")

    now = utc_now_iso()
    run_id = new_ulid("run")
    step_id = new_ulid("step")
    conn.execute(
        "INSERT INTO runs ("
        "id, project_id, swarm_profile_id, run_type, target_chapter_id, status, input_json, output_json, "
        "budget_json, started_at, finished_at"
        ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            run_id,
            payload.project_id,
            payload.swarm_profile_id,
            payload.run_type,
            payload.chapter_id,
            "created",
            (
                json.dumps(payload.input_json, ensure_ascii=True, sort_keys=True)
                if payload.input_json is not None
                else None
            ),
            None,
            (
                json.dumps(payload.budget_json, ensure_ascii=True, sort_keys=True)
                if payload.budget_json is not None
                else None
            ),
            now,
            None,
        ),
    )
    conn.execute(
        "INSERT INTO run_steps ("
        "id, run_id, step_no, step_type, role, status, requires_approval, approval_status, "
        "override_payload_json, input_json, output_json, budget_json, started_at, finished_at, error_text"
        ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            step_id,
            run_id,
            1,
            "draft",
            "writer",
            "pending",
            1 if payload.requires_approval else 0,
            "n/a",
            None,
            None,
            None,
            (
                json.dumps(payload.budget_json, ensure_ascii=True, sort_keys=True)
                if payload.budget_json is not None
                else None
            ),
            now,
            None,
            None,
        ),
    )

    run_row = _run_row_or_404(conn, run_id)
    if payload.auto_start:
        run_row = _execute_run_until_stable(conn, run_id)

    conn.commit()
    return _run_from_row(run_row)


@app.get("/runs/{run_id}", response_model=RunOut)
def get_run(run_id: str, conn: sqlite3.Connection = Depends(db_session)) -> RunOut:
    row = _run_row_or_404(conn, run_id)
    return _run_from_row(row)


@app.get("/runs/{run_id}/steps", response_model=RunStepListResponse)
def list_run_steps(run_id: str, conn: sqlite3.Connection = Depends(db_session)) -> RunStepListResponse:
    _run_row_or_404(conn, run_id)
    rows = conn.execute(
        "SELECT id, run_id, step_no, step_type, role, status, requires_approval, approval_status, "
        "override_payload_json, input_json, output_json, budget_json, started_at, finished_at, error_text "
        "FROM run_steps WHERE run_id = ? ORDER BY step_no",
        (run_id,),
    ).fetchall()
    return RunStepListResponse(items=[_run_step_from_row(row) for row in rows])


@app.get("/runs/{run_id}/steps/{step_id}", response_model=RunStepOut)
def get_run_step(
    run_id: str, step_id: str, conn: sqlite3.Connection = Depends(db_session)
) -> RunStepOut:
    _run_row_or_404(conn, run_id)
    row = _run_step_row_or_404(conn, run_id, step_id)
    return _run_step_from_row(row)


@app.post("/runs/{run_id}/pause", response_model=RunOut)
def pause_run(run_id: str, conn: sqlite3.Connection = Depends(db_session)) -> RunOut:
    run_row = _run_row_or_404(conn, run_id)
    if run_row["status"] != "running":
        raise HTTPException(status_code=409, detail="Run is not in running state.")

    conn.execute("UPDATE runs SET status = ? WHERE id = ?", ("paused", run_id))
    conn.commit()
    return _run_from_row(_run_row_or_404(conn, run_id))


@app.post("/runs/{run_id}/resume", response_model=RunOut)
def resume_run(run_id: str, conn: sqlite3.Connection = Depends(db_session)) -> RunOut:
    run_row = _run_row_or_404(conn, run_id)
    if run_row["status"] not in {"paused", "created"}:
        raise HTTPException(status_code=409, detail="Run is not resumable in current state.")

    step_row = _first_run_step(conn, run_id)
    if step_row is not None and step_row["status"] == "pending_approval":
        raise HTTPException(status_code=409, detail="Run is waiting for step approval.")

    conn.execute("UPDATE runs SET status = ? WHERE id = ?", ("running", run_id))
    updated_run = _execute_run_until_stable(conn, run_id)
    conn.commit()
    return _run_from_row(updated_run)


@app.post("/runs/{run_id}/cancel", response_model=RunOut)
def cancel_run(run_id: str, conn: sqlite3.Connection = Depends(db_session)) -> RunOut:
    run_row = _run_row_or_404(conn, run_id)
    if run_row["status"] in {"completed", "failed", "cancelled"}:
        raise HTTPException(status_code=409, detail="Run is already finalized.")

    now = utc_now_iso()
    conn.execute(
        "UPDATE runs SET status = ?, output_json = ?, finished_at = ? WHERE id = ?",
        (
            "cancelled",
            json.dumps({"cancelled": True}, ensure_ascii=True, sort_keys=True),
            now,
            run_id,
        ),
    )
    if run_row["target_chapter_id"] is not None:
        conn.execute(
            "UPDATE chapters SET needs_review = 1, review_reason = ?, updated_at = ? WHERE id = ?",
            ("run_cancelled", now, run_row["target_chapter_id"]),
        )
    conn.commit()
    return _run_from_row(_run_row_or_404(conn, run_id))


@app.post("/runs/{run_id}/steps/{step_id}/approve", response_model=RunStepOut)
def approve_run_step(
    run_id: str,
    step_id: str,
    conn: sqlite3.Connection = Depends(db_session),
) -> RunStepOut:
    run_row = _run_row_or_404(conn, run_id)
    if run_row["status"] not in {"paused", "running"}:
        raise HTTPException(status_code=409, detail="Run cannot accept step approval in current state.")

    step_row = _run_step_row_or_404(conn, run_id, step_id)
    if step_row["status"] != "pending_approval":
        raise HTTPException(status_code=409, detail="Step is not waiting for approval.")

    conn.execute(
        "UPDATE run_steps SET status = ?, approval_status = ? WHERE id = ?",
        ("approved", "approved", step_id),
    )
    conn.execute("UPDATE runs SET status = ? WHERE id = ?", ("running", run_id))
    _execute_run_until_stable(conn, run_id)
    conn.commit()
    return _run_step_from_row(_run_step_row_or_404(conn, run_id, step_id))


@app.post("/runs/{run_id}/steps/{step_id}/override", response_model=RunStepOut)
def override_run_step(
    run_id: str,
    step_id: str,
    payload: RunStepOverride,
    conn: sqlite3.Connection = Depends(db_session),
) -> RunStepOut:
    run_row = _run_row_or_404(conn, run_id)
    if run_row["status"] not in {"paused", "running"}:
        raise HTTPException(status_code=409, detail="Run cannot accept step override in current state.")

    step_row = _run_step_row_or_404(conn, run_id, step_id)
    if step_row["status"] != "pending_approval":
        raise HTTPException(status_code=409, detail="Step is not waiting for override.")

    step_output = _loads_optional_json(step_row["output_json"]) or {}
    if not isinstance(step_output, dict):
        step_output = {}
    step_output["content_text"] = payload.content_text
    step_output["overridden"] = True
    conn.execute(
        "UPDATE run_steps SET status = ?, approval_status = ?, override_payload_json = ?, output_json = ? "
        "WHERE id = ?",
        (
            "approved",
            "approved",
            json.dumps({"content_text": payload.content_text}, ensure_ascii=True, sort_keys=True),
            json.dumps(step_output, ensure_ascii=True, sort_keys=True),
            step_id,
        ),
    )
    conn.execute("UPDATE runs SET status = ? WHERE id = ?", ("running", run_id))
    _execute_run_until_stable(conn, run_id)
    conn.commit()
    return _run_step_from_row(_run_step_row_or_404(conn, run_id, step_id))
