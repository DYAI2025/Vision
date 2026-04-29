# DEC-cursor-pagination-and-event-stream-conventions: Cursor pagination + long-poll/SSE event streaming as cross-cutting API conventions

**Status**: Active

**Category**: Convention

**Scope**: backend (`backlog-core`, `gbrain-bridge`, `kanban-sync`; consumed by `hermes-runtime` and `cli`)

**Source**: [`REQ-USA-paginated-lists`](../1-spec/requirements/REQ-USA-paginated-lists.md), [`api-design.md`](../2-design/api-design.md) § Pagination + § Stream endpoint

**Last updated**: 2026-04-29

## Context

The MVP API surface includes ~10 list endpoints (`GET /v1/audit/query`, `GET /v1/sources`, `GET /v1/review/queue`, `GET /v1/sources/:id/history`, `GET /v1/reconciliation/runs`, etc.) and exactly one event-driven endpoint (`GET /v1/events/stream` consumed by `hermes-runtime`). `2-design/api-design.md` documented two cross-cutting conventions for these — opaque cursor tokens for lists, long-poll/SSE for the events stream — but the conventions had no formal decision record. Completeness assessment M-5 (2026-04-27) flagged this gap. This decision closes M-5 by capturing both conventions as enforceable rules.

Without a recorded decision, individual endpoint implementations could drift to offset/limit pagination, page-number pagination, or polling-based event consumption — each of which has known scaling pathologies on an event-sourced backend (offset jumps over deleted partitions; page-number breaks on retention sweep; polling adds dead bandwidth and end-of-event latency).

## Decision

All MVP API list and stream endpoints follow these two cross-cutting conventions:

### List endpoints — opaque cursor pagination

Every `GET /v1/...` endpoint that returns a collection accepts:

- `?after=<cursor>` — opaque token returned by a previous response; the server treats it as a black-box and clients never construct it.
- `?limit=<n>` — page size hint. **Default `50`, maximum `500`.** Servers MAY return fewer items if the requested page exceeds an internal cap.

The response body shape is:

```json
{
  "items": [...],
  "next_cursor": "..." | null
}
```

`next_cursor` is `null` when the page is the final one. Clients paginate by re-issuing the same query with `?after=<next_cursor>` until `null`.

### Event stream — long-poll / SSE

`GET /v1/events/stream` is the **only** push-style endpoint at MVP. Clients (`hermes-runtime` is the canonical caller) connect with `?last_event_id=<id>` and receive a stream of JSON events until the connection idles out. The transport is HTTP/1.1 chunked transfer or HTTP/2 server-sent events — the upstream contract is identical regardless of transport. The server MUST support graceful client reconnection from `last_event_id`.

No alternative push mechanism (WebSocket, gRPC streaming, message broker subscription) is permitted at MVP; per [`DEC-direct-http-between-services`](DEC-direct-http-between-services.md), HTTP is the only inter-service transport.

## Enforcement

### Trigger conditions

- **Design phase**: any new endpoint specification in `2-design/api-design.md` that returns a collection or a stream of events must conform to one of these two patterns.
- **Code phase**: any task that implements a list endpoint or the events stream — including all the `*-endpoint` tasks in Phase 2-7 (e.g., `TASK-audit-query-endpoint`, `TASK-events-stream-endpoint`, `TASK-review-queue-endpoints`, `TASK-source-history-endpoint`, `TASK-data-export-endpoints`, `TASK-reconciliation-endpoints`, `TASK-source-registration-endpoint` for its `GET /v1/sources` listing).

### Required patterns

**Cursor pagination — server side:**

- Cursor encodes the minimum state needed to resume the query deterministically against an immutable / append-only source. For the event log (`backlog-core`), a tuple of `(seq_id, event_id)` encoded base64-URL is sufficient.
- Cursor MUST be opaque to the client — clients never parse, compose, or mutate it. Servers MAY change the cursor encoding without a major-version bump as long as old cursors continue to work for a 1-hour window after a deploy (forward compatibility for in-flight pagination sessions).
- `next_cursor: null` is the only signal of end-of-page. Empty `items` with a non-null `next_cursor` is allowed (e.g., when retention sweep deleted a whole partition between pages) — clients keep paginating.

**Cursor pagination — client side:**

- The `vision` CLI's list commands (`vision audit query`, `vision source list`, etc.) must paginate to completion before printing the result, OR stream pages to stdout if the user passes a `--stream` flag — never truncate silently.
- The Obsidian command-palette watch script and `hermes-runtime`'s context-lookup paths consume only the first page; long lists are surfaced via the operator CLI, not via the agent or the review surface.

**Event stream:**

- Server emits one JSON event per line (`application/x-ndjson`) or one SSE `data:` block per event. The two encodings are interchangeable for the same event payload.
- Each event carries `event_id` (the audit-log primary key). Clients reconnect with the most recently received `event_id` as `?last_event_id=`.
- Idle timeout on the server is **30 seconds**: if no events are emitted in that window, the server sends a heartbeat (`event: heartbeat\ndata: {}` or an `ndjson` line with `{"type":"heartbeat","ts":"..."}`) so intermediaries don't drop the connection.
- Total connection lifetime cap is **5 minutes**: the server closes after 5 minutes regardless of activity. Clients reconnect with `?last_event_id=` within their existing event loop. This bounds resource holds on the server.

### Required checks

1. Any new list endpoint added to `2-design/api-design.md` must carry the `?after=<cursor>&limit=<n>` query-param signature in its endpoint specification line.
2. Any task implementing such an endpoint must reference `REQ-USA-paginated-lists` in its `Req` column in `3-code/tasks.md`. Direct list endpoints with no other Req link MUST link to `REQ-USA-paginated-lists` at minimum.
3. Component tests for list endpoints must cover (a) empty-list response (`items: []`, `next_cursor: null`), (b) full-page response with non-null `next_cursor`, (c) round-trip pagination terminates without infinite loop, (d) `limit > 500` is clamped to 500.
4. The `events/stream` implementation in `backlog-core` must be tested for (a) heartbeat emission within 30 s of idle, (b) graceful 5-minute connection cap with reconnect-resumable state, (c) `last_event_id` resumption across a deliberate disconnect.

### Prohibited patterns

- Offset/limit pagination (`?offset=N&limit=M`) — breaks under retention sweep.
- Page-number pagination (`?page=N&size=M`) — same problem, plus client-visible pagination state that becomes wrong on insertions.
- Total-count fields (`total_items`, `total_pages`) in list responses — encourages clients to render UI that doesn't degrade gracefully on large datasets and forces servers to do an extra count query per request.
- WebSocket, gRPC streaming, or message-broker subscriptions for event consumption at MVP. Adding any of these would supersede this decision and `DEC-direct-http-between-services` together.
- Polling `events/stream` instead of streaming it (e.g., re-issuing `GET /v1/events/stream` every N seconds without holding the long-poll open) — defeats the latency benefit; the long-poll IS the polling. If a future profile genuinely needs polling, add a separate `GET /v1/events?after=<cursor>&since=<ts>` endpoint that follows cursor-pagination semantics.
