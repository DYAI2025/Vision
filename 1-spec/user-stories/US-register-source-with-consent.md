# US-register-source-with-consent: Register a new ingestion source with explicit consent

**As an** operator, **I want** to register a new ingestion source with an explicit `consent_scope`, named `actor_id`, and chosen `retention_policy`, **so that** every input that subsequently flows from that source is consented and traceable to a recorded lawful basis.

**Status**: Draft

**Priority**: Must-have

**Source stakeholder**: [STK-ben](../stakeholders.md)

**Related goal**: [GOAL-auditable-consent-and-privacy](../goals/GOAL-auditable-consent-and-privacy.md)

## Acceptance Criteria

- Given a source that is not yet registered, when the operator submits `source_id`, `actor_id`, `consent_scope`, and `retention_policy`, then the source becomes active and may produce `input_event`s; the registration is recorded as an event in `backlog-core`.
- Given an active source, when the operator updates its `consent_scope` (e.g., enables `remote_inference_allowed`), then the change is audit-logged with before/after values and takes effect on the next ingest event from that source.

## Derived Requirements

- [REQ-F-source-registration](../requirements/REQ-F-source-registration.md)
- [REQ-COMP-consent-record](../requirements/REQ-COMP-consent-record.md)
