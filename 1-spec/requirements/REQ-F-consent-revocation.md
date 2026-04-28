# REQ-F-consent-revocation: Operator can revoke consent and ingest halts before the next event

**Type**: Functional

**Status**: Approved

**Priority**: Must-have

**Source**: [US-revoke-or-update-consent](../user-stories/US-revoke-or-update-consent.md), [CON-consent-required](../constraints/CON-consent-required.md)

**Source stakeholder**: [STK-ben](../stakeholders.md)

## Description

The system provides a revocation primitive that takes immediate effect. When the operator revokes consent on a source, the revocation is appended as a `source.consent_revoked` event in `backlog-core`, the active consent table is updated synchronously with the event commit, and any further `input_event` from that source is dropped at the ingest boundary with reason `consent_revoked`. In-flight events from the same source that have not yet committed to durable storage at the moment of revocation are also dropped with the same reason.

A revocation is final for the original consent record; re-enabling a source after revocation requires a new `REQ-F-source-registration` action with a new `consent_scope`.

## Acceptance Criteria

- Given an active source with at least one in-flight `input_event` not yet committed, when the operator revokes consent, then the in-flight event is dropped with reason `consent_revoked` and never reaches durable storage; the drop is recorded in the audit log.
- Given a source for which consent has just been revoked, when content arrives from that source within the next 60 seconds, then the input is dropped at ingest with reason `consent_revoked`; no `input_event` is created.
- Given a revoked source, when the operator queries the audit log for the revocation, then the entry contains `actor_id`, `timestamp`, optional `reason` text, and the prior `consent_scope` state.

## Related Constraints

- [CON-consent-required](../constraints/CON-consent-required.md) — defines revocation as a hard gate, not advisory.

## Related Assumptions

- [ASM-subject-reference-resolvable](../assumptions/ASM-subject-reference-resolvable.md) — assumes a revocation can resolve to all in-flight events bound to the source quickly enough to drop them before commit.
