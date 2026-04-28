## Language Policy

**All AI outputs must be in English**, regardless of the language used in user prompts. This applies to code, comments, documentation, configuration files, commit messages, and response text.

## Memory Policy

**Do not use Claude memory files to store project information**. All project knowledge — domain context, team structure, constraints, decisions, and any other relevant information — must be captured exclusively through the SDLC artifact system (stakeholders, constraints, assumptions, goals, requirements, decisions, etc.). This ensures all knowledge is structured, traceable, and available to every team member working on the project.

---

## Project Overview

**Name:** `project-agent-system` (codename: Vision)

**What it is.** A local, agent-driven project management system, deployable to any VPS, that turns multi-channel inputs (WhatsApp, chat, voice transcripts, repository events, manual CLI entries, Obsidian/Kanban edits) into structured, traceable project work. It serves two named human collaborators (Vincent and Ben) and is supervised, never autonomous-by-default.

**Problem it solves.** Project knowledge — tasks, decisions, requirements, risks, learnings — is scattered across chat, voice, and code, with no consented, auditable pipeline that turns it into a maintained project memory and a usable kanban board. This system provides that pipeline locally, without surveillance and without bypassing platform protections.

**Architectural backbone (separation of concerns).**
- **Hermes** — the project-manager agent (steering layer; produces proposals, never the source of truth).
- **GBrain** — human-readable semantic + episodic project memory, stored as a markdown vault with stable IDs, frontmatter, and links between projects, people, episodes, decisions, and learnings.
- **Backlog-Core** — append-only, event-sourced technical truth (Postgres) used for project-state reconstruction, rollback, and validation of agent proposals.
- **Obsidian Kanban** — the human collaborative surface; markdown-backed boards kept in sync with Backlog-Core and GBrain via dedicated sync tooling.
- **WhatsOrga Ingest** — normalizes inputs into `input_event`s, validating consent, source, actor, and retention; private/off-topic content is filtered.
- **Ollama + Gemma** — local model runtime that powers Hermes; no required cloud LLM dependency.
- **Tailscale + Docker Compose** — private networking and portable deployment; no hard host bindings.

**Non-negotiable principles** (these shape every requirement and decision):
- Consent-based ingestion only — every source carries `source_id`, `actor_id`, `consent_scope`, `retention_policy`. Missing/unclear consent → block, no processing.
- No bypassing of platform protections (encryption, login, 2FA, session security).
- Confidence gate: `<0.55` ignore with reason; `0.55–0.85` human review/clarification; `≥0.85` autonomous proposal or write **only if** consent + whitelist + auto-policy all permit it.
- Hermes writes nothing directly — proposals are validated by Backlog-Core; GBrain and Kanban are mutated only via dedicated tools; every change generates audit + memory entries.
- Human corrections are first-class — every override becomes a `learning_event` that updates routing rules, project profiles, and prompt context.
- No secrets in the repo; deployment configurable via `.env` and Compose only.

**Key collaborators (modeled as consented actors):** Vincent, Ben.

**Source specification.** The full design intent, target repository structure, GBrain memory model, Obsidian kanban model, confidence policy, Hermes prompt and skills, backlog-core event model, deployment plan, testing strategy, and Definition of Done are captured in [`../Vision-full-prompt.md`](../Vision-full-prompt.md). Treat that document as the authoritative input to the Specification phase — its content gets translated into stakeholders, goals, requirements, assumptions, constraints, and decisions inside `1-spec/` rather than referenced ad hoc during later phases.

### Current State

**Phase: Design.** The Specification phase closed on 2026-04-27 with all gate preconditions met (5 goals + 10 requirements approved on Ben's authority, subject to Vincent's concurrence per [`DEC-stakeholder-tiebreaker-consensus`](decisions/DEC-stakeholder-tiebreaker-consensus.md); gap analysis 0 Critical / 0 Important / 3 Minor; M-3 resolved by [`DEC-gdpr-legal-review-deferred`](decisions/DEC-gdpr-legal-review-deferred.md)).

**Design documents:**
- [`architecture.md`](2-design/architecture.md) — drafted (5-service decomposition: `whatsorga-ingest`, `hermes-runtime`, `backlog-core`, `gbrain-bridge`, `kanban-sync`; Postgres event store; Caddy / Tailscale ingress profile via `.env`; Ollama-backed local inference; Obsidian-as-review-UI). Includes constraint compliance table, requirement coverage table, and the GDPR-deferral fallback note required by `DEC-gdpr-legal-review-deferred`.
- [`data-model.md`](2-design/data-model.md) — drafted (Postgres `events` + `consent_sources` + `consent_history` + `subject_index` matview; partition strategy; full event-type catalog with retention class; cross-cutting `input_event` / `proposal` / `learning_event` payload shapes; 10 GBrain page-type schemas with bidirectional links; Kanban sync-owned vs. user-owned field set with versioned schema). Includes constraint compliance, approved-requirement coverage, and the GDPR-deferral fallback note.
- [`api-design.md`](2-design/api-design.md) — drafted (cross-cutting conventions: URL-path versioning, bearer-token auth, idempotency-key headers, error response shape, pagination, content type; full HTTP API for `backlog-core` (input events, proposal pipeline, consent management, RTBF, export, audit, state reconstruction, sweep, reconciliation, review queue, event stream), `gbrain-bridge` (page CRUD, vault audit sweep, watch-script disposition hook), `kanban-sync` (card operations, sync trigger, board read), `hermes-runtime` (health, operator-triggered processing); Ollama integration; operator CLI command surface; Obsidian command-palette bindings). Includes constraint compliance, approved-requirement coverage, and the GDPR-deferral fallback note.

**Decisions recorded this phase (9):**
- [`DEC-postgres-as-event-store`](decisions/DEC-postgres-as-event-store.md) — Postgres for `backlog-core`'s event log.
- [`DEC-direct-http-between-services`](decisions/DEC-direct-http-between-services.md) — synchronous HTTP/REST between services at MVP.
- [`DEC-confidence-gate-as-middleware`](decisions/DEC-confidence-gate-as-middleware.md) — gate inside `hermes-runtime`; persistence-side auth as defense-in-depth.
- [`DEC-platform-bypass-review-checklist`](decisions/DEC-platform-bypass-review-checklist.md) — explicit list of patterns reviewers reject; closes gap-analysis M-1.
- [`DEC-obsidian-as-review-ui`](decisions/DEC-obsidian-as-review-ui.md) — review queue and proposal-detail views as GBrain pages disposed via Obsidian command palette; no dedicated frontend service at MVP.
- [`DEC-hash-chain-over-payload-hash`](decisions/DEC-hash-chain-over-payload-hash.md) — chain incorporates a stable `payload_hash` so RTBF and retention sweep can redact `payload` without breaking the chain.
- [`DEC-api-versioning`](decisions/DEC-api-versioning.md) — URL-path versioning (`/v1/...`) across all services.
- [`DEC-service-auth-bearer-tokens`](decisions/DEC-service-auth-bearer-tokens.md) — per-service bearer tokens with declared purposes; `.env`-driven; rotated per `REQ-REL-secret-rotation`.
- [`DEC-idempotency-keys`](decisions/DEC-idempotency-keys.md) — `Idempotency-Key` header on every mutation endpoint; 24h TTL.

Decision totals: 11 (2 carried from Spec phase + 9 from Design).

**Spec → Design carry-overs:**
- `ASM-derived-artifacts-gdpr-permissible` (High, Unverified) — legal review deferred per `DEC-gdpr-legal-review-deferred`; `architecture.md` includes the mandatory fallback-if-invalidated note. Review must complete before first non-Vincent/Ben source registration and before first non-development deploy.
- Vincent's concurrence on the spec-phase approvals (5 goals + 10 requirements) is still outstanding; if Vincent objects on any item, that artifact parks back to `Draft` and dependent design content may need adjustment.

**Completeness assessment (2026-04-27, second pass):** 0 Critical, 0 Important, 2 Minor. I-1 closed by a small `architecture.md` update assigning duplicate detection to `hermes-runtime` (with rationale). Spec-phase carry-overs M-1 and M-3 remain closed. Remaining Minor findings: **M-4** (`REQ-PERF-ingest-latency` / `REQ-PERF-routing-throughput` not explicitly traced; runtime concerns) and **M-5** (cursor-based pagination + long-poll/SSE event-stream documented as conventions but not DEC'd) — both addressable during Code phase. All 10 approved requirements covered across the 3 design docs; 23/24 Draft requirements covered (the remaining one — `REQ-F-duplicate-detection` — is now design-anchored to `hermes-runtime`); all 10 constraints verified with no violations; all 7 unverified assumptions either have design fallbacks or Code-phase verification plans; 11 decisions recorded. **Component decomposition (2026-04-28):** 6 components identified and per-component directories created under `3-code/`: `whatsorga-ingest`, `hermes-runtime`, `backlog-core`, `gbrain-bridge`, `kanban-sync`, `cli`. Each component carries a `CLAUDE.component.md`. Per-component technology choices deferred to Code-phase decisions when the first implementation task per component is picked up.

**Implementation progress (2026-04-28):** 5 / 105 tasks Done. Currently in **Phase 1: Bootstrap & Deployment Foundation** (5/16 tasks complete). Just completed: `TASK-ollama-bootstrap` — Ollama operator-facing bootstrap (`4-deploy/ollama/README.md` with model footprint table for Gemma family + remote-inference opt-in pointer; `scripts/ollama.sh` generic exec wrapper; `scripts/ollama-pull.sh` one-time idempotent model-pull; `OLLAMA_MODEL=gemma3:4b` default added to `.env.example` and injected into hermes-runtime per `CON-local-first-inference`). Auto-pull at container start deferred — no upstream hook in `ollama/ollama:latest`; operator runs the pull script once after `docker compose up`, and `TASK-install-vps-script` will fold this into the install runbook. Previously completed: `TASK-monorepo-skeleton`, `TASK-compose-stack-skeleton`, `TASK-env-example-bootstrap`, `TASK-postgres-bootstrap`.

**Implementation plan created (2026-04-28):** 7 phases, **105 tasks** in `3-code/tasks.md` covering all 5 approved goals:
- **Phase 1** (16 tasks) — Bootstrap & deployment foundation: empty deployable system, `vision health` aggregator, ingress profile.
- **Phase 2** (16 tasks) — Consent foundation + audit backbone: source CRUD, consent history, hash-chained audit log.
- **Phase 3** (12 tasks) — Minimum end-to-end pipeline: manual CLI ingest → normalization → backlog-core; proposal pipeline; events stream consumer.
- **Phase 4** (13 tasks) — Privacy compliance: retention sweep, RTBF cascade with verification, data export.
- **Phase 5** (15 tasks) — Agent foundation + GBrain + Kanban surface: confidence gate, routing/extraction/duplicate-detection skills, GBrain page CRUD with schema/links/redaction, Kanban card CRUD with sync-vs-edit boundary.
- **Phase 6** (14 tasks) — Supervision & learning loop: review queue, Obsidian watch script, proposal disposition, learning loop, state reconstruction.
- **Phase 7** (19 tasks) — Multi-channel & operability: WhatsApp/voice/repo adapters, daily reconciliation, vault audit sweep, backup/restore, secret rotation, cross-provider VPS verification, performance load tests, remote-inference profile.

Each phase ends with a manual-testing-readiness task (`TASK-phase-N-manual-testing`) that creates/updates a runbook in `4-deploy/runbooks/` and updates per-component READMEs.

**Next step:** transition into execution via `/SDLC-execute-next-task` — picks the next pending task from Phase 1 (`TASK-monorepo-skeleton`), implements with tests, handles design gaps, and updates task status. For ad-hoc fixes outside the phased plan, use `/SDLC-fix`. Use `/SDLC-status` at any time for a project-wide dashboard.

---

## Phase-Specific Instructions

Each phase directory contains a `CLAUDE.<phase>.md` file. When working in a phase:

1. Read the phase-specific instructions — they extend (not override) this file
2. Consult the decisions index in that phase file before starting work (for the Code phase, decisions indexes are in each component's `CLAUDE.component.md`, not in `CLAUDE.code.md`)
3. Work within the appropriate phase structure

| Phase | Directory | Focus |
|-------|-----------|-------|
| **Specification** | `1-spec/` | Define what to build and why |
| **Design** | `2-design/` | Define how to build it |
| **Code** | `3-code/` | Build it |
| **Deploy** | `4-deploy/` | Ship and operate it |

### Cross-Skill Artifact Procedures

Any modification to phase artifacts — whether performed inside a skill, during a free-prompt conversation, or as a side effect of any other task — must follow the authoritative procedures for that phase:

- **Specification artifacts** (`1-spec/`): follow the procedures in [`.claude/skills/SDLC-elicit/SKILL.md`](.claude/skills/SDLC-elicit/SKILL.md) — including traceability rules, status downgrade on modification, index synchronization, bidirectional link maintenance, and Current State tracking.
- **Design artifacts** (`2-design/`): follow the procedures in [`.claude/skills/SDLC-design/SKILL.md`](.claude/skills/SDLC-design/SKILL.md) — including downstream effect checks, decision recording triggers, requirement coverage verification, and Current State tracking.
- **Code phase task artifacts** (`3-code/tasks.md`): follow the procedures in [`.claude/skills/SDLC-implementation-plan/SKILL.md`](.claude/skills/SDLC-implementation-plan/SKILL.md) — including phased task grouping, traceability links, incremental deployability, and Current State tracking.

### Phase Gates

Before creating artifacts in the next phase, check these minimum preconditions. Gates are advisory — warn the user if not met, but proceed if they confirm.

| Transition | Preconditions |
|------------|---------------|
| Spec → Design | Stakeholders defined; at least one goal Approved; at least one requirement Approved; gap analysis recorded in Current State and fresh (not stale, no Critical gaps) |
| Design → Code | All design documents drafted (`architecture.md`, `data-model.md`, `api-design.md`); completeness assessment recorded in Current State and fresh (not stale, no Critical findings); components identified (per-component directories in `3-code/`) |

There is no gate between Code and Deploy. Deploy activities (deployments, runbooks, infrastructure setup) can happen at any time during the Code phase.

---

## Artifacts

All project knowledge is captured as structured markdown files alongside the source code. This gives AI agents the full context that human developers would normally carry in their heads or scattered across external tools, and creates a traceability chain from business goals to deployed code.

### Types and locations

| Prefix | Artifact | Location |
|--------|----------|----------|
| `GOAL` | Goals | `1-spec/goals/` |
| `US` | User Stories | `1-spec/user-stories/` |
| `REQ-CLASS` | Requirements | `1-spec/requirements/` |
| `ASM` | Assumptions | `1-spec/assumptions/` |
| `CON` | Constraints | `1-spec/constraints/` |
| `STK` | Stakeholders | `1-spec/stakeholders.md` (rows) |
| `TASK` | Tasks | `3-code/tasks.md` (rows) |
| `DEC` | Decisions | `decisions/` |

### Naming

All artifact IDs use the pattern `PREFIX-kebab-name` — a type prefix followed by a descriptive kebab-case name. The descriptive name **is** the unique identifier (e.g., `DEC-use-postgres`, `REQ-F-search-by-name`). There are no numeric sequences, to avoid ID collisions when working on parallel branches.

### Phase indexes

Every `CLAUDE.<phase>.md` file contains index tables listing the artifacts in that phase. Each index must include a **File column** with a relative link to the artifact file, so that AI agents can discover the file name and human reviewers can navigate easily.

---

## Graduated Safeguards

AI agents operate autonomously within development tasks. For project-level decisions, the scaffold defines three tiers:

| Tier | When | Agent behavior |
|------|------|----------------|
| **Always ask** | Conflict resolution, design gaps, decision deprecation/supersession, phase gate advancement | Stop, present options, wait for human approval |
| **Ask first time, then follow precedent** | Naming conventions, error handling patterns, test structure | Ask once, record the decision, apply consistently afterward |
| **Decide and record** | Routine implementation choices within established patterns | Decide autonomously, record in the appropriate artifact |

When spotting a related issue, potential improvement, or ambiguous situation during a task, **surface it to the user** instead of silently deciding to act or not act.

---

## Decisions

Decisions live in `decisions/`. Each decision has two files:

- **`DEC-kebab-name.md`** — the active record (context, decision, enforcement). Read during normal task execution.
- **`DEC-kebab-name.history.md`** — the trail (alternatives, reasoning, changelog). Read only when evaluating or changing a decision.

Each `CLAUDE.<phase>.md` contains a decisions index with trigger conditions. A decision may appear in multiple phase indexes.

### How to use decisions during tasks

1. Consult the decisions index in the current phase's `CLAUDE.<phase>.md`, or in a component-specific `CLAUDE.<component>.md` when working within a specific component.
2. Follow the File column link to read the relevant `DEC-*.md` file.
3. Apply its enforcement rules.

Do **not** modify `*.history.md` except to append to the changelog.

### Recording, deprecating, or superseding decisions

When a significant decision, pattern, or constraint emerges, record it as a new decision. For the recording procedure, as well as deprecation and supersession, see [`decisions/PROCEDURES.md`](decisions/PROCEDURES.md).

---

## After Making Changes

Evaluate whether to:

1. **Update this file** if project-wide patterns or architecture change significantly.
2. **Update phase-specific files** (`CLAUDE.<phase>.md`) if phase-specific patterns or conventions are established.
3. **Create new instruction files** if a workflow becomes complex enough to need dedicated guidance.

Proactively suggest these updates when relevant.
