"""FastAPI application entry point for kanban-sync.

Skeleton task (TASK-kanban-sync-skeleton): exposes only `GET /v1/health`,
which checks the Kanban subtree mount is reachable and writable. Card CRUD,
sync-vs-edit boundary detection, manual column-move attribution, the
periodic sync trigger, and the RTBF cascade endpoint all land in subsequent
Phase 4 / Phase 5 tasks.
"""

from typing import Literal

from fastapi import FastAPI, Response
from fastapi import status as http_status
from pydantic import BaseModel

from app import __version__
from app.kanban import is_writable, kanban_subtree

app = FastAPI(
    title="kanban-sync",
    description="Obsidian Kanban file I/O + sync-vs-edit boundary detection.",
    version=__version__,
    docs_url="/docs",
    redoc_url=None,
    openapi_url="/openapi.json",
)


class HealthResponse(BaseModel):
    """Shape per api-design.md § Health and observability."""

    status: Literal["ok", "degraded", "down"]
    version: str
    checks: dict[str, str]


@app.get(
    "/v1/health",
    response_model=HealthResponse,
    tags=["health"],
    responses={
        200: {"description": "Kanban subtree mounted and writable; component ready."},
        503: {"description": "Kanban subtree missing, not a directory, or not writable."},
    },
)
async def health(response: Response) -> HealthResponse:
    kanban_ok = is_writable(kanban_subtree())
    if not kanban_ok:
        response.status_code = http_status.HTTP_503_SERVICE_UNAVAILABLE
    return HealthResponse(
        status="ok" if kanban_ok else "degraded",
        version=__version__,
        checks={"kanban_subtree": "ok" if kanban_ok else "down"},
    )
