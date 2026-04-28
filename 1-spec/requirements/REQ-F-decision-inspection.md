# REQ-F-decision-inspection: Every agent proposal exposes an inspectable detail view

**Type**: Functional

**Status**: Draft

**Priority**: Must-have

**Source**: [US-inspect-agent-decision](../user-stories/US-inspect-agent-decision.md), [CON-confidence-gated-autonomy](../constraints/CON-confidence-gated-autonomy.md)

**Source stakeholder**: [STK-vincent](../stakeholders.md), [STK-ben](../stakeholders.md)

## Description

Every agent proposal — accepted, pending review, or suppressed — exposes a detail view containing:

- `confidence` (numeric)
- Gate band (`low` / `mid` / `high`)
- `cited_pages` (the GBrain pages the agent consulted, with link to each)
- `learnings_applied` (the `learning_event_id`s the agent considered, with link to each)
- Originating `input_event` reference (with link)
- The persistence tool that would (or did) apply the proposal
- For suppressed proposals: a structured `suppression_reason` (one of `confidence_low_band`, `consent_scope_missing`, `tool_not_whitelisted`, `auto_policy_disabled`, `subject_floor_breach`, `tooling_error_<id>`)
- For applied proposals: link to the resulting `proposal.applied` audit event and the produced artifacts

The detail view is reachable from:

- The Kanban card (link in card frontmatter or a dedicated section)
- The review-queue entry
- The audit-log entry (any `proposal.*` event opens to its detail view)

Suppressed proposals are first-class artifacts in this surface — they are not invisible. A `suppressed_proposal.recorded` event is in the audit log for every suppression, so silent rejection is impossible.

## Acceptance Criteria

- Given any `proposal_id`, when the operator opens the detail view, then all six fields above are populated (or explicitly `null` with a recorded reason); no field is silently absent.
- Given a suppressed proposal, when the detail view is opened, then the structured `suppression_reason` is shown and the operator can navigate from the suppression to the responsible gate-input fact (e.g., the source's `consent_scope` snapshot at the time of suppression).
- Given a free-form audit-log query for "agent did nothing on event X," when the operator runs it, then the query can resolve to a `suppressed_proposal.recorded` event for X with the suppression reason, or to no proposal events at all (in which case the agent never reached the action site for X).

## Related Constraints

- [CON-confidence-gated-autonomy](../constraints/CON-confidence-gated-autonomy.md) — suppression reasons map to gate decisions.
- [CON-no-direct-agent-writes](../constraints/CON-no-direct-agent-writes.md) — proposals and their audit chain are the only legitimate trace of agent behavior.
