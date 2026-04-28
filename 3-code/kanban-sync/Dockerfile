FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder
WORKDIR /app
COPY pyproject.toml ./
RUN uv sync --frozen --no-dev || uv sync --no-dev
COPY app ./app

FROM python:3.12-slim
WORKDIR /app
COPY --from=builder /app /app
RUN useradd -m appuser
USER appuser
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
