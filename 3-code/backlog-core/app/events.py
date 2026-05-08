"""Event-emission primitive for backlog-core.

The primitive owns the audit-log hash-chain mechanics for every write path:
callers provide the event semantics, and this module computes canonical
``payload_hash``, links to the previous event hash, inserts the row, and
returns the persisted audit identity.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import hashlib
from typing import Any, Protocol
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from canonical_json import canonical_json, canonical_json_str

ZERO_HASH = b"\x00" * 32


@dataclass(frozen=True)
class EmittedEvent:
    """Identity and hash material returned after inserting an event."""

    event_id: UUID
    created_at: datetime
    payload_hash: bytes
    prev_hash: bytes
    hash: bytes


class EventEmitRequest(BaseModel):
    """Payload for emitting a new event."""

    event_type: str
    actor_id: str
    proposal_id: UUID | None = None
    source_input_event_id: UUID | None = None
    subject_ref: str | None = None
    payload: dict[str, Any] | None = None
    retention_class: str = "audit_kept"


class _ConnectionLike(Protocol):
    """Subset of `asyncpg.Connection` we depend on."""

    async def fetchval(self, sql: str, *args: Any) -> Any: ...
    async def fetchrow(self, sql: str, *args: Any) -> Any: ...
    async def execute(self, sql: str, *args: Any) -> Any: ...


def _utc_iso(value: datetime) -> str:
    """Return a stable UTC ISO-8601 timestamp string for hash material."""
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC).isoformat(timespec="microseconds")


def compute_payload_hash(payload: Any) -> bytes:
    """Compute SHA-256 over the canonical JSON representation of a payload."""
    return hashlib.sha256(canonical_json(payload)).digest()


def compute_event_hash(
    *,
    event_id: UUID,
    event_type: str,
    created_at: datetime,
    actor_id: str,
    payload_hash: bytes,
    prev_hash: bytes,
) -> bytes:
    """Compute the event hash stored in ``events.hash``."""
    material = {
        "actor_id": actor_id,
        "created_at": _utc_iso(created_at),
        "event_id": str(event_id),
        "event_type": event_type,
        "payload_hash": payload_hash.hex(),
        "prev_hash": prev_hash.hex(),
    }
    return hashlib.sha256(canonical_json(material)).digest()


async def emit(conn: _ConnectionLike, req: EventEmitRequest) -> UUID:
    """Append one hash-chained event using an EventEmitRequest object."""
    return (await _emit_core(
        conn,
        event_type=req.event_type,
        actor_id=req.actor_id,
        payload=req.payload,
        retention_class=req.retention_class,
        proposal_id=req.proposal_id,
        source_input_event_id=req.source_input_event_id,
        subject_ref=req.subject_ref
    )).event_id


async def emit_event(
    conn: _ConnectionLike,
    *,
    event_type: str,
    actor_id: str,
    payload: dict[str, Any],
    retention_class: str = "audit_kept",
    event_id: UUID | None = None,
    created_at: datetime | None = None,
    proposal_id: UUID | None = None,
    source_input_event_id: UUID | None = None,
    subject_ref: str | None = None,
) -> EmittedEvent:
    """Append one hash-chained event using individual parameters (Legacy API)."""
    return await _emit_core(
        conn,
        event_type=event_type,
        actor_id=actor_id,
        payload=payload,
        retention_class=retention_class,
        event_id=event_id,
        created_at=created_at,
        proposal_id=proposal_id,
        source_input_event_id=source_input_event_id,
        subject_ref=subject_ref
    )


async def _emit_core(
    conn: _ConnectionLike,
    *,
    event_type: str,
    actor_id: str,
    payload: dict[str, Any] | None,
    retention_class: str,
    event_id: UUID | None = None,
    created_at: datetime | None = None,
    proposal_id: UUID | None = None,
    source_input_event_id: UUID | None = None,
    subject_ref: str | None = None,
) -> EmittedEvent:
    """Core logic for appending a hash-chained event."""
    event_id = event_id or uuid4()
    created_at = created_at or datetime.now(UTC)
    payload_data = payload or {}
    payload_hash = compute_payload_hash(payload_data)

    # Advisory lock to prevent race conditions on prev_hash
    await conn.execute("SELECT pg_advisory_xact_lock(hashtext('backlog_core_events_chain'))")

    previous = await conn.fetchrow(
        "SELECT hash FROM events ORDER BY created_at DESC, event_id DESC LIMIT 1"
    )
    prev_hash = bytes(previous["hash"]) if previous else ZERO_HASH

    chain_hash = compute_event_hash(
        event_id=event_id,
        event_type=event_type,
        created_at=created_at,
        actor_id=actor_id,
        payload_hash=payload_hash,
        prev_hash=prev_hash,
    )

    row = await conn.fetchrow(
        """
        INSERT INTO events (
            event_id, event_type, created_at, actor_id, proposal_id,
            source_input_event_id, subject_ref, payload, payload_hash,
            prev_hash, hash, retention_class
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
        RETURNING event_id, created_at, payload_hash, prev_hash, hash
        """,
        event_id,
        event_type,
        created_at,
        actor_id,
        proposal_id,
        source_input_event_id,
        subject_ref,
        canonical_json_str(payload_data),
        payload_hash,
        prev_hash,
        chain_hash,
        retention_class,
    )

    return EmittedEvent(
        event_id=row["event_id"],
        created_at=row["created_at"],
        payload_hash=bytes(row["payload_hash"]),
        prev_hash=bytes(row["prev_hash"]),
        hash=bytes(row["hash"]),
    )
