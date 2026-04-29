"""`vision health` aggregator implementation.

Polls the per-service health aggregation paths (`/v1/health/<service>`,
served by Caddy via path rewrites) for all five backend services in
parallel via `asyncio.gather`, then renders the result as a Rich table or
JSON. Per `DEC-cli-stack-python-typer`: parallel-fan-out is mandatory for
this command; serial sequential calls are prohibited.

Tailscale-mode limitation: `tailscale serve` does not support URL rewriting,
so the per-service health aggregation paths only work in caddy mode. In
tailscale mode this command will report all services as `down` because the
Tailnet hostname does not route `/v1/health/<service>` paths. Future
hardening (TASK-tailscale-serve-health-paths or similar) can either expose
explicit per-service health subdomains or have this command fall back to
direct service hostnames over the Tailnet.
"""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal

import httpx

if TYPE_CHECKING:
    from app.config import Config

SERVICES: tuple[str, ...] = (
    "whatsorga-ingest",
    "hermes-runtime",
    "backlog-core",
    "gbrain-bridge",
    "kanban-sync",
)
"""The five backend components, in declaration order. Skeleton hits each
one's `/v1/health/<service>` aggregation path through the ingress."""


HealthStatus = Literal["ok", "degraded", "down", "unreachable"]


@dataclass(frozen=True, slots=True)
class ServiceHealth:
    """One row in the aggregator output."""

    service: str
    status: HealthStatus
    http_status: int | None
    """HTTP status code if a response came back; None if the request itself failed
    (DNS, TLS, connection refused, timeout)."""
    detail: str
    """Short human-readable explanation. Never includes secret values."""


def _classify_response(response: httpx.Response) -> tuple[HealthStatus, str]:
    """Map an HTTP response from a service's `/v1/health/<service>` path to a
    structured status. The body shape is documented in `2-design/api-design.md`
    § Health and observability:
        {"status": "ok|degraded|down", "version": "...", "checks": {...}}
    """
    try:
        body = response.json()
    except (ValueError, json.JSONDecodeError):
        return "down", f"non-JSON response (status {response.status_code})"

    if not isinstance(body, dict):
        return "down", f"non-object JSON (status {response.status_code})"

    raw_status = body.get("status", "unknown")
    if raw_status not in ("ok", "degraded", "down"):
        return "down", f"unrecognized status field: {raw_status!r}"

    checks = body.get("checks", {})
    detail = (
        ", ".join(f"{k}={v}" for k, v in checks.items()) if isinstance(checks, dict) and checks
        else "no checks"
    )
    return raw_status, detail


async def _check_one(
    client: httpx.AsyncClient,
    base_url: str,
    service: str,
    timeout: float,
) -> ServiceHealth:
    url = f"{base_url}/v1/health/{service}"
    try:
        response = await client.get(url, timeout=timeout)
    except httpx.HTTPError as exc:
        return ServiceHealth(
            service=service,
            status="unreachable",
            http_status=None,
            detail=f"{type(exc).__name__}: {exc}",
        )

    if response.status_code == 503:
        # backlog-core / gbrain-bridge / kanban-sync return 503 with a body when degraded.
        status, detail = _classify_response(response)
        return ServiceHealth(
            service=service,
            status=status if status != "ok" else "degraded",
            http_status=response.status_code,
            detail=detail,
        )

    if response.status_code != 200:
        return ServiceHealth(
            service=service,
            status="down",
            http_status=response.status_code,
            detail=f"HTTP {response.status_code}",
        )

    status, detail = _classify_response(response)
    return ServiceHealth(
        service=service,
        status=status,
        http_status=response.status_code,
        detail=detail,
    )


async def gather_health(
    config: Config,
    *,
    services: tuple[str, ...] = SERVICES,
    timeout: float = 5.0,
    transport: httpx.AsyncBaseTransport | None = None,
) -> list[ServiceHealth]:
    """Query all `services` in parallel via `asyncio.gather`."""
    async with httpx.AsyncClient(transport=transport) as client:
        return await asyncio.gather(
            *(_check_one(client, config.base_url, name, timeout) for name in services)
        )


def overall_status(results: list[ServiceHealth]) -> HealthStatus:
    """Reduce per-service results to one stack-level verdict.

    Rules:
      - all `ok` → `ok`
      - any `unreachable` or `down` → `down` (something is unambiguously broken)
      - else (mixture of `ok` and `degraded`) → `degraded`
    """
    statuses = {r.status for r in results}
    if statuses == {"ok"}:
        return "ok"
    if "unreachable" in statuses or "down" in statuses:
        return "down"
    return "degraded"


def to_json(results: list[ServiceHealth]) -> str:
    """Render results as a stable JSON document for `--json` mode."""
    payload: dict[str, Any] = {
        "overall": overall_status(results),
        "services": [
            {
                "service": r.service,
                "status": r.status,
                "http_status": r.http_status,
                "detail": r.detail,
            }
            for r in results
        ],
    }
    return json.dumps(payload, indent=2, sort_keys=False)
