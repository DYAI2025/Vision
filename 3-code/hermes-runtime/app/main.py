"""FastAPI application entry point for hermes-runtime.

Skeleton task (TASK-hermes-skeleton): exposes only `GET /v1/health` per
`2-design/api-design.md` § "Health and observability". The agent runtime,
skills, confidence-gate middleware, and learning-loop land in subsequent
Phase 3 / Phase 5 tasks. The Ollama client primitive in `app.ollama_client`
is wired and importable but not yet invoked from any endpoint.
"""

from typing import Literal

from fastapi import FastAPI
from pydantic import BaseModel

from app import __version__

app = FastAPI(
    title="hermes-runtime",
    description="Project-manager agent runtime for project-agent-system.",
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
