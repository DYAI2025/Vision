"""FastAPI dependency that resolves the calling identity or raises.

Usage in a consuming service::

    from bearer_auth import (
        AcceptedTokens, BearerAuthVerifier, CallingIdentity, require_bearer_auth,
    )

    accepted = AcceptedTokens([
        "hermes-runtime",
        "whatsorga-ingest",
        "operator",
    ])
    verifier = accepted.build_verifier()
    app.state.bearer_auth_verifier = verifier

    @app.post("/v1/some-protected-endpoint")
    async def handler(
        identity: CallingIdentity = Depends(require_bearer_auth),
    ) -> ...:
        # identity.name is e.g. "hermes-runtime" — use it for audit attribution.
        ...

Health and metrics endpoints MUST NOT depend on this — they remain
unauthenticated per ``2-design/api-design.md`` § "Health and observability".

The dependency reads ``request.app.state.bearer_auth_verifier`` rather than
taking the verifier as a parameter. This lets the same dependency live in the
shared package while each consuming app installs its own verifier at startup.
"""

from fastapi import Request
from fastapi.responses import JSONResponse

from bearer_auth.errors import AuthError, InvalidAuthError, MissingAuthError
from bearer_auth.identity import CallingIdentity
from bearer_auth.verifier import BearerAuthVerifier

__all__ = ["auth_error_to_response", "require_bearer_auth"]


_BEARER_PREFIX = "Bearer "


def _extract_bearer_token(authorization_header: str | None) -> str:
    """Return the raw token from an ``Authorization`` header, or raise.

    Raises :class:`MissingAuthError` if the header is absent / empty / does
    not use the Bearer scheme. The api-design distinguishes ``auth_required``
    (no credentials) from ``auth_invalid`` (credentials present but
    unrecognized) — a malformed header (wrong scheme, missing token portion)
    is still an "absent credential" condition for our purposes, which matches
    RFC 6750 §3.1's recommendation to treat malformed credentials as missing.
    """
    if not authorization_header:
        raise MissingAuthError
    if not authorization_header.startswith(_BEARER_PREFIX):
        raise MissingAuthError
    token = authorization_header[len(_BEARER_PREFIX):].strip()
    if not token:
        raise MissingAuthError
    return token


def require_bearer_auth(request: Request) -> CallingIdentity:
    """FastAPI dependency: extract the bearer token, resolve the identity.

    Side effect: assigns ``request.state.calling_identity`` so middleware
    further down the chain (e.g., the future purpose-limitation middleware)
    can read the identity without re-parsing the header.

    Raises
    ------
    MissingAuthError
        Header absent / empty / wrong scheme.
    InvalidAuthError
        Header parsed but the token is not in the verifier's accepted set.
    """
    verifier = getattr(request.app.state, "bearer_auth_verifier", None)
    if not isinstance(verifier, BearerAuthVerifier):
        # Misconfiguration: the consuming app forgot to install a verifier.
        # Treat as auth_required so we never accidentally accept anonymous
        # callers when the verifier is missing.
        raise MissingAuthError

    header = request.headers.get("Authorization")
    token = _extract_bearer_token(header)

    identity = verifier.verify(token)
    if identity is None:
        raise InvalidAuthError

    request.state.calling_identity = identity
    return identity


def auth_error_to_response(exc: AuthError, trace_id: str | None = None) -> JSONResponse:
    """Build the api-design error envelope for an :class:`AuthError`.

    Consuming services register this with::

        from fastapi import FastAPI, Request
        from fastapi.responses import JSONResponse
        from bearer_auth import AuthError, auth_error_to_response

        @app.exception_handler(AuthError)
        async def _auth_exception_handler(
            request: Request, exc: AuthError,
        ) -> JSONResponse:
            return auth_error_to_response(exc)

    The ``trace_id`` argument is reserved for future log-correlation wiring
    (per api-design.md error envelope); pass ``None`` until the tracing layer
    lands.
    """
    body: dict[str, object] = {
        "error": {
            "code": exc.code,
            "message": exc.message,
        },
    }
    if trace_id is not None:
        # The error envelope's `trace_id` is documented as a UUID; we don't
        # generate one here because the tracing layer is the right place.
        body_error = body["error"]
        assert isinstance(body_error, dict)
        body_error["trace_id"] = trace_id
    return JSONResponse(status_code=exc.http_status, content=body)
