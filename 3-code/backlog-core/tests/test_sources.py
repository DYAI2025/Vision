"""Unit tests for source-consent service functions."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any, cast
from uuid import UUID

import pytest

from app.sources import normalize_scope, register_source, revoke_source, update_source

_NOW = datetime(2026, 5, 7, 12, tzinfo=UTC)


class _SourceConn:
    def __init__(self) -> None:
        self.current_source: dict[str, Any] | None = None
        self.history_args: list[tuple[object, ...]] = []
        self.event_types: list[str] = []
        self.previous_hash: bytes | None = None

    async def execute(self, sql: str, *args: object) -> None:
        if "pg_advisory_xact_lock" in sql:
            return None
        if "INSERT INTO consent_history" in sql:
            self.history_args.append(args)
            return None
        raise AssertionError(f"unexpected execute SQL: {sql}")

    async def fetch(self, sql: str, *args: object) -> list[dict[str, Any]]:
        raise AssertionError(f"unexpected fetch SQL: {sql}")

    async def fetchrow(self, sql: str, *args: object) -> dict[str, Any] | None:
        if "SELECT hash" in sql:
            return {"hash": self.previous_hash} if self.previous_hash is not None else None
        if "INSERT INTO events" in sql:
            self.event_types.append(str(args[1]))
            return {
                "event_id": args[0],
                "created_at": args[2],
                "payload_hash": args[8],
                "prev_hash": args[9],
                "hash": args[10],
            }
        if "INSERT INTO consent_sources" in sql:
            self.current_source = {
                "source_id": args[0],
                "actor_id": args[1],
                "lawful_basis": "consent",
                "consent_scope": args[2],
                "retention_policy": args[3],
                "current_state": "active",
                "granted_at": args[4],
                "granted_by": args[5],
                "updated_at": args[4],
            }
            return self.current_source
        if "FROM consent_sources" in sql and "WHERE source_id" in sql:
            return self.current_source
        if "UPDATE consent_sources" in sql and "current_state = 'revoked'" in sql:
            assert self.current_source is not None
            self.current_source = {
                **self.current_source,
                "current_state": "revoked",
                "updated_at": args[1],
            }
            return self.current_source
        if "UPDATE consent_sources" in sql and "retention_policy" in sql:
            assert self.current_source is not None
            self.current_source = {
                **self.current_source,
                "consent_scope": args[1],
                "retention_policy": args[2],
                "updated_at": args[3],
            }
            return self.current_source
        raise AssertionError(f"unexpected fetchrow SQL: {sql}")


def test_normalize_scope_keeps_mvp_flags_default_false() -> None:
    scope = normalize_scope({"summarize": True})

    assert scope == {
        "route_to_projects": False,
        "summarize": True,
        "extract_artifacts": False,
        "learning_signal": False,
        "remote_inference_allowed": False,
    }


@pytest.mark.asyncio
async def test_register_source_emits_event_and_initial_history() -> None:
    conn = _SourceConn()

    source = await register_source(
        conn,
        source_id="telegram:vincent",
        actor_id="STK-vincent",
        consent_scope={"summarize": True},
        retention_policy="raw_30d",
        granted_by="operator",
        now=_NOW,
    )

    assert source["consent_scope"]["summarize"] is True
    assert source["consent_scope"]["route_to_projects"] is False
    assert conn.event_types == ["source.registered"]
    assert len(conn.history_args) == 1
    assert json.loads(cast(str, conn.history_args[0][3])) == source["consent_scope"]
    assert isinstance(conn.history_args[0][6], UUID)


@pytest.mark.asyncio
async def test_update_source_emits_update_history_with_prior_state() -> None:
    conn = _SourceConn()
    await register_source(
        conn,
        source_id="telegram:vincent",
        actor_id="STK-vincent",
        consent_scope={"summarize": True},
        retention_policy="raw_30d",
        granted_by="operator",
        now=_NOW,
    )

    source = await update_source(
        conn,
        source_id="telegram:vincent",
        consent_scope={"extract_artifacts": True},
        retention_policy="derived_keep",
        change_reason="operator expanded scope",
        actor_id="operator",
        now=datetime(2026, 5, 7, 13, tzinfo=UTC),
    )

    assert source is not None
    assert source["retention_policy"] == "derived_keep"
    assert source["consent_scope"]["extract_artifacts"] is True
    assert conn.event_types[-1] == "source.consent_updated"
    prior_scope = json.loads(cast(str, conn.history_args[-1][3]))
    new_scope = json.loads(cast(str, conn.history_args[-1][4]))
    assert prior_scope["summarize"] is True
    assert new_scope["extract_artifacts"] is True


@pytest.mark.asyncio
async def test_revoke_source_marks_source_revoked_and_appends_history() -> None:
    conn = _SourceConn()
    await register_source(
        conn,
        source_id="telegram:vincent",
        actor_id="STK-vincent",
        consent_scope={"summarize": True},
        retention_policy="raw_30d",
        granted_by="operator",
        now=_NOW,
    )

    source = await revoke_source(
        conn,
        source_id="telegram:vincent",
        change_reason="user withdrew consent",
        actor_id="operator",
        now=datetime(2026, 5, 7, 14, tzinfo=UTC),
    )

    assert source is not None
    assert source["current_state"] == "revoked"
    assert conn.event_types[-1] == "source.consent_revoked"
    assert conn.history_args[-1][5] == "active"
    assert conn.history_args[-1][6] == "user withdrew consent"
