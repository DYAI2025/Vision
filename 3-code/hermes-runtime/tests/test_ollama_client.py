"""Tests for the OllamaClient primitive (TASK-hermes-skeleton).

Uses httpx.MockTransport — no Ollama process required, no extra dep beyond
the already-installed httpx. Each test asserts both the request shape (URL,
method, body) and the client's interpretation of the response.
"""

from __future__ import annotations

import json
from typing import Any

import httpx
import pytest

from app.ollama_client import (
    DEFAULT_OLLAMA_MODEL,
    DEFAULT_OLLAMA_URL,
    OllamaClient,
    OllamaError,
)


def _mock_transport(handler: Any) -> httpx.MockTransport:
    return httpx.MockTransport(handler)


def test_client_defaults_when_env_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OLLAMA_URL", raising=False)
    monkeypatch.delenv("OLLAMA_MODEL", raising=False)

    client = OllamaClient()

    assert client.base_url == DEFAULT_OLLAMA_URL
    assert client.model == DEFAULT_OLLAMA_MODEL


def test_client_reads_env_overrides(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OLLAMA_URL", "http://other:11434/")
    monkeypatch.setenv("OLLAMA_MODEL", "gemma3:1b")

    client = OllamaClient()

    assert client.base_url == "http://other:11434"  # trailing slash trimmed
    assert client.model == "gemma3:1b"


def test_constructor_args_override_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OLLAMA_URL", "http://env:11434")
    monkeypatch.setenv("OLLAMA_MODEL", "from-env")

    client = OllamaClient(base_url="http://explicit:11434", model="explicit-model")

    assert client.base_url == "http://explicit:11434"
    assert client.model == "explicit-model"


async def test_generate_posts_to_api_generate_with_expected_payload() -> None:
    captured: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["method"] = request.method
        captured["body"] = json.loads(request.content)
        return httpx.Response(200, json={"response": "hi", "done": True})

    client = OllamaClient(
        base_url="http://test:11434",
        model="gemma3:4b",
        transport=_mock_transport(handler),
    )

    result = await client.generate("hello")

    assert result == "hi"
    assert captured["method"] == "POST"
    assert captured["url"] == "http://test:11434/api/generate"
    assert captured["body"] == {"model": "gemma3:4b", "prompt": "hello", "stream": False}


async def test_generate_passes_options_when_supplied() -> None:
    captured: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["body"] = json.loads(request.content)
        return httpx.Response(200, json={"response": "ok"})

    client = OllamaClient(
        base_url="http://test:11434",
        model="m",
        transport=_mock_transport(handler),
    )

    await client.generate("p", temperature=0.2, num_predict=64)

    assert captured["body"]["options"] == {"temperature": 0.2, "num_predict": 64}


async def test_generate_raises_on_5xx() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, json={"error": "model loading"})

    client = OllamaClient(
        base_url="http://test:11434",
        model="m",
        transport=_mock_transport(handler),
    )

    with pytest.raises(httpx.HTTPStatusError):
        await client.generate("p")


async def test_generate_raises_ollama_error_on_missing_response_field() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"done": True})  # no "response"

    client = OllamaClient(
        base_url="http://test:11434",
        model="m",
        transport=_mock_transport(handler),
    )

    with pytest.raises(OllamaError, match="missing 'response'"):
        await client.generate("p")


async def test_embeddings_returns_float_vector() -> None:
    captured: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["body"] = json.loads(request.content)
        return httpx.Response(200, json={"embedding": [0.1, 0.2, 0.3]})

    client = OllamaClient(
        base_url="http://test:11434",
        model="gemma3:4b",
        transport=_mock_transport(handler),
    )

    vec = await client.embeddings("hello")

    assert vec == [0.1, 0.2, 0.3]
    assert all(isinstance(x, float) for x in vec)
    assert captured["url"] == "http://test:11434/api/embeddings"
    assert captured["body"] == {"model": "gemma3:4b", "prompt": "hello"}


async def test_embeddings_raises_ollama_error_when_payload_malformed() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"embedding": "not a list"})

    client = OllamaClient(
        base_url="http://test:11434",
        model="m",
        transport=_mock_transport(handler),
    )

    with pytest.raises(OllamaError, match="invalid 'embedding'"):
        await client.embeddings("p")
