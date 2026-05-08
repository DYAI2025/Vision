"""Idempotency store logic for backlog-core.

Per DEC-idempotency-keys.
Prevents duplicate processing of the same request identified by X-Idempotency-Key.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Protocol
from uuid import UUID

from pydantic import BaseModel


class IdempotencyRecord(BaseModel):
    """Stored response for an idempotency key."""
    payload: dict[str, Any]
    status_code: int


class _ConnectionLike(Protocol):
    """Subset of `asyncpg.Connection` we depend on."""
    async def fetchrow(self, sql: str, *args: Any) -> dict[str, Any] | None: ...
    async def execute(self, sql: str, *args: Any) -> None: ...


async def get_idempotent_response(conn: _ConnectionLike, key: UUID) -> IdempotencyRecord | None:
    """Retrieve a stored response for a given idempotency key."""
    row = await conn.fetchrow(
        "SELECT response_payload, response_status FROM idempotency_keys WHERE key = $1",
        key
    )
    if not row:
        return None
        
    return IdempotencyRecord(
        payload=json.loads(row["response_payload"]) if isinstance(row["response_payload"], str) else row["response_payload"],
        status_code=row["response_status"]
    )


async def save_idempotent_response(
    conn: _ConnectionLike, 
    key: UUID, 
    record: IdempotencyRecord
) -> None:
    """Store a response for a given idempotency key."""
    await conn.execute(
        """
        INSERT INTO idempotency_keys (key, response_payload, response_status, created_at)
        VALUES ($1, $2, $3, $4)
        ON CONFLICT (key) DO NOTHING
        """,
        key,
        json.dumps(record.payload),
        record.status_code,
        datetime.now(timezone.utc)
    )
