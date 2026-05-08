"""Review dashboard generator for kanban-sync.

Per DEC-obsidian-as-review-ui.
Maintains a central Review.md file for human disposition of proposals.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path

import httpx

from .kanban import kanban_subtree

BACKLOG_CORE_URL = os.environ.get("BACKLOG_CORE_URL", "http://backlog-core:8000")
KANBAN_SYNC_TOKEN = os.environ.get("KANBAN_SYNC_TOKEN", "test-token")


def get_review_file_path() -> Path:
    return kanban_subtree() / "09_Inbox" / "Review.md"


async def update_review_dashboard() -> dict[str, Any]:
    """Fetch pending proposals and refresh the Review.md dashboard."""
    
    async with httpx.AsyncClient(base_url=BACKLOG_CORE_URL) as client:
        headers = {"Authorization": f"Bearer {KANBAN_SYNC_TOKEN}"}
        resp = await client.get("/v1/proposals?status=pending", headers=headers)
        resp.raise_for_status()
        proposals = resp.json()

    lines = [
        "# 📥 Review Queue",
        f"Last Updated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC",
        "",
        "## Pending Proposals",
        "Mark the checkbox `[x]` to approve a proposal. It will be moved to the Kanban board.",
        ""
    ]

    if not proposals:
        lines.append("_No pending proposals._")
    else:
        for p in proposals:
            p_id = p["proposal_id"]
            title = p["content"].get("title", "Untitled")
            conf = int(p["gate_inputs"].get("confidence", 0) * 100)
            band = p["gate_inputs"].get("gate_band", "low")
            
            # Format: - [ ] [[proposal-id]] Title | Conf: 90% | Band: high
            lines.append(f"- [ ] [[{p_id}]] **{title}** | Conf: {conf}% | Band: {band}")

    file_path = get_review_file_path()
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Simple write for now, no complex merge
    file_path.write_text("\n".join(lines), encoding="utf-8")
    
    return {
        "proposal_count": len(proposals),
        "status": "updated"
    }
