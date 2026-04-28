"""Thin async client for the Ollama HTTP API.

Skeleton-level primitive (TASK-hermes-skeleton). Future skills consume it:
routing-skill, extraction-skill, brain-first lookup, learning-loop. Wire shape
follows the Ollama HTTP API: `POST /api/generate` and `POST /api/embeddings`.
Per `3-code/hermes-runtime/CLAUDE.component.md` interfaces.

Default-local: the constructor reads OLLAMA_URL / OLLAMA_MODEL from the
process environment, falling back to the in-Compose service URL and the
default Gemma model from `.env.example`. Remote-inference profile gating and
audit-log emission per REQ-SEC-remote-inference-audit are NOT implemented
here — they land in TASK-model-router and TASK-remote-inference-profile.
"""

from __future__ import annotations

import os
from typing import Any

import httpx

DEFAULT_OLLAMA_URL = "http://ollama:11434"
DEFAULT_OLLAMA_MODEL = "gemma3:4b"


class OllamaError(RuntimeError):
    """Raised when the Ollama HTTP API returns an error or an unexpected payload."""


class OllamaClient:
    """Async wrapper around Ollama's `/api/generate` and `/api/embeddings` endpoints."""

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        *,
        timeout: float = 60.0,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.base_url = (base_url or os.environ.get("OLLAMA_URL") or DEFAULT_OLLAMA_URL).rstrip("/")
        self.model = model or os.environ.get("OLLAMA_MODEL") or DEFAULT_OLLAMA_MODEL
        self._timeout = timeout
        self._transport = transport

    def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self._timeout,
            transport=self._transport,
        )

    async def generate(self, prompt: str, **options: Any) -> str:
        """Single-shot completion against `/api/generate`. Streaming is disabled."""
        payload: dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
        }
        if options:
            payload["options"] = options

        async with self._client() as http:
            response = await http.post("/api/generate", json=payload)
            response.raise_for_status()
            body = response.json()

        if "response" not in body:
            raise OllamaError(f"missing 'response' field in /api/generate payload: {body!r}")
        return str(body["response"])

    async def embeddings(self, prompt: str) -> list[float]:
        """Embed a single prompt via `/api/embeddings`."""
        payload = {"model": self.model, "prompt": prompt}

        async with self._client() as http:
            response = await http.post("/api/embeddings", json=payload)
            response.raise_for_status()
            body = response.json()

        embedding = body.get("embedding")
        if not isinstance(embedding, list) or not all(
            isinstance(x, int | float) for x in embedding
        ):
            raise OllamaError(f"missing/invalid 'embedding' field in payload: {body!r}")
        return [float(x) for x in embedding]
