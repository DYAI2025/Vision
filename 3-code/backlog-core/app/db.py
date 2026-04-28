"""Postgres connection lifecycle and health primitives.

Skeleton-level (TASK-backlog-core-skeleton). The pool is created at FastAPI
startup via `lifespan` and closed at shutdown. Future tasks layer the event
schema, idempotency store, hash-chained audit log, RTBF cascade, etc. on top.

Per `DEC-postgres-as-event-store` and `DEC-backend-stack-python-fastapi`,
the driver is asyncpg.
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Any, Protocol, cast

import asyncpg

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from fastapi import FastAPI


class _PoolLike(Protocol):
    """Subset of `asyncpg.Pool` we depend on. Lets tests substitute fakes."""

    def acquire(self) -> object: ...

    async def close(self) -> None: ...


def _database_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError(
            "DATABASE_URL is required — backlog-core fails fast per REQ-MNT-env-driven-config."
        )
    return url


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Create the connection pool on startup; close it on shutdown."""
    pool = await asyncpg.create_pool(dsn=_database_url(), min_size=1, max_size=10)
    app.state.pool = pool
    try:
        yield
    finally:
        await pool.close()


async def get_pool(app: FastAPI) -> _PoolLike:
    """FastAPI dependency: returns the pool created by `lifespan`.

    Raises if the lifespan didn't run (e.g., default TestClient usage). Tests
    that don't go through lifespan must override this dependency.
    """
    pool: Any = getattr(app.state, "pool", None)
    if pool is None:
        raise RuntimeError(
            "connection pool not initialized — lifespan must run, "
            "or get_pool must be overridden in tests"
        )
    return cast(_PoolLike, pool)


async def ping(pool: _PoolLike) -> bool:
    """Return True if the pool can complete a `SELECT 1`. Never raises."""
    try:
        async with pool.acquire() as conn:  # type: ignore[attr-defined]
            value: Any = await conn.fetchval("SELECT 1")
            return bool(value == 1)
    except Exception:
        return False
