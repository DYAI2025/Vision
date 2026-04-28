from typing import Literal

from fastapi import FastAPI
from pydantic import BaseModel

from app import __version__

app = FastAPI(title="kanban-sync", version=__version__)


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded", "down"]
    version: str
    checks: dict[str, str]


@app.get("/v1/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok", version=__version__, checks={})
