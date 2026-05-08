"""Extraction skill for Hermes.

Processes raw text to extract structured summaries, tags, and action items.
Per TASK-hermes-skill-summarize and data-model.md.
"""

from __future__ import annotations

import json
import re
from typing import Any

from pydantic import BaseModel, Field

from ..ollama_client import OllamaClient


class ExtractionResult(BaseModel):
    """Structured output of the semantic extraction."""

    summary: str = Field(description="A concise 1-2 sentence summary of the input.")
    tags: list[str] = Field(default_factory=list, description="Relevant keywords for indexing.")
    action_items: list[str] = Field(default_factory=list, description="Specific tasks identified in the text.")
    confidence: float = Field(default=0.0, description="Confidence score between 0 and 1.")


EXTRACTION_PROMPT_TEMPLATE = """
You are Hermes, a project-manager agent. Your task is to analyze the following input and extract a structured summary, relevant tags, and any specific action items.

INPUT:
{text}

OUTPUT FORMAT (JSON):
{{
  "summary": "...",
  "tags": ["tag1", "tag2"],
  "action_items": ["item1", "item2"],
  "confidence": 0.0 to 1.0
}}

Ensure the output is ONLY valid JSON.
"""

async def extract_semantic_data(client: OllamaClient, text: str) -> ExtractionResult:
    """Run the extraction skill using local Ollama."""
    prompt = EXTRACTION_PROMPT_TEMPLATE.format(text=text)
    
    # Run generation
    raw_response = await client.generate(prompt)
    
    # Try to find JSON in the response (handle models that wrap JSON in backticks)
    json_match = re.search(r"(\{.*\})", raw_response, re.DOTALL)
    if json_match:
        try:
            data = json.loads(json_match.group(1))
            return ExtractionResult(**data)
        except (json.JSONDecodeError, ValueError):
            pass
            
    # Fallback if parsing fails
    return ExtractionResult(
        summary="Konnte Inhalt nicht automatisch zusammenfassen.",
        tags=["manual_review"],
        action_items=[],
        confidence=0.1
    )
