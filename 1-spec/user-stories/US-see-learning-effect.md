# US-see-learning-effect: See corrections reflected in subsequent agent behavior within the same session

**As a** collaborator, **I want** the agent to demonstrably reflect my recent corrections in its next proposals on the same scope (project, source, action class) within the same working session, **so that** I'm not correcting the same mistake repeatedly in a single sitting.

**Status**: Draft

**Priority**: Must-have

**Source stakeholder**: [STK-vincent](../stakeholders.md), [STK-ben](../stakeholders.md)

**Related goal**: [GOAL-trustworthy-supervised-agent](../goals/GOAL-trustworthy-supervised-agent.md)

## Acceptance Criteria

- Given the collaborator has just made a correction on a scope (e.g., re-routed an input from project X to project Y), when the agent processes the next inputs in that scope, then the resulting proposals apply the corrected pattern (visible via the proposal's cited learnings or its routing decision changing along the corrected axis).
- Given a session with multiple corrections, when the collaborator inspects an agent proposal, then they can see which `learning_event`s were considered and whether any contradicted the correction (so a divergence has a visible reason rather than appearing as silent regression).

## Derived Requirements

- [REQ-F-learning-loop](../requirements/REQ-F-learning-loop.md)
- [REQ-F-correction-actions](../requirements/REQ-F-correction-actions.md)
