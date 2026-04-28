# US-revoke-or-update-consent: Revoke or modify consent on an existing source

**As an** operator, **I want** to revoke or modify consent on an existing source at any time, **so that** ingestion stops or narrows immediately when a source's status changes (sender request, role change, suspected leak).

**Status**: Draft

**Priority**: Must-have

**Source stakeholder**: [STK-ben](../stakeholders.md)

**Related goal**: [GOAL-auditable-consent-and-privacy](../goals/GOAL-auditable-consent-and-privacy.md)

## Acceptance Criteria

- Given an active source, when the operator revokes consent, then ingest from that source halts before the next event is processed; the revocation is audit-logged with reason, actor, and timestamp.
- Given a revoked source, when content arrives from it after revocation, then the input is dropped at ingest with the consent-revoked reason logged and never reaches storage beyond the drop record.

## Derived Requirements

- [REQ-F-consent-revocation](../requirements/REQ-F-consent-revocation.md)
- [REQ-COMP-consent-record](../requirements/REQ-COMP-consent-record.md)
