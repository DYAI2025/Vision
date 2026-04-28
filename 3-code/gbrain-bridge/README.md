# gbrain-bridge

GBrain vault read/write + Obsidian command-palette watch script for `project-agent-system`. See [`CLAUDE.component.md`](CLAUDE.component.md) for full responsibility, interfaces, and applicable decisions.

**Skeleton state.** Currently exposes only `GET /v1/health` (with a vault-readability check) plus the `app.vault` filesystem primitive. Page CRUD, schema validation, bidirectional links, redaction precondition, RTBF cascade, the Obsidian command-palette watch script, and the weekly vault audit sweep land in subsequent Phase 4 / Phase 5 / Phase 6 / Phase 7 tasks.

## Tech stack

Per [`DEC-backend-stack-python-fastapi`](../../decisions/DEC-backend-stack-python-fastapi.md): Python 3.12 + FastAPI + uvicorn + Pydantic, managed with `uv`, tested with `pytest`, linted with `ruff`, type-checked with `mypy --strict`. No DB driver yet — the future Postgres consumers (vault audit sweep results, etc.) will be `backlog-core`'s job.

## Layout

```
3-code/gbrain-bridge/
├── Dockerfile                # multi-stage; runtime is python:3.12-slim, non-root
├── pyproject.toml            # runtime + dev deps, ruff/mypy/pytest config
├── uv.lock                   # committed lockfile — uv sync --frozen is reproducible
├── .python-version           # "3.12"
├── app/
│   ├── __init__.py           # exposes __version__
│   ├── main.py               # FastAPI app + GET /v1/health (vault-aware)
│   └── vault.py              # VAULT_PATH config + is_readable primitive
└── tests/
    ├── test_health.py        # 7 health-endpoint cases (200/503, shape, vault states)
    └── test_vault.py         # 7 cases for vault_path() + is_readable()
```

## Vault layer & health

The vault is a Docker volume mounted at `VAULT_PATH` (default: `/vault`) by `docker-compose.yml`. `app.vault.is_readable(path)` returns True iff the path exists, is a directory, and the process can iterate it. Never raises — health-probe semantics fold permission errors, missing paths, and "is a file not a dir" into False.

`GET /v1/health`:
- Calls `is_readable(vault_path())`.
- On success: `{"status": "ok", "checks": {"vault": "ok"}}` with HTTP 200.
- On failure: `{"status": "degraded", "checks": {"vault": "down"}}` with HTTP 503 — Compose marks the container unhealthy.

`<VAULT_PATH>/Kanban/` is **owned by `kanban-sync`**, not this component. Future page CRUD must explicitly skip that subtree.

## Local development

Requires [`uv`](https://docs.astral.sh/uv/). `.python-version` pins CPython 3.12.

| Command | Purpose |
|---|---|
| `uv sync --frozen` | Create / refresh `.venv/` with the locked deps. |
| `uv run --frozen pytest` | Run the test suite (uses pytest's `tmp_path` — no real `/vault` needed). |
| `uv run --frozen ruff check .` | Lint. |
| `uv run --frozen ruff format .` | Format. |
| `uv run --frozen mypy app` | Type-check. |
| `VAULT_PATH=/path/to/local/vault uv run --frozen uvicorn app.main:app --reload --port 8000` | Run the dev server. |

To upgrade a dependency, edit `pyproject.toml`, run `uv lock`, commit both files, then re-run `uv sync --frozen`.

## Container build & run

```bash
# from repo root
docker compose build gbrain-bridge
docker compose up -d gbrain-bridge
docker compose exec gbrain-bridge python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:8000/v1/health',timeout=2).read().decode())"
```

The healthcheck (in `docker-compose.yml`) uses the same Python-stdlib one-liner.

## Tests in CI

`.github/workflows/ci.yml` runs a `gbrain-bridge-test` job: `setup-uv` (cached on `uv.lock`) → `uv sync --frozen` → ruff → mypy → pytest. Mirrors the previous component templates.
