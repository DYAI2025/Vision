"""End-to-end FastAPI integration tests.

Cover ``DEC-service-auth-bearer-tokens`` § "Required checks" 1-2:
1. The middleware checks (a) bearer present, (b) token recognized.
2. A deliberately malformed `Authorization` header is rejected with `401`.

Required check 3 (purpose denial) is the next task's responsibility.

These tests build a minimal FastAPI app with a single protected endpoint plus
the canonical health endpoint (which must remain unauthenticated). The same
shape will be used by the consuming services when they wire the dependency.

This file deliberately does NOT use ``from __future__ import annotations`` —
FastAPI's dependency resolution requires the ``Annotated[T, Depends(...)]``
metadata to be a real runtime object on the function signature, and the
stringified-annotations mode does not always unwrap aliased Annotated through
``get_type_hints``. Skeleton components (e.g., backlog-core) follow the same
no-``__future__`` convention.
"""

from typing import Annotated, Any

import pytest
from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from bearer_auth import (
    AcceptedTokens,
    AuthError,
    CallingIdentity,
    require_bearer_auth,
)
from bearer_auth.dependency import auth_error_to_response

# `Annotated[T, Depends(...)]` is the project convention (matches backlog-core's
# existing dependency wiring) and avoids ruff's B008 "Depends in default" rule.
_AuthIdentity = Annotated[CallingIdentity, Depends(require_bearer_auth)]


def _build_app(env: dict[str, str] | None = None) -> FastAPI:
    """Build an app with the bearer-auth dependency wired the canonical way."""
    app = FastAPI()
    accepted = AcceptedTokens(["hermes-runtime", "operator"])
    app.state.bearer_auth_verifier = accepted.build_verifier(env)  # type: ignore[arg-type]

    @app.exception_handler(AuthError)
    async def _h(_request: Request, exc: AuthError) -> JSONResponse:
        return auth_error_to_response(exc)

    @app.get("/v1/health")
    async def health() -> dict[str, Any]:
        # Stays unauthenticated per api-design.md § "Health and observability".
        return {"status": "ok", "version": "0.0.1", "checks": {}}

    @app.post("/v1/_test/protected")
    async def protected(identity: _AuthIdentity) -> dict[str, str]:
        return {"calling_identity": identity.name}

    return app


@pytest.fixture
def env() -> dict[str, str]:
    return {"HERMES_RUNTIME_TOKEN": "tok-hermes", "OPERATOR_TOKEN": "tok-op"}


@pytest.fixture
def client(env: dict[str, str]) -> TestClient:
    return TestClient(_build_app(env))


def test_health_endpoint_does_not_require_auth(client: TestClient) -> None:
    # api-design.md mandates that /v1/health stays unauthenticated. This is
    # the regression guard: if a future change accidentally adds the auth
    # dependency to health, this test fails before the change ships.
    r = client.get("/v1/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_protected_endpoint_with_recognized_token_succeeds(client: TestClient) -> None:
    r = client.post(
        "/v1/_test/protected",
        headers={"Authorization": "Bearer tok-hermes"},
    )
    assert r.status_code == 200
    assert r.json() == {"calling_identity": "hermes-runtime"}


def test_protected_endpoint_distinguishes_callers_by_token(client: TestClient) -> None:
    r = client.post(
        "/v1/_test/protected",
        headers={"Authorization": "Bearer tok-op"},
    )
    assert r.status_code == 200
    assert r.json() == {"calling_identity": "operator"}


def test_protected_endpoint_without_authorization_returns_401_auth_required(
    client: TestClient,
) -> None:
    r = client.post("/v1/_test/protected")
    assert r.status_code == 401
    assert r.json() == {"error": {"code": "auth_required", "message": "Authentication required."}}


def test_protected_endpoint_with_empty_bearer_returns_401_auth_required(
    client: TestClient,
) -> None:
    r = client.post(
        "/v1/_test/protected",
        headers={"Authorization": "Bearer "},
    )
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "auth_required"


def test_protected_endpoint_with_wrong_scheme_returns_401_auth_required(
    client: TestClient,
) -> None:
    # Per the dependency docstring (RFC 6750 §3.1): a wrong scheme is treated
    # as "no credentials" rather than "invalid credentials".
    r = client.post(
        "/v1/_test/protected",
        headers={"Authorization": "Basic dXNlcjpwYXNz"},
    )
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "auth_required"


def test_protected_endpoint_with_malformed_header_returns_401(client: TestClient) -> None:
    # DEC-service-auth-bearer-tokens § Required checks #2: a deliberately
    # malformed header is rejected with 401. Bare token (no `Bearer ` prefix)
    # is the canonical malformed case.
    r = client.post(
        "/v1/_test/protected",
        headers={"Authorization": "tok-hermes"},
    )
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "auth_required"


def test_protected_endpoint_with_unknown_token_returns_401_auth_invalid(
    client: TestClient,
) -> None:
    r = client.post(
        "/v1/_test/protected",
        headers={"Authorization": "Bearer not-a-real-token"},
    )
    assert r.status_code == 401
    assert r.json() == {"error": {"code": "auth_invalid", "message": "Authentication invalid."}}


def test_error_response_does_not_leak_diagnostics(client: TestClient) -> None:
    # Per DEC § "Prohibited patterns": error responses must be minimal — they
    # must NOT distinguish "your token has the right shape but is wrong" from
    # "your token is in the wrong format". We assert message inertia rather
    # than the absence of every conceivable leak.
    r = client.post(
        "/v1/_test/protected",
        headers={"Authorization": "Bearer wrong"},
    )
    body = r.text
    assert "wrong" not in body  # token value not echoed
    assert "format" not in body
    assert "shape" not in body
    assert "purpose" not in body  # don't conflate with purpose-denied


def test_app_without_verifier_state_returns_401_auth_required() -> None:
    # Defense-in-depth: if a consuming app forgets to install the verifier,
    # we must NOT silently accept anonymous callers. Treat as auth_required
    # so an oncall sees the 401 floods rather than wide-open endpoints.
    app = FastAPI()  # no app.state.bearer_auth_verifier

    @app.exception_handler(AuthError)
    async def _h(_request: Request, exc: AuthError) -> JSONResponse:
        return auth_error_to_response(exc)

    @app.post("/x")
    async def x(_id: _AuthIdentity) -> dict[str, str]:
        return {}

    c = TestClient(app)
    r = c.post("/x", headers={"Authorization": "Bearer anything"})
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "auth_required"


def test_protected_endpoint_attaches_identity_to_request_state() -> None:
    # The purpose-limitation middleware (next task) will read
    # request.state.calling_identity. Verify the dependency populates it.
    app = FastAPI()
    accepted = AcceptedTokens(["operator"])
    app.state.bearer_auth_verifier = accepted.build_verifier({"OPERATOR_TOKEN": "tok"})  # type: ignore[arg-type]

    @app.exception_handler(AuthError)
    async def _h(_request: Request, exc: AuthError) -> JSONResponse:
        return auth_error_to_response(exc)

    captured: dict[str, str] = {}

    @app.post("/probe")
    async def probe(request: Request, identity: _AuthIdentity) -> dict[str, str]:
        # Round-trip the identity through request.state to confirm it was set
        # before the handler ran (the purpose middleware will read it the
        # same way).
        from_state = request.state.calling_identity
        assert isinstance(from_state, CallingIdentity)
        captured["state"] = from_state.name
        captured["dep"] = identity.name
        return {"ok": "1"}

    c = TestClient(app)
    r = c.post("/probe", headers={"Authorization": "Bearer tok"})
    assert r.status_code == 200
    assert captured == {"state": "operator", "dep": "operator"}
