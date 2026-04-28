"""Postgres connection lifecycle and health primitives.

Skeleton-level (TASK-backlog-core-skeleton). The pool is created at FastAPI
startup via `lifespan` and closed at shutdown. Future tasks layer the event
schema, idempotency store, hash-chained audit log, RTBF cascade, etc. on top.

Per `DEC-postgres-as-event-store` and `DEC-backend-stack-python-fastapi`,
the driver is asyncpg.
"""

from __future__ import annotations

import os
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from typing import TYPE_CHECKING, Any, Protocol, cast

import asyncpg
from fastapi import Request  # noqa: TCH002 — FastAPI resolves param types at runtime

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from fastapi import FastAPI


class _PoolLike(Protocol):
    """Subset of `asyncpg.Pool` we depend on. Lets tests substitute fakes."""

    def acquire(self) -> AbstractAsyncContextManager[Any]: ...

    async def close(self) -> None: ...


DEFAULT_POOL_MIN = 1
DEFAULT_POOL_MAX = 10


def _database_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError(
            "DATABASE_URL is required — backlog-core fails fast per REQ-MNT-env-driven-config."
        )
    return url


def _pool_size() -> tuple[int, int]:
    """Read pool sizing from env with safe defaults; validate min <= max."""
    min_size = int(os.environ.get("BACKLOG_CORE_DB_POOL_MIN", DEFAULT_POOL_MIN))
    max_size = int(os.environ.get("BACKLOG_CORE_DB_POOL_MAX", DEFAULT_POOL_MAX))
    if min_size > max_size:
        raise RuntimeError(
            f"BACKLOG_CORE_DB_POOL_MIN ({min_size}) exceeds "
            f"BACKLOG_CORE_DB_POOL_MAX ({max_size}) — refusing to start."
        )
    return min_size, max_size


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Create the connection pool on startup; close it on shutdown."""
    min_size, max_size = _pool_size()
    pool = await asyncpg.create_pool(
        dsn=_database_url(), min_size=min_size, max_size=max_size
    )
    app.state.pool = pool
    try:
        yield
    finally:
        await pool.close()


async def get_pool(request: Request) -> _PoolLike:
    """FastAPI dependency: returns the pool created by `lifespan`.

    Raises if the lifespan didn't run (e.g., default TestClient usage). Tests
    that don't go through lifespan must override this dependency.
    """
    pool: Any = getattr(request.app.state, "pool", None)
    if pool is None:
        raise RuntimeError(
            "connection pool not initialized — lifespan must run, "
            "or get_pool must be overridden in tests"
        )
    return cast(_PoolLike, pool)


async def ping(pool: _PoolLike) -> bool:
    """Return True if the pool can complete a `SELECT 1`. Never raises."""
    try:
        async with pool.acquire() as conn:
            value: Any = await conn.fetchval("SELECT 1")
            return bool(value == 1)
    except Exception:
        return False
