# REQ-USA-paginated-lists: All list endpoints use opaque cursor pagination; the events stream uses long-poll/SSE

**Type**: Usability

**Status**: Approved

**Priority**: Should-have

**Source**: [GOAL-multi-source-project-ingestion](../goals/GOAL-multi-source-project-ingestion.md), [GOAL-trustworthy-supervised-agent](../goals/GOAL-trustworthy-supervised-agent.md), [`api-design.md`](../../2-design/api-design.md) § Pagination + § Stream endpoint

**Source stakeholder**: [STK-ben](../stakeholders.md)

## Description

Every API endpoint that returns a collection (`GET /v1/...` listing endpoints) and the single event-driven endpoint (`GET /v1/events/stream`) follow consistent, scale-tolerant interaction patterns so operator and agent consumers can navigate large result sets without information loss.

**List endpoints** accept `?after=<cursor>&limit=<n>` query parameters. Cursors are server-issued opaque tokens; clients never construct or parse them. Default `limit` is 50, max 500; servers MAY return fewer items if the requested page exceeds an internal cap. Response body shape is `{"items": [...], "next_cursor": "..." | null}` — `next_cursor: null` is the only end-of-page signal.

**The events stream** at `GET /v1/events/stream` is a long-poll / server-sent-events endpoint. Clients reconnect using the most recently received `event_id` as `?last_event_id=`. Server emits a heartbeat on 30 s of idle so intermediaries don't drop the connection; the connection itself is capped at 5 minutes after which the client must reconnect with `?last_event_id=`.

These conventions are formally specified in [`DEC-cursor-pagination-and-event-stream-conventions`](../../decisions/DEC-cursor-pagination-and-event-stream-conventions.md) — that decision is the enforceable rule; this requirement is the testable obligation.

## Acceptance Criteria

- Given any `GET /v1/...` endpoint that returns a collection, when invoked without `?limit`, then the response contains at most 50 items and `next_cursor` is either a non-empty string (page non-final) or `null` (page final).
- Given a request with `?limit=600`, when the endpoint executes, then the response contains at most 500 items (clamping enforced server-side).
- Given pagination round-trip (`?after=<cursor>` re-issued until `next_cursor: null`), when the listing source is stable across the round-trip, then no items are returned twice and no items are skipped.
- Given pagination round-trip across a retention-sweep tick (a partition is dropped between page N and page N+1), when the round-trip resumes, then `items` may legitimately be empty in some pages but the round-trip terminates without infinite loop and without the client observing a half-deleted state.
- Given `GET /v1/events/stream` with no `?last_event_id`, when the client connects, then it receives only events emitted after connection time. Given `?last_event_id=<id>` from a previous session, when the client reconnects, then it receives every event with `event_id > id` plus any heartbeats. No events between `id` and reconnect are silently dropped.
- Given an idle period of ≥30 s on `events/stream`, when no real events are emitted, then the server emits a heartbeat (newline-delimited JSON `{"type":"heartbeat","ts":"..."}` or SSE `event: heartbeat\ndata: {}`).
- Given a connection that has been open for 5 minutes, when the cap fires, then the server closes the connection cleanly and the client can reconnect with `?last_event_id=` to resume without missing events.
- Given component tests for any new list endpoint, when the test suite runs, then all four cursor-pagination cases are exercised: empty-list, full page with non-null cursor, round-trip terminates, `?limit > 500` clamping.
- Given the operator running `vision audit query` (or any other CLI list command), when the result set has ≥51 items, then the CLI either paginates to completion before printing OR streams pages to stdout under `--stream`, never silently truncating.

## Related Constraints

- [CON-vps-portable-deployment](../constraints/CON-vps-portable-deployment.md) — cursor pagination + SSE work on plain HTTP, no special ingress configuration.

## Related Assumptions

- [ASM-no-scalability-target](../assumptions/ASM-no-scalability-target.md) — single-consumer assumption on `events/stream` is part of the scope choice; if invalidated by a second consumer, fan-out semantics in `backlog-core` may need revision while this requirement's contract stays intact.
