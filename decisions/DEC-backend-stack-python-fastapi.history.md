# DEC-backend-stack-python-fastapi: Trail

> Companion to `DEC-backend-stack-python-fastapi.md`.
> AI agents read this only when evaluating whether the decision is still
> valid or when proposing a change or supersession.

## Alternatives considered

### Option A: Python 3.12 + FastAPI uniformly (chosen)

- **Pros**:
  - Native fit for Ollama (Python client mature), Whisper / voice transcription, GBrain markdown handling, and Pydantic-based `input_event` validation.
  - FastAPI's automatic OpenAPI generation gives `2-design/api-design.md` ↔ implementation traceability cheaply.
  - `uv` is fast enough that lockfile churn and CI install times are not bottlenecks.
  - Only one runtime / linter / type checker / test runner to learn and operate.
  - Cross-cutting utilities (canonical-JSON, bearer-auth, idempotency, purpose-limitation, subject-ref normalization) implemented once.
- **Cons**:
  - Python is single-process-async-bound — `backlog-core`'s eventual hot path (event ingest under load) may need vertical scaling or a small Go rewrite if `REQ-PERF-ingest-latency` p95 targets bind. Acceptable for MVP; revisit when load tests run (Phase 7).
  - mypy strict mode adds friction for fast prototyping but is worth it for contract integrity.

### Option B: Node.js + TypeScript (FastAPI ↔ Express/Fastify)

- **Pros**:
  - WhatsApp library ecosystem (`whatsapp-web.js`, `Baileys`) is arguably stronger than Python's.
  - Single-binary distribution via `bun build` / `pkg`.
- **Cons**:
  - Whisper / voice transcription, Ollama, GBrain markdown processing all weaker in Node ecosystem — would need shelling out or partial Python anyway.
  - Doubles the language burden if `backlog-core` stays Python.
  - WhatsApp libraries that look strong in Node are precisely the ones flagged by `DEC-platform-bypass-review-checklist` — they assume reverse-engineered web sessions, which is exactly what the platform-bypass constraint forbids unless review-checklist-clean.

### Option C: Go for `backlog-core` only + Python elsewhere

- **Pros**:
  - Stronger latency / throughput characteristics for the event store hot path; native HTTP/2; static binary.
- **Cons**:
  - Cross-cutting utilities have to be implemented in both Go and Python — 2× implementation, 2× test surface, divergence risk.
  - Adds a second language to the operator's mental model.
  - Performance gains are speculative until load tests bind (Phase 7); premature optimization.

### Option D: Rust (Axum) for all backend services

- **Pros**:
  - Best runtime performance; strong type system; memory safety.
- **Cons**:
  - Highest cost in dev hours / iteration speed for a 2-person MVP team.
  - Ecosystem gaps for Whisper, Ollama, markdown handling.
  - Not justified by current performance requirements.

## Reasoning

Two-person team + MVP delivery pace makes "minimize the cognitive surface" the dominant constraint. Python wins on three independent axes:

1. **Domain fit** — every external integration in the design (Ollama, Whisper, Obsidian markdown, Pydantic-shaped `input_event`s) is a first-class Python use case.
2. **Cross-cutting amortization** — five common utilities × five components = 25 implementations under mixed languages, vs. 5 implementations + 5 imports under uniform Python. The math doesn't favor mixing languages until performance forces it.
3. **Operator experience** — single language across services means one venv pattern, one lockfile format, one test runner, one lint config. Easier to keep coherent.

FastAPI is preferred over Flask / aiohttp / Starlette-direct because:
- Pydantic v2 integration is native (validation + serialization free).
- OpenAPI schemas come without extra wiring — pairs with `2-design/api-design.md`'s endpoint catalogue.
- Async-first matches the streaming / long-poll / SSE patterns in the events stream and Ollama integration.

Trade-offs explicitly accepted:
- We accept a possible future need to rewrite `backlog-core`'s ingest hot path in Go if `REQ-PERF-ingest-latency` p95 targets fail load testing in Phase 7. The replacement would supersede this decision in scope, not invalidate the decision for the other four services.
- We accept that `whatsapp-web.js`-class libraries are off the table — this is enforced by `DEC-platform-bypass-review-checklist`, not by language choice, so it's not a real loss.
- We accept mypy strict friction in exchange for catching `input_event` / `proposal` / `audit_event` shape bugs at lint time rather than runtime.

Conditions that would invalidate this reasoning:
- Performance load tests in Phase 7 show that `backlog-core` cannot meet `REQ-PERF-ingest-latency` under realistic burst load even with Python optimization (uvloop, asyncpg, CPython 3.12, batched commits). At that point, evaluate whether to (a) supersede this decision for `backlog-core` only with Go, or (b) accept a softer SLA.
- The team grows by 3+ engineers and a polyglot codebase becomes operationally cheap. Then per-component language choices become viable again.

## Human involvement

**Type**: ai-proposed/human-approved

**Notes**: AI proposed Python 3.12 + FastAPI as the uniform backend stack with full trade-off analysis when picking up `TASK-whatsorga-skeleton` (the first per-component skeleton). User approved with "go yes" on 2026-04-28, accepting all three sub-questions (uniform Python, CI test job included, defer cross-component utility location to `TASK-canonical-json-helper`). Vincent's concurrence is part of the same outstanding tiebreaker package noted in `CLAUDE.md` Spec → Design carry-overs.

## Changelog

| Date | Change | Involvement |
|------|--------|-------------|
| 2026-04-28 | Initial decision | ai-proposed/human-approved |
