# DEC-cli-stack-python-typer: Python 3.12 + Typer for the operator CLI

**Status**: Active

**Category**: Convention

**Scope**: cli (`3-code/cli/`)

**Source**: n/a — defers from [`DEC-backend-stack-python-fastapi`](DEC-backend-stack-python-fastapi.md) which explicitly puts the CLI's tech stack out of scope

**Last updated**: 2026-04-29

## Context

The `cli` component is the operator's primary surface for transactional / high-stakes operations: source registration / consent management, RTBF cascade, data-subject export, audit query, state-reconstruction preview, backup / restore, secret rotation, and aggregated health. The implementation plan defines 20+ commands across Phases 1-7, each calling backend HTTP endpoints. Per [`3-code/cli/CLAUDE.component.md`](../3-code/cli/CLAUDE.component.md): "Technology: TBD per Code-phase decision (Go for single-binary distribution, or Python matching backend services)."

`DEC-backend-stack-python-fastapi`'s rationale (uniform Python across the 5 backend services for cross-cutting utility amortization) does not directly extend to the CLI because the CLI is a runtime peer, not a library consumer. The stack choice for the CLI is therefore independent and is made now, when the first per-component task lands.

## Decision

The `cli` component uses **Python 3.12** with the following stack:

| Concern | Choice |
|---|---|
| Runtime | Python 3.12 (Docker base: `python:3.12-slim`) |
| CLI framework | **Typer** (FastAPI's CLI counterpart; type-hint-driven; integrates Rich for output) |
| HTTP client | httpx (sync mode by default; `asyncio.gather` for parallel-fan-out commands like `vision health`) |
| Validation / models | Pydantic v2 (shared with backend schemas where applicable) |
| Distribution | **Primary**: `uv tool install` from the repo on the operator's host. **Secondary**: a profile-gated `cli` service in `docker-compose.yml` for in-stack invocation via `docker compose run --rm cli vision <subcommand>`. |
| Dependency / venv manager | `uv` |
| Test runner | pytest + Typer's `CliRunner` (from `typer.testing`) + `httpx.MockTransport` for HTTP isolation |
| Linter / formatter | ruff (same config as backend) |
| Type checker | mypy strict |
| Console-script entry point | `vision = "app.main:cli"` in `[project.scripts]` |

The package source layout mirrors the backend components (`app/` package, `tests/` at repo root) for toolchain uniformity even though `app/` is an unusual name for a CLI package — consistency with the 5 backend skeletons outweighs CLI-specific naming convention.

## Enforcement

### Trigger conditions

- **Code phase**: any task that creates or modifies source code, build configuration, or test infrastructure inside `3-code/cli/`. This includes the eight Phase 2-7 CLI tasks (`TASK-cli-source-commands`, `TASK-cli-audit-commands`, `TASK-cli-manual-input`, `TASK-cli-rtbf`, `TASK-cli-export`, `TASK-cli-review-commands`, `TASK-cli-state-preview`, `TASK-cli-backup-restore`, `TASK-cli-rotate`, `TASK-cli-reconciliation-run`).

### Required patterns

- Per-component layout (rooted at `3-code/cli/`):
  ```
  Dockerfile
  pyproject.toml          # runtime + dev deps + tool config
  uv.lock                 # committed lockfile
  .python-version         # contains "3.12"
  app/                    # importable package
    __init__.py
    main.py               # Typer app instance + global flags + subcommand registration
    config.py             # env / .env loading; base URL + token discovery
    health.py             # `vision health` aggregator (this skeleton task)
    ...                   # one module per command group as Phase 2+ tasks land
  tests/                  # pytest test root
    __init__.py
    test_*.py
  README.md
  .dockerignore
  .gitignore
  ```
- `pyproject.toml` declares runtime deps (`typer`, `httpx`, `pydantic`, `python-dotenv` for `.env` loading), dev deps (`pytest`, `httpx`-with-test-utilities, `ruff`, `mypy`), and a `[project.scripts]` entry mapping `vision` to the Typer app.
- `pyproject.toml` configures `[tool.ruff]`, `[tool.mypy]` strict mode, and `[tool.pytest.ini_options]`.
- Subcommand modules use Typer's `app.add_typer(subapp, name="…")` pattern (e.g., `vision source register` → a `source_app` registered under the root). Skeleton has only `vision health` as a flat command.
- Output: human-readable by default (Rich tables / colored status), JSON via `--json` flag per `3-code/cli/CLAUDE.component.md` Interfaces. Skeleton implements the `--json` flag for `vision health`.
- Auth: `OPERATOR_TOKEN` read from env (or from `.env` if present) per [`DEC-service-auth-bearer-tokens`](DEC-service-auth-bearer-tokens.md). Token values are never logged.
- Idempotency: each invocation that mutates server state generates a fresh UUID4 and passes it via `Idempotency-Key` header per [`DEC-idempotency-keys`](DEC-idempotency-keys.md). Skeleton has no mutations yet.
- Pagination: list commands paginate to completion before printing (or stream pages to stdout under a `--stream` flag) per [`DEC-cursor-pagination-and-event-stream-conventions`](DEC-cursor-pagination-and-event-stream-conventions.md). Skeleton has no list commands yet.

### Required checks

1. `uv lock --check` (or `uv sync --frozen`) must succeed in CI.
2. `uv run --frozen ruff check .` and `uv run --frozen mypy app` must pass before any `cli` task is `Done`.
3. `uv run --frozen pytest -q` must pass; commands that hit HTTP endpoints must be tested via `httpx.MockTransport` with no real network calls.
4. Distribution test: `uv tool install --from . vision-cli` (or equivalent) must succeed against the committed source; after install, `vision --help` lists the registered commands. (Not enforced in CI for the skeleton — verified manually in Phase 1 manual testing.)

### Prohibited patterns

- Re-implementing CLI commands in another language without first superseding this decision per `decisions/PROCEDURES.md`.
- Logging token values (even in debug mode). Use a redaction helper if a token must appear in a structured log.
- Hardcoding service URLs. All endpoint construction goes through `app.config` to read `VISION_BASE_URL` (or equivalent) from env.
- Synchronous serial fan-out for commands that legitimately query multiple services (e.g., `vision health` MUST use `asyncio.gather` to query the 5 services in parallel — not 5 sequential blocking calls).
- Importing CLI code from any backend service or vice versa. The CLI is a separate component; it talks to backends only over HTTP.
