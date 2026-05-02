"""Schema migration runner for backlog-core.

Wraps yoyo-migrations' programmatic API per
``DEC-postgres-migration-tool``. Migrations live as numbered ``.sql`` files
under ``3-code/backlog-core/migrations/`` and apply forward-only. The
operator runs::

    uv run --frozen python -m app.migrations apply

…after ``docker compose up`` and before the smoke test. The install
runbook (per ``REQ-PORT-vps-deploy``) and the future ``vision migrate``
operator command both invoke this entry point.

Migrations do **not** apply automatically on FastAPI startup — schema is
the operator's responsibility. ``app.main``'s lifespan assumes the schema
already exists; if it doesn't, ``/v1/health`` correctly degrades.

Two subcommands are exposed:

- ``apply``: applies all pending migrations.
- ``status``: lists applied / pending migrations without modifying state.

Both read ``DATABASE_URL`` from env. Missing env var → fail-fast with a
clear error message per ``REQ-MNT-env-driven-config``.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from yoyo import get_backend, read_migrations

if TYPE_CHECKING:
    from yoyo.migrations import MigrationList


def _migrations_dir() -> Path:
    """Resolve ``3-code/backlog-core/migrations/`` regardless of cwd.

    The runner is invoked from inside the component dir at deploy time and
    from arbitrary cwds in tests. Anchoring on this module's location keeps
    both call sites correct.
    """
    return Path(__file__).resolve().parent.parent / "migrations"


def _backend_url(database_url: str) -> str:
    """Convert an asyncpg-style URL to yoyo's expected format.

    The application uses ``postgresql://`` URLs read by asyncpg. yoyo's
    backend dispatch wants ``postgresql+psycopg2://`` to select the sync
    driver explicitly. We do the substitution here so callers (and the
    install runbook) don't need to know about the driver split.

    Already-prefixed URLs pass through unchanged so power users can override.
    """
    if database_url.startswith(("postgresql+", "postgres+")):
        return database_url
    if database_url.startswith("postgresql://"):
        return "postgresql+psycopg2://" + database_url[len("postgresql://") :]
    if database_url.startswith("postgres://"):
        return "postgresql+psycopg2://" + database_url[len("postgres://") :]
    raise ValueError(
        f"DATABASE_URL must start with 'postgresql://' or 'postgres://'; "
        f"got prefix {database_url.split(':', 1)[0]!r}"
    )


def _read_database_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError(
            "DATABASE_URL is required — backlog-core migrations fail fast "
            "per REQ-MNT-env-driven-config."
        )
    return url


def _load_migrations() -> MigrationList:
    return read_migrations(str(_migrations_dir()))


def cmd_apply(database_url: str | None = None) -> int:
    """Apply all pending migrations. Returns exit code (0 = ok)."""
    url = _backend_url(database_url or _read_database_url())
    backend = get_backend(url)
    migrations = _load_migrations()
    pending = backend.to_apply(migrations)
    with backend.lock():
        backend.apply_migrations(pending)
    print(f"Applied {len(pending)} migration(s).")
    return 0


def cmd_status(database_url: str | None = None) -> int:
    """List applied + pending migrations. Returns exit code (0 = ok)."""
    url = _backend_url(database_url or _read_database_url())
    backend = get_backend(url)
    migrations = _load_migrations()
    pending = list(backend.to_apply(migrations))
    rollback = list(backend.to_rollback(migrations))
    applied = [m for m in migrations if m not in pending]

    print(f"Applied ({len(applied)}):")
    for m in applied:
        print(f"  {m.id}")
    print(f"Pending ({len(pending)}):")
    for m in pending:
        print(f"  {m.id}")
    if rollback:
        # yoyo can roll back applied-but-removed migrations. The project is
        # forward-only per DEC-postgres-migration-tool, so anything here is
        # a smell — surface it but exit 0 (status is informational).
        print(
            f"WARNING: {len(rollback)} migration(s) applied to DB but missing "
            f"from {_migrations_dir()} — investigate before running apply.",
            file=sys.stderr,
        )
        for m in rollback:
            print(f"  {m.id}", file=sys.stderr)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m app.migrations",
        description="Schema migration runner for backlog-core (yoyo-migrations).",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("apply", help="Apply all pending migrations.")
    sub.add_parser("status", help="List applied and pending migrations.")
    args = parser.parse_args(argv)

    if args.cmd == "apply":
        return cmd_apply()
    if args.cmd == "status":
        return cmd_status()
    # argparse's required=True makes this unreachable, but mypy strict
    # wants every branch covered.
    parser.error(f"unknown command {args.cmd!r}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
