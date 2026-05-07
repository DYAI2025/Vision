"""Tests for the backlog-core event-emission primitive."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

import pytest

from app.events import ZERO_HASH, compute_event_hash, compute_payload_hash, emit_event


class _FakeConn:
    def __init__(self) -> None:
        self.executed: list[str] = []
        self.previous_hash: bytes | None = None
        self.insert_args: tuple[object, ...] | None = None

    async def execute(self, sql: str, *args: object) -> None:
        self.executed.append(sql)

    async def fetchrow(self, sql: str, *args: object) -> dict[str, object] | None:
        if "SELECT hash" in sql:
            return {"hash": self.previous_hash} if self.previous_hash is not None else None
        if "INSERT INTO events" in sql:
            self.insert_args = args
            return {
                "event_id": args[0],
                "created_at": args[2],
                "payload_hash": args[8],
                "prev_hash": args[9],
                "hash": args[10],
            }
        raise AssertionError(f"unexpected SQL: {sql}")


def test_payload_hash_is_stable_for_key_order() -> None:
    assert compute_payload_hash({"b": 2, "a": 1}) == compute_payload_hash({"a": 1, "b": 2})


def test_event_hash_changes_when_previous_hash_changes() -> None:
    event_id = UUID("00000000-0000-0000-0000-000000000001")
    created_at = datetime(2026, 5, 7, 12, tzinfo=UTC)
    payload_hash = compute_payload_hash({"source_id": "source-1"})

    first = compute_event_hash(
        event_id=event_id,
        event_type="source.registered",
        created_at=created_at,
        actor_id="operator",
        payload_hash=payload_hash,
        prev_hash=ZERO_HASH,
    )
    second = compute_event_hash(
        event_id=event_id,
        event_type="source.registered",
        created_at=created_at,
        actor_id="operator",
        payload_hash=payload_hash,
        prev_hash=b"\x01" * 32,
    )

    assert first != second


@pytest.mark.asyncio
async def test_emit_event_locks_chain_and_inserts_hash_material() -> None:
    conn = _FakeConn()
    event_id = UUID("00000000-0000-0000-0000-000000000002")
    created_at = datetime(2026, 5, 7, 13, tzinfo=UTC)

    event = await emit_event(
        conn,
        event_id=event_id,
        event_type="source.registered",
        actor_id="operator",
        payload={"source_id": "source-1"},
        created_at=created_at,
    )

    assert "pg_advisory_xact_lock" in conn.executed[0]
    assert conn.insert_args is not None
    assert conn.insert_args[0] == event_id
    assert conn.insert_args[1] == "source.registered"
    assert conn.insert_args[8] == event.payload_hash
    assert conn.insert_args[9] == ZERO_HASH
    assert conn.insert_args[10] == event.hash
