# REQ-COMP-rtbf: Right-to-be-forgotten cascades end-to-end within 24 hours and verifies clean

**Type**: Compliance

**Status**: Approved

**Priority**: Must-have

**Source**: [US-service-rtbf-request](../user-stories/US-service-rtbf-request.md), [CON-gdpr-applies](../constraints/CON-gdpr-applies.md)

**Source stakeholder**: [STK-message-sender](../stakeholders.md), [STK-ben](../stakeholders.md)

## Description

The system implements GDPR Art. 17 right-to-be-forgotten end-to-end. Given a registered subject reference, the operator can initiate an RTBF cascade that:

1. Removes all subject-attributable content from `backlog-core` events. Where deletion would break the audit chain, content fields are redacted in place (replaced with a tombstone marker carrying `rtbf_run_id`, `redacted_at`); the event id, type, and chain hash are preserved.
2. Removes all subject-attributable GBrain pages, including bidirectional link cleanup so no orphaned references remain.
3. Removes all subject-attributable Kanban cards.
4. Hard-deletes any remaining `raw_30d` artifacts referencing the subject regardless of age.
5. Records a `rtbf.cascade_completed` audit event with `rtbf_run_id`, `subject_ref`, layer-by-layer counts, and `completed_at`.

**Completion target: ≤ 24 hours** from operator acceptance to `rtbf.cascade_completed`.

A per-subject verification query, run after cascade completion, returns zero rows of subject-attributable content across all storage layers. Verification is mandatory — cascade is not considered complete without a successful verification result recorded as part of the same `rtbf_run_id`.

## Acceptance Criteria

- Given a known subject reference with content in all four layers, when the operator initiates RTBF, then within 24 hours the cascade completes, every layer's count of remaining subject rows is zero, and the audit log contains the cascade event with non-zero deletion counts in at least the layers that held subject content.
- Given a completed RTBF cascade, when the per-subject verification query is run, then it returns zero rows across `backlog-core` (excluding tombstoned events), GBrain, Kanban, and raw cache.
- Given an RTBF cascade interrupted by a process restart, when the cascade is resumed, then it continues from the last-committed layer-step and completes correctly without double-deletion or missed records.

## Related Constraints

- [CON-gdpr-applies](../constraints/CON-gdpr-applies.md) — anchors the regulatory obligation.
- [CON-tiered-retention](../constraints/CON-tiered-retention.md) — RTBF overrides retention class (forces hard delete of `raw_30d` regardless of age).

## Related Assumptions

- [ASM-rtbf-24h-window-acceptable](../assumptions/ASM-rtbf-24h-window-acceptable.md) — assumes 24h is acceptable.
- [ASM-subject-reference-resolvable](../assumptions/ASM-subject-reference-resolvable.md) — assumes a stable subject reference indexes across all layers.
