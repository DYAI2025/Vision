# Tasks

## Status Legend

| Symbol | Status |
|--------|--------|
| `Todo` | Not started |
| `In Progress` | Currently being worked on |
| `Blocked` | Waiting on a dependency or decision (reason **must** be noted in the Notes column) |
| `Done` | Completed |
| `Cancelled` | No longer needed (reason **must** be noted in the Notes column) |

## Priority Legend

| Priority | Meaning |
|----------|---------|
| `P0` | Infrastructure / cross-cutting — required before feature work |
| `P1` | Implements a Must-have goal |
| `P2` | Implements a Should-have goal |
| `P3` | Implements a Could-have goal |

---

## Task Table

<!-- Req column: links to requirements this task implements (comma-separated), or "-" if none. -->

### Setup & Infrastructure

| ID | Task | Priority | Status | Req | Dependencies | Updated | Notes |
|----|------|----------|--------|-----|--------------|---------|-------|
| TASK-monorepo-skeleton | Top-level repo structure (per-component dirs, root README, CI placeholder) | P0 | Done | - | - | 2026-04-28 | Project README replaces scaffold's; `.github/workflows/ci.yml` runs structure check; per-component dirs already created by `/SDLC-decompose` |
| TASK-compose-stack-skeleton | `docker-compose.yml` with 6 services + Postgres + Ollama + ingress profile | P0 | Done | [REQ-PORT-vps-deploy](../1-spec/requirements/REQ-PORT-vps-deploy.md) | TASK-monorepo-skeleton | 2026-04-28 | Compose stack: 5 components (build contexts → `3-code/<component>/`) + Postgres 16-alpine + Ollama latest + Caddy/Tailscale as profile-gated ingress; healthchecks on `/v1/health`; named volumes; single internal bridge network per `DEC-direct-http-between-services`. `docker compose config` validation pending (Docker not installed locally). |
| TASK-env-example-bootstrap | `.env.example` with required keys + drift-check script | P0 | Done | [REQ-MNT-env-driven-config](../1-spec/requirements/REQ-MNT-env-driven-config.md) | TASK-compose-stack-skeleton | 2026-04-28 | `.env.example` declares 13 keys (Compose profile, Postgres, Caddy/Tailscale ingress, 6 service auth tokens per `DEC-service-auth-bearer-tokens`); `scripts/check-env-drift.sh` validates compose ↔ env alignment with intrinsic-key allowlist; CI gains `env-drift-check` job + token dummies in `compose-validate`; H-1 from code review fully closed — each service's `environment:` block now scopes auth tokens (own + accepted callers only). Negative-path drift detection verified locally. |
| TASK-postgres-bootstrap | Postgres container with empty database init | P0 | Done | - | TASK-compose-stack-skeleton | 2026-04-28 | Postgres image-based service already declared in compose; bootstrap layer adds: `4-deploy/postgres/init/` mount (RO) for first-start init scripts (currently empty by design — schema lands in Phase 2 via migrations); `4-deploy/postgres/README.md` documenting bootstrap, healthcheck, init semantics, backup conventions; `scripts/psql.sh` operator helper (chmod +x). |
| TASK-ollama-bootstrap | Ollama sidecar with Gemma model pull | P0 | Done | - | TASK-compose-stack-skeleton | 2026-04-28 | Ollama image-based service already declared in compose; bootstrap layer adds: `OLLAMA_MODEL=gemma3:4b` default in `.env.example` injected into hermes-runtime per `CON-local-first-inference`; `4-deploy/ollama/README.md` (model footprint table, opt-in remote-inference pointer); `scripts/ollama.sh` (generic exec wrapper) + `scripts/ollama-pull.sh` (one-time bootstrap pull, idempotent). Auto-pull at container start deferred (no upstream hook) — operator runs the pull script once after `docker compose up`; `TASK-install-vps-script` will fold this into the install runbook. Drift check caught a forgotten `.env.example` entry mid-task — fixed and re-verified clean (14 keys). |
| TASK-ingress-caddy-config | Caddy reverse-proxy config (`.env`-driven hostname) | P2 | Done | [REQ-MNT-env-driven-config](../1-spec/requirements/REQ-MNT-env-driven-config.md) | TASK-compose-stack-skeleton | 2026-04-28 | `4-deploy/ingress/Caddyfile` with path-based routing per `api-design.md` (per-service `/v1/health/<service>` rewrite for `vision health`; backlog-core / gbrain-bridge / kanban-sync / hermes-runtime path namespaces); `4-deploy/ingress/README.md` (operator-facing routing matrix + auto-TLS guidance for localhost vs. public hostname); `.env.example` adds `CADDY_HOSTNAME=localhost` + `CADDY_ACME_EMAIL=operator@example.com`; `docker-compose.yml` mounts Caddyfile read-only into `ingress-caddy` and injects new vars. Drift check clean (16 keys). |
| TASK-ingress-tailscale-config | Tailscale ingress profile (optional via `.env` flag) | P2 | Done | [REQ-MNT-env-driven-config](../1-spec/requirements/REQ-MNT-env-driven-config.md) | TASK-compose-stack-skeleton | 2026-04-28 | `4-deploy/ingress/tailscale-serve.json` declares 18 path-prefix routes (mirroring the Caddy matrix per `api-design.md`) on TCP 443 HTTPS, scoped to `${TS_CERT_DOMAIN}:443`; `docker-compose.yml` wires `TS_SERVE_CONFIG=/config/serve.json` and mounts the file read-only into `ingress-tailscale`; `4-deploy/ingress/README.md` Tailscale section completed (operator setup with auth-key creation, routing matrix, divergences from Caddy — no path rewrites means no `/v1/health/<service>` aggregation). No Funnel exposure (private-network-only per `REQ-PORT-vps-deploy`). Drift check clean (16 keys); JSON + YAML syntactic validation green. Pre-existing issue (resolved 2026-05-01 in `a336fe8`): `scripts/check-env-drift.sh` previously didn't filter YAML comments before scanning `${VAR}` references, surfacing a false positive on a prior comment shape. The fix adds a `sed -E 's/(^|[[:space:]])#.*//'` pre-strip before the `${VAR}` grep — covers both `# comment with ${VAR}` and `key: value  # trailing ${VAR}` shapes; verified with positive (comment-with-fake-var → exit 0) and negative (real undeclared var → exit 1) cases. |
| TASK-canonical-json-helper | Shared canonical-JSON serialization helper | P0 | Done | - | - | 2026-04-29 | Per `DEC-hash-chain-over-payload-hash`. **First Phase 2 task; settles the cross-component shared-utility location convention deferred from `DEC-backend-stack-python-fastapi`.** New [`DEC-shared-utility-path-deps`](../decisions/DEC-shared-utility-path-deps.md) (15th active): `3-code/_common/<package>/` siblings to per-component dirs, consumed via uv path-deps; component-isolation rule in `3-code/CLAUDE.code.md` amended with a narrow `_common/` carve-out (cross-component imports between component dirs still forbidden). New package `3-code/_common/canonical_json/` (20/20 tests green; ruff clean; mypy strict clean): `canonical_json(value) -> bytes` and `canonical_json_str(value) -> str` implementing JCS-style serialization (sort_keys=True, separators=(",",":"), ensure_ascii=False, allow_nan=False) — the property the audit chain depends on (key insertion order does not affect output) is verified directly. All 5 backend `pyproject.toml` files declare `canonical-json` under `[project] dependencies` + `[tool.uv.sources]` with `path = "../_common/canonical_json", editable = true`; per-component `uv.lock` files regenerated. All 5 backend Dockerfiles restructured to use **repo-root build context** + explicit `dockerfile: 3-code/<component>/Dockerfile`: builder stage copies `3-code/_common` → `/build/3-code/_common` (preserves the relative path the path-dep declares), then copies the component dir + runs `uv sync --frozen`; runtime stage copies `/opt/venv` + the component's `app/` + mirrors `/build/3-code/_common` so the venv's editable .pth files (which reference path-dep sources by absolute path) resolve. `docker-compose.yml`'s 5 backend `build:` blocks updated accordingly; `cli` service untouched (no `_common/` deps). New CI job `_common-canonical-json-test` (12 jobs total now); each consuming component's `cache-dependency-glob` updated to multi-line form including `3-code/_common/canonical_json/uv.lock` so caches invalidate on shared-helper changes. Smoke verified: `from canonical_json import canonical_json` works from all 5 backends; existing 67 backend tests unchanged green. Docker build / `docker compose build` validation deferred to CI (Docker not installed locally) — YAML and CI workflow syntax validated locally. |
| TASK-bearer-auth-middleware | Service-to-service bearer-token middleware with declared purposes | P0 | Done | - | TASK-env-example-bootstrap | 2026-05-02 | Per `DEC-service-auth-bearer-tokens`. Second cross-cutting helper under `3-code/_common/`, scoped to **inbound authentication only** — purpose-limitation enforcement is the next task per the Phase-2/Phase-3 split. New package `3-code/_common/bearer_auth/` (37/37 tests green; ruff clean; mypy strict clean) ships: `CallingIdentity` frozen dataclass; `BearerAuthVerifier` with `hmac.compare_digest` constant-time match + defensive copy of input mapping; `AcceptedTokens` env-driven config loader using the `<NAME>_TOKEN` convention already in `.env.example` (e.g., `hermes-runtime` → `HERMES_RUNTIME_TOKEN`); `MissingAuthError` / `InvalidAuthError` mapping to api-design.md `auth_required` / `auth_invalid` (HTTP 401); and the `require_bearer_auth` FastAPI dependency that attaches `request.state.calling_identity` for the next-task purpose middleware to read. Tests cover DEC § "Required checks" 1+2 (presence/recognition + malformed-header rejection); check 3 (purpose denial) defers to `TASK-purpose-limitation-middleware`. End-to-end FastAPI integration tests build a minimal app with the canonical wiring + a regression guard that `/v1/health` stays unauthenticated per api-design.md. Defense-in-depth: missing verifier state returns 401 `auth_required` (fail-closed); duplicate-token across distinct identities raises `ValueError` at startup. All 5 backend `pyproject.toml` files declare `bearer-auth` under `[project] dependencies` + `[tool.uv.sources]` path-dep `editable = true`; per-component `uv.lock` files regenerated (each adds bearer-auth at v0.0.1; starlette pinned to 0.41.3 within FastAPI's compatible range). New CI job `_common-bearer-auth-test` (13 jobs total now); each consuming component's `cache-dependency-glob` adds `3-code/_common/bearer_auth/uv.lock`. Backend Dockerfiles unchanged — the repo-root build context + `_common/` copy already established by `TASK-canonical-json-helper` accommodates additional `_common/` packages without modification. Compose config validated locally (`docker compose --profile caddy config --quiet`); env-drift check clean (19 keys unchanged — no new env vars). 67/67 backend skeleton tests still green. **Pre-existing observation correction (closed by 2026-05-02-backlog-core-cast-quotes-followup):** The original closeout claimed `cast(_PoolLike, pool)` in `3-code/backlog-core/app/db.py:85` triggered ruff `TC006`. On verification this is not reproducible — ruff 0.7.4 (our pinned version) does not ship a `TC006` rule, and the per-component CI invocation (`uv run --frozen ruff check .` inside the component dir) is clean. The misread was likely an inadvertent ruff run that crossed config boundaries. The follow-up plan applied the forward-compatible `cast("_PoolLike", pool)` quoted-string form anyway (zero runtime cost; mypy strict accepts it identically) so a future ruff upgrade that does ship `TC006` will land green on this site. Convention pin (informational, not a new decision): bearer-auth's `dependency.py` deliberately does NOT use `from __future__ import annotations` because FastAPI's `get_type_hints` introspection of dependency signatures requires runtime-resolvable annotations — encoded in the README "Wiring" section so future shared FastAPI-dependency packages follow the same rule. |
| TASK-idempotency-middleware | Shared `Idempotency-Key` middleware + idempotency store | P0 | Todo | - | TASK-bearer-auth-middleware, TASK-postgres-events-schema | 2026-04-28 | Per `DEC-idempotency-keys` |
| TASK-purpose-limitation-middleware | Per-endpoint purpose check from declared component manifests | P1 | Todo | [REQ-COMP-purpose-limitation](../1-spec/requirements/REQ-COMP-purpose-limitation.md) | TASK-bearer-auth-middleware | 2026-04-28 |  |
| TASK-subject-ref-normalization | Subject-reference normalization function shared across services | P0 | Todo | - | - | 2026-04-28 | Verifies `ASM-subject-reference-resolvable` |

### whatsorga-ingest

| ID | Task | Priority | Status | Req | Dependencies | Updated | Notes |
|----|------|----------|--------|-----|--------------|---------|-------|
| TASK-whatsorga-skeleton | `whatsorga-ingest` service: Dockerfile + `/v1/health` | P0 | Done | - | TASK-compose-stack-skeleton | 2026-04-28 | First per-component skeleton; established the uniform backend stack convention via new [`DEC-backend-stack-python-fastapi`](../decisions/DEC-backend-stack-python-fastapi.md) (Python 3.12 + FastAPI + uv + pytest + ruff + mypy strict; applies to all 5 backend components, CLI deferred). Skeleton: `app/main.py` exposes only `GET /v1/health` returning `{status, version, checks}` per `api-design.md`; `app/__init__.py` reads version via `importlib.metadata`; multi-stage Dockerfile (uv builder → `python:3.12-slim` runtime, non-root UID 1000, port 8000); committed `uv.lock` (35 packages); `.dockerignore`, `.gitignore`, `.python-version=3.12`. Tests (`tests/test_health.py`): 5 cases — 200, payload shape per design, `status=ok`, no auth required, unknown path 404 — all green locally (ruff clean, mypy strict clean, pytest 5 passed). New CI job `whatsorga-ingest-test` runs setup-uv (cached on uv.lock) → `uv sync --frozen` → ruff → mypy → pytest. README documents build/run/test commands. Cross-component utility location (vendoring vs `_common/` carve-out) deferred to `TASK-canonical-json-helper` per user agreement. |
| TASK-whatsorga-normalization | Normalization layer producing channel-agnostic `input_event`s | P1 | Todo | [REQ-F-input-event-normalization](../1-spec/requirements/REQ-F-input-event-normalization.md) | TASK-whatsorga-skeleton, TASK-canonical-json-helper | 2026-04-28 | Verifies `ASM-channel-shape-convergeable` via swap-test |
| TASK-whatsorga-manual-cli-adapter | Manual CLI adapter (simplest channel) | P1 | Todo | [REQ-F-input-event-normalization](../1-spec/requirements/REQ-F-input-event-normalization.md) | TASK-whatsorga-normalization | 2026-04-28 |  |
| TASK-whatsorga-consent-check | Consent-snapshot + drop-revoked logic at boundary | P1 | Todo | [REQ-F-consent-revocation](../1-spec/requirements/REQ-F-consent-revocation.md) | TASK-whatsorga-normalization, TASK-source-history-endpoint | 2026-04-28 |  |
| TASK-whatsapp-adapter | WhatsApp ingest adapter (user-attached session) | P1 | Todo | [REQ-F-input-event-normalization](../1-spec/requirements/REQ-F-input-event-normalization.md) | TASK-whatsorga-normalization | 2026-04-28 | Per `DEC-platform-bypass-review-checklist` — no headless login, no token replay |
| TASK-voice-adapter | Voice transcript ingest adapter | P1 | Todo | [REQ-F-input-event-normalization](../1-spec/requirements/REQ-F-input-event-normalization.md) | TASK-whatsorga-normalization | 2026-04-28 |  |
| TASK-repo-events-adapter | Repository webhook receiver adapter | P1 | Todo | [REQ-F-input-event-normalization](../1-spec/requirements/REQ-F-input-event-normalization.md) | TASK-whatsorga-normalization | 2026-04-28 |  |

### hermes-runtime

| ID | Task | Priority | Status | Req | Dependencies | Updated | Notes |
|----|------|----------|--------|-----|--------------|---------|-------|
| TASK-hermes-skeleton | `hermes-runtime` service: Dockerfile + `/v1/health` + Ollama client | P0 | Done | - | TASK-compose-stack-skeleton, TASK-ollama-bootstrap | 2026-04-28 | Second per-component skeleton, applies `DEC-backend-stack-python-fastapi`. Skeleton mirrors `whatsorga-ingest`'s template (multi-stage Dockerfile, non-root, port 8000) plus `app/ollama_client.py` — async wrapper over `POST /api/generate` and `POST /api/embeddings` per `hermes-runtime/CLAUDE.component.md` interfaces. Reads `OLLAMA_URL` / `OLLAMA_MODEL` from env (defaults: `http://ollama:11434`, `gemma3:4b`). Custom `OllamaError` for malformed payloads; `httpx.HTTPStatusError` propagates on non-2xx. Tests: 5 health-endpoint cases (mirror) + 9 client cases using `httpx.MockTransport` (no Ollama process required) — 14/14 green; ruff clean; mypy strict clean. New CI job `hermes-runtime-test` mirrors `whatsorga-ingest-test`. Audit-log emission for remote-inference profiles deferred to `TASK-model-router` / `TASK-remote-inference-profile` per `REQ-SEC-remote-inference-audit`. |
| TASK-hermes-events-consumer | Long-poll consumer of `GET /v1/events/stream` + dispatcher stub | P1 | Todo | [REQ-USA-paginated-lists](../1-spec/requirements/REQ-USA-paginated-lists.md) | TASK-hermes-skeleton, TASK-events-stream-endpoint | 2026-04-29 | Consumer side of the SSE convention: reconnect with `?last_event_id=`, respect 30 s heartbeat, handle 5 min connection cap with auto-reconnect-and-resume per `DEC-cursor-pagination-and-event-stream-conventions`. |
| TASK-confidence-gate-middleware | Three-band gate middleware with band-thresholds config | P1 | Todo | [REQ-F-confidence-gate](../1-spec/requirements/REQ-F-confidence-gate.md) | TASK-hermes-events-consumer, TASK-purpose-limitation-middleware | 2026-04-28 | Per `DEC-confidence-gate-as-middleware` |
| TASK-routing-skill | Project-routing skill producing `routing_decision` | P1 | Todo | [REQ-F-project-routing](../1-spec/requirements/REQ-F-project-routing.md) | TASK-confidence-gate-middleware | 2026-04-28 | Verifies `ASM-confidence-scores-are-meaningful` (calibration curve) |
| TASK-brain-first-lookup | Brain-first lookup + `cited_pages` recording | P1 | Todo | [REQ-F-brain-first-lookup](../1-spec/requirements/REQ-F-brain-first-lookup.md) | TASK-routing-skill, TASK-gbrain-page-crud | 2026-04-28 |  |
| TASK-extraction-skill | Artifact-extraction skill (typed candidates) | P1 | Todo | [REQ-F-artifact-extraction](../1-spec/requirements/REQ-F-artifact-extraction.md) | TASK-routing-skill | 2026-04-28 |  |
| TASK-duplicate-detection-skill | Semantic + lexical duplicate detector | P1 | Todo | [REQ-F-duplicate-detection](../1-spec/requirements/REQ-F-duplicate-detection.md) | TASK-extraction-skill | 2026-04-28 |  |
| TASK-model-router | Model-router middleware with default-local + remote-profile support | P1 | Todo | [REQ-SEC-remote-inference-audit](../1-spec/requirements/REQ-SEC-remote-inference-audit.md) | TASK-hermes-skeleton | 2026-04-28 | Per `CON-local-first-inference` |
| TASK-learning-loop-skill | Within-session prompt-context refresh + routing-rules update | P1 | Todo | [REQ-F-learning-loop](../1-spec/requirements/REQ-F-learning-loop.md) | TASK-learning-event-emit, TASK-gbrain-page-crud | 2026-04-28 | Verifies `ASM-in-session-learning-feasible` |
| TASK-remote-inference-profile | `.env`-driven remote-inference profile config + audit emission | P1 | Todo | [REQ-SEC-remote-inference-audit](../1-spec/requirements/REQ-SEC-remote-inference-audit.md) | TASK-model-router, TASK-event-emit-primitive | 2026-04-28 |  |

### backlog-core

| ID | Task | Priority | Status | Req | Dependencies | Updated | Notes |
|----|------|----------|--------|-----|--------------|---------|-------|
| TASK-backlog-core-skeleton | `backlog-core` service: Dockerfile + `/v1/health` + Postgres connection | P0 | Done | - | TASK-postgres-bootstrap | 2026-04-28 | Third per-component skeleton, applies `DEC-backend-stack-python-fastapi` + `DEC-postgres-as-event-store`. Skeleton template (Dockerfile multi-stage, non-root, port 8000; `pyproject.toml` adds asyncpg `>=0.30,<0.31`; `uv.lock` 36 packages). `app/db.py` provides the asyncpg connection-pool lifecycle (`@asynccontextmanager` lifespan stores pool on `app.state.pool`, closes on shutdown), a `_PoolLike` Protocol for test fakes, `get_pool` FastAPI dependency, and a non-raising `ping(pool)` primitive that runs `SELECT 1`. `app/main.py` wires lifespan + `Annotated[_PoolLike, Depends(...)]` so `/v1/health` reports `{"checks": {"postgres": "ok|down"}}` and degrades to `status: "degraded"` when Postgres is unreachable. Tests (11/11 green): `tests/conftest.py` ships an in-process `FakePool` (no Postgres process required) + `client_with_pool` fixture; `tests/test_health.py` covers 6 health-endpoint cases (200, payload shape, postgres ok, postgres down → degraded, no auth, 404); `tests/test_db.py` covers 5 cases (DATABASE_URL set + raise-when-unset; ping ok; ping false on connection-raise; ping false on broken pool). ruff clean (after refactoring `Depends` default → `Annotated[..., Depends]`), mypy strict clean (with `[[tool.mypy.overrides]]` for asyncpg's missing stubs). New CI job `backlog-core-test` mirrors prior templates. DATABASE_URL fail-fast at startup per REQ-MNT-env-driven-config — schema, idempotency store, hash-chain audit, RTBF cascade, retention sweep, etc. land in subsequent Phase 2 / Phase 3 / Phase 4 / Phase 6 / Phase 7 tasks. |
| TASK-postgres-events-schema | `events` table + indexes per `data-model.md` | P1 | Done | [REQ-SEC-audit-log](../1-spec/requirements/REQ-SEC-audit-log.md) | TASK-backlog-core-skeleton | 2026-05-07 | Closed in Sprint 2 after review: migration `0001_create-events-table.sql` creates the partitioned event log, indexes, constraints, and first 12 monthly partitions; schema/insertion/default/idempotency tests remain green. |
| TASK-postgres-consent-schema | `consent_sources` + `consent_history` tables | P1 | Done | [REQ-COMP-consent-record](../1-spec/requirements/REQ-COMP-consent-record.md) | TASK-backlog-core-skeleton | 2026-05-07 | Added migration `0002_create-consent-tables.sql` with `consent_sources` current-state records, append-only `consent_history`, lawful-basis/retention/state/scope CHECK constraints, read-as-of index `(source_id, changed_at DESC)`, and tests for schema shape, default false MVP purpose flags, consent-only lawful basis, append-only mutation rejection, and read-as-of behavior. `event_id` is application-validated rather than DB-FK because `events` is partitioned with composite PK `(event_id, created_at)`. Forward-compatible for `DEC-gdpr-legal-review-deferred` fallback via JSONB-additive consent flags. |
| TASK-postgres-events-partitioning | Monthly partitioning + partition-creation cron | P1 | Todo | [REQ-F-retention-sweep](../1-spec/requirements/REQ-F-retention-sweep.md) | TASK-postgres-events-schema | 2026-04-28 |  |
| TASK-event-emit-primitive | Event-emit with `payload_hash` + chain linkage | P1 | Done | [REQ-SEC-audit-log](../1-spec/requirements/REQ-SEC-audit-log.md) | TASK-postgres-events-schema, TASK-canonical-json-helper | 2026-05-07 | `backlog-core/app/events.py` computes SHA-256 over canonical JSON payloads, serializes stable event-hash material, uses a transaction-scoped advisory lock, links to the previous event hash, inserts the event row, and returns persisted hash material. Unit tests cover payload-hash stability, prev-hash sensitivity, advisory locking, and inserted hash columns. |
| TASK-hash-chain-verify | Chain-verification routine + secondary integrity check | P1 | Todo | [REQ-SEC-audit-log](../1-spec/requirements/REQ-SEC-audit-log.md) | TASK-event-emit-primitive | 2026-04-28 |  |
| TASK-source-registration-endpoint | `POST /v1/sources` + first `consent_history` row | P1 | Done | [REQ-F-source-registration](../1-spec/requirements/REQ-F-source-registration.md) | TASK-postgres-consent-schema, TASK-event-emit-primitive, TASK-bearer-auth-middleware | 2026-05-07 | `POST /v1/sources` returns `201` with the created source record and persists `source.registered` plus the initial append-only consent-history row atomically. Endpoint tests verify bearer-auth gating, request forwarding, and response shape. |
| TASK-source-update-endpoint | `PATCH /v1/sources/:id` (consent_scope / retention_policy) | P1 | Done | [REQ-F-source-registration](../1-spec/requirements/REQ-F-source-registration.md) | TASK-source-registration-endpoint | 2026-05-07 | `PATCH /v1/sources/{source_id}` applies partial consent-scope / retention-policy changes, rejects empty patches with validation error, emits `source.consent_updated`, and appends a history version. |
| TASK-source-revoke-endpoint | `POST /v1/sources/:id/revoke` + halt-ingest semantics | P1 | Done | [REQ-F-consent-revocation](../1-spec/requirements/REQ-F-consent-revocation.md) | TASK-source-registration-endpoint | 2026-05-07 | `POST /v1/sources/{source_id}/revoke` marks the source `revoked`, emits `source.consent_revoked`, and appends a history version so the future ingest boundary can halt this source from current state. |
| TASK-source-history-endpoint | `GET /v1/sources/:id/history` with `?as_of=` | P1 | Done | [REQ-COMP-consent-record](../1-spec/requirements/REQ-COMP-consent-record.md), [REQ-USA-paginated-lists](../1-spec/requirements/REQ-USA-paginated-lists.md) | TASK-source-registration-endpoint | 2026-05-07 | `GET /v1/sources/{source_id}/history` returns append-only history; `?as_of=` returns the version in effect at the requested timestamp. Cursor pagination is still listed separately for broader list endpoints/audit query hardening. |
| TASK-audit-query-endpoint | `GET /v1/audit/query` with filters + pagination | P1 | Todo | [REQ-SEC-audit-log](../1-spec/requirements/REQ-SEC-audit-log.md), [REQ-USA-paginated-lists](../1-spec/requirements/REQ-USA-paginated-lists.md) | TASK-event-emit-primitive | 2026-04-29 | Canonical cursor-paginated list endpoint per `DEC-cursor-pagination-and-event-stream-conventions`: `?after=<cursor>&limit=<n>` (default 50, max 500), `next_cursor: null` end-of-page signal, retention-sweep tolerant. |
| TASK-audit-verify-chain-endpoint | `POST /v1/audit/verify-chain` | P1 | Todo | [REQ-SEC-audit-log](../1-spec/requirements/REQ-SEC-audit-log.md) | TASK-hash-chain-verify | 2026-04-28 |  |
| TASK-input-event-endpoint | `POST /v1/inputs` writing `input.received` events | P1 | Todo | [REQ-F-input-event-normalization](../1-spec/requirements/REQ-F-input-event-normalization.md) | TASK-event-emit-primitive, TASK-idempotency-middleware | 2026-04-28 |  |
| TASK-proposal-pipeline-endpoint | `POST /v1/proposals` with `gate_inputs` validation | P1 | Todo | [REQ-F-proposal-pipeline](../1-spec/requirements/REQ-F-proposal-pipeline.md), [REQ-F-confidence-gate](../1-spec/requirements/REQ-F-confidence-gate.md) | TASK-event-emit-primitive, TASK-idempotency-middleware, TASK-purpose-limitation-middleware | 2026-04-28 |  |
| TASK-proposal-detail-endpoint | `GET /v1/proposals/:id` returning chain + gate inputs | P1 | Todo | [REQ-F-decision-inspection](../1-spec/requirements/REQ-F-decision-inspection.md) | TASK-proposal-pipeline-endpoint | 2026-04-28 |  |
| TASK-events-stream-endpoint | `GET /v1/events/stream` long-poll/SSE | P1 | Todo | [REQ-USA-paginated-lists](../1-spec/requirements/REQ-USA-paginated-lists.md) | TASK-event-emit-primitive | 2026-04-29 | Canonical implementation of the SSE half of `DEC-cursor-pagination-and-event-stream-conventions`: `?last_event_id=`, 30 s heartbeat, 5 min connection cap. |
| TASK-subject-index-matview | `subject_index` materialized view + refresh triggers | P1 | Todo | [REQ-COMP-rtbf](../1-spec/requirements/REQ-COMP-rtbf.md) | TASK-postgres-events-schema, TASK-subject-ref-normalization | 2026-04-28 |  |
| TASK-retention-sweep-service | Daily idempotent sweep with crash safety | P1 | Todo | [REQ-F-retention-sweep](../1-spec/requirements/REQ-F-retention-sweep.md) | TASK-postgres-events-partitioning | 2026-04-28 |  |
| TASK-retention-sweep-endpoint | `GET /v1/sweep/status` + per-run statistics | P1 | Todo | [REQ-F-retention-sweep](../1-spec/requirements/REQ-F-retention-sweep.md) | TASK-retention-sweep-service | 2026-04-28 |  |
| TASK-rtbf-cascade-engine | Cascade engine with layer fan-out + verification | P1 | Todo | [REQ-COMP-rtbf](../1-spec/requirements/REQ-COMP-rtbf.md) | TASK-subject-index-matview, TASK-event-emit-primitive | 2026-04-28 | Verifies `ASM-rtbf-24h-window-acceptable` performance |
| TASK-rtbf-endpoints | `POST /v1/rtbf` + `GET /v1/rtbf/:run_id` | P1 | Todo | [REQ-COMP-rtbf](../1-spec/requirements/REQ-COMP-rtbf.md) | TASK-rtbf-cascade-engine | 2026-04-28 |  |
| TASK-data-export-tool | Export tool producing JSON bundle | P1 | Todo | [REQ-COMP-data-export](../1-spec/requirements/REQ-COMP-data-export.md) | TASK-subject-index-matview | 2026-04-28 |  |
| TASK-data-export-endpoints | `POST /v1/exports` + `GET /v1/exports/:export_id` | P1 | Todo | [REQ-COMP-data-export](../1-spec/requirements/REQ-COMP-data-export.md) | TASK-data-export-tool | 2026-04-28 |  |
| TASK-review-queue-endpoints | `GET /v1/review/queue` + `GET/POST /v1/review/:id*` | P1 | Todo | [REQ-F-review-queue](../1-spec/requirements/REQ-F-review-queue.md), [REQ-USA-paginated-lists](../1-spec/requirements/REQ-USA-paginated-lists.md) | TASK-event-emit-primitive | 2026-04-29 | List endpoint follows cursor pagination per `DEC-cursor-pagination-and-event-stream-conventions`. |
| TASK-proposal-disposition-endpoint | `POST /v1/proposals/:id/disposition` + diff capture | P1 | Todo | [REQ-F-correction-actions](../1-spec/requirements/REQ-F-correction-actions.md) | TASK-proposal-pipeline-endpoint | 2026-04-28 |  |
| TASK-learning-event-emit | Auto-emit `learning_event` on every disposition | P1 | Todo | [REQ-F-correction-actions](../1-spec/requirements/REQ-F-correction-actions.md) | TASK-proposal-disposition-endpoint | 2026-04-28 |  |
| TASK-state-reconstruction-service | Replay engine producing in-memory state at `as_of` | P1 | Todo | [REQ-F-state-reconstruction](../1-spec/requirements/REQ-F-state-reconstruction.md) | TASK-event-emit-primitive | 2026-04-28 |  |
| TASK-state-reconstruction-endpoint | `POST /v1/state/reconstruct` (preview-mode) | P1 | Todo | [REQ-F-state-reconstruction](../1-spec/requirements/REQ-F-state-reconstruction.md) | TASK-state-reconstruction-service | 2026-04-28 |  |
| TASK-daily-reconciliation-job | Daily reconciliation: unmatched mutations + gate bypasses + orphans | P1 | Todo | [REQ-REL-audit-reconciliation](../1-spec/requirements/REQ-REL-audit-reconciliation.md) | TASK-event-emit-primitive | 2026-04-28 |  |
| TASK-reconciliation-endpoints | `GET /v1/reconciliation/runs` + `POST /v1/reconciliation/run` | P1 | Todo | [REQ-REL-audit-reconciliation](../1-spec/requirements/REQ-REL-audit-reconciliation.md) | TASK-daily-reconciliation-job | 2026-04-28 |  |
| TASK-event-replay-correctness-tests | Boundary tests for replay determinism, idempotence, crash safety, fail-fast | P1 | Todo | [REQ-REL-event-replay-correctness](../1-spec/requirements/REQ-REL-event-replay-correctness.md) | TASK-state-reconstruction-service | 2026-04-28 |  |

### gbrain-bridge

| ID | Task | Priority | Status | Req | Dependencies | Updated | Notes |
|----|------|----------|--------|-----|--------------|---------|-------|
| TASK-gbrain-bridge-skeleton | `gbrain-bridge` service: Dockerfile + `/v1/health` + vault volume mount | P0 | Done | - | TASK-compose-stack-skeleton | 2026-04-28 | Fourth per-component skeleton, applies `DEC-backend-stack-python-fastapi`. Same multi-stage Dockerfile / non-root / port 8000 template; 35 packages locked. `app/vault.py` provides the filesystem layer: `vault_path()` reads `VAULT_PATH` from env (default `/vault`); `is_readable(path)` returns `True` iff the path exists, is a directory, and the process can iterate it — never raises (health-probe semantics fold permission errors into `False`). `app/main.py` exposes `GET /v1/health` doing a live `is_readable(vault_path())` check, returning **HTTP 503 with `status: "degraded"`, `checks.vault: "down"`** when the vault mount is missing/unreadable, mirroring the 503-on-degraded pattern hardened on backlog-core. Tests (14/14 green): `tests/test_vault.py` 7 cases (default path, env override, real dir ok, missing path, file-not-dir, permission-error duck-typed, non-empty dir); `tests/test_health.py` 7 cases (200/503 for ok/degraded paths via pytest's `tmp_path` + monkeypatch — no real `/vault` mount required). ruff clean (after `pytest` import → TYPE_CHECKING block since only used as annotation), mypy strict clean. New CI job `gbrain-bridge-test` mirrors prior templates. Page CRUD, schema validation, bidirectional links, redaction precondition, RTBF cascade, watch script, weekly vault audit sweep land in subsequent Phase 4 / Phase 5 / Phase 6 / Phase 7 tasks. |
| TASK-gbrain-cascade-endpoint | `DELETE /v1/pages?subject_ref=...` + bidirectional cleanup | P1 | Todo | [REQ-COMP-rtbf](../1-spec/requirements/REQ-COMP-rtbf.md) | TASK-gbrain-bridge-skeleton, TASK-bearer-auth-middleware | 2026-04-28 |  |
| TASK-gbrain-page-schema-validator | Per-type frontmatter validator | P1 | Todo | [REQ-F-gbrain-schema](../1-spec/requirements/REQ-F-gbrain-schema.md) | TASK-gbrain-bridge-skeleton | 2026-04-28 |  |
| TASK-gbrain-page-crud | `POST/GET/PATCH/DELETE /v1/pages` | P1 | Todo | [REQ-F-gbrain-schema](../1-spec/requirements/REQ-F-gbrain-schema.md) | TASK-gbrain-page-schema-validator, TASK-idempotency-middleware | 2026-04-28 |  |
| TASK-gbrain-bidirectional-links | Atomic forward+back link writes; half-link rejection | P1 | Todo | [REQ-F-bidirectional-links](../1-spec/requirements/REQ-F-bidirectional-links.md) | TASK-gbrain-page-crud | 2026-04-28 |  |
| TASK-gbrain-redaction-precondition | Raw-content marker detection + reject on `derived_keep` | P1 | Todo | [REQ-SEC-redaction-precondition](../1-spec/requirements/REQ-SEC-redaction-precondition.md) | TASK-gbrain-page-crud | 2026-04-28 |  |
| TASK-review-queue-page-format | `review_queue_item` GBrain page schema + write path | P1 | Todo | [REQ-F-review-queue](../1-spec/requirements/REQ-F-review-queue.md) | TASK-gbrain-page-crud | 2026-04-28 |  |
| TASK-proposal-detail-page-format | `proposal_detail` GBrain page schema + write path | P1 | Todo | [REQ-F-decision-inspection](../1-spec/requirements/REQ-F-decision-inspection.md) | TASK-gbrain-page-crud | 2026-04-28 |  |
| TASK-obsidian-watch-script | File-system watch + command-palette → HTTP translation | P1 | Todo | - | TASK-review-queue-page-format, TASK-proposal-detail-page-format | 2026-04-28 | Per `DEC-obsidian-as-review-ui` |
| TASK-disposition-hook-endpoint | `POST /v1/dispositions` (loopback) | P1 | Todo | [REQ-F-correction-actions](../1-spec/requirements/REQ-F-correction-actions.md) | TASK-obsidian-watch-script | 2026-04-28 |  |
| TASK-obsidian-bindings-bundle | `obsidian-bindings/` config files for operators to import | P1 | Todo | - | TASK-obsidian-watch-script | 2026-04-28 |  |
| TASK-vault-audit-sweep | Weekly sweep: schema, links, redaction, retention consistency | P1 | Todo | [REQ-MNT-vault-audit-sweep](../1-spec/requirements/REQ-MNT-vault-audit-sweep.md) | TASK-gbrain-page-schema-validator, TASK-gbrain-bidirectional-links | 2026-04-28 |  |
| TASK-vault-audit-sweep-endpoint | `POST /v1/audit-sweep` + `GET /v1/audit-sweep/runs` | P1 | Todo | [REQ-MNT-vault-audit-sweep](../1-spec/requirements/REQ-MNT-vault-audit-sweep.md) | TASK-vault-audit-sweep | 2026-04-28 |  |

### kanban-sync

| ID | Task | Priority | Status | Req | Dependencies | Updated | Notes |
|----|------|----------|--------|-----|--------------|---------|-------|
| TASK-kanban-sync-skeleton | `kanban-sync` service: Dockerfile + `/v1/health` + Kanban subtree mount | P0 | Done | - | TASK-compose-stack-skeleton | 2026-04-29 | Fifth and final per-component skeleton, applies `DEC-backend-stack-python-fastapi`. Same multi-stage Dockerfile / non-root / port 8000 template; 35 packages locked. `app/kanban.py` provides the filesystem layer scoped to the **Kanban subtree** specifically: `vault_path()` reads `VAULT_PATH` (read-only access for project-page link resolution); `kanban_subtree()` reads `KANBAN_SUBTREE` (default `/vault/Kanban`, read/write); `is_writable(path)` returns `True` iff the path exists, is a directory, and is read+writable via `os.access(path, R_OK | W_OK)` — never raises. `app/main.py` exposes `GET /v1/health` doing a live `is_writable(kanban_subtree())` check, returning **HTTP 503 with `status: "degraded"`, `checks.kanban_subtree: "down"`** when missing/unwritable, mirroring the 503-on-degraded pattern hardened on backlog-core and gbrain-bridge. The skeleton intentionally does not auto-create the subtree — by design, misconfiguration is visible rather than silent. Tests (19/19 green): `tests/test_kanban.py` 11 cases (default/env paths for both VAULT_PATH and KANBAN_SUBTREE, real dir, missing path, file-not-dir, read-only-dir via chmod 0555, OSError-raising duck-type, non-empty dir, default-subtree-under-default-vault path invariant); `tests/test_health.py` 8 cases (200/503 for ok/degraded paths via pytest's `tmp_path` + monkeypatch, including a "subtree is a file" misconfig case). ruff clean (after `pytest` import → TYPE_CHECKING block since only used as annotation), mypy strict clean. New CI job `kanban-sync-test` is the fifth component-test job — trailing comment in ci.yml updated to note all 5 backend templates landed; only cli's TBD-tech-stack CI job left. Card CRUD, sync-vs-edit boundary, manual column-move attribution, periodic `POST /v1/sync`, and the RTBF cascade endpoint defer to Phase 4 / Phase 5. |
| TASK-kanban-cascade-endpoint | `DELETE /v1/cards?subject_ref=...` | P1 | Todo | [REQ-COMP-rtbf](../1-spec/requirements/REQ-COMP-rtbf.md) | TASK-kanban-sync-skeleton, TASK-bearer-auth-middleware | 2026-04-28 |  |
| TASK-kanban-card-crud | `POST/GET/PATCH/DELETE /v1/cards` | P1 | Todo | [REQ-USA-kanban-obsidian-fidelity](../1-spec/requirements/REQ-USA-kanban-obsidian-fidelity.md) | TASK-kanban-sync-skeleton, TASK-idempotency-middleware | 2026-04-28 |  |
| TASK-kanban-sync-vs-edit | Sync-owned vs user-owned field detection | P1 | Todo | [REQ-USA-kanban-obsidian-fidelity](../1-spec/requirements/REQ-USA-kanban-obsidian-fidelity.md) | TASK-kanban-card-crud | 2026-04-28 |  |
| TASK-kanban-column-move-detection | Manual column-move detection → `kanban.user_edit` | P1 | Todo | [REQ-USA-kanban-obsidian-fidelity](../1-spec/requirements/REQ-USA-kanban-obsidian-fidelity.md) | TASK-kanban-sync-vs-edit | 2026-04-28 |  |
| TASK-kanban-sync-trigger | `POST /v1/sync` periodic + on-demand | P1 | Todo | [REQ-USA-kanban-obsidian-fidelity](../1-spec/requirements/REQ-USA-kanban-obsidian-fidelity.md) | TASK-kanban-card-crud | 2026-04-28 |  |

### cli

| ID | Task | Priority | Status | Req | Dependencies | Updated | Notes |
|----|------|----------|--------|-----|--------------|---------|-------|
| TASK-cli-skeleton | `vision` binary skeleton + `vision health` aggregator | P0 | Done | - | - | 2026-04-29 | Sixth and final per-component skeleton; second per-component tech-stack decision point. New [`DEC-cli-stack-python-typer`](../decisions/DEC-cli-stack-python-typer.md) settles the cli's stack: Python 3.12 + Typer + httpx + Pydantic + python-dotenv + Rich, distributed via `uv tool install` (primary) and a profile-gated `cli` Compose service (secondary). `app/main.py` registers the Typer app + `vision health` command + global `--version`; `app/config.py` provides env / `.env`-driven base URL + `OPERATOR_TOKEN` discovery (precedence: `--base-url` arg > `VISION_BASE_URL` env > nearest upward `.env` > default `http://localhost`); `app/health.py` is the parallel-fan-out aggregator (`asyncio.gather` over the 5 backend services hitting `/v1/health/<service>` Caddy aggregation paths) with `ServiceHealth` dataclass, classifier handling 200/503/4xx/non-JSON/connection-failure variants, `overall_status` reducer, and `to_json` for `--json` mode. Tests (19/19 green): `tests/test_config.py` 7 cases (env / `.env` / `--base-url` arg precedence, walk-up `.env` discovery, empty-token-as-None); `tests/test_health.py` 12 cases via `httpx.MockTransport` (all-ok, one-degraded-503, one-unreachable, all-unreachable, unknown-status-as-down, non-JSON-as-down, 4xx-as-down, URL-construction verification, `overall_status` reduction rules, JSON round-trip, parametric 200/503-body-shape regression). ruff clean (3 issues fixed during verify: 2 line-too-long wraps + empty TYPE_CHECKING block); mypy strict clean. New CI job `cli-test` mirrors the 5 backend templates; compose-validate CI job updated to also validate the new `cli` profile. **Phase 1 milestone:** with this skeleton all 6 components have runnable scaffolding. Caddy-mode-only at the skeleton level; tailscale-mode limitation (no URL rewrites for `/v1/health/<service>`) documented in README and `app/health.py` docstring as a future hardening item. |
| TASK-cli-source-commands | `vision source register / update / revoke / list / show` | P1 | Todo | [REQ-F-source-registration](../1-spec/requirements/REQ-F-source-registration.md), [REQ-F-consent-revocation](../1-spec/requirements/REQ-F-consent-revocation.md), [REQ-COMP-consent-record](../1-spec/requirements/REQ-COMP-consent-record.md) | TASK-source-registration-endpoint, TASK-source-update-endpoint, TASK-source-revoke-endpoint, TASK-source-history-endpoint | 2026-04-28 |  |
| TASK-cli-audit-commands | `vision audit query / verify-chain` | P1 | Todo | [REQ-SEC-audit-log](../1-spec/requirements/REQ-SEC-audit-log.md) | TASK-audit-query-endpoint, TASK-audit-verify-chain-endpoint | 2026-04-28 |  |
| TASK-cli-manual-input | `vision input <text>` invokes manual CLI adapter | P1 | Todo | [REQ-F-input-event-normalization](../1-spec/requirements/REQ-F-input-event-normalization.md) | TASK-whatsorga-manual-cli-adapter, TASK-cli-skeleton | 2026-04-28 |  |
| TASK-cli-rtbf | `vision rtbf <subject>` with poll-to-completion | P1 | Todo | [REQ-COMP-rtbf](../1-spec/requirements/REQ-COMP-rtbf.md) | TASK-rtbf-endpoints | 2026-04-28 |  |
| TASK-cli-export | `vision export <subject>` producing the bundle | P1 | Todo | [REQ-COMP-data-export](../1-spec/requirements/REQ-COMP-data-export.md) | TASK-data-export-endpoints | 2026-04-28 |  |
| TASK-cli-review-commands | `vision review list / inspect / dispose` (CLI fallback) | P1 | Todo | [REQ-F-review-queue](../1-spec/requirements/REQ-F-review-queue.md) | TASK-review-queue-endpoints | 2026-04-28 |  |
| TASK-cli-state-preview | `vision state preview --as-of` | P1 | Todo | [REQ-F-state-reconstruction](../1-spec/requirements/REQ-F-state-reconstruction.md) | TASK-state-reconstruction-endpoint | 2026-04-28 |  |
| TASK-cli-backup-restore | `vision backup` and `vision restore` | P2 | Todo | [REQ-REL-backup-restore-fidelity](../1-spec/requirements/REQ-REL-backup-restore-fidelity.md) | TASK-backup-script, TASK-restore-script | 2026-04-28 |  |
| TASK-cli-rotate | `vision rotate <secret-category>` | P2 | Todo | [REQ-REL-secret-rotation](../1-spec/requirements/REQ-REL-secret-rotation.md) | TASK-secret-rotation-runbook | 2026-04-28 |  |
| TASK-cli-reconciliation-run | `vision reconciliation run` | P1 | Todo | [REQ-REL-audit-reconciliation](../1-spec/requirements/REQ-REL-audit-reconciliation.md) | TASK-reconciliation-endpoints | 2026-04-28 |  |

### Deploy & Operations

| ID | Task | Priority | Status | Req | Dependencies | Updated | Notes |
|----|------|----------|--------|-----|--------------|---------|-------|
| TASK-install-vps-script | `install_vps.sh` — bring up Compose stack from clean clone | P1 | Done | [REQ-PORT-vps-deploy](../1-spec/requirements/REQ-PORT-vps-deploy.md) | TASK-compose-stack-skeleton, TASK-env-example-bootstrap | 2026-04-29 | New `scripts/install_vps.sh` (executable, ~280 lines, `set -euo pipefail`). 10-step flow with named exit codes (1=prereq missing, 2=drift, 3=health timeout): (1) verify `docker` + `docker compose version` (v2 required); (2) verify run-from-repo-root; (3) verify `.env` exists with cp-template remediation; (4) run `scripts/check-env-drift.sh`; (5) source `.env` and check 8 required-key values (`COMPOSE_PROFILES`, `POSTGRES_PASSWORD`, 6× tokens) are non-empty; (6) profile-specific `TS_AUTHKEY` check when tailscale profile active; (7) `docker compose pull`; (8) `docker compose build`; (9) `docker compose up -d`; (10) wait up to 5min for 7 expected containers to report healthy (postgres, ollama, 5 backend services); (11) invoke `scripts/ollama-pull.sh`; (12) print next-steps with `vision health` invocation. Idempotent — re-running is safe. ANSI color helpers no-op when stdout not a TTY. New CI job `scripts-lint` runs `bash -n` + `shellcheck` on every `scripts/*.sh` (5 existing + 1 new = 6 scripts; shellcheck preinstalled on ubuntu-latest). Per `REQ-PORT-vps-deploy`: no host-specific patches; default deployment makes zero remote inference calls per `CON-local-first-inference`. Smoke testing (`smoke_test.sh`) is `TASK-smoke-test-skeleton` (#16); install runbook is `TASK-phase-1-manual-testing` (#17). Local verification: `bash -n` clean on all 6 scripts; full integration verification deferred to manual VPS run in #17 (Docker not installed in dev shell). |
| TASK-smoke-test-skeleton | `smoke_test.sh` — healthchecks across all services | P1 | Done | [REQ-PORT-vps-deploy](../1-spec/requirements/REQ-PORT-vps-deploy.md) | TASK-install-vps-script | 2026-04-29 | New `scripts/smoke_test.sh` (executable, ~190 lines, `set -euo pipefail`). Phase-1 scope: **healthcheck-only** per Execution Plan capability "passing healthcheck-only smoke test"; the full functional flow per `REQ-PORT-vps-deploy` (synthetic ingest → routing → Kanban write → mid-band review → RTBF cascade) lands with `TASK-cross-provider-verification` in Phase 7. 4-step flow: (1) prerequisite verification (Docker, compose v2, repo root, `.env`); (2) profile gate — caddy-mode-only (tailscale-mode = documented deferred-hardening item; exits 5 = not-applicable rather than failing); (3) per-container Compose-health check across 7 expected containers (postgres, ollama, 5 backend services); (4) `vision health` aggregator via `docker compose --profile cli run --rm cli health`, mapping its 0/1/2 exit codes to this script's 0/3/4. Stable exit-code contract (0=ok, 1=prereq missing, 2=container unhealthy, 3=vision degraded, 4=vision down, 5=non-caddy not-applicable) so automation gating on this script does not change as Phase-7 extends it. `install_vps.sh` next-steps printout updated to point at the now-real script. Local: `bash -n` clean. shellcheck verification via the existing `scripts-lint` CI job. |
| TASK-backup-script | `backup.sh` producing host-independent archive | P2 | Todo | [REQ-REL-backup-restore-fidelity](../1-spec/requirements/REQ-REL-backup-restore-fidelity.md) | TASK-postgres-events-schema | 2026-04-28 | `pg_dump --format=directory` per `DEC-postgres-as-event-store` |
| TASK-restore-script | `restore.sh` with chain verification before resuming writes | P2 | Todo | [REQ-REL-backup-restore-fidelity](../1-spec/requirements/REQ-REL-backup-restore-fidelity.md) | TASK-backup-script, TASK-hash-chain-verify | 2026-04-28 |  |
| TASK-secret-rotation-runbook | Documented rotation procedure per secret category | P2 | Todo | [REQ-REL-secret-rotation](../1-spec/requirements/REQ-REL-secret-rotation.md) | TASK-bearer-auth-middleware | 2026-04-28 |  |
| TASK-cross-provider-verification | Run install + smoke test on ≥2 VPS providers; capture deltas as DECs | P2 | Todo | [REQ-PORT-vps-deploy](../1-spec/requirements/REQ-PORT-vps-deploy.md) | TASK-install-vps-script, TASK-smoke-test-skeleton | 2026-04-28 | Verifies `ASM-vps-docker-baseline-stable` |
| TASK-tailscale-health-aggregation | Make `vision health` work in tailscale-only mode | P2 | Todo | [REQ-PORT-vps-deploy](../1-spec/requirements/REQ-PORT-vps-deploy.md) | TASK-cross-provider-verification | 2026-04-29 | Closes MEDIUM 1 from the 2026-04-29 code review of `TASK-phase-1-manual-testing`. The cli compose service hardcodes `VISION_BASE_URL=http://ingress-caddy`, but `ingress-caddy` doesn't run in tailscale-only mode, AND `tailscale-serve.json` has no `/v1/health/<service>` routes (Tailscale serve has no URL-rewrite primitive). Three independent fix paths to choose during the task: (a) add per-service `/v1/health/<service>` aliases on each backend FastAPI app + expose them in `tailscale-serve.json`; (b) make the cli compose service's `VISION_BASE_URL` env-overridable so tailscale operators can point at the Tailnet hostname; (c) add a `--per-service` mode to `vision health` that bypasses Caddy aggregation. Pick a path during the task and document the decision. Until then, the documented workaround is enabling both ingress profiles (`COMPOSE_PROFILES=caddy,tailscale`) so Caddy provides the aggregation paths over the Tailnet. |
| TASK-perf-ingest-latency-tests | Synthetic monitoring + load test for p95 targets | P1 | Todo | [REQ-PERF-ingest-latency](../1-spec/requirements/REQ-PERF-ingest-latency.md) | TASK-input-event-endpoint, TASK-proposal-pipeline-endpoint | 2026-04-28 |  |
| TASK-perf-routing-throughput-tests | Sustained + burst throughput load test | P2 | Todo | [REQ-PERF-routing-throughput](../1-spec/requirements/REQ-PERF-routing-throughput.md) | TASK-routing-skill | 2026-04-28 |  |
| TASK-ci-caddyfile-validate | CI Caddyfile syntax validation job | P2 | Done | [REQ-MNT-env-driven-config](../1-spec/requirements/REQ-MNT-env-driven-config.md) | TASK-ingress-caddy-config | 2026-04-28 | New `caddyfile-validate` job in `.github/workflows/ci.yml` runs `caddy validate` against the mounted Caddyfile via the `caddy:2-alpine` image. Closes the deferred-hardening item from `TASK-ingress-caddy-config`'s "Pre-existing issues observed" notes. Surfaced and fixed a real Caddyfile bug on first green run (single-line `handle X { reverse_proxy Y }` is invalid — Caddy rejects "Unexpected next token after '{' on same line"; commit c617e95 expanded all 19 affected handlers to multi-line form). Negative-path verification: throwaway PR #1 (branch `ci-test/caddyfile-syntax-failure`) injected a deliberate unclosed brace; CI correctly failed `Caddyfile syntax check` (job 73421718057) at line 133 while the other three jobs passed; PR closed + branch deleted. Plan: `docs/plans/2026-04-28-caddyfile-ci-validation.md`. |
| TASK-phase-1-manual-testing | Install runbook + per-component README skeletons for Phase 1 | P1 | Done | - | TASK-install-vps-script, TASK-smoke-test-skeleton, TASK-cli-skeleton | 2026-04-29 | New `4-deploy/runbooks/install.md` (~280 lines) — canonical install runbook: prerequisites table, 5-step procedure (clone → `.env` → `install_vps.sh` → `smoke_test.sh` → CLI install), exit-code contracts for both scripts, 4 manual verification scenarios (all healthy / Postgres-stop 503-propagation / gbrain-bridge missing-vault visibility / CLI exit-code contract), tailscale-mode operator-verification path with the documented `vision health` aggregation gap, troubleshooting (4 common failures with diagnostics), rollback / clean teardown, GDPR-deferral gate per `DEC-gdpr-legal-review-deferred` (production deploy blocked until `ASM-derived-artifacts-gdpr-permissible` is Verified), pointers to all 7 future per-phase runbooks. Root `README.md` updated: status reflects Phase-1-near-complete + 106 tasks (was outdated "execution begins" + 105); new "Install" section with the 4-command quickstart pointing at the runbook; tech-stack conventions section now lists both DECs (backend-stack + cli-stack) instead of "deferred". Per-component READMEs spot-checked: all 5 backend READMEs share identical section structure (Tech stack / Layout / Local development / Container build & run / Tests in CI); cli's slightly different shape (Distribution / Modes / Exit codes) is appropriate for a CLI. **Phase 1 complete.** |
| TASK-phase-2-manual-testing | Consent + audit runbook; component READMEs updated for Phase 2 | P1 | Todo | - | TASK-cli-source-commands, TASK-cli-audit-commands | 2026-04-28 |  |
| TASK-phase-3-manual-testing | End-to-end ingest runbook + READMEs for Phase 3 | P1 | Todo | - | TASK-cli-manual-input, TASK-hermes-events-consumer | 2026-04-28 |  |
| TASK-phase-4-manual-testing | Privacy runbook (RTBF, export, retention) + READMEs for Phase 4 | P1 | Todo | - | TASK-cli-rtbf, TASK-cli-export, TASK-retention-sweep-endpoint | 2026-04-28 |  |
| TASK-phase-5-manual-testing | Agent + GBrain + Kanban runbook + READMEs for Phase 5 | P1 | Todo | - | TASK-routing-skill, TASK-extraction-skill, TASK-gbrain-page-crud, TASK-kanban-card-crud | 2026-04-28 |  |
| TASK-phase-6-manual-testing | Supervision-loop runbook + READMEs for Phase 6 | P1 | Todo | - | TASK-learning-loop-skill, TASK-cli-review-commands, TASK-cli-state-preview | 2026-04-28 |  |
| TASK-phase-7-manual-testing | Operability runbook (multi-channel + backup + rotate + cross-provider) + final READMEs | P1 | Todo | - | TASK-whatsapp-adapter, TASK-cli-backup-restore, TASK-cli-rotate, TASK-cross-provider-verification, TASK-perf-ingest-latency-tests, TASK-vault-audit-sweep-endpoint | 2026-04-28 |  |

---

## Execution Plan

Defines the order in which tasks should be executed. Tasks are grouped into phases; complete all tasks in a phase before moving to the next. Within a phase, execute tasks in the listed order. Each phase ends with a deployable or testable system.

### Phase 1: Bootstrap & Deployment Foundation

**Capabilities delivered:**
- Fresh-VPS install completes from clean clone to passing healthcheck-only smoke test (`GOAL-E` partial — `REQ-PORT-vps-deploy`).
- All 6 services come up via `docker-compose up`; `vision health` aggregates status.
- Caddy or Tailscale ingress switchable via `.env` flag (`REQ-MNT-env-driven-config`).
- Default deployment makes 0 remote inference calls (`GOAL-E` zero-remote default).

**Tasks:**
1. TASK-monorepo-skeleton
2. TASK-compose-stack-skeleton
3. TASK-env-example-bootstrap
4. TASK-postgres-bootstrap
5. TASK-ollama-bootstrap
6. TASK-ingress-caddy-config
7. TASK-ingress-tailscale-config
8. TASK-ci-caddyfile-validate
9. TASK-whatsorga-skeleton
10. TASK-hermes-skeleton
11. TASK-backlog-core-skeleton
12. TASK-gbrain-bridge-skeleton
13. TASK-kanban-sync-skeleton
14. TASK-cli-skeleton
15. TASK-install-vps-script
16. TASK-smoke-test-skeleton
17. TASK-phase-1-manual-testing

### Phase 2: Consent Foundation + Audit Backbone

**Capabilities delivered:**
- Operator can register, update, revoke source consents (`GOAL-A` consent enforcement).
- Consent state queryable read-as-of any timestamp (`REQ-COMP-consent-record`).
- Hash-chained audit log functions; chain verification works end-to-end (`REQ-SEC-audit-log`).
- Service-to-service auth + bearer-token middleware operational.

**Tasks:**
1. TASK-canonical-json-helper
2. TASK-bearer-auth-middleware
3. TASK-postgres-events-schema
4. TASK-postgres-consent-schema
5. TASK-postgres-events-partitioning
6. TASK-event-emit-primitive
7. TASK-hash-chain-verify
8. TASK-source-registration-endpoint
9. TASK-source-update-endpoint
10. TASK-source-revoke-endpoint
11. TASK-source-history-endpoint
12. TASK-audit-query-endpoint
13. TASK-audit-verify-chain-endpoint
14. TASK-cli-source-commands
15. TASK-cli-audit-commands
16. TASK-phase-2-manual-testing

### Phase 3: Minimum End-to-End Pipeline

**Capabilities delivered:**
- Manual CLI input flows through normalization to `backlog-core` (`GOAL-B` partial — `REQ-F-input-event-normalization`).
- Consent check enforces at the ingest boundary; revoked-source events dropped with reason logged.
- Proposal pipeline accepts proposals; idempotency middleware operational (`REQ-F-proposal-pipeline`).
- `hermes-runtime` consumes events via `GET /v1/events/stream`.

**Tasks:**
1. TASK-idempotency-middleware
2. TASK-purpose-limitation-middleware
3. TASK-whatsorga-normalization
4. TASK-whatsorga-manual-cli-adapter
5. TASK-whatsorga-consent-check
6. TASK-input-event-endpoint
7. TASK-proposal-pipeline-endpoint
8. TASK-proposal-detail-endpoint
9. TASK-events-stream-endpoint
10. TASK-hermes-events-consumer
11. TASK-cli-manual-input
12. TASK-phase-3-manual-testing

### Phase 4: Privacy Compliance

**Capabilities delivered:**
- Retention sweep deletes `raw_30d` artifacts at age 30 days (`REQ-F-retention-sweep`).
- RTBF cascade across all storage layers within 24h with verification (`REQ-COMP-rtbf` — full `GOAL-A` privacy floor).
- Data subject export bundle producible (`REQ-COMP-data-export`).
- Subject reference normalization works; `subject_index` matview supports per-subject queries.

**Tasks:**
1. TASK-subject-ref-normalization
2. TASK-subject-index-matview
3. TASK-retention-sweep-service
4. TASK-retention-sweep-endpoint
5. TASK-rtbf-cascade-engine
6. TASK-rtbf-endpoints
7. TASK-data-export-tool
8. TASK-data-export-endpoints
9. TASK-gbrain-cascade-endpoint
10. TASK-kanban-cascade-endpoint
11. TASK-cli-rtbf
12. TASK-cli-export
13. TASK-phase-4-manual-testing

### Phase 5: Agent Foundation + GBrain + Kanban Surface

**Capabilities delivered:**
- Confidence gate intercepts every action site (`GOAL-C` gate compliance — `REQ-F-confidence-gate`).
- Agent does basic project routing with cited GBrain pages (`REQ-F-project-routing`, `REQ-F-brain-first-lookup`).
- GBrain pages can be created/read/updated/deleted with schema validation, bidirectional links, redaction precondition (`GOAL-D` foundations).
- Kanban cards created/updated through proposal pipeline; sync-vs-edit boundary detects manual changes (`REQ-USA-kanban-obsidian-fidelity`).
- Artifact extraction produces typed candidates from autonomous-band events (`REQ-F-artifact-extraction`).
- Duplicate detection runs after routing (`REQ-F-duplicate-detection`).

**Tasks:**
1. TASK-confidence-gate-middleware
2. TASK-routing-skill
3. TASK-brain-first-lookup
4. TASK-extraction-skill
5. TASK-duplicate-detection-skill
6. TASK-model-router
7. TASK-gbrain-page-schema-validator
8. TASK-gbrain-page-crud
9. TASK-gbrain-bidirectional-links
10. TASK-gbrain-redaction-precondition
11. TASK-kanban-card-crud
12. TASK-kanban-sync-vs-edit
13. TASK-kanban-column-move-detection
14. TASK-kanban-sync-trigger
15. TASK-phase-5-manual-testing

### Phase 6: Supervision & Learning Loop

**Capabilities delivered:**
- Review queue routes mid-band / ambiguous-consent / classifier-review-required input to operator (`REQ-F-review-queue`).
- Obsidian command-palette dispositions translate to `backlog-core` via watch script (per `DEC-obsidian-as-review-ui`).
- Proposal disposition emits `learning_event` automatically (`REQ-F-correction-actions`).
- Within-session learning loop: corrections reflect in next proposals on same scope (`REQ-F-learning-loop`).
- Decision inspection surfaces full proposal context including suppression reasons (`REQ-F-decision-inspection`).
- State reconstruction works in preview mode (`REQ-F-state-reconstruction`).

**Tasks:**
1. TASK-review-queue-endpoints
2. TASK-proposal-disposition-endpoint
3. TASK-learning-event-emit
4. TASK-state-reconstruction-service
5. TASK-state-reconstruction-endpoint
6. TASK-review-queue-page-format
7. TASK-proposal-detail-page-format
8. TASK-obsidian-watch-script
9. TASK-disposition-hook-endpoint
10. TASK-obsidian-bindings-bundle
11. TASK-learning-loop-skill
12. TASK-cli-review-commands
13. TASK-cli-state-preview
14. TASK-phase-6-manual-testing

### Phase 7: Multi-Channel & Operability

**Capabilities delivered:**
- All four MVP channels operational: WhatsApp, voice, repo events (manual already done in Phase 3) (`GOAL-B` complete).
- Daily reconciliation report identifies gate bypasses (`REQ-REL-audit-reconciliation`).
- Weekly vault audit sweep verifies vault integrity (`REQ-MNT-vault-audit-sweep`).
- Backup → restore round-trip preserves state bit-identically (`REQ-REL-backup-restore-fidelity`).
- Secret rotation preserves project state with no stale credentials (`REQ-REL-secret-rotation`).
- Cross-provider VPS verification on ≥2 providers (`REQ-PORT-vps-deploy` complete).
- Performance load tests confirm `REQ-PERF-ingest-latency` and `REQ-PERF-routing-throughput` targets.
- Remote-inference profile (opt-in, `.env`-gated) audited end-to-end (`REQ-SEC-remote-inference-audit` complete).
- Event replay correctness fully validated (`REQ-REL-event-replay-correctness`).

**Tasks:**
1. TASK-whatsapp-adapter
2. TASK-voice-adapter
3. TASK-repo-events-adapter
4. TASK-daily-reconciliation-job
5. TASK-reconciliation-endpoints
6. TASK-event-replay-correctness-tests
7. TASK-vault-audit-sweep
8. TASK-vault-audit-sweep-endpoint
9. TASK-backup-script
10. TASK-restore-script
11. TASK-cli-backup-restore
12. TASK-secret-rotation-runbook
13. TASK-cli-rotate
14. TASK-cross-provider-verification
15. TASK-tailscale-health-aggregation
16. TASK-perf-ingest-latency-tests
17. TASK-perf-routing-throughput-tests
18. TASK-remote-inference-profile
19. TASK-cli-reconciliation-run
20. TASK-phase-7-manual-testing
