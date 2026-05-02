"""Per-service bearer-token authentication for inter-service HTTP.

Lives under ``3-code/_common/`` per ``DEC-shared-utility-path-deps``; consumed
via uv path-dep by every backend component that exposes HTTP endpoints. This
package implements ``DEC-service-auth-bearer-tokens`` for the **inbound** auth
path: extracting ``Authorization: Bearer <token>`` from a request, recognizing
the calling identity, and returning the structured 401 errors defined in
``2-design/api-design.md`` § "Error response shape".

Purpose enforcement (REQ-COMP-purpose-limitation) is intentionally NOT in this
package — that is ``TASK-purpose-limitation-middleware`` (Phase 3). The
calling-identity name returned here is the input that the purpose middleware
will read to look up the identity's declared purposes.

Public surface
--------------
- :class:`CallingIdentity` — dataclass attached to ``request.state.calling_identity``
- :class:`BearerAuthVerifier` — token → identity resolver with constant-time compare
- :class:`AcceptedTokens` — env-driven config loader for the verifier
- :func:`require_bearer_auth` — FastAPI dependency that resolves identity or raises
- :class:`AuthError` / :class:`MissingAuthError` / :class:`InvalidAuthError` —
  structured errors mapping to ``401 auth_required`` and ``401 auth_invalid``
"""

from __future__ import annotations

from bearer_auth.config import AcceptedTokens
from bearer_auth.dependency import require_bearer_auth
from bearer_auth.errors import AuthError, InvalidAuthError, MissingAuthError
from bearer_auth.identity import CallingIdentity
from bearer_auth.verifier import BearerAuthVerifier

__all__ = [
    "AcceptedTokens",
    "AuthError",
    "BearerAuthVerifier",
    "CallingIdentity",
    "InvalidAuthError",
    "MissingAuthError",
    "require_bearer_auth",
]
