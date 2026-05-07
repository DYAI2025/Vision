"""Source-consent service functions for backlog-core."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from canonical_json import canonical_json_str

from app.events import emit_event

DEFAULT_CONSENT_SCOPE: dict[str, bool] = {
    "route_to_projects": False,
    "summarize": False,
    "extract_artifacts": False,
    "learning_signal": False,
    "remote_inference_allowed": False,
}


def normalize_scope(scope: dict[str, bool] | None) -> dict[str, bool]:
    """Merge caller-supplied scope with the MVP default-false flags."""
    merged = dict(DEFAULT_CONSENT_SCOPE)
    if scope:
        merged.update(scope)
    return merged


def _json_object(value: Any) -> dict[str, Any]:
    if isinstance(value, str):
        loaded = json.loads(value)
        if isinstance(loaded, dict):
            return loaded
        raise ValueError("JSONB value must decode to an object")
    return dict(value)


def _row_to_source(row: Any) -> dict[str, Any]:
    return {
        "source_id": row["source_id"],
        "actor_id": row["actor_id"],
        "lawful_basis": row["lawful_basis"],
        "consent_scope": _json_object(row["consent_scope"]),
        "retention_policy": row["retention_policy"],
        "current_state": row["current_state"],
        "granted_at": row["granted_at"],
        "granted_by": row["granted_by"],
        "updated_at": row["updated_at"],
    }


def _row_to_history(row: Any) -> dict[str, Any]:
    return {
        "history_id": row["history_id"],
        "source_id": row["source_id"],
        "changed_at": row["changed_at"],
        "prior_scope": _json_object(row["prior_scope"]) if row["prior_scope"] is not None else None,
        "new_scope": _json_object(row["new_scope"]),
        "prior_retention": row["prior_retention"],
        "new_retention": row["new_retention"],
        "prior_state": row["prior_state"],
        "new_state": row["new_state"],
        "change_reason": row["change_reason"],
        "event_id": row["event_id"],
    }


async def register_source(
    conn: Any,
    *,
    source_id: str,
    actor_id: str,
    consent_scope: dict[str, bool],
    retention_policy: str,
    granted_by: str,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Register a source, emit ``source.registered``, and append first history row."""
    now = now or datetime.now(UTC)
    scope = normalize_scope(consent_scope)
    payload = {
        "source_id": source_id,
        "actor_id": actor_id,
        "consent_scope": scope,
        "retention_policy": retention_policy,
        "granted_at": now.isoformat(),
        "granted_by": granted_by,
    }
    event = await emit_event(
        conn,
        event_type="source.registered",
        actor_id=granted_by,
        payload=payload,
        created_at=now,
    )
    source_row = await conn.fetchrow(
        """
        INSERT INTO consent_sources (
            source_id, actor_id, lawful_basis, consent_scope, retention_policy,
            current_state, granted_at, granted_by, updated_at
        )
        VALUES ($1, $2, 'consent', $3::jsonb, $4, 'active', $5, $6, $5)
        RETURNING source_id, actor_id, lawful_basis, consent_scope, retention_policy,
                  current_state, granted_at, granted_by, updated_at
        """,
        source_id,
        actor_id,
        canonical_json_str(scope),
        retention_policy,
        now,
        granted_by,
    )
    await conn.execute(
        """
        INSERT INTO consent_history (
            history_id, source_id, changed_at, prior_scope, new_scope,
            prior_retention, new_retention, prior_state, new_state,
            change_reason, event_id
        )
        VALUES ($1, $2, $3, NULL, $4::jsonb, NULL, $5, NULL, 'active', $6, $7)
        """,
        uuid4(),
        source_id,
        now,
        canonical_json_str(scope),
        retention_policy,
        "initial registration",
        event.event_id,
    )
    return _row_to_source(source_row)


async def get_source(conn: Any, source_id: str) -> dict[str, Any] | None:
    row = await conn.fetchrow(
        """
        SELECT source_id, actor_id, lawful_basis, consent_scope, retention_policy,
               current_state, granted_at, granted_by, updated_at
        FROM consent_sources
        WHERE source_id = $1
        """,
        source_id,
    )
    return _row_to_source(row) if row else None


async def list_sources(
    conn: Any,
    *,
    status: str | None = None,
    actor_id: str | None = None,
) -> list[dict[str, Any]]:
    rows = await conn.fetch(
        """
        SELECT source_id, actor_id, lawful_basis, consent_scope, retention_policy,
               current_state, granted_at, granted_by, updated_at
        FROM consent_sources
        WHERE ($1::text IS NULL OR current_state = $1)
          AND ($2::text IS NULL OR actor_id = $2)
        ORDER BY updated_at DESC, source_id ASC
        LIMIT 500
        """,
        status,
        actor_id,
    )
    return [_row_to_source(row) for row in rows]


async def update_source(
    conn: Any,
    *,
    source_id: str,
    consent_scope: dict[str, bool] | None,
    retention_policy: str | None,
    change_reason: str | None,
    actor_id: str,
    now: datetime | None = None,
) -> dict[str, Any] | None:
    now = now or datetime.now(UTC)
    current = await get_source(conn, source_id)
    if current is None:
        return None
    new_scope = (
        normalize_scope(consent_scope)
        if consent_scope is not None
        else current["consent_scope"]
    )
    new_retention = retention_policy or current["retention_policy"]
    payload = {
        "source_id": source_id,
        "prior_scope": current["consent_scope"],
        "new_scope": new_scope,
        "prior_retention": current["retention_policy"],
        "new_retention": new_retention,
        "change_reason": change_reason,
    }
    event = await emit_event(
        conn,
        event_type="source.consent_updated",
        actor_id=actor_id,
        payload=payload,
        created_at=now,
    )
    source_row = await conn.fetchrow(
        """
        UPDATE consent_sources
        SET consent_scope = $2::jsonb, retention_policy = $3, updated_at = $4
        WHERE source_id = $1
        RETURNING source_id, actor_id, lawful_basis, consent_scope, retention_policy,
                  current_state, granted_at, granted_by, updated_at
        """,
        source_id,
        canonical_json_str(new_scope),
        new_retention,
        now,
    )
    await conn.execute(
        """
        INSERT INTO consent_history (
            history_id, source_id, changed_at, prior_scope, new_scope,
            prior_retention, new_retention, prior_state, new_state,
            change_reason, event_id
        )
        VALUES ($1, $2, $3, $4::jsonb, $5::jsonb, $6, $7, $8, $9, $10, $11)
        """,
        uuid4(),
        source_id,
        now,
        canonical_json_str(current["consent_scope"]),
        canonical_json_str(new_scope),
        current["retention_policy"],
        new_retention,
        current["current_state"],
        current["current_state"],
        change_reason,
        event.event_id,
    )
    return _row_to_source(source_row)


async def revoke_source(
    conn: Any,
    *,
    source_id: str,
    change_reason: str | None,
    actor_id: str,
    now: datetime | None = None,
) -> dict[str, Any] | None:
    now = now or datetime.now(UTC)
    current = await get_source(conn, source_id)
    if current is None:
        return None
    payload = {
        "source_id": source_id,
        "prior_scope": current["consent_scope"],
        "prior_state": current["current_state"],
        "change_reason": change_reason,
    }
    event = await emit_event(
        conn,
        event_type="source.consent_revoked",
        actor_id=actor_id,
        payload=payload,
        created_at=now,
    )
    source_row = await conn.fetchrow(
        """
        UPDATE consent_sources
        SET current_state = 'revoked', updated_at = $2
        WHERE source_id = $1
        RETURNING source_id, actor_id, lawful_basis, consent_scope, retention_policy,
                  current_state, granted_at, granted_by, updated_at
        """,
        source_id,
        now,
    )
    await conn.execute(
        """
        INSERT INTO consent_history (
            history_id, source_id, changed_at, prior_scope, new_scope,
            prior_retention, new_retention, prior_state, new_state,
            change_reason, event_id
        )
        VALUES ($1, $2, $3, $4::jsonb, $4::jsonb, $5, $5, $6, 'revoked', $7, $8)
        """,
        uuid4(),
        source_id,
        now,
        canonical_json_str(current["consent_scope"]),
        current["retention_policy"],
        current["current_state"],
        change_reason,
        event.event_id,
    )
    return _row_to_source(source_row)


async def source_history(
    conn: Any,
    *,
    source_id: str,
    as_of: datetime | None = None,
) -> list[dict[str, Any]]:
    if as_of is None:
        rows = await conn.fetch(
            """
            SELECT history_id, source_id, changed_at, prior_scope, new_scope,
                   prior_retention, new_retention, prior_state, new_state,
                   change_reason, event_id
            FROM consent_history
            WHERE source_id = $1
            ORDER BY changed_at ASC, history_id ASC
            """,
            source_id,
        )
    else:
        rows = await conn.fetch(
            """
            SELECT history_id, source_id, changed_at, prior_scope, new_scope,
                   prior_retention, new_retention, prior_state, new_state,
                   change_reason, event_id
            FROM consent_history
            WHERE source_id = $1 AND changed_at <= $2
            ORDER BY changed_at DESC, history_id DESC
            LIMIT 1
            """,
            source_id,
            as_of,
        )
    return [_row_to_history(row) for row in rows]
