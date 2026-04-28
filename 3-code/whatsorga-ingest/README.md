# whatsorga-ingest

Adapter layer + normalization for `project-agent-system`. See [`CLAUDE.component.md`](CLAUDE.component.md) for full responsibility, interfaces, and applicable decisions.

**Skeleton state.** This component currently exposes only `GET /v1/health`. Adapters (WhatsApp, voice, repo events, manual CLI), normalization, and the consent boundary are added by subsequent Phase 1 / Phase 3 tasks (`TASK-whatsorga-normalization`, `TASK-whatsorga-manual-cli-adapter`, `TASK-whatsorga-consent-check`, `TASK-whatsapp-adapter`, `TASK-voice-adapter`, `TASK-repo-events-adapter`).

## Tech stack

Per [`DEC-backend-stack-python-fastapi`](../../decisions/DEC-backend-stack-python-fastapi.md): Python 3.12 + FastAPI + uvicorn + Pydantic, managed with `uv`, tested with `pytest`, linted with `ruff`, type-checked with `mypy --strict`.

## Layout

```
3-code/whatsorga-ingest/
├── Dockerfile                # multi-stage; runtime is python:3.12-slim, non-root
├── pyproject.toml            # runtime + dev deps, ruff/mypy/pytest config
├── uv.lock                   # committed lockfile — uv sync --frozen is reproducible
├── .python-version           # "3.12" — uv reads this for venv creation
├── app/                      # importable package
│   ├── __init__.py           # exposes __version__
│   └── main.py               # FastAPI app + GET /v1/health
└── tests/
    └── test_health.py        # smoke tests for the health endpoint
```

## Local development

Requires [`uv`](https://docs.astral.sh/uv/). The project's `.python-version` pins CPython 3.12, which `uv` will install automatically if missing.

| Command | Purpose |
|---|---|
| `uv sync --frozen` | Create / refresh `.venv/` with the locked deps. Run once after pulling. |
| `uv run --frozen pytest` | Run the test suite. |
| `uv run --frozen ruff check .` | Lint. |
| `uv run --frozen ruff format .` | Format. |
| `uv run --frozen mypy app` | Type-check. |
| `uv run --frozen uvicorn app.main:app --reload --port 8000` | Run the dev server with auto-reload. |

To upgrade a dependency, edit `pyproject.toml`, run `uv lock`, commit both files, then re-run `uv sync --frozen`.

## Container build & run

The image is built by Docker Compose from this directory's `Dockerfile`:

```bash
# from repo root
docker compose build whatsorga-ingest
docker compose up -d whatsorga-ingest
docker compose exec whatsorga-ingest wget -qO- http://localhost:8000/v1/health
```

Network model: the service listens on internal port 8000 only and is reachable from inside the `internal` bridge network. External access goes through the active ingress profile (`caddy` or `tailscale`) per [`4-deploy/ingress/README.md`](../../4-deploy/ingress/README.md). No host port mapping is exposed.

## Tests in CI

`.github/workflows/ci.yml` runs a `whatsorga-ingest-test` job on every PR and main-branch push: `uv sync --frozen` + `uv run --frozen pytest`. The job is independent of the docker-compose validation jobs so a Python-only failure surfaces a tight feedback loop.
