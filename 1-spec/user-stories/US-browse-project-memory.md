# US-browse-project-memory: Navigate any project's state, decisions, and learnings in Obsidian

**As a** collaborator, **I want** to open the GBrain vault in Obsidian and navigate any project's current state, decisions, and learnings via internal links, **so that** I can review status, history, and rationale without asking the agent or hunting through chat logs.

**Status**: Draft

**Priority**: Must-have

**Source stakeholder**: [STK-vincent](../stakeholders.md), [STK-ben](../stakeholders.md)

**Related goal**: [GOAL-durable-project-memory](../goals/GOAL-durable-project-memory.md)

## Acceptance Criteria

- Given an opened GBrain vault, when the collaborator opens a project's `PROJECT.md`, then `PROFILE.md`, `CURRENT_STATE.md`, `BACKLOG_SUMMARY.md`, `OPEN_QUESTIONS.md`, `DECISIONS.md`, and `LEARNINGS.md` resolve via valid internal links and render with their frontmatter and content intact.
- Given any artifact in the vault (episode, decision, learning, person), when the collaborator follows its bidirectional links, then linked artifacts open without broken-link errors and link-back integrity is preserved (a link from A to B implies a link from B to A where the schema requires it).

## Derived Requirements

- [REQ-F-gbrain-schema](../requirements/REQ-F-gbrain-schema.md)
- [REQ-F-bidirectional-links](../requirements/REQ-F-bidirectional-links.md)
- [REQ-MNT-vault-audit-sweep](../requirements/REQ-MNT-vault-audit-sweep.md)
