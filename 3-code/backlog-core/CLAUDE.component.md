# backlog-core

**Responsibility**: The event-sourced technical truth layer. Hosts the append-only event log (Postgres), the proposal pipeline, the consent-record store, the hash-chained audit log, the retention sweep service, the RTBF cascade engine, the data-export tool, the state-reconstruction service, the daily reconciliation job, and the review-queue routing.

**Technology**: Python 3.12 + FastAPI per [`DEC-backend-stack-python-fastapi`](../../decisions/DEC-backend-stack-python-fastapi.md). Uniform across all five backend components. (DEC's Reasoning explicitly accepts a possible future supersession for `backlog-core` only if Phase-7 load tests show `REQ-PERF-ingest-latency` cannot be met in Python.)

## Interfaces

- **HTTP inbound**:
  - `POST /v1/inputs` — from `whatsorga-ingest`.
  - `POST /v1/proposals` and `POST /v1/proposals/:id/disposition` — from `hermes-runtime` and from `gbrain-bridge`'s Obsidian watch script.
  - `POST /v1/sources` / `PATCH /v1/sources/:id` / `POST /v1/sources/:id/revoke` — from operator CLI.
  - `POST /v1/rtbf` / `POST /v1/exports` — from operator CLI.
  - `GET /v1/audit/query` / `POST /v1/audit/verify-chain` / `GET /v1/sweep/status` / `GET /v1/reconciliation/runs` / `POST /v1/reconciliation/run` / `GET /v1/review/queue` / `POST /v1/review/:id/dispose`.
  - `POST /v1/state/reconstruct` — preview-mode replay.
  - `GET /v1/events/stream` — long-poll/SSE for `hermes-runtime`.
  - `GET /v1/health` / `GET /v1/metrics`.
- **HTTP outbound** (cascade fan-out):
  - `DELETE /v1/pages?subject_ref=...&rtbf_run_id=...` to `gbrain-bridge`.
  - `DELETE /v1/cards?subject_ref=...&rtbf_run_id=...` to `kanban-sync`.
- **Postgres** (single instance per deployment): event log, consent tables, idempotency store, subject-keyed materialized view.

## Requirements Addressed

| File | Type | Priority | Summary |
|------|------|----------|---------|
| [REQ-F-source-registration](../../1-spec/requirements/REQ-F-source-registration.md) | Functional | Must-have | Operator can register / update consent_scope on a source; both flows persist as events |
| [REQ-F-consent-revocation](../../1-spec/requirements/REQ-F-consent-revocation.md) | Functional | Must-have | Revocation halts ingest; in-flight events from the source dropped |
| [REQ-F-retention-sweep](../../1-spec/requirements/REQ-F-retention-sweep.md) | Functional | Must-have | Daily idempotent sweep hard-deletes `raw_30d` artifacts at age 30d |
| [REQ-COMP-consent-record](../../1-spec/requirements/REQ-COMP-consent-record.md) | Compliance | Must-have | Per-source consent record with append-only history and read-as-of capability |
| [REQ-COMP-rtbf](../../1-spec/requirements/REQ-COMP-rtbf.md) | Compliance | Must-have | Art. 17 RTBF cascade across all storage layers within 24h with verification |
| [REQ-COMP-data-export](../../1-spec/requirements/REQ-COMP-data-export.md) | Compliance | Must-have | Art. 15 + 20 per-subject export covering consent + derived artifacts + pending raw artifacts |
| [REQ-COMP-purpose-limitation](../../1-spec/requirements/REQ-COMP-purpose-limitation.md) | Compliance | Must-have | Components declare processing purposes; cross-purpose access rejected at the persistence boundary |
| [REQ-SEC-audit-log](../../1-spec/requirements/REQ-SEC-audit-log.md) | Security | Must-have | Append-only hash-chained audit log; tamper-evident even after RTBF redaction |
| [REQ-F-proposal-pipeline](../../1-spec/requirements/REQ-F-proposal-pipeline.md) | Functional | Must-have | Every agent mutation flows through propose → validate → apply with `proposal_id` chaining |
| [REQ-F-correction-actions](../../1-spec/requirements/REQ-F-correction-actions.md) | Functional | Must-have | Disposition events live here; `learning_event`s emitted automatically |
| [REQ-F-state-reconstruction](../../1-spec/requirements/REQ-F-state-reconstruction.md) | Functional | Must-have | Reconstruct full project state from the event log; deterministic, side-effect-free in preview |
| [REQ-REL-audit-reconciliation](../../1-spec/requirements/REQ-REL-audit-reconciliation.md) | Reliability | Must-have | Daily reconciliation: 0 unmatched mutations target, <1% gate bypasses target |
| [REQ-REL-event-replay-correctness](../../1-spec/requirements/REQ-REL-event-replay-correctness.md) | Reliability | Must-have | Replay is deterministic, idempotent, crash-safe, fails fast on corrupted chains |
| [REQ-PERF-ingest-latency](../../1-spec/requirements/REQ-PERF-ingest-latency.md) | Performance | Must-have | p95 autonomous-path < 5 min; p95 review-path < 2 min; 30-min tail constraint |

## Relevant Decisions

| File | Title | Trigger |
|------|-------|---------|
| [DEC-backend-stack-python-fastapi](../../decisions/DEC-backend-stack-python-fastapi.md) | Python 3.12 + FastAPI as the uniform backend stack | Any task that creates or modifies source code, build configuration, or test infrastructure inside this component |
| [DEC-postgres-as-event-store](../../decisions/DEC-postgres-as-event-store.md) | Postgres for `backlog-core`'s event log | All storage-layer code |
| [DEC-hash-chain-over-payload-hash](../../decisions/DEC-hash-chain-over-payload-hash.md) | Audit chain hashes a stable payload digest, not the payload itself | Event-emit, retention sweep, RTBF cascade, audit verification |
| [DEC-direct-http-between-services](../../decisions/DEC-direct-http-between-services.md) | Synchronous HTTP/REST between services at MVP | Inter-service call patterns |
| [DEC-api-versioning](../../decisions/DEC-api-versioning.md) | URL-path versioning (`/v1/...`) | Every endpoint route |
| [DEC-service-auth-bearer-tokens](../../decisions/DEC-service-auth-bearer-tokens.md) | Per-service bearer tokens with declared purposes | Authentication on every endpoint; purpose-limitation enforcement |
| [DEC-idempotency-keys](../../decisions/DEC-idempotency-keys.md) | `Idempotency-Key` header on mutations | Every mutation endpoint; idempotency store implementation |
| [DEC-cursor-pagination-and-event-stream-conventions](../../decisions/DEC-cursor-pagination-and-event-stream-conventions.md) | Cursor pagination + long-poll/SSE event-stream | Every list endpoint (`/v1/sources`, `/v1/audit/query`, `/v1/review/queue`, `/v1/reconciliation/runs`, `/v1/sources/:id/history`, etc.); the canonical `GET /v1/events/stream` implementation |
| [DEC-confidence-gate-as-middleware](../../decisions/DEC-confidence-gate-as-middleware.md) | Gate middleware inside `hermes-runtime`, not a separate service | `POST /v1/proposals` validates `gate_inputs` are present and non-null |
| [DEC-gdpr-legal-review-deferred](../../decisions/DEC-gdpr-legal-review-deferred.md) | GDPR legal review deferred to Code phase | Consent-record schema migrations may need to add `derivative_retention_consent` if assumption invalidated |
