# REQ-F-project-routing: Each input event is scored against active projects with cited GBrain context

**Type**: Functional

**Status**: Draft

**Priority**: Must-have

**Source**: [US-ingest-from-any-channel](../user-stories/US-ingest-from-any-channel.md), [CON-no-direct-agent-writes](../constraints/CON-no-direct-agent-writes.md)

**Source stakeholder**: [STK-vincent](../stakeholders.md), [STK-ben](../stakeholders.md)

## Description

The routing layer takes a normalized `input_event` and produces a `routing_decision`:

```
{
  project_id: <project_uuid> | null,
  confidence: <0.0 .. 1.0>,
  cited_pages: [<gbrain_page_id>, ...],
  alternatives: [{project_id, confidence}, ...],
  reasoning_summary: <string>
}
```

Routing must perform a brain-first lookup before scoring: the layer queries GBrain (project profiles, recent episodes, learnings) and records the cited page ids in the decision so [`US-inspect-agent-decision`](../user-stories/US-inspect-agent-decision.md) can surface them.

`project_id = null` is a valid outcome when no project's confidence exceeds a defined floor (typically the low-band threshold of 0.55) — these events go to the review queue, not silently dropped.

The routing decision is recorded as a `routing.decided` event in `backlog-core` regardless of outcome (autonomous, review, drop) — every routing call leaves an audit trail.

## Acceptance Criteria

- Given a routable `input_event`, when routing completes, then the resulting `routing_decision` includes a non-empty `cited_pages` list (or an explicit `cited_pages = []` with `reasoning_summary` explaining why no relevant pages exist) and is persisted as a `routing.decided` event.
- Given a routing decision with confidence below 0.55, when downstream processing runs, then the event is queued for review (per [REQ-F-review-queue](REQ-F-review-queue.md)) rather than committed to a project.
- Given a labeled ground-truth set of routed events with confirmed correct project, when accuracy is measured at confidence ≥0.85 over a rolling 30-day window post-launch, then accuracy ≥85% (post-launch metric; not gate-blocking pre-launch).

## Related Constraints

- [CON-no-direct-agent-writes](../constraints/CON-no-direct-agent-writes.md) — routing decisions are events, not direct mutations.
- [CON-confidence-gated-autonomy](../constraints/CON-confidence-gated-autonomy.md) — confidence drives downstream branching.

## Related Assumptions

- [ASM-confidence-scores-are-meaningful](../assumptions/ASM-confidence-scores-are-meaningful.md) — assumes scores are calibrated enough that 0.85 is a meaningful threshold.
