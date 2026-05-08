"""Tests for idempotency logic in backlog-core."""

from __future__ import annotations

import uuid
from typing import Any

import pytest
from fastapi import FastAPI, Request, Depends
from fastapi.testclient import TestClient
from app.idempotency import IdempotencyRecord, get_idempotent_response, save_idempotent_response
from app.main import app
from app.db import get_pool
from bearer_auth import CallingIdentity, require_bearer_auth


class _FakeConn:
    def __init__(self) -> None:
        self.keys: dict[uuid.UUID, dict[str, Any]] = {}

    async def fetchrow(self, sql: str, *args: Any) -> dict[str, Any] | None:
        return self.keys.get(args[0])

    async def execute(self, sql: str, *args: Any) -> None:
        self.keys[args[0]] = {
            "response_payload": args[1],
            "response_status": args[2]
        }


@pytest.mark.asyncio
async def test_idempotency_store_cycle() -> None:
    conn = _FakeConn()
    key = uuid.uuid4()
    record = IdempotencyRecord(payload={"foo": "bar"}, status_code=201)
    
    # Not found
    assert await get_idempotent_response(conn, key) is None
    
    # Save
    await save_idempotent_response(conn, key, record)
    
    # Found
    loaded = await get_idempotent_response(conn, key)
    assert loaded is not None
    assert loaded.payload == {"foo": "bar"}
    assert loaded.status_code == 201


def test_middleware_idempotency_workflow(client_with_pool: TestClient) -> None:
    # We need to override auth to pass the middleware
    def _auth_override() -> CallingIdentity:
        return CallingIdentity("operator")
    
    app.dependency_overrides[require_bearer_auth] = _auth_override
    try:
        key = str(uuid.uuid4())
        headers = {
            "X-Idempotency-Key": key
        }
        
        # Define a test payload
        payload = {
            "source_id": f"test-idemp-{uuid.uuid4()}",
            "actor_id": "tester",
            "consent_scope": {"summarize": True},
            "retention_policy": "raw_30d",
            "granted_by": "manual"
        }

        # First request
        resp1 = client_with_pool.post("/v1/sources", json=payload, headers=headers)
        assert resp1.status_code == 201
        assert resp1.headers.get("X-Cache-Hit") is None
        
        # Second request with same key
        resp2 = client_with_pool.post("/v1/sources", json=payload, headers=headers)
        assert resp2.status_code == 201
        assert resp2.headers.get("X-Cache-Hit") == "true"
        assert resp2.json() == resp1.json()
    finally:
        app.dependency_overrides.pop(require_bearer_auth, None)


def test_middleware_invalid_key(client_with_pool: TestClient) -> None:
    headers = {"X-Idempotency-Key": "not-a-uuid"}
    resp = client_with_pool.post("/v1/sources", json={}, headers=headers)
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "invalid_idempotency_key"
