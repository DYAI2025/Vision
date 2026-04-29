# vision-cli

Operator CLI for `project-agent-system`. See [`CLAUDE.component.md`](CLAUDE.component.md) for full responsibility, interfaces, and applicable decisions.

**Skeleton state.** Currently exposes only `vision health` (parallel-fan-out aggregator over the 5 backend services) and `vision --version`. Subcommand groups (`vision source`, `vision audit`, `vision rtbf`, `vision export`, `vision review`, `vision state`, `vision backup`, `vision rotate`, `vision reconciliation`) are added by the corresponding Phase 2-7 tasks.

## Tech stack

Per [`DEC-cli-stack-python-typer`](../../decisions/DEC-cli-stack-python-typer.md): Python 3.12 + Typer + httpx + Pydantic + python-dotenv + Rich, managed with `uv`, tested with `pytest`, linted with `ruff`, type-checked with `mypy --strict`.

## Layout

```
3-code/cli/
├── Dockerfile                # multi-stage; runtime is python:3.12-slim, non-root
├── pyproject.toml            # runtime + dev deps, ruff/mypy/pytest config, [project.scripts] vision = "app.main:cli"
├── uv.lock                   # committed lockfile
├── .python-version           # "3.12"
├── app/
│   ├── __init__.py           # __version__
│   ├── main.py               # Typer app (`cli`); `vision health` command + global --version
│   ├── config.py             # env-driven base URL + token loader (.env discovery)
│   └── health.py             # parallel-fan-out aggregator, classifier, JSON renderer
└── tests/
    ├── test_config.py        # 7 cases: env / .env / arg precedence + walk-up + empty-token
    └── test_health.py        # 12 cases via httpx.MockTransport (no live network)
```

## Distribution

Two modes are supported in parallel — both ship the same Python package.

### A. Operator's host (primary)

```bash
uv tool install --from /path/to/repo/3-code/cli vision-cli
```

After install, `vision health` is on PATH. Operators on a Tailscale-connected laptop point at the public ingress (`VISION_BASE_URL=https://<CADDY_HOSTNAME>` or the Tailnet hostname) — see "Modes" below.

### B. In-stack (secondary)

A profile-gated `cli` service in `docker-compose.yml` (profile `cli`) lets in-stack invocation:

```bash
docker compose --profile cli run --rm cli health
docker compose --profile cli run --rm cli health --json
```

Useful for debugging from the same host as the Compose stack without installing anything on the host. The Compose service injects `VISION_BASE_URL=http://ingress-caddy` and `OPERATOR_TOKEN` from `.env`.

## Modes

`vision health` hits `<VISION_BASE_URL>/v1/health/<service>` for each of the five backend services in parallel. The path-aggregation pattern (`/v1/health/<service>` rewrites to `/v1/health` upstream) is **caddy-mode-only** — Caddy supports URL rewriting, Tailscale serve does not.

| Mode | `VISION_BASE_URL` | Notes |
|---|---|---|
| **Caddy on operator host** (primary external) | `https://<CADDY_HOSTNAME>` (e.g. `https://localhost` for the default deploy) | Skeleton works as-is; `/v1/health/<service>` aggregation is implemented in `4-deploy/ingress/Caddyfile`. |
| **In-stack via Compose `cli` service** | `http://ingress-caddy` (default in compose) | Same caddy aggregation, internal HTTP — no TLS to worry about. |
| **Tailscale on operator host** | `https://<TS_HOSTNAME>.<tailnet>.ts.net` | **Limitation**: Tailscale serve doesn't support URL rewriting, so `/v1/health/<service>` paths return 404 in this mode. Skeleton will report all services as `unreachable` / `down`. Future hardening (e.g., a `--tailscale` flag that hits each service's individual route directly) closes this gap; not in scope for this skeleton. |

## Local development

Requires [`uv`](https://docs.astral.sh/uv/). `.python-version` pins CPython 3.12.

| Command | Purpose |
|---|---|
| `uv sync --frozen` | Create / refresh `.venv/` with the locked deps. |
| `uv run --frozen pytest` | Run the test suite (no live network — uses `httpx.MockTransport`). |
| `uv run --frozen ruff check .` | Lint. |
| `uv run --frozen ruff format .` | Format. |
| `uv run --frozen mypy app` | Type-check. |
| `uv run --frozen vision --help` | Run the dev binary against your venv. |
| `VISION_BASE_URL=http://localhost uv run --frozen vision health` | Run against a local stack. |

To upgrade a dependency, edit `pyproject.toml`, run `uv lock`, commit both files, then re-run `uv sync --frozen`.

## Exit codes

`vision health`:

| Code | Meaning |
|---|---|
| 0 | Overall status `ok` (every service reports `ok`) |
| 1 | Overall status `degraded` (mixture of `ok` and `degraded`; nothing unreachable) |
| 2 | Overall status `down` (at least one service is unreachable or reports `down`) |

Future commands document their exit codes per `3-code/cli/CLAUDE.component.md` Interfaces (one column in the operator-CLI command surface table in `2-design/api-design.md`).

## Tests in CI

`.github/workflows/ci.yml` runs a `cli-test` job: `setup-uv` (cached on `uv.lock`) → `uv sync --frozen` → ruff → mypy → pytest. Mirrors the five backend per-component templates.
