# CON-human-correction-priority: Human corrections override agent decisions and produce learning signals

**Category**: Operational

**Status**: Active

**Source stakeholder**: [STK-vincent](../stakeholders.md), [STK-ben](../stakeholders.md)

## Description

When a human (Vincent or Ben) overrides, edits, or rejects an agent decision, the system must:

1. **Apply the override immediately**, not on a schedule. The corrected state is the new authoritative state in `backlog-core`, GBrain, and any downstream surface.
2. **Persist the override** as a first-class event in `backlog-core` (not as a free-form edit indistinguishable from agent activity).
3. **Emit a `learning_event`** that captures: the original proposal, the corrected outcome, the actor making the correction, the affected scope (project, source, action class), the confidence value before correction, and a `human_feedback` field if the actor provided one.
4. **Reflect the correction in subsequent agent behavior within the same session** for the affected scope — at minimum by injecting the relevant `learning_event`s into the agent's prompt context and applying any updated routing/confidence rules the learning loop produces.

Corrections override even high-confidence agent autonomous writes. A human always wins over the agent for the artifact in question.

This rule is bounded by the floor in [DEC-stakeholder-tiebreaker-consensus](../../decisions/DEC-stakeholder-tiebreaker-consensus.md): Vincent's correction may conflict with Ben's, in which case the conflict-resolution flow takes over.

## Rationale

The system's accuracy strategy depends on cheap, frequent human-correction loops. Corrections are training signal, not noise — they are the primary way the system learns project structure, routing rules, and confidence calibration. If corrections were treated as ephemeral overrides without learning emission, the agent would repeat the same mistake every session.

## Impact

- Every agent-action surface (kanban edit proposal, task creation proposal, routing decision, project assignment) must expose explicit accept / edit / reject primitives, not just an "edit anywhere" path.
- Schema: `learning_event` is a defined type in `backlog-core`'s event log with required fields (`learning_type`, `before`, `after`, `actor_id`, `applies_to`, `confidence_before`, `confidence_after`, `human_feedback?`).
- Drives a `learning-loop` skill in Hermes runtime that reads recent `learning_event`s and refreshes prompt context / routing rules.
- Drives a per-project profile (`PROFILE.md` in GBrain) that is updated as learnings accumulate, so project-specific routing improves over time without requiring every correction to be re-applied.
- Pairs with [CON-no-direct-agent-writes](CON-no-direct-agent-writes.md): corrections also flow through the proposal-validate-apply-audit loop, just with `actor_id = human` and an implicit confidence of 1.0.
