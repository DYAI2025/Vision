Phase-specific instructions for the **Code** phase. Extends [../CLAUDE.md](../CLAUDE.md).

## Purpose

This phase contains the **implementation**. Focus on clean, tested, maintainable code.

---

## Components

All five backend components share a uniform stack per [`DEC-backend-stack-python-fastapi`](../decisions/DEC-backend-stack-python-fastapi.md): Python 3.12 + FastAPI + uvicorn + Pydantic + asyncpg (where applicable) + uv (deps + venv) + pytest + httpx + ruff + mypy strict.

### whatsorga-ingest

- **Directory**: [`whatsorga-ingest/`](whatsorga-ingest/)
- **Technology**: Python 3.12 + FastAPI
- **Responsibility**: Adapter layer + normalization. Hosts one adapter per input channel (WhatsApp, voice, repo events, manual CLI) and produces channel-agnostic `input_event`s flowing into `backlog-core`. Performs the consent check at the system boundary.

### hermes-runtime

- **Directory**: [`hermes-runtime/`](hermes-runtime/)
- **Technology**: Python 3.12 + FastAPI
- **Responsibility**: Hosts the agent, its skills (routing, extraction, duplicate detection, brain-first lookup, model routing), the confidence-gate middleware, and the learning-loop. Has read access to the systems of record but no write credentials.

### backlog-core

- **Directory**: [`backlog-core/`](backlog-core/)
- **Technology**: Python 3.12 + FastAPI (DEC's Reasoning explicitly accepts a possible future supersession for `backlog-core` only if Phase-7 load tests show `REQ-PERF-ingest-latency` cannot be met in Python.)
- **Responsibility**: The event-sourced technical truth layer. Hosts the event log (Postgres), proposal pipeline, consent records, audit log, retention sweep, RTBF cascade engine, data-export tool, state-reconstruction service, and daily reconciliation job.

### gbrain-bridge

- **Directory**: [`gbrain-bridge/`](gbrain-bridge/)
- **Technology**: Python 3.12 + FastAPI
- **Responsibility**: GBrain vault read/write with schema validation, bidirectional link integrity, redaction-precondition check, weekly vault audit sweep, and the Obsidian command-palette watch script.

### kanban-sync

- **Directory**: [`kanban-sync/`](kanban-sync/)
- **Technology**: Python 3.12 + FastAPI
- **Responsibility**: Obsidian Kanban markdown file I/O. Maintains the sync-owned vs. user-owned card-frontmatter boundary; detects manual column moves and unattributed edits.

### cli

- **Directory**: [`cli/`](cli/)
- **Technology**: Python 3.12 + Typer per [`DEC-cli-stack-python-typer`](../decisions/DEC-cli-stack-python-typer.md). Distributed primarily via `uv tool install`; secondary mode is a profile-gated `cli` Compose service for in-stack invocation.
- **Responsibility**: The operator `vision` binary — source registration, RTBF, data export, review-queue CLI fallback, backup / restore, secret rotation, VPS install + smoke test, audit query, state-reconstruction preview.

<!-- Add an entry for each component/codebase -->

---

## Component Isolation

All source code, configuration, and assets for a component **must reside within that component's directory**. Specifically:

- **No code outside component directories** — never place source files, configuration files, or build artifacts in `3-code/` itself or anywhere else outside the owning component's directory.
- **No cross-component configuration** — configuration that spans multiple components should never be necessary. If such a situation arises, treat it as a potential design flaw or incorrect component separation. Stop work, notify the user with a clear description of the conflict, and propose alternative actions (e.g., refactoring responsibilities, introducing a new component, or adjusting the design).
- **Do not rename or move component directories** — the directory names listed above are fixed; renaming or relocating them breaks cross-phase references and tooling assumptions.

### Carve-out: `3-code/_common/<package>/` for declared cross-cutting utilities

Per [`DEC-shared-utility-path-deps`](../decisions/DEC-shared-utility-path-deps.md), `3-code/_common/<package>/` is the **single sanctioned location** for cross-cutting Python utilities consumed by multiple backend components (e.g., `canonical_json`, `bearer_auth`, `idempotency`, `purpose_limitation`, `subject_ref_normalization`).

- Each shared utility lives as an independent uv-managed Python package under `3-code/_common/<package>/` with its own `pyproject.toml`, `uv.lock`, tests, and CI job.
- Backend components consume it via uv path-dep (`[tool.uv.sources]` with `path = "../_common/<package>", editable = true`).
- Backend Dockerfiles use **repo root** as build context and copy both `3-code/<component>/` and `3-code/_common/` (so the path-dep resolves at build time). `docker-compose.yml` backend services use `build: { context: ., dockerfile: 3-code/<component>/Dockerfile }`.
- The carve-out applies only to **declared cross-cutting** utilities — code that is genuinely shared across the backend stack. Two-component-only sharing is still forbidden by the unmodified part of the isolation rule; refactor responsibilities or keep the code in the calling component.
- Cross-component imports between component directories are still forbidden — `from <other-component>.app import …` remains illegal regardless of `_common/`.

---

## Build Commands

Scripts and commands for each component are documented in that component's own codebase (package.json, Makefile, README, or equivalent). Check there first.

When invoking any command, apply active decisions from the component's `CLAUDE.component.md` whose trigger conditions match.

---

## Task Tracking

All development tasks are tracked in [`tasks.md`](tasks.md).

To create the initial implementation plan (phased tasks from design artifacts), run `/SDLC-implementation-plan`. This should be done after `/SDLC-decompose` and before starting any coding work.

---

## Linking to Other Phases

- Implementation follows designs in `2-design/`
- Tests verify requirements from `1-spec/`
- Infrastructure code goes in `4-deploy/`; when a coding task modifies IaC, the deploy phase instructions ([`CLAUDE.deploy.md`](../4-deploy/CLAUDE.deploy.md)) apply as well
