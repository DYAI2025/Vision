# REQ-COMP-purpose-limitation: Components declare and are gated by their processing purposes

**Type**: Compliance

**Status**: Approved

**Priority**: Must-have

**Source**: [CON-gdpr-applies](../constraints/CON-gdpr-applies.md), [CON-consent-required](../constraints/CON-consent-required.md)

**Source stakeholder**: [STK-message-sender](../stakeholders.md)

## Description

Every component that reads source-attributable content declares its processing purpose(s) — drawn from the same vocabulary as `consent_scope` (`route_to_projects`, `summarize`, `extract_artifacts`, `learning_signal`, `remote_inference_allowed`) — in its component manifest. The persistence services (`backlog-core`, `gbrain-bridge`, `kanban-sync`) and any inference router enforce purpose-scoped access at the access boundary: a request from a component for content from a source whose `consent_scope` does not grant the component's declared purpose is rejected before any content is returned.

Cross-purpose access (component A reading content for purpose P2 when its declared purpose is P1) is rejected at the runtime boundary, not via convention or business-logic checks.

This requirement does not prevent reading metadata fields that are not source content (e.g., `source_id`, `created_at`); it gates access to content fields and to derived artifacts whose creation depended on a specific purpose.

## Acceptance Criteria

- Given a component declaring purpose `P1`, when it requests content from a source whose `consent_scope` does not grant `P1`, then the access is rejected at the persistence-service boundary with a structured `purpose_denied` error and an audit event.
- Given a component declaring purpose `P1`, when it requests content from a source whose `consent_scope` grants `P1`, then the access succeeds and is logged with `component_id`, `purpose`, `source_id`, and outcome.
- Given a component manifest missing a declared purpose, when the component starts, then it fails to start with a configuration error; the persistence services refuse to honor any access from it.

## Related Constraints

- [CON-gdpr-applies](../constraints/CON-gdpr-applies.md) — Art. 5(1)(b) purpose limitation.
- [CON-consent-required](../constraints/CON-consent-required.md) — `consent_scope` is the access vocabulary.
- [CON-no-direct-agent-writes](../constraints/CON-no-direct-agent-writes.md) — purpose checks live at the same boundary that gates writes.
