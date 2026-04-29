# DEC-cli-stack-python-typer: Trail

> Companion to `DEC-cli-stack-python-typer.md`.
> AI agents read this only when evaluating whether the decision is still
> valid or when proposing a change or supersession.

## Alternatives considered

### Option A: Python 3.12 + Typer (chosen)

- **Pros**:
  - Language uniformity across all 6 components (5 backend + CLI), reducing the team's cognitive surface to one runtime, one venv pattern, one test runner, one lint/format toolchain.
  - Pydantic schema reuse: `InputEvent`, `Proposal`, audit-event payloads, etc. can be imported directly into the CLI without re-typing in another language. Avoids divergence risk on shared contracts.
  - Typer is FastAPI's CLI counterpart — same author, same idiom, minimal new concepts for a team already using FastAPI extensively.
  - `uv tool install` is a one-line operator install: `uv tool install --from <path-or-url> vision-cli`. Operator gets a globally-callable `vision` script with the venv isolated automatically.
  - In-stack runnability via a profile-gated `cli` Compose service satisfies the "no host install at all" use case as a secondary distribution mode without extra implementation cost.
  - asyncio + httpx make parallel-fan-out commands like `vision health` cheap; this is the dominant operation pattern (most commands query 1-N services).
- **Cons**:
  - Operator needs Python 3.12 OR uv on the host. uv install is one curl line; Python 3.12 is widely available. Insignificant friction.
  - Cold start ~150 ms (Python interpreter boot + Typer + httpx imports). For a human-driven CLI this is invisible. Would matter only if the CLI were invoked in a tight loop, which is not the use case.
  - Not a single binary. Operators wanting a self-contained executable must use `pyinstaller` or `shiv` as a manual step, which is supported but not the default path.

### Option B: Go + Cobra (single fat binary)

- **Pros**:
  - True single-binary distribution: one HTTP download, one chmod, ready to run on any host with no Python or uv.
  - Sub-10ms cold start.
  - Strong CLI ecosystem: cobra for command structure, viper for config, well-trodden patterns for env-driven config.
- **Cons**:
  - Different language from the 5 backend services — no Pydantic schema reuse. Every shared type (`InputEvent`, `Proposal`, etc.) must be hand-translated to Go structs and kept in sync. Real divergence risk over a 7-phase plan with 20+ commands.
  - Two CI lanes: setup-go for the CLI, setup-uv for the backend. Doubles the maintenance surface on every uv / Go version bump.
  - Two languages for a 2-person team (Vincent + Ben) to maintain. Per `STK-ben` "low ops overhead" interest, this is a real cost.
  - Cross-compile + GitHub Releases distribution adds setup steps (GoReleaser, signed binaries, version policy) that we don't have today.
  - The "single binary on a fresh VPS" scenario is largely moot for our deployment model: the VPS already has Docker (running the Compose stack); installing Python or uv is a strictly smaller ask than installing a new tool, and the operator typically administers from their laptop where they already have a development toolchain.

### Option C: Python in-Compose only (no host install)

A degenerate case of A: ship the CLI as a Compose service only, invoked via `docker compose run --rm cli vision <subcommand>`.

- **Pros**:
  - Zero install friction beyond Docker, which is already required.
  - No `uv tool install` step on the operator's machine.
- **Cons**:
  - UX is awkward: `docker compose run --rm cli vision health` is verbose every time vs. `vision health`.
  - Operator can't run from any shell — must be in a directory with the project's `docker-compose.yml`.
  - Tailscale-host operator can't run from their laptop; must SSH into the VPS first.

This is included in option A as a **secondary** distribution mode (the `cli` Compose service), not as the primary mode. Best of both worlds: laptop operators do `uv tool install`; in-stack debugging uses `docker compose run`.

## Reasoning

Three factors tip the choice to Python:

1. **Schema reuse.** 20+ CLI commands × shared backend models (`InputEvent`, `Proposal`, `ConsentRecord`, audit-event shapes, etc.) = high duplication cost in any non-Python option. Python keeps the contract single-sourced.
2. **Toolchain uniformity for a 2-person team.** One runtime, one venv pattern, one CI job template per component, one set of formatters and linters. Mixing Go would double the operational surface for marginal end-user gain.
3. **The "single binary" advantage of Go is largely moot for this deployment model.** The operator already has Docker (compulsory for the Compose stack). Adding Python (or uv, which is a single static binary) is a smaller incremental ask than adopting a second language for the team.

Trade-offs explicitly accepted:

- We accept Python's ~150ms cold start. CLI is human-driven; latency is invisible.
- We accept that `uv tool install` (one line) is a slightly heavier operator install than copying a Go binary. The win is single-language across the project.
- We accept the dual distribution surface (uv-installed laptop CLI + Compose service for in-stack invocation). Both are needed for different operator scenarios.

Conditions that would invalidate this reasoning:

- The operator base grows beyond Vincent + Ben to include users who explicitly cannot or will not install Python / uv (e.g., distribution to non-technical operators on locked-down hosts). At that point, evaluate cross-compiling the Python CLI via `shiv` / `pyinstaller` first; only switch to Go if those don't satisfy.
- Performance load tests (Phase 7) show that Python-CLI fan-out latency is unacceptable for some emergent power-user workflow (e.g., running `vision audit query` in a tight scripted loop). At that point, the bottleneck is almost certainly server-side latency, not Python startup, so the remediation is on the backend side.

## Human involvement

**Type**: ai-proposed/human-approved

**Notes**: AI proposed Python 3.12 + Typer with full trade-off analysis when picking up `TASK-cli-skeleton` (the second per-component tech-stack decision point after `DEC-backend-stack-python-fastapi`). User approved with "go yes" on 2026-04-29, accepting all three sub-questions in the proposal: (1) adopt Python+Typer, (2) include the optional Compose `cli` service, (3) caddy-mode-only with documented tailscale gap. Vincent's concurrence on this decision is part of the same outstanding tiebreaker package noted in `CLAUDE.md` Spec → Design carry-overs (no objection received as of this date).

## Changelog

| Date | Change | Involvement |
|------|--------|-------------|
| 2026-04-29 | Initial decision | ai-proposed/human-approved |
