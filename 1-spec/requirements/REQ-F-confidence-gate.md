# REQ-F-confidence-gate: Three-band confidence gate intercepts every action site

**Type**: Functional

**Status**: Draft

**Priority**: Must-have

**Source**: [CON-confidence-gated-autonomy](../constraints/CON-confidence-gated-autonomy.md)

**Source stakeholder**: [STK-vincent](../stakeholders.md), [STK-ben](../stakeholders.md)

## Description

A confidence-gate middleware in `hermes-runtime` intercepts every action site (route, extract, propose-write, side-effect-tool-call). For each action, the gate reads:

- The action's `confidence` (from routing or extraction)
- The source's `consent_scope` for the action's purpose
- The action's tool whitelist entry (allowed / not-allowed for this skill / project)
- The project's `auto_policy` for the action class (autonomous / review-only / blocked)

The gate dispatches based on three bands (default thresholds, configurable per project):

- **Low band** (`confidence < 0.55`): drop or send to inbox with structured reason. Never act.
- **Middle band** (`0.55 ≤ confidence < 0.85`): route to review queue or request clarification. Never act autonomously.
- **High band** (`confidence ≥ 0.85`): act autonomously **only if all four** of (consent permits the purpose, tool is on whitelist, project auto-policy permits this action class, no `STK-message-sender` floor breach) are true. **Demotion rule:** any failed precondition demotes the action to the next-lower band; demotions never escalate upward.

Every gate decision is audit-logged with all inputs (confidence, gate band, consent state, whitelist entry, auto-policy state, demotion reason if any) and the outcome.

Thresholds (`0.55`, `0.85`) are not hardcoded — they live in per-project configuration with the documented defaults. Changing them requires an operator action that is itself audit-logged.

## Acceptance Criteria

- Given a confidence value just below 0.85 and otherwise-permitting preconditions, when an action passes through the gate, then it is routed to the review queue (mid-band behavior); given confidence just above 0.85 and the same preconditions, the action proceeds autonomously.
- Given confidence ≥0.85 but `consent_scope` does not permit the action's purpose, when the action passes through the gate, then it is demoted to mid-band (review queue) and the audit entry records `demotion_reason = consent_scope_missing`.
- Given a project whose `auto_policy` for the action class is `review-only`, when an autonomous-band action arrives, then it is demoted to mid-band regardless of confidence; the demotion is audit-logged.
- Given an action that bypasses the gate due to a tooling error, when the audit reconciliation runs at end-of-day, then the bypass is detected as a non-zero count and triggers an alert per [GOAL-trustworthy-supervised-agent](../goals/GOAL-trustworthy-supervised-agent.md).

## Related Constraints

- [CON-confidence-gated-autonomy](../constraints/CON-confidence-gated-autonomy.md) — defines the gate as a structural rule.
- [CON-no-direct-agent-writes](../constraints/CON-no-direct-agent-writes.md) — gate decisions on autonomous writes flow through the proposal pipeline.
- [CON-consent-required](../constraints/CON-consent-required.md) — consent scope is one of the gate inputs.

## Related Assumptions

- [ASM-confidence-scores-are-meaningful](../assumptions/ASM-confidence-scores-are-meaningful.md)
