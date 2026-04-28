# REQ-COMP-data-export: Subject access and portability via a per-subject machine-readable export

**Type**: Compliance

**Status**: Approved

**Priority**: Must-have

**Source**: [CON-gdpr-applies](../constraints/CON-gdpr-applies.md)

**Source stakeholder**: [STK-message-sender](../stakeholders.md), [STK-ben](../stakeholders.md)

## Description

The system implements GDPR Art. 15 (right of access) and Art. 20 (right to data portability). Given a registered subject reference, the operator can produce an export that contains all stored data attributable to the subject, in a structured, machine-readable format (JSON minimum; CSV and human-readable summary acceptable additional formats).

The export contains:

- The current consent state and full consent history for any source identifying the subject as `actor_id`.
- All `derived_keep` artifacts (summaries, decisions, learnings, kanban cards, project profile entries) referencing the subject, with link metadata.
- A list of `raw_30d` artifacts currently held that reference the subject, with retention countdown.
- A per-layer count of subject-attributable rows.

The export action is audit-logged (`subject.export_produced` with `subject_ref`, `actor_id`, `formats`, `byte_size`, `completed_at`) and the export bundle itself is treated as `raw_30d` (must be deleted from any cache within 30 days; not stored as durable record beyond the audit reference).

## Acceptance Criteria

- Given a registered subject reference, when the operator runs the export tool, then a JSON bundle is produced within 24 hours that conforms to the documented schema and contains all categories above.
- Given an export bundle, when validated against the documented schema, then it parses without errors and the per-layer counts match a fresh subject-keyed query at the same logical timestamp.
- Given the export tool was invoked, when the operator inspects the audit log, then a `subject.export_produced` event is present with all required fields.

## Related Constraints

- [CON-gdpr-applies](../constraints/CON-gdpr-applies.md) — anchors Art. 15 + 20.
- [CON-tiered-retention](../constraints/CON-tiered-retention.md) — export bundle is `raw_30d`.

## Related Assumptions

- [ASM-subject-reference-resolvable](../assumptions/ASM-subject-reference-resolvable.md)
