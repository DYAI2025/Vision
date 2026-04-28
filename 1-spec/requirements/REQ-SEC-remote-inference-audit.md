# REQ-SEC-remote-inference-audit: Every remote inference call is fully audited and pre-gated

**Type**: Security

**Status**: Approved

**Priority**: Must-have

**Source**: [CON-local-first-inference](../constraints/CON-local-first-inference.md)

**Source stakeholder**: [STK-message-sender](../stakeholders.md), [STK-ben](../stakeholders.md)

## Description

Every remote inference call (LLM completion, embedding, transcription, or any other call to a non-local model endpoint) is gated and audited. Gate (pre-call):

- The calling component / skill is on the configured `remote_inference_profiles[].allowed_callers` list.
- The data class being sent (raw vs. derived vs. metadata-only) is on the same profile's `allowed_data_classes` list.
- The source's `consent_scope.remote_inference_allowed = true`.
- An operator-approved `remote_inference_profile` is enabled for the deployment.

Failure of any gate condition rejects the call **before any network request is initiated**.

Audit (post-call):

- Caller component / skill id
- Data class
- `source_id` and `consent_scope` snapshot
- Model identifier and endpoint
- `remote_inference_profile` that authorized the call
- Operator approval reference (which config flipped it on, when, by whom)
- Request size, response size, latency
- Outcome: `accepted` / `rejected_by_gate` / `network_error` / `provider_error`

The audit entry is recorded in the same audit log as [REQ-SEC-audit-log](REQ-SEC-audit-log.md).

## Acceptance Criteria

- Given no `remote_inference_profile` is enabled, when any component attempts a remote inference call, then the call is rejected with `rejected_by_gate` reason `no_profile_enabled` and an audit entry is written; no network egress occurs.
- Given a profile enabled with allowed callers `[A]` and data classes `[derived]`, when component `B` (not in allowed callers) attempts a remote call, then it is rejected with `rejected_by_gate` reason `caller_not_allowed`.
- Given a profile enabled and a permitted call, when component `A` makes the call against a source with `remote_inference_allowed = true`, then the call proceeds and the audit entry contains all required fields above.

## Related Constraints

- [CON-local-first-inference](../constraints/CON-local-first-inference.md) — defines default-local + opt-in remote.
- [CON-consent-required](../constraints/CON-consent-required.md) — `remote_inference_allowed` is a `consent_scope` flag.
