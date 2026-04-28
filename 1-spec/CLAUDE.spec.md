Phase-specific instructions for the **Specification** phase. Extends [../CLAUDE.md](../CLAUDE.md).

## Purpose

This phase defines **what** we're building and **why**. Focus on clarity, measurability, and alignment with stakeholder needs.

## Phase artifacts

| Artifact | Location | Purpose |
|----------|----------|---------|
| Stakeholders | [`stakeholders.md`](stakeholders.md) | Roles with interests and influence |
| Goals | [`goals/`](goals/) | High-level outcomes |
| User Stories | [`user-stories/`](user-stories/) | User-facing capabilities |
| Requirements | [`requirements/`](requirements/) | Testable system requirements |
| Assumptions | [`assumptions/`](assumptions/) | Beliefs taken as true but not verified |
| Constraints | [`constraints/`](constraints/) | Hard limits on design and implementation |

---

## AI Guidelines

### Per-artifact guidance

**Stakeholders**: ask who uses, funds, operates, or is affected by the system. Record influence level honestly — it drives conflict resolution. Add entries to [`stakeholders.md`](stakeholders.md).

**Goals**: decompose vague ideas into concrete, measurable outcomes. Use MoSCoW priority consistently.
Status lifecycle: `Draft → Approved → Achieved → Deprecated`. Only a human can approve or deprecate. The agent marks `Achieved` when all success criteria are met (linked requirements implemented).

**User Stories**: use "As a [role], I want [capability], so that [benefit]." The role must be an existing stakeholder ID. Acceptance criteria at the story level are high-level; detailed criteria live in requirements.
Status lifecycle: `Draft → Approved → Implemented → Deprecated`. Only a human can approve or deprecate. The agent marks `Implemented` when all linked requirements reach `Implemented`.

**Requirements**: use clear, testable language (not "should be fast" — use "response time < 200ms at p95"). Choose the correct requirement class.
Requirement classes: `REQ-F` Functional, `REQ-PERF` Performance, `REQ-SEC` Security, `REQ-REL` Reliability, `REQ-USA` Usability, `REQ-MNT` Maintainability, `REQ-PORT` Portability, `REQ-SCA` Scalability, `REQ-COMP` Compliance.
Status lifecycle: `Draft → Approved → Implemented → Deprecated`. Only a human can approve or deprecate. The agent marks `Implemented` when all linked tasks reach Done.

**Assumptions**: always record the risk level (what happens if wrong?) and a verification plan when possible.
Status lifecycle: `Unverified → Verified | Invalidated`. The agent marks `Verified` when the verification plan confirms the assumption. Only a human can mark `Invalidated` (triggers impact analysis on dependent artifacts).

**Constraints**: consider technical (platforms, dependencies), business (budget, timeline, team size), and operational (hosting, compliance) categories.
Status lifecycle: `Active → Lifted`. Only a human can lift a constraint.

### Conflict resolution

A conflict exists when two or more requirements cannot both be satisfied as stated.

**Never resolve a conflict silently.** Always surface it before acting.

1. **Identify**: note conflicting requirement IDs, source stakeholders, influence levels, and why they are incompatible.
2. **Ask the user**: present what makes them incompatible, stakeholders and influence levels, two or more resolution options, and a recommended option if one is clearly better.
3. **Wait for explicit approval** before modifying any file.
4. **Apply**: update affected requirement files and index rows. Update dependent user stories or goals if affected. Record a decision if the resolution imposes a recurring constraint.
5. **Verify**: no artifacts remain in a conflicting state after resolution.

### Assumption invalidation

When an assumption is found to be wrong or no longer holds:

1. **Identify impact**: list all artifacts (requirements, user stories, decisions) that depend on the invalidated assumption.
2. **Ask the user**: present the invalidated assumption, the affected artifacts, and proposed adjustments or alternatives.
3. **Wait for explicit approval** before modifying any file.
4. **Apply**: change the assumption's Status to `Invalidated`. Update or flag all dependent artifacts as directed.
5. **Verify**: no artifacts remain based on the invalidated assumption without acknowledgment.

### Artifact deprecation

When an artifact (goal, user story, requirement) is no longer relevant:

1. Propose deprecation to the user with rationale and downstream impact.
2. Wait for explicit approval.
3. Change Status to `Deprecated` in the artifact file. Update its index row.
4. Check for dependent artifacts — flag any that reference the deprecated item.

---

## Decisions Relevant to This Phase

| File | Title | Trigger |
|------|-------|---------|
| [DEC-stakeholder-tiebreaker-consensus](../decisions/DEC-stakeholder-tiebreaker-consensus.md) | Peer-stakeholder conflicts resolved by consensus, not influence | An artifact (stakeholder field, goal, user story, requirement, assumption, constraint) has explicit feedback from both `STK-vincent` and `STK-ben` and the positions are not reconcilable as worded |
| [DEC-gdpr-legal-review-deferred](../decisions/DEC-gdpr-legal-review-deferred.md) | GDPR legal review deferred from Spec → Design gate to Code phase | Promoting a requirement that lists `ASM-derived-artifacts-gdpr-permissible` as a Related Assumption from `Status: Draft` to `Status: Approved` (must include "if invalidated" remediation reference) |
<!-- Add rows as decisions are recorded. File column: [DEC-kebab-name](../decisions/DEC-kebab-name.md) -->

---

## Linking to Other Phases

- Goals, user stories, constraints, assumptions, and requirements are referenced in design documents (`2-design/`)
- Requirements determine the development tasks in `3-code/tasks.md`; each task references the requirements it fulfills
- Acceptance criteria inform test cases (`3-code/`)

---

## Goals Index

| File | Priority | Status | Summary |
|------|----------|--------|---------|
| [GOAL-auditable-consent-and-privacy](goals/GOAL-auditable-consent-and-privacy.md) | Must-have | Approved | Every input has a verifiable consent record, retention is auto-enforced, RTBF is servable end-to-end within 24h |
| [GOAL-multi-source-project-ingestion](goals/GOAL-multi-source-project-ingestion.md) | Must-have | Approved | All MVP input channels (WhatsApp, voice, repo, manual CLI) flow through one normalization path producing routed, deduplicated, structured project artifacts |
| [GOAL-trustworthy-supervised-agent](goals/GOAL-trustworthy-supervised-agent.md) | Must-have | Approved | Hermes is gated by confidence + consent + auto-policy; humans correct cheaply; corrections improve agent behavior in-session |
| [GOAL-durable-project-memory](goals/GOAL-durable-project-memory.md) | Must-have | Approved | GBrain is a usable, queryable, human-readable memory with brain-first lookup discipline and zero raw-content leakage in the durable layer |
| [GOAL-local-portable-deployment](goals/GOAL-local-portable-deployment.md) | Should-have | Approved | Operator deploys to any Docker-capable VPS in <60 min; default-zero remote inference; backup/restore tested; Tailscale optional |
<!-- Add rows as goals are created. File column: [GOAL-kebab-name](goals/GOAL-kebab-name.md) -->

---

## User Stories Index

| File | Role | Priority | Status | Summary |
|------|------|----------|--------|---------|
| [US-register-source-with-consent](user-stories/US-register-source-with-consent.md) | operator | Must-have | Draft | Register a new ingestion source with explicit consent scope, actor, and retention policy |
| [US-revoke-or-update-consent](user-stories/US-revoke-or-update-consent.md) | operator | Must-have | Draft | Revoke or modify consent on an existing source; revocation halts ingest immediately and is audit-logged |
| [US-service-rtbf-request](user-stories/US-service-rtbf-request.md) | operator | Must-have | Draft | Service an RTBF request end-to-end across all storage layers and verify zero subject rows remain |
| [US-ingest-from-any-channel](user-stories/US-ingest-from-any-channel.md) | collaborator | Must-have | Draft | Any consented MVP channel (WhatsApp / voice / repo / manual CLI) flows through the same normalization path |
| [US-handle-review-required-input](user-stories/US-handle-review-required-input.md) | operator | Must-have | Draft | Low-confidence or ambiguous-consent input lands in a review queue with explicit disposition options |
| [US-see-extracted-artifacts](user-stories/US-see-extracted-artifacts.md) | collaborator | Must-have | Draft | Extracted artifacts appear on the project Kanban board with traceability back to the source `input_event` |
| [US-review-and-act-on-proposal](user-stories/US-review-and-act-on-proposal.md) | collaborator | Must-have | Draft | Accept / edit / reject agent proposals from one surface; `learning_event` emitted automatically |
| [US-see-learning-effect](user-stories/US-see-learning-effect.md) | collaborator | Must-have | Draft | Agent reflects recent corrections in subsequent same-session proposals on the same scope |
| [US-inspect-agent-decision](user-stories/US-inspect-agent-decision.md) | collaborator | Must-have | Draft | Inspect why the agent made a proposal — confidence, gate band, GBrain citations, applied learnings, source input |
| [US-browse-project-memory](user-stories/US-browse-project-memory.md) | collaborator | Must-have | Draft | Navigate any project's state, decisions, and learnings in Obsidian via valid internal links |
| [US-fresh-vps-install](user-stories/US-fresh-vps-install.md) | operator | Should-have | Draft | Deploy from a clean clone to a passing smoke test on any Docker-capable VPS using only `.env.example` |
| [US-backup-restore-cycle](user-stories/US-backup-restore-cycle.md) | operator | Should-have | Draft | Take a backup on host A and restore identical state on host B |
| [US-secret-rotation](user-stories/US-secret-rotation.md) | operator | Should-have | Draft | Rotate secrets on a running system without losing project state |
<!-- Add rows as user stories are created. File column: [US-kebab-name](user-stories/US-kebab-name.md) -->

---

## Requirements Index

| File | Type | Priority | Status | Summary |
|------|------|----------|--------|---------|
| [REQ-F-source-registration](requirements/REQ-F-source-registration.md) | Functional | Must-have | Approved | Operator can register a source and update its `consent_scope`; both flows persist as events with before/after state |
| [REQ-F-consent-revocation](requirements/REQ-F-consent-revocation.md) | Functional | Must-have | Approved | Revocation halts ingest before the next event; in-flight events from the source are dropped at the boundary |
| [REQ-F-retention-sweep](requirements/REQ-F-retention-sweep.md) | Functional | Must-have | Approved | Daily idempotent sweep hard-deletes `raw_30d` artifacts at age 30; sweep is crash-safe and audit-logged per deletion |
| [REQ-COMP-consent-record](requirements/REQ-COMP-consent-record.md) | Compliance | Must-have | Approved | Per-source consent record with `lawful_basis = consent` (Art. 6(1)(a)), append-only history, read-as-of capability |
| [REQ-COMP-rtbf](requirements/REQ-COMP-rtbf.md) | Compliance | Must-have | Approved | Art. 17 RTBF cascade across all storage layers within 24h, with mandatory verification query returning zero subject rows |
| [REQ-COMP-data-export](requirements/REQ-COMP-data-export.md) | Compliance | Must-have | Approved | Art. 15 + 20 per-subject export (JSON minimum) covering consent state, derived artifacts, and pending raw artifacts |
| [REQ-COMP-purpose-limitation](requirements/REQ-COMP-purpose-limitation.md) | Compliance | Must-have | Approved | Components declare processing purposes; cross-purpose access is rejected at the persistence boundary |
| [REQ-SEC-audit-log](requirements/REQ-SEC-audit-log.md) | Security | Must-have | Approved | Append-only hash-chained audit log covering mutations, consent operations, RTBF, remote inference, retention sweeps |
| [REQ-SEC-redaction-precondition](requirements/REQ-SEC-redaction-precondition.md) | Security | Must-have | Approved | Persistence-service writes to `derived_keep` reject payloads containing raw-content markers; ingestion derives before write |
| [REQ-SEC-remote-inference-audit](requirements/REQ-SEC-remote-inference-audit.md) | Security | Must-have | Approved | Remote inference calls pre-gated by profile + caller + data class + consent scope; full audit entry on every call attempt |
| [REQ-F-input-event-normalization](requirements/REQ-F-input-event-normalization.md) | Functional | Must-have | Draft | Single normalization layer produces channel-agnostic `input_event`s; channel concerns confined to `channel_metadata` extension |
| [REQ-F-project-routing](requirements/REQ-F-project-routing.md) | Functional | Must-have | Draft | Routing produces `{project_id, confidence, cited_pages, alternatives, reasoning}` with brain-first GBrain lookup; null project_id is valid |
| [REQ-F-artifact-extraction](requirements/REQ-F-artifact-extraction.md) | Functional | Must-have | Draft | Typed artifacts (task / proposal / decision_candidate / risk / open_question) extracted from autonomous-band events through the proposal pipeline |
| [REQ-F-duplicate-detection](requirements/REQ-F-duplicate-detection.md) | Functional | Must-have | Draft | Semantic + lexical duplicate detector; FN ≤5% / FP ≤2%; duplicates attach to existing artifact rather than creating new ones |
| [REQ-F-review-queue](requirements/REQ-F-review-queue.md) | Functional | Must-have | Draft | Mid-band, ambiguous-consent, and `review_required` items queue with structured dispositions; reclassify dispositions emit `learning_event` |
| [REQ-F-confidence-gate](requirements/REQ-F-confidence-gate.md) | Functional | Must-have | Draft | Three-band gate intercepts every action; thresholds configurable per project; demotion never escalates upward; gate decisions audit-logged |
| [REQ-PERF-ingest-latency](requirements/REQ-PERF-ingest-latency.md) | Performance | Must-have | Draft | p95 autonomous-path < 5 min, p95 review-path < 2 min; 30-min tail constraint with `processing.stuck` alerts; synthetic monitoring |
| [REQ-PERF-routing-throughput](requirements/REQ-PERF-routing-throughput.md) | Performance | Should-have | Draft | ≥10 events/min sustained, ≥30 events/min for 2-min burst on reference VPS spec, without violating ingest-latency p95 |
| [REQ-F-proposal-pipeline](requirements/REQ-F-proposal-pipeline.md) | Functional | Must-have | Draft | Every agent mutation flows through propose → validate → apply with all stages chained by `proposal_id` in audit log |
| [REQ-F-correction-actions](requirements/REQ-F-correction-actions.md) | Functional | Must-have | Draft | Accept / edit-and-accept / reject primitives on every agent surface; each disposition emits a `learning_event` automatically |
| [REQ-F-learning-loop](requirements/REQ-F-learning-loop.md) | Functional | Must-have | Draft | Eager within-session loop: refresh prompt context + project profile + routing rules; subsequent proposals tagged with `learnings_applied` |
| [REQ-F-decision-inspection](requirements/REQ-F-decision-inspection.md) | Functional | Must-have | Draft | Detail view per proposal: confidence, gate band, citations, applied learnings, source event, tool, suppression reason if any |
| [REQ-REL-audit-reconciliation](requirements/REQ-REL-audit-reconciliation.md) | Reliability | Must-have | Draft | Daily reconciliation: 0 unmatched mutations target, <1% gate bypasses target, orphan audits recorded; report stored as derived_keep |
| [REQ-F-gbrain-schema](requirements/REQ-F-gbrain-schema.md) | Functional | Must-have | Draft | Every GBrain page validates against type-specific frontmatter at write time; out-of-schema writes rejected with structured error |
| [REQ-F-bidirectional-links](requirements/REQ-F-bidirectional-links.md) | Functional | Must-have | Draft | Forward + back links are atomic in `gbrain-memory-write`; half-link writes rejected; deletes propagate symmetrically |
| [REQ-F-brain-first-lookup](requirements/REQ-F-brain-first-lookup.md) | Functional | Must-have | Draft | Routing/extraction queries GBrain pre-scoring; `cited_pages`+ `lookup_summary` recorded; ≥95% citation rate on qualifying scopes (30-day window) |
| [REQ-MNT-vault-audit-sweep](requirements/REQ-MNT-vault-audit-sweep.md) | Maintainability | Must-have | Draft | Weekly vault audit: ≥99% schema conformance, 0 half-links, 0 raw-content leaks in `derived_keep`, 0 expired raw envelopes |
| [REQ-PORT-vps-deploy](requirements/REQ-PORT-vps-deploy.md) | Portability | Should-have | Draft | Fresh-VPS install + smoke test < 60 min on any Docker-capable host; verified on ≥2 providers with no script edits |
| [REQ-MNT-env-driven-config](requirements/REQ-MNT-env-driven-config.md) | Maintainability | Should-have | Draft | All runtime config via `.env`; `.env.example` drift-checked; missing required keys cause fail-fast at startup |
| [REQ-REL-backup-restore-fidelity](requirements/REQ-REL-backup-restore-fidelity.md) | Reliability | Should-have | Draft | Backup-on-A → restore-on-B reproduces project state bit-identically; retention sweep re-evaluates against original timestamps |
| [REQ-REL-secret-rotation](requirements/REQ-REL-secret-rotation.md) | Reliability | Should-have | Draft | Rotation procedure preserves running state; zero stale credentials remain anywhere; `secret.rotated` audit event with no values logged |
| [REQ-F-state-reconstruction](requirements/REQ-F-state-reconstruction.md) | Functional | Must-have | Draft | Backlog-Core can reconstruct full project state from event log alone; deterministic, side-effect-free in preview mode; powers rollback / audit replay / disaster recovery |
| [REQ-REL-event-replay-correctness](requirements/REQ-REL-event-replay-correctness.md) | Reliability | Must-have | Draft | Replay is deterministic, idempotent, crash-safe, and fails fast on corrupted chains; verified by smoke-test harness |
| [REQ-USA-kanban-obsidian-fidelity](requirements/REQ-USA-kanban-obsidian-fidelity.md) | Usability | Must-have | Draft | Kanban boards open in stock Obsidian without parse errors; sync only touches declared sync-owned fields; human edits to non-sync fields preserved; manual column moves detected |
<!-- Add rows as requirements are created. File column: [REQ-CLASS-kebab-name](requirements/REQ-CLASS-kebab-name.md) -->

---

## Assumptions Index

| File | Category | Status | Risk | Summary |
|------|----------|--------|------|---------|
| [ASM-derived-artifacts-gdpr-permissible](assumptions/ASM-derived-artifacts-gdpr-permissible.md) | Regulatory | Unverified | High | Derived artifacts retained indefinitely under original consent are GDPR-defensible (subject to RTBF and redaction); pending legal review |
| [ASM-rtbf-24h-window-acceptable](assumptions/ASM-rtbf-24h-window-acceptable.md) | Regulatory | Unverified | Medium | A 24h RTBF completion window is acceptable for personal-use deployment under GDPR Art. 12(3); revisit on commercial use |
| [ASM-subject-reference-resolvable](assumptions/ASM-subject-reference-resolvable.md) | Technology | Unverified | Medium | Stable subject references can be indexed across `backlog-core`, GBrain, and Kanban without storage redesign at MVP scale |
| [ASM-confidence-scores-are-meaningful](assumptions/ASM-confidence-scores-are-meaningful.md) | Technology | Unverified | High | Composite confidence scoring is calibrated enough that the 0.55 / 0.85 thresholds are decision-relevant; calibration curve must be reviewed before enabling autonomous-band defaults per project |
| [ASM-channel-shape-convergeable](assumptions/ASM-channel-shape-convergeable.md) | Technology | Unverified | Medium | Four MVP channels normalize into one `input_event` shape with channel concerns confined to `channel_metadata`; verified by a swap-test before second adapter |
| [ASM-in-session-learning-feasible](assumptions/ASM-in-session-learning-feasible.md) | Technology | Unverified | Medium | Prompt-context refresh + routing-rules update is sufficient for visible behavior change in-session, without model retrain or re-embedding |
| [ASM-vps-docker-baseline-stable](assumptions/ASM-vps-docker-baseline-stable.md) | Environment | Unverified | Medium | Docker-capable VPS baseline (Ubuntu/Debian + Compose v2 + reference hardware) is stable across mainstream providers without provider-specific patches |
<!-- Add rows as assumptions are created. File column: [ASM-kebab-name](assumptions/ASM-kebab-name.md) -->

---

## Constraints Index

| File | Category | Status | Summary |
|------|----------|--------|---------|
| [CON-consent-required](constraints/CON-consent-required.md) | Operational | Draft | Every ingestion source must register `source_id`, `actor_id`, `consent_scope`, and `retention_policy` before any input is processed; missing/unclear consent blocks ingestion |
| [CON-no-platform-bypass](constraints/CON-no-platform-bypass.md) | Operational | Draft | No code, config, or runbook may circumvent third-party platform security mechanisms (encryption, login, 2FA, session integrity, anti-automation) |
| [CON-confidence-gated-autonomy](constraints/CON-confidence-gated-autonomy.md) | Operational | Draft | Agent autonomy is bounded by a three-band confidence gate; thresholds and behaviors specified as `REQ-F-*` |
| [CON-no-direct-agent-writes](constraints/CON-no-direct-agent-writes.md) | Operational | Draft | Agents mutate state only through dedicated audited tools (`backlog-core`, `gbrain-memory-write`, `kanban-sync`); direct DB/vault/file writes prohibited |
| [CON-human-correction-priority](constraints/CON-human-correction-priority.md) | Operational | Draft | Human corrections override agent decisions immediately, are persisted as first-class events, and emit `learning_event`s that feed back into agent context within the session |
| [CON-local-first-inference](constraints/CON-local-first-inference.md) | Technical | Draft | Default-local inference via Ollama + Gemma; remote inference only as named, audited, per-task operator opt-in with consent-scope gate |
| [CON-vps-portable-deployment](constraints/CON-vps-portable-deployment.md) | Technical | Draft | System runs on any Docker-capable VPS via `.env` + Compose; no host lock-in, no cloud-vendor dependencies, Tailscale optional |
| [CON-gdpr-applies](constraints/CON-gdpr-applies.md) | Operational | Draft | EU GDPR applies; lawful basis is consent (Art. 6(1)(a)); data subject rights (Art. 15–20) supported operationally; purpose limitation and data minimization enforced |
| [CON-tiered-retention](constraints/CON-tiered-retention.md) | Operational | Draft | Three retention classes per artifact: `raw_30d` (hard delete), `derived_keep` (kept, RTBF-bound), `review_required` (human-review queue) |
| [CON-gbrain-no-raw-private-truth](constraints/CON-gbrain-no-raw-private-truth.md) | Operational | Draft | GBrain stores derived artifacts only; raw content allowed only inside `raw_30d`-classed envelopes that the retention sweep can prune |
<!-- Add rows as constraints are created. File column: [CON-kebab-name](constraints/CON-kebab-name.md) -->
