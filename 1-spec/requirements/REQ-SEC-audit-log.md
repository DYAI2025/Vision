# REQ-SEC-audit-log: Append-only, hash-chained audit log covers all mutations and consent operations

**Type**: Security

**Status**: Approved

**Priority**: Must-have

**Source**: [CON-no-direct-agent-writes](../constraints/CON-no-direct-agent-writes.md), [CON-gdpr-applies](../constraints/CON-gdpr-applies.md)

**Source stakeholder**: [STK-vincent](../stakeholders.md), [STK-ben](../stakeholders.md), [STK-message-sender](../stakeholders.md)

## Description

The system maintains a single append-only audit log that records:

- All mutation events to any system of record (`backlog-core`, GBrain, Kanban) with `actor_id`, `tool_id`, `proposal_id`, `confidence` (where relevant), `before_hash`, `after_hash`.
- All consent operations: `source.registered`, `source.consent_updated`, `source.consent_revoked` with full before/after `consent_scope`.
- All RTBF runs and verification results: `rtbf.run_started`, `rtbf.cascade_completed`, `rtbf.verification_passed`.
- All remote inference calls per [REQ-SEC-remote-inference-audit](REQ-SEC-remote-inference-audit.md).
- All purpose-denied access rejections per [REQ-COMP-purpose-limitation](REQ-COMP-purpose-limitation.md).
- All retention sweeps per [REQ-F-retention-sweep](REQ-F-retention-sweep.md).

Each event carries a hash that chains it to the previous event's hash. The chain is verifiable: a removed or modified entry produces a detectable break.

Audit log retention is `derived_keep`. RTBF cascades **redact** subject-attributable content fields within audit entries (replacing with a tombstone marker referencing the `rtbf_run_id`) but preserve event ids, types, timestamps, and chain hashes — the audit shape survives RTBF.

## Acceptance Criteria

- Given a sequence of audit events, when an event is removed or its content is modified, then the chain verification routine reports the break at the affected position; an unmodified chain verifies clean end-to-end.
- Given a representative day of activity, when the operator queries the audit log, then for every committed mutation in `backlog-core` / GBrain / Kanban there is at least one audit entry; reconciliation between mutation events and audit entries shows zero unmatched mutations at end-of-day.
- Given an RTBF cascade has redacted subject content from audit entries, when the chain is verified, then verification still passes (event ids and chain hashes were preserved).

## Related Constraints

- [CON-no-direct-agent-writes](../constraints/CON-no-direct-agent-writes.md) — audit log is the trace of every legitimate mutation path.
- [CON-gdpr-applies](../constraints/CON-gdpr-applies.md) — RTBF compatibility (redact, not delete).
