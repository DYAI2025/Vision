"""Unit tests for app.db's connection-lifecycle and ping primitives."""

from __future__ import annotations

import pytest

from app.db import _database_url, ping
from tests.conftest import FakePool


def test_database_url_returns_value_when_set(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgres://u:p@h:5432/d")
    assert _database_url() == "postgres://u:p@h:5432/d"


def test_database_url_raises_when_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(RuntimeError, match="DATABASE_URL is required"):
        _database_url()


def test_pool_size_returns_defaults_when_env_unset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("BACKLOG_CORE_DB_POOL_MIN", raising=False)
    monkeypatch.delenv("BACKLOG_CORE_DB_POOL_MAX", raising=False)

    from app.db import _pool_size

    assert _pool_size() == (1, 10)


def test_pool_size_reads_env_overrides(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BACKLOG_CORE_DB_POOL_MIN", "4")
    monkeypatch.setenv("BACKLOG_CORE_DB_POOL_MAX", "32")

    from app.db import _pool_size

    assert _pool_size() == (4, 32)


def test_pool_size_rejects_min_greater_than_max(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("BACKLOG_CORE_DB_POOL_MIN", "20")
    monkeypatch.setenv("BACKLOG_CORE_DB_POOL_MAX", "10")

    from app.db import _pool_size

    with pytest.raises(RuntimeError, match=r"POOL_MIN.*exceeds.*POOL_MAX"):
        _pool_size()


async def test_ping_returns_true_on_select_one_success() -> None:
    pool = FakePool(success=True)
    assert await ping(pool) is True
    assert pool.acquire_count == 1


async def test_ping_returns_false_when_connection_raises() -> None:
    pool = FakePool(success=False)
    assert await ping(pool) is False


async def test_ping_returns_false_on_acquire_exception() -> None:
    """ping() must never raise — it always returns a bool."""

    class BrokenPool:
        def acquire(self) -> object:
            raise RuntimeError("acquire blew up")

        async def close(self) -> None:
            return None

    assert await ping(BrokenPool()) is False
