# REQ-F-source-registration: Operator can register a new ingestion source and update its consent scope

**Type**: Functional

**Status**: Approved

**Priority**: Must-have

**Source**: [US-register-source-with-consent](../user-stories/US-register-source-with-consent.md), [CON-consent-required](../constraints/CON-consent-required.md)

**Source stakeholder**: [STK-ben](../stakeholders.md)

## Description

The system provides a tool by which the operator (Ben) registers a new ingestion source and modifies the `consent_scope` of an existing source. Each registration carries the four required fields: `source_id` (stable, unique), `actor_id` (the responsible human or system actor), `consent_scope` (explicit booleans for `route_to_projects`, `summarize`, `extract_artifacts`, `learning_signal`, `remote_inference_allowed`, default `false` unless explicitly granted), and `retention_policy` (one of the three classes from `CON-tiered-retention`). Both the initial registration and any subsequent scope update are persisted as events in `backlog-core` with the full prior and new state, and are reflected in the active consent record table within one ingest cycle.

## Acceptance Criteria

- Given a `source_id` not yet registered, when the operator submits valid `source_id`, `actor_id`, `consent_scope`, and `retention_policy`, then a `source.registered` event is appended to `backlog-core`, the source becomes active, and subsequent ingest queries resolve the source as registered.
- Given an active source, when the operator updates one or more `consent_scope` flags, then a `source.consent_updated` event is appended with `before` and `after` scope states, the change takes effect on the next `input_event` from that source, and the audit query resolves the new scope state for any timestamp at or after the update.
- Given a registration submission missing any of the four required fields, when the operator submits, then the registration is rejected with a structured error naming the missing field; no event is written.

## Related Constraints

- [CON-consent-required](../constraints/CON-consent-required.md) — defines the required fields and the lawful-basis posture that this requirement implements operationally.
- [CON-no-direct-agent-writes](../constraints/CON-no-direct-agent-writes.md) — registration is a mutation; flows through a dedicated tool and emits both an audit and a memory entry.
