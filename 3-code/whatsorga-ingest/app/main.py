"""FastAPI application entry point for whatsorga-ingest."""

from __future__ import annotations

import os
from datetime import UTC, datetime
from typing import Any, Literal
from uuid import uuid4

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app import __version__

app = FastAPI(
    title="whatsorga-ingest",
    description="Adapter layer + normalization for project-agent-system.",
    version=__version__,
    docs_url="/docs",
    redoc_url=None,
    openapi_url="/openapi.json",
)


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded", "down"]
    version: str
    checks: dict[str, str]


class ManualIngestRequest(BaseModel):
    source_id: str = Field(min_length=1)
    actor_id: str = Field(min_length=1)
    message_text: str = Field(min_length=1)
    project_hint: str | None = None
    channel_metadata: dict[str, Any] = Field(default_factory=dict)


class NormalizedInputEvent(BaseModel):
    event_id: str
    source_id: str
    actor_id: str
    channel: Literal["manual_cli"]
    project_hint: str | None = None
    message_text: str
    happened_at: datetime
    channel_metadata: dict[str, Any]


class ManualIngestResponse(BaseModel):
    normalized_event: NormalizedInputEvent
    backlog_result: dict[str, Any]


@app.get("/v1/health", response_model=HealthResponse, tags=["health"])
async def health() -> HealthResponse:
    return HealthResponse(status="ok", version=__version__, checks={})


@app.post("/v1/ingest/manual", response_model=ManualIngestResponse, tags=["ingest"])
async def ingest_manual(body: ManualIngestRequest) -> ManualIngestResponse:
    event = NormalizedInputEvent(
        event_id=str(uuid4()),
        source_id=body.source_id,
        actor_id=body.actor_id,
        channel="manual_cli",
        project_hint=body.project_hint,
        message_text=body.message_text,
        happened_at=datetime.now(UTC),
        channel_metadata=body.channel_metadata,
    )

    backlog_url = os.environ.get("BACKLOG_CORE_URL", "http://backlog-core:8000")
    token = os.environ.get("WHATSORGA_INGEST_TOKEN", "")

    headers = {
        "Idempotency-Key": event.event_id,
        "Authorization": f"Bearer {token}",
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{backlog_url}/v1/inputs",
                json=event.model_dump(mode="json"),
                headers=headers,
            )
            response.raise_for_status()
            result = response.json()
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"backlog_unreachable: {exc}") from exc

    return ManualIngestResponse(normalized_event=event, backlog_result=result)
