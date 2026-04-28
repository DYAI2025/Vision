# DEC-gdpr-legal-review-deferred: GDPR legal review deferred from Spec → Design gate to Code phase

**Status**: Active

**Category**: Process

**Scope**: system-wide

**Source**: [ASM-derived-artifacts-gdpr-permissible](../1-spec/assumptions/ASM-derived-artifacts-gdpr-permissible.md), [CON-gdpr-applies](../1-spec/constraints/CON-gdpr-applies.md), [GOAL-auditable-consent-and-privacy](../1-spec/goals/GOAL-auditable-consent-and-privacy.md)

**Last updated**: 2026-04-27

## Context

`ASM-derived-artifacts-gdpr-permissible` is a High-risk `Unverified` assumption: that derived artifacts (summaries, decisions, learnings) under `derived_keep` retention can lawfully be retained indefinitely under the original "consent for project work" basis, subject to RTBF cascades. The assumption's verification plan calls for legal review **before the Spec → Design phase-gate transition** of (i) the `consent_scope` vocabulary, (ii) the categories of derived artifacts retained indefinitely, and (iii) the RTBF cascade design.

Without this review, transitioning to Design either (a) blocks indefinitely while the review is scheduled and completed, or (b) proceeds while a foundational architectural assumption remains High-risk Unverified. Option (a) costs Design-phase momentum; option (b) is exactly the failure mode phase gates are designed to prevent.

A third option — proceed to Design, but commit to completing the review before specific Code-phase milestones that would make the assumption load-bearing — preserves momentum while keeping the verification commitment real and time-bounded.

## Decision

The legal review of `ASM-derived-artifacts-gdpr-permissible` is **deferred from the Spec → Design phase gate to the Code phase**. The Spec → Design transition proceeds without requiring the assumption to be `Verified`. The deferral is bounded by explicit triggers that re-introduce the review as a hard precondition before specific Code- and Deploy-phase milestones.

The deferral is **not indefinite** and **not unconditional**. The assumption remains High-risk; this decision exists to make the deferral and its triggers explicit, not to soften the verification commitment.

## Enforcement

### Trigger conditions

- **Specification phase**: n/a — this decision applies at and after the gate transition; the Spec phase itself is unaffected.
- **Design phase**: any design choice that depends on the validity of `ASM-derived-artifacts-gdpr-permissible` — including RTBF cascade design, derived-artifact retention strategy, `consent_scope` vocabulary, GBrain page schemas — must include an explicit *"fallback if assumption invalidated"* note in the relevant design document. Reviewers must verify these notes exist before approving the design artifact. The intent is to avoid sunk cost if the legal review later forces a redesign.
- **Code phase**: the legal review **must complete and the assumption must be `Verified`** (or be `Invalidated` and replanned) **before**:
  - First registration of any source whose `actor_id` is **not** `STK-vincent` or `STK-ben` (i.e., before any third-party data subject can be onboarded).
  - First non-development deployment that processes data subjects beyond personal use.
  - Whichever comes first.
- **Deploy phase**: production / non-development deployment is **blocked** until the assumption is `Verified`. Operator (Ben) must confirm verification status as part of the production-deploy runbook precondition checklist.

### Required patterns

- Design and Code work proceeds *as if* the assumption holds, while explicitly tracking where the design depends on it. Each affected design or requirement carries a fallback note.
- Every requirement that lists `ASM-derived-artifacts-gdpr-permissible` as a Related Assumption must, before its `Status` advances to `Approved`, include an "if invalidated" remediation outline in its acceptance criteria or in a linked note.
- The legal review remains tracked as an open verification item in the assumption's file. Updates to the review's scheduling, progress, or completion are recorded by appending to `ASM-derived-artifacts-gdpr-permissible.md`'s Verification Plan section and to `*.history.md`'s changelog.
- The operator's production-deploy runbook (`4-deploy/runbooks/`) carries an explicit precondition: "Confirm `ASM-derived-artifacts-gdpr-permissible.Status == Verified` before proceeding."

### Required checks

1. Before approving a design artifact (architecture / data-model / API design) that touches consent vocabulary, derived-artifact retention, RTBF design, or GBrain page schemas, verify the artifact contains a fallback-if-invalidated note for `ASM-derived-artifacts-gdpr-permissible`.
2. Before promoting any requirement that lists this assumption as `Related Assumption` from `Status: Draft` to `Status: Approved`, verify the requirement's acceptance criteria include an "if invalidated" remediation reference.
3. Before the first non-Vincent / non-Ben source is registered in any environment beyond local development, confirm the assumption is `Verified`. If not, block the registration.
4. Before any production deploy, the operator runs the deploy precondition checklist; the GDPR-verification check must pass.
5. Whenever the legal-review status changes (scheduled / in-progress / completed-Verified / completed-Invalidated), update `ASM-derived-artifacts-gdpr-permissible.md` and append to its history file.

### Prohibited patterns

- **Treating the deferral as permanent.** The assumption remains High-risk until reviewed. "We'll get to it eventually" without trigger-bound milestones is the failure mode this decision exists to prevent.
- **Onboarding non-Vincent / non-Ben subjects** (commercial use, external collaborators, additional named users with their own consent profile) under the deferred state. Personal-use scope only until verification.
- **Any production / non-development deploy** under the deferred state.
- **Silently flipping the assumption to `Verified`** without a recorded review event in the history file naming the reviewer, date, and review scope.
- **Treating the design-phase fallback notes as optional documentation.** They are gate-review-blocking artifacts.
