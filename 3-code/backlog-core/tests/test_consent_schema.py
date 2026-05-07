"""Integration tests for the consent source/history schema.

This covers ``TASK-postgres-consent-schema``. Per
``DEC-postgres-migration-tool`` every storage migration is exercised against
real Postgres through the same migration runner operators use. The Docker gate
mirrors ``test_events_schema.py`` so local shells without Docker can run the
unit suite while CI still validates schema behavior end-to-end.
"""

from __future__ import annotations

import shutil
import subprocess
from typing import TYPE_CHECKING

import psycopg2
import psycopg2.extras
import pytest

if TYPE_CHECKING:
    from collections.abc import Iterator

    from psycopg2.extensions import connection as PgConnection


MVP_SCOPE = {
    "route_to_projects": True,
    "summarize": True,
    "extract_artifacts": False,
    "learning_signal": False,
    "remote_inference_allowed": False,
}


def _docker_daemon_reachable() -> bool:
    if shutil.which("docker") is None:
        return False
    try:
        subprocess.run(
            ["docker", "info"],
            check=True,
            capture_output=True,
            timeout=5,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError):
        return False
    return True


pytestmark = [
    pytest.mark.postgres,
    pytest.mark.skipif(
        not _docker_daemon_reachable(),
        reason="Docker daemon not reachable — testcontainers needs a running Docker socket",
    ),
]


@pytest.fixture(scope="module")
def postgres_url() -> Iterator[str]:
    from testcontainers.postgres import PostgresContainer

    with PostgresContainer("postgres:16-alpine") as pg:
        yield pg.get_connection_url()


@pytest.fixture(scope="module")
def migrated_url(postgres_url: str) -> str:
    from app.migrations import cmd_apply

    cmd_apply(database_url=postgres_url)
    return postgres_url


def _connect(url: str) -> PgConnection:
    if url.startswith("postgresql+psycopg2://"):
        url = "postgresql://" + url[len("postgresql+psycopg2://") :]
    if url.startswith("postgresql+asyncpg://"):
        url = "postgresql://" + url[len("postgresql+asyncpg://") :]
    return psycopg2.connect(url)


def _insert_source(conn: PgConnection, source_id: str = "manual:ben") -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO consent_sources
                (source_id, actor_id, consent_scope, retention_policy, granted_by)
            VALUES (%s, %s, %s::jsonb, %s, %s)
            """,
            (source_id, "ben", psycopg2.extras.Json(MVP_SCOPE), "raw_30d", "ben"),
        )


def _insert_history(
    conn: PgConnection,
    *,
    source_id: str = "manual:ben",
    history_id: str = "11111111-1111-1111-1111-111111111111",
    changed_at: str = "2026-05-07T10:00:00+00:00",
    new_scope: dict[str, bool] | None = None,
    new_retention: str = "raw_30d",
    new_state: str = "active",
) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO consent_history
                (history_id, source_id, changed_at, new_scope,
                 new_retention, new_state, event_id)
            VALUES (%s, %s, %s, %s::jsonb, %s, %s, %s)
            """,
            (
                history_id,
                source_id,
                changed_at,
                psycopg2.extras.Json(new_scope or MVP_SCOPE),
                new_retention,
                new_state,
                "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            ),
        )


# ---------------------------------------------------------------------------
# Migration runner produces the expected schema.
# ---------------------------------------------------------------------------


def test_migration_applies_both_events_and_consent_migrations(migrated_url: str) -> None:
    conn = _connect(migrated_url)
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT migration_id FROM _yoyo_migration ORDER BY migration_id")
            applied = [r[0] for r in cur.fetchall()]
    finally:
        conn.close()
    expected = ["0001_create-events-table", "0002_create-consent-tables"]
    assert applied[: len(expected)] == expected


def test_consent_tables_have_expected_columns(migrated_url: str) -> None:
    conn = _connect(migrated_url)
    expected = {
        "consent_sources": {
            ("source_id", "text", "NO"),
            ("actor_id", "text", "NO"),
            ("lawful_basis", "text", "NO"),
            ("consent_scope", "jsonb", "NO"),
            ("retention_policy", "text", "NO"),
            ("current_state", "text", "NO"),
            ("granted_at", "timestamp with time zone", "NO"),
            ("granted_by", "text", "NO"),
            ("updated_at", "timestamp with time zone", "NO"),
        },
        "consent_history": {
            ("history_id", "uuid", "NO"),
            ("source_id", "text", "NO"),
            ("changed_at", "timestamp with time zone", "NO"),
            ("prior_scope", "jsonb", "YES"),
            ("new_scope", "jsonb", "NO"),
            ("prior_retention", "text", "YES"),
            ("new_retention", "text", "NO"),
            ("prior_state", "text", "YES"),
            ("new_state", "text", "NO"),
            ("change_reason", "text", "YES"),
            ("event_id", "uuid", "NO"),
        },
    }
    try:
        with conn.cursor() as cur:
            for table, expected_columns in expected.items():
                cur.execute(
                    """
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns
                    WHERE table_name = %s
                    """,
                    (table,),
                )
                actual = set(cur.fetchall())
                missing = expected_columns - actual
                assert expected_columns.issubset(actual), f"{table} missing {missing}"
    finally:
        conn.close()


def test_read_as_of_index_exists(migrated_url: str) -> None:
    conn = _connect(migrated_url)
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT indexname FROM pg_indexes
                WHERE tablename = 'consent_history'
                """
            )
            actual = {r[0] for r in cur.fetchall()}
    finally:
        conn.close()
    assert "consent_history_source_changed_at_idx" in actual


# ---------------------------------------------------------------------------
# Constraint behavior.
# ---------------------------------------------------------------------------


def test_lawful_basis_is_constrained_to_consent(migrated_url: str) -> None:
    conn = _connect(migrated_url)
    try:
        with conn, pytest.raises(psycopg2.errors.CheckViolation), conn.cursor() as cur:
            cur.execute(
                """
                    INSERT INTO consent_sources
                        (source_id, actor_id, lawful_basis, retention_policy, granted_by)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                ("manual:bad", "ben", "legitimate_interest", "raw_30d", "ben"),
            )
    finally:
        conn.close()


def test_default_scope_contains_all_mvp_flags_false(migrated_url: str) -> None:
    conn = _connect(migrated_url)
    try:
        with conn, conn.cursor() as cur:
            cur.execute(
                """
                    INSERT INTO consent_sources
                        (source_id, actor_id, retention_policy, granted_by)
                    VALUES (%s, %s, %s, %s)
                    RETURNING consent_scope, current_state, lawful_basis
                    """,
                ("manual:defaults", "ben", "raw_30d", "ben"),
            )
            scope, state, basis = cur.fetchone()
        assert scope == {
            "route_to_projects": False,
            "summarize": False,
            "extract_artifacts": False,
            "learning_signal": False,
            "remote_inference_allowed": False,
        }
        assert state == "active"
        assert basis == "consent"
    finally:
        conn.close()


def test_scope_requires_mvp_flags_as_booleans(migrated_url: str) -> None:
    conn = _connect(migrated_url)
    invalid_scope = dict(MVP_SCOPE)
    invalid_scope.pop("summarize")
    try:
        with conn, pytest.raises(psycopg2.errors.CheckViolation), conn.cursor() as cur:
            cur.execute(
                """
                    INSERT INTO consent_sources
                        (source_id, actor_id, consent_scope, retention_policy, granted_by)
                    VALUES (%s, %s, %s::jsonb, %s, %s)
                    """,
                (
                    "manual:missing-flag",
                    "ben",
                    psycopg2.extras.Json(invalid_scope),
                    "raw_30d",
                    "ben",
                ),
            )
    finally:
        conn.close()


def test_history_new_scope_requires_mvp_flags_as_booleans(migrated_url: str) -> None:
    conn = _connect(migrated_url)
    invalid_scope = dict(MVP_SCOPE)
    invalid_scope.pop("learning_signal")
    try:
        with conn:
            _insert_source(conn, "manual:history-missing-flag")
        with conn, pytest.raises(psycopg2.errors.CheckViolation):
            _insert_history(
                conn,
                source_id="manual:history-missing-flag",
                history_id="44444444-4444-4444-4444-444444444444",
                new_scope=invalid_scope,
            )
    finally:
        conn.close()


def test_consent_history_is_append_only(migrated_url: str) -> None:
    conn = _connect(migrated_url)
    try:
        with conn:
            _insert_source(conn, "manual:append-only")
            _insert_history(conn, source_id="manual:append-only")
        with (
            conn,
            pytest.raises(psycopg2.errors.ObjectNotInPrerequisiteState),
            conn.cursor() as cur,
        ):
            cur.execute(
                """
                    UPDATE consent_history
                    SET change_reason = 'mutated in place'
                    WHERE history_id = %s
                    """,
                ("11111111-1111-1111-1111-111111111111",),
            )
    finally:
        conn.close()


def test_read_as_of_returns_latest_history_before_timestamp(migrated_url: str) -> None:
    conn = _connect(migrated_url)
    later_scope = dict(MVP_SCOPE)
    later_scope["remote_inference_allowed"] = True
    try:
        with conn:
            _insert_source(conn, "manual:as-of")
            _insert_history(
                conn,
                source_id="manual:as-of",
                history_id="22222222-2222-2222-2222-222222222222",
                changed_at="2026-05-07T10:00:00+00:00",
            )
            _insert_history(
                conn,
                source_id="manual:as-of",
                history_id="33333333-3333-3333-3333-333333333333",
                changed_at="2026-05-07T11:00:00+00:00",
                new_scope=later_scope,
                new_retention="derived_keep",
            )
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT new_scope, new_retention, new_state
                FROM consent_history
                WHERE source_id = %s
                  AND changed_at <= %s
                ORDER BY changed_at DESC
                LIMIT 1
                """,
                ("manual:as-of", "2026-05-07T10:30:00+00:00"),
            )
            scope, retention, state = cur.fetchone()
        assert scope == MVP_SCOPE
        assert retention == "raw_30d"
        assert state == "active"
    finally:
        conn.close()
