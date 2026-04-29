# project-agent-system

Local, agent-driven project management system for two named human collaborators (Vincent and Ben). Multi-channel inputs (WhatsApp, voice, repository events, manual CLI) flow through a normalization pipeline and become structured, traceable project work via a supervised agent. Consent-based ingestion only, no platform bypass, no required cloud LLM dependency, deployable to any VPS via Docker Compose.

See [`CLAUDE.md`](CLAUDE.md) → `## Project Overview` for the full project intent and architectural backbone.

## Status

**Phase: Code (execution-ready).** The implementation plan lives in [`3-code/tasks.md`](3-code/tasks.md) — 7 phases, 105 tasks. Execution begins at Phase 1: Bootstrap & Deployment Foundation.

## Repository structure

```
.
├── CLAUDE.md           # Root AI instructions and project overview — start here
├── 1-spec/             # WHAT and WHY — stakeholders, goals, requirements, constraints, assumptions
├── 2-design/           # HOW — architecture, data model, API design
├── 3-code/             # BUILD — 6 per-component directories + tasks.md
├── 4-deploy/           # SHIP — runbooks
├── decisions/          # DEC-* records (active + history)
└── .github/workflows/  # CI
```

## Components

See [`2-design/architecture.md`](2-design/architecture.md) for the full system architecture and [`3-code/CLAUDE.code.md`](3-code/CLAUDE.code.md) for component pointers.

| Component | Responsibility |
|---|---|
| [`3-code/whatsorga-ingest/`](3-code/whatsorga-ingest/) | Channel adapters (WhatsApp, voice, repo, manual CLI) + normalization + consent check at boundary |
| [`3-code/hermes-runtime/`](3-code/hermes-runtime/) | Agent + skills (routing, extraction, duplicate detection, brain-first lookup) + confidence-gate middleware + learning loop |
| [`3-code/backlog-core/`](3-code/backlog-core/) | Event store (Postgres) + proposal pipeline + audit log + RTBF cascade + retention sweep + state reconstruction |
| [`3-code/gbrain-bridge/`](3-code/gbrain-bridge/) | GBrain vault r/w + schema validation + bidirectional links + redaction precondition + Obsidian command-palette watch script |
| [`3-code/kanban-sync/`](3-code/kanban-sync/) | Obsidian Kanban file I/O + sync-owned vs. user-owned card-frontmatter boundary |
| [`3-code/cli/`](3-code/cli/) | The operator `vision` binary — source registration, RTBF, data export, backup/restore, secret rotation, install, smoke test |

Per-component technology choices (Python / Go / etc.) are deferred to Code-phase decisions recorded as `DEC-*` artifacts when the first implementation task per component is picked up.

## How to navigate

- **What is this and why** → [`CLAUDE.md`](CLAUDE.md) `## Project Overview`.
- **Specification (what we're building)** → [`1-spec/CLAUDE.spec.md`](1-spec/CLAUDE.spec.md) — index linking goals, user stories, requirements, constraints, assumptions.
- **Design (how we're building)** → [`2-design/architecture.md`](2-design/architecture.md), [`2-design/data-model.md`](2-design/data-model.md), [`2-design/api-design.md`](2-design/api-design.md).
- **Tasks (what's next)** → [`3-code/tasks.md`](3-code/tasks.md), Execution Plan section.
- **Decisions (why each call was made)** → [`decisions/`](decisions/) — every `DEC-*.md` carries source, scope, and enforcement; companion `*.history.md` files hold alternatives + reasoning.

## License

License pending — to be chosen during repository finalization. The bootstrapping scaffold (the `AI SDLC Scaffold`) is licensed under Apache 2.0; the project's own code may adopt the same or a different license.
