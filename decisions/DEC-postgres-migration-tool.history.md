# DEC-postgres-migration-tool: Trail

> Companion to `DEC-postgres-migration-tool.md`.
> AI agents read this only when evaluating whether the decision is still
> valid or when proposing a change or supersession.

## Alternatives considered

### Option A: yoyo-migrations (chosen)

- **Pros**:
  - Raw-SQL-first migration model matches the project's "schema is owned by SQL, not generated from a Python ORM" stance — `backlog-core` uses asyncpg directly, no SQLAlchemy.
  - Small (~300 LOC core), focused, mature (PyPI package since 2014; actively maintained).
  - Tracks applied migrations in a `_yoyo_migration` table the tool manages — no need for us to write ledger logic, lock-acquisition, or concurrency handling.
  - Wraps each migration in a transaction by default; safe rollback on failure.
  - Programmatic API works with asyncpg URLs (`postgresql://...`) via `psycopg2` for the migration runner only — production app code stays asyncpg-only; the migration tool's sync driver is acceptable because migrations run as a one-shot command, not in the request path.
  - Forward-only by convention is straightforward: just don't author `step()` rollback files.
- **Cons**:
  - Smaller ecosystem than Alembic — fewer tutorials, fewer "how do I X" StackOverflow hits.
  - Requires `psycopg2` (sync driver) for the runner side; we're already pulling in asyncpg, so this is a small-but-real second-driver dep.
  - The community-typical pattern uses Python-DSL migrations (`step("CREATE TABLE ...")`); our raw-SQL preference is supported (`.sql` files in the migrations dir) but is the less-documented path.

### Option B: Alembic

- **Pros**:
  - Industry standard — every Python developer recognizes the workflow; lots of tutorials and tooling integration (Pycharm, Cursor, etc.).
  - Auto-generation of migrations from SQLAlchemy model diffs (irrelevant for us since we don't use SQLAlchemy, but useful for projects that do).
  - Mature transactional handling; well-tested edge cases (concurrent migrations, broken-state recovery).
- **Cons**:
  - Built around SQLAlchemy. We'd use it as a glorified migration runner while writing every migration as `op.execute("raw SQL")` — paying for the ORM machinery without using it.
  - Heavier dep tree (Alembic + SQLAlchemy core minimum).
  - The auto-generation feature, the headline benefit, is dead weight for raw-SQL projects. We'd actively avoid `alembic revision --autogenerate` because it would try to model our schema in SQLAlchemy types, which is exactly what we don't want.
  - Steeper "what shape is a migration" cognitive cost — Alembic migrations are Python files with `upgrade()` / `downgrade()` functions even for raw-SQL workflows; the file shape adds noise relative to a `.sql` file.

### Option C: Hand-rolled `migrations/NNNN_*.sql` + small runner script

- **Pros**:
  - Zero new dependencies — just the asyncpg driver we already have.
  - Full control over the runner's behavior (idempotency strategy, lock-acquisition, error handling).
  - Easy to debug — every line is in our codebase.
- **Cons**:
  - Reinvents the wheel. yoyo, alembic, and others have already solved this; our runner would converge toward yoyo's shape over time.
  - Ledger management (which migrations applied, when, by whom) is real engineering work that we'd have to write and test ourselves.
  - Concurrency handling (two `migrations apply` invocations racing) requires advisory locks — easy to get subtly wrong.
  - The first incident where two operators run migrations at once and corrupt the ledger is a self-inflicted wound that no review catches until prod.

### Option D: `4-deploy/postgres/init/*.sql` only — no migration tool

- **Pros**:
  - Zero new dependencies; zero new code.
  - Already wired (the directory exists; the bootstrap mounts it).
- **Cons**:
  - **Runs once, on first container start.** Subsequent starts ignore it. Schema upgrades after the first deploy are simply not possible via this path.
  - Conflicts with `DEC-postgres-as-event-store` § "Required checks" #1 ("forward-compatible with existing event data — no destructive migration of historical events") — there is no migration mechanism at all, let alone a forward-compatible one.
  - The `4-deploy/postgres/README.md` already explicitly documents that init scripts are inadequate for schema evolution and points at "Phase 2 via migrations".

## Reasoning

Option A wins because:

1. **Raw SQL fits our model.** We picked raw asyncpg precisely because we want the schema to live in `.sql` files we can read with `psql` and grep with `rg`. yoyo treats `.sql` files as first-class migrations; Alembic treats them as a second-class workflow. The fit matters more than ecosystem size.

2. **Schema ownership is explicit and checkable.** With yoyo + raw-SQL files, a code reviewer reads the migration text and the test that exercises it. With Alembic + autogeneration, reviewers have to also reason about SQLAlchemy's diff inference. Fewer moving parts under review = fewer bugs.

3. **The known weaknesses are bounded.** yoyo's forward-only-by-convention bites if we ship a wrong migration to prod, but we have a small audience (Vincent + Ben) and Phase-7 tooling for backup/restore as a safety net. The smaller-ecosystem cost is real but the migrations themselves are simple SQL — there's no "how do I do X in yoyo" question that doesn't have a SQL answer.

4. **`psycopg2` for the runner is acceptable.** It only loads when migrations run, not in the request path. We already accepted "Postgres" as a single-vendor choice in `DEC-postgres-as-event-store`, so a Postgres-specific sync driver in dev tooling doesn't compromise portability further than already chosen.

Conditions that would invalidate this reasoning:

- A migration framework emerges that's natively async, ORM-agnostic, raw-SQL-first, and as mature as Alembic (e.g., a hypothetical `asyncpg-migrate`). Then revisit.
- The project picks up SQLAlchemy for any reason. Then Alembic becomes the obvious choice.
- A second component acquires a database. At that point either generalize this decision (swap "backlog-core" for "system-wide") or record a parallel decision.

## Human involvement

**Type**: ai-proposed/human-approved

**Notes**: AI proposed yoyo-migrations as part of three coupled choices for `TASK-postgres-events-schema` (migration tool, partitioning scope, schema test strategy). Human approved all three with the single response "Approved" on 2026-05-02 in the SDLC-execute-next-task skill flow. The two coupled choices (partitioning from day one + testcontainers-python for tests) are reflected in the migration's structure and the test suite respectively, but are properties of `TASK-postgres-events-schema` rather than of this DEC.

## Changelog

| Date | Change | Involvement |
|------|--------|-------------|
| 2026-05-02 | Initial decision — yoyo-migrations chosen as the schema migration tool for `backlog-core` | ai-proposed/human-approved |
