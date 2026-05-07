"""API tests for source-consent management endpoints."""

from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

if TYPE_CHECKING:
    from collections.abc import Iterator

from bearer_auth import CallingIdentity, require_bearer_auth

from app.db import get_pool
from app.main import app

_NOW = datetime(2026, 5, 7, 12, 0, tzinfo=UTC)


def _source(**overrides: object) -> dict[str, object]:
    data: dict[str, object] = {
        "source_id": "telegram:vincent",
        "actor_id": "STK-vincent",
        "lawful_basis": "consent",
        "consent_scope": {
            "route_to_projects": True,
            "summarize": True,
            "extract_artifacts": False,
            "learning_signal": False,
            "remote_inference_allowed": False,
        },
        "retention_policy": "raw_30d",
        "current_state": "active",
        "granted_at": _NOW,
        "granted_by": "operator",
        "updated_at": _NOW,
    }
    data.update(overrides)
    return data


class _Conn:
    def transaction(self) -> Any:
        @asynccontextmanager
        async def _ctx() -> Any:
            yield None

        return _ctx()


class _Pool:
    def acquire(self) -> Any:
        @asynccontextmanager
        async def _ctx() -> Any:
            yield _Conn()

        return _ctx()

    async def close(self) -> None:
        return None


@pytest.fixture
def source_client() -> Iterator[TestClient]:
    async def _override() -> _Pool:
        return _Pool()

    def _auth_override() -> CallingIdentity:
        return CallingIdentity("operator")

    app.dependency_overrides[get_pool] = _override
    app.dependency_overrides[require_bearer_auth] = _auth_override
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.pop(get_pool, None)
        app.dependency_overrides.pop(require_bearer_auth, None)


def test_source_endpoint_requires_auth() -> None:
    async def _override() -> _Pool:
        return _Pool()

    app.dependency_overrides[get_pool] = _override
    try:
        response = TestClient(app).get("/v1/sources/telegram:vincent")
    finally:
        app.dependency_overrides.pop(get_pool, None)

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "auth_required"

def test_create_source_returns_201_and_created_record(
    monkeypatch: pytest.MonkeyPatch,
    source_client: TestClient,
) -> None:
    async def fake_register_source(_conn: object, **kwargs: object) -> dict[str, object]:
        assert kwargs["source_id"] == "telegram:vincent"
        assert kwargs["consent_scope"] == {"summarize": True}
        return _source(consent_scope={"summarize": True})

    monkeypatch.setattr("app.main.register_source", fake_register_source)

    response = source_client.post(
        "/v1/sources",
        json={
            "source_id": "telegram:vincent",
            "actor_id": "STK-vincent",
            "consent_scope": {"summarize": True},
            "retention_policy": "raw_30d",
            "granted_by": "operator",
        },
    )

    assert response.status_code == 201
    assert response.json()["source_id"] == "telegram:vincent"
    assert response.json()["current_state"] == "active"


def test_get_source_returns_404_for_unknown_source(
    monkeypatch: pytest.MonkeyPatch,
    source_client: TestClient,
) -> None:
    async def fake_get_source(_conn: object, source_id: str) -> None:
        assert source_id == "missing"
        return None

    monkeypatch.setattr("app.main.get_source", fake_get_source)

    response = source_client.get("/v1/sources/missing")

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "not_found"


def test_patch_source_requires_a_change(source_client: TestClient) -> None:
    response = source_client.patch("/v1/sources/telegram:vincent", json={})

    assert response.status_code == 422


def test_patch_source_returns_updated_record(
    monkeypatch: pytest.MonkeyPatch,
    source_client: TestClient,
) -> None:
    async def fake_update_source(_conn: object, **kwargs: object) -> dict[str, object]:
        assert kwargs["source_id"] == "telegram:vincent"
        assert kwargs["retention_policy"] == "derived_keep"
        return _source(retention_policy="derived_keep")

    monkeypatch.setattr("app.main.update_source", fake_update_source)

    response = source_client.patch(
        "/v1/sources/telegram:vincent",
        json={"retention_policy": "derived_keep", "changed_by": "operator"},
    )

    assert response.status_code == 200
    assert response.json()["retention_policy"] == "derived_keep"


def test_revoke_source_returns_revoked_record(
    monkeypatch: pytest.MonkeyPatch,
    source_client: TestClient,
) -> None:
    async def fake_revoke_source(_conn: object, **kwargs: object) -> dict[str, object]:
        assert kwargs["change_reason"] == "user withdrew consent"
        return _source(current_state="revoked")

    monkeypatch.setattr("app.main.revoke_source", fake_revoke_source)

    response = source_client.post(
        "/v1/sources/telegram:vincent/revoke",
        json={"change_reason": "user withdrew consent"},
    )

    assert response.status_code == 200
    assert response.json()["current_state"] == "revoked"


def test_history_supports_read_as_of_query(
    monkeypatch: pytest.MonkeyPatch,
    source_client: TestClient,
) -> None:
    async def fake_source_history(
        _conn: object,
        *,
        source_id: str,
        as_of: datetime | None,
    ) -> list[dict[str, object]]:
        assert source_id == "telegram:vincent"
        assert as_of == datetime(2026, 5, 7, 12, 30, tzinfo=UTC)
        return [
            {
                "history_id": UUID("00000000-0000-0000-0000-000000000001"),
                "source_id": source_id,
                "changed_at": _NOW,
                "prior_scope": None,
                "new_scope": {"summarize": True},
                "prior_retention": None,
                "new_retention": "raw_30d",
                "prior_state": None,
                "new_state": "active",
                "change_reason": "initial registration",
                "event_id": UUID("00000000-0000-0000-0000-000000000002"),
            }
        ]

    monkeypatch.setattr("app.main.source_history", fake_source_history)

    response = source_client.get(
        "/v1/sources/telegram:vincent/history?as_of=2026-05-07T12:30:00Z"
    )

    assert response.status_code == 200
    assert response.json()["items"][0]["new_state"] == "active"
