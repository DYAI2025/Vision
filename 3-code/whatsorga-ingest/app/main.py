"""FastAPI application entry point for whatsorga-ingest.

Skeleton task (TASK-whatsorga-skeleton): exposes only `GET /v1/health` per
`2-design/api-design.md` § "Health and observability". Adapters, normalization,
and the consent boundary are added by subsequent Phase 1 / Phase 3 tasks.
"""

from typing import Literal

from fastapi import FastAPI
from pydantic import BaseModel

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
    """Shape per api-design.md § Health and observability."""

    status: Literal["ok", "degraded", "down"]
    version: str
    checks: dict[str, str]


@app.get("/v1/health", response_model=HealthResponse, tags=["health"])
async def health() -> HealthResponse:
    return HealthResponse(status="ok", version=__version__, checks={})
