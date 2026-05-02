"""Error subclass codes match the api-design enumeration."""

from __future__ import annotations

import pytest

from bearer_auth import AuthError, InvalidAuthError, MissingAuthError


def test_missing_auth_error_uses_api_design_code() -> None:
    # api-design.md § "Error response shape" lists `auth_required` for HTTP 401
    # when no credentials were presented.
    assert MissingAuthError.code == "auth_required"
    assert MissingAuthError.http_status == 401


def test_invalid_auth_error_uses_api_design_code() -> None:
    # api-design.md lists `auth_invalid` for HTTP 401 when credentials were
    # presented but rejected.
    assert InvalidAuthError.code == "auth_invalid"
    assert InvalidAuthError.http_status == 401


def test_subclasses_inherit_from_auth_error() -> None:
    # The FastAPI exception handler registers AuthError, not the subclasses,
    # so subclass-of must hold.
    assert issubclass(MissingAuthError, AuthError)
    assert issubclass(InvalidAuthError, AuthError)


def test_auth_error_subclasses_are_raisable_without_args() -> None:
    # Required by the dependency: `raise MissingAuthError` (no instance args).
    with pytest.raises(MissingAuthError):
        raise MissingAuthError
    with pytest.raises(InvalidAuthError):
        raise InvalidAuthError


def test_invalid_auth_error_message_does_not_leak_token_diagnostics() -> None:
    # Per `DEC-service-auth-bearer-tokens` § "Prohibited patterns": the error
    # message must be minimal and must not differentiate "token well-formed
    # but unrecognized" from "purpose-denied" (the latter is a different
    # error class, but both error messages are kept generic).
    assert "token" not in InvalidAuthError.message.lower()
    assert "format" not in InvalidAuthError.message.lower()
    assert "shape" not in InvalidAuthError.message.lower()
