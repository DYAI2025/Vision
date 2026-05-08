"""Concurrency stress test for Kanban sync."""

from __future__ import annotations

import asyncio
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from app.kanban import save_card, load_card
from app.models import CardRecord, CardSyncFields
import pytest

def test_concurrent_card_writes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Setup tmp vault
    kanban_dir = tmp_path / "Kanban"
    kanban_dir.mkdir()
    monkeypatch.setenv("KANBAN_SUBTREE", str(kanban_dir))
    
    card_id = "stress-task"
    
    def write_task(i: int) -> None:
        card = CardRecord(
            card_id=card_id,
            title=f"Title {i}",
            content=f"Content {i}"
        )
        save_card(card)

    # Run 20 writes in parallel threads
    with ThreadPoolExecutor(max_workers=10) as executor:
        list(executor.map(write_task, range(20)))
    
    # Load and verify it's still a valid file
    loaded = load_card(card_id)
    assert loaded is not None
    assert loaded.card_id == card_id
    assert "Title" in loaded.title
