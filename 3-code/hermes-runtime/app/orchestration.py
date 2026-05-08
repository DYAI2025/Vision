"""Orchestration logic for Hermes processing.

Integrates extraction with backlog-core and kanban-sync to complete the
intelligence loop.
"""

from __future__ import annotations

import os
from typing import Any
from uuid import UUID

import httpx
from pydantic import BaseModel

from .skills.extraction import extract_semantic_data, ExtractionResult
from .ollama_client import OllamaClient

BACKLOG_CORE_URL = os.environ.get("BACKLOG_CORE_URL", "http://backlog-core:8000")
KANBAN_SYNC_URL = os.environ.get("KANBAN_SYNC_URL", "http://kanban-sync:8000")
HERMES_TOKEN = os.environ.get("HERMES_TOKEN", "test-token")


class ProcessRequest(BaseModel):
    text: str
    target_memo: str = "inbox"


async def process_idea_to_proposal(ollama: OllamaClient, req: ProcessRequest) -> dict[str, Any]:
    """Process a raw idea text into a verifiable proposal and a Kanban card."""
    
    # 1. Extraction (Local AI)
    extraction = await extract_semantic_data(ollama, req.text)
    
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {HERMES_TOKEN}"}
        
        # 2. Emit Input Event
        input_resp = await client.post(
            f"{BACKLOG_CORE_URL}/v1/inputs",
            json={
                "event_type": "idea.captured",
                "payload": {
                    "text": req.text,
                    "target_memo": req.target_memo,
                    "extraction_preview": extraction.model_dump()
                }
            },
            headers=headers
        )
        input_resp.raise_for_status()
        source_input_event_id = input_resp.json()["event_id"]
        
        # 3. Create Proposal
        proposal_resp = await client.post(
            f"{BACKLOG_CORE_URL}/v1/proposals",
            json={
                "tool_id": "kanban-sync",
                "content": {
                    "action": "create_card",
                    "title": extraction.summary,
                    "body": req.text,
                    "column": "Inbox"
                },
                "gate_inputs": {
                    "confidence": extraction.confidence,
                    "gate_band": "high" if extraction.confidence > 0.8 else "mid",
                    "consent_snapshot": { "summarize": True } # Simplified for MVP
                },
                "source_input_event_id": source_input_event_id
            },
            headers=headers
        )
        proposal_resp.raise_for_status()
        proposal_id = proposal_resp.json()["proposal_id"]
        
        # 4. Create Kanban Card
        kanban_resp = await client.post(
            f"{KANBAN_SYNC_URL}/v1/cards",
            json={
                "card_id": str(proposal_id),
                "title": extraction.summary,
                "content": req.text,
                "column": "Inbox",
                "sync": {
                    "proposal_id": proposal_id,
                    "confidence": extraction.confidence
                },
                "user_fields": {
                    "tags": extraction.tags,
                    "source": "frontend-workbench"
                }
            },
            headers=headers
        )
        kanban_resp.raise_for_status()
        
    return {
        "proposal_id": proposal_id,
        "extraction": extraction,
        "status": "card_created"
    }
