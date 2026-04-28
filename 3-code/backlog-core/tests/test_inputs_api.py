from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi.testclient import TestClient


def test_post_input_event_and_list_recent(client_with_pool: TestClient) -> None:
    payload = {
        "event_id": "evt-00000001",
        "source_id": "src-1",
        "actor_id": "ben",
        "project_hint": "vision",
        "channel": "manual_cli",
        "message_text": "Capture this requirement.",
        "happened_at": "2026-04-28T00:00:00Z",
        "channel_metadata": {},
    }

    created = client_with_pool.post("/v1/inputs", json=payload)
    assert created.status_code == 201
    assert created.json()["event_id"] == payload["event_id"]

    recent = client_with_pool.get("/v1/inputs/recent")
    assert recent.status_code == 200
    assert any(item["event_id"] == payload["event_id"] for item in recent.json())


def test_post_input_rejects_conflicting_idempotency_key(client_with_pool: TestClient) -> None:
    payload = {
        "event_id": "evt-00000002",
        "source_id": "src-1",
        "actor_id": "ben",
        "channel": "manual_cli",
        "message_text": "Capture this requirement.",
        "happened_at": "2026-04-28T00:00:00Z",
        "channel_metadata": {},
    }
    response = client_with_pool.post(
        "/v1/inputs",
        json=payload,
        headers={"Idempotency-Key": "another-id"},
    )
    assert response.status_code == 409
