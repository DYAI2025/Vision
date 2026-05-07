# project-agent-system

Local, agent-driven project management system for two named human collaborators (Vincent and Ben). Multi-channel inputs (WhatsApp, voice, repository events, manual CLI) flow through a normalization pipeline and become structured, traceable project work via a supervised agent. Consent-based ingestion only, no platform bypass, no required cloud LLM dependency, deployable to any VPS via Docker Compose.

See [`CLAUDE.md`](CLAUDE.md) → `## Project Overview` for the full project intent and architectural backbone.

## Status

**Phase: Code — Phase 1 Bootstrap complete; Phase 2 in progress.** All 6 original component skeletons shipped (whatsorga-ingest, hermes-runtime, backlog-core, gbrain-bridge, kanban-sync, cli); install + smoke scripts ready; a Railway-ready frontend MVP cockpit now exists for service health and manual semantic-intake preview. The implementation plan lives in [`3-code/tasks.md`](3-code/tasks.md) — 7 phases, 107 tasks.

## Install

Bring up the full Compose stack on a fresh Docker-capable VPS (4 vCPU / 8 GB / ≥50 GB disk recommended):

```bash
git clone https://github.com/DYAI2025/Vision.git && cd Vision
cp .env.example .env && $EDITOR .env       # generate tokens with: openssl rand -hex 32
bash scripts/install_vps.sh                 # ~10 min on a fresh host
bash scripts/smoke_test.sh                  # Phase-1 healthcheck-only verification
```

Full step-by-step procedure, prerequisites, manual verification scenarios, and troubleshooting are in **[`4-deploy/runbooks/install.md`](4-deploy/runbooks/install.md)** — the canonical install runbook.

After install, the operator CLI is `vision`:

```bash
# Install uv first if you don't have it:
command -v uv >/dev/null || curl -LsSf https://astral.sh/uv/install.sh | sh
uv tool install --from ./3-code/cli vision-cli
vision health
```

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
| [`3-code/frontend/`](3-code/frontend/) | Railway-ready browser cockpit for backend health, architecture visibility, and manual semantic communication-to-Evermemos intake preview |

Tech-stack conventions (recorded as Code-phase decisions during Phase 1):

- 5 backend components: **Python 3.12 + FastAPI** per [`DEC-backend-stack-python-fastapi`](decisions/DEC-backend-stack-python-fastapi.md).
- `cli`: **Python 3.12 + Typer** per [`DEC-cli-stack-python-typer`](decisions/DEC-cli-stack-python-typer.md).
- Dependency / venv management: `uv` (one venv per component, `.venv/` ignored).
- Tests: pytest. Lint: ruff. Type check: mypy strict. CI runs all three on every per-component test job.


## Frontend MVP cockpit

A browser frontend is available in [`3-code/frontend/`](3-code/frontend/). It can be deployed as a Railway service with the service root set to `3-code/frontend`, uses `VITE_API_BASE_URL` to call the existing ingress, and currently focuses on the product slice that is already useful before the backend is complete: service health visibility plus local preparation of semantic communication-summary candidates for future `/v1/inputs` ingestion. See [`docs/reviews/2026-05-07-architecture-mvp-frontend-analysis.md`](docs/reviews/2026-05-07-architecture-mvp-frontend-analysis.md) for the current architecture/UI/backend evaluation and MVP sequence.

## How to navigate

- **What is this and why** → [`CLAUDE.md`](CLAUDE.md) `## Project Overview`.
- **Specification (what we're building)** → [`1-spec/CLAUDE.spec.md`](1-spec/CLAUDE.spec.md) — index linking goals, user stories, requirements, constraints, assumptions.
- **Design (how we're building)** → [`2-design/architecture.md`](2-design/architecture.md), [`2-design/data-model.md`](2-design/data-model.md), [`2-design/api-design.md`](2-design/api-design.md).
- **Tasks (what's next)** → [`3-code/tasks.md`](3-code/tasks.md), Execution Plan section.
- **Decisions (why each call was made)** → [`decisions/`](decisions/) — every `DEC-*.md` carries source, scope, and enforcement; companion `*.history.md` files hold alternatives + reasoning.

## License

License pending — to be chosen during repository finalization. The bootstrapping scaffold (the `AI SDLC Scaffold`) is licensed under Apache 2.0; the project's own code may adopt the same or a different license.
