"""Calling-identity value type.

The verifier resolves an inbound bearer token to a :class:`CallingIdentity`,
which is then attached to ``request.state.calling_identity`` for downstream
handlers. Audit-log entries record ``identity.name`` (the calling-identity name
like ``hermes-runtime`` or ``operator``) — never the token itself.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CallingIdentity:
    """The identity behind an authenticated inbound HTTP request.

    Attributes
    ----------
    name:
        The calling-identity name as declared in the receiving service's env
        config (e.g., ``"hermes-runtime"``, ``"whatsorga-ingest"``,
        ``"operator"``). Stable across token rotations — the token changes,
        the name does not. Used as the audit-log attribution string per
        ``REQ-SEC-audit-log``.
    """

    name: str
