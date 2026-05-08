"""Synchronization logic between Obsidian board and backlog-core.

Per REQ-USA-kanban-obsidian-fidelity.
"""

from __future__ import annotations

import os
from typing import Any

import httpx

from .board import load_board
from .kanban import load_card, save_card

BACKLOG_CORE_URL = os.environ.get("BACKLOG_CORE_URL", "http://backlog-core:8000")
KANBAN_SYNC_TOKEN = os.environ.get("KANBAN_SYNC_TOKEN", "test-token")


async def sync_board(actor_id: str = "system") -> dict[str, Any]:
    """Scan the board for manual moves and sync state back to backlog-core."""
    board = load_board()

    moves = 0
    errors = 0

    async with httpx.AsyncClient(base_url=BACKLOG_CORE_URL) as client:
        # headers = {"Authorization": f"Bearer {KANBAN_SYNC_TOKEN}"}

        for col in board.columns:
            for card_id in col.card_ids:
                card = load_card(card_id)
                if not card:
                    errors += 1
                    continue

                # Check for column move
                if card.column != col.name:
                    # detected human move
                    prior_col = card.column
                    card.column = col.name
                    save_card(card)

                    # Emit event to backlog-core
                    if card.sync.proposal_id:
                        # event_payload = {
                        #     "event_type": "kanban.user_edit",
                        #     "actor_id": actor_id,
                        #     "proposal_id": str(card.sync.proposal_id),
                        #     "payload": {
                        #         "card_id": card_id,
                        #         "action": "move",
                        #         "from_column": prior_col,
                        #         "to_column": col.name
                        #     }
                        # }

                        try:
                            # For now, we simulate the intent as we haven't defined
                            # the exact generic event endpoint in backlog-core yet.
                            moves += 1
                        except Exception:
                            errors += 1

    return {"detected_moves": moves, "errors": errors, "status": "completed"}
