"""FastAPI application entry point for gbrain-bridge.

Skeleton task (TASK-gbrain-bridge-skeleton): exposes only `GET /v1/health`,
which checks the GBrain vault mount is reachable and reports the result in
`checks.vault`. Page CRUD, schema validation, bidirectional links, redaction
precondition, RTBF cascade, the Obsidian command-palette watch script, and
the weekly vault audit sweep all land in subsequent Phase 4 / Phase 5 / Phase
6 / Phase 7 tasks.
"""

from typing import Literal

from fastapi import FastAPI, Response
from fastapi import status as http_status
from pydantic import BaseModel

from app import __version__
from app.vault import is_readable, vault_path

app = FastAPI(
    title="gbrain-bridge",
    description="GBrain vault read/write + watch script for project-agent-system.",
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
        200: {"description": "Vault mount reachable; component ready."},
        503: {"description": "Vault mount missing or unreadable."},
    },
)
async def health(response: Response) -> HealthResponse:
    vault_ok = is_readable(vault_path())
    if not vault_ok:
        response.status_code = http_status.HTTP_503_SERVICE_UNAVAILABLE
    return HealthResponse(
        status="ok" if vault_ok else "degraded",
        version=__version__,
        checks={"vault": "ok" if vault_ok else "down"},
    )
