# hermes-runtime

Project-manager agent runtime for `project-agent-system`. See [`CLAUDE.component.md`](CLAUDE.component.md) for full responsibility, interfaces, and applicable decisions.

**Skeleton state.** This component currently exposes only `GET /v1/health`, plus an importable `OllamaClient` primitive (`app.ollama_client.OllamaClient`) for future skills. Skills (project routing, artifact extraction, duplicate detection, brain-first lookup, model routing), the confidence-gate middleware, the events-stream consumer, and the learning loop are added by Phase 3 / Phase 5 tasks.

## Tech stack

Per [`DEC-backend-stack-python-fastapi`](../../decisions/DEC-backend-stack-python-fastapi.md): Python 3.12 + FastAPI + uvicorn + Pydantic + httpx (for Ollama), managed with `uv`, tested with `pytest`, linted with `ruff`, type-checked with `mypy --strict`.

## Layout

```
3-code/hermes-runtime/
├── Dockerfile                # multi-stage; runtime is python:3.12-slim, non-root
├── pyproject.toml            # runtime + dev deps, ruff/mypy/pytest config
├── uv.lock                   # committed lockfile — uv sync --frozen is reproducible
├── .python-version           # "3.12"
├── app/
│   ├── __init__.py
│   ├── main.py               # FastAPI app + GET /v1/health
│   └── ollama_client.py      # OllamaClient: /api/generate + /api/embeddings wrappers
└── tests/
    ├── test_health.py        # 5 smoke tests for the health endpoint
    └── test_ollama_client.py # 9 tests using httpx.MockTransport (no Ollama process needed)
```

## OllamaClient

Thin async wrapper over Ollama's HTTP API. Reads `OLLAMA_URL` and `OLLAMA_MODEL` from the environment (defaults: `http://ollama:11434` and `gemma3:4b` per `.env.example` and `docker-compose.yml`). Two methods today:

| Method | Wraps | Returns |
|---|---|---|
| `await client.generate(prompt, **options)` | `POST /api/generate` (stream=False) | the response string |
| `await client.embeddings(prompt)` | `POST /api/embeddings` | a list of floats |

Errors:

- `httpx.HTTPStatusError` for any non-2xx Ollama response (raise via `raise_for_status()`).
- `OllamaError` (custom) for missing / malformed expected fields in the JSON payload.

For deterministic tests, pass an `httpx.MockTransport` via the `transport=` kwarg — see `tests/test_ollama_client.py`.

Audit-log emission for remote-inference profiles (per `REQ-SEC-remote-inference-audit`) is **not** implemented in this skeleton — it lands in `TASK-model-router` (Phase 5) and `TASK-remote-inference-profile` (Phase 7). Until then, every call goes to the in-Compose Ollama service via the internal Docker network.

## Local development

Requires [`uv`](https://docs.astral.sh/uv/). `.python-version` pins CPython 3.12.

| Command | Purpose |
|---|---|
| `uv sync --frozen` | Create / refresh `.venv/` with the locked deps. |
| `uv run --frozen pytest` | Run the test suite. |
| `uv run --frozen ruff check .` | Lint. |
| `uv run --frozen ruff format .` | Format. |
| `uv run --frozen mypy app` | Type-check. |
| `uv run --frozen uvicorn app.main:app --reload --port 8000` | Run the dev server with auto-reload. |

To upgrade a dependency, edit `pyproject.toml`, run `uv lock`, commit both files, then re-run `uv sync --frozen`.

## Container build & run

```bash
# from repo root
docker compose build hermes-runtime
docker compose up -d hermes-runtime
docker compose exec hermes-runtime python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:8000/v1/health',timeout=2).read().decode())"
```

The healthcheck (in `docker-compose.yml`) uses the same Python-stdlib one-liner.

## Tests in CI

`.github/workflows/ci.yml` runs a `hermes-runtime-test` job: `setup-uv` (cached on `uv.lock`) → `uv sync --frozen` → ruff → mypy → pytest. Mirrors the `whatsorga-ingest-test` template established by `TASK-whatsorga-skeleton`.
