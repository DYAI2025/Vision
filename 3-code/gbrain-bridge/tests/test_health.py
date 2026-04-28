"""Tests for GET /v1/health (TASK-gbrain-bridge-skeleton).

The endpoint exercises `app.vault.is_readable` against the configured
`VAULT_PATH`. We point VAULT_PATH at pytest's tmp_path for ok cases and at a
non-existent path for degraded cases — no real `/vault` mount required.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi.testclient import TestClient

from app.main import app

if TYPE_CHECKING:
    from pathlib import Path

    import pytest

client = TestClient(app)


def test_health_returns_200_when_vault_is_readable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("VAULT_PATH", str(tmp_path))
    response = client.get("/v1/health")
    assert response.status_code == 200


def test_health_payload_shape_matches_api_design(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Per 2-design/api-design.md § Health and observability."""
    monkeypatch.setenv("VAULT_PATH", str(tmp_path))
    body = client.get("/v1/health").json()

    assert set(body.keys()) == {"status", "version", "checks"}
    assert body["status"] in {"ok", "degraded", "down"}
    assert isinstance(body["version"], str)
    assert body["version"]
    assert isinstance(body["checks"], dict)


def test_health_reports_vault_ok(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VAULT_PATH", str(tmp_path))
    body = client.get("/v1/health").json()
    assert body["checks"]["vault"] == "ok"
    assert body["status"] == "ok"


def test_health_reports_degraded_when_vault_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("VAULT_PATH", str(tmp_path / "missing-mount"))
    body = client.get("/v1/health").json()
    assert body["checks"]["vault"] == "down"
    assert body["status"] == "degraded"


def test_health_returns_503_when_vault_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Compose's HTTP-status-only healthcheck must mark the container
    unhealthy when the vault mount is unreadable. Body still carries
    {status, version, checks} per api-design.md."""
    monkeypatch.setenv("VAULT_PATH", str(tmp_path / "missing-mount"))
    response = client.get("/v1/health")
    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "degraded"
    assert body["checks"]["vault"] == "down"


def test_health_does_not_require_auth(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Per api-design.md: 'No auth required' on /v1/health."""
    monkeypatch.setenv("VAULT_PATH", str(tmp_path))
    response = client.get("/v1/health")
    assert response.status_code != 401
    assert response.status_code != 403


def test_unknown_path_returns_404(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("VAULT_PATH", str(tmp_path))
    response = client.get("/v1/pages")
    assert response.status_code == 404
