# REQ-F-learning-loop: Within-session learning loop refreshes context and routing rules eagerly

**Type**: Functional

**Status**: Draft

**Priority**: Must-have

**Source**: [US-see-learning-effect](../user-stories/US-see-learning-effect.md), [CON-human-correction-priority](../constraints/CON-human-correction-priority.md)

**Source stakeholder**: [STK-vincent](../stakeholders.md), [STK-ben](../stakeholders.md)

## Description

The `learning-loop` skill in `hermes-runtime` reads recent `learning_event`s for the **affected scope** (project, source, action class) and applies them to subsequent agent proposals within the same working session. The loop performs three actions on each new `learning_event`:

1. **Prompt-context refresh** — the most recent and most relevant learnings for the affected scope are added to the agent's prompt context. Older learnings can fall off via a recency + relevance score; learnings explicitly tagged `permanent` (via a future operator action) never fall off.
2. **Project-profile update** — the project's `PROFILE.md` and any relevant routing-rules pages in GBrain are updated via `gbrain-memory-write`, recording the corrected pattern.
3. **Marking subsequent proposals** — the next agent proposals in the affected scope are tagged with `learnings_applied: [learning_event_id, ...]` so [REQ-F-decision-inspection](REQ-F-decision-inspection.md) can show them.

The loop runs **eagerly**: the next agent action in the affected scope after a correction reads the new learning before scoring or proposing — there is no batch-refresh latency between correction and effect.

Out of scope at MVP: model fine-tuning, embedding-space updates beyond what `gbrain-memory-write` produces incidentally. Those become candidates if [ASM-in-session-learning-feasible](../assumptions/ASM-in-session-learning-feasible.md) is invalidated.

## Acceptance Criteria

- Given a correction emitted in scope S at time T, when the next agent proposal in scope S after T is generated, then the proposal carries `learnings_applied` referencing the new `learning_event_id`, and at least the proposal's prompt context demonstrably reflects the correction (verified by reading the proposal's recorded prompt-context snapshot).
- Given a series of paired test events — a known-incorrect input, a correction, then a paraphrase of the original — when the agent processes the paraphrase, then the resulting proposal differs from the pre-correction proposal along the corrected axis (different `project_id`, different artifact type, different confidence band, etc., as the test specifies).
- Given multiple `learning_event`s on overlapping scopes, when the loop applies them, then the most recent learning takes precedence for conflicts, and prior learnings remain visible (not deleted) so the precedence chain is auditable.

## Related Constraints

- [CON-human-correction-priority](../constraints/CON-human-correction-priority.md) — the loop is the structural mechanism that makes corrections training-signal rather than noise.

## Related Assumptions

- [ASM-in-session-learning-feasible](../assumptions/ASM-in-session-learning-feasible.md) — assumes prompt-context refresh + routing-rules update is sufficient for visible behavior change in-session.
