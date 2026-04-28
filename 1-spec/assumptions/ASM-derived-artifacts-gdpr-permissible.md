# ASM-derived-artifacts-gdpr-permissible: Derived artifacts can be retained indefinitely under the original consent

**Category**: Regulatory

**Status**: Unverified

**Risk if wrong**: High — if false, the entire `derived_keep` retention model is invalid; we would need to either time-bound derivative retention (forcing periodic re-derivation or deletion of project memory) or obtain fresh, separate consent for derivative retention. Either alternative materially changes the product's value proposition (durable project memory) and the system architecture (GBrain becomes ephemeral or requires per-derivation consent records).

## Statement

Derived artifacts (summaries, project profiles, decisions, learnings, kanban cards) created from inputs covered by an active consent record can lawfully be retained indefinitely under that original consent — without fresh consent, without a hard time limit on the derivative, and without retroactive deletion when the original `raw_30d` source content is swept — provided that:

1. The derivation purpose (`summarize`, `extract_artifacts`, `learning_signal`) was within the source's `consent_scope` at the time of derivation.
2. The RTBF cascade ([REQ-COMP-rtbf](../requirements/REQ-COMP-rtbf.md)) propagates correctly through derived artifacts.
3. Derived artifacts do not embed raw content beyond what consent covered ([REQ-SEC-redaction-precondition](../requirements/REQ-SEC-redaction-precondition.md)).

## Rationale

This matches a common interpretation of GDPR for legitimately consented downstream processing — where the lawful basis at the moment of processing governs the resulting artifact's lifetime, subject to data subject rights. The data minimization principle is satisfied at the *raw* layer (30-day delete) rather than at the derived layer.

The interpretation is plausible but not statically verified. It is most fragile in cases where (a) a derived artifact is so detailed that it constitutes a continued surveillance product, or (b) the original consent was vague enough that the chosen `consent_scope` vocabulary does not actually cover what the system is doing.

## Verification Plan

> **Verification deferred to Code phase per [DEC-gdpr-legal-review-deferred](../../decisions/DEC-gdpr-legal-review-deferred.md) (2026-04-27).** The Spec → Design phase gate may proceed without verification; the review is now bound to Code-phase milestones (first non-Vincent/Ben source registration; first non-development deploy) rather than to the gate itself. Production deployment remains blocked until verification completes.

- **Originally scheduled:** before Spec → Design phase-gate transition (now deferred per the decision above).
- **Now required by:** before first registration of any source whose `actor_id` is not `STK-vincent` or `STK-ben`, AND before first non-development deploy — whichever comes first.
- **Review scope:** legal review of (i) the `consent_scope` vocabulary as worded in the source-registration UX, (ii) the categories of derived artifacts the system intends to keep, and (iii) the RTBF cascade design's coverage of derivatives. Reviewer confirms or annotates with adjustments.
- **Ongoing:** if derived artifacts grow in scope (e.g., new artifact types added in later releases), re-confirm against the original consent vocabulary or amend the vocabulary and require re-consent.
- **Trigger for re-verification:** any change that broadens what derived artifacts capture; any commercial deployment (would change the regulatory profile entirely).
- **Status update protocol:** when the review is scheduled / in-progress / completed, append to this section with the date and current state, and append a corresponding entry to `*.history.md`'s changelog (per `DEC-gdpr-legal-review-deferred` enforcement).

## Related Artifacts

- Goals: [GOAL-auditable-consent-and-privacy](../goals/GOAL-auditable-consent-and-privacy.md), [GOAL-durable-project-memory](../goals/GOAL-durable-project-memory.md)
- Requirements: [REQ-COMP-consent-record](../requirements/REQ-COMP-consent-record.md), [REQ-COMP-rtbf](../requirements/REQ-COMP-rtbf.md), [REQ-COMP-purpose-limitation](../requirements/REQ-COMP-purpose-limitation.md)
- Constraints: [CON-gdpr-applies](../constraints/CON-gdpr-applies.md), [CON-tiered-retention](../constraints/CON-tiered-retention.md), [CON-gbrain-no-raw-private-truth](../constraints/CON-gbrain-no-raw-private-truth.md)
