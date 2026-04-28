"""Tests for GET /v1/health (TASK-backlog-core-skeleton).

backlog-core's health endpoint is the first that exercises a downstream
dependency (Postgres). The response shape still matches api-design.md §
Health and observability — `checks.postgres` is the new field.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from fastapi.testclient import TestClient

if TYPE_CHECKING:
    from collections.abc import Iterator

    from tests.conftest import FakePool

from app.db import get_pool
from app.main import app


@pytest.fixture
def client_with_down_pool(fake_pool_down: FakePool) -> Iterator[TestClient]:
    async def _override() -> FakePool:
        return fake_pool_down

    app.dependency_overrides[get_pool] = _override
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.pop(get_pool, None)


def test_health_returns_200_when_postgres_is_ok(client_with_pool: TestClient) -> None:
    response = client_with_pool.get("/v1/health")
    assert response.status_code == 200


def test_health_payload_shape_matches_api_design(client_with_pool: TestClient) -> None:
    response = client_with_pool.get("/v1/health")
    body = response.json()

    assert set(body.keys()) == {"status", "version", "checks"}
    assert body["status"] in {"ok", "degraded", "down"}
    assert isinstance(body["version"], str)
    assert body["version"]
    assert isinstance(body["checks"], dict)


def test_health_reports_postgres_ok(client_with_pool: TestClient) -> None:
    body = client_with_pool.get("/v1/health").json()
    assert body["checks"]["postgres"] == "ok"
    assert body["status"] == "ok"


def test_health_reports_degraded_when_postgres_is_down(
    client_with_down_pool: TestClient,
) -> None:
    """If `SELECT 1` fails, status flips to degraded and postgres=down."""
    body = client_with_down_pool.get("/v1/health").json()
    assert body["checks"]["postgres"] == "down"
    assert body["status"] == "degraded"


def test_health_returns_503_when_postgres_is_down(
    client_with_down_pool: TestClient,
) -> None:
    """Compose's HTTP-status-only healthcheck must mark the container
    unhealthy when Postgres is unreachable. The body still carries the
    full {status, version, checks} shape per api-design.md."""
    response = client_with_down_pool.get("/v1/health")
    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "degraded"
    assert body["checks"]["postgres"] == "down"


def test_health_does_not_require_auth(client_with_pool: TestClient) -> None:
    """Per api-design.md: 'No auth required' on /v1/health."""
    response = client_with_pool.get("/v1/health")
    assert response.status_code != 401
    assert response.status_code != 403


def test_unknown_path_returns_404(client_with_pool: TestClient) -> None:
    response = client_with_pool.get("/v1/inputs")
    assert response.status_code == 404
