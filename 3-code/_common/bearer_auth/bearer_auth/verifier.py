"""Token → calling-identity resolution with constant-time comparison.

``DEC-service-auth-bearer-tokens`` § "Required patterns" mandates:

- "Token comparison uses constant-time comparison to avoid timing side
  channels." — implemented via :func:`hmac.compare_digest`.
- "Tokens are opaque random strings (≥256 bits of entropy from a CSPRNG).
  They are not JWTs and do not encode claims — claims (purposes, identity)
  live in the receiving service's config keyed by token hash." — the verifier
  treats tokens as opaque and only resolves their identity via a static
  mapping passed in at construction time.

The verifier itself does no I/O. The mapping is loaded by
:class:`bearer_auth.config.AcceptedTokens` from environment variables and
passed to the verifier — keeping the verifier deterministic and testable
without env mocking.
"""

from __future__ import annotations

import hmac
from typing import TYPE_CHECKING

from bearer_auth.identity import CallingIdentity

if TYPE_CHECKING:
    from collections.abc import Mapping


class BearerAuthVerifier:
    """Resolves a presented bearer token to its calling identity.

    Parameters
    ----------
    accepted_tokens:
        Mapping from raw token string to the calling-identity name. The
        verifier copies this mapping at construction time so later mutation
        of the source mapping does not affect resolution. Empty mappings are
        legal (e.g., a service that accepts no inbound auth in some test
        configuration) — every token presented will be rejected.
    """

    def __init__(self, accepted_tokens: Mapping[str, str]) -> None:
        # Defensive copy: the verifier is constructed once at startup; we
        # don't want a later config mutation (test helper, hot-reload) to
        # silently change which tokens we accept.
        self._accepted: dict[str, str] = dict(accepted_tokens)

    def verify(self, presented_token: str) -> CallingIdentity | None:
        """Return the :class:`CallingIdentity` for ``presented_token``, or ``None``.

        Constant-time compare across every accepted token so the running time
        does not depend on which token was presented (or whether any matches).
        For the small N (≤6 tokens at MVP) we accept the linear scan over a
        per-token hash lookup — the security property comes from
        ``compare_digest``, and a hash-keyed dict lookup would short-circuit
        and leak length information.
        """
        if not presented_token:
            return None

        presented_bytes = presented_token.encode("utf-8")
        match: str | None = None
        for token, identity_name in self._accepted.items():
            # `compare_digest` is constant-time only across equal-length inputs;
            # for unequal lengths it returns False fast but does not leak per-
            # byte timing. Both branches still iterate the full mapping so the
            # total work is independent of WHICH token (if any) matched.
            if hmac.compare_digest(presented_bytes, token.encode("utf-8")):
                match = identity_name
                # Don't break — finish the loop to keep total work uniform.
        if match is None:
            return None
        return CallingIdentity(name=match)
