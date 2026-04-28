# DEC-obsidian-as-review-ui: Trail

> Companion to `DEC-obsidian-as-review-ui.md`.

## Alternatives considered

### Option A: Obsidian as the review UI (chosen)
- Pros: Reuses an interface operators already use (`GOAL-durable-project-memory` puts the vault at the center anyway); zero new components — disposition lives in `gbrain-bridge`'s watch loop; review items become first-class GBrain pages with full frontmatter, traceability, and link-back.
- Cons: Disposition latency depends on Obsidian's file-watcher; command-palette wiring is per-vault setup; complex review actions (multi-step approvals, custom pickers) get awkward.

### Option B: Web UI
- Pros: Familiar pattern for review-queue interactions; supports rich pickers and dashboards; multi-operator-friendly.
- Cons: Adds a frontend service to the Compose stack; doubles the operator-surface code (CLI + web + Obsidian); ergonomic improvements over Obsidian are marginal at MVP scale.

### Option C: CLI-only
- Pros: Simplest possible — no UI infrastructure; transactional clarity per command.
- Cons: For frequent review actions, command-line cycle is slower than a click-through; operators (especially Vincent, less ops-comfortable) get a less ergonomic surface; cross-references to GBrain content require copy-paste of identifiers.

## Reasoning

Option A was chosen because the project memory already centers on Obsidian (`GOAL-durable-project-memory`, `US-browse-project-memory`); making the review queue *also* live in the vault means operators stay in one tool. Each review item becomes a GBrain page with all the cross-linking benefits the rest of the vault has. The watch-script approach keeps the implementation localized to `gbrain-bridge` instead of adding a frontend service.

The CLI remains the right answer for transactional, high-stakes actions (RTBF, source registration, secret rotation) — those benefit from explicit, scripted invocation rather than vault-mediated disposition.

Accepted trade-off: complex multi-step review actions are awkward in the command palette. Mitigation: structured prompts via the watch script; if any operation outgrows command-palette ergonomics, that operation gets a CLI command instead — still no new frontend service.

## Human involvement

**Type**: human-decided

**Notes**: User explicitly chose this option ("Obsidian-as-UI") in the architecture-framing question Q-1 (2026-04-27). Recorded as `human-decided` rather than `ai-proposed/human-approved` because the user actively selected this option from a presented set rather than approving an AI proposal.

## Changelog

| Date | Change | Involvement |
|------|--------|-------------|
| 2026-04-27 | Initial decision; user chose this option from a presented set | human-decided |
