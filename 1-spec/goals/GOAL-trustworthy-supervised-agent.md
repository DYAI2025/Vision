# GOAL-trustworthy-supervised-agent: Hermes operates under explicit human supervision, with corrections that improve behavior in-session

**Description**: A useful agent is one that humans actually let act. This goal makes Hermes trustworthy by construction: every action is gated by confidence and consent, every write is a proposal that flows through audited tools, every human correction is a first-class learning signal, and the agent visibly improves on the affected scope within the same working session — not after a nightly retrain. Supervision is not a "review tab" added later; it is the default interaction shape and the source of the system's accuracy strategy.

**Status**: Approved

**Priority**: Must-have

**Source stakeholder**: [STK-vincent](../stakeholders.md), [STK-ben](../stakeholders.md)

## Success Criteria

- [ ] **No silent writes**: 0 agent-initiated mutations to `backlog-core`, GBrain, or Kanban occur without an audit-log entry containing the gate decision, confidence value, tool id, and source `proposal_id`. Verified by reconciliation between mutation events and audit events at end-of-day.
- [ ] **Correction loop completeness**: 100% of human accept/edit/reject actions on agent proposals produce a `learning_event` with all required fields (`learning_type`, `before`, `after`, `actor_id`, `applies_to`, `confidence_before`, `confidence_after`).
- [ ] **Correction friction**: median time from "agent proposal visible" to "human disposition recorded" is **<30 seconds** for routine accept/reject, **<2 minutes** for edits.
- [ ] **In-session adaptation**: after a correction, the next ≥3 agent actions on the same affected scope (project, source, action class) reflect the correction — verified by boundary tests that issue a known-incorrect proposal, record a correction, and assert the next proposal differs along the corrected axis.
- [ ] **Gate compliance**: <1% of agent actions per session bypass the confidence gate (caused by tooling errors only, never by design); bypasses are logged and trigger an alert.
- [ ] **Auto-policy enforcement**: 0 high-band autonomous writes occur for action classes where the project's auto-policy is disabled, even at confidence ≥0.85.

## Related Artifacts

- Stakeholders: [STK-vincent](../stakeholders.md), [STK-ben](../stakeholders.md)
- Constraints: [CON-confidence-gated-autonomy](../constraints/CON-confidence-gated-autonomy.md), [CON-no-direct-agent-writes](../constraints/CON-no-direct-agent-writes.md), [CON-human-correction-priority](../constraints/CON-human-correction-priority.md), [CON-consent-required](../constraints/CON-consent-required.md)
- Decisions: [DEC-stakeholder-tiebreaker-consensus](../../decisions/DEC-stakeholder-tiebreaker-consensus.md)
- User stories: [US-review-and-act-on-proposal](../user-stories/US-review-and-act-on-proposal.md), [US-see-learning-effect](../user-stories/US-see-learning-effect.md), [US-inspect-agent-decision](../user-stories/US-inspect-agent-decision.md)
- Requirements: [REQ-F-proposal-pipeline](../requirements/REQ-F-proposal-pipeline.md), [REQ-F-correction-actions](../requirements/REQ-F-correction-actions.md), [REQ-F-learning-loop](../requirements/REQ-F-learning-loop.md), [REQ-F-decision-inspection](../requirements/REQ-F-decision-inspection.md), [REQ-REL-audit-reconciliation](../requirements/REQ-REL-audit-reconciliation.md), [REQ-F-confidence-gate](../requirements/REQ-F-confidence-gate.md), [REQ-SEC-audit-log](../requirements/REQ-SEC-audit-log.md), [REQ-F-state-reconstruction](../requirements/REQ-F-state-reconstruction.md), [REQ-REL-event-replay-correctness](../requirements/REQ-REL-event-replay-correctness.md)
- Assumptions: [ASM-in-session-learning-feasible](../assumptions/ASM-in-session-learning-feasible.md), [ASM-confidence-scores-are-meaningful](../assumptions/ASM-confidence-scores-are-meaningful.md)
