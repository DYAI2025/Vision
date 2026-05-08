"""API tests for kanban-sync."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import TYPE_CHECKING
import pytest
from fastapi.testclient import TestClient
from app.main import app
from bearer_auth import CallingIdentity, require_bearer_auth

if TYPE_CHECKING:
    from collections.abc import Iterator


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    # Setup tmp vault
    kanban_dir = tmp_path / "Kanban"
    kanban_dir.mkdir()
    monkeypatch.setenv("KANBAN_SUBTREE", str(kanban_dir))
    
    # Auth override
    def _auth_override() -> CallingIdentity:
        return CallingIdentity("operator")
    
    app.dependency_overrides[require_bearer_auth] = _auth_override
    
    with TestClient(app) as c:
        yield c
    
    app.dependency_overrides.pop(require_bearer_auth, None)


def test_post_card_creates_files(client: TestClient) -> None:
    payload = {
        "card_id": "task-1",
        "title": "New Task",
        "content": "Description here",
        "sync": {"confidence": 1.0},
        "column": "Inbox"
    }
    
    resp = client.post("/v1/cards", json=payload)
    assert resp.status_code == 201
    
    # Verify card file
    kanban_dir = Path(os.environ["KANBAN_SUBTREE"])
    assert (kanban_dir / "cards" / "task-1.md").exists()
    
    # Verify board link
    board_text = (kanban_dir / "Project Steering.md").read_text()
    assert "- [ ] [[task-1]]" in board_text


def test_sync_detects_move(client: TestClient) -> None:
    # 1. Create a card in Inbox
    client.post("/v1/cards", json={
        "card_id": "task-move",
        "title": "Move Me",
        "column": "Inbox",
        "sync": {"proposal_id": "00000000-0000-0000-0000-000000000001"}
    })
    
    kanban_dir = Path(os.environ["KANBAN_SUBTREE"])
    board_path = kanban_dir / "Project Steering.md"
    
    # 2. Simulate human move in board file
    content = board_path.read_text()
    content = re.sub(r"## Inbox\n- \[ \] \[\[task-move\]\]", "## Inbox\n\n## Done\n- [ ] [[task-move]]", content)
    board_path.write_text(content)
    
    # 3. Trigger sync
    resp = client.post("/v1/sync")
    assert resp.status_code == 200
    assert resp.json()["detected_moves"] == 1
    
    # 4. Verify card file is updated
    resp = client.get("/v1/cards/task-move")
    assert resp.json()["column"] == "Done"
