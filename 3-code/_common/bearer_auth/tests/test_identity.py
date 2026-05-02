"""CallingIdentity is the value attached to ``request.state`` after auth."""

from __future__ import annotations

import pytest

from bearer_auth import CallingIdentity


def test_calling_identity_carries_a_name() -> None:
    identity = CallingIdentity(name="hermes-runtime")
    assert identity.name == "hermes-runtime"


def test_calling_identity_is_frozen() -> None:
    # Per ``DEC-service-auth-bearer-tokens``: the audit-log records the
    # identity name. Mutating identity post-attach would silently alter the
    # attribution string — frozen=True prevents that. FrozenInstanceError
    # is a subclass of AttributeError on frozen dataclasses.
    from dataclasses import FrozenInstanceError

    identity = CallingIdentity(name="operator")
    with pytest.raises(FrozenInstanceError):
        identity.name = "hermes-runtime"  # type: ignore[misc]


def test_two_identities_with_same_name_are_equal() -> None:
    # Identity equality is name equality — useful for test assertions.
    assert CallingIdentity(name="operator") == CallingIdentity(name="operator")


def test_identities_with_different_names_are_not_equal() -> None:
    assert CallingIdentity(name="operator") != CallingIdentity(name="hermes-runtime")
