from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

from app import __version__

app = FastAPI(
    title="gbrain-bridge",
    description="GBrain vault read/write bridge for project-agent-system.",
    version=__version__,
    docs_url="/docs",
    redoc_url=None,
    openapi_url="/openapi.json",
)


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded", "down"]
    version: str
    checks: dict[str, str]


class ContextSnippet(BaseModel):
    page_id: str
    score: float
    text: str


class ContextResponse(BaseModel):
    project_id: str
    query: str
    snippets: list[ContextSnippet]


def _vault_root() -> Path:
    return Path(os.environ.get("VAULT_PATH", "/vault"))


def _project_pages(project_id: str) -> list[Path]:
    root = _vault_root() / "projects" / project_id
    if not root.exists():
        return []
    return sorted(path for path in root.glob("*.md") if path.is_file())


def _score_text(query: str, text: str) -> float:
    query_terms = {part.lower() for part in query.split() if part.strip()}
    if not query_terms:
        return 0.0
    low = text.lower()
    hits = sum(1 for term in query_terms if term in low)
    return hits / len(query_terms)


@app.get("/v1/health", response_model=HealthResponse, tags=["health"])
async def health() -> HealthResponse:
    return HealthResponse(status="ok", version=__version__, checks={})


@app.get("/v1/context/{project_id}", response_model=ContextResponse, tags=["context"])
async def project_context(
    project_id: str,
    q: str,
    limit: int = 3,
    authorization: str | None = Header(default=None),
) -> ContextResponse:
    token = os.environ.get("HERMES_RUNTIME_TOKEN")
    if token and authorization != f"Bearer {token}":
        raise HTTPException(status_code=401, detail="auth_invalid")

    snippets: list[ContextSnippet] = []
    for page in _project_pages(project_id):
        text = page.read_text(encoding="utf-8")
        score = _score_text(q, text)
        if score <= 0:
            continue
        snippets.append(
            ContextSnippet(page_id=page.stem, score=round(score, 3), text=text[:500])
        )

    snippets.sort(key=lambda item: item.score, reverse=True)
    safe_limit = max(1, min(limit, 20))
    return ContextResponse(project_id=project_id, query=q, snippets=snippets[:safe_limit])
