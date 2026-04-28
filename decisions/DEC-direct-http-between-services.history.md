# DEC-direct-http-between-services: Trail

> Companion to `DEC-direct-http-between-services.md`.

## Alternatives considered

### Option A: Synchronous HTTP/REST (chosen)
- Pros: Simplest possible deployment; one less component to operate; failure modes are obvious (request timeout, error code); operator can curl any endpoint to debug.
- Cons: Synchronous coupling means a slow downstream service slows the upstream chain; recovery from a hung service requires explicit timeouts; no built-in retry semantics across service boundaries.

### Option B: Message bus (NATS / Redis pub/sub)
- Pros: Decouples timing — upstream returns fast, downstream processes when available; built-in retry and dead-letter queues; familiar pattern for event-driven flows.
- Cons: Extra infrastructure to deploy and operate (a bus service); ordering guarantees and exactly-once semantics add operational complexity; debugging requires correlating events across systems.

### Option C: Postgres LISTEN/NOTIFY for events, HTTP for synchronous calls
- Pros: No new infrastructure (Postgres is already deployed for `backlog-core`); event-driven decoupling where it helps.
- Cons: LISTEN/NOTIFY is per-connection; implementing the listener pattern across services requires careful connection management; less mature operationally than a dedicated bus.

## Reasoning

Option A was chosen because the system's call patterns at MVP scale are fundamentally synchronous (operator submits a proposal → expects accepted/rejected response; agent emits a proposal → wants the resulting card id back). The handful of inherently event-shaped flows (e.g., "kanban updates after a proposal commits") can be implemented as a synchronous chain at MVP without measurable user-visible latency cost. Operating a bus is significant overhead relative to the size of the team (Ben as sole operator) and exceeds the benefit at MVP volume.

Option C remains available as a fast-follow if a specific flow becomes problematic — it requires no new infrastructure, just code.

Accepted trade-off: a slow downstream service slows the upstream chain. Mitigation: timeouts + the `processing.stuck` alert mechanism per `REQ-PERF-ingest-latency` catch hung paths quickly.

## Human involvement

**Type**: ai-proposed/human-approved

**Notes**: Proposed during the architecture-design session (2026-04-27); user approved the architecture proposal which embedded this choice.

## Changelog

| Date | Change | Involvement |
|------|--------|-------------|
| 2026-04-27 | Initial decision recorded as part of architecture.md drafting | ai-proposed/human-approved |
