# DEC-gdpr-legal-review-deferred: Trail

> Companion to `DEC-gdpr-legal-review-deferred.md`.
> AI agents read this only when evaluating whether the decision is still
> valid or when proposing a change or supersession.

## Alternatives considered

### Option A: Complete the legal review before the Spec → Design gate
- Pros: Eliminates High-risk Unverified assumption before architecture work begins; if the assumption is invalidated, no Design work is wasted on a foundation that will need to change.
- Cons: Blocks Design-phase progress on an out-of-band scheduling activity; review may take days to weeks; Design momentum is lost; the assumption's risk doesn't materialize until non-personal-use data subjects are onboarded, which is itself a Code-phase event.

### Option B: Defer to the Code phase with explicit milestone-bound triggers (chosen)
- Pros: Preserves Design momentum; the deferral is explicitly time-bounded by triggers that match when the assumption actually becomes load-bearing (non-Vincent/Ben source registration; first non-development deploy); Design artifacts that depend on the assumption carry fallback notes so design rework is not silent if the review later invalidates.
- Cons: Design may proceed in directions that the legal review later contradicts, requiring localized rework; fallback-note discipline must be enforced consistently or the deferral gradually loses meaning.

### Option C: Defer indefinitely / no formal deferral decision
- Pros: Simplest in the short term; no decision overhead.
- Cons: A High-risk assumption permanently load-bearing without verification is exactly what gates exist to prevent. No trigger enforcement means the review is unlikely to happen until something forces it (e.g., a regulator inquiry, a subject complaint), which is the most expensive moment to discover an invalidation.

## Reasoning

Option B was chosen because the assumption's risk is **conditional on a specific event** — onboarding non-Vincent/Ben data subjects — that does not occur during personal-use development. Tying the verification deadline to that event aligns the cost of verification with the moment the assumption becomes load-bearing, while preserving Design momentum during the development window where the risk is dormant.

The accepted trade-off: Design work may need localized rework if the legal review later invalidates the assumption. This is acceptable because (1) the fallback-note discipline at design-artifact level keeps the dependency surface visible and bounded, (2) the alternative — pausing Design indefinitely — is more expensive than localized rework, and (3) the deferral has explicit triggers, so the verification commitment remains real rather than aspirational.

Conditions that would invalidate this reasoning: if the personal-use scope expands such that "Vincent and Ben only" stops being the actual data-subject set in practice (e.g., they start ingesting messages from many third-party senders without scheduling the legal review), the deferral has effectively lapsed and the decision should be superseded by one that reschedules the verification deadline.

## Human involvement

**Type**: human-decided

**Notes**: User explicitly chose Option B in the gap-analysis follow-up after seeing all three options laid out. No dissent recorded. Vincent has not been consulted directly in this scaffold conversation; per `DEC-stakeholder-tiebreaker-consensus`, this decision is open to amendment if Vincent objects when surfaced, in which case the deferral would park until consensus.

## Changelog

| Date | Change | Involvement |
|------|--------|-------------|
| 2026-04-27 | Initial decision; deferral established with Code-phase and Deploy-phase triggers | human-decided |
