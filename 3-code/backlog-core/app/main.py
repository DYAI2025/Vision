"""FastAPI application entry point for backlog-core.

Exposes health and the Sprint-2 source-consent management API. Remaining
proposal pipeline, RTBF cascade, audit-query, and stream endpoints land in
subsequent Phase 2+ tasks.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Annotated, Any, Literal, cast
from uuid import UUID

from bearer_auth import (
    AcceptedTokens,
    AuthError,
    CallingIdentity,
    require_bearer_auth,
)
from bearer_auth.dependency import auth_error_to_response
from fastapi import Depends, FastAPI, HTTPException, Query, Request, Response
from fastapi import status as http_status
from pydantic import BaseModel, Field, model_validator
from starlette.responses import Response as StarletteResponse

from app import __version__
from app.db import _PoolLike, get_pool, ping
from app.db import lifespan as db_lifespan
from app.sources import (
    get_source,
    list_sources,
    register_source,
    revoke_source,
    source_history,
    update_source,
)
from app.audit import query_audit, verify_chain, VerificationResult


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    app.state.bearer_auth_verifier = AcceptedTokens(["operator", "gbrain-bridge", "hermes-runtime", "whatsorga-ingest", "kanban-sync"]).build_verifier()
    async with db_lifespan(app):
        yield


app = FastAPI(
    title="backlog-core",
    description="Event-sourced technical truth layer for project-agent-system.",
    version=__version__,
    docs_url="/docs",
    redoc_url=None,
    openapi_url="/openapi.json",
    lifespan=lifespan,
)


PoolDep = Annotated[_PoolLike, Depends(get_pool)]
AuthDep = Annotated[CallingIdentity, Depends(require_bearer_auth)]


@app.exception_handler(AuthError)
async def auth_exception_handler(_request: Request, exc: AuthError) -> StarletteResponse:
    return cast(StarletteResponse, auth_error_to_response(exc))


class HealthResponse(BaseModel):
    """Shape per api-design.md § Health and observability."""

    status: Literal["ok", "degraded", "down"]
    version: str
    checks: dict[str, str]


ConsentScope = dict[str, bool]


class SourceRecord(BaseModel):
    source_id: str
    actor_id: str
    lawful_basis: str
    consent_scope: ConsentScope
    retention_policy: str
    current_state: str
    granted_at: datetime
    granted_by: str
    updated_at: datetime


class SourceCreateRequest(BaseModel):
    source_id: str = Field(min_length=1)
    actor_id: str = Field(min_length=1)
    consent_scope: ConsentScope = Field(default_factory=dict)
    retention_policy: str
    granted_by: str = Field(min_length=1)


class SourceUpdateRequest(BaseModel):
    consent_scope: ConsentScope | None = None
    retention_policy: str | None = None
    change_reason: str | None = None

    @model_validator(mode="after")
    def at_least_one_change(self) -> "SourceUpdateRequest":
        if self.consent_scope is None and self.retention_policy is None:
            raise ValueError("consent_scope or retention_policy is required")
        return self


class SourceRevokeRequest(BaseModel):
    change_reason: str | None = None
    revoked_by: str = Field(default="operator")


class SourceHistoryRecord(BaseModel):
    history_id: UUID
    source_id: str
    changed_at: datetime
    prior_scope: dict[str, Any] | None
    new_scope: dict[str, Any]
    prior_retention: str | None
    new_retention: str
    prior_state: str | None
    new_state: str
    change_reason: str | None
    event_id: UUID


class SourceHistoryResponse(BaseModel):
    items: list[SourceHistoryRecord]


@app.get(
    "/v1/health",
    response_model=HealthResponse,
    tags=["health"],
    responses={
        200: {"description": "All checked dependencies healthy."},
        503: {"description": "One or more dependencies are degraded or down."},
    },
)
async def health(pool: PoolDep, response: Response) -> HealthResponse:
    postgres_ok = await ping(pool)
    if not postgres_ok:
        response.status_code = http_status.HTTP_503_SERVICE_UNAVAILABLE
    return HealthResponse(
        status="ok" if postgres_ok else "degraded",
        version=__version__,
        checks={"postgres": "ok" if postgres_ok else "down"},
    )


@app.post(
    "/v1/sources",
    response_model=SourceRecord,
    status_code=http_status.HTTP_201_CREATED,
    tags=["sources"],
    responses={409: {"description": "Source already exists."}},
)
async def create_source(
    request: SourceCreateRequest,
    pool: PoolDep,
    _identity: AuthDep,
) -> dict[str, Any]:
    try:
        async with pool.acquire() as conn, conn.transaction():
            return await register_source(conn, **request.model_dump())
    except Exception as exc:
        if exc.__class__.__name__ == "UniqueViolationError":
            raise HTTPException(
                status_code=409, detail={"code": "already_exists"}
            ) from exc
        raise


class SourceListResponse(BaseModel):
    items: list[SourceRecord]
    next_cursor: str | None = None


@app.get("/v1/sources", response_model=SourceListResponse, tags=["sources"])
async def read_sources(
    pool: PoolDep,
    _identity: AuthDep,
    status_filter: Literal["active", "revoked"] | None = Query(
        default=None, alias="status"
    ),
    actor_id: str | None = None,
) -> dict[str, Any]:
    async with pool.acquire() as conn:
        sources = await list_sources(conn, status=status_filter, actor_id=actor_id)
    return {"items": sources, "next_cursor": None}


@app.get(
    "/v1/sources/{source_id}",
    response_model=SourceRecord,
    tags=["sources"],
    responses={404: {"description": "Source not found."}},
)
async def read_source(source_id: str, pool: PoolDep, _identity: AuthDep) -> dict[str, Any]:
    async with pool.acquire() as conn:
        source = await get_source(conn, source_id)
    if source is None:
        raise HTTPException(status_code=404, detail={"code": "not_found"})
    return source


@app.patch(
    "/v1/sources/{source_id}",
    response_model=SourceRecord,
    tags=["sources"],
    responses={404: {"description": "Source not found."}},
)
async def patch_source(
    source_id: str,
    request: SourceUpdateRequest,
    pool: PoolDep,
    identity: AuthDep,
) -> dict[str, Any]:
    async with pool.acquire() as conn, conn.transaction():
        source = await update_source(
            conn,
            source_id=source_id,
            consent_scope=request.consent_scope,
            retention_policy=request.retention_policy,
            change_reason=request.change_reason,
            actor_id=identity.name,
        )
    if source is None:
        raise HTTPException(status_code=404, detail={"code": "not_found"})
    return source


@app.post(
    "/v1/sources/{source_id}/revoke",
    response_model=SourceRecord,
    tags=["sources"],
    responses={404: {"description": "Source not found."}},
)
async def post_source_revoke(
    source_id: str,
    request: SourceRevokeRequest,
    pool: PoolDep,
    identity: AuthDep,
) -> dict[str, Any]:
    async with pool.acquire() as conn, conn.transaction():
        source = await revoke_source(
            conn,
            source_id=source_id,
            change_reason=request.change_reason,
            actor_id=identity.name,
        )
    if source is None:
        raise HTTPException(status_code=404, detail={"code": "not_found"})
    return source


@app.get(
    "/v1/sources/{source_id}/history",
    response_model=SourceHistoryResponse,
    tags=["sources"],
)
async def read_source_history(
    source_id: str,
    pool: PoolDep,
    _identity: AuthDep,
    as_of: datetime | None = None,
) -> dict[str, Any]:
    async with pool.acquire() as conn:
        items = await source_history(conn, source_id=source_id, as_of=as_of)
    return {"items": items}


@app.get(
    "/v1/audit/query",
    tags=["audit"],
)
async def get_audit_query(
    pool: PoolDep,
    _identity: AuthDep,
    after: UUID | None = Query(None),
    limit: int = Query(50, le=100),
) -> list[dict[str, Any]]:
    async with pool.acquire() as conn:
        return await query_audit(conn, after, limit)


@app.post(
    "/v1/audit/verify-chain",
    response_model=VerificationResult,
    tags=["audit"],
)
async def post_audit_verify(
    pool: PoolDep,
    _identity: AuthDep,
) -> VerificationResult:
    async with pool.acquire() as conn:
        return await verify_chain(conn)
