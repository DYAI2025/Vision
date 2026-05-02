# DEC-shared-utility-path-deps: Trail

> Companion to `DEC-shared-utility-path-deps.md`.
> AI agents read this only when evaluating whether the decision is still
> valid or when proposing a change or supersession.

## Alternatives considered

### Option A: uv path-deps + Dockerfile context restructure (chosen)

- **Pros**:
  - Single source of truth per helper. Bug fixes land in one place.
  - Path-deps are first-class in `uv` — the lockfile pins the relative path; `uv sync --frozen` resolves it without network access; CI doesn't need a private index.
  - Each shared package gets its own ruff / mypy / pytest run, exactly mirroring the per-component pattern. Familiar shape, low cognitive cost.
  - Per-component `uv.lock` files stay independent — each backend can upgrade its non-shared deps without coordinating across the workspace.
  - Editable mode means a developer working on `whatsorga-ingest` who needs to change `canonical_json` edits the file in place and the change is immediately picked up.
- **Cons**:
  - One-time structural cost: 5 backend Dockerfiles change build context, 5 backend `pyproject.toml` files gain a path-dep declaration, 5 backend `docker-compose.yml` blocks change `build:` shape.
  - `docker build -f ./3-code/<component>/Dockerfile .` is more verbose than `docker build ./3-code/<component>` — operators have to learn the new shape (mitigated by `docker compose build` hiding it).
  - All five backends carry all of `_common/` in their build context even when they only consume one helper. Layer cost is small in practice (`canonical_json` is ~50 LOC; full `_common/` even with 5 helpers will be a few thousand LOC), but it is technically waste.

### Option B: Per-component vendoring with CI byte-identity check

- **Pros**:
  - Zero changes to Dockerfiles, `docker-compose.yml`, or `pyproject.toml` shape — keeps the existing per-component build context and lockfile pattern intact.
  - Each component's deploy artifact has only the bytes it strictly needs.
  - No new "where does this code live" rule beyond the existing component-isolation rule.
- **Cons**:
  - Estimated **~3.2k LOC of duplication** when all five planned helpers land (5 helpers × 5 components averaging ~120 LOC each, including tests). Every fix touches 5 files; every fix must update 5 sets of tests.
  - CI gains 5 byte-identity check jobs (one per shared helper) to detect drift. False sense of safety: byte-identity checks fail when files diverge, but the moment you intentionally need a divergence — say, a hotfix in one component before the others are updated — the check becomes a chore to silence.
  - The "byte-identity" guarantee is only as strong as the canonical source's discipline. There is no canonical source under vendoring — every copy is equally authoritative — so reviewers have to manually pick the "right" version.
  - Onboarding cost: every new contributor learns "if you fix `canonical_json`, you're fixing it in 5 places."

### Option C: uv workspaces

- **Pros**:
  - Single workspace lockfile gives consistent dep pins across all components. Useful for security-update sweeps where you want to bump a transitive dep in one place.
  - Workspace member cross-imports are trivial — `[tool.uv.sources]` declarations are not needed inside the workspace.
- **Cons**:
  - **Conflicts with the per-component `uv.lock` pattern** that all 6 component skeletons already established. Migrating to workspaces would mean deleting 6 lockfiles, regenerating one root lockfile, and re-validating every component's CI job.
  - Per-component lockfile independence is intentional: each backend can adopt a new dep version on its own cadence, without forcing a coordinated bump across the other 4 backends and the CLI.
  - Workspaces couple deploy artifacts more than wanted: a Dockerfile for one component would either ship the full workspace lockfile (over-broad) or carry a derived per-member lockfile (extra tooling).
  - Operator mental model shifts from "each component is an independent project" to "all components are members of one workspace" — a non-trivial change to undo if it doesn't fit.

## Reasoning

The decision boils down to a multi-helper amortization question. With one helper, vendoring's cost is low (~120 duplicated LOC, 4 fix sites). With five planned helpers, vendoring becomes **the dominant maintenance tax** — every fix is a 5-file change, and CI byte-identity checks are sticky overhead that adds friction without preventing intentional drift.

uv path-deps are the standard Python-mono-repo pattern for this exact shape — small number of consumers (5), small number of shared modules (5 planned), all in one repo, all built and tested together. The one-time structural cost (5 Dockerfile changes + 5 compose-block changes + 5 pyproject.toml additions) is paid once now; every subsequent helper is a sub-30-minute add: create the package directory, add the path-dep line to each consumer's `pyproject.toml`, done. No structural change required for helpers #2–5.

Workspaces are over-engineered for this shape — they solve a "many components share many deps" problem this project does not have. The per-component lockfile pattern is the right granularity for a 2-person team operating 6 deploy units.

The component-isolation rule needs a narrow carve-out, not removal — `_common/` is the **only** sanctioned location for cross-cutting utilities. Two-component-only sharing is still forbidden and should refactor responsibilities or live in the calling component. This keeps the rule's intent intact (no accidental cross-component coupling) while permitting declared cross-cutting infrastructure.

Trade-offs explicitly accepted:
- We accept the one-time structural cost of changing 5 Dockerfiles + 5 compose entries now, in exchange for zero structural cost on helpers #2–5.
- We accept that all 5 backends copy all of `_common/` into their build context, even when they consume only one helper. Layer cost is small; per-Dockerfile drift risk is high if we tried to pick-and-choose, and `_common/` is intentionally small.
- We accept that operators run `docker build -f ./3-code/<component>/Dockerfile .` rather than `docker build ./3-code/<component>`. Mitigation: nobody runs `docker build` directly — the canonical path is `docker compose build`, which hides the flag.

Conditions that would invalidate this reasoning:
- If `_common/` grows to >5 helpers averaging >500 LOC each, the "small layer cost" argument weakens and per-Dockerfile selectivity may become worth the drift risk.
- If two backends start to need different versions of the same helper (semver divergence), path-deps stop being enough and we need real packaging (PyPI / private index).
- If the team grows and a workspace-wide unified lockfile becomes operationally cheap, Option C becomes viable again.

## Human involvement

**Type**: ai-proposed/human-approved

**Notes**: AI proposed three options (vendoring, path-deps, workspaces) with full trade-off analysis when picking up `TASK-canonical-json-helper`. User approved Option 2 (path-deps + Dockerfile context restructure) on 2026-04-29 with "go yes," confirming the default of doing the full restructure (5 Dockerfiles + 5 compose entries) now so subsequent helpers have zero structural cost. Vincent's concurrence is part of the same outstanding tiebreaker package noted in `CLAUDE.md` Spec → Design carry-overs.

## Changelog

| Date | Change | Involvement |
|------|--------|-------------|
| 2026-04-29 | Initial decision | ai-proposed/human-approved |
