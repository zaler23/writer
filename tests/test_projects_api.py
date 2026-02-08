from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def test_projects_create_get_and_list(monkeypatch, tmp_path) -> None:
    db_path = tmp_path / "core.db"
    monkeypatch.setenv("WRITER_DB_PATH", str(db_path))

    with TestClient(app) as client:
        created = client.post(
            "/projects",
            json={"name": "My Novel", "genre": "Fantasy", "premise": "A seed premise"},
        )
        assert created.status_code == 200
        project = created.json()
        assert project["id"].startswith("proj_")

        fetched = client.get(f"/projects/{project['id']}")
        assert fetched.status_code == 200
        assert fetched.json()["name"] == "My Novel"

        listed = client.get("/projects", params={"limit": 10})
        assert listed.status_code == 200
        payload = listed.json()
        assert len(payload["items"]) >= 1
        assert payload["items"][0]["id"] == project["id"]


def test_project_update(monkeypatch, tmp_path) -> None:
    db_path = tmp_path / "core.db"
    monkeypatch.setenv("WRITER_DB_PATH", str(db_path))

    with TestClient(app) as client:
        created = client.post("/projects", json={"name": "Old Name"})
        project_id = created.json()["id"]

        updated = client.put(
            f"/projects/{project_id}",
            json={"name": "New Name", "premise": "Updated premise"},
        )
        assert updated.status_code == 200
        body = updated.json()
        assert body["name"] == "New Name"
        assert body["premise"] == "Updated premise"


def test_project_settings_validation_and_upsert(monkeypatch, tmp_path) -> None:
    db_path = tmp_path / "core.db"
    monkeypatch.setenv("WRITER_DB_PATH", str(db_path))

    with TestClient(app) as client:
        created = client.post("/projects", json={"name": "Config Test"})
        project_id = created.json()["id"]

        invalid = client.put(
            f"/projects/{project_id}/settings",
            json={"settings_json": {"schema_version": "2.0"}},
        )
        assert invalid.status_code == 422

        saved = client.put(
            f"/projects/{project_id}/settings",
            json={"settings_json": {"schema_version": "1.2", "max_tokens": 12000}},
        )
        assert saved.status_code == 200
        assert saved.json()["settings_json"]["max_tokens"] == 12000

        loaded = client.get(f"/projects/{project_id}/settings")
        assert loaded.status_code == 200
        assert loaded.json()["settings_json"]["schema_version"] == "1.2"

