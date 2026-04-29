# DEC-cursor-pagination-and-event-stream-conventions: Trail

> Companion to `DEC-cursor-pagination-and-event-stream-conventions.md`.
> AI agents read this only when evaluating whether the decision is still
> valid or when proposing a change or supersession.

## Alternatives considered

### Option A: Cursor pagination + long-poll/SSE event stream (chosen)

- **Pros**:
  - Cursor pagination tolerates the event-sourced backend's retention sweeps and partition rewrites without breaking client pagination state mid-session.
  - Opaque cursors hide server-side encoding choices, allowing migration without client changes.
  - Long-poll/SSE rides on plain HTTP — no extra protocol, no extra runtime, no extra ops surface vs. WebSocket / gRPC streaming.
  - Aligns with `DEC-direct-http-between-services` — same transport, same auth, same idempotency story.
  - Matches Phase-7 `REQ-PERF-routing-throughput` — `hermes-runtime` consumes events with sub-second latency on a healthy stream while idle bandwidth is dominated by the 30 s heartbeat.
- **Cons**:
  - Cursor format is opaque, so debugging "where am I in the stream?" requires server-side decoding tools (mitigated by structured server logs that emit `decoded_cursor: {seq_id, event_id}` on each list-query handler).
  - SSE clients in Python require a library that handles the chunked transfer / heartbeat semantics correctly. `httpx` covers SSE; `hermes-runtime`'s consumer can be written without extra deps.
  - Total-count is unavailable to UI surfaces. Acceptable for the MVP since the only UI is Obsidian + CLI; both render lists without count headers.

### Option B: Offset/limit pagination + WebSocket event stream

- **Pros**:
  - Offset/limit is the most familiar pagination idiom; UI frameworks have built-in support for "page 3 of 47" displays.
  - WebSockets give bidirectional streaming with mature Python libraries.
- **Cons**:
  - **Offset/limit breaks deterministically under retention sweep:** when partition N is dropped between page requests, all rows in pages > N shift up, and client pagination state silently re-displays earlier rows or skips rows. Showstopper given the daily retention sweep on `raw_30d` artifacts.
  - WebSocket is bidirectional, but the events stream is one-way (server → client). The bidirectional capability is dead weight.
  - WebSocket needs sticky-session routing through Caddy / Tailscale ingress — adds ingress config complexity and breaks horizontal scaling additivity (irrelevant per `ASM-no-scalability-target`, but the dead complexity remains).
  - Auth on WebSocket is non-trivial (the bearer token needs to flow on the upgrade request); HTTP/SSE auth is just the same `Authorization: Bearer` header that the rest of the API uses per `DEC-service-auth-bearer-tokens`.

### Option C: Page-number pagination + polling

- **Pros**:
  - Simplest possible client implementation; literally "issue request, parse response, sleep, repeat".
- **Cons**:
  - Same retention-sweep pathology as offset/limit, but worse: page numbers visibly disagree with reality after every sweep.
  - Polling adds end-of-event latency proportional to the polling interval (3-30 s typical), which would force `REQ-PERF-ingest-latency`'s autonomous-path < 5 min target to absorb extra seconds at every event-bus hop. Marginal but cumulative.
  - Doubles dead bandwidth on idle hours (an empty poll every 3 s is 28k requests/day per consumer).

### Option D: Message broker (Redis Streams / NATS / RabbitMQ) for event consumption

- **Pros**:
  - Industry-standard pattern for event-driven backends; rich ecosystem.
  - Decouples publisher from subscriber clock, allowing burst tolerance via the broker buffer.
- **Cons**:
  - Adds a new component to the Compose stack — extra ops surface, extra healthcheck, extra backup/restore story (e.g., Redis `BGSAVE` snapshots), extra failure mode.
  - Conflicts with `DEC-direct-http-between-services` at the MVP scope. Adopting it would supersede that decision and propagate ripple changes through every service-to-service call site.
  - The throughput justification doesn't hold at MVP scale: `hermes-runtime` is the only consumer, and a single SSE connection is sufficient. The broker is solving a problem we don't have.

## Reasoning

This decision crystallizes conventions that were already documented in `api-design.md` § Pagination and § Stream endpoint at Spec/Design phase close — completeness assessment 2026-04-27 (M-5) flagged that they had no formal decision record. The decision content reflects the conventions as written, so this is a documentation-tightening decision rather than a fresh technical choice. The alternative analysis was implicit in the Design phase but not preserved; recording it here closes the audit trail.

Trade-offs explicitly accepted:

- **Total-count fields are forbidden** in list responses. UI surfaces that need approximate counts must derive them from `backlog-core`'s metrics rather than from list endpoints.
- **Bidirectional streaming is forbidden** at MVP. If future tasks need it (e.g., a real-time collaboration surface), they must supersede this decision rather than introducing a side-channel.
- **The 5-minute connection cap on `events/stream` forces clients to handle reconnect-with-resume.** This is preferable to indefinite long-poll connections that hide resource leaks; clients that ignore the cap will simply see periodic 5-minute reconnect cycles, which is the documented behavior.

Conditions that would invalidate this reasoning:

- Adding a UI surface (e.g., a web dashboard) that genuinely needs total-count fields. At that point, we'd add a separate `/v1/.../count` endpoint rather than overloading the list response.
- Performance load tests (`TASK-perf-ingest-latency-tests`, Phase 7) showing that long-poll/SSE imposes per-connection overhead beyond what the reference VPS can sustain at the documented user count. Mitigation paths in increasing severity: tune heartbeat / connection-cap parameters; offload to a dedicated event-streaming process; supersede with broker-based consumption.
- A second consumer of `events/stream` joining `hermes-runtime`. At that point, the single-consumer assumption baked into `backlog-core`'s implementation may not hold; the convention itself stays valid but implementation may need to fan-out events.

## Human involvement

**Type**: ai-proposed/human-approved

**Notes**: AI proposed this decision after the user requested closure of completeness-assessment gap M-5 in a single sweep alongside the M-4 traceability fix and the `ASM-no-scalability-target` recording. The user explicitly stated Vincent's concurrence had already been secured for the spec / design tightening package. Approved on 2026-04-29.

## Changelog

| Date | Change | Involvement |
|------|--------|-------------|
| 2026-04-29 | Initial decision — formalizes pagination + event-stream conventions previously documented in `api-design.md` only as prose | ai-proposed/human-approved |
