# gbrain-bridge — multi-stage image per DEC-backend-stack-python-fastapi.
#
# Stage 1 builds the venv with frozen deps via uv. Stage 2 is a minimal slim
# runtime that only carries the venv + the app package and runs uvicorn as a
# non-root user. Listens on internal port 8000 — exposed only via the ingress
# profile (Caddy or Tailscale), not as a host port. The `vault` Docker volume
# is mounted at VAULT_PATH (default /vault) by docker-compose.yml.

FROM python:3.12-slim AS builder

# Pinned uv release; bump intentionally when we want a newer resolver.
COPY --from=ghcr.io/astral-sh/uv:0.9.16 /uv /uvx /usr/local/bin/

WORKDIR /build

ENV UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1

# Install dependencies first (no project) to maximize Docker layer cache hits
# when only app/ source changes.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Install the project itself into the same venv.
COPY app ./app
RUN uv sync --frozen --no-dev


FROM python:3.12-slim

# Non-root runtime user.
RUN groupadd --system --gid 1000 app \
    && useradd --system --uid 1000 --gid app --home-dir /app --no-create-home --shell /usr/sbin/nologin app

WORKDIR /app

# Copy the prebuilt venv and app package from the builder stage.
COPY --from=builder --chown=app:app /opt/venv /opt/venv
COPY --from=builder --chown=app:app /build/app /app/app

USER app

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

EXPOSE 8000

CMD ["/opt/venv/bin/python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
