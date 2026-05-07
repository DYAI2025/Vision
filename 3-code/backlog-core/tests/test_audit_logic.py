"""Tests for the backlog-core audit verification logic."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

import pytest

from app.audit import verify_chain
from app.events import ZERO_HASH, compute_event_hash, compute_payload_hash


class _FakeConn:
    def __init__(self, rows: list[dict[str, object]]) -> None:
        self.rows = rows

    async def fetch(self, sql: str, *args: object) -> list[dict[str, object]]:
        # This is a very simple fake that doesn't respect the SQL filters,
        # but for unit testing the logic on a fixed set of rows it's enough.
        # The verify_chain uses batching, so we need to handle the LIMIT/OFFSET
        # correctly if we want to test batch transitions.
        if "LIMIT" in sql:
            # Simple batching simulation
            return self.rows # For simplicity in unit tests
        return self.rows


@pytest.mark.asyncio
async def test_verify_chain_returns_valid_for_empty_table() -> None:
    conn = _FakeConn([])
    result = await verify_chain(conn)
    assert result.valid is True
    assert result.event_count == 0


@pytest.mark.asyncio
async def test_verify_chain_detects_prev_hash_mismatch() -> None:
    event_id = UUID("00000000-0000-0000-0000-000000000001")
    created_at = datetime(2026, 5, 7, 12, tzinfo=UTC)
    payload = {"a": 1}
    p_hash = compute_payload_hash(payload)
    
    # Valid row
    h = compute_event_hash(
        event_id=event_id,
        event_type="t",
        created_at=created_at,
        actor_id="a",
        payload_hash=p_hash,
        prev_hash=ZERO_HASH
    )
    
    row = {
        "event_id": event_id,
        "event_type": "t",
        "created_at": created_at,
        "actor_id": "a",
        "payload": payload,
        "payload_hash": p_hash,
        "prev_hash": b"wrong", # Mismatch!
        "hash": h,
        "redacted": False
    }
    
    conn = _FakeConn([row])
    result = await verify_chain(conn)
    assert result.valid is False
    assert "prev_hash mismatch" in result.error_message


@pytest.mark.asyncio
async def test_verify_chain_detects_hash_tampering() -> None:
    event_id = UUID("00000000-0000-0000-0000-000000000001")
    created_at = datetime(2026, 5, 7, 12, tzinfo=UTC)
    payload = {"a": 1}
    p_hash = compute_payload_hash(payload)
    
    row = {
        "event_id": event_id,
        "event_type": "t",
        "created_at": created_at,
        "actor_id": "a",
        "payload": payload,
        "payload_hash": p_hash,
        "prev_hash": ZERO_HASH,
        "hash": b"tampered",
        "redacted": False
    }
    
    conn = _FakeConn([row])
    result = await verify_chain(conn)
    assert result.valid is False
    assert "hash mismatch" in result.error_message
