"""Kanban-subtree filesystem configuration and logic.

Per REQ-USA-kanban-obsidian-fidelity.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

import yaml
from filelock import FileLock

from .models import CardRecord, CardSyncFields

DEFAULT_VAULT_PATH = "/vault"
DEFAULT_KANBAN_SUBTREE = "/vault/Kanban"


def vault_path() -> Path:
    """Read VAULT_PATH from env (default: /vault). Read-only access scope."""
    raw = os.environ.get("VAULT_PATH") or DEFAULT_VAULT_PATH
    return Path(raw)


def kanban_subtree() -> Path:
    """Read KANBAN_SUBTREE from env (default: /vault/Kanban). Read/write scope."""
    raw = os.environ.get("KANBAN_SUBTREE") or DEFAULT_KANBAN_SUBTREE
    return Path(raw)


def get_inbox_column() -> str:
    """Read KANBAN_INBOX_COLUMN from env (default: Inbox)."""
    return os.environ.get("KANBAN_INBOX_COLUMN", "Inbox")


def is_writable(path: Path) -> bool:
    """Return True iff `path` exists, is a directory, and passes write checks."""
    try:
        if not path.exists() or not path.is_dir():
            return False
        mode = os.R_OK | os.W_OK | os.X_OK
        return os.access(path, mode)
    except OSError:
        return False


def _cards_dir() -> Path:
    return kanban_subtree() / "cards"


def save_card(card: CardRecord) -> Path:
    """Save a card to its .md file in the vault."""
    cards_dir = _cards_dir()
    cards_dir.mkdir(parents=True, exist_ok=True)

    file_path = cards_dir / f"{card.card_id}.md"
    lock_path = file_path.with_suffix(".lock")

    # Merge sync, column, and user fields for frontmatter
    # We use model_dump(mode="json") to ensure UUIDs and datetimes are serialized to strings
    frontmatter = card.user_fields.copy()
    sync_data = card.sync.model_dump(mode="json", exclude_none=True)
    frontmatter.update(sync_data)
    if card.column:
        frontmatter["column"] = card.column

    yaml_text = yaml.safe_dump(frontmatter, sort_keys=False)

    content = f"---\n{yaml_text}---\n# {card.title}\n\n{card.content}\n"

    with FileLock(lock_path):
        file_path.write_text(content, encoding="utf-8")

    return file_path


def load_card(card_id: str) -> CardRecord | None:
    """Load a card from its .md file."""
    file_path = _cards_dir() / f"{card_id}.md"
    if not file_path.exists():
        return None

    lock_path = file_path.with_suffix(".lock")

    with FileLock(lock_path):
        text = file_path.read_text(encoding="utf-8")

    # Simple regex-based frontmatter split
    match = re.match(r"^---\n(.*?)\n---\n(.*)", text, re.DOTALL)
    if not match:
        # No frontmatter?
        title_match = re.search(r"^# (.*)", text, re.MULTILINE)
        return CardRecord(
            card_id=card_id,
            title=title_match.group(1) if title_match else card_id,
            content=text,
        )

    raw_yaml = match.group(1)
    body = match.group(2).strip()

    try:
        raw_frontmatter = yaml.safe_load(raw_yaml) or {}
    except yaml.YAMLError:
        # Graceful fallback for corrupt frontmatter per code review
        raw_frontmatter = {}

    # Extract title from body # H1
    title_match = re.search(r"^# (.*)", body, re.MULTILINE)
    title = title_match.group(1) if title_match else card_id

    # Split sync vs user vs column fields
    sync_field_names = CardSyncFields.model_fields.keys()
    sync_data = {k: v for k, v in raw_frontmatter.items() if k in sync_field_names}

    column = raw_frontmatter.get("column")

    # User fields are anything NOT sync and NOT column
    user_data = {
        k: v for k, v in raw_frontmatter.items() if k not in sync_field_names and k != "column"
    }

    return CardRecord(
        card_id=card_id,
        title=title,
        content=body,
        sync=CardSyncFields(**sync_data),
        user_fields=user_data,
        column=column,
    )
