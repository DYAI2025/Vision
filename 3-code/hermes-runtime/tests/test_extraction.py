"""Tests for the Hermes extraction skill."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock

import pytest

from app.skills.extraction import extract_semantic_data, ExtractionResult


@pytest.mark.asyncio
async def test_extract_semantic_data_success() -> None:
    client = AsyncMock()
    client.generate.return_value = json.dumps({
        "summary": "Implement auth.",
        "tags": ["auth", "security"],
        "action_items": ["Add JWT"],
        "confidence": 0.95
    })
    
    result = await extract_semantic_data(client, "We need to add JWT authentication.")
    
    assert result.summary == "Implement auth."
    assert "auth" in result.tags
    assert len(result.action_items) == 1
    assert result.confidence == 0.95


@pytest.mark.asyncio
async def test_extract_semantic_data_fallback() -> None:
    client = AsyncMock()
    client.generate.return_value = "This is not JSON."
    
    result = await extract_semantic_data(client, "Garbage input.")
    
    assert result.confidence == 0.1
    assert "manual_review" in result.tags
