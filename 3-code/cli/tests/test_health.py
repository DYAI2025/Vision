"""Unit tests for app.health: per-service classification + parallel aggregation."""

from __future__ import annotations

from typing import Any

import httpx
import pytest

from app.config import Config
from app.health import (
    SERVICES,
    ServiceHealth,
    gather_health,
    overall_status,
    to_json,
)


def _ok_payload(service: str) -> dict[str, Any]:
    """Body shape per `2-design/api-design.md` § Health and observability."""
    checks = {"postgres": "ok"} if service == "backlog-core" else {}
    return {"status": "ok", "version": "0.0.1", "checks": checks}


def _degraded_payload(service: str) -> dict[str, Any]:
    if service == "backlog-core":
        return {"status": "degraded", "version": "0.0.1", "checks": {"postgres": "down"}}
    if service == "gbrain-bridge":
        return {"status": "degraded", "version": "0.0.1", "checks": {"vault": "down"}}
    return {"status": "degraded", "version": "0.0.1", "checks": {}}


def _config(base_url: str = "http://test") -> Config:
    return Config(base_url=base_url, operator_token=None)


def _all_ok_handler() -> Any:
    def handler(request: httpx.Request) -> httpx.Response:
        # URL shape: /v1/health/<service>
        service = request.url.path.rsplit("/", 1)[-1]
        return httpx.Response(200, json=_ok_payload(service))

    return handler


async def test_gather_health_all_services_ok() -> None:
    transport = httpx.MockTransport(_all_ok_handler())

    results = await gather_health(_config(), transport=transport)

    assert len(results) == len(SERVICES)
    assert {r.service for r in results} == set(SERVICES)
    assert all(r.status == "ok" and r.http_status == 200 for r in results)
    assert overall_status(results) == "ok"


async def test_gather_health_one_service_degraded_returns_503() -> None:
    """backlog-core / gbrain-bridge / kanban-sync return 503 with body when degraded."""

    def handler(request: httpx.Request) -> httpx.Response:
        service = request.url.path.rsplit("/", 1)[-1]
        if service == "backlog-core":
            return httpx.Response(503, json=_degraded_payload(service))
        return httpx.Response(200, json=_ok_payload(service))

    results = await gather_health(_config(), transport=httpx.MockTransport(handler))

    backlog = next(r for r in results if r.service == "backlog-core")
    assert backlog.status == "degraded"
    assert backlog.http_status == 503
    assert "postgres=down" in backlog.detail

    others = [r for r in results if r.service != "backlog-core"]
    assert all(r.status == "ok" for r in others)
    assert overall_status(results) == "degraded"


async def test_gather_health_one_service_unreachable_marks_overall_down() -> None:
    """Connection failures fold to status=`unreachable` and overall=`down`."""

    def handler(request: httpx.Request) -> httpx.Response:
        service = request.url.path.rsplit("/", 1)[-1]
        if service == "hermes-runtime":
            raise httpx.ConnectError("simulated connection failure", request=request)
        return httpx.Response(200, json=_ok_payload(service))

    results = await gather_health(_config(), transport=httpx.MockTransport(handler))

    hermes = next(r for r in results if r.service == "hermes-runtime")
    assert hermes.status == "unreachable"
    assert hermes.http_status is None
    assert "ConnectError" in hermes.detail
    assert overall_status(results) == "down"


async def test_gather_health_all_unreachable() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("everything down", request=request)

    results = await gather_health(_config(), transport=httpx.MockTransport(handler))

    assert all(r.status == "unreachable" for r in results)
    assert overall_status(results) == "down"


async def test_gather_health_classifies_unrecognized_status_as_down() -> None:
    """A service returning {'status': 'unknown', ...} folds to status=down with detail."""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"status": "weird-state", "version": "0", "checks": {}})

    results = await gather_health(
        _config(), services=("whatsorga-ingest",), transport=httpx.MockTransport(handler)
    )

    assert results[0].status == "down"
    assert "weird-state" in results[0].detail
    assert overall_status(results) == "down"


async def test_gather_health_classifies_non_json_response_as_down() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=b"not json", headers={"content-type": "text/plain"})

    results = await gather_health(
        _config(), services=("whatsorga-ingest",), transport=httpx.MockTransport(handler)
    )

    assert results[0].status == "down"
    assert "non-JSON" in results[0].detail


async def test_gather_health_classifies_unexpected_4xx_as_down() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"error": "not found"})

    results = await gather_health(
        _config(), services=("whatsorga-ingest",), transport=httpx.MockTransport(handler)
    )

    assert results[0].status == "down"
    assert results[0].http_status == 404
    assert "HTTP 404" in results[0].detail


async def test_gather_health_constructs_correct_aggregation_urls() -> None:
    """Skeleton uses the Caddy `/v1/health/<service>` aggregation pattern."""
    seen_urls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen_urls.append(str(request.url))
        return httpx.Response(200, json=_ok_payload("whatsorga-ingest"))

    await gather_health(
        _config("https://vision.example.com"),
        services=("whatsorga-ingest", "hermes-runtime"),
        transport=httpx.MockTransport(handler),
    )

    assert seen_urls == [
        "https://vision.example.com/v1/health/whatsorga-ingest",
        "https://vision.example.com/v1/health/hermes-runtime",
    ]


def test_overall_status_reduction_rules() -> None:
    """Three small unit tests for the overall_status reducer."""
    all_ok = [ServiceHealth(s, "ok", 200, "fine") for s in SERVICES]
    assert overall_status(all_ok) == "ok"

    one_degraded = list(all_ok)
    one_degraded[0] = ServiceHealth(SERVICES[0], "degraded", 503, "stale cache")
    assert overall_status(one_degraded) == "degraded"

    one_down = list(all_ok)
    one_down[0] = ServiceHealth(SERVICES[0], "down", 500, "internal error")
    assert overall_status(one_down) == "down"

    one_unreachable = list(all_ok)
    one_unreachable[0] = ServiceHealth(SERVICES[0], "unreachable", None, "connection refused")
    assert overall_status(one_unreachable) == "down"


def test_to_json_round_trips_and_includes_overall() -> None:
    import json

    results = [
        ServiceHealth("whatsorga-ingest", "ok", 200, ""),
        ServiceHealth("backlog-core", "degraded", 503, "postgres=down"),
    ]
    encoded = to_json(results)
    decoded = json.loads(encoded)

    assert decoded["overall"] == "degraded"
    assert decoded["services"][0]["service"] == "whatsorga-ingest"
    assert decoded["services"][1]["http_status"] == 503


@pytest.mark.parametrize("status_code", [200, 503])
async def test_gather_health_parses_body_consistently_for_200_and_503(status_code: int) -> None:
    """Whether a service uses 200+ok or 503+degraded, the body shape is the same
    and our classifier handles both. Regression test against the cleanup pass
    that introduced the 503-on-degraded pattern."""

    def handler(request: httpx.Request) -> httpx.Response:
        body = (
            _ok_payload("backlog-core") if status_code == 200 else _degraded_payload("backlog-core")
        )
        return httpx.Response(status_code, json=body)

    results = await gather_health(
        _config(), services=("backlog-core",), transport=httpx.MockTransport(handler)
    )

    if status_code == 200:
        assert results[0].status == "ok"
    else:
        assert results[0].status == "degraded"
