"""Unit tests for the backlog-core migration runner."""

from __future__ import annotations

import pytest
from yoyo import read_migrations

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


def test_yoyo_reads_all_numbered_sql_migrations() -> None:
    migrations = read_migrations("migrations")
    assert [migration.id for migration in migrations] == [
        "0001_create-events-table",
        "0002_create-consent-tables",
        "0003_fix-consent-scope-check-null-handling",
    ]
