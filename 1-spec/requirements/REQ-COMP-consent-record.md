# REQ-COMP-consent-record: Per-source consent records with named lawful basis and immutable history

**Type**: Compliance

**Status**: Approved

**Priority**: Must-have

**Source**: [CON-consent-required](../constraints/CON-consent-required.md), [CON-gdpr-applies](../constraints/CON-gdpr-applies.md)

**Source stakeholder**: [STK-message-sender](../stakeholders.md), [STK-ben](../stakeholders.md)

## Description

For every registered ingestion source, the system maintains a consent record that satisfies the documentation expectations of GDPR Art. 7. Each record carries:

- `source_id`, `actor_id`
- `lawful_basis = consent` (Art. 6(1)(a)) — the only permitted lawful basis at MVP; other bases require an amendment to [CON-gdpr-applies](../constraints/CON-gdpr-applies.md).
- `consent_scope` — boolean per declared purpose (`route_to_projects`, `summarize`, `extract_artifacts`, `learning_signal`, `remote_inference_allowed`); default `false`.
- `retention_policy` — chosen `retention_class`.
- `granted_at`, `granted_by` (actor / channel of consent)
- An append-only history of `consent_scope` and `retention_policy` changes; each prior state is immutable.

The system can produce, for any `source_id` and any timestamp `t`, the consent state in effect at `t` (read-as-of). When a source is revoked, the historical consent states are retained for the duration of the audit log retention period to preserve audit shape — they are not deleted by revocation.

## Acceptance Criteria

- Given a registered source and a timestamp `t`, when the system is queried for the consent state at `t`, then it returns the `consent_scope` and `retention_policy` that were active at `t`, with the `granted_at` and any subsequent change events visible.
- Given a `consent_scope` change event, when the system attempts to mutate the prior state in place, then the operation is rejected — the prior state is immutable; only new versions can be appended.
- Given a registered source for which `lawful_basis` is anything other than `consent`, when the source is created, then the registration is rejected at the schema boundary.

## Related Constraints

- [CON-consent-required](../constraints/CON-consent-required.md) — defines the required fields.
- [CON-gdpr-applies](../constraints/CON-gdpr-applies.md) — defines `consent` as the only permitted lawful basis at MVP.

## Related Assumptions

- [ASM-derived-artifacts-gdpr-permissible](../assumptions/ASM-derived-artifacts-gdpr-permissible.md) — assumes the consent-scope vocabulary is sufficient to legitimize derived-artifact retention.
  - **If invalidated** (per [DEC-gdpr-legal-review-deferred](../../decisions/DEC-gdpr-legal-review-deferred.md) — required note for `Status: Approved` advancement): the consent record schema must add an explicit `derivative_retention_consent` field requiring a separate consent flag for indefinite retention of derived artifacts. Existing sources without this flag are migrated to time-bounded derivative retention — e.g., derivatives expire 90 days after the source's `raw_30d` envelope is swept — until re-consented under the expanded vocabulary. The append-only consent history that this requirement establishes is the structural basis for the migration: prior states remain visible, new states are appended; no destructive rewrite of historical records is needed.
