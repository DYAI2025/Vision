# Postgres

PostgreSQL is the event store for `backlog-core` per [`DEC-postgres-as-event-store`](../../decisions/DEC-postgres-as-event-store.md). This directory holds Postgres-specific deploy assets.

## Bootstrap behavior

- Service `postgres` defined in [`../../docker-compose.yml`](../../docker-compose.yml).
- Image: `postgres:16-alpine`. Internal Compose network only — no host port mapping.
- Database / user: `${POSTGRES_USER:-vision}` / `${POSTGRES_DB:-vision}` (from `.env`).
- Password: `${POSTGRES_PASSWORD}` — **REQUIRED**, no default; `docker compose up` fails fast if missing.
- Data persists in the `postgres-data` named volume (`project-agent-system_postgres-data` in `docker volume ls`).
- Healthcheck: `pg_isready -U <user> -d <db>` every 10s.

## Init scripts (`init/`)

[`init/`](init/) is mounted **read-only** into the Postgres container at `/docker-entrypoint-initdb.d/` and processed on the **first container start** (when the data volume is empty). The official `postgres` image runs:

- `*.sh` — shell scripts (executed)
- `*.sql` — SQL files (piped to `psql`)
- `*.sql.gz` — gzipped SQL (decompressed and piped)

…in alphabetical order. **On subsequent starts, init scripts are not re-run.**

This directory is currently empty by design. Schema creation lands in `TASK-postgres-events-schema` (Phase 2) via migrations run by `backlog-core`, not init scripts — keeping schema evolution under application-side control. If a future task needs *one-time* container-init logic (e.g., creating a non-default extension), it can add an `*.sql` here.

## Operator quick-access

[`../../scripts/psql.sh`](../../scripts/psql.sh) opens an interactive `psql` session against the running Postgres container. Reads `POSTGRES_USER` / `POSTGRES_DB` from `.env`; falls back to compose defaults if `.env` is absent.

```bash
./scripts/psql.sh                     # interactive shell
./scripts/psql.sh -c "SELECT 1"       # one-shot query
./scripts/psql.sh -c "\dt"            # list tables
./scripts/psql.sh -f scripts/foo.sql  # run a SQL file
```

The helper requires Docker + `docker compose` and the `postgres` service running.

## Backup and restore

Per `DEC-postgres-as-event-store`, backups use `pg_dump --format=directory --jobs=N` to produce host-independent archives. The full backup / restore tooling and runbook are added by:

- `TASK-backup-script` → `scripts/backup.sh`
- `TASK-restore-script` → `scripts/restore.sh`
- `TASK-phase-7-manual-testing` → runbook in `4-deploy/runbooks/`
