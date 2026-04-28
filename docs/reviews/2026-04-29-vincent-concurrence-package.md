# Vincent Concurrence Package — Spec-Phase Approvals

**Date prepared:** 2026-04-29
**Prepared by:** Ben (with AI agent assistance)
**For:** Vincent
**Authority basis:** [`DEC-stakeholder-tiebreaker-consensus`](../../decisions/DEC-stakeholder-tiebreaker-consensus.md) — peer-stakeholder approvals require both Ben and Vincent.

---

## Why this exists

When the Specification phase closed on 2026-04-27, **Ben approved 5 goals and 10 must-have requirements alone**, then advanced the project into Design and Code. The peer-stakeholder rule (`DEC-stakeholder-tiebreaker-consensus`) says approvals like these need both of us. So everything below is **provisionally approved on Ben's signature, pending your concurrence.**

If you object to any item, that artifact rolls back to `Draft`. Design content that depends on it may need rework. The agent has been continuing on the optimistic assumption that you'll concur — implementation progress is now at **12 / 106 tasks done (Phase 1: 12/17)**, all in the bootstrap layer that is well upstream of any of the items below, so a "no" on a specific item is recoverable without throwing away work.

The simplest reply is **"I concur on all of it"** — that locks the spec phase and removes the carry-over flag from `CLAUDE.md`. If you want edits, list the IDs and what should change; we'll loop back through `/SDLC-elicit` for those.

---

## What needs concurrence — Goals (5)

All five are recorded as `Status: Approved` in [`1-spec/goals/`](../../1-spec/goals/). Read the file for the full success-criteria checkboxes; one-line summaries below.

| ID | Priority | Summary |
|----|---|---|
| [`GOAL-auditable-consent-and-privacy`](../../1-spec/goals/GOAL-auditable-consent-and-privacy.md) | **Must** | Every input has a verifiable consent record, retention is auto-enforced, RTBF servable end-to-end within 24h. |
| [`GOAL-multi-source-project-ingestion`](../../1-spec/goals/GOAL-multi-source-project-ingestion.md) | **Must** | All MVP input channels (WhatsApp, voice, repo, manual CLI) flow through one normalization path producing routed, deduplicated, structured project artifacts. |
| [`GOAL-trustworthy-supervised-agent`](../../1-spec/goals/GOAL-trustworthy-supervised-agent.md) | **Must** | Hermes is gated by confidence + consent + auto-policy; humans correct cheaply; corrections improve agent behavior in-session. |
| [`GOAL-durable-project-memory`](../../1-spec/goals/GOAL-durable-project-memory.md) | **Must** | GBrain is a usable, queryable, human-readable memory with brain-first lookup discipline and zero raw-content leakage in the durable layer. |
| [`GOAL-local-portable-deployment`](../../1-spec/goals/GOAL-local-portable-deployment.md) | Should | Deploy to any Docker-capable VPS in <60 min; default-zero remote inference; backup/restore tested; Tailscale optional. |

---

## What needs concurrence — Approved Requirements (10)

All ten are recorded as `Status: Approved` in [`1-spec/requirements/`](../../1-spec/requirements/). Each links to a goal and a stakeholder.

### Compliance (4) — non-negotiable per `STK-message-sender` floor

| ID | Summary |
|----|---|
| [`REQ-COMP-consent-record`](../../1-spec/requirements/REQ-COMP-consent-record.md) | Per-source consent record with `lawful_basis = consent` (Art. 6(1)(a)), append-only history, read-as-of capability. |
| [`REQ-COMP-rtbf`](../../1-spec/requirements/REQ-COMP-rtbf.md) | Art. 17 RTBF cascade across all storage layers within 24h, with mandatory verification query returning zero subject rows. |
| [`REQ-COMP-data-export`](../../1-spec/requirements/REQ-COMP-data-export.md) | Art. 15 + 20 per-subject export (JSON minimum) covering consent state, derived artifacts, and pending raw artifacts. |
| [`REQ-COMP-purpose-limitation`](../../1-spec/requirements/REQ-COMP-purpose-limitation.md) | Components declare processing purposes; cross-purpose access rejected at the persistence boundary. |

### Security (3)

| ID | Summary |
|----|---|
| [`REQ-SEC-audit-log`](../../1-spec/requirements/REQ-SEC-audit-log.md) | Append-only hash-chained audit log covering mutations, consent operations, RTBF, remote inference, retention sweeps. |
| [`REQ-SEC-redaction-precondition`](../../1-spec/requirements/REQ-SEC-redaction-precondition.md) | Persistence-service writes to `derived_keep` reject payloads containing raw-content markers; ingestion derives before write. |
| [`REQ-SEC-remote-inference-audit`](../../1-spec/requirements/REQ-SEC-remote-inference-audit.md) | Remote inference calls pre-gated by profile + caller + data class + consent scope; full audit entry on every call attempt. |

### Functional (3) — consent operations

| ID | Summary |
|----|---|
| [`REQ-F-source-registration`](../../1-spec/requirements/REQ-F-source-registration.md) | Operator can register a source and update its `consent_scope`; both flows persist as events with before/after state. |
| [`REQ-F-consent-revocation`](../../1-spec/requirements/REQ-F-consent-revocation.md) | Revocation halts ingest before the next event; in-flight events from the source are dropped at the boundary. |
| [`REQ-F-retention-sweep`](../../1-spec/requirements/REQ-F-retention-sweep.md) | Daily idempotent sweep hard-deletes `raw_30d` artifacts at age 30; sweep is crash-safe and audit-logged per deletion. |

---

## For awareness (concurrence on these is implicit if you concur on the items above)

### Decisions made during Spec + Design phases (12 active)

You should see these because they shape what "approved" actually means in practice. The two with direct stakeholder-meta impact:

| ID | Why you should know |
|----|---|
| [`DEC-stakeholder-tiebreaker-consensus`](../../decisions/DEC-stakeholder-tiebreaker-consensus.md) | The rule that produces this very document. Defines that any Vincent ↔ Ben conflict is parked until consensus. Records the floor: `STK-message-sender` interests aren't subject to negotiation. |
| [`DEC-gdpr-legal-review-deferred`](../../decisions/DEC-gdpr-legal-review-deferred.md) | We deferred the GDPR legal review out of the Spec → Design gate into the Code phase. Means design proceeds on the assumption (`ASM-derived-artifacts-gdpr-permissible`) that derived artifacts are GDPR-defensible long-term, with a fallback documented in `architecture.md`. **Legal review must complete before first non-Vincent/Ben source registration and before first non-development deploy.** |

The other 10 decisions are technical scope (Postgres as event store, FastAPI stack, hash-chain over payload-hash, URL-path API versioning, etc.). Listed in [`CLAUDE.md`](../../CLAUDE.md) under "Decisions recorded this phase" if you want the full set; nothing in there normally requires stakeholder-level review.

### Unverified assumptions — one is load-bearing

| ID | Risk | Why it matters |
|----|---|---|
| [`ASM-derived-artifacts-gdpr-permissible`](../../1-spec/assumptions/ASM-derived-artifacts-gdpr-permissible.md) | **High** | Pending legal review; if invalidated, RTBF cascade gains a `consent_for_derivatives` toggle and `consent_scope` schema gets `derivative_retention` enum. Architecture has the fallback note. |

The other six assumptions are technology/environment risks (confidence-score calibration, channel-shape convergence, VPS-Docker baseline stability, etc.) — verifiable during Code-phase tasks, not requiring your sign-off now.

---

## What I need from you

Pick one of the following. Replying "1" or "2" by itself is enough:

1. **"I concur on all of it"** — locks all 5 goals + 10 requirements as fully approved. Removes the carry-over flag from `CLAUDE.md`. Implementation continues unchanged.
2. **"I concur except [list of IDs]"** — concur on everything not listed; the listed items roll back to `Draft` and we re-elicit them via `/SDLC-elicit`. Spell out what you'd change for each: scope, wording, or priority.
3. **"I concur, but I want to record a stipulation"** — concur on all items but with a recorded condition (e.g., "this requirement is approved on the basis that we revisit X in Phase Y"). I'll record the stipulation as a decision or as a note on the affected artifact's history.

If something is ambiguous to you in any of the items above, **don't guess** — flag it and I'll pull the full file content into the next reply so you have the acceptance criteria in front of you.

---

## What happens after you reply

- **All concur:** I update `CLAUDE.md` Current State to drop the "subject to Vincent's concurrence" carry-over and the `Spec → Design carry-overs` bullet. I add a one-line entry to each affected artifact's history-equivalent (the carry-over note in CLAUDE.md). Done.
- **Some objections:** the listed artifacts revert. I run `/SDLC-elicit` to walk the changes through; design content that depends on the reverted artifacts gets re-validated; if any task in `tasks.md` already references a reverted requirement, it gets flagged.
- **Stipulation:** I record a new `DEC-*` capturing the stipulation, link it from the affected artifacts, and the Current State carry-over note gets replaced with a pointer to the new decision.

In all three cases, the Code-phase work that has happened so far (Phase 1: bootstrap + 4 component skeletons) is **not affected** — it touches no approved goal/requirement directly; the worst case is that the implementation plan in Phase 2+ may need re-ordering if a requirement gets re-prioritized.

---

## Quick links

- All goals: [`1-spec/goals/`](../../1-spec/goals/)
- All requirements: [`1-spec/requirements/`](../../1-spec/requirements/)
- All assumptions: [`1-spec/assumptions/`](../../1-spec/assumptions/)
- All constraints: [`1-spec/constraints/`](../../1-spec/constraints/)
- All decisions: [`decisions/`](../../decisions/)
- Spec-phase index: [`1-spec/CLAUDE.spec.md`](../../1-spec/CLAUDE.spec.md)
- Project Current State: [`CLAUDE.md`](../../CLAUDE.md) (search for "Spec → Design carry-overs")
