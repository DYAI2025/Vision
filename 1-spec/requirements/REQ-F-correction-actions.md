# REQ-F-correction-actions: Accept, edit-and-accept, and reject primitives wired to every agent surface

**Type**: Functional

**Status**: Draft

**Priority**: Must-have

**Source**: [US-review-and-act-on-proposal](../user-stories/US-review-and-act-on-proposal.md), [CON-human-correction-priority](../constraints/CON-human-correction-priority.md)

**Source stakeholder**: [STK-vincent](../stakeholders.md), [STK-ben](../stakeholders.md)

## Description

Every surface that displays an agent proposal exposes three explicit primitives:

- **Accept** — apply the proposal as-is.
- **Edit-and-accept** — modify the proposal's content, then apply the modified version.
- **Reject** — discard the proposal; record the reason.

The surfaces that must support these primitives at MVP:

- Kanban cards (in Obsidian via `kanban-sync` markdown conventions)
- Review-queue entries
- Project page proposal sections (GBrain)
- Routing decisions in the operator's review surface

Every disposition is recorded in `backlog-core` as a `proposal.disposition` event with: `proposal_id`, `actor_id` (the human), `disposition` (`accept` / `edit_and_accept` / `reject`), optional `human_feedback` text, and (for edits) the diff between proposal content and accepted content.

For every disposition, a `learning_event` is emitted automatically with required fields populated:
- `learning_type` (`routing` / `extraction` / `confidence` / `correction` / `project_structure` / `agent_behavior`)
- `before` (proposal content + scoring inputs)
- `after` (accepted content or rejection)
- `actor_id`
- `applies_to` (scope: project, source, action class)
- `confidence_before`
- `confidence_after` (1.0 for human disposition; influences future scoring)
- `human_feedback` (if provided)

Free-form Obsidian edits made outside the disposition primitives (e.g., the user opens a card and changes its body manually) are detected by `kanban-sync` (file-level diff against last-applied state) and surfaced for the operator to formally accept/edit/reject — they do **not** silently propagate as learnings.

## Acceptance Criteria

- Given any displayed agent proposal, when the operator selects accept / edit-and-accept / reject, then both a `proposal.disposition` event and a `learning_event` are emitted with all required fields; reconciliation finds zero dispositions without a paired `learning_event`.
- Given a free-form Obsidian edit on a kanban card outside the primitives, when `kanban-sync` next runs, then the edit is detected, surfaced as an `unattributed_edit` review item, and not propagated as a `learning_event` until formally dispositioned.
- Given an `edit-and-accept` disposition, when the audit log is queried, then both the original proposal content and the accepted (edited) content are recoverable, with the diff visible.

## Related Constraints

- [CON-human-correction-priority](../constraints/CON-human-correction-priority.md) — corrections are first-class events, not free-form edits.
- [CON-no-direct-agent-writes](../constraints/CON-no-direct-agent-writes.md) — dispositions flow through the proposal pipeline.
