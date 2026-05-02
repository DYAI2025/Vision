"""Env-driven loader for the verifier's accepted-tokens mapping.

Per ``DEC-service-auth-bearer-tokens`` § "Required patterns": "Tokens are
stored in ``.env`` only; never committed to the repo". The receiving service's
``docker-compose.yml`` ``environment:`` block declares one env var per accepted
calling identity (e.g., ``backlog-core``'s block declares ``HERMES_RUNTIME_TOKEN``,
``WHATSORGA_INGEST_TOKEN``, ``OPERATOR_TOKEN`` etc. — all callers it accepts).

This loader reads those env vars and produces the ``token → identity-name``
mapping the verifier consumes.

The mapping is **caller-name → env-var-name**, not token → name — because the
canonical naming in env (``HERMES_RUNTIME_TOKEN``) is derived from the
identity name (``hermes-runtime``). The loader resolves env values once at
startup and constructs the verifier; the env values themselves are not stored
on the loader instance.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

from bearer_auth.verifier import BearerAuthVerifier

if TYPE_CHECKING:
    from collections.abc import Iterable


def _identity_to_env_var(identity_name: str) -> str:
    """Convert ``hermes-runtime`` → ``HERMES_RUNTIME_TOKEN``.

    Hyphens become underscores, the whole name uppercases, and ``_TOKEN`` is
    appended. This matches the convention already established in
    ``.env.example`` and ``docker-compose.yml``.
    """
    return identity_name.replace("-", "_").upper() + "_TOKEN"


class AcceptedTokens:
    """Env-driven config for the set of identities a service accepts inbound.

    Parameters
    ----------
    accepted_identities:
        The identity names the service accepts as callers. Each name maps to
        an env var of shape ``<NAME>_TOKEN`` (with hyphens replaced by
        underscores, uppercased). Tokens absent or empty in the environment
        are silently dropped — useful for partial-deploy scenarios (e.g., a
        local dev profile where only the operator token is set).

    Notes
    -----
    Per ``DEC-service-auth-bearer-tokens``, every required token MUST be
    present in production deploys; ``.env.example`` declares all six slots and
    ``docker-compose.yml`` enforces presence with ``${VAR:?required}``. By the
    time this loader runs, env values are guaranteed non-empty in production.
    Dropping silently in this loader serves dev/test ergonomics, not as a
    production gate.
    """

    def __init__(self, accepted_identities: Iterable[str]) -> None:
        # Preserve declaration order — useful for test assertions and for
        # debug logging; functional behavior does not depend on order.
        self._identities: tuple[str, ...] = tuple(accepted_identities)

    def to_token_map(self, environ: os._Environ[str] | None = None) -> dict[str, str]:
        """Resolve env vars and return a ``token → identity-name`` mapping.

        Parameters
        ----------
        environ:
            The environment to read from. Defaults to ``os.environ``. Tests
            pass an in-process mapping (e.g., ``{"OPERATOR_TOKEN": "abc"}``)
            to avoid mutating the real environment.
        """
        env = environ if environ is not None else os.environ
        mapping: dict[str, str] = {}
        for identity in self._identities:
            env_var = _identity_to_env_var(identity)
            value = env.get(env_var, "")
            if value:
                # Distinct identities with the same token would silently
                # overwrite — protect that case with a hard error so deploy
                # misconfigurations surface at startup, not at first request.
                if value in mapping and mapping[value] != identity:
                    raise ValueError(
                        f"Bearer token for identity {identity!r} collides with "
                        f"an already-registered identity. Tokens must be unique "
                        f"per identity."
                    )
                mapping[value] = identity
        return mapping

    def build_verifier(
        self, environ: os._Environ[str] | None = None
    ) -> BearerAuthVerifier:
        """Convenience: read env and return a configured verifier."""
        return BearerAuthVerifier(self.to_token_map(environ))
