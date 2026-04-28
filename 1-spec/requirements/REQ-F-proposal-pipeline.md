# REQ-F-proposal-pipeline: Every agent mutation flows through propose → validate → apply with linked audit chain

**Type**: Functional

**Status**: Draft

**Priority**: Must-have

**Source**: [GOAL-trustworthy-supervised-agent](../goals/GOAL-trustworthy-supervised-agent.md), [CON-no-direct-agent-writes](../constraints/CON-no-direct-agent-writes.md)

**Source stakeholder**: [STK-vincent](../stakeholders.md), [STK-ben](../stakeholders.md)

## Description

Every agent-initiated mutation to a system of record (`backlog-core`, GBrain, Kanban) flows through a uniform three-step pattern:

1. **Propose** — the agent emits a `proposal` event in `backlog-core` carrying:
   - `proposal_id` (unique, used to chain the rest)
   - `actor_id = hermes` (or other agent id)
   - `tool_id` (the dedicated persistence tool that would apply the proposal)
   - `content` (the proposed mutation, in the tool's schema)
   - `gate_inputs` (`confidence`, `gate_band`, `consent_snapshot`, `whitelist_entry`, `auto_policy`)
   - `source_input_event_id` (originating event, if any)
   - `cited_pages`, `learnings_applied`

2. **Validate** — the owning persistence service (`backlog-core` for events, `gbrain-bridge` for GBrain pages, `kanban-sync` for cards) validates the proposal against schema, retention-class invariants, redaction precondition, and bidirectional-link integrity. Validation outcome is one of:
   - `apply` — invariants hold; service applies the mutation.
   - `reject` — at least one invariant fails; mutation is not applied; rejection reason recorded.

3. **Apply or reject** — the service emits a `proposal.applied` or `proposal.rejected` audit event chained to the original `proposal_id`. Applied proposals also produce the resulting state-change events (e.g., `kanban.card_created`, `gbrain.page_updated`) chained to the same `proposal_id`.

No agent code may bypass this pipeline. Tools that perform mutations without a corresponding `proposal_id` linkage are detected by [REQ-REL-audit-reconciliation](REQ-REL-audit-reconciliation.md) and alerted.

## Acceptance Criteria

- Given any agent-initiated mutation that landed in storage, when an audit query is run for its `proposal_id`, then it resolves the full chain (proposal → validation → apply → resulting state events); no chain links are missing.
- Given a proposal that violates a validation invariant (e.g., a `derived_keep` payload containing raw content), when the service evaluates it, then `proposal.rejected` is emitted with structured reason and no state mutation occurs.
- Given a tool that attempts a direct mutation without first emitting a `proposal` event, when reconciliation runs, then the mutation is flagged as unmatched and triggers an alert per [REQ-REL-audit-reconciliation](REQ-REL-audit-reconciliation.md).

## Related Constraints

- [CON-no-direct-agent-writes](../constraints/CON-no-direct-agent-writes.md) — defines the proposal pipeline as the only legitimate mutation path.
- [CON-confidence-gated-autonomy](../constraints/CON-confidence-gated-autonomy.md) — the gate runs before the proposal is emitted; gate inputs are recorded on the proposal.
