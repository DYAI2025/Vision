# DEC-confidence-gate-as-middleware: Confidence gate is middleware inside `hermes-runtime`, not a separate service

**Status**: Active

**Category**: Architecture

**Scope**: backend (`hermes-runtime` + persistence services)

**Source**: [REQ-F-confidence-gate](../1-spec/requirements/REQ-F-confidence-gate.md), [CON-confidence-gated-autonomy](../1-spec/constraints/CON-confidence-gated-autonomy.md), [CON-no-direct-agent-writes](../1-spec/constraints/CON-no-direct-agent-writes.md)

**Last updated**: 2026-04-27

## Context

The confidence gate is required by `REQ-F-confidence-gate` to intercept every action site (route, extract, propose-write, side-effect tool call). It can be implemented as:

- Middleware inside `hermes-runtime` (callable function) — agent-side enforcement.
- A separate gate service that all action sites call through HTTP — network-mediated enforcement.
- A library shared between `hermes-runtime` and persistence services.

The choice affects defense-in-depth, latency, and operational complexity.

## Decision

The gate is **middleware inside `hermes-runtime`**, not a separate service. Defense-in-depth is achieved by **also enforcing service-to-service auth and per-component declared purposes at the persistence-service boundary** (per `REQ-COMP-purpose-limitation`), so that a compromised `hermes-runtime` cannot bypass the gate by calling tools directly with crafted payloads — the persistence services reject unrecognized callers and out-of-scope purposes.

Shape:

- The gate is a callable that every agent-action site invokes before tool dispatch; bypass is detected by `REQ-REL-audit-reconciliation` (gate-decision absent on audit chain → alert).
- Persistence services check service-to-service auth tokens, declared component purposes, and source `consent_scope` at every accepted call.
- Both layers must concur for an action to take effect; either layer's refusal stops the action.

## Enforcement

### Trigger conditions

- **Design phase**: any design proposing a new agent-action site must indicate where the gate runs and where the persistence-side check runs.
- **Code phase**: every agent-action site implements gate invocation; persistence services implement auth + purpose checks at HTTP entry.

### Required patterns

- Single gate-middleware module in `hermes-runtime` is the only legitimate gate implementation; agent action sites must invoke it (not reimplement gate logic).
- Persistence services maintain a per-service token list with declared purposes and check the inbound caller against the token + purpose at HTTP entry.
- Gate-decision events are recorded on the proposal in `backlog-core` so reconciliation can detect bypass.

### Required checks

1. Before merging an agent-action site, confirm it routes through the gate middleware; lint check rejects code that calls a tool without prior gate invocation.
2. Penetration-style test: a synthetic `hermes-runtime` build that omits the gate must be rejected by every persistence service it calls.

### Prohibited patterns

- Reimplementing gate logic anywhere outside the middleware module.
- Persistence-service code paths that accept calls without the auth + purpose check.
- "Trusted backdoor" credentials that bypass either layer.

## Reconsider trigger

Revisit this decision if:

- Agent-action sites grow to a number where consistent middleware invocation becomes brittle (e.g., a network of agents instead of one).
- A regulatory or threat-model change requires gate decisions to be made by a service outside `hermes-runtime`'s trust domain.
