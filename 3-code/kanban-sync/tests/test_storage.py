"""Tests for Kanban storage logic."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.kanban import load_card, save_card
from app.models import CardRecord, CardSyncFields


def test_save_and_load_card(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Setup tmp vault
    kanban_dir = tmp_path / "Kanban"
    kanban_dir.mkdir()

    monkeypatch.setenv("KANBAN_SUBTREE", str(kanban_dir))

    card = CardRecord(
        card_id="task-123",
        title="Implement Auth",
        content="We need to add bearer auth.",
        sync=CardSyncFields(confidence=0.9),
        user_fields={"due": "2026-05-10", "note": "Priority high"},
    )

    # Save
    save_card(card)

    # Verify file exists
    file_path = kanban_dir / "cards" / "task-123.md"
    assert file_path.exists()

    # Load
    loaded = load_card("task-123")
    assert loaded is not None
    assert loaded.card_id == "task-123"
    assert loaded.title == "Implement Auth"
    assert loaded.sync.confidence == 0.9
    assert loaded.user_fields["due"] == "2026-05-10"
    assert loaded.user_fields["note"] == "Priority high"
    assert "We need to add bearer auth." in loaded.content


def test_load_card_corrupt_yaml(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Setup tmp vault
    kanban_dir = tmp_path / "Kanban"
    kanban_dir.mkdir()
    monkeypatch.setenv("KANBAN_SUBTREE", str(kanban_dir))
    cards_dir = kanban_dir / "cards"
    cards_dir.mkdir()

    # Write a file with invalid YAML in frontmatter
    (cards_dir / "corrupt.md").write_text(
        "---\ninvalid: : yaml\n---\n# Title\nBody", encoding="utf-8"
    )

    card = load_card("corrupt")
    assert card is not None
    assert card.title == "Title"
    assert card.user_fields == {}  # Should fall back gracefully
