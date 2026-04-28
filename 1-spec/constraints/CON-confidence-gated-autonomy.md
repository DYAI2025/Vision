# CON-confidence-gated-autonomy: Agent autonomy is bounded by confidence

**Category**: Operational

**Status**: Active

**Source stakeholder**: [STK-vincent](../stakeholders.md), [STK-ben](../stakeholders.md)

## Description

The agent (Hermes) must consult a per-action confidence score before taking any action that produces or proposes a change to project state. The score gates behavior across three bands:

- **Low band** — the agent must not act on its own and must not produce a binding proposal; the input is parked or routed to an inbox with an explicit reason.
- **Middle band** — the agent must request human review or clarification before acting; it may produce a proposal but it cannot self-accept.
- **High band** — the agent may act autonomously, **but only if all of the following hold**: the source's `consent_scope` permits the action, the tool being invoked is on the agent's whitelist, and the auto-policy for the project allows autonomous writes for this action class.

The exact band thresholds and the per-band behaviors are tracked as `REQ-F-*` requirements (`REQ-F-confidence-gate-low`, `REQ-F-confidence-gate-mid`, `REQ-F-confidence-gate-high`) so that thresholds can be tuned without changing this constraint.

Missing or revoked consent, an absent tool whitelist entry, or a disabled auto-policy each individually demote the action to the next-lower band. Demotion never escalates upward.

## Rationale

Codifies the "Hermes never writes unchecked" principle as a structural rule rather than a per-feature toggle. Bounds blast radius of agent errors and keeps the human-correction loop ([CON-human-correction-priority](CON-human-correction-priority.md)) usable — without a gate, low-confidence actions would flood the correction queue.

## Impact

- Every agent action site must expose a confidence value and route through a `confidence-gate` middleware in `hermes-runtime`. Sites that cannot produce a confidence value are not allowed to act.
- Drives the boundary-test harness: each band threshold needs explicit just-below / just-above tests.
- Drives schema for `auto-policy` per project (which action classes can run autonomously at high confidence).
- Audit log must record the confidence value, the band, and the gate decision for every agent action attempt — including refusals.
- This constraint pairs with [CON-no-direct-agent-writes](CON-no-direct-agent-writes.md): the gate decides *whether* to propose; the proposal pipeline decides *how* to apply.
