"""Smoke tests for GET /v1/health (TASK-hermes-skeleton).

Mirrors the suite in 3-code/whatsorga-ingest/tests/test_health.py — kept
parallel so any payload-shape drift is obvious.
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_returns_200() -> None:
    response = client.get("/v1/health")
    assert response.status_code == 200


def test_health_payload_shape_matches_api_design() -> None:
    """Per 2-design/api-design.md § Health and observability."""
    response = client.get("/v1/health")
    body = response.json()

    assert set(body.keys()) == {"status", "version", "checks"}
    assert body["status"] in {"ok", "degraded", "down"}
    assert isinstance(body["version"], str)
    assert body["version"]
    assert isinstance(body["checks"], dict)


def test_health_skeleton_reports_ok() -> None:
    """Skeleton task has no real dependencies to check, so /v1/health is unconditionally ok."""
    response = client.get("/v1/health")
    assert response.json()["status"] == "ok"


def test_health_does_not_require_auth() -> None:
    """Per api-design.md: 'No auth required' on /v1/health."""
    response = client.get("/v1/health")
    assert response.status_code != 401
    assert response.status_code != 403


def test_unknown_path_returns_404() -> None:
    """Skeleton has no other routes; everything else is 404."""
    response = client.get("/v1/not-found")
    assert response.status_code == 404
