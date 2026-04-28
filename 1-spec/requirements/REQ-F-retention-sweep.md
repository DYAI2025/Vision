# REQ-F-retention-sweep: Daily retention sweep deletes expired raw content idempotently

**Type**: Functional

**Status**: Approved

**Priority**: Must-have

**Source**: [GOAL-auditable-consent-and-privacy](../goals/GOAL-auditable-consent-and-privacy.md), [CON-tiered-retention](../constraints/CON-tiered-retention.md)

**Source stakeholder**: [STK-message-sender](../stakeholders.md), [STK-ben](../stakeholders.md)

## Description

The system runs a retention-sweep service that scans all storage layers (`backlog-core` raw blobs, GBrain `raw_30d` envelopes, Kanban attachments, raw cache) on a schedule of at least once every 24 hours, identifies artifacts whose `retention_class` is `raw_30d` and whose age exceeds 30 days from ingest timestamp, and hard-deletes them. The sweep:

- Is **idempotent** — re-running the same sweep run produces no additional deletions and no errors.
- Is **crash-safe** — interrupted runs resume cleanly on next invocation; partial runs do not leave artifacts in inconsistent states.
- Emits one `retention.deleted` audit event per artifact (id, `retention_class`, age_days, sweep_run_id), without including the deleted content.
- Does **not** touch `derived_keep` or `review_required` artifacts.
- Does **not** touch raw content that has already been deleted by an RTBF cascade.

The sweep schedule, run history, and per-run statistics are operator-visible.

## Acceptance Criteria

- Given a set of `raw_30d` artifacts of various ages, when the daily sweep runs, then artifacts with `age_days >= 30` are deleted within the same run, artifacts with `age_days < 30` are untouched, and the audit log contains one `retention.deleted` entry per deletion.
- Given a sweep run that crashes mid-execution, when the next sweep run starts, then it resumes without re-attempting already-deleted artifacts and without missing artifacts that were due during the interrupted window.
- Given a 7-day operational window, when the operator queries sweep statistics, then ≥99% of artifacts due for deletion in that window were deleted within 24 hours of crossing the 30-day threshold.

## Related Constraints

- [CON-tiered-retention](../constraints/CON-tiered-retention.md) — defines the three retention classes and the 30-day floor for raw content.
- [CON-gbrain-no-raw-private-truth](../constraints/CON-gbrain-no-raw-private-truth.md) — sweep is the structural enforcement that GBrain cannot become a covert long-term raw archive.
