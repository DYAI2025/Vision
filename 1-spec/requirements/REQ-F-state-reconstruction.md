# REQ-F-state-reconstruction: Backlog-Core can reconstruct full project state from the event log

**Type**: Functional

**Status**: Draft

**Priority**: Must-have

**Source**: [GOAL-trustworthy-supervised-agent](../goals/GOAL-trustworthy-supervised-agent.md), [CON-no-direct-agent-writes](../constraints/CON-no-direct-agent-writes.md)

**Source stakeholder**: [STK-vincent](../stakeholders.md), [STK-ben](../stakeholders.md)

## Description

Given the `backlog-core` event log up to time `T`, the system can reconstruct the full project state at `T` from the event log alone. Reconstructed state covers:

- All projects and their current status
- Per-project Kanban-card snapshot (columns, cards, ordering, content)
- Per-project artifact set (tasks, proposals, decisions, risks, open questions)
- Consent records per source (current state and full append-only history per [REQ-COMP-consent-record](REQ-COMP-consent-record.md))
- Audit-log chain head and integrity check
- Per-source `routing_rules` and learning-event chains
- GBrain page references (the events that *would* have written which pages — actual GBrain content lives in the vault, but the events that drove every page are replayable)

Reconstruction is **deterministic**: the same event log replayed by the same code produces bit-identical state. Reconstruction is **side-effect-free against external systems** when run in a "preview" mode — it must not mutate GBrain, Kanban, or audit log; it produces an in-memory state representation the operator can compare against current production state.

The reconstruction tool is operator-invokable for three primary uses:

1. **Rollback preview** — show what state would be after dropping events from time `T` onward.
2. **Audit replay** — verify any agent action by replaying its proposal chain and observing the resulting state.
3. **Disaster recovery** — rebuild a fresh deployment from a saved event log when a vault or kanban backup is unavailable but the event log survives.

## Acceptance Criteria

- Given an event log captured up to time `T` and the live state at time `T`, when reconstruction runs in preview mode, then the reconstructed state is bit-identical to the live state across project records, consent records, and Kanban-card snapshot (modulo timestamps that record the reconstruction itself).
- Given the same event log replayed twice, when both reconstructions complete, then they produce identical state — replay is deterministic.
- Given a request to reconstruct state at an earlier time `T - Δ`, when reconstruction runs, then the produced state corresponds to the system as it existed at `T - Δ`, with all events at or after that time excluded.

## Related Constraints

- [CON-no-direct-agent-writes](../constraints/CON-no-direct-agent-writes.md) — only events can mutate state; reconstruction works because every mutation is an event.

## Related Assumptions

- [ASM-subject-reference-resolvable](../assumptions/ASM-subject-reference-resolvable.md) — reconstruction depends on stable subject references for replay across stores.
