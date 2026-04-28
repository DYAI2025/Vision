# DEC-confidence-gate-as-middleware: Trail

> Companion to `DEC-confidence-gate-as-middleware.md`.

## Alternatives considered

### Option A: Middleware inside `hermes-runtime`, with persistence-side auth as second layer (chosen)
- Pros: Lowest latency (no extra hop); simplest deployment; gate stays close to the agent code that needs it; persistence-side auth provides defense-in-depth.
- Cons: A bug in the agent code that omits gate invocation is a bypass risk; mitigated by reconciliation detection but still possible to ship.

### Option B: Separate gate service
- Pros: Gate is a hard barrier — any action must go through it; can be operated and audited independently of agent code.
- Cons: Adds a network hop on every agent action (latency hit on `REQ-PERF-ingest-latency`); adds an operational service; the agent must still call the gate, so the bypass risk doesn't fully disappear — it just moves.

### Option C: Gate library shared between `hermes-runtime` and persistence services
- Pros: Both sides invoke the same code; consistency by construction.
- Cons: Couples agent and persistence code via a shared library — version-skew risk; harder to evolve gate logic without coordinated deploys; still requires the agent to actually invoke it.

## Reasoning

Option A was chosen because the gate is fundamentally an agent-side decision (the agent has the confidence value, the consent snapshot, the auto-policy state) and putting it in a separate service adds latency and operational service without removing the bypass risk — the agent still has to call the gate either way. Defense-in-depth is achieved through `REQ-COMP-purpose-limitation` enforcement at the persistence boundary (which is independent of the gate).

Accepted trade-off: an agent-code bug omitting gate invocation is theoretically possible. Mitigation: lint checks at code-review time + `REQ-REL-audit-reconciliation` detection at runtime; bypasses produce alerts within one reconciliation cycle.

## Human involvement

**Type**: ai-proposed/human-approved

**Notes**: Proposed during the architecture-design session (2026-04-27); user approved the architecture proposal which embedded this choice.

## Changelog

| Date | Change | Involvement |
|------|--------|-------------|
| 2026-04-27 | Initial decision recorded as part of architecture.md drafting | ai-proposed/human-approved |
