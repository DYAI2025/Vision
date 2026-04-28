# US-review-and-act-on-proposal: Accept, edit, or reject agent proposals from one surface

**As a** collaborator, **I want** to accept, edit, or reject agent proposals from a single review surface, **so that** I can keep up with agent activity without context-switching between Obsidian, the kanban, and a CLI.

**Status**: Draft

**Priority**: Must-have

**Source stakeholder**: [STK-vincent](../stakeholders.md), [STK-ben](../stakeholders.md)

**Related goal**: [GOAL-trustworthy-supervised-agent](../goals/GOAL-trustworthy-supervised-agent.md)

## Acceptance Criteria

- Given an open agent proposal, when the collaborator accepts, edits, or rejects it, then the disposition takes immediate effect against the affected artifact and is recorded as an event in `backlog-core` with `actor_id`, `tool_id`, and `proposal_id`.
- Given any disposition (accept / edit / reject), when it is recorded, then a `learning_event` is emitted automatically with the required fields populated; the collaborator does not need to author it manually.

## Derived Requirements

- [REQ-F-correction-actions](../requirements/REQ-F-correction-actions.md)
- [REQ-F-proposal-pipeline](../requirements/REQ-F-proposal-pipeline.md)
