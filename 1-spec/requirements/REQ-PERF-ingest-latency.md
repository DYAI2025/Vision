# REQ-PERF-ingest-latency: End-to-end p95 latency targets for the autonomous and review paths

**Type**: Performance

**Status**: Draft

**Priority**: Must-have

**Source**: [GOAL-multi-source-project-ingestion](../goals/GOAL-multi-source-project-ingestion.md)

**Source stakeholder**: [STK-vincent](../stakeholders.md), [STK-ben](../stakeholders.md)

## Description

End-to-end ingest latency is measured from `input_event.arrived_at` to one of two terminal states:

- **Autonomous path** (high-band confidence, all gate preconditions satisfied): latency is measured from arrival to **kanban card created** (visible in Obsidian via `kanban-sync`). **Target: p95 < 5 minutes.**
- **Review path** (mid-band confidence or ambiguous consent): latency is measured from arrival to **review-queue notification visible** to the operator. **Target: p95 < 2 minutes.**

Measurement window: rolling 7-day. Metrics computed per channel and aggregated.

**Tail constraint:** no event may remain in either pipeline past **30 minutes** without either reaching its terminal state or producing an explicit `processing.stuck` alert with `event_id`, last-completed step, and elapsed time. This catches stalled processing rather than masking it in aggregate latency.

Synthetic monitoring: a low-rate synthetic injection (one event per channel per hour) feeds known events through the pipeline and asserts both p95 targets continuously. Synthetic events use a dedicated `source_id` with full consent scope; their results do not contribute to user-facing project state.

## Acceptance Criteria

- Given the synthetic monitoring task, when results are aggregated over a 7-day window, then p95 autonomous-path latency is < 5 min and p95 review-path latency is < 2 min on each channel.
- Given any in-flight event, when its elapsed time crosses 30 min without reaching a terminal state, then a `processing.stuck` alert is emitted within 1 min of the threshold crossing.
- Given a deliberate fault injection (one component slow / down), when the system recovers, then no events are silently lost — every fault-window event either reaches a terminal state or produces a `processing.stuck` record that the operator can dispose.

## Related Constraints

_none directly_

## Related Assumptions

- [ASM-channel-shape-convergeable](../assumptions/ASM-channel-shape-convergeable.md) — assumes uniform measurement is feasible across channels.
