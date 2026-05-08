"""Tests for Kanban data models."""

from __future__ import annotations

import uuid
from app.models import CardRecord, CardSyncFields


def test_card_record_separation() -> None:
    proposal_id = uuid.uuid4()
    
    # Simulate loading from a file with mixed frontmatter
    raw_frontmatter = {
        "proposal_id": str(proposal_id),
        "confidence": 0.85,
        "user_note": "Don't delete this",
        "custom_tag": "priority-1"
    }
    
    # Split fields
    sync_field_names = CardSyncFields.model_fields.keys()
    sync_data = {k: v for k, v in raw_frontmatter.items() if k in sync_field_names}
    user_data = {k: v for k, v in raw_frontmatter.items() if k not in sync_field_names}
    
    card = CardRecord(
        card_id="test-1",
        title="Test Card",
        sync=CardSyncFields(**sync_data),
        user_fields=user_data
    )
    
    assert card.sync.proposal_id == proposal_id
    assert card.sync.confidence == 0.85
    assert card.user_fields["user_note"] == "Don't delete this"
    assert "proposal_id" not in card.user_fields
