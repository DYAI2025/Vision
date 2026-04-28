# DEC-stakeholder-tiebreaker-consensus: Trail

> Companion to `DEC-stakeholder-tiebreaker-consensus.md`.
> AI agents read this only when evaluating whether the decision is still
> valid or when proposing a change or supersession.

## Alternatives considered

### Option A: Consensus required (chosen)
- Pros: Matches the system's consent-and-correctness posture (parking on uncertainty is the same shape as confidence-gate parking). Prevents the agent from silently picking a side. No co-owner gets pushed into rubber-stamping. Easy to relax later if a recurring topic produces its own DEC.
- Cons: Can stall progress indefinitely if Vincent and Ben don't engage. No automatic escape valve. Requires both stakeholders to actually respond before anything moves on contested items.

### Option B: Initiator wins after a stated review window
- Pros: Keeps the project moving. Avoids indefinite parking. Reasonable when both parties trust each other's judgment on routine items.
- Cons: Encodes a default that effectively pressures the second reviewer into rubber-stamping (silence becomes assent). Misaligned with the "human corrections take precedence" principle. A timeout-based mechanism is exactly the kind of "agent decided based on the clock" behavior the spec rules out elsewhere (cf. confidence gate).

### Option C: Defer / case-by-case
- Pros: Maximum flexibility; no predetermined rule could be wrong.
- Cons: Lacks predictability. Leaves room for the agent to make ad-hoc picks ("I thought this was minor"). Encourages the silent-pick failure mode.

## Reasoning

Option A was chosen because parking-on-disagreement is the same posture the system already takes for low-confidence proposals and missing consent — it is internally consistent. Options B and C both contain implicit agent-side decision points (timeout, "this seems minor") that violate the broader rule that Hermes never writes unchecked.

The accepted trade-off: contested items can stall. This is acceptable because (1) Vincent and Ben are co-owners with strong shared incentive to unblock, (2) the alternative — agent silently or pseudo-automatically picking a side — is incompatible with the project's audit and consent posture, and (3) recurring stalls on the same topic are a signal to record a substantive `DEC-*` for that topic, which converts the recurring dispute into a one-time agreement.

Conditions that would invalidate this reasoning: if Vincent or Ben becomes effectively unreachable (extended absence, departure, role change) such that "consensus required" stops meaning "two engaged co-owners" and starts meaning "indefinite block." In that case, supersede with a rule that handles asymmetric availability (e.g., named-deputy, scope-based authority).

## Human involvement

**Type**: human-decided

**Notes**: User explicitly chose Option A in elicitation when presented with all three options and a recommendation for Option A. No dissent recorded. Vincent has not been consulted directly in this scaffold conversation; this is documented as a process rule that Vincent will be able to review and amend when the spec phase is closed.

## Changelog

| Date | Change | Involvement |
|------|--------|-------------|
| 2026-04-27 | Initial decision | human-decided |
