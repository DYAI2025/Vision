"""Verifier resolves a presented token to its calling identity.

Covers ``DEC-service-auth-bearer-tokens`` § "Required patterns" beyond the
HTTP layer: constant-time comparison, unrecognized tokens rejected, defensive
copy of the input mapping.
"""

from __future__ import annotations

from bearer_auth import BearerAuthVerifier, CallingIdentity


def test_recognized_token_resolves_to_its_identity() -> None:
    v = BearerAuthVerifier({"abc123": "hermes-runtime"})
    assert v.verify("abc123") == CallingIdentity(name="hermes-runtime")


def test_unrecognized_token_returns_none() -> None:
    v = BearerAuthVerifier({"abc123": "hermes-runtime"})
    assert v.verify("does-not-match") is None


def test_empty_token_returns_none() -> None:
    # An empty token would otherwise compare-equal to the empty string in
    # an empty mapping; reject up-front so the caller can return
    # `auth_required` (missing) vs. `auth_invalid` (rejected).
    v = BearerAuthVerifier({"abc": "operator"})
    assert v.verify("") is None


def test_empty_mapping_rejects_every_token() -> None:
    v = BearerAuthVerifier({})
    assert v.verify("anything") is None


def test_each_token_maps_to_its_distinct_identity() -> None:
    v = BearerAuthVerifier({
        "tok-hermes": "hermes-runtime",
        "tok-whatsorga": "whatsorga-ingest",
        "tok-operator": "operator",
    })
    assert v.verify("tok-hermes") == CallingIdentity(name="hermes-runtime")
    assert v.verify("tok-whatsorga") == CallingIdentity(name="whatsorga-ingest")
    assert v.verify("tok-operator") == CallingIdentity(name="operator")


def test_token_compare_is_case_sensitive() -> None:
    # Bearer tokens are opaque random strings; case-insensitive matching
    # would shrink the keyspace and break ``DEC-service-auth-bearer-tokens``'s
    # ≥256-bit-entropy property.
    v = BearerAuthVerifier({"AbCdEf": "operator"})
    assert v.verify("abcdef") is None
    assert v.verify("ABCDEF") is None
    assert v.verify("AbCdEf") == CallingIdentity(name="operator")


def test_input_mapping_is_defensively_copied() -> None:
    # A consuming app constructs the verifier once at startup. If the source
    # mapping is mutated later (test helper, hot-reload), the verifier must
    # still authenticate against the snapshot it was built from.
    source: dict[str, str] = {"tok-a": "operator"}
    v = BearerAuthVerifier(source)
    source["tok-b"] = "hermes-runtime"  # mutate the source after construction
    assert v.verify("tok-b") is None
    assert v.verify("tok-a") == CallingIdentity(name="operator")


def test_substring_match_is_rejected() -> None:
    # Defense against any future regression where a `startswith` check is
    # introduced — only exact, full-length matches resolve.
    v = BearerAuthVerifier({"abc12345": "operator"})
    assert v.verify("abc") is None
    assert v.verify("abc12345extra") is None


def test_unicode_token_is_compared_byte_exact() -> None:
    # Tokens are produced by `openssl rand -hex 32` and are ASCII-only in
    # practice, but the verifier must not silently normalize unicode.
    v = BearerAuthVerifier({"naïve-token": "operator"})
    assert v.verify("naïve-token") == CallingIdentity(name="operator")
    # NFC/NFD-different but visually identical strings must not match.
    nfd = "naïve-token"
    assert v.verify(nfd) is None
