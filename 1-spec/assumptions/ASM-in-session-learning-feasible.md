# ASM-in-session-learning-feasible: Prompt-context refresh + routing-rules update produces visible behavior change in-session

**Category**: Technology

**Status**: Unverified

**Risk if wrong**: Medium — if false, the user-visible "agent learns from corrections in real time" behavior collapses into "agent learns overnight after re-embedding or retraining," which materially weakens [GOAL-trustworthy-supervised-agent](../goals/GOAL-trustworthy-supervised-agent.md)'s correction-loop value proposition. The remediation is bounded: add a faster online-learning path (e.g., embedding-space pinning per project, lightweight LoRA-style adapters, or per-project retrieval index updates), or accept a softer learning latency target with explicit communication in the proposal detail view ("this learning will apply on the next batch refresh"). Neither remediation is architecture-breaking, but both add complexity that is currently designed out.

## Statement

Within-session learning application — refreshing the agent's prompt context with recent `learning_event`s for the affected scope, plus updating per-project routing rules and `PROFILE.md` content via `gbrain-memory-write` — is sufficient to produce a visible behavior change in the next-N agent proposals on the same scope. Specifically: the agent reading the new learning into its context window, and the routing layer's brain-first lookup picking up the updated profile and rules pages, together flip behavior on a paraphrased version of the original mistake within the same session.

This excludes scenarios that would require model parameter updates: corrections that require unlearning or strongly contradict the model's pretraining priors may not be reachable through context + retrieval alone.

## Rationale

The plausibility comes from how the agent's behavior is shaped: routing decisions are dominated by the brain-first lookup result (project profile, recent episodes, learnings) rather than by raw model parameters. Prompt context, with named recent corrections plus a refreshed routing-rules table, is generally sufficient to flip an instruction-following model's behavior on similar inputs in the same session. This is the same pattern that works in production retrieval-augmented agents in adjacent products.

The risk concentrates on edge cases: (1) corrections that are *adversarial* against the model's strong priors (e.g., the model is over-confident on a routing pattern that is wrong only in this user's context); (2) the prompt-context window filling up with too many learnings, forcing fall-off that loses recently-corrected patterns; (3) routing decisions that are dominated by embedding similarity rather than by the prompt-cited rules, where re-indexing GBrain pages happens slower than the next proposal arrives.

## Verification Plan

- **During Code phase, before exposing autonomous-band defaults to any project:** build a boundary test that issues a known-incorrect proposal in scope S, records a correction, then issues a paraphrased input also in scope S — assert the corrected behavior applies on the paraphrase. Repeat the test across each `learning_type` category (`routing`, `extraction`, `confidence`, `correction`, `project_structure`, `agent_behavior`).
- **Trigger for re-verification:** the boundary test fails on a `learning_type`; observed in-the-wild "agent repeated the same mistake after correction" reports cluster around a specific `learning_type`; prompt-context fall-off becomes a visible cause of regression.

## Related Artifacts

- Goals: [GOAL-trustworthy-supervised-agent](../goals/GOAL-trustworthy-supervised-agent.md)
- Requirements: [REQ-F-learning-loop](../requirements/REQ-F-learning-loop.md), [REQ-F-correction-actions](../requirements/REQ-F-correction-actions.md)
- Constraints: [CON-human-correction-priority](../constraints/CON-human-correction-priority.md)
