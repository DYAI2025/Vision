from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient

from app.main import app


class _FakeOllama:
    async def generate(self, prompt: str, **options: object) -> str:
        return "Semantic summary\n- point one\n- point two"

    async def embeddings(self, prompt: str) -> list[float]:
        return [0.1] * 1024


async def _fake_context(project_id: str, query: str) -> tuple[str, list[str]]:
    return "Known context for routing.", ["page-1"]


def test_process_now_uses_llm_and_context(monkeypatch: Any) -> None:
    monkeypatch.setattr("app.main.OllamaClient", lambda: _FakeOllama())
    monkeypatch.setattr("app.main._load_gbrain_context", _fake_context)

    client = TestClient(app)
    response = client.post(
        "/v1/agent/process-now",
        json={
            "event_id": "evt-1",
            "project_id": "vision",
            "message_text": "Need a migration checklist and rollback plan.",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["semantic_summary"] == "Semantic summary"
    assert payload["cited_pages"] == ["page-1"]
    assert payload["confidence"] > 0.6
