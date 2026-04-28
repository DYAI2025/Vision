# US-inspect-agent-decision: Inspect why the agent made a particular proposal

**As a** collaborator, **I want** to inspect why the agent made a particular proposal — confidence, gate band, GBrain pages cited, learning events applied, and triggering input — **so that** I can decide whether to trust it, refine it, or correct it on an informed basis.

**Status**: Draft

**Priority**: Must-have

**Source stakeholder**: [STK-vincent](../stakeholders.md), [STK-ben](../stakeholders.md)

**Related goal**: [GOAL-trustworthy-supervised-agent](../goals/GOAL-trustworthy-supervised-agent.md)

## Acceptance Criteria

- Given any agent proposal, when the collaborator opens its detail view, then they see at minimum: confidence value, gate band, GBrain pages cited, `learning_event`s applied, the originating `input_event`, and the tool that would apply the proposal if accepted.
- Given a proposal that was suppressed (low confidence, missing consent scope, disabled auto-policy), when the collaborator inspects it, then the suppression reason is shown explicitly so silent rejections never appear as "the agent did nothing."

## Derived Requirements

- [REQ-F-decision-inspection](../requirements/REQ-F-decision-inspection.md)
- [REQ-F-confidence-gate](../requirements/REQ-F-confidence-gate.md)
