"""Tests for GET /v1/health (TASK-kanban-sync-skeleton).

The endpoint exercises `app.kanban.is_writable` against the configured
`KANBAN_SUBTREE`. We point KANBAN_SUBTREE at pytest's tmp_path for ok cases
and at a non-existent path for degraded cases — no real `/vault/Kanban`
mount required.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi.testclient import TestClient

from app.main import app

if TYPE_CHECKING:
    from pathlib import Path

    import pytest

client = TestClient(app)


def test_health_returns_200_when_kanban_subtree_is_writable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("KANBAN_SUBTREE", str(tmp_path))
    response = client.get("/v1/health")
    assert response.status_code == 200


def test_health_payload_shape_matches_api_design(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Per 2-design/api-design.md § Health and observability."""
    monkeypatch.setenv("KANBAN_SUBTREE", str(tmp_path))
    body = client.get("/v1/health").json()

    assert set(body.keys()) == {"status", "version", "checks"}
    assert body["status"] in {"ok", "degraded", "down"}
    assert isinstance(body["version"], str)
    assert body["version"]
    assert isinstance(body["checks"], dict)


def test_health_reports_kanban_subtree_ok(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("KANBAN_SUBTREE", str(tmp_path))
    body = client.get("/v1/health").json()
    assert body["checks"]["kanban_subtree"] == "ok"
    assert body["status"] == "ok"


def test_health_reports_degraded_when_kanban_subtree_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("KANBAN_SUBTREE", str(tmp_path / "missing-mount"))
    body = client.get("/v1/health").json()
    assert body["checks"]["kanban_subtree"] == "down"
    assert body["status"] == "degraded"


def test_health_returns_503_when_kanban_subtree_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Compose's HTTP-status-only healthcheck must mark the container
    unhealthy when the Kanban subtree is missing or not writable. Body
    still carries {status, version, checks} per api-design.md."""
    monkeypatch.setenv("KANBAN_SUBTREE", str(tmp_path / "missing-mount"))
    response = client.get("/v1/health")
    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "degraded"
    assert body["checks"]["kanban_subtree"] == "down"


def test_health_returns_503_when_kanban_subtree_is_a_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """If a misconfiguration mounts a file as the Kanban subtree, fail visibly."""
    fake_subtree = tmp_path / "Kanban"
    fake_subtree.write_text("not a directory")
    monkeypatch.setenv("KANBAN_SUBTREE", str(fake_subtree))
    response = client.get("/v1/health")
    assert response.status_code == 503
    assert response.json()["checks"]["kanban_subtree"] == "down"


def test_health_does_not_require_auth(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Per api-design.md: 'No auth required' on /v1/health."""
    monkeypatch.setenv("KANBAN_SUBTREE", str(tmp_path))
    response = client.get("/v1/health")
    assert response.status_code != 401
    assert response.status_code != 403


def test_unknown_path_returns_404(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("KANBAN_SUBTREE", str(tmp_path))
    response = client.get("/v1/cards")
    assert response.status_code == 404
