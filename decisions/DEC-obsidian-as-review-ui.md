# DEC-obsidian-as-review-ui: Review queue and proposal-detail views are GBrain pages disposed via Obsidian command palette

**Status**: Active

**Category**: Architecture

**Scope**: backend (`gbrain-bridge` + `backlog-core` + operator UX)

**Source**: [REQ-F-review-queue](../1-spec/requirements/REQ-F-review-queue.md), [REQ-F-decision-inspection](../1-spec/requirements/REQ-F-decision-inspection.md), [REQ-F-correction-actions](../1-spec/requirements/REQ-F-correction-actions.md), [REQ-USA-kanban-obsidian-fidelity](../1-spec/requirements/REQ-USA-kanban-obsidian-fidelity.md)

**Last updated**: 2026-04-27

## Context

The review queue (`REQ-F-review-queue`), the agent-decision detail view (`REQ-F-decision-inspection`), and the correction-action surface (`REQ-F-correction-actions`) all need an operator-facing surface. Options:

- A dedicated web frontend service.
- A CLI for everything.
- Obsidian — items written as GBrain pages with structured frontmatter; dispositions via Obsidian command palette + a watch script.

The choice affects deployment surface area, operator UX consistency, and where new code lives.

## Decision

Review-queue items, agent-decision detail views, and correction-action prompts are written as GBrain pages with structured frontmatter under dedicated subtrees (`09_Inbox/review-queue/`, `09_Inbox/proposals/`, `05_Learnings/agent-behavior/reconciliation/`). Operators dispose of items by selecting an Obsidian command-palette command (e.g., `Vision: Accept proposal`, `Vision: Reject with reason`) wired to a lightweight watch script run by `gbrain-bridge`. The watch script reads the current page's frontmatter, prompts for any required input, and posts the disposition to `backlog-core`'s proposal-pipeline disposition endpoint.

The system therefore does **not** ship a dedicated web frontend service at MVP. The CLI remains for high-stakes transactional operations (source registration, RTBF, data export, backup/restore, secret rotation, install).

## Enforcement

### Trigger conditions

- **Design phase**: design choices that introduce operator-facing surfaces beyond the CLI must consult this decision before adding new components.
- **Code phase**: review-queue / proposal-detail / correction-action implementations target the GBrain page format and the Obsidian command-palette wiring; no new frontend service is added.

### Required patterns

- Review-queue items written by `backlog-core` → `gbrain-bridge` → vault subtree, with frontmatter declaring item type, `proposal_id`, `reason`, and candidate `proposed_dispositions`.
- Obsidian command-palette commands invoke a small companion script that reads the current page's frontmatter, prompts for any required input (e.g., reason text), and posts to `backlog-core`'s disposition endpoint.
- Watch-script implementation lives in `gbrain-bridge`'s service code; the Obsidian-side bindings ship as a small repo-shipped configuration that operators import into their vault.

### Required checks

1. Before adding any operator-facing capability, evaluate whether it fits the GBrain-page-plus-command-palette pattern; only add a new surface (CLI, web) when this pattern is genuinely insufficient.
2. Review-queue and proposal-detail pages must conform to `REQ-F-gbrain-schema` validation; out-of-schema pages are rejected at write time.

### Prohibited patterns

- Adding a dedicated frontend service for the review queue without superseding this decision.
- Disposition flows that bypass `backlog-core`'s disposition endpoint (e.g., direct vault edits that get retroactively reconciled — these are detected as `unattributed_edit` per `REQ-F-correction-actions` and require formal disposition).

## Reconsider trigger

Revisit this decision if:

- The disposition rate exceeds what command-palette ergonomics support (operators find themselves doing many actions per minute).
- A multi-operator setup beyond Vincent and Ben is introduced and Obsidian's single-vault model becomes a bottleneck.
- Observability needs (charts, dashboards) outgrow what GBrain pages can present.
