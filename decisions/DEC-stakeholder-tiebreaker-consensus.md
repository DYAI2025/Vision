# DEC-stakeholder-tiebreaker-consensus: Peer-stakeholder conflicts resolved by consensus, not influence

**Status**: Active

**Category**: Process

**Scope**: system-wide

**Source**: [stakeholders.md](../1-spec/stakeholders.md) (`STK-vincent`, `STK-ben`); aligned with the "human corrections take precedence" principle in the project overview ([CLAUDE.md](../CLAUDE.md))

**Last updated**: 2026-04-27

## Context

`STK-vincent` and `STK-ben` are both `High`-influence peer collaborators with no hierarchy between them. The default conflict-resolution procedure in [`1-spec/CLAUDE.spec.md`](../1-spec/CLAUDE.spec.md) resolves conflicts by stakeholder influence — that mechanism is unavailable here.

Without an explicit rule, conflicts between Vincent and Ben can be silently picked by the agent (violating the "Hermes never writes unchecked" principle), default to first-mover (encoding rubber-stamp pressure on the second reviewer), or stall indefinitely without anyone knowing the project is blocked. All three failure modes are misaligned with the system's consent-and-correctness posture.

## Decision

When `STK-vincent` and `STK-ben` hold conflicting positions on the same artifact or proposal, the agent **parks** the conflicting items — no advancement, no silent pick — until the two reach explicit consensus.

`STK-message-sender` consent, retention, and privacy obligations form a non-negotiable floor: they **cannot be overruled** even by joint Vincent + Ben consensus. When a Vincent/Ben consensus would breach the floor, the floor wins and the proposal is rejected, not parked.

## Enforcement

### Trigger conditions

- **Specification phase**: an artifact (stakeholder field, goal, user story, requirement, assumption, constraint) has explicit feedback from both Vincent and Ben, and the positions are not reconcilable as worded.
- **Design phase**: a design choice in `architecture.md`, `data-model.md`, or `api-design.md` has explicit feedback from both Vincent and Ben, and the positions are not reconcilable as worded.
- **Code phase**: a code-level decision (component scope, naming, error-handling pattern, library choice, test strategy) has explicit feedback from both Vincent and Ben, and the positions are not reconcilable as worded.
- **Deploy phase**: not applicable by default — Ben is the sole operator (`STK-ben` carries the operator interest set). Revisit if `STK-vincent` is later given operator scope.

### Required patterns

- **Detect divergence** explicitly. Both stakeholders must have weighed in on the same field for a parking event to fire — silence from one party is not dissent.
- **Park** the conflicting artifact: if `Approved`, downgrade to `Draft` (per the standard status downgrade rule); if `Draft`, hold without advancement; do not advance any phase gate that depends on the parked artifact.
- **Notify** both stakeholders: summarize the divergence, list the candidate resolutions, name `STK-message-sender` floor implications if any.
- **Resume** only on explicit joint approval (both confirm the same resolution), or on one-then-other-acknowledged confirmation (one proposes the resolution, the other explicitly agrees) — never on inferred agreement, response timeout, or "no response after N hours."

### Required checks

1. Identify the conflicting fields and which stakeholders disagree.
2. Check whether `STK-message-sender` consent / retention / privacy interests are in tension. If yes, the floor wins regardless of Vincent / Ben consensus, and the proposal must be rejected or rewritten — not negotiated.
3. Confirm both Vincent and Ben have actually weighed in on the same artifact / field — never park on inferred dissent or third-party reports.
4. Confirm explicit consensus before resuming — both names confirmed, ideally on the artifact itself.
5. If a recurring pattern of conflict on the same topic emerges, propose a separate decision capturing the substantive resolution so future conflicts on that topic resolve automatically.

### Prohibited patterns

- Agent picks a side based on recency, length of argument, or "stronger reasoning."
- First-mover wins / last-mover wins by default.
- Time-based auto-resolution (e.g., "no response in 24 h → accept").
- Treating silence as agreement.
- Any resolution path that overrides `STK-message-sender` consent, retention, or privacy interests.
- Resuming the artifact while the conflict is still open, even if "the user clarified verbally" — confirmation must land on the artifact.
