"""Tests for Kanban board management logic."""

from __future__ import annotations

from pathlib import Path
from app.board import load_board, save_board, add_card_to_board
from app.models import BoardState, BoardColumn


def test_save_and_load_board(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Setup tmp vault
    kanban_dir = tmp_path / "Kanban"
    kanban_dir.mkdir()
    monkeypatch.setenv("KANBAN_SUBTREE", str(kanban_dir))
    
    state = BoardState(
        title="Test Board",
        columns=[
            BoardColumn(name="Inbox", card_ids=["task-1"]),
            BoardColumn(name="Done", card_ids=["task-2", "task-3"])
        ]
    )
    
    # Save
    save_board(state)
    
    # Verify file
    board_file = kanban_dir / "Project Steering.md"
    assert board_file.exists()
    
    # Load
    loaded = load_board()
    assert len(loaded.columns) == 2
    assert loaded.columns[0].name == "Inbox"
    assert "task-1" in loaded.columns[0].card_ids
    assert "task-3" in loaded.columns[1].card_ids


def test_add_card_to_board(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Setup tmp vault
    kanban_dir = tmp_path / "Kanban"
    kanban_dir.mkdir()
    monkeypatch.setenv("KANBAN_SUBTREE", str(kanban_dir))
    
    add_card_to_board("new-task", column_name="Backlog")
    
    loaded = load_board()
    assert loaded.columns[0].name == "Backlog"
    assert "new-task" in loaded.columns[0].card_ids
