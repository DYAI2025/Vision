# REQ-F-duplicate-detection: Same content from multiple sources produces at most one artifact

**Type**: Functional

**Status**: Draft

**Priority**: Must-have

**Source**: [GOAL-multi-source-project-ingestion](../goals/GOAL-multi-source-project-ingestion.md)

**Source stakeholder**: [STK-vincent](../stakeholders.md), [STK-ben](../stakeholders.md)

## Description

A duplicate-detection step compares each newly-routed `input_event` against recent events within the same project window (configurable, default 7 days) using both **semantic similarity** (embedding cosine distance against the new event's content) and **lexical / source heuristics** (n-gram overlap, sender id correspondence, manual repaste markers). When the combined score exceeds the duplicate threshold:

- The new event does **not** produce a fresh extracted artifact.
- The existing artifact (kanban card / task / proposal) gains a `duplicate_of` reference linking back to the new `input_event`.
- A `duplicate.detected` event is appended to `backlog-core` with the matched `existing_artifact_id`, the `new_input_event_id`, and the similarity scores.

The threshold is configurable per project. Confirmed duplicates that turn out to be legitimately distinct (false positive) can be split via a manual operator action; the split is recorded as a `learning_event` so the duplicate detector improves on the same pattern.

## Acceptance Criteria

- Given a labeled set of true duplicates and true non-duplicates within a 7-day project window, when the detector runs, then false-negative rate ≤5% (true duplicates missed) and false-positive rate ≤2% (non-duplicates flagged).
- Given an `input_event` that the detector flags as duplicate, when downstream processing runs, then no fresh artifact is created; the existing artifact's card shows the new `input_event` listed as a duplicate source.
- Given a flagged duplicate that the operator splits, when the split action is recorded, then a `learning_event` of type `duplicate_correction` is emitted with the original similarity scores and the corrected outcome.

## Related Constraints

- [CON-no-direct-agent-writes](../constraints/CON-no-direct-agent-writes.md) — duplicate links flow through `kanban-sync` like any other mutation.
- [CON-human-correction-priority](../constraints/CON-human-correction-priority.md) — operator splits feed back as learning signal.
