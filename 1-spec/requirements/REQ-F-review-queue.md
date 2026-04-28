# REQ-F-review-queue: Mid-band and ambiguous-consent items route to a review queue with explicit dispositions

**Type**: Functional

**Status**: Draft

**Priority**: Must-have

**Source**: [US-handle-review-required-input](../user-stories/US-handle-review-required-input.md), [CON-confidence-gated-autonomy](../constraints/CON-confidence-gated-autonomy.md)

**Source stakeholder**: [STK-ben](../stakeholders.md)

## Description

A review queue holds `input_event`s that cannot be processed autonomously and cannot be silently dropped. Items enter the queue when **any** of the following hold:

- Routing confidence falls in the mid band (`0.55 ≤ confidence < 0.85`).
- Consent classification is ambiguous (e.g., source partially registered, scope mismatched against the action class, retention class undetermined).
- The classifier produces a `review_required` retention class per [CON-tiered-retention](../constraints/CON-tiered-retention.md).

Each queue record carries:

- The originating `input_event_id`
- A structured `reason` (one of `confidence_mid_band`, `consent_ambiguous`, `classifier_review_required`, `manual_flag`)
- A `proposed_dispositions` set (one or more of `reclassify_to_project:<project_id>`, `reclassify_as_non_project`, `drop`, `forward_to_actor:<actor_id>`)
- A `proposed_at` timestamp

Operator disposition is final and audit-logged (`review.disposed` with `actor_id`, `disposition`, `reason`). Reclassify dispositions re-enter the standard processing path with the chosen classification recorded as a `learning_event` so the routing layer can adjust on similar future inputs.

Queue size and median dwell time are operator-visible (a metric / page in GBrain or a CLI report).

## Acceptance Criteria

- Given an `input_event` routed at mid-band confidence, when downstream processing runs, then the event appears in the review queue with `reason = confidence_mid_band` within the [REQ-PERF-ingest-latency](REQ-PERF-ingest-latency.md) review-path target; the event does **not** produce an extracted artifact.
- Given a queue item, when the operator selects a `reclassify_to_project` disposition, then the disposition is audit-logged, a `learning_event` is emitted, and the item re-enters routing with the corrected `project_id` annotated.
- Given the operator queries the queue dashboard, when the query runs, then the queue shows current depth, oldest pending item age, and median dwell time over the last 7 days.

## Related Constraints

- [CON-confidence-gated-autonomy](../constraints/CON-confidence-gated-autonomy.md) — mid-band requires human review.
- [CON-consent-required](../constraints/CON-consent-required.md) — ambiguous consent is a review trigger, not a silent drop.
- [CON-tiered-retention](../constraints/CON-tiered-retention.md) — `review_required` is one of the retention classes.
