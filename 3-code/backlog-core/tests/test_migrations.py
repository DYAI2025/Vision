"""Unit tests for the backlog-core migration runner."""

from __future__ import annotations

from pathlib import Path

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


def test_consent_scope_fix_constraints_are_added_not_valid() -> None:
    migration_sql = Path(
        "migrations/0003_fix-consent-scope-check-null-handling.sql"
    ).read_text()

    assert "consent_sources_scope_mvp_flags_check CHECK" in migration_sql
    assert "consent_history_new_scope_mvp_flags_check CHECK" in migration_sql
    assert migration_sql.count(") NOT VALID;") == 2
