# backlog-core

Event-sourced technical truth layer for `project-agent-system`. See [`CLAUDE.component.md`](CLAUDE.component.md) for full responsibility, interfaces, and applicable decisions.

**Skeleton state.** This component currently exposes only `GET /v1/health` (now with a real Postgres readiness check) plus the connection-pool primitive in `app.db`. The event log schema, proposal pipeline, consent records, hash-chained audit log, retention sweep, RTBF cascade engine, data-export tool, state-reconstruction service, and daily reconciliation all land in subsequent Phase 2 / Phase 3 / Phase 4 / Phase 6 / Phase 7 tasks.

## Tech stack

Per [`DEC-backend-stack-python-fastapi`](../../decisions/DEC-backend-stack-python-fastapi.md): Python 3.12 + FastAPI + uvicorn + Pydantic + asyncpg, managed with `uv`, tested with `pytest`, linted with `ruff`, type-checked with `mypy --strict`.

Postgres backend per [`DEC-postgres-as-event-store`](../../decisions/DEC-postgres-as-event-store.md). Driver: asyncpg (pinned `>=0.30,<0.31`).

## Layout

```
3-code/backlog-core/
├── Dockerfile                # multi-stage; runtime is python:3.12-slim, non-root
├── pyproject.toml            # runtime + dev deps, ruff/mypy/pytest config
├── uv.lock                   # committed lockfile — uv sync --frozen is reproducible
├── .python-version           # "3.12"
├── app/
│   ├── __init__.py           # exposes __version__
│   ├── main.py               # FastAPI app + GET /v1/health (DB-aware)
│   └── db.py                 # asyncpg pool lifecycle + ping primitive + get_pool dep
└── tests/
    ├── conftest.py           # FakePool fixture (no real Postgres needed for unit tests)
    ├── test_health.py        # 6 health-endpoint cases (ok, degraded, shape, auth, 404)
    └── test_db.py            # 5 cases for _database_url + ping
```

## Connection pool & health

The pool is created at FastAPI startup via `app.db.lifespan` (an `@asynccontextmanager`-decorated async generator), stored on `app.state.pool`, and closed on shutdown.

`GET /v1/health`:
- Runs `SELECT 1` through `app.db.ping(pool)`.
- On success: `{"status": "ok", "version": "...", "checks": {"postgres": "ok"}}`.
- On any failure (connection refused, timeout, query exception): `{"status": "degraded", "version": "...", "checks": {"postgres": "down"}}`.

`ping()` never raises; it always returns a bool. This keeps `/v1/health` resilient to transient Postgres flakiness — the operator sees `degraded`, not a 500.

`DATABASE_URL` is **required** at startup. If unset, `_database_url()` raises `RuntimeError` so `docker compose up` fails fast per `REQ-MNT-env-driven-config`.

## Local development

Requires [`uv`](https://docs.astral.sh/uv/). `.python-version` pins CPython 3.12.

| Command | Purpose |
|---|---|
| `uv sync --frozen` | Create / refresh `.venv/` with the locked deps. |
| `uv run --frozen pytest` | Run the test suite (no Postgres required — uses `FakePool`). |
| `uv run --frozen ruff check .` | Lint. |
| `uv run --frozen ruff format .` | Format. |
| `uv run --frozen mypy app` | Type-check. |
| `DATABASE_URL=postgres://… uv run --frozen uvicorn app.main:app --reload --port 8000` | Run the dev server (needs a Postgres reachable at the URL). |

To upgrade a dependency, edit `pyproject.toml`, run `uv lock`, commit both files, then re-run `uv sync --frozen`.

## Container build & run

```bash
# from repo root
docker compose build backlog-core
docker compose up -d postgres backlog-core
docker compose exec backlog-core python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:8000/v1/health',timeout=2).read().decode())"
```

`backlog-core`'s compose entry depends on `postgres` with `condition: service_healthy`, so the pool will see a ready Postgres when uvicorn comes up.

## Tests in CI

`.github/workflows/ci.yml` runs a `backlog-core-test` job: `setup-uv` (cached on `uv.lock`) → `uv sync --frozen` → ruff → mypy → pytest. Mirrors the `whatsorga-ingest-test` / `hermes-runtime-test` template.
