"""FastAPI application entry point for backlog-core.

Skeleton task (TASK-backlog-core-skeleton): exposes only `GET /v1/health`,
which pings the Postgres pool created by `app.db.lifespan` and reports
connectivity. Schema, event-emit primitives, proposal pipeline, RTBF cascade,
and the rest of the API surface land in subsequent Phase 2 / Phase 3 / Phase
4 tasks.
"""

from typing import Annotated, Literal

from fastapi import Depends, FastAPI, Response
from fastapi import status as http_status
from pydantic import BaseModel

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
    """Shape per api-design.md § Health and observability."""

    status: Literal["ok", "degraded", "down"]
    version: str
    checks: dict[str, str]


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
