"""Shared test fixtures for backlog-core tests.

Provides a minimal in-process fake of `asyncpg.Pool` so the FastAPI app can
be exercised without a real Postgres process. Used both directly in tests
and as a `dependency_overrides` substitute for `app.db.get_pool`.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any
from uuid import uuid4

import pytest

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Iterator

    from fastapi.testclient import TestClient


class _FakeConnection:
    def __init__(self, fetchval_impl: Any, fetchrow_impl: Any, execute_impl: Any) -> None:
        self._fetchval_impl = fetchval_impl
        self._fetchrow_impl = fetchrow_impl
        self._execute_impl = execute_impl

    async def fetchval(self, sql: str, *args: Any) -> Any:
        return await self._fetchval_impl(sql, *args)

    async def fetchrow(self, sql: str, *args: Any) -> Any:
        return await self._fetchrow_impl(sql, *args)

    async def execute(self, sql: str, *args: Any) -> None:
        return await self._execute_impl(sql, *args)

    async def fetch(self, sql: str, *args: Any) -> list[dict[str, Any]]:
        return []

    @asynccontextmanager
    async def transaction(self) -> AsyncIterator[None]:
        yield


class FakePool:
    """In-process fake for `asyncpg.Pool`.

    `success=True` makes `SELECT 1` return 1; `success=False` makes the
    connection's `fetchval` raise to simulate a downstream Postgres failure.
    """

    def __init__(self, *, success: bool = True) -> None:
        self._success = success
        self.acquire_count = 0
        self.close_count = 0
        self.idempotency_store: dict[Any, dict[str, Any]] = {}

    def acquire(self) -> Any:
        self.acquire_count += 1
        success = self._success

        async def fetchval(sql: str, *args: Any) -> Any:
            if not success:
                raise RuntimeError("simulated connection failure")
            if sql.strip().upper() == "SELECT 1":
                return 1
            if "FROM events" in sql:
                return None
            return None

        async def fetchrow(sql: str, *args: Any) -> Any:
            if not success:
                raise RuntimeError("simulated connection failure")
            
            # Idempotency lookup
            if "FROM idempotency_keys" in sql:
                return self.idempotency_store.get(args[0])

            # Match register_source INSERT
            if "INSERT INTO events" in sql:
                return {
                    "event_id": args[0],
                    "created_at": args[2],
                    "payload_hash": args[8],
                    "prev_hash": args[9],
                    "hash": args[10],
                }
            
            # Match register_source INSERT for consent_sources
            if "INSERT INTO consent_sources" in sql:
                return {
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
            return None

        async def execute(sql: str, *args: Any) -> Any:
            if not success:
                raise RuntimeError("simulated connection failure")
            
            # Idempotency save
            if "INSERT INTO idempotency_keys" in sql:
                self.idempotency_store[args[0]] = {
                    "response_payload": args[1],
                    "response_status": args[2]
                }
            return "INSERT 0 1"

        @asynccontextmanager
        async def _ctx() -> Any:
            yield _FakeConnection(fetchval, fetchrow, execute)

        return _ctx()

    async def close(self) -> None:
        self.close_count += 1


@pytest.fixture
def fake_pool_ok() -> FakePool:
    return FakePool(success=True)


@pytest.fixture
def fake_pool_down() -> FakePool:
    return FakePool(success=False)


@pytest.fixture
def client_with_pool(fake_pool_ok: FakePool) -> Iterator[TestClient]:
    """A FastAPI TestClient whose `get_pool` dependency returns a healthy fake pool."""
    from fastapi.testclient import TestClient

    from app.db import get_pool
    from app.main import app

    async def _override() -> FakePool:
        return fake_pool_ok

    app.dependency_overrides[get_pool] = _override
    # Also attach it to app.state.pool for the middleware
    app.state.pool = fake_pool_ok
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.pop(get_pool, None)


@pytest.fixture
def client_with_down_pool(fake_pool_down: FakePool) -> Iterator[TestClient]:
    """A FastAPI TestClient whose `get_pool` dependency returns a failing fake pool."""
    from fastapi.testclient import TestClient

    from app.db import get_pool
    from app.main import app

    async def _override() -> FakePool:
        return fake_pool_down

    app.dependency_overrides[get_pool] = _override
    app.state.pool = fake_pool_down
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.pop(get_pool, None)
