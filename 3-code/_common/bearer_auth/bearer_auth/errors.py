"""Structured 401 errors per ``2-design/api-design.md`` § "Error response shape".

The api-design enumerates two relevant codes for this package:

- ``auth_required`` — no ``Authorization`` header or empty bearer (HTTP 401)
- ``auth_invalid`` — header present and parseable, token unrecognized (HTTP 401)

The third code on the auth axis, ``purpose_denied`` (HTTP 403), is the
purpose-limitation layer's responsibility (``TASK-purpose-limitation-middleware``).
This package raises only the 401 variants; the FastAPI dependency converts them
to the api-design error envelope before the response leaves the service.

Per ``DEC-service-auth-bearer-tokens`` § "Prohibited patterns": error responses
are minimal — they never leak whether a token was structurally well-formed but
unrecognized vs. valid-but-purpose-denied. ``InvalidAuthError`` therefore
carries no token-shape diagnostics in its public message.
"""

from __future__ import annotations


class AuthError(Exception):
    """Base class for bearer-auth failures.

    The :func:`bearer_auth.dependency.require_bearer_auth` FastAPI dependency
    catches subclasses and produces the structured api-design 401 envelope.
    """

    code: str = "auth_error"
    message: str = "Authentication failed."
    http_status: int = 401


class MissingAuthError(AuthError):
    """No ``Authorization`` header present, or header is empty / non-bearer.

    Maps to api-design code ``auth_required`` (HTTP 401).
    """

    code = "auth_required"
    message = "Authentication required."
    http_status = 401


class InvalidAuthError(AuthError):
    """``Authorization: Bearer <token>`` header parsed but token unrecognized.

    Maps to api-design code ``auth_invalid`` (HTTP 401). The error message is
    deliberately generic — see the module docstring on minimal error responses.
    """

    code = "auth_invalid"
    message = "Authentication invalid."
    http_status = 401
