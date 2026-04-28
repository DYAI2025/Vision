# REQ-USA-kanban-obsidian-fidelity: Kanban boards remain operationally usable in stock Obsidian after sync

**Type**: Usability

**Status**: Draft

**Priority**: Must-have

**Source**: [US-see-extracted-artifacts](../user-stories/US-see-extracted-artifacts.md), [GOAL-durable-project-memory](../goals/GOAL-durable-project-memory.md)

**Source stakeholder**: [STK-vincent](../stakeholders.md), [STK-ben](../stakeholders.md)

## Description

The Kanban boards produced and maintained by `kanban-sync` are operationally usable in stock Obsidian with the Obsidian Kanban community plugin, without setup beyond opening the vault folder. Required properties:

**Render correctness:**

- Boards open without parse errors in the stock Obsidian Kanban plugin.
- Card frontmatter renders cleanly (no orphan keys, no invalid YAML).
- Internal links from a card back to its source `input_event` (in `backlog-core`'s human-readable mirror in GBrain) are clickable and resolve.
- Internal links from a card to its project page (`PROJECT.md`) are clickable and resolve.

**Sync-vs-edit boundary:**

- `kanban-sync` writes only **declared sync-owned fields** of a card's frontmatter (e.g., `proposal_id`, `extraction_confidence`, `source_input_event_id`, `cited_pages`, `learnings_applied`).
- Human-edited fields outside the sync-owned set (operator notes, ad-hoc tags, due-date overrides, custom labels) are **preserved across sync** — `kanban-sync` does not overwrite, drop, or normalize them.
- The set of sync-owned fields is documented and version-tagged in the schema; adding a field to the sync-owned set is a deliberate change, not an accident.

**Detection of human edits:**

- Manual column moves (operator drags a card from "In Progress" to "Done") are detected by `kanban-sync` on the next run and recorded as `kanban.user_edit` events in `backlog-core` with `actor_id`, `card_id`, before/after column.
- Manual content edits to a card's body or non-sync-owned frontmatter are detected (per [REQ-F-correction-actions](REQ-F-correction-actions.md)'s `unattributed_edit` handling) and surfaced for formal disposition; they are not silently propagated as learnings.

**Out of scope:**

- Custom Obsidian themes, vault-specific plugins beyond Kanban, or Obsidian Sync. These are the operator's prerogative; the system does not depend on them.

## Acceptance Criteria

- Given a freshly created board produced by `kanban-sync`, when the operator opens the vault in stock Obsidian with the Kanban plugin installed, then the board renders without parse errors; card frontmatter and internal links are clickable.
- Given a card whose operator has added a non-sync-owned field (e.g., `note: "follow up next sprint"`), when `kanban-sync` next runs and updates the card's sync-owned fields, then the operator-added field is preserved unchanged.
- Given an operator-initiated column move from "In Progress" to "Done", when `kanban-sync` next runs, then a `kanban.user_edit` event is recorded with the move details; reconciliation can map the move to the operator who made it.

## Related Constraints

- [CON-no-direct-agent-writes](../constraints/CON-no-direct-agent-writes.md) — agent writes go through `kanban-sync` and only touch sync-owned fields.
- [CON-human-correction-priority](../constraints/CON-human-correction-priority.md) — human edits to non-sync-owned fields are first-class signals that survive sync.
