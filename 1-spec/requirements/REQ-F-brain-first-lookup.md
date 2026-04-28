# REQ-F-brain-first-lookup: Routing and extraction query GBrain before scoring; citation discipline is measured

**Type**: Functional

**Status**: Draft

**Priority**: Must-have

**Source**: [GOAL-durable-project-memory](../goals/GOAL-durable-project-memory.md), [CON-no-direct-agent-writes](../constraints/CON-no-direct-agent-writes.md)

**Source stakeholder**: [STK-vincent](../stakeholders.md), [STK-ben](../stakeholders.md)

## Description

Agent routing and extraction must query GBrain (project profiles, recent episodes, learnings for the affected scope) **before** producing a proposal. The query result and a relevance summary are recorded on the resulting `proposal` event:

- `cited_pages` — list of GBrain page ids consulted that contributed to the proposal.
- `lookup_summary` — a short structured summary of what the lookup returned and why it is or isn't reflected in the proposal (e.g., "3 prior episodes in project X, 1 routing learning applied", or "no prior episodes found in this project — confidence reduced accordingly").

`cited_pages` may be empty only when accompanied by an explicit `lookup_summary` reason. Empty `cited_pages` without a reason is treated as a **missed lookup** and rejected at the proposal-pipeline validation step.

Discipline is measured: on a rolling 30-day window, **≥95% of routing decisions for projects with ≥10 prior episodes carry a non-empty `cited_pages`**. Projects with <10 prior episodes (cold-start) are excluded from the percentage but still required to record a non-empty `lookup_summary`.

When the rate falls below 95% on a qualifying project, the daily [REQ-REL-audit-reconciliation](REQ-REL-audit-reconciliation.md) emits a `learning_gap.brain-first-discipline` event so the operator can investigate. Possible causes: lookup tooling failure, prompt-context fall-off (per [ASM-in-session-learning-feasible](../assumptions/ASM-in-session-learning-feasible.md)), or schema drift hiding pages from search.

This requirement complements [REQ-F-project-routing](REQ-F-project-routing.md) (which defines the routing-decision shape) and [REQ-F-decision-inspection](REQ-F-decision-inspection.md) (which surfaces `cited_pages` to the operator). This requirement formalizes the discipline as an enforceable, measured property of the system — not a documentation item.

## Acceptance Criteria

- Given a routing or extraction proposal whose `cited_pages` is empty and whose `lookup_summary` is also empty, when the proposal-pipeline validates it, then the proposal is rejected with `missed_lookup`; the agent must retry the lookup before re-emitting.
- Given a 30-day window with routing decisions for projects of varying maturity, when the metric is computed, then qualifying-project (≥10 prior episodes) citation rate ≥95%; cold-start-project routing decisions all have non-empty `lookup_summary`.
- Given a project whose citation rate falls below 95%, when reconciliation runs, then a `learning_gap.brain-first-discipline` event is emitted with the project id and the rate.

## Related Constraints

- [CON-no-direct-agent-writes](../constraints/CON-no-direct-agent-writes.md) — proposal-pipeline validation includes the missed-lookup check.

## Related Assumptions

- [ASM-confidence-scores-are-meaningful](../assumptions/ASM-confidence-scores-are-meaningful.md) — citation contributes to scoring meaningfulness.
- [ASM-in-session-learning-feasible](../assumptions/ASM-in-session-learning-feasible.md) — citation depends on prompt-context refresh discipline holding up.
