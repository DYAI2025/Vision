# CON-no-direct-agent-writes: Agents mutate state only through dedicated, audited tools

**Category**: Operational

**Status**: Active

**Source stakeholder**: [STK-vincent](../stakeholders.md), [STK-ben](../stakeholders.md)

## Description

Hermes (and any future agent in the system) must not write directly to systems of record. All mutations go through dedicated tools, each of which validates the proposal, applies it within the boundaries of its own service, and emits both an audit entry and a memory entry:

- `backlog-core` for append-only event-sourced project state (proposals, tasks, decisions, project state reconstruction)
- `gbrain-memory-write` for the human-readable semantic vault (project pages, episodes, decisions, learnings)
- `kanban-sync` for the Obsidian Kanban markdown boards

Direct database writes, vault filesystem writes, kanban-file edits, network filesystem mutations, or any path that bypasses the proposal-validate-apply-audit loop is **prohibited**. The agent's tool whitelist is configured negatively: anything not on the allow list is denied at the runtime boundary, not at the application layer.

Reads are not gated by this constraint — Hermes may freely read from any service it has read access to. The rule is about mutations.

## Rationale

Preserves a single, auditable mutation path. Without it, rollback becomes meaningless (no canonical event log to replay against), audit becomes incomplete (some mutations aren't recorded), and shadow state can accumulate (the agent's view of "what's true" diverges from the system of record).

Closely related to [CON-confidence-gated-autonomy](CON-confidence-gated-autonomy.md) — the gate decides whether to attempt an action; this constraint defines how attempted actions reach storage.

## Impact

- Architectural — defines the service boundary between `hermes-runtime` (which holds the agent + skills) and the persistence services (`backlog-core`, `gbrain-bridge`, `kanban-sync`). Each persistence service exposes a narrow tool surface; Hermes' container has no credentials for direct DB / vault / file access.
- Drives a runtime tool-whitelist mechanism (declared per skill / per project, enforced at invocation).
- Drives audit-log schema: every mutation carries `actor_id`, `tool_id`, `proposal_id`, `pre_state_hash` and `post_state_hash` (or equivalent), and `confidence` from the gate.
- Drives `learning_event` schema: corrections recorded under [CON-human-correction-priority](CON-human-correction-priority.md) reference the same `proposal_id` so corrections trace cleanly back to the originating action.
