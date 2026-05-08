"""Board management logic for kanban-sync.

Per REQ-USA-kanban-obsidian-fidelity.
"""

from __future__ import annotations

import re
from pathlib import Path

from filelock import FileLock

from .kanban import get_inbox_column, kanban_subtree
from .models import BoardColumn, BoardState

DEFAULT_BOARD_NAME = "Project Steering.md"


def get_board_path() -> Path:
    return kanban_subtree() / DEFAULT_BOARD_NAME


def get_board_lock_path() -> Path:
    return get_board_path().with_suffix(".lock")


def load_board() -> BoardState:
    """Load the board state from the central markdown file."""
    path = get_board_path()
    if not path.exists():
        return BoardState(title="Project Steering")

    lock_path = get_board_lock_path()
    with FileLock(lock_path):
        text = path.read_text(encoding="utf-8")

    # Simple parser for Obsidian Kanban format
    columns: list[BoardColumn] = []
    current_col: BoardColumn | None = None

    for line in text.splitlines():
        # Match column header ## Column Name
        col_match = re.match(r"^## (.*)", line)
        if col_match:
            current_col = BoardColumn(name=col_match.group(1).strip())
            columns.append(current_col)
            continue

        # Match card item - [ ] [[card_id]]
        # Robust regex handling whitespace per code review
        card_match = re.match(r"^- \[ \] \[\[\s*(.*?)\s*\]\]", line)
        if card_match and current_col is not None:
            current_col.card_ids.append(card_match.group(1).strip())

    return BoardState(title="Project Steering", columns=columns)


def save_board(state: BoardState) -> None:
    """Save the board state to the markdown file."""
    path = get_board_path()

    lines = ["---", "kanban-plugin: basic", "---", ""]

    for col in state.columns:
        lines.append(f"## {col.name}")
        for card_id in col.card_ids:
            lines.append(f"- [ ] [[{card_id}]]")
        lines.append("")

    lock_path = get_board_lock_path()
    with FileLock(lock_path):
        path.write_text("\n".join(lines), encoding="utf-8")


def add_card_to_board(card_id: str, column_name: str | None = None) -> None:
    """Add a card to a specific column on the board."""
    if column_name is None:
        column_name = get_inbox_column()

    state = load_board()

    # Find or create column
    target_col = next((c for c in state.columns if c.name == column_name), None)
    if not target_col:
        target_col = BoardColumn(name=column_name)
        state.columns.append(target_col)

    # Check if card already exists on board
    for col in state.columns:
        if card_id in col.card_ids:
            if col.name == column_name:
                return  # Already there
            col.card_ids.remove(card_id)  # Move from other column

    target_col.card_ids.append(card_id)
    save_board(state)
