"""Data models for kanban-sync.

Per REQ-USA-kanban-obsidian-fidelity.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class CardSyncFields(BaseModel):
    """Fields owned by the system. Human edits to these will be reconciled."""

    proposal_id: UUID | None = None
    source_event_id: UUID | None = None
    confidence: float | None = None
    learnings_applied: list[str] = Field(default_factory=list)


class CardRecord(BaseModel):
    """Complete card state, separating system and user concerns."""

    card_id: str
    title: str
    content: str = ""
    # System-owned metadata
    sync: CardSyncFields = Field(default_factory=CardSyncFields)
    # User-owned metadata (anything not in CardSyncFields)
    user_fields: dict[str, Any] = Field(default_factory=dict)
    # Current location
    column: str | None = None


class BoardColumn(BaseModel):
    name: str
    card_ids: list[str] = Field(default_factory=list)


class BoardState(BaseModel):
    title: str
    columns: list[BoardColumn] = Field(default_factory=list)
