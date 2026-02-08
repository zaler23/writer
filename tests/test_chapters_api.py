from __future__ import annotations

from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app.db import get_connection
from app.main import app
from app.ulid import new_ulid


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _create_project(client: TestClient, name: str = "Novel") -> str:
    resp = client.post("/projects", json={"name": name})
    assert resp.status_code == 200
    return resp.json()["id"]


def test_chapter_create_get_update_and_list(monkeypatch, tmp_path) -> None:
    db_path = tmp_path / "core.db"
    monkeypatch.setenv("WRITER_DB_PATH", str(db_path))

    with TestClient(app) as client:
        project_id = _create_project(client, "Chapter Book")

        created = client.post(
            "/chapters",
            json={
                "project_id": project_id,
                "volume_no": 1,
                "chapter_no": 1,
                "title": "Chapter One",
                "plan_json": {"schema_version": "1.2", "goals": ["introduce hero"]},
            },
        )
        assert created.status_code == 200
        chapter = created.json()
        assert chapter["id"].startswith("ch_")
        assert chapter["status"] == "planned"
        assert chapter["plan_json"]["schema_version"] == "1.2"

        fetched = client.get(f"/chapters/{chapter['id']}")
        assert fetched.status_code == 200
        assert fetched.json()["title"] == "Chapter One"

        updated = client.put(
            f"/chapters/{chapter['id']}",
            json={"title": "Opening Chapter", "plan_json": {"schema_version": "1.2", "goals": ["setup"]}},
        )
        assert updated.status_code == 200
        assert updated.json()["title"] == "Opening Chapter"
        assert updated.json()["plan_json"]["goals"] == ["setup"]

        listed = client.get("/chapters", params={"project_id": project_id, "limit": 10})
        assert listed.status_code == 200
        payload = listed.json()
        assert len(payload["items"]) == 1
        assert payload["items"][0]["id"] == chapter["id"]


def test_chapter_unique_number_conflict(monkeypatch, tmp_path) -> None:
    db_path = tmp_path / "core.db"
    monkeypatch.setenv("WRITER_DB_PATH", str(db_path))

    with TestClient(app) as client:
        project_id = _create_project(client, "Conflict Book")

        first = client.post(
            "/chapters",
            json={"project_id": project_id, "volume_no": 1, "chapter_no": 1, "title": "C1"},
        )
        assert first.status_code == 200

        duplicate = client.post(
            "/chapters",
            json={"project_id": project_id, "volume_no": 1, "chapter_no": 1, "title": "C1 Duplicate"},
        )
        assert duplicate.status_code == 409


def test_chapter_segments_upsert_and_list(monkeypatch, tmp_path) -> None:
    db_path = tmp_path / "core.db"
    monkeypatch.setenv("WRITER_DB_PATH", str(db_path))

    with TestClient(app) as client:
        project_id = _create_project(client, "Segment Book")
        chapter = client.post(
            "/chapters",
            json={"project_id": project_id, "volume_no": 1, "chapter_no": 2, "title": "C2"},
        )
        chapter_id = chapter.json()["id"]

        created_segment = client.post(
            f"/chapters/{chapter_id}/segments",
            json={
                "segment_no": 1,
                "title": "Hook",
                "segment_type": "action",
                "content_text": "first draft",
                "attrs_json": {"pace": "fast"},
            },
        )
        assert created_segment.status_code == 200
        assert created_segment.json()["title"] == "Hook"

        updated_segment = client.post(
            f"/chapters/{chapter_id}/segments",
            json={
                "segment_no": 1,
                "title": "Hook Revised",
                "segment_type": "action",
                "content_text": "second draft",
                "attrs_json": {"pace": "medium"},
            },
        )
        assert updated_segment.status_code == 200
        assert updated_segment.json()["title"] == "Hook Revised"

        listed = client.get(f"/chapters/{chapter_id}/segments")
        assert listed.status_code == 200
        payload = listed.json()
        assert len(payload["items"]) == 1
        assert payload["items"][0]["content_text"] == "second draft"
        assert payload["items"][0]["attrs_json"]["pace"] == "medium"


def test_chapter_text_versions_and_reviews_list(monkeypatch, tmp_path) -> None:
    db_path = tmp_path / "core.db"
    monkeypatch.setenv("WRITER_DB_PATH", str(db_path))

    with TestClient(app) as client:
        project_id = _create_project(client, "History Book")
        chapter = client.post(
            "/chapters",
            json={"project_id": project_id, "volume_no": 1, "chapter_no": 3, "title": "C3"},
        )
        chapter_id = chapter.json()["id"]
        version_id = new_ulid("chv")
        now = _utc_now_iso()

        with get_connection() as conn:
            conn.execute(
                "INSERT INTO chapter_text_versions "
                "(id, chapter_id, version_no, stage, content_text, source_run_id, source_step_id, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (version_id, chapter_id, 1, "final", "content v1", None, None, now),
            )
            conn.execute(
                "INSERT INTO chapter_reviews "
                "(id, chapter_id, version_id, review_type, report_json, source_run_id, source_step_id, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    new_ulid("chrev"),
                    chapter_id,
                    version_id,
                    "logic",
                    '{"issues":[{"level":"warn","message":"check pacing"}]}',
                    None,
                    None,
                    now,
                ),
            )
            conn.commit()

        versions = client.get(f"/chapters/{chapter_id}/text-versions")
        assert versions.status_code == 200
        assert len(versions.json()["items"]) == 1
        assert versions.json()["items"][0]["version_no"] == 1

        reviews = client.get(f"/chapters/{chapter_id}/reviews")
        assert reviews.status_code == 200
        assert len(reviews.json()["items"]) == 1
        assert reviews.json()["items"][0]["review_type"] == "logic"
