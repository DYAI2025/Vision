# bearer_auth

Cross-cutting per-service bearer-token authentication helper for `project-agent-system`. Lives under `3-code/_common/` per [`DEC-shared-utility-path-deps`](../../../decisions/DEC-shared-utility-path-deps.md); consumed via uv path-dep by every backend component that exposes HTTP endpoints. Implements [`DEC-service-auth-bearer-tokens`](../../../decisions/DEC-service-auth-bearer-tokens.md) for the **inbound** auth path.

## What this delivers

- Extracts `Authorization: Bearer <token>` from a FastAPI request.
- Recognizes the calling identity (e.g., `hermes-runtime`, `whatsorga-ingest`, `operator`) via constant-time comparison against an env-driven token map.
- Attaches the resolved [`CallingIdentity`](bearer_auth/identity.py) to `request.state.calling_identity`, ready for the next-task purpose-limitation middleware to read.
- Returns the api-design.md error envelope with code `auth_required` (no/malformed credentials) or `auth_invalid` (token unrecognized) — both HTTP 401.

## What this does NOT deliver

- **Purpose enforcement** (`REQ-COMP-purpose-limitation`, code `purpose_denied` / HTTP 403). That is `TASK-purpose-limitation-middleware` (Phase 3). This package provides the calling-identity attribution that the purpose middleware will key on.
- **Outbound bearer auth** for inter-service HTTP calls. Each component will add `Authorization: Bearer ${OWN_TOKEN}` to outbound calls when the corresponding endpoints come online (e.g., `whatsorga-ingest → backlog-core POST /v1/inputs` lands with `TASK-input-event-endpoint`).

## Public surface

```python
from bearer_auth import (
    AcceptedTokens,        # env-driven config loader
    BearerAuthVerifier,    # token → identity resolver (constant-time)
    CallingIdentity,       # frozen dataclass attached to request.state
    AuthError,             # base exception
    MissingAuthError,      # → 401 auth_required
    InvalidAuthError,      # → 401 auth_invalid
    require_bearer_auth,   # FastAPI dependency
)
from bearer_auth.dependency import auth_error_to_response
```

## Wiring in a consuming service

```python
from typing import Annotated

from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse

from bearer_auth import (
    AcceptedTokens, AuthError, CallingIdentity, require_bearer_auth,
)
from bearer_auth.dependency import auth_error_to_response

app = FastAPI(...)

# 1. Declare which calling identities this service accepts inbound. The
#    receiving service's docker-compose.yml `environment:` block declares one
#    `<NAME>_TOKEN` env var per identity (e.g., backlog-core accepts
#    whatsorga-ingest, hermes-runtime, gbrain-bridge, kanban-sync, operator).
accepted = AcceptedTokens([
    "whatsorga-ingest",
    "hermes-runtime",
    "gbrain-bridge",
    "kanban-sync",
    "operator",
])
app.state.bearer_auth_verifier = accepted.build_verifier()

# 2. Register the structured-error converter.
@app.exception_handler(AuthError)
async def _auth_exception_handler(_request: Request, exc: AuthError) -> JSONResponse:
    return auth_error_to_response(exc)

# 3. Apply the dependency to every protected endpoint.
AuthIdentity = Annotated[CallingIdentity, Depends(require_bearer_auth)]

@app.post("/v1/sources")
async def register_source(identity: AuthIdentity, body: SourceRegistration) -> ...:
    # identity.name → audit_log attribution, NOT the token itself.
    ...
```

`/v1/health` and `/v1/metrics` MUST NOT depend on `require_bearer_auth` — health stays unauthenticated per `2-design/api-design.md` § "Health and observability".

The annotation alias pattern (`Annotated[T, Depends(...)]`) matches the project convention used by `backlog-core` (see `app/main.py`) and avoids ruff's `B008` "Depends in default" rule. Note: `bearer_auth/dependency.py` does NOT use `from __future__ import annotations` — FastAPI's `get_type_hints` introspection of dependency signatures requires runtime-resolvable annotations.

## Identity-name → env-var convention

Identity names are kebab-case. The env-var name is the upper-snake form with `_TOKEN` appended:

| Calling identity      | Env variable             |
|-----------------------|--------------------------|
| `whatsorga-ingest`    | `WHATSORGA_INGEST_TOKEN` |
| `hermes-runtime`      | `HERMES_RUNTIME_TOKEN`   |
| `backlog-core`        | `BACKLOG_CORE_TOKEN`     |
| `gbrain-bridge`       | `GBRAIN_BRIDGE_TOKEN`    |
| `kanban-sync`         | `KANBAN_SYNC_TOKEN`      |
| `operator`            | `OPERATOR_TOKEN`         |

`.env.example` declares all six slots; `docker-compose.yml` enforces presence with `${VAR:?required}` per receiver scope. Generate values with `openssl rand -hex 32`.

## Security properties

- **Constant-time comparison** via `hmac.compare_digest` — required by `DEC-service-auth-bearer-tokens` § "Required patterns" to avoid timing side channels.
- **Defensive copy** of the input mapping at construction — later mutation cannot retroactively grant access.
- **No token-shape diagnostics in error messages** — per `DEC-service-auth-bearer-tokens` § "Prohibited patterns": "Returning verbose auth error details that aid an attacker." Both 401 codes carry the same generic shape.
- **Anonymous-fail-closed** — if a consuming app forgets to install `app.state.bearer_auth_verifier`, every protected endpoint returns 401 `auth_required`.
- **Duplicate-token detection at startup** — `AcceptedTokens.to_token_map` raises `ValueError` if two distinct identities resolve to the same token, surfacing deploy misconfigurations before the first request.

## Layout

```
.
├── pyproject.toml             # bearer-auth package, uv-managed
├── uv.lock                    # committed lockfile
├── .python-version            # 3.12
├── bearer_auth/               # importable package
│   ├── __init__.py            # public surface
│   ├── identity.py            # CallingIdentity dataclass
│   ├── errors.py              # AuthError + MissingAuthError + InvalidAuthError
│   ├── verifier.py            # BearerAuthVerifier (constant-time compare)
│   ├── config.py              # AcceptedTokens env loader
│   └── dependency.py          # FastAPI dependency + error→envelope helper
├── tests/                     # pytest suite — 37 tests
│   ├── __init__.py
│   ├── test_identity.py
│   ├── test_errors.py
│   ├── test_verifier.py
│   ├── test_config.py
│   └── test_dependency.py     # end-to-end FastAPI integration
├── README.md
└── .gitignore
```

## Local development

```bash
cd 3-code/_common/bearer_auth
uv sync --frozen
uv run --frozen ruff check .
uv run --frozen mypy bearer_auth
uv run --frozen pytest -q
```

## CI

Per-package CI job `_common-bearer-auth-test` mirrors the per-component pattern: `uv sync --frozen` → ruff → mypy strict → pytest.

Each consuming backend's `cache-dependency-glob` includes `3-code/_common/bearer_auth/uv.lock` so its cache invalidates when this package changes.

## Consumed by

- `whatsorga-ingest`
- `hermes-runtime`
- `backlog-core`
- `gbrain-bridge`
- `kanban-sync`

The `cli` component does NOT consume this package — the operator CLI authenticates against backend services as the calling-identity `operator`, but the CLI itself is a client, not an HTTP server.

Each consumer declares the path-dep in its `pyproject.toml`:

```toml
[project]
dependencies = [
    "bearer-auth",
]

[tool.uv.sources]
bearer-auth = { path = "../_common/bearer_auth", editable = true }
```

Each consumer's Dockerfile already uses the **repo root** as build context and copies `3-code/_common/` into the builder stage (set up by `TASK-canonical-json-helper`); no Dockerfile changes are required to add a second `_common/` package.

## Change policy

This package is on the inter-service trust boundary. Changes to the verifier, the env-var convention, or the error-envelope shape require:

1. A test demonstrating that existing behavior is preserved (or a documented, intentional break with a migration plan in the consuming `DEC-service-auth-bearer-tokens.history.md`).
2. Lockstep updates across all five consumers in the same commit.
3. CI green on `_common-bearer-auth-test` and on every consuming `<component>-test` job.

Wire-format-affecting changes (env-var convention, error code names, HTTP status mapping) MUST coordinate with `2-design/api-design.md` § "Authentication" and § "Error response shape".
