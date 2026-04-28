"""FastAPI application entry point for hermes-runtime."""

from __future__ import annotations

import os
from typing import Literal

import httpx
from fastapi import FastAPI
from pydantic import BaseModel, Field

from app import __version__
from app.ollama_client import OllamaClient, OllamaError

app = FastAPI(
    title="hermes-runtime",
    description="Project-manager agent runtime for project-agent-system.",
    version=__version__,
    docs_url="/docs",
    redoc_url=None,
    openapi_url="/openapi.json",
)


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded", "down"]
    version: str
    checks: dict[str, str]


class ProcessNowRequest(BaseModel):
    event_id: str
    project_id: str
    message_text: str = Field(min_length=1)


class ProcessNowResponse(BaseModel):
    event_id: str
    project_id: str
    semantic_summary: str
    key_points: list[str]
    cited_pages: list[str]
    confidence: float


async def _load_gbrain_context(project_id: str, query: str) -> tuple[str, list[str]]:
    gbrain_url = os.environ.get("GBRAIN_BRIDGE_URL", "http://gbrain-bridge:8000")
    token = os.environ.get("HERMES_RUNTIME_TOKEN", "")
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                f"{gbrain_url}/v1/context/{project_id}",
                params={"q": query, "limit": 3},
                headers={"Authorization": f"Bearer {token}"},
            )
            response.raise_for_status()
            payload = response.json()
            snippets = payload.get("snippets", [])
            pages = [str(item.get("page_id", "")) for item in snippets if item.get("page_id")]
            context_text = "\n".join(str(item.get("text", "")) for item in snippets)
            return context_text, pages
    except httpx.HTTPError:
        return "", []


def _fallback_semantic_parse(message: str) -> tuple[str, list[str], float]:
    lines = [chunk.strip("-• ") for chunk in message.split(".") if chunk.strip()]
    key_points = lines[:3] if lines else [message[:120]]
    return message[:400], key_points, 0.62


@app.get("/v1/health", response_model=HealthResponse, tags=["health"])
async def health() -> HealthResponse:
    return HealthResponse(status="ok", version=__version__, checks={})


@app.post("/v1/agent/process-now", response_model=ProcessNowResponse, tags=["agent"])
async def process_now(body: ProcessNowRequest) -> ProcessNowResponse:
    context_text, cited_pages = await _load_gbrain_context(body.project_id, body.message_text)
    prompt = (
        "Extract a concise semantic summary and up to 3 bullet key points for project planning. "
        "Return plain text with one summary sentence and bullet lines.\n"
        f"Project: {body.project_id}\n"
        f"Context:\n{context_text or 'No context found.'}\n"
        f"Input:\n{body.message_text}\n"
    )

    client = OllamaClient()
    try:
        llm_text = await client.generate(prompt, temperature=0.1)
        embedding = await client.embeddings(body.message_text)
        confidence = min(0.98, 0.55 + (len(embedding) / 10000.0))
        lines = [line.strip() for line in llm_text.splitlines() if line.strip()]
        semantic_summary = lines[0] if lines else body.message_text[:400]
        key_points = [line.lstrip("-* ") for line in lines[1:4]] or [semantic_summary]
    except (OllamaError, httpx.HTTPError):
        semantic_summary, key_points, confidence = _fallback_semantic_parse(body.message_text)

    return ProcessNowResponse(
        event_id=body.event_id,
        project_id=body.project_id,
        semantic_summary=semantic_summary,
        key_points=key_points,
        cited_pages=cited_pages,
        confidence=round(confidence, 3),
    )
