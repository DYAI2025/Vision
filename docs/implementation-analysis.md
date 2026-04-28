# Implementation Analysis and Stabilization (2026-04-28)

## Scope

This analysis reviewed the executable code under `3-code/` with focus on:

- WhatsOrga ingest boundary and normalization path.
- GBrain integration path used by Hermes.
- LLM-driven semantic capture in Hermes.
- Architecture breaks that prevented a runnable end-to-end flow.

## Findings (before fixes)

1. **Critical runtime gaps:** `gbrain-bridge` and `kanban-sync` had no runnable code, Dockerfile, or dependency manifests.
   - Impact: `docker compose build` and full-stack startup would fail.
2. **Missing ingest path:** `whatsorga-ingest` had only `/v1/health` and no way to emit normalized `input_event`s.
3. **Missing intake endpoint in backlog-core:** no `/v1/inputs`, therefore no contract target for WhatsOrga.
4. **No callable Hermes processing endpoint:** no `/v1/agent/process-now`; Ollama client existed but not wired.
5. **No GBrain read path for semantic context:** Hermes had no mechanism to retrieve project memory snippets.

## Fixes introduced

1. **Backlog-Core API bridge added**
   - `POST /v1/inputs` with idempotency-key consistency check and optional token validation.
   - In-memory rolling event buffer for MVP integration (`/v1/inputs/recent`).
2. **WhatsOrga manual ingest adapter added**
   - `POST /v1/ingest/manual` normalizes payload into `input_event` and forwards to `backlog-core`.
   - Uses `Idempotency-Key = event_id` and service bearer token.
3. **Hermes process-now path added**
   - `POST /v1/agent/process-now` now:
     - loads contextual snippets from GBrain,
     - runs Ollama generate + embeddings,
     - computes a confidence proxy,
     - returns semantic summary, key points, and citations.
   - Includes deterministic fallback semantic parsing when LLM/context are unavailable.
4. **GBrain bridge service implemented**
   - Added runnable FastAPI component, Dockerfile, pyproject, tests.
   - Added `GET /v1/context/{project_id}` lexical relevance retrieval from vault markdown pages.
5. **Kanban-sync runnable skeleton added**
   - Added minimal service and build artifacts to remove compose build break.

## Remaining risks / next hardening steps

- Backlog-Core input persistence is currently memory-backed for integration unblocking; move to Postgres event table next.
- GBrain context matching is lexical, not embedding-based; add vector index to improve recall and semantic precision.
- Hermes confidence should eventually be calibrated against labeled operator outcomes, not embedding-length proxy.
- Service auth currently allows permissive mode when token env vars are unset; tighten for production profiles.

## Performance notes

- Current paths are lightweight and non-blocking (`httpx.AsyncClient`, bounded buffers, bounded limits).
- Main bottleneck remains LLM latency; current fallback path ensures endpoint continuity under model outages.
- Avoiding large vault scans per request should be addressed by indexing/caching in a follow-up task.
