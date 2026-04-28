"""Shared test fixtures for backlog-core tests.

Provides a minimal in-process fake of `asyncpg.Pool` so the FastAPI app can
be exercised without a real Postgres process. Used both directly in tests
and as a `dependency_overrides` substitute for `app.main._pool_dependency`.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Any

import pytest

if TYPE_CHECKING:
    from collections.abc import Iterator


class _FakeConnection:
    def __init__(self, fetchval_impl: Any) -> None:
        self._fetchval_impl = fetchval_impl

    async def fetchval(self, sql: str) -> Any:
        return await self._fetchval_impl(sql)


class FakePool:
    """In-process fake for `asyncpg.Pool`.

    `success=True` makes `SELECT 1` return 1; `success=False` makes the
    connection's `fetchval` raise to simulate a downstream Postgres failure.
    """

    def __init__(self, *, success: bool = True) -> None:
        self._success = success
        self.acquire_count = 0
        self.close_count = 0

    def acquire(self) -> Any:
        self.acquire_count += 1
        success = self._success

        async def fetchval(sql: str) -> Any:
            if not success:
                raise RuntimeError("simulated connection failure")
            if sql.strip().upper() == "SELECT 1":
                return 1
            return None

        @asynccontextmanager
        async def _ctx() -> Any:
            yield _FakeConnection(fetchval)

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
def client_with_pool(fake_pool_ok: FakePool) -> Iterator[Any]:
    """A FastAPI TestClient whose `get_pool` dependency returns a healthy fake pool."""
    from fastapi.testclient import TestClient

    from app.db import get_pool
    from app.main import app

    async def _override() -> FakePool:
        return fake_pool_ok

    app.dependency_overrides[get_pool] = _override
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.pop(get_pool, None)
