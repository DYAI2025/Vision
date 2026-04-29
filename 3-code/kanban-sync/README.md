# kanban-sync

Obsidian Kanban file I/O + sync-vs-edit boundary detection for `project-agent-system`. See [`CLAUDE.component.md`](CLAUDE.component.md) for full responsibility, interfaces, and applicable decisions.

**Skeleton state.** Currently exposes only `GET /v1/health` (with a Kanban-subtree writability check) plus the `app.kanban` filesystem primitive. Card CRUD, sync-vs-edit boundary detection, manual column-move attribution, the periodic `POST /v1/sync` trigger, and the RTBF cascade endpoint land in subsequent Phase 4 / Phase 5 tasks.

## Tech stack

Per [`DEC-backend-stack-python-fastapi`](../../decisions/DEC-backend-stack-python-fastapi.md): Python 3.12 + FastAPI + uvicorn + Pydantic, managed with `uv`, tested with `pytest`, linted with `ruff`, type-checked with `mypy --strict`. No DB driver yet — the future event emissions (`kanban.user_edit`, `unattributed_edit`) flow to `backlog-core` via HTTP per `DEC-direct-http-between-services`.

## Layout

```
3-code/kanban-sync/
├── Dockerfile                # multi-stage; runtime is python:3.12-slim, non-root
├── pyproject.toml            # runtime + dev deps, ruff/mypy/pytest config
├── uv.lock                   # committed lockfile — uv sync --frozen is reproducible
├── .python-version           # "3.12"
├── app/
│   ├── __init__.py           # exposes __version__
│   ├── main.py               # FastAPI app + GET /v1/health (Kanban-subtree-aware)
│   └── kanban.py             # VAULT_PATH + KANBAN_SUBTREE config + is_writable
└── tests/
    ├── test_health.py        # 8 health-endpoint cases (200/503, shape, subtree states)
    └── test_kanban.py        # 11 cases for path config + writability primitive
```

## Vault / Kanban-subtree boundary

This component is the **only** writer to the Kanban subtree. The boundary is enforced by configuration and reviewed in code:

| Path | Read | Write | Owner |
|------|------|-------|-------|
| `<VAULT_PATH>/` (default `/vault/`) | ✅ kanban-sync (for project-page link resolution) | ❌ never | `gbrain-bridge` (excluding the Kanban subtree) |
| `<KANBAN_SUBTREE>/` (default `/vault/Kanban/`) | ✅ kanban-sync | ✅ kanban-sync only | kanban-sync |

`gbrain-bridge`'s component instructions explicitly carve out the Kanban subtree from its own write path. Future kanban-sync tasks must not write outside `<KANBAN_SUBTREE>/`.

`app.kanban.is_writable(path)` returns True iff the path exists, is a directory, and the process can read+write it. Never raises — health-probe semantics fold permission errors / missing paths / "is a file not a dir" into False.

`GET /v1/health`:
- Calls `is_writable(kanban_subtree())`.
- On success: `{"status": "ok", "checks": {"kanban_subtree": "ok"}}` with HTTP 200.
- On failure: `{"status": "degraded", "checks": {"kanban_subtree": "down"}}` with HTTP 503 — Compose marks the container unhealthy.

Note: the skeleton does **not** auto-create the Kanban subtree. The operator (or a future card-CRUD task) is responsible for ensuring `<KANBAN_SUBTREE>/` exists. On a fresh deployment with an empty `vault` Docker volume, the container will report `degraded` until the directory is created — by design, so misconfiguration is visible rather than silent.

## Local development

Requires [`uv`](https://docs.astral.sh/uv/). `.python-version` pins CPython 3.12.

| Command | Purpose |
|---|---|
| `uv sync --frozen` | Create / refresh `.venv/` with the locked deps. |
| `uv run --frozen pytest` | Run the test suite (uses pytest's `tmp_path` — no real Kanban subtree needed). |
| `uv run --frozen ruff check .` | Lint. |
| `uv run --frozen ruff format .` | Format. |
| `uv run --frozen mypy app` | Type-check. |
| `KANBAN_SUBTREE=/path/to/Kanban uv run --frozen uvicorn app.main:app --reload --port 8000` | Run the dev server. |

To upgrade a dependency, edit `pyproject.toml`, run `uv lock`, commit both files, then re-run `uv sync --frozen`.

## Container build & run

```bash
# from repo root — make sure the Kanban subtree exists in the vault volume first
docker compose run --rm gbrain-bridge mkdir -p /vault/Kanban
docker compose build kanban-sync
docker compose up -d kanban-sync
docker compose exec kanban-sync python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:8000/v1/health',timeout=2).read().decode())"
```

The healthcheck (in `docker-compose.yml`) uses the same Python-stdlib one-liner.

## Tests in CI

`.github/workflows/ci.yml` runs a `kanban-sync-test` job: `setup-uv` (cached on `uv.lock`) → `uv sync --frozen` → ruff → mypy → pytest. Mirrors the prior four component templates.
