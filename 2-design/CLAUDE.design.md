Phase-specific instructions for the **Design** phase. Extends [../CLAUDE.md](../CLAUDE.md).

## Purpose

This phase defines **how** we're building the system. Focus on architecture, data models, APIs, and key technical decisions.

## Files in This Phase

| File | Purpose |
|------|---------|
| [`architecture.md`](architecture.md) | System architecture overview and diagrams |
| [`data-model.md`](data-model.md) | Data structures, schemas, and relationships |
| [`api-design.md`](api-design.md) | API specifications and contracts |

---

## Decisions Relevant to This Phase

| File | Title | Trigger |
|------|-------|---------|
| [DEC-stakeholder-tiebreaker-consensus](../decisions/DEC-stakeholder-tiebreaker-consensus.md) | Peer-stakeholder conflicts resolved by consensus, not influence | A design choice in `architecture.md`, `data-model.md`, or `api-design.md` has explicit feedback from both `STK-vincent` and `STK-ben` and the positions are not reconcilable as worded |
| [DEC-gdpr-legal-review-deferred](../decisions/DEC-gdpr-legal-review-deferred.md) | GDPR legal review deferred from Spec → Design gate to Code phase | Any design choice that depends on `ASM-derived-artifacts-gdpr-permissible` (RTBF cascade, derived-artifact retention, `consent_scope` vocabulary, GBrain page schemas) — must include an explicit fallback-if-invalidated note before review approval |
| [DEC-postgres-as-event-store](../decisions/DEC-postgres-as-event-store.md) | Postgres is the event store for `backlog-core` | Any design that touches `backlog-core`'s storage layer — schema, indexing strategy, backup format, retention partitioning |
| [DEC-direct-http-between-services](../decisions/DEC-direct-http-between-services.md) | Synchronous HTTP/REST between services at MVP | Any new inter-service flow proposed must use HTTP/REST unless this decision is superseded |
| [DEC-confidence-gate-as-middleware](../decisions/DEC-confidence-gate-as-middleware.md) | Confidence gate is middleware inside `hermes-runtime`, not a separate service | Any design proposing a new agent-action site must indicate where the gate runs and where the persistence-side check runs |
| [DEC-obsidian-as-review-ui](../decisions/DEC-obsidian-as-review-ui.md) | Review queue and proposal-detail views are GBrain pages disposed via Obsidian command palette | Any design choice that introduces an operator-facing surface beyond the CLI must consult this decision before adding new components |
| [DEC-platform-bypass-review-checklist](../decisions/DEC-platform-bypass-review-checklist.md) | Reviewer checklist of patterns rejected as platform-protection bypass | Any design that touches `whatsorga-ingest` adapters or adds a new channel adapter must be reviewed against the checklist |
| [DEC-hash-chain-over-payload-hash](../decisions/DEC-hash-chain-over-payload-hash.md) | Audit chain hashes a stable payload digest, not the payload itself | Any design that touches the `events` table schema, audit-log verification, or the redaction mechanism |
| [DEC-api-versioning](../decisions/DEC-api-versioning.md) | URL-path versioning (`/v1/...`) for inter-service APIs | Any new endpoint design must use the active major version path; breaking changes require a new major version |
| [DEC-service-auth-bearer-tokens](../decisions/DEC-service-auth-bearer-tokens.md) | Service-to-service auth via per-service bearer tokens with declared purposes | Any new inter-service endpoint specifies accepted calling identities and required purposes |
| [DEC-idempotency-keys](../decisions/DEC-idempotency-keys.md) | Mutation endpoints accept `Idempotency-Key` headers | Any new mutation endpoint declares whether it accepts the header (default: yes) |
| [DEC-cursor-pagination-and-event-stream-conventions](../decisions/DEC-cursor-pagination-and-event-stream-conventions.md) | Cursor pagination + long-poll/SSE event-stream as cross-cutting API conventions | Any new list endpoint or stream endpoint specification — cursor for collections, SSE for events, no offset/page/WebSocket alternatives at MVP |
<!-- Add rows as decisions are recorded. File column: [DEC-kebab-name](../decisions/DEC-kebab-name.md) -->

---

## Linking to Other Phases

- Reference requirements from `1-spec/` to justify design choices
- Design documents guide implementation in `3-code/`
- Infrastructure design informs deployment in `4-deploy/`
