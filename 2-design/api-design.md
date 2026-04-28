# API Design

## Purpose

This document defines the HTTP APIs between services, the operator CLI surface, and the Obsidian command-palette bindings (per [`DEC-obsidian-as-review-ui`](../decisions/DEC-obsidian-as-review-ui.md)). It is the interface-level companion to [`architecture.md`](architecture.md) and [`data-model.md`](data-model.md). The design principle remains: define only the endpoints and contracts needed to satisfy approved requirements. Speculative APIs for features not backed by an approved requirement are excluded.

---

## Cross-cutting conventions

### Versioning — URL path

All inter-service APIs use **URL-path versioning** (`/v1/...`) per [`DEC-api-versioning`](../decisions/DEC-api-versioning.md). The MVP ships with `v1` across all services. Breaking changes go to `v2`; additive changes (new optional fields, new endpoints) stay within `v1`.

### Authentication — service-scoped bearer tokens

Every inter-service request carries `Authorization: Bearer <token>` per [`DEC-service-auth-bearer-tokens`](../decisions/DEC-service-auth-bearer-tokens.md). Tokens are:

- One per calling service (e.g., `hermes-runtime` has a token recognized by `backlog-core` / `gbrain-bridge` / `kanban-sync`).
- `.env`-driven (per `REQ-MNT-env-driven-config`).
- Rotated per `REQ-REL-secret-rotation`.
- Map to a **declared purposes set** in the receiving service's config, used to enforce `REQ-COMP-purpose-limitation`.

Operator CLI requests carry an operator token recognized by `backlog-core`'s ingress. The Obsidian watch script (in `gbrain-bridge`) carries the same operator token when posting dispositions.

### Authorization — purpose checks

Per `REQ-COMP-purpose-limitation`, every endpoint that accesses source-attributable content checks the calling service's declared purposes against the source's `consent_scope` for the relevant flag. Failures return `403 purpose_denied` with a structured reason.

### Idempotency — `Idempotency-Key` header on mutations

Every mutation endpoint (`POST`, `PATCH`, `DELETE`) accepts an `Idempotency-Key` header per [`DEC-idempotency-keys`](../decisions/DEC-idempotency-keys.md). Behaviour:

- A unique key per logical operation (typically the `proposal_id` for proposal-pipeline calls; a per-CLI-invocation UUID for operator commands).
- The receiving service stores the key + the resulting outcome for ≥24 hours.
- A repeat request with the same key returns the original outcome without re-applying the mutation.
- Mutations without an `Idempotency-Key` are accepted but not deduplicated (allowed for one-shot operator commands where retry is not a concern).

### Error response shape

All error responses use a structured shape rather than opaque 5xx bodies:

```json
{
  "error": {
    "code": "string (snake_case enum)",
    "message": "human-readable string",
    "field": "field_name (optional, for validation errors)",
    "trace_id": "uuid (for log correlation)"
  }
}
```

Common codes: `validation_error`, `auth_required`, `auth_invalid`, `purpose_denied`, `consent_revoked`, `consent_scope_missing`, `idempotency_conflict`, `not_found`, `gone` (for RTBF-redacted resources), `chain_corrupt`, `rate_limited`, `internal_error`.

Status code mapping:
- `400` → `validation_error`, `idempotency_conflict`
- `401` → `auth_required`, `auth_invalid`
- `403` → `purpose_denied`, `consent_revoked`, `consent_scope_missing`
- `404` → `not_found`
- `410` → `gone` (RTBF-redacted; preserves audit shape)
- `422` → `chain_corrupt`, `redaction_required`
- `429` → `rate_limited`
- `500` → `internal_error`

### Pagination — cursor-based

List endpoints (`GET /v1/...?after=<cursor>&limit=<n>`) use opaque cursor tokens. Default `limit` is 50, max 500. Responses include `next_cursor` if more results are available.

### Health and observability

Every service exposes `GET /v1/health` returning `{"status": "ok|degraded|down", "version": "...", "checks": {...}}`. Used by Docker Compose healthchecks. No auth required.

`GET /v1/metrics` returns Prometheus-format metrics. Auth required (operator token).

### Content type

`Content-Type: application/json; charset=utf-8` for all bodies. UTF-8 throughout. Timestamps are RFC 3339 (ISO 8601 with UTC offset).

---

## `backlog-core` HTTP API

The persistence service for the event log, consent records, audit log, and proposal pipeline coordination.

### Input events

**`POST /v1/inputs`** — submit a normalized `input_event` from `whatsorga-ingest`.

- Caller: `whatsorga-ingest` only.
- Body: `input_event` payload (see `data-model.md`).
- Idempotency key: `event_id` of the candidate event.
- Response: `201` with `{"event_id": "..."}` or `403 consent_revoked` / `consent_scope_missing` (drop logged).
- Side effects: writes `input.received` event; subject_index materialized view refreshed asynchronously.

### Proposal pipeline

**`POST /v1/proposals`** — submit a proposal from `hermes-runtime`.

- Caller: `hermes-runtime` only.
- Body: `proposal` payload (see `data-model.md`).
- Idempotency key: `proposal_id`.
- Response: `201` with `{"proposal_id": "...", "status": "accepted_for_validation"}` or `400 validation_error` / `403 consent_scope_missing` / `403 auto_policy_disabled`.
- Side effects: writes `proposal.proposed` event; triggers downstream validation via the persistence service named in `tool_id`.

**`GET /v1/proposals/:proposal_id`** — fetch full proposal detail (per `REQ-F-decision-inspection`).

- Caller: any operator-token holder.
- Response: `200` with the full proposal record including `gate_inputs`, `cited_pages`, `learnings_applied`, `source_input_event_id`, current `status`, and the chain of related events (proposed → applied/rejected → disposition → learning).
- For RTBF-redacted proposals: `410 gone` with `{"error": {"code": "gone", "rtbf_run_id": "..."}}`.

**`POST /v1/proposals/:proposal_id/disposition`** — record human disposition (accept / edit-and-accept / reject) per `REQ-F-correction-actions`.

- Caller: operator token (CLI) or `gbrain-bridge`'s watch script (Obsidian command palette).
- Body: `{"disposition": "accept|edit_and_accept|reject", "edit_content": {...}?, "human_feedback": "..."?}`.
- Idempotency key: per-disposition UUID generated by the caller.
- Response: `201` with `{"disposition_event_id": "...", "learning_event_id": "..."}`.
- Side effects: writes `proposal.disposition` and `learning.recorded` events; for `accept` / `edit_and_accept`, triggers downstream `proposal.applied` once the persistence service confirms the mutation.

### Source / consent management

**`POST /v1/sources`** — register a new source (per `REQ-F-source-registration`).

- Caller: operator token (CLI).
- Body: `{"source_id", "actor_id", "consent_scope", "retention_policy", "granted_by"}`.
- Idempotency key: `source_id`.
- Response: `201` with the created source record.
- Errors: `400 validation_error` (missing required field), `409 already_exists`.
- Side effects: writes `source.registered` event + first `consent_history` row.

**`PATCH /v1/sources/:source_id`** — update `consent_scope` or `retention_policy`.

- Body: `{"consent_scope": {...}?, "retention_policy": "..."?}` (partial update; supplied fields replace).
- Idempotency key: per-update UUID generated by the caller.
- Response: `200` with the updated record.
- Side effects: writes `source.consent_updated` event + `consent_history` row.

**`POST /v1/sources/:source_id/revoke`** — revoke consent (per `REQ-F-consent-revocation`).

- Body: `{"change_reason": "..."?}`.
- Idempotency key: per-revocation UUID.
- Response: `200` with the revoked record.
- Side effects: writes `source.consent_revoked` event; halts ingest from this source on next event; in-flight events for this source are dropped at the boundary; `consent_history` row appended.

**`GET /v1/sources/:source_id`** — current consent state.

- Response: `200` with `{"source_id", "actor_id", "lawful_basis", "consent_scope", "retention_policy", "current_state", "granted_at", "updated_at"}`.

**`GET /v1/sources/:source_id/history`** — append-only consent history (per `REQ-COMP-consent-record`).

- Query params: `?as_of=<iso8601>` for read-as-of.
- Response: `200` with the full history array, or the single state in effect at `as_of`.

**`GET /v1/sources`** — list registered sources (paginated).

- Query params: `?status=active|revoked&actor_id=...`.

### RTBF cascade

**`POST /v1/rtbf`** — initiate an RTBF cascade for a subject (per `REQ-COMP-rtbf`).

- Caller: operator token (CLI only).
- Body: `{"subject_ref": "...", "requested_by": "..."}`.
- Idempotency key: per-request UUID.
- Response: `202` with `{"rtbf_run_id": "..."}` (async; cascade may take minutes).
- Side effects: writes `rtbf.run_started` event; cascade fans out to `gbrain-bridge` and `kanban-sync` via `DELETE /v1/pages?subject_ref=...` and `DELETE /v1/cards?subject_ref=...`; on completion, writes `rtbf.cascade_completed` and runs the verification query → writes `rtbf.verification_passed`.

**`GET /v1/rtbf/:rtbf_run_id`** — cascade status.

- Response: `200` with `{"rtbf_run_id", "subject_ref", "started_at", "completed_at?", "verification_passed?", "layer_counts", "status": "running|completed|failed"}`.

### Data subject export (Art. 15 + 20)

**`POST /v1/exports`** — produce a per-subject data export (per `REQ-COMP-data-export`).

- Caller: operator token (CLI only).
- Body: `{"subject_ref": "...", "formats": ["json", "csv"?]}`.
- Idempotency key: per-request UUID.
- Response: `202` with `{"export_id": "..."}`. The export bundle is written to a `raw_30d`-classed location and a `subject.export_produced` event is emitted with byte size and formats.

**`GET /v1/exports/:export_id`** — fetch export bundle.

- Response: `200` with the JSON bundle, or `202 not_ready` if still generating.

### Audit log

**`GET /v1/audit/query`** — filtered audit query.

- Query params: `?event_type=...&proposal_id=...&subject_ref=...&actor_id=...&from=...&to=...&after=<cursor>&limit=<n>`.
- Caller: operator token. Persistence services may also query for cross-validation purposes within their declared scope.
- Response: `200` with paginated events. Redacted events show `payload: null` and `redacted: true`.

**`POST /v1/audit/verify-chain`** — verify hash-chain integrity (per `REQ-SEC-audit-log`, `REQ-REL-event-replay-correctness`).

- Body: `{"from_event_id": "..."?, "to_event_id": "..."?}` (defaults to entire chain).
- Response: `200` with `{"valid": true|false, "first_corrupt_event_id": "..."?, "events_checked": N}`. Run on a sampled basis during normal operation; run end-to-end after every restore.

### State reconstruction (per `REQ-F-state-reconstruction`)

**`POST /v1/state/reconstruct`** — preview-mode state reconstruction.

- Body: `{"as_of": "iso8601", "scope": "all|project:<id>|source:<id>"}`.
- Response: `200` with the reconstructed state representation. Side-effect-free (no storage layer is mutated).
- Use cases: rollback preview, audit replay, disaster-recovery dry-run.

### Retention sweep

**`GET /v1/sweep/status`** — sweep run history and statistics.

- Response: `200` with the most recent sweep runs, the partition coverage, and per-run deletion counts. Used by the operator runbook and by the daily reconciliation report.

### Reconciliation (per `REQ-REL-audit-reconciliation`)

**`GET /v1/reconciliation/runs`** — list daily reconciliation reports.

- Response: `200` with paginated reports (`run_date`, `unmatched_mutations`, `gate_bypasses`, `orphan_audits`, link to the GBrain page).

**`POST /v1/reconciliation/run`** — trigger an on-demand reconciliation.

- Idempotency key: per-trigger UUID.
- Response: `202` with `{"run_id": "..."}`.

### Review queue (per `REQ-F-review-queue`)

**`GET /v1/review/queue`** — list pending review items.

- Query params: `?status=pending|disposed&reason=...&after=<cursor>`.
- Response: `200` paginated.

**`GET /v1/review/:review_id`** — review item detail (also surfaces in Obsidian as a `review_queue_item` page).

**`POST /v1/review/:review_id/dispose`** — dispose of a review item.

- Body: `{"disposition": "...", "reason": "..."?, "disposed_by": "..."}`.
- Idempotency key: per-disposition UUID.
- Response: `201` with the disposition event id.

### Stream endpoint for `hermes-runtime`

**`GET /v1/events/stream`** — long-poll / SSE endpoint for `hermes-runtime` to receive new events of interest.

- Query params: `?after=<last_event_id>&types=input.received,proposal.disposition,review.disposed`.
- Caller: `hermes-runtime` only (declared purpose: `agent_inbound`).
- Response: streams JSON events until idle timeout. Client reconnects with the new `last_event_id`.
- This is the only event-driven affordance in the API at MVP — the alternative would be polling, which works but adds latency. Stream is implemented over HTTP/1.1 chunked transfer or HTTP/2 server-sent events; the upstream contract is the same.

---

## `gbrain-bridge` HTTP API

The persistence service for the GBrain vault. All mutations flow through here per `CON-no-direct-agent-writes`.

### Page CRUD

**`POST /v1/pages`** — create a page.

- Caller: `hermes-runtime` (proposal pipeline) or `backlog-core` (cascade / system_doc creation).
- Body: `{"page": {<frontmatter + body>}, "proposal_id": "..."?}`. `proposal_id` required when called by `hermes-runtime`.
- Idempotency key: `proposal_id` (when present) or per-call UUID.
- Response: `201` with `{"page_id": "...", "vault_path": "..."}`.
- Errors: `422 schema_violation` (missing required frontmatter), `422 redaction_required` (raw content in `derived_keep` payload), `422 link_not_bidirectional` (forward-only link write).
- Side effects: bidirectional links written atomically; emits `gbrain.page_mutated` event to `backlog-core`.

**`GET /v1/pages/:page_id`** — read a page.

- Response: `200` with the page (frontmatter + body). For RTBF-redacted pages: `410 gone`.

**`PATCH /v1/pages/:page_id`** — update a page.

- Body: similar to POST; partial updates allowed for non-key frontmatter fields.
- Idempotency key: `proposal_id` or per-call UUID.
- Response: `200` with updated page.
- Same validation gates as POST.

**`DELETE /v1/pages/:page_id`** — delete a page.

- Body: `{"reason": "rtbf | archival", "rtbf_run_id?": "..."}`.
- Caller: `backlog-core` (RTBF cascade) or operator token (archival).
- Side effects: bidirectional back-links cleaned up atomically; emits `gbrain.page_mutated` (mutation_type `deleted`).

### Subject-scoped delete (RTBF cascade endpoint)

**`DELETE /v1/pages?subject_ref=...&rtbf_run_id=...`** — bulk delete all pages for a subject.

- Caller: `backlog-core` only.
- Response: `200` with `{"deleted_count": N, "page_ids": [...]}`.
- Side effects: cascade through bidirectional links; emit one `gbrain.page_mutated` per deletion.

### Vault audit sweep (per `REQ-MNT-vault-audit-sweep`)

**`POST /v1/audit-sweep`** — trigger a vault audit sweep.

- Body: `{"scope": "all|raw_check|schema_check|link_check"}`.
- Idempotency key: per-trigger UUID.
- Response: `202` with `{"sweep_run_id": "..."}`.
- Side effects: writes a `reconciliation`-style report page + emits `gbrain.audit_swept` event.

**`GET /v1/audit-sweep/runs`** — list sweep runs and counts.

### Obsidian watch-script disposition hook

**`POST /v1/dispositions`** — internal endpoint used by the watch script when an operator selects a command-palette command on an Obsidian page (per `DEC-obsidian-as-review-ui`).

- Caller: `gbrain-bridge`'s own watch process (loopback only — not exposed to ingress).
- Body: `{"page_path": "...", "command": "accept | reject | edit_and_accept | forward", "input": "..."?}`.
- Side effects: reads the page's frontmatter, translates the command into a `POST /v1/proposals/:id/disposition` or `POST /v1/review/:id/dispose` call to `backlog-core`.

---

## `kanban-sync` HTTP API

The persistence service for Obsidian Kanban boards. All card mutations flow through here.

### Card operations

**`POST /v1/cards`** — create a card from a proposal.

- Caller: `hermes-runtime` (proposal pipeline) or `backlog-core` (post-disposition apply).
- Body: `{"card": {<sync-owned frontmatter + body>}, "board_id": "...", "column": "...", "proposal_id": "..."?}`.
- Idempotency key: `proposal_id` (when present) or per-call UUID.
- Response: `201` with `{"card_id": "..."}`.
- Errors: `422 schema_violation` (sync-owned schema mismatch), `422 redaction_required` (raw content).

**`GET /v1/cards/:card_id`** — read a card. Returns sync-owned + user-owned frontmatter + body.

**`PATCH /v1/cards/:card_id`** — update card sync-owned fields.

- Body: partial sync-owned-fields update. **User-owned fields are never written by this endpoint** — they're preserved unchanged.
- Idempotency key: `proposal_id` or per-call UUID.

**`DELETE /v1/cards/:card_id`** — delete a card (RTBF cascade or archival).

### Subject-scoped delete (RTBF cascade)

**`DELETE /v1/cards?subject_ref=...&rtbf_run_id=...`** — bulk delete all cards referencing a subject.

- Caller: `backlog-core` only.

### Sync trigger

**`POST /v1/sync`** — trigger a sync of all boards (file-watcher fallback).

- Caller: `backlog-core` (scheduled) or operator token.
- Side effects: detects unattributed edits and column moves, emits `kanban.user_edit` and `unattributed_edit` events.

### Board read

**`GET /v1/boards/:project_id`** — read a project's Kanban board snapshot.

- Response: `200` with the board structure (columns, cards in order).

---

## `hermes-runtime` HTTP API

Minimal ingress — the agent is mostly an outbound caller. Endpoints exist for healthcheck and for operator-initiated agent actions.

**`GET /v1/health`** — healthcheck.

**`POST /v1/agent/process-now`** — operator-triggered processing of a specific input event (debugging / catch-up after maintenance).

- Caller: operator token.
- Body: `{"input_event_id": "..."}`.

No `/v1/agent/notify` endpoint — `hermes-runtime` consumes events via `backlog-core`'s `GET /v1/events/stream` (pull, not push).

---

## Ollama integration

`hermes-runtime` calls Ollama's standard local API:

- `POST http://ollama:11434/api/generate` — text generation.
- `POST http://ollama:11434/api/embeddings` — embedding generation.

No auth — Ollama runs on the internal Docker network only. Per `CON-local-first-inference`, no fallback to remote endpoints unless an explicit `remote_inference_profile` is configured (per `REQ-SEC-remote-inference-audit`); remote calls are routed through `hermes-runtime`'s model-router middleware which emits `remote_inference.called` events for every call.

---

## Operator CLI

The CLI binary (`vision`) ships in `scripts/`. All commands invoke `backlog-core` HTTP endpoints with the operator token; some commands also call `gbrain-bridge` and `kanban-sync` directly for read-only inspection.

### Source / consent management

| Command | Action |
|---|---|
| `vision source register` | interactive registration of a new ingestion source; calls `POST /v1/sources` |
| `vision source update <source_id>` | update `consent_scope` or `retention_policy`; calls `PATCH /v1/sources/:source_id` |
| `vision source revoke <source_id>` | revoke consent; calls `POST /v1/sources/:source_id/revoke` |
| `vision source list` | list active and revoked sources; calls `GET /v1/sources` |
| `vision source show <source_id>` | show current state and history; calls `GET /v1/sources/:source_id` and `GET /v1/sources/:source_id/history` |

### Data subject rights

| Command | Action |
|---|---|
| `vision rtbf <subject_ref>` | initiate RTBF cascade; calls `POST /v1/rtbf`; polls `GET /v1/rtbf/:run_id` until completion; prints verification result |
| `vision export <subject_ref> [--format json\|csv]` | produce subject export bundle; calls `POST /v1/exports`; downloads via `GET /v1/exports/:id` |

### Review queue (CLI fallback to Obsidian)

| Command | Action |
|---|---|
| `vision review list` | list pending review items |
| `vision review inspect <review_id>` | show full detail |
| `vision review dispose <review_id> --as <disposition>` | dispose; calls `POST /v1/review/:id/dispose` |

### Audit / state

| Command | Action |
|---|---|
| `vision audit query --type ... --from ... --to ...` | filtered audit query |
| `vision audit verify-chain` | end-to-end chain verification |
| `vision state preview --as-of <iso8601>` | preview state reconstruction |
| `vision reconciliation run` | trigger on-demand reconciliation |

### Operations (per `REQ-PORT-vps-deploy`, `REQ-REL-backup-restore-fidelity`, `REQ-REL-secret-rotation`)

| Command | Action |
|---|---|
| `vision install` | run `install_vps.sh`; bring up the Compose stack from a clean clone |
| `vision smoke-test` | run `smoke_test.sh`; full end-to-end MVP flow assertion |
| `vision backup [--out <path>]` | produce host-independent backup archive |
| `vision restore <archive>` | restore on this host; runs chain verification end-to-end before resuming writes |
| `vision rotate <secret-category>` | follow the rotation runbook for a secret category; verifies via smoke-test |
| `vision health` | aggregate `GET /v1/health` from all services |

CLI implementation: a single Go or Python binary (decision deferred to Code phase). Subcommands map to HTTP calls; output is human-readable by default, JSON via `--json`. Exit codes are documented per command.

---

## Obsidian command-palette bindings

Per [`DEC-obsidian-as-review-ui`](../decisions/DEC-obsidian-as-review-ui.md), operators dispose of review-queue items and proposal-detail pages via Obsidian command-palette commands. The bindings ship as a small repo-shipped configuration file that operators import into their vault.

| Command | Wired to |
|---|---|
| `Vision: Accept proposal` | reads frontmatter `proposal_id`; `gbrain-bridge` watch script posts `disposition: accept` to `POST /v1/proposals/:id/disposition` |
| `Vision: Edit and accept proposal` | prompts for edited content; posts `disposition: edit_and_accept` with `edit_content` |
| `Vision: Reject proposal` | prompts for reason; posts `disposition: reject` with `human_feedback` |
| `Vision: Reclassify review item to <project>` | dynamic command listing active projects; posts `POST /v1/review/:id/dispose` with `disposition: reclassify_to_project:<project_id>` |
| `Vision: Drop review item` | posts `disposition: drop` |
| `Vision: Forward review item to actor` | prompts for actor; posts `disposition: forward_to_actor:<id>` |

The watch script reads the current page's `id` and `type` to determine which endpoint to call. Pages outside the recognized types (`review_queue_item`, `proposal_detail`) reject the command with an Obsidian notice.

---

## Constraint compliance (API-design-specific)

| Constraint | API-design element |
|---|---|
| `CON-no-direct-agent-writes` | `proposal_id` required on `POST /v1/pages` and `POST /v1/cards` from `hermes-runtime`; persistence services reject without it |
| `CON-confidence-gated-autonomy` | `gate_inputs` required on every `POST /v1/proposals` body; `audit.gate_decision` events emitted by gate middleware before the call |
| `CON-consent-required` | every `input_event` carries `consent_check_result`; `POST /v1/inputs` rejects with `403 consent_revoked` if check fails |
| `CON-gdpr-applies` | `POST /v1/rtbf`, `POST /v1/exports`, `GET /v1/sources/:id/history` cover Art. 15 / 17 / 20 |
| `CON-tiered-retention` | `retention_class` carried on every event; sweep runs against `events` partitions; `GET /v1/sweep/status` exposes runs |
| `CON-gbrain-no-raw-private-truth` | `POST /v1/pages` rejects raw-content markers with `422 redaction_required` |
| `CON-human-correction-priority` | `POST /v1/proposals/:id/disposition` is a first-class endpoint; emits `learning_event` automatically |
| `CON-no-platform-bypass` | `POST /v1/inputs` accepts only `whatsorga-ingest`'s declared adapter contracts; review checklist enforces at design / code review |
| `CON-vps-portable-deployment` | All endpoints are HTTP/JSON; ingress profile (Caddy / Tailscale) is `.env`-driven |
| `CON-local-first-inference` | Ollama integration is the default; remote-inference profiles are `.env`-driven and audited via `remote_inference.called` |

## Approved-requirement coverage (API-design-specific)

| Requirement | Endpoint(s) |
|---|---|
| `REQ-F-source-registration` | `POST /v1/sources`, `PATCH /v1/sources/:id`; CLI `vision source register/update` |
| `REQ-F-consent-revocation` | `POST /v1/sources/:id/revoke`; `POST /v1/inputs` enforces `consent_check_result` |
| `REQ-F-retention-sweep` | `GET /v1/sweep/status`; sweep itself runs as scheduled job inside `backlog-core` |
| `REQ-COMP-consent-record` | `GET /v1/sources/:id/history?as_of=...` (read-as-of); `POST /v1/sources` enforces `lawful_basis = consent` |
| `REQ-COMP-rtbf` | `POST /v1/rtbf` + `GET /v1/rtbf/:run_id`; cascade endpoints `DELETE /v1/pages?subject_ref=...` and `DELETE /v1/cards?subject_ref=...` |
| `REQ-COMP-data-export` | `POST /v1/exports` + `GET /v1/exports/:id`; CLI `vision export` |
| `REQ-COMP-purpose-limitation` | every endpoint enforces the calling service's declared purposes against the source's `consent_scope` |
| `REQ-SEC-audit-log` | `GET /v1/audit/query`, `POST /v1/audit/verify-chain` |
| `REQ-SEC-redaction-precondition` | `POST /v1/pages` returns `422 redaction_required` |
| `REQ-SEC-remote-inference-audit` | `hermes-runtime` model-router middleware emits `remote_inference.called` events; queryable via `GET /v1/audit/query?event_type=remote_inference.called` |

## Decisions referenced

- [`DEC-direct-http-between-services`](../decisions/DEC-direct-http-between-services.md)
- [`DEC-api-versioning`](../decisions/DEC-api-versioning.md) (new)
- [`DEC-service-auth-bearer-tokens`](../decisions/DEC-service-auth-bearer-tokens.md) (new)
- [`DEC-idempotency-keys`](../decisions/DEC-idempotency-keys.md) (new)
- [`DEC-confidence-gate-as-middleware`](../decisions/DEC-confidence-gate-as-middleware.md)
- [`DEC-no-direct-agent-writes`](../1-spec/constraints/CON-no-direct-agent-writes.md) — enforcement at every persistence-service endpoint
- [`DEC-obsidian-as-review-ui`](../decisions/DEC-obsidian-as-review-ui.md)
- [`DEC-postgres-as-event-store`](../decisions/DEC-postgres-as-event-store.md)
- [`DEC-hash-chain-over-payload-hash`](../decisions/DEC-hash-chain-over-payload-hash.md)
- [`DEC-gdpr-legal-review-deferred`](../decisions/DEC-gdpr-legal-review-deferred.md)

## Dependency on `ASM-derived-artifacts-gdpr-permissible`

Per [`DEC-gdpr-legal-review-deferred`](../decisions/DEC-gdpr-legal-review-deferred.md):

**Where the API design depends on the assumption:**

- `POST /v1/sources` accepts a `consent_scope` JSONB without a `derivative_retention_consent` flag.
- `POST /v1/exports` produces a bundle that includes derived artifacts under the assumption that the original `consent_scope` covers indefinite retention of derivatives.
- `POST /v1/rtbf` cascades to derivatives by redaction, not by time-bounded expiration.

**Fallback if invalidated:**

- `consent_scope` JSONB gains `derivative_retention_consent: bool` (default `false`); `POST /v1/sources` and `PATCH /v1/sources/:id` accept the new flag (forward-compatible — old callers unchanged).
- `GET /v1/sources/:id/history?as_of=...` already supports the new key without API changes.
- A new optional query parameter on `GET /v1/audit/query?include_derived_expirations=true` exposes pending derivative-retention sweeps.
- `POST /v1/exports` adds a new field to the bundle: pending derivative expirations per artifact.
- `DELETE /v1/pages?subject_ref=...` semantics unchanged; a new `DELETE /v1/pages?expires_at_before=...` may be added for the new sweep job.

The migration is purely additive at the API surface — no breaking changes; existing clients keep working.
