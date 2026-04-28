# GOAL-auditable-consent-and-privacy: Every input is consented, retention is enforced, and subject rights are servable end-to-end

**Description**: The system's privacy posture is verifiable from the outside, not just promised. Every input that reaches storage carries a traceable consent record, retention is enforced automatically against per-artifact `retention_class`, and EU GDPR data-subject rights (Art. 15–20) — especially right-to-be-forgotten — are operationally servable through a defined runbook rather than ad-hoc database surgery. This goal exists because the entire system's lawful basis depends on consent being a real, enforceable artifact rather than a marketing claim.

**Status**: Approved

**Priority**: Must-have

**Source stakeholder**: [STK-message-sender](../stakeholders.md), [STK-vincent](../stakeholders.md), [STK-ben](../stakeholders.md)

## Success Criteria

- [ ] **Consent coverage**: 100% of `input_event`s in `backlog-core` carry a resolvable link to an active consent record at ingest time, verifiable via a single audit query.
- [ ] **Consent enforcement**: 0 `input_event`s persisted from sources whose consent is missing, expired, or out-of-scope within the last 7-day sweep window; consent-blocked drops are logged with reason.
- [ ] **Retention enforcement**: the retention sweep runs at least daily, is idempotent, and hard-deletes `raw_30d` artifacts within 24h of crossing the 30-day threshold; sweep audit log shows ≥99% of due artifacts deleted on schedule.
- [ ] **Right-to-be-forgotten end-to-end**: an RTBF request keyed on a registered subject reference completes — all subject data deleted across `backlog-core`, GBrain, Kanban, and any raw cache — within **24 hours** of operator acceptance, with completion confirmable via a per-subject audit query that returns zero rows.
- [ ] **Remote inference auditability**: 100% of remote inference calls (if any are enabled per [CON-local-first-inference](../constraints/CON-local-first-inference.md)) appear in the audit log with caller, data class, source `consent_scope`, model identifier, and operator-approval reference.
- [ ] **GBrain non-archival property**: a periodic vault audit sweep finds zero `derived_keep` pages containing raw input content (full message bodies, full transcripts) at end-of-cycle.

## Related Artifacts

- Stakeholders: [STK-message-sender](../stakeholders.md), [STK-vincent](../stakeholders.md), [STK-ben](../stakeholders.md)
- Constraints: [CON-consent-required](../constraints/CON-consent-required.md), [CON-gdpr-applies](../constraints/CON-gdpr-applies.md), [CON-tiered-retention](../constraints/CON-tiered-retention.md), [CON-gbrain-no-raw-private-truth](../constraints/CON-gbrain-no-raw-private-truth.md), [CON-local-first-inference](../constraints/CON-local-first-inference.md), [CON-no-platform-bypass](../constraints/CON-no-platform-bypass.md)
- User stories: [US-register-source-with-consent](../user-stories/US-register-source-with-consent.md), [US-revoke-or-update-consent](../user-stories/US-revoke-or-update-consent.md), [US-service-rtbf-request](../user-stories/US-service-rtbf-request.md)
- Requirements: [REQ-F-source-registration](../requirements/REQ-F-source-registration.md), [REQ-F-consent-revocation](../requirements/REQ-F-consent-revocation.md), [REQ-F-retention-sweep](../requirements/REQ-F-retention-sweep.md), [REQ-COMP-consent-record](../requirements/REQ-COMP-consent-record.md), [REQ-COMP-rtbf](../requirements/REQ-COMP-rtbf.md), [REQ-COMP-data-export](../requirements/REQ-COMP-data-export.md), [REQ-COMP-purpose-limitation](../requirements/REQ-COMP-purpose-limitation.md), [REQ-SEC-audit-log](../requirements/REQ-SEC-audit-log.md), [REQ-SEC-redaction-precondition](../requirements/REQ-SEC-redaction-precondition.md), [REQ-SEC-remote-inference-audit](../requirements/REQ-SEC-remote-inference-audit.md)
- Assumptions: [ASM-derived-artifacts-gdpr-permissible](../assumptions/ASM-derived-artifacts-gdpr-permissible.md), [ASM-rtbf-24h-window-acceptable](../assumptions/ASM-rtbf-24h-window-acceptable.md), [ASM-subject-reference-resolvable](../assumptions/ASM-subject-reference-resolvable.md)
