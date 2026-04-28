# Postgres init scripts

This directory is mounted **read-only** into the Postgres container at `/docker-entrypoint-initdb.d/`. The Postgres image processes `*.sh`, `*.sql`, and `*.sql.gz` files here alphabetically on the **first container start only** (when the data volume is empty). On subsequent boots they are not re-run.

See [`../README.md`](../README.md) for the full bootstrap story.

This directory currently contains no init scripts. Schema creation is delivered by `TASK-postgres-events-schema` (Phase 2) via migrations through `backlog-core`, not init scripts.

If you add a file here:
- Name it `NN-description.sql` (numeric prefix) to control execution order.
- Make it idempotent if possible (`CREATE TABLE IF NOT EXISTS` rather than bare `CREATE TABLE`).
- Note the file in [`../README.md`](../README.md) so operators can see what runs at first start.
