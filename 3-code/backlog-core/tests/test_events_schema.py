"""Integration tests for the events table schema.

Per ``DEC-postgres-migration-tool`` § "Required patterns": every migration
is verified by at least one test that applies it to a real Postgres
container, asserts the resulting schema, and exercises behavior the
migration enables (CHECK constraints, indexes, partition routing).

The tests use ``testcontainers-python`` to spin up a real Postgres 16
container per test session. Tests that need Postgres are gated by the
``postgres`` marker so devs without Docker can ``pytest -m 'not postgres'``
to skip them. CI runs them unconditionally — the GitHub-hosted Ubuntu
runner has Docker.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

import psycopg2
import pytest

if TYPE_CHECKING:
    from collections.abc import Iterator

    from psycopg2.extensions import connection as PgConnection


def _docker_daemon_reachable() -> bool:
    """Return True iff a Docker daemon answers — not just that the CLI is on PATH.

    On Mac dev shells the CLI is often present (`/opt/homebrew/bin/docker`)
    while the daemon (colima / Docker Desktop / OrbStack) is stopped. The
    earlier `shutil.which('docker')`-only gate let the tests proceed in
    that case and produced confusing connection errors. CI runners on
    Ubuntu always have a running daemon, so this stricter gate doesn't
    suppress real failures there.
    """
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


# Mark every test in this file as requiring Postgres + Docker. See
# pytest.ini_options in pyproject.toml for the marker registration.
pytestmark = [
    pytest.mark.postgres,
    pytest.mark.skipif(
        not _docker_daemon_reachable(),
        reason="Docker daemon not reachable — testcontainers needs a running Docker socket",
    ),
]


@pytest.fixture(scope="module")
def postgres_url() -> Iterator[str]:
    """Spin up a Postgres 16 container for the test module.

    Module-scoped so all schema tests share one container; the migration
    runs once and the connection-level tests reuse the resulting DB.
    """
    from testcontainers.postgres import PostgresContainer

    with PostgresContainer("postgres:16-alpine") as pg:
        yield pg.get_connection_url()


@pytest.fixture(scope="module")
def migrated_url(postgres_url: str) -> str:
    """Apply migrations to the testcontainer DB and return its URL.

    Uses the production-side runner (``app.migrations.cmd_apply``) so the
    code path tested is the same one operators run. testcontainers'
    ``get_connection_url`` returns a SQLAlchemy-style URL prefixed with
    ``postgresql+psycopg2://``; the runner accepts this verbatim.
    """
    from app.migrations import cmd_apply

    cmd_apply(database_url=postgres_url)
    return postgres_url


def _connect(url: str) -> PgConnection:
    """Open a sync psycopg2 connection given an asyncpg-or-yoyo-style URL."""
    # psycopg2 doesn't recognize the `postgresql+psycopg2://` scheme yoyo
    # uses; strip the driver suffix before passing to psycopg2.
    if url.startswith("postgresql+psycopg2://"):
        url = "postgresql://" + url[len("postgresql+psycopg2://") :]
    return psycopg2.connect(url)


# ---------------------------------------------------------------------------
# Migration runner produces the expected schema.
# ---------------------------------------------------------------------------


def test_migration_applies_cleanly(migrated_url: str) -> None:
    """Confirm the migration ran and the yoyo ledger reflects it."""
    conn = _connect(migrated_url)
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT migration_id FROM _yoyo_migration ORDER BY migration_id"
            )
            rows = cur.fetchall()
        applied = [r[0] for r in rows]
    finally:
        conn.close()
    assert applied == ["0001_create-events-table"]


def test_events_table_exists_and_is_partitioned(migrated_url: str) -> None:
    """Per data-model.md § Partitioning: events is RANGE-partitioned on created_at."""
    conn = _connect(migrated_url)
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT relkind FROM pg_class WHERE relname = 'events'"
            )
            row = cur.fetchone()
            assert row is not None, "events table did not get created"
            # 'p' = partitioned table; 'r' = ordinary table.
            assert row[0] == "p", f"events is relkind={row[0]!r}, expected 'p' (partitioned)"
    finally:
        conn.close()


def test_events_table_has_expected_columns(migrated_url: str) -> None:
    """Every column from data-model.md § events is present with the right NOT NULL shape."""
    conn = _connect(migrated_url)
    expected = {
        ("event_id", "uuid", "NO"),
        ("event_type", "text", "NO"),
        ("created_at", "timestamp with time zone", "NO"),
        ("actor_id", "text", "NO"),
        ("proposal_id", "uuid", "YES"),
        ("source_input_event_id", "uuid", "YES"),
        ("subject_ref", "text", "YES"),
        ("payload", "jsonb", "YES"),
        ("payload_hash", "bytea", "NO"),
        ("prev_hash", "bytea", "NO"),
        ("hash", "bytea", "NO"),
        ("retention_class", "text", "NO"),
        ("redacted", "boolean", "NO"),
        ("redaction_run_id", "uuid", "YES"),
        ("redacted_at", "timestamp with time zone", "YES"),
    }
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = 'events'
                """
            )
            actual = set(cur.fetchall())
    finally:
        conn.close()
    assert actual == expected


def test_events_primary_key_is_event_id_and_created_at(migrated_url: str) -> None:
    """Per migration: PK is composite because partition key must participate."""
    conn = _connect(migrated_url)
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT a.attname
                FROM pg_index i
                JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
                WHERE i.indrelid = 'events'::regclass AND i.indisprimary
                ORDER BY array_position(i.indkey, a.attnum)
                """
            )
            cols = [r[0] for r in cur.fetchall()]
    finally:
        conn.close()
    assert cols == ["event_id", "created_at"]


def test_all_five_indexes_exist(migrated_url: str) -> None:
    """Per data-model.md § Indexes: 5 indexes — verify every one is present."""
    conn = _connect(migrated_url)
    expected = {
        "events_subject_ref_created_at_idx",
        "events_proposal_id_idx",
        "events_event_type_created_at_idx",
        "events_retention_sweep_idx",
        "events_source_input_event_id_idx",
    }
    try:
        with conn.cursor() as cur:
            # Indexes on a partitioned parent are listed in pg_indexes via
            # the parent's relname.
            cur.execute(
                """
                SELECT indexname FROM pg_indexes
                WHERE tablename = 'events'
                """
            )
            actual = {r[0] for r in cur.fetchall()}
    finally:
        conn.close()
    # actual may include the PK index plus the five user indexes.
    assert expected.issubset(actual), f"missing: {expected - actual}"


def test_retention_sweep_index_is_partial_on_redacted_false(migrated_url: str) -> None:
    """The retention-sweep index must be partial WHERE redacted = FALSE."""
    conn = _connect(migrated_url)
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT pg_get_indexdef(c.oid)
                FROM pg_class c
                WHERE c.relname = 'events_retention_sweep_idx'
                """
            )
            row = cur.fetchone()
    finally:
        conn.close()
    assert row is not None, "retention-sweep index missing"
    indexdef = row[0]
    # The partial predicate may be reformatted by pg_get_indexdef; check
    # for the substantive shape rather than exact string match.
    assert "WHERE" in indexdef
    assert "redacted" in indexdef
    assert "false" in indexdef.lower()


def test_first_two_partitions_exist(migrated_url: str) -> None:
    """Migration creates 2026_05 and 2026_06 partitions inline."""
    conn = _connect(migrated_url)
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT inhrelid::regclass::text
                FROM pg_inherits
                WHERE inhparent = 'events'::regclass
                ORDER BY inhrelid::regclass::text
                """
            )
            partitions = [r[0] for r in cur.fetchall()]
    finally:
        conn.close()
    assert partitions == ["events_2026_05", "events_2026_06"]


# ---------------------------------------------------------------------------
# CHECK constraints reject invalid values.
# ---------------------------------------------------------------------------


def _insert_event(conn: PgConnection, **overrides: object) -> None:
    """Insert one event with sane defaults; overrides take precedence.

    Used to exercise CHECK constraints — the test passes if the INSERT
    raises (constraint did its job) or fails if it succeeds when expected
    to be rejected.
    """
    base: dict[str, object] = {
        "event_id": "00000000-0000-0000-0000-000000000001",
        "event_type": "input.received",
        "created_at": "2026-05-15T12:00:00+00:00",
        "actor_id": "test-actor",
        "proposal_id": None,
        "source_input_event_id": None,
        "subject_ref": None,
        "payload": '{"hello": "world"}',
        "payload_hash": b"\x00" * 32,
        "prev_hash": b"\x00" * 32,
        "hash": b"\x00" * 32,
        "retention_class": "raw_30d",
        "redacted": False,
        "redaction_run_id": None,
        "redacted_at": None,
    }
    base.update(overrides)
    cols = ", ".join(base.keys())
    placeholders = ", ".join(["%s"] * len(base))
    with conn.cursor() as cur:
        cur.execute(
            f"INSERT INTO events ({cols}) VALUES ({placeholders})",
            list(base.values()),
        )


def test_event_type_check_rejects_unknown_type(migrated_url: str) -> None:
    """The event_type CHECK closes the enum — unknown types must be rejected."""
    conn = _connect(migrated_url)
    try:
        with conn, pytest.raises(psycopg2.errors.CheckViolation):
            _insert_event(
                conn,
                event_id="11111111-1111-1111-1111-111111111111",
                event_type="this.is.not.a.real.event.type",
            )
    finally:
        conn.close()


def test_event_type_check_accepts_every_documented_type(migrated_url: str) -> None:
    """Every event_type listed in data-model.md § Event-type catalog is accepted."""
    documented = [
        "input.received",
        "routing.decided",
        "proposal.proposed",
        "proposal.applied",
        "proposal.rejected",
        "proposal.disposition",
        "learning.recorded",
        "source.registered",
        "source.consent_updated",
        "source.consent_revoked",
        "retention.deleted",
        "rtbf.run_started",
        "rtbf.cascade_completed",
        "rtbf.verification_passed",
        "remote_inference.called",
        "audit.gate_decision",
        "gbrain.page_mutated",
        "kanban.card_mutated",
        "kanban.user_edit",
        "unattributed_edit",
        "secret.rotated",
        "duplicate.detected",
        "review.disposed",
        "processing.stuck",
        "extraction.empty",
        "learning_gap.brain_first_discipline",
        "subject.export_produced",
        "kanban.user_edit_acknowledged",
    ]
    conn = _connect(migrated_url)
    try:
        with conn:
            for i, et in enumerate(documented):
                _insert_event(
                    conn,
                    event_id=f"22222222-2222-2222-2222-{i:012d}",
                    event_type=et,
                )
        # Cleanup so neighboring tests start from a clean partition.
        with conn, conn.cursor() as cur:
            cur.execute(
                "DELETE FROM events WHERE actor_id = 'test-actor'"
            )
    finally:
        conn.close()


def test_retention_class_check_rejects_unknown_value(migrated_url: str) -> None:
    """retention_class CHECK closes the three-class vocabulary."""
    conn = _connect(migrated_url)
    try:
        with conn, pytest.raises(psycopg2.errors.CheckViolation):
            _insert_event(
                conn,
                event_id="33333333-3333-3333-3333-333333333333",
                retention_class="forever_keep",
            )
    finally:
        conn.close()


def test_retention_class_check_accepts_all_three_documented_values(
    migrated_url: str,
) -> None:
    """audit_kept / raw_30d / derived_keep are all accepted."""
    conn = _connect(migrated_url)
    try:
        with conn:
            for i, rc in enumerate(("audit_kept", "raw_30d", "derived_keep")):
                _insert_event(
                    conn,
                    event_id=f"44444444-4444-4444-4444-44444444444{i}",
                    retention_class=rc,
                )
        # Cleanup so neighboring tests start clean.
        with conn, conn.cursor() as cur:
            cur.execute(
                "DELETE FROM events WHERE actor_id = 'test-actor'"
            )
    finally:
        conn.close()


def test_redaction_consistency_check_rejects_partial_redaction(
    migrated_url: str,
) -> None:
    """redacted=TRUE without redaction_run_id / redacted_at must be rejected."""
    conn = _connect(migrated_url)
    try:
        with conn, pytest.raises(psycopg2.errors.CheckViolation):
            # redaction_run_id intentionally omitted (NULL).
            _insert_event(
                conn,
                event_id="55555555-5555-5555-5555-555555555555",
                redacted=True,
            )
    finally:
        conn.close()


def test_redaction_consistency_check_rejects_orphan_redaction_metadata(
    migrated_url: str,
) -> None:
    """redacted=FALSE with redaction_run_id set must also be rejected."""
    conn = _connect(migrated_url)
    try:
        with conn, pytest.raises(psycopg2.errors.CheckViolation):
            _insert_event(
                conn,
                event_id="66666666-6666-6666-6666-666666666666",
                redacted=False,
                redaction_run_id="77777777-7777-7777-7777-777777777777",
                redacted_at="2026-05-15T13:00:00+00:00",
            )
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Partition routing.
# ---------------------------------------------------------------------------


def test_insert_into_2026_05_lands_in_2026_05_partition(migrated_url: str) -> None:
    """Rows with created_at in May 2026 go into events_2026_05."""
    conn = _connect(migrated_url)
    try:
        with conn:
            _insert_event(
                conn,
                event_id="88888888-8888-8888-8888-888888888888",
                created_at="2026-05-15T12:00:00+00:00",
            )
        with conn, conn.cursor() as cur:
            cur.execute(
                "SELECT count(*) FROM events_2026_05 WHERE event_id = %s",
                ("88888888-8888-8888-8888-888888888888",),
            )
            (count,) = cur.fetchone()
            assert count == 1
        # Cleanup.
        with conn, conn.cursor() as cur:
            cur.execute(
                "DELETE FROM events WHERE event_id = %s",
                ("88888888-8888-8888-8888-888888888888",),
            )
    finally:
        conn.close()


def test_insert_into_unmapped_month_raises(migrated_url: str) -> None:
    """A created_at outside any defined partition must raise — never silently lose data."""
    conn = _connect(migrated_url)
    try:
        # The PostgreSQL error class for "no partition for given key" is
        # actually 23514 (check_violation) on partitioned-no-default
        # tables; accept either CheckViolation or "no partition" message
        # text from the message inspection below.
        with conn, pytest.raises(psycopg2.errors.CheckViolation) as excinfo:
            _insert_event(
                conn,
                event_id="99999999-9999-9999-9999-999999999999",
                created_at="2027-01-15T12:00:00+00:00",
            )
        assert (
            "no partition" in str(excinfo.value).lower()
            or "check" in str(excinfo.value).lower()
        )
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Default values.
# ---------------------------------------------------------------------------


def test_redacted_defaults_to_false(migrated_url: str) -> None:
    """Newly inserted rows have redacted=FALSE without explicit assignment."""
    conn = _connect(migrated_url)
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO events
                        (event_id, event_type, actor_id,
                         payload_hash, prev_hash, hash, retention_class)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
                        "input.received",
                        "test-actor",
                        b"\x00" * 32,
                        b"\x00" * 32,
                        b"\x00" * 32,
                        "raw_30d",
                    ),
                )
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT redacted FROM events WHERE event_id = %s",
                    ("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",),
                )
                (val,) = cur.fetchone()
            assert val is False
        with conn, conn.cursor() as cur:
            cur.execute(
                "DELETE FROM events WHERE event_id = %s",
                ("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",),
            )
    finally:
        conn.close()


def test_created_at_defaults_to_now(migrated_url: str) -> None:
    """created_at default of now() lets event-emit code skip the column."""
    conn = _connect(migrated_url)
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO events
                        (event_id, event_type, actor_id,
                         payload_hash, prev_hash, hash, retention_class)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING created_at
                    """,
                    (
                        "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
                        "input.received",
                        "test-actor",
                        b"\x00" * 32,
                        b"\x00" * 32,
                        b"\x00" * 32,
                        "raw_30d",
                    ),
                )
                (created_at,) = cur.fetchone()
            assert created_at is not None
        with conn, conn.cursor() as cur:
            cur.execute(
                "DELETE FROM events WHERE event_id = %s",
                ("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",),
            )
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Migration idempotency.
# ---------------------------------------------------------------------------


def test_running_apply_twice_is_a_noop(migrated_url: str) -> None:
    """yoyo's ledger means re-running 'apply' against an up-to-date DB does nothing."""
    from app.migrations import cmd_apply

    rc = cmd_apply(database_url=migrated_url)
    assert rc == 0
    conn = _connect(migrated_url)
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT count(*) FROM _yoyo_migration")
            (count,) = cur.fetchone()
    finally:
        conn.close()
    # Migration count is still 1 — nothing was re-applied.
    assert count == 1


# ---------------------------------------------------------------------------
# Migration directory layout.
# ---------------------------------------------------------------------------


def test_migrations_directory_has_only_sql_files() -> None:
    """No stray .py / .yaml files — yoyo would try to load them as migrations."""
    migrations_dir = Path(__file__).resolve().parent.parent / "migrations"
    assert migrations_dir.is_dir()
    extensions = {f.suffix for f in migrations_dir.iterdir() if f.is_file()}
    assert extensions == {".sql"}, (
        f"unexpected non-SQL files in migrations/: {extensions}"
    )
