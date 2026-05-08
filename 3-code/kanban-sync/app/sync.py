"""Synchronization logic between Obsidian board and backlog-core.

Per REQ-USA-kanban-obsidian-fidelity.
"""

from __future__ import annotations

import os
import re
from typing import Any

import httpx

from .board import load_board
from .kanban import load_card, save_card
from .models import CardRecord
from .review import get_review_file_path, update_review_dashboard

BACKLOG_CORE_URL = os.environ.get("BACKLOG_CORE_URL", "http://backlog-core:8000")
KANBAN_SYNC_TOKEN = os.environ.get("KANBAN_SYNC_TOKEN", "test-token")


async def sync_board(actor_id: str = "system") -> dict[str, Any]:
    """Scan the board and review file for manual changes."""

    # 1. Update Review Dashboard (Pull from backlog-core)
    await update_review_dashboard()

    # 2. Check for Dispositions in Review.md
    review_path = get_review_file_path()
    dispositions = 0
    if review_path.exists():
        content = review_path.read_text(encoding="utf-8")
        # Find lines like - [x] [[uuid]]
        for line in content.splitlines():
            match = re.match(r"^- \[x\] \[\[(.*?)\]\]", line)
            if match:
                proposal_id = match.group(1).strip()
                # Emit disposition event
                async with httpx.AsyncClient(base_url=BACKLOG_CORE_URL) as client:
                    headers = {"Authorization": f"Bearer {KANBAN_SYNC_TOKEN}"}
                    try:
                        # For now, we simulate applying the proposal
                        # In real use, this would trigger the actual tool execution
                        await client.post(
                            "/v1/inputs",
                            json={
                                "event_type": "proposal.disposition",
                                "payload": {
                                    "proposal_id": proposal_id,
                                    "action": "applied",
                                    "reason": "Human checkbox marked in Obsidian",
                                },
                            },
                            headers=headers,
                        )
                        dispositions += 1
                    except Exception:
                        pass

    # 3. Standard Kanban Sync
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
                            # For now, we simulate the intent
                            moves += 1
                        except Exception:
                            errors += 1

    return {
        "detected_moves": moves,
        "detected_dispositions": dispositions,
        "errors": errors,
        "status": "completed",
    }
