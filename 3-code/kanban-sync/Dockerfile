# kanban-sync — multi-stage image per DEC-backend-stack-python-fastapi
# and DEC-shared-utility-path-deps.
#
# Build context = repository root, so that uv path-deps from this component's
# pyproject.toml to `../_common/<package>` resolve at build time per
# DEC-shared-utility-path-deps. docker-compose.yml specifies
# `context: .` + `dockerfile: 3-code/kanban-sync/Dockerfile` accordingly.
#
# Stage 1 builds the venv with frozen deps via uv. Stage 2 is a minimal slim
# runtime that only carries the venv + the app package + the consumed
# `_common/` packages (the venv's editable .pth files reference the latter
# by absolute path). The shared `vault` Docker volume is mounted at VAULT_PATH
# (default /vault); KANBAN_SUBTREE (default /vault/Kanban) is the read/write
# carve-out exclusively owned by this component (gbrain-bridge must not write
# there).

FROM python:3.12-slim AS builder

# Pinned uv release; bump intentionally when we want a newer resolver.
COPY --from=ghcr.io/astral-sh/uv:0.9.16 /uv /uvx /usr/local/bin/

# Layout: shared utilities under /build/3-code/_common (siblings to per-component
# dirs), the component itself under /build/3-code/kanban-sync. This preserves
# the relative path declared in [tool.uv.sources] (`../_common/<package>`).
COPY 3-code/_common /build/3-code/_common

WORKDIR /build/3-code/kanban-sync

ENV UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1

# Install dependencies first (no project) to maximize Docker layer cache hits
# when only app/ source changes. The canonical-json path-dep is editable —
# uv registers it via a .pth file pointing at /build/3-code/_common/canonical_json.
COPY 3-code/kanban-sync/pyproject.toml 3-code/kanban-sync/uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Install the project itself into the same venv.
COPY 3-code/kanban-sync/app ./app
RUN uv sync --frozen --no-dev


FROM python:3.12-slim

# Non-root runtime user.
RUN groupadd --system --gid 1000 app \
    && useradd --system --uid 1000 --gid app --home-dir /app --no-create-home --shell /usr/sbin/nologin app

WORKDIR /app

# Copy the prebuilt venv and app package from the builder stage.
COPY --from=builder --chown=app:app /opt/venv /opt/venv
COPY --from=builder --chown=app:app /build/3-code/kanban-sync/app /app/app
# The venv's editable .pth files reference path-dep sources by absolute path
# (per DEC-shared-utility-path-deps). Mirror /build/3-code/_common so those
# references resolve at runtime.
COPY --from=builder --chown=app:app /build/3-code/_common /build/3-code/_common

USER app

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
