from __future__ import annotations

from typing import Any

import httpx
from fastapi.testclient import TestClient

from app.main import app


class _FakeResponse:
    def __init__(self) -> None:
        self._payload = {"event_id": "abc", "stored_at": "2026-01-01T00:00:00Z"}

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict[str, str]:
        return self._payload


async def _fake_post(
    self: httpx.AsyncClient,
    url: str,
    *,
    json: dict[str, object],
    headers: dict[str, str],
) -> _FakeResponse:
    assert url.endswith("/v1/inputs")
    assert headers["Idempotency-Key"] == json["event_id"]
    return _FakeResponse()


def test_manual_ingest_normalizes_and_forwards(
    monkeypatch: Any,
) -> None:
    monkeypatch.setattr(httpx.AsyncClient, "post", _fake_post)
    client = TestClient(app)

    response = client.post(
        "/v1/ingest/manual",
        json={
            "source_id": "src-1",
            "actor_id": "vincent",
            "message_text": "Please create a ticket for release prep.",
            "project_hint": "vision",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["normalized_event"]["channel"] == "manual_cli"
    assert payload["backlog_result"]["event_id"] == "abc"
