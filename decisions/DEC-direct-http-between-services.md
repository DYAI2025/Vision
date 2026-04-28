# DEC-direct-http-between-services: Synchronous HTTP/REST between services at MVP

**Status**: Active

**Category**: Architecture

**Scope**: system-wide (inter-service communication)

**Source**: [GOAL-multi-source-project-ingestion](../1-spec/goals/GOAL-multi-source-project-ingestion.md), [REQ-PERF-ingest-latency](../1-spec/requirements/REQ-PERF-ingest-latency.md)

**Last updated**: 2026-04-27

## Context

The system has five services that must communicate (`whatsorga-ingest`, `hermes-runtime`, `backlog-core`, `gbrain-bridge`, `kanban-sync`). Communication options:

- Direct synchronous HTTP/REST.
- Asynchronous message bus (NATS, Redis pub/sub, RabbitMQ).
- Event-sourced fan-out via Postgres `LISTEN/NOTIFY`.
- Hybrid (HTTP for synchronous, bus for events).

The choice affects deployment complexity, operational surface, latency characteristics, and failure modes.

## Decision

At MVP, all inter-service communication is **synchronous HTTP/REST**. No message bus is deployed. If event-driven coupling becomes necessary later, Postgres `LISTEN/NOTIFY` is the next-step option without adding new infrastructure.

Specific application:

- `whatsorga-ingest` → `backlog-core` over HTTP for input event submission.
- `hermes-runtime` → `backlog-core` / `gbrain-bridge` / `kanban-sync` over HTTP for proposal-pipeline calls.
- `hermes-runtime` ↔ `Ollama` over HTTP for inference.
- All services accept HTTP from CLI / operator surfaces routed through Caddy or Tailscale.

## Enforcement

### Trigger conditions

- **Design phase**: any new inter-service flow proposed must use HTTP/REST unless a `DEC-*` supersession is recorded.
- **Code phase**: all service-to-service calls implemented as HTTP clients/servers; no direct database access from one service into another's database.

### Required patterns

- Service boundaries enforce auth tokens scoped per service (defense-in-depth for `CON-no-direct-agent-writes`).
- HTTP clients implement timeout + retry-with-jitter for transient failures; a hung downstream produces a `processing.stuck` alert per `REQ-PERF-ingest-latency`'s tail constraint.
- Responses include structured error codes downstream callers can act on (vs. opaque 5xx).

### Required checks

1. Before merging a new inter-service interaction, confirm the call uses the documented HTTP API and not a "shortcut" path.
2. Tail-latency monitoring per `REQ-PERF-ingest-latency` validates that the synchronous design is meeting targets.

### Prohibited patterns

- Direct service-to-database access across service boundaries (e.g., `hermes-runtime` reading Postgres directly without going through `backlog-core`'s API).
- Adding a message bus or queueing system without first recording a supersession of this decision.
- Inter-service calls that hold open connections beyond a bounded timeout — the synchronous design assumes calls return quickly or fail fast.

## Reconsider trigger

Revisit this decision if:

- Any persistent flow's measured p95 latency exceeds the `REQ-PERF-ingest-latency` targets despite tuning.
- A new flow is event-driven by nature (e.g., periodic cross-service sync) and would be cleaner with publish/subscribe.
- The system grows to enough services that point-to-point HTTP becomes a maintenance burden (>~10 services).
