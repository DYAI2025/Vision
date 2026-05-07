"""Integration tests for the audit API endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from bearer_auth import CallingIdentity, require_bearer_auth
from app.db import get_pool
from app.main import app

if TYPE_CHECKING:
    from collections.abc import Iterator


class _Pool:
    def acquire(self) -> Any:
        from contextlib import asynccontextmanager
        @asynccontextmanager
        async def _ctx() -> Any:
            # Mock connection that supports fetch
            class _Conn:
                async def fetch(self, sql: str, *args: Any) -> list[Any]:
                    return []
            yield _Conn()
        return _ctx()

    async def close(self) -> None:
        return None


@pytest.fixture
def audit_client() -> Iterator[TestClient]:
    async def _pool_override() -> _Pool:
        return _Pool()

    def _auth_override() -> CallingIdentity:
        return CallingIdentity("operator")

    app.dependency_overrides[get_pool] = _pool_override
    app.dependency_overrides[require_bearer_auth] = _auth_override
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.pop(get_pool, None)
        app.dependency_overrides.pop(require_bearer_auth, None)


@pytest.mark.asyncio
async def test_get_audit_query_requires_auth() -> None:
    # Use a client with pool override but WITHOUT auth override
    async def _pool_override() -> _Pool:
        return _Pool()
    
    app.dependency_overrides[get_pool] = _pool_override
    try:
        response = TestClient(app).get("/v1/audit/query")
    finally:
        app.dependency_overrides.pop(get_pool, None)
        
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_get_audit_query_success(audit_client: TestClient) -> None:
    response = audit_client.get("/v1/audit/query")
    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_post_audit_verify_success(audit_client: TestClient) -> None:
    response = audit_client.post("/v1/audit/verify-chain")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["valid"] is True
