"""Unit tests for the backlog-core migration runner."""

from __future__ import annotations

import pytest

from app.migrations import _backend_url


@pytest.mark.parametrize(
    ("input_url", "expected_url"),
    [
        (
            "postgresql+psycopg2://user:pass@localhost:5432/vision",
            "postgresql://user:pass@localhost:5432/vision",
        ),
        (
            "postgresql+asyncpg://user:pass@localhost:5432/vision",
            "postgresql://user:pass@localhost:5432/vision",
        ),
        (
            "postgresql://user:pass@localhost:5432/vision",
            "postgresql://user:pass@localhost:5432/vision",
        ),
        (
            "postgres://user:pass@localhost:5432/vision",
            "postgres://user:pass@localhost:5432/vision",
        ),
    ],
)
def test_backend_url_normalizes_yoyo_compatible_postgres_schemes(
    input_url: str,
    expected_url: str,
) -> None:
    assert _backend_url(input_url) == expected_url


def test_backend_url_rejects_non_postgres_scheme() -> None:
    with pytest.raises(ValueError, match="DATABASE_URL must start"):
        _backend_url("mysql://user:pass@localhost:3306/vision")
