# REQ-SEC-redaction-precondition: Raw content must be redacted or derived before reaching durable storage classes

**Type**: Security

**Status**: Approved

**Priority**: Must-have

**Source**: [CON-gbrain-no-raw-private-truth](../constraints/CON-gbrain-no-raw-private-truth.md)

**Source stakeholder**: [STK-message-sender](../stakeholders.md)

## Description

Any path that writes to a `derived_keep`-classed artifact must validate that the payload does not contain raw input content. The persistence-service write tools (`gbrain-memory-write`, `kanban-sync`) implement this as a precondition check: if a payload claiming `retention_class = derived_keep` matches against raw-input markers (full message bodies above N tokens, full transcripts, embedded raw payload references not bounded by a `raw_30d` envelope), the write is rejected with a structured `redaction_required` error.

Upstream, the ingestion adapters (WhatsOrga ingest, voice ingest, repo ingest, manual CLI) produce derived artifacts (summaries, classifications, structured proposals) before the content is permitted to reach `derived_keep` storage. Raw content may persist only inside a `raw_30d` envelope linked from — but not embedded in — a derived artifact.

A periodic vault audit sweep (per [REQ-MNT-vault-audit-sweep](#) — to be drafted under Goal D) verifies the absence of raw content in `derived_keep` artifacts.

## Acceptance Criteria

- Given a payload tagged `retention_class = derived_keep` containing a recognizable raw-content marker, when `gbrain-memory-write` is invoked, then the write is rejected with `redaction_required` and no page is created.
- Given a payload tagged `retention_class = derived_keep` containing only derived content (summaries, classifications, references), when the same tool is invoked, then the write succeeds.
- Given a `derived_keep` GBrain page, when the vault audit sweep runs, then 0 pages are flagged as containing raw content; flagged pages, if any, generate a high-priority alert and a per-page remediation task.

## Related Constraints

- [CON-gbrain-no-raw-private-truth](../constraints/CON-gbrain-no-raw-private-truth.md) — defines the structural prohibition.
- [CON-tiered-retention](../constraints/CON-tiered-retention.md) — defines `raw_30d` as the only durable home for raw content.
