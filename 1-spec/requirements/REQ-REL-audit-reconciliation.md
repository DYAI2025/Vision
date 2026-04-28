# REQ-REL-audit-reconciliation: Daily reconciliation detects gate bypasses, unmatched mutations, and orphan audits

**Type**: Reliability

**Status**: Draft

**Priority**: Must-have

**Source**: [GOAL-trustworthy-supervised-agent](../goals/GOAL-trustworthy-supervised-agent.md), [CON-no-direct-agent-writes](../constraints/CON-no-direct-agent-writes.md)

**Source stakeholder**: [STK-vincent](../stakeholders.md), [STK-ben](../stakeholders.md)

## Description

A reconciliation job runs at least once per day (configurable cadence, ≥1×/day) and compares:

- **(A)** Committed mutation events in `backlog-core`, GBrain, and Kanban over the reconciliation window.
- **(B)** Audit-log entries with matching `proposal_id`s over the same window.

The job produces three counts per run:

1. **Unmatched mutations** — committed mutations whose `proposal_id` resolves to no proposal event, or whose chain (proposal → validation → apply) is incomplete. **Target: 0.** Any non-zero count triggers a high-priority alert and lists the offending mutation ids.
2. **Gate bypasses** — committed mutations whose audit chain shows the gate did not run (e.g., `gate_decision = null`, `gate_skipped = true`, or no gate-decision sub-event in the chain). **Target: <1% per session.** Non-zero counts trigger a warning and a per-event remediation ticket.
3. **Orphan audit entries** — `proposal` events whose corresponding mutation never committed and that are not paired with a `proposal.rejected` event. Recorded but not alerted (legitimate cause: rollback / process crash mid-pipeline).

Each reconciliation run produces a report stored as a `derived_keep` GBrain page at `05_Learnings/agent-behavior/reconciliation/<run-date>.md`, containing the three counts, lists of affected ids, and a per-run summary. The report itself is a learning artifact — recurring patterns of bypass or unmatched mutation can be turned into formal `DEC-*` decisions.

## Acceptance Criteria

- Given a session with one deliberate gate-bypass injection (a tool configured to mutate without invoking the gate), when the next reconciliation runs, then the bypass is detected, the bypass count for the window is non-zero, the alert fires, and the offending mutation id is listed in the report.
- Given a clean session (no bypasses, no unmatched mutations), when reconciliation runs, then unmatched-mutations count is 0, gate-bypass count is 0, and the report records this clean state.
- Given a `proposal.rejected` event with no matching mutation, when reconciliation runs, then it is recognized as a legitimate orphan (not alerted) and recorded in the orphan-audit count.

## Related Constraints

- [CON-no-direct-agent-writes](../constraints/CON-no-direct-agent-writes.md) — reconciliation is the structural enforcement that the proposal pipeline cannot be bypassed silently.
- [CON-confidence-gated-autonomy](../constraints/CON-confidence-gated-autonomy.md) — gate-bypass detection is a reliability check on the gate's coverage.
