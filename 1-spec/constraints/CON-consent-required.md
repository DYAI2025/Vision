# CON-consent-required: Every ingestion source must carry an explicit consent record

**Category**: Operational

**Status**: Active

**Source stakeholder**: [STK-message-sender](../stakeholders.md), [STK-vincent](../stakeholders.md), [STK-ben](../stakeholders.md)

## Description

Every ingestion source — WhatsApp chat, voice channel, repository feed, manual CLI sink, Obsidian vault, or any future input — must register a consent record before any input from it is processed. The record must include at minimum:

- `source_id` — stable, unique source identifier
- `actor_id` — the human or system actor responsible for the source
- `consent_scope` — what the source's content may be used for (project routing, summarization, learning, remote inference, etc.); each scope is an explicit boolean, not an implied default
- `retention_policy` — which `retention_class` (see [CON-tiered-retention](CON-tiered-retention.md)) applies to raw inputs from this source

When consent is missing, expired, ambiguous, or revoked, all input from the source is **dropped at ingest** with the reason logged. Dropped input may not be persisted beyond the minimal audit metadata needed to confirm the drop happened. There is no "process now, classify consent later" path.

## Rationale

Consent is the lawful basis the entire data pipeline depends on (see [CON-gdpr-applies](CON-gdpr-applies.md)). Anchoring it in a per-source record — rather than as an implicit "we don't surveil" promise — makes it auditable, revocable, and enforceable at the system boundary instead of inside business logic.

## Impact

- Every ingestion adapter (WhatsOrga ingest, voice ingest, repo event ingest, manual CLI, Obsidian sync) must call a consent-check primitive before producing an `input_event`. The check is a hard gate, not advisory.
- A source-registration UX (initial onboarding + scope edits + revocation) is a hard prerequisite for every input channel — drives goals around "operator can register and revoke sources."
- Audit log schema must record both successful ingests and consent-blocked drops, with the blocking reason.
- `consent_scope` is the contract the rest of the system reads from: components that route, store, or send data must check that the relevant scope flag is true for the source — including `remote_inference_allowed` from [CON-local-first-inference](CON-local-first-inference.md).
