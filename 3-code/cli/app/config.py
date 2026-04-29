"""Environment + .env-driven configuration for the CLI.

Skeleton-level (TASK-cli-skeleton). Reads the base URL the CLI uses to reach
backend services and the operator bearer token. Per
`DEC-cli-stack-python-typer` Required patterns, no service URL is ever
hardcoded in command modules — they go through `Config.base_url`.

Per `DEC-service-auth-bearer-tokens`, the operator token is `OPERATOR_TOKEN`
from `.env` (or the process environment); token values are never logged or
written to stdout.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

DEFAULT_BASE_URL = "http://localhost"
"""Caddy-mode default per `DEC-cursor-pagination-and-event-stream-conventions`
context: Caddy serves on `{$CADDY_HOSTNAME:localhost}` with auto-TLS or
internal CA, and the cli skeleton hits `{base}/v1/health/<service>` per
`api-design.md` aggregation paths. Tailscale-mode operator must override
this via `VISION_BASE_URL=https://<ts-hostname>.<tailnet>.ts.net` and
accept the no-rewrite limitation on per-service health aggregation."""


@dataclass(frozen=True, slots=True)
class Config:
    """Resolved CLI configuration. Construct via `load_config()`."""

    base_url: str
    operator_token: str | None
    """Optional at the skeleton level — `vision health` doesn't need auth.
    Future commands that hit auth-required endpoints will require it and
    fail-fast when missing."""


def _find_dotenv(start: Path | None = None) -> Path | None:
    """Walk upward from `start` looking for a `.env` file. Returns the first
    match or None. Mirrors how operators expect dev tools to discover env
    files."""
    cwd = start or Path.cwd()
    for parent in (cwd, *cwd.parents):
        candidate = parent / ".env"
        if candidate.is_file():
            return candidate
    return None


def load_config(override_base_url: str | None = None) -> Config:
    """Build a `Config` from the environment.

    Order of precedence (highest first):
      1. `override_base_url` argument (typically from a `--base-url` CLI flag).
      2. `VISION_BASE_URL` env var.
      3. `.env` file discovered by walking upward from CWD.
      4. `DEFAULT_BASE_URL`.
    """
    dotenv_path = _find_dotenv()
    if dotenv_path is not None:
        # `override=False` so explicit env vars win over `.env` values.
        load_dotenv(dotenv_path, override=False)

    if override_base_url is not None:
        base_url = override_base_url
    else:
        base_url = os.environ.get("VISION_BASE_URL", DEFAULT_BASE_URL)

    operator_token = os.environ.get("OPERATOR_TOKEN") or None

    return Config(
        base_url=base_url.rstrip("/"),
        operator_token=operator_token,
    )
