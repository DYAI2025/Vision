from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from app.main import app


def test_context_lookup(monkeypatch: Any, tmp_path: Path) -> None:
    project_dir = tmp_path / "projects" / "p1"
    project_dir.mkdir(parents=True)
    (project_dir / "page-a.md").write_text("Release plan for payment integration", encoding="utf-8")
    monkeypatch.setenv("VAULT_PATH", str(tmp_path))

    client = TestClient(app)
    response = client.get("/v1/context/p1", params={"q": "payment plan"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["project_id"] == "p1"
    assert payload["snippets"]
    assert payload["snippets"][0]["page_id"] == "page-a"
