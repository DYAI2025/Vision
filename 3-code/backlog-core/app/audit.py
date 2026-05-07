"""Audit and chain verification for backlog-core.

Per TASK-hash-chain-verify and data-model.md.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Protocol

from pydantic import BaseModel

from app.events import compute_event_hash, compute_payload_hash


class VerificationResult(BaseModel):
    """Result of a hash-chain verification run."""

    valid: bool
    event_count: int = 0
    error_event_id: uuid.UUID | None = None
    error_message: str | None = None


class _ConnectionLike(Protocol):
    """Subset of `asyncpg.Connection` we depend on."""

    async def fetch(self, sql: str, *args: Any) -> list[dict[str, Any]]: ...


async def verify_chain(conn: _ConnectionLike, batch_size: int = 1000) -> VerificationResult:
    """Verify the cryptographic integrity of the append-only event log.

    1. Fetch events in batches (created_at, event_id).
    2. For each event:
        a. Verify `prev_hash` matches previous row's `hash`.
        b. Recompute `hash` from static fields + `payload_hash` and compare.
        c. If `payload` is not redacted (redacted=FALSE), verify `payload_hash`
           matches SHA-256 of the JSON payload.
    """
    current_prev_hash = b"\x00" * 32
    count = 0
    last_event_id: uuid.UUID | None = None
    last_created_at: datetime | None = None

    while True:
        if last_event_id and last_created_at:
            rows = await conn.fetch(
                """
                SELECT event_id, event_type, created_at, actor_id, payload,
                       payload_hash, prev_hash, hash, redacted
                FROM events
                WHERE (created_at, event_id) > ($1, $2)
                ORDER BY created_at ASC, event_id ASC
                LIMIT $3
                """,
                last_created_at,
                last_event_id,
                batch_size,
            )
        else:
            rows = await conn.fetch(
                """
                SELECT event_id, event_type, created_at, actor_id, payload,
                       payload_hash, prev_hash, hash, redacted
                FROM events
                ORDER BY created_at ASC, event_id ASC
                LIMIT $1
                """,
                batch_size,
            )

        if not rows:
            break

        for row in rows:
            event_id = row["event_id"]

            # 1. Verify prev_hash link
            if bytes(row["prev_hash"]) != current_prev_hash:
                return VerificationResult(
                    valid=False,
                    event_count=count,
                    error_event_id=event_id,
                    error_message=f"prev_hash mismatch: expected {current_prev_hash.hex()}, got {bytes(row['prev_hash']).hex()}",
                )

            # 2. Verify chain hash
            recomputed_hash = compute_event_hash(
                event_id=event_id,
                event_type=row["event_type"],
                created_at=row["created_at"],
                actor_id=row["actor_id"],
                payload_hash=bytes(row["payload_hash"]),
                prev_hash=bytes(row["prev_hash"]),
            )

            if bytes(row["hash"]) != recomputed_hash:
                return VerificationResult(
                    valid=False,
                    event_count=count,
                    error_event_id=event_id,
                    error_message=f"hash mismatch: expected {bytes(row['hash']).hex()}, got {recomputed_hash.hex()}",
                )

            # 3. Verify payload integrity (only if not redacted)
            if not row["redacted"] and row["payload"] is not None:
                p_hash = compute_payload_hash(row["payload"])
                if p_hash != bytes(row["payload_hash"]):
                    return VerificationResult(
                        valid=False,
                        event_count=count,
                        error_event_id=event_id,
                        error_message="payload_hash mismatch (payload was tampered with)",
                    )

            current_prev_hash = bytes(row["hash"])
            count += 1
            last_event_id = event_id
            last_created_at = row["created_at"]

        if len(rows) < batch_size:
            break

    return VerificationResult(valid=True, event_count=count)


async def query_audit(
    conn: _ConnectionLike, after: uuid.UUID | None = None, limit: int = 50
) -> list[dict[str, Any]]:
    """Query the audit log with cursor-based pagination.

    Uses event_id (UUIDv7) as the cursor since it is time-sortable and unique.
    """
    if after:
        rows = await conn.fetch(
            "SELECT * FROM events WHERE event_id > $1 ORDER BY event_id ASC LIMIT $2",
            after,
            limit,
        )
    else:
        rows = await conn.fetch(
            "SELECT * FROM events ORDER BY event_id ASC LIMIT $1", limit
        )
    return [dict(row) for row in rows]
