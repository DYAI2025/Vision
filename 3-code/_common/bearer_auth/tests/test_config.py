"""AcceptedTokens loads env vars into the verifier's token-map.

The mapping is **identity-name → env-var-name** by convention
(``hermes-runtime`` → ``HERMES_RUNTIME_TOKEN``). Tests pass an in-memory
``environ`` dict so the real process environment is never mutated.
"""

from __future__ import annotations

import pytest

from bearer_auth import AcceptedTokens, BearerAuthVerifier, CallingIdentity


def test_resolves_env_var_for_each_identity() -> None:
    accepted = AcceptedTokens(["hermes-runtime", "operator"])
    env = {"HERMES_RUNTIME_TOKEN": "tok-hermes", "OPERATOR_TOKEN": "tok-op"}
    mapping = accepted.to_token_map(env)  # type: ignore[arg-type]
    assert mapping == {"tok-hermes": "hermes-runtime", "tok-op": "operator"}


def test_hyphens_in_identity_become_underscores_in_env_var() -> None:
    # `whatsorga-ingest` → `WHATSORGA_INGEST_TOKEN` per the project convention.
    accepted = AcceptedTokens(["whatsorga-ingest"])
    env = {"WHATSORGA_INGEST_TOKEN": "tok-w"}
    mapping = accepted.to_token_map(env)  # type: ignore[arg-type]
    assert mapping == {"tok-w": "whatsorga-ingest"}


def test_missing_env_var_is_silently_dropped() -> None:
    # Useful for partial-deploy / dev-profile scenarios where only some
    # tokens are set. Production presence is enforced upstream by
    # `${VAR:?required}` in docker-compose.yml.
    accepted = AcceptedTokens(["hermes-runtime", "operator"])
    env = {"OPERATOR_TOKEN": "tok-op"}
    mapping = accepted.to_token_map(env)  # type: ignore[arg-type]
    assert mapping == {"tok-op": "operator"}


def test_empty_env_var_is_treated_as_missing() -> None:
    # `${VAR:-}` and `unset` both produce empty strings in some shells; an
    # empty string would otherwise become a "valid" (empty) token, which the
    # verifier already rejects but we drop here for defense-in-depth.
    accepted = AcceptedTokens(["hermes-runtime"])
    env = {"HERMES_RUNTIME_TOKEN": ""}
    mapping = accepted.to_token_map(env)  # type: ignore[arg-type]
    assert mapping == {}


def test_duplicate_token_across_distinct_identities_raises() -> None:
    # A deploy misconfiguration where two services share a token would
    # otherwise silently overwrite the mapping in dict insertion order. We
    # surface it as a hard error so the operator notices at startup, not at
    # the first audit-log mis-attribution.
    accepted = AcceptedTokens(["hermes-runtime", "operator"])
    env = {"HERMES_RUNTIME_TOKEN": "same", "OPERATOR_TOKEN": "same"}
    with pytest.raises(ValueError, match="collides"):
        accepted.to_token_map(env)  # type: ignore[arg-type]


def test_same_identity_with_same_token_does_not_raise() -> None:
    # Idempotent calls with the same env should produce the same mapping.
    accepted = AcceptedTokens(["operator"])
    env = {"OPERATOR_TOKEN": "tok"}
    assert accepted.to_token_map(env) == {"tok": "operator"}  # type: ignore[arg-type]


def test_build_verifier_returns_a_configured_verifier() -> None:
    accepted = AcceptedTokens(["operator"])
    env = {"OPERATOR_TOKEN": "tok-op"}
    verifier = accepted.build_verifier(env)  # type: ignore[arg-type]
    assert isinstance(verifier, BearerAuthVerifier)
    assert verifier.verify("tok-op") == CallingIdentity(name="operator")


def test_default_environ_reads_real_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    # Smoke test that the loader actually reads from os.environ when no
    # explicit environ is passed. Use monkeypatch to avoid leaking into
    # other tests.
    monkeypatch.setenv("OPERATOR_TOKEN", "from-real-env")
    accepted = AcceptedTokens(["operator"])
    mapping = accepted.to_token_map()
    assert mapping == {"from-real-env": "operator"}
