# US-see-extracted-artifacts: Find extracted artifacts on the project kanban with traceability to their source

**As a** collaborator, **I want** extracted artifacts (tasks, proposals, decisions, risks, open questions) to appear on the project's Obsidian Kanban board with a link back to the source `input_event`, **so that** I can act on them in my normal workflow and trace what triggered each.

**Status**: Draft

**Priority**: Must-have

**Source stakeholder**: [STK-vincent](../stakeholders.md), [STK-ben](../stakeholders.md)

**Related goal**: [GOAL-multi-source-project-ingestion](../goals/GOAL-multi-source-project-ingestion.md)

## Acceptance Criteria

- Given a routed `input_event`, when artifact extraction succeeds, then matching cards (one per extracted artifact) appear on the project's Kanban board through `kanban-sync` and are visible in Obsidian without manual refresh.
- Given a card on the board, when the collaborator opens it, then it shows the originating `input_event` reference, the extraction confidence, the artifact type, and any cited GBrain pages.

## Derived Requirements

- [REQ-F-artifact-extraction](../requirements/REQ-F-artifact-extraction.md)
- [REQ-F-duplicate-detection](../requirements/REQ-F-duplicate-detection.md)
- [REQ-USA-kanban-obsidian-fidelity](../requirements/REQ-USA-kanban-obsidian-fidelity.md)
