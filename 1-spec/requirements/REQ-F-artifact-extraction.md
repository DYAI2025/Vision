# REQ-F-artifact-extraction: Extract typed artifacts from routed events through the proposal pipeline

**Type**: Functional

**Status**: Draft

**Priority**: Must-have

**Source**: [US-see-extracted-artifacts](../user-stories/US-see-extracted-artifacts.md), [CON-no-direct-agent-writes](../constraints/CON-no-direct-agent-writes.md)

**Source stakeholder**: [STK-vincent](../stakeholders.md), [STK-ben](../stakeholders.md)

## Description

For each `input_event` routed at confidence ≥0.85 (autonomous band) or accepted from the review queue with a confirmed `project_id`, the artifact-extraction step proposes typed artifacts and flows them through the proposal pipeline. Supported artifact types at MVP:

- `task` — actionable work item with title, description, optional assignee
- `proposal` — a recommendation or candidate decision pending human acceptance
- `decision_candidate` — a decision the input implies has been made or should be made
- `risk` — an identified risk with optional severity hint
- `open_question` — an unresolved question raised by the input

Each extracted artifact carries its own `extraction_confidence`. Each accepted artifact:

1. Becomes an event in `backlog-core` (`artifact.proposed` with type, content, confidence, source `input_event`).
2. Produces a Kanban card via `kanban-sync` carrying `input_event` reference, `extraction_confidence`, artifact type, and any cited GBrain pages.
3. Updates the project's GBrain page (`PROJECT.md`, `BACKLOG_SUMMARY.md`, or relevant subpage) via `gbrain-memory-write`.

Mid-band events (0.55 ≤ confidence < 0.85) do **not** produce extracted artifacts directly — they go to the review queue. Low-band events produce nothing beyond their `routing.decided` audit entry.

## Acceptance Criteria

- Given a project-relevant `input_event` routed at confidence ≥0.85, when extraction runs, then ≥1 artifact candidate is produced in the same processing pass (target: ≥80% on a labeled extraction set).
- Given an extracted artifact, when its Kanban card is opened in Obsidian, then the card displays the originating `input_event` reference, the `extraction_confidence`, the artifact type, and any cited GBrain pages (per [US-see-extracted-artifacts](../user-stories/US-see-extracted-artifacts.md)).
- Given an extraction attempt that produces no candidates (event was project-relevant but contained no extractable artifact), when extraction completes, then a `extraction.empty` audit event is recorded with the reason — silent zero-output is not permitted.

## Related Constraints

- [CON-no-direct-agent-writes](../constraints/CON-no-direct-agent-writes.md) — all writes go through the proposal pipeline + dedicated tools.
- [CON-confidence-gated-autonomy](../constraints/CON-confidence-gated-autonomy.md) — only autonomous-band events bypass review for extraction.

## Related Assumptions

- [ASM-confidence-scores-are-meaningful](../assumptions/ASM-confidence-scores-are-meaningful.md)
