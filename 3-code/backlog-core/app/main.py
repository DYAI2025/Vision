from __future__ import annotations

import os
from collections import deque
from datetime import UTC, datetime
from typing import Annotated, Any, Literal

from fastapi import Depends, FastAPI, Header, HTTPException, Response
from fastapi import status as http_status
from pydantic import BaseModel, Field

from app import __version__
from app.db import _PoolLike, get_pool, lifespan, ping

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


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded", "down"]
    version: str
    checks: dict[str, str]


class InputEvent(BaseModel):
    event_id: str = Field(min_length=8)
    source_id: str = Field(min_length=1)
    actor_id: str = Field(min_length=1)
    project_hint: str | None = None
    channel: Literal["manual_cli", "whatsapp", "voice", "repo"]
    message_text: str = Field(min_length=1)
    happened_at: datetime
    channel_metadata: dict[str, Any] = Field(default_factory=dict)


class InputAck(BaseModel):
    event_id: str
    stored_at: datetime


def _events_buffer() -> deque[InputEvent]:
    events = getattr(app.state, "events", None)
    if events is None:
        events = deque(maxlen=1000)
        app.state.events = events
    return events


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
    "/v1/inputs",
    response_model=InputAck,
    status_code=http_status.HTTP_201_CREATED,
    tags=["inputs"],
)
async def ingest_input(
    body: InputEvent,
    authorization: str | None = Header(default=None),
    idempotency_key: str | None = Header(default=None),
) -> InputAck:
    """Store normalized input events for downstream agent processing."""
    expected_token = os.environ.get("WHATSORGA_INGEST_TOKEN")
    if expected_token and authorization != f"Bearer {expected_token}":
        raise HTTPException(status_code=401, detail="auth_invalid")

    if idempotency_key and idempotency_key != body.event_id:
        raise HTTPException(status_code=409, detail="idempotency_conflict")

    events = _events_buffer()
    if any(existing.event_id == body.event_id for existing in events):
        return InputAck(event_id=body.event_id, stored_at=datetime.now(UTC))

    events.append(body)
    return InputAck(event_id=body.event_id, stored_at=datetime.now(UTC))


@app.get("/v1/inputs/recent", response_model=list[InputEvent], tags=["inputs"])
async def list_recent_inputs(limit: int = 20) -> list[InputEvent]:
    bounded_limit = max(1, min(limit, 200))
    events = list(_events_buffer())
    return events[-bounded_limit:]
