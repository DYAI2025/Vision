# hermes-runtime

**Responsibility**: Hosts the agent (Ollama-backed Gemma-family model) and its skills (project routing, artifact extraction, **duplicate detection**, brain-first lookup, model routing), the **confidence-gate middleware**, and the **learning-loop** skill. Has read access to `backlog-core` and the GBrain vault but **no write credentials** for any system of record.

**Technology**: TBD per Code-phase decision (Python likely — LLM ergonomics, agent libraries, prompt-templating tooling). Recorded as a per-component `DEC-*` when the first implementation task is picked up.

## Interfaces

- **HTTP outbound** to `backlog-core`:
  - `POST /v1/proposals` to submit proposals through the proposal pipeline.
  - `GET /v1/events/stream` long-poll/SSE consumer for input-event notifications.
  - `GET /v1/audit/query` for context lookup (e.g., recent learnings).
  - `GET /v1/sources/:id/history?as_of=...` for read-as-of consent context.
- **HTTP outbound** to `gbrain-bridge`: `GET /v1/pages/:id` for brain-first lookup; `POST /v1/pages` (page-creation proposals through the proposal pipeline — `proposal_id` always set).
- **HTTP outbound** to `kanban-sync`: `GET /v1/boards/:project_id` for context; `POST/PATCH /v1/cards` (card mutations through the proposal pipeline).
- **HTTP outbound** to Ollama sidecar: `POST http://ollama:11434/api/generate` and `POST http://ollama:11434/api/embeddings`. Default-local; remote-inference profiles are `.env`-driven and audited.
- **HTTP inbound** (minimal): `GET /v1/health` and `POST /v1/agent/process-now` (operator-triggered).

## Requirements Addressed

| File | Type | Priority | Summary |
|------|------|----------|---------|
| [REQ-F-project-routing](../../1-spec/requirements/REQ-F-project-routing.md) | Functional | Must-have | Each input event scored against active projects with cited GBrain context |
| [REQ-F-artifact-extraction](../../1-spec/requirements/REQ-F-artifact-extraction.md) | Functional | Must-have | Typed artifacts (task / proposal / decision_candidate / risk / open_question) extracted from autonomous-band events |
| [REQ-F-duplicate-detection](../../1-spec/requirements/REQ-F-duplicate-detection.md) | Functional | Must-have | Semantic + lexical detector; FN ≤5%, FP ≤2%; emits `duplicate.detected` and `learning_event`s on operator splits |
| [REQ-F-confidence-gate](../../1-spec/requirements/REQ-F-confidence-gate.md) | Functional | Must-have | Three-band gate intercepts every action; thresholds configurable per project |
| [REQ-F-learning-loop](../../1-spec/requirements/REQ-F-learning-loop.md) | Functional | Must-have | Eager within-session loop: refresh prompt context + project profile + routing rules |
| [REQ-F-brain-first-lookup](../../1-spec/requirements/REQ-F-brain-first-lookup.md) | Functional | Must-have | Routing/extraction queries GBrain pre-scoring; ≥95% citation rate on qualifying scopes |
| [REQ-F-decision-inspection](../../1-spec/requirements/REQ-F-decision-inspection.md) | Functional | Must-have | Detail view per proposal — fed by data this component produces (gate inputs, citations, learnings applied) |
| [REQ-SEC-remote-inference-audit](../../1-spec/requirements/REQ-SEC-remote-inference-audit.md) | Security | Must-have | Remote inference calls pre-gated by profile + caller + data class + consent scope; full audit entry per call |
| [REQ-PERF-routing-throughput](../../1-spec/requirements/REQ-PERF-routing-throughput.md) | Performance | Should-have | ≥10 events/min sustained; ≥30 events/min for 2-min burst on reference VPS |

## Relevant Decisions

| File | Title | Trigger |
|------|-------|---------|
| [DEC-confidence-gate-as-middleware](../../decisions/DEC-confidence-gate-as-middleware.md) | Gate middleware inside `hermes-runtime`, not a separate service | Any agent-action site implementation |
| [DEC-direct-http-between-services](../../decisions/DEC-direct-http-between-services.md) | Synchronous HTTP/REST between services at MVP | Inter-service call patterns |
| [DEC-api-versioning](../../decisions/DEC-api-versioning.md) | URL-path versioning (`/v1/...`) | Endpoint construction on every outbound call |
| [DEC-service-auth-bearer-tokens](../../decisions/DEC-service-auth-bearer-tokens.md) | Per-service bearer tokens with declared purposes | Authentication on every outbound call |
| [DEC-idempotency-keys](../../decisions/DEC-idempotency-keys.md) | `Idempotency-Key` header on mutations | `proposal_id` is the natural key on proposal-pipeline calls |
| [DEC-stakeholder-tiebreaker-consensus](../../decisions/DEC-stakeholder-tiebreaker-consensus.md) | Peer-stakeholder conflicts resolved by consensus | When Vincent and Ben disagree on agent-behavior changes (auto-policy, threshold tuning, prompt tweaks) |
