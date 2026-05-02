# DEC-postgres-migration-tool: yoyo-migrations is the schema migration tool for `backlog-core`

**Status**: Active

**Category**: Convention

**Scope**: backend (`backlog-core` only — the only component with a database)

**Source**: [DEC-postgres-as-event-store](DEC-postgres-as-event-store.md), [REQ-MNT-env-driven-config](../1-spec/requirements/REQ-MNT-env-driven-config.md), [REQ-REL-backup-restore-fidelity](../1-spec/requirements/REQ-REL-backup-restore-fidelity.md)

**Last updated**: 2026-05-02

## Context

`TASK-postgres-bootstrap` mounted `4-deploy/postgres/init/` for first-start Postgres init scripts but explicitly deferred schema creation to "Phase 2 via migrations run by `backlog-core`". `TASK-postgres-events-schema` is the first such schema task — and every later Phase-2 schema task (`TASK-postgres-consent-schema`, `TASK-postgres-events-partitioning`, `TASK-subject-index-matview`) plus Phase-4's RTBF cascade and Phase-7's restore flow all depend on having a single agreed migration tool.

`DEC-postgres-as-event-store` § "Required checks" #1 mandates that schema changes be **forward-compatible with existing event data** — no destructive migration of historical events. That rules out the "drop init scripts in `4-deploy/postgres/init/`" approach (which never re-runs on subsequent container starts and offers no upgrade path) and demands a migration tool that supports versioning, idempotent application, and a tracked migration ledger.

`backlog-core` uses raw `asyncpg` (not SQLAlchemy ORM) per `DEC-backend-stack-python-fastapi`'s "asyncpg (where applicable)" direction. The migration tool must therefore be ORM-agnostic and play well with raw-SQL migrations.

## Decision

The schema migration tool for `backlog-core` is **`yoyo-migrations`** (the `yoyo-migrations` PyPI package, used in raw-SQL mode).

Specific shape:

- Migration files live under **`3-code/backlog-core/migrations/`** as `NNNN_descriptive-kebab-name.sql` files (4-digit zero-padded sequence number, `_` separator, kebab-case description). Examples: `0001_create-events-table.sql`, `0002_create-consent-tables.sql`.
- The migration ledger lives in the same Postgres database as a `_yoyo_migration` table managed by yoyo. yoyo creates and updates this table; we never write to it directly.
- Migrations are **forward-only** — no `down` / rollback files at MVP. `DEC-postgres-as-event-store`'s "no destructive migration of historical events" rule, combined with append-only-by-convention semantics, makes rollback unsafe and unnecessary. If a migration needs to be undone in practice, the right shape is a **new forward migration** (e.g., `0007_revert-0006-foo.sql`), not a yoyo `down` file.
- Migrations apply via **`uv run --frozen python -m app.migrations apply`**, an entry point in `3-code/backlog-core/app/migrations.py` that wraps yoyo's programmatic API. The entry point reads `DATABASE_URL` from env and refuses to run if the env var is missing.
- Migrations do **not** apply automatically on FastAPI startup. Schema is the operator's responsibility — `app.main`'s lifespan assumes the schema already exists; if it doesn't, health-checks correctly degrade. This separation means a misconfigured deploy fails visibly at health-check time rather than silently mutating the database when an unrelated container restarts.
- The install runbook (`4-deploy/runbooks/install.md`) and the future operator CLI command `vision migrate` (deferred to a Phase-2/3 cli task) both invoke the entry point.
- Tests apply migrations against a real Postgres 16 container provisioned by `testcontainers-python` (per `DEC-postgres-schema-test-strategy` if recorded later, or this decision's § "Required patterns" until then) — schema correctness cannot be verified against a `FakePool`.

Why yoyo and not the alternatives:

- **Alembic** (rejected for this project): industry-standard but built around SQLAlchemy ORM machinery. We use raw asyncpg; we'd carry Alembic's metadata-driven migration generation as dead weight while writing all migrations as raw `op.execute(...)` strings anyway. Yoyo's raw-SQL-first model matches our "schema is owned by SQL, not generated from Python classes" stance.
- **Hand-rolled `migrations/NNNN_*.sql` + small runner script** (rejected): would require us to write and maintain the ledger logic, idempotency, lock-acquisition, and concurrency handling that yoyo already gets right. Reinventing for no gain.
- **`4-deploy/postgres/init/*.sql` only** (rejected): runs only on first container start. No upgrade path. Already documented as inadequate in the postgres bootstrap README.

## Enforcement

### Trigger conditions

- **Specification phase**: n/a.
- **Design phase**: any design doc that introduces a new Postgres table, index, or partition for `backlog-core` MUST be implementable as a yoyo migration (raw SQL). Designs that require non-SQL schema operations (e.g., extension pre-installation, role grants) note the carve-out explicitly.
- **Code phase**: every schema task in `backlog-core` adds at least one new `migrations/NNNN_*.sql` file and verifies it via `testcontainers-python` integration tests. Schema is never edited in-place — corrections land as new migrations.
- **Deploy phase**: the install runbook runs `python -m app.migrations apply` after `docker compose up` and before the smoke test. The restore runbook (per `REQ-REL-backup-restore-fidelity`) reapplies migrations after restore in case the backup-source DB was on an older migration generation.

### Required patterns

- New schema lands as a numbered migration in `3-code/backlog-core/migrations/`. Sequence number is 4-digit zero-padded and increments monotonically; gaps in the sequence are a smell.
- Migration filenames are descriptive kebab-case after the prefix: `0001_create-events-table.sql`, `0002_create-consent-tables.sql`. Filename describes what the migration *introduces*, not why.
- Migrations contain raw SQL only. No transactional DDL wrappers (yoyo wraps each migration in a transaction by default; `BEGIN`/`COMMIT` in the file is redundant and breaks yoyo's transaction handling).
- Migrations are idempotent only at the yoyo-ledger level — yoyo never re-runs an applied migration. Individual SQL statements may use `IF NOT EXISTS` defensively where it costs nothing, but this is not required.
- The application code in `app/migrations.py` reads `DATABASE_URL` from env (per `REQ-MNT-env-driven-config`); fails fast with a clear error if missing.
- Testing: every migration is verified by at least one test in `tests/test_*_schema.py` that applies the migration to a real Postgres container, asserts the resulting schema (table existence, column types, indexes, constraints), and exercises behavior the migration enables (e.g., a CHECK constraint actually rejects an invalid value).

### Required checks

1. Before merging any schema-modifying PR, confirm a new migration file exists under `3-code/backlog-core/migrations/`.
2. Confirm the migration's sequence number is monotonically next (no skips).
3. Confirm the migration applies cleanly via the test suite (testcontainers Postgres 16 must report no errors).
4. Confirm `_yoyo_migration` ledger contains the new migration after the test run.

### Prohibited patterns

- Editing an already-applied migration file. Once a migration has shipped to any environment, treat it as immutable. Corrections land as new migrations.
- Adding a yoyo `down`-style rollback file. Forward-only at MVP per the rationale above.
- Running migrations from FastAPI's lifespan (`app.main`'s startup handler). Migrations are an operator action, not a side effect of starting the service.
- Storing schema in any directory other than `3-code/backlog-core/migrations/`. `4-deploy/postgres/init/` is reserved for *one-time* container-init logic (e.g., extension `CREATE EXTENSION` if any becomes necessary) and is not a substitute for migrations.
- Skipping the testcontainers integration test for a migration. Schema is the trust boundary; "ruff and mypy passed" is not sufficient evidence.

## Reconsider trigger

Revisit this decision if:

- The migration cadence grows to where forward-only becomes painful (e.g., a wrong migration ships to prod and the rollback cost dominates engineering time).
- A second component acquires its own database — at that point we either record a parallel `DEC-<component>-migration-tool` or generalize this decision to system-wide.
- yoyo upstream stops being maintained (last release > 18 months ago at decision-update time would be the trigger).
