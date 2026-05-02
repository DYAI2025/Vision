# `TASK-postgres-events-schema` review-fix plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Resolve every issue surfaced in the in-session code review of the work-in-progress `TASK-postgres-events-schema` (Phase 2 #3) so the migration, runner, tests, DEC, and deploy integration ship as a single coherent green-CI commit set.

**Architecture:** Sequential atomic commits, each with TDD-shaped verification where the change is testable (test changes, runner hardening) and short doc-only commits where it isn't (DEC pin, runbook integration). The task order respects dependencies: SQL changes first (because partition extension changes the migration content other tasks build on), then test hardening, then runner hardening, then DEC convention pin, then deploy-pipeline integration, then a single verification round against a real Postgres, then closeout (tasks.md + CLAUDE.md + final push).

**Tech Stack:** Python 3.12 + asyncpg + yoyo-migrations + psycopg2 + testcontainers-python + pytest + ruff + mypy strict + uv. Local Docker daemon = colima (currently stopped — Task 8 starts it).

**Worktree note:** Plan generated without a dedicated worktree. Working directly on `main` per the established session pattern (the cast-quotes-followup followed the same pattern). All edits are scoped to `backlog-core/`, the new DEC, `install_vps.sh`, the runbook, and final closeout files; no surprise blast radius.

**Starting state:**
- HEAD: `bece603` (`docs(tasks): close TASK-ingress-tailscale-config drift-script note`).
- Working tree has uncommitted changes for `TASK-postgres-events-schema` so far: a new DEC pair, the migration SQL, the runner, the tests, the pyproject.toml updates, the lockfile regen, the cross-refs in `CLAUDE.component.md` and `4-deploy/CLAUDE.deploy.md`, and the `In Progress` flip on the task row in `tasks.md`. None of this has been committed yet.
- `git status` should show ~10 modified files and 3 untracked (`migrations/`, `app/migrations.py`, `tests/test_events_schema.py`, the two DEC files).
- Run `git diff --stat` before starting to confirm the baseline matches.

**Definition of Done for the whole plan:**
1. All review issues (I-1, I-2, M-1, M-2, M-3, M-4, M-5) addressed in code; the "pre-existing" plan-saving convention either confirmed already adequate or amended with one line.
2. The schema migration applies cleanly against Postgres 16 via testcontainers, all 19 postgres-marked tests green.
3. `install_vps.sh` runs migrations between `compose up` healthy-check and operator's smoke test.
4. `tasks.md` row for `TASK-postgres-events-schema` flipped from `In Progress` to `Done` with closeout notes; row for `TASK-postgres-events-partitioning` (Phase 2 #5) narrowed to "rolling-future cron + retention-aware sweep helpers" since this task introduces the partitioning structure.
5. `CLAUDE.md` Current State updated: 19/107 → 20/107, Phase 2 progress 2/16 → 3/16, decision count 15 → 16 (the new `DEC-postgres-migration-tool`).
6. Three or more focused commits land and push to `origin/main`.

---

## Background — what the code review surfaced

For full context, see `docs/plans/` is not a published document set; the review was an in-session response under the `/code-reviewer` skill. The summarised findings are reproduced in each task's "Why" section so this plan stands alone.

The review's bottom line: **conditional approval, not yet shippable**. Two important issues need decisions before commit (I-1, I-2) and the verification gap (testcontainers tests not yet executed against a real Postgres) was hard-blocking per the DEC's own required checks.

The user's directive: *"fixing all bugs including the pre-existing completely"* — so this plan addresses every flagged item, including the M-tier (minor, non-blocking) items and the "pre-existing observation" about plan-saving convention drift.

---

## Task 1: Extend partition pre-creation to 12 months (I-2)

**Why:** The current migration creates only `events_2026_05` and `events_2026_06`. After 2026-06-30, any insert with `created_at >= 2026-07-01` raises `23514` "no partition of relation found for row". `TASK-postgres-events-partitioning` (Phase 2 #5) ships the rolling-future partition cron, but we have no guarantee that task lands before mid-June. Pre-creating 12 months of partitions in this migration costs ~10 extra `CREATE TABLE` statements and removes the cliff entirely; #5's scope cleanly narrows to "automation around partitions" rather than "introduce partitioning + automation."

**Files:**
- Modify: `3-code/backlog-core/migrations/0001_create-events-table.sql` (the partition section near the bottom, currently 2 partition blocks at lines ~165-170)

**Step 1: Read the current partition section**

```bash
cd /Users/benjaminpoersch/Projects/Vision/ai-sdlc-scaffold-main
grep -n 'PARTITION OF' 3-code/backlog-core/migrations/0001_create-events-table.sql
```

Expected: 2 matches (the `events_2026_05` and `events_2026_06` blocks).

**Step 2: Replace the 2-month section with a 12-month section**

Find this block in `0001_create-events-table.sql` (lines roughly 165-170):

```sql
CREATE TABLE events_2026_05 PARTITION OF events
    FOR VALUES FROM ('2026-05-01 00:00:00+00') TO ('2026-06-01 00:00:00+00');

CREATE TABLE events_2026_06 PARTITION OF events
    FOR VALUES FROM ('2026-06-01 00:00:00+00') TO ('2026-07-01 00:00:00+00');
```

Replace it with the 12-month version (May 2026 through April 2027 inclusive):

```sql
CREATE TABLE events_2026_05 PARTITION OF events
    FOR VALUES FROM ('2026-05-01 00:00:00+00') TO ('2026-06-01 00:00:00+00');

CREATE TABLE events_2026_06 PARTITION OF events
    FOR VALUES FROM ('2026-06-01 00:00:00+00') TO ('2026-07-01 00:00:00+00');

CREATE TABLE events_2026_07 PARTITION OF events
    FOR VALUES FROM ('2026-07-01 00:00:00+00') TO ('2026-08-01 00:00:00+00');

CREATE TABLE events_2026_08 PARTITION OF events
    FOR VALUES FROM ('2026-08-01 00:00:00+00') TO ('2026-09-01 00:00:00+00');

CREATE TABLE events_2026_09 PARTITION OF events
    FOR VALUES FROM ('2026-09-01 00:00:00+00') TO ('2026-10-01 00:00:00+00');

CREATE TABLE events_2026_10 PARTITION OF events
    FOR VALUES FROM ('2026-10-01 00:00:00+00') TO ('2026-11-01 00:00:00+00');

CREATE TABLE events_2026_11 PARTITION OF events
    FOR VALUES FROM ('2026-11-01 00:00:00+00') TO ('2026-12-01 00:00:00+00');

CREATE TABLE events_2026_12 PARTITION OF events
    FOR VALUES FROM ('2026-12-01 00:00:00+00') TO ('2027-01-01 00:00:00+00');

CREATE TABLE events_2027_01 PARTITION OF events
    FOR VALUES FROM ('2027-01-01 00:00:00+00') TO ('2027-02-01 00:00:00+00');

CREATE TABLE events_2027_02 PARTITION OF events
    FOR VALUES FROM ('2027-02-01 00:00:00+00') TO ('2027-03-01 00:00:00+00');

CREATE TABLE events_2027_03 PARTITION OF events
    FOR VALUES FROM ('2027-03-01 00:00:00+00') TO ('2027-04-01 00:00:00+00');

CREATE TABLE events_2027_04 PARTITION OF events
    FOR VALUES FROM ('2027-04-01 00:00:00+00') TO ('2027-05-01 00:00:00+00');
```

Also update the comment block immediately above the partition definitions to reflect the new window — change:

```
-- First partition: current month (2026-05) and a grace partition for
-- 2026-06 so the system has at least one future partition pre-created.
```

to:

```
-- Initial 12 months of partitions: May 2026 through April 2027 inclusive.
-- This gives `TASK-postgres-events-partitioning` (Phase 2 #5) a year-long
-- window to land its rolling-future cron without any insert ever failing
-- with "no partition for given key". The cron's job at that point is
-- maintenance — pre-creating month N+12 each month — not establishing
-- partitioning.
```

**Step 3: Update `test_first_two_partitions_exist` to assert the new shape**

The test currently asserts exactly 2 partitions. With 12 partitions it should assert all 12. Modify `tests/test_events_schema.py`:

Find:

```python
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
```

Replace with:

```python
def test_initial_twelve_months_of_partitions_exist(migrated_url: str) -> None:
    """Migration pre-creates 12 months of partitions (May 2026 → April 2027)."""
    expected = [
        "events_2026_05", "events_2026_06", "events_2026_07", "events_2026_08",
        "events_2026_09", "events_2026_10", "events_2026_11", "events_2026_12",
        "events_2027_01", "events_2027_02", "events_2027_03", "events_2027_04",
    ]
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
    assert partitions == expected
```

**Step 4: Re-run lint / type-check / non-postgres tests**

```bash
cd /Users/benjaminpoersch/Projects/Vision/ai-sdlc-scaffold-main/3-code/backlog-core
uv run --frozen ruff check .
uv run --frozen mypy app
uv run --frozen pytest -q -m 'not postgres'
```

Expected:
- ruff: `All checks passed!`
- mypy: `Success: no issues found in 4 source files`
- pytest: `15 passed, 19 deselected`

**Step 5: Commit (do NOT push yet — chain of commits coming)**

```bash
cd /Users/benjaminpoersch/Projects/Vision/ai-sdlc-scaffold-main
git add 3-code/backlog-core/migrations/0001_create-events-table.sql \
        3-code/backlog-core/tests/test_events_schema.py
git commit -m "$(cat <<'EOF'
feat(backlog-core): pre-create 12 months of events partitions in 0001

Closes I-2 from the in-session review of TASK-postgres-events-schema.
Original migration created only 2026_05 and 2026_06 partitions; after
2026-06-30 inserts would raise 23514 "no partition for given key" until
TASK-postgres-events-partitioning (Phase 2 #5) ships the rolling-future
cron. Extending the initial window to 12 months removes the cliff and
narrows #5's scope to maintenance-rate partition creation rather than
"introduce partitioning + automate it".

Test updated from test_first_two_partitions_exist to
test_initial_twelve_months_of_partitions_exist asserting the full set.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 2: Per-test unique actor IDs (M-1)

**Why:** Two tests insert with `actor_id = "test-actor"` and clean up via `DELETE FROM events WHERE actor_id = 'test-actor'`. If a future test uses the same actor and runs first under non-default pytest ordering (`--lf`, `--ff`, random), the cleanup deletes neighbor data. Use unique actor IDs per test so each test owns a disjoint key set.

**Files:**
- Modify: `3-code/backlog-core/tests/test_events_schema.py` — three test functions:
  - `test_event_type_check_accepts_every_documented_type`
  - `test_retention_class_check_accepts_all_three_documented_values`
  - `_insert_event` (the helper) — gains an `actor_id` parameter override consumers can specify

**Step 1: Update `test_event_type_check_accepts_every_documented_type`**

Find:

```python
def test_event_type_check_accepts_every_documented_type(migrated_url: str) -> None:
    """Every event_type listed in data-model.md § Event-type catalog is accepted."""
    documented = [
        ...
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
```

Replace the `actor_id` filter and explicitly pass it through:

```python
def test_event_type_check_accepts_every_documented_type(migrated_url: str) -> None:
    """Every event_type listed in data-model.md § Event-type catalog is accepted."""
    documented = [
        ...  # unchanged
    ]
    actor = "test-actor-event-types"  # unique per test for safe cleanup
    conn = _connect(migrated_url)
    try:
        with conn:
            for i, et in enumerate(documented):
                _insert_event(
                    conn,
                    event_id=f"22222222-2222-2222-2222-{i:012d}",
                    event_type=et,
                    actor_id=actor,
                )
        with conn, conn.cursor() as cur:
            cur.execute("DELETE FROM events WHERE actor_id = %s", (actor,))
    finally:
        conn.close()
```

**Step 2: Update `test_retention_class_check_accepts_all_three_documented_values`**

Same pattern — replace `'test-actor'` with `'test-actor-retention-classes'` and parameterize the cleanup query.

```python
def test_retention_class_check_accepts_all_three_documented_values(
    migrated_url: str,
) -> None:
    """audit_kept / raw_30d / derived_keep are all accepted."""
    actor = "test-actor-retention-classes"
    conn = _connect(migrated_url)
    try:
        with conn:
            for i, rc in enumerate(("audit_kept", "raw_30d", "derived_keep")):
                _insert_event(
                    conn,
                    event_id=f"44444444-4444-4444-4444-44444444444{i}",
                    retention_class=rc,
                    actor_id=actor,
                )
        with conn, conn.cursor() as cur:
            cur.execute("DELETE FROM events WHERE actor_id = %s", (actor,))
    finally:
        conn.close()
```

**Step 3: Verify the `_insert_event` helper already supports `actor_id` override**

The helper takes `**overrides: object` and merges into a `base` dict that has `"actor_id": "test-actor"`. Passing `actor_id="..."` already works via the override mechanism. No change needed in the helper itself.

Run a quick grep to confirm no other test relies on the literal `'test-actor'` filter for cleanup:

```bash
grep -n "test-actor" 3-code/backlog-core/tests/test_events_schema.py
```

Expected: only the matches you just edited (within `test_event_type_check_accepts_every_documented_type` and `test_retention_class_check_accepts_all_three_documented_values`). Any other match indicates a missed cleanup site to fix.

**Step 4: Re-run linters + non-postgres tests**

```bash
cd /Users/benjaminpoersch/Projects/Vision/ai-sdlc-scaffold-main/3-code/backlog-core
uv run --frozen ruff check .
uv run --frozen mypy app
uv run --frozen pytest -q -m 'not postgres'
```

Expected: same as Task 1 Step 4 — all green; 15 passed, 19 deselected.

**Step 5: Commit**

```bash
cd /Users/benjaminpoersch/Projects/Vision/ai-sdlc-scaffold-main
git add 3-code/backlog-core/tests/test_events_schema.py
git commit -m "$(cat <<'EOF'
test(backlog-core): unique actor IDs per cleanup-needed schema test

Closes M-1 from the in-session review. test_event_type_check_accepts_
every_documented_type and test_retention_class_check_accepts_all_three_
documented_values both used actor_id='test-actor' and cleaned up by
deleting that actor's rows. Under non-default pytest ordering, a future
test using the same actor that ran first would have its rows deleted by
these tests' cleanup. Switched to per-test unique actors and
parameterized the DELETE query.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 3: Use `psycopg2.extras.Json` for `payload` (M-2)

**Why:** The `_insert_event` helper passes `payload` as a JSON string literal `'{"hello": "world"}'`. Postgres parses the string into JSONB on insert, so it works — but the idiomatic psycopg2 pattern is to wrap dict values with `psycopg2.extras.Json(...)`, which adapts the value at the driver level rather than relying on Postgres-side parsing. Same behavior; clearer shape; future tests inserting dicts directly will copy this pattern.

**Files:**
- Modify: `3-code/backlog-core/tests/test_events_schema.py` — the `_insert_event` helper's `base` dict.

**Step 1: Add the `Json` import**

Find the existing imports near the top:

```python
import psycopg2
import pytest
```

Add the `Json` import alongside:

```python
import psycopg2
import psycopg2.extras
import pytest
```

**Step 2: Update `_insert_event`'s default `payload`**

Find:

```python
    base: dict[str, object] = {
        "event_id": "00000000-0000-0000-0000-000000000001",
        "event_type": "input.received",
        ...
        "payload": '{"hello": "world"}',
        ...
    }
```

Replace the `payload` line with:

```python
        "payload": psycopg2.extras.Json({"hello": "world"}),
```

**Step 3: Re-run linters + non-postgres tests**

```bash
cd /Users/benjaminpoersch/Projects/Vision/ai-sdlc-scaffold-main/3-code/backlog-core
uv run --frozen ruff check .
uv run --frozen mypy app
uv run --frozen pytest -q -m 'not postgres'
```

Expected: green; 15 passed, 19 deselected.

If ruff complains about `psycopg2.extras` being unused (because no test actually inserts a custom payload yet), keep the import — it documents the canonical pattern and the testcontainers run will exercise it via `_insert_event`'s default.

**Step 4: Commit**

```bash
cd /Users/benjaminpoersch/Projects/Vision/ai-sdlc-scaffold-main
git add 3-code/backlog-core/tests/test_events_schema.py
git commit -m "$(cat <<'EOF'
test(backlog-core): use psycopg2.extras.Json for payload in _insert_event

Closes M-2 from the in-session review. _insert_event's default payload
was a JSON string literal; postgres parses it into JSONB on insert so
behaviour was correct, but the idiomatic psycopg2 pattern is the Json
adapter. Same insert; clearer call site for future tests that pass dicts.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 4: `cmd_status` exits 1 on unexpected rollback warnings (M-3)

**Why:** The `app/migrations.py` `cmd_status` subcommand prints a warning to stderr when yoyo finds applied migrations on the DB that don't exist on disk. Per `DEC-postgres-migration-tool`, migrations are immutable — so if `to_rollback()` returns anything, that's a hard incident: a migration file got dropped from a branch merge or was renamed without a forward migration. Print-only is too quiet; CI should fail. Convert to a non-zero exit.

**Files:**
- Modify: `3-code/backlog-core/app/migrations.py` — the `cmd_status` function.
- Add: `3-code/backlog-core/tests/test_migrations_runner.py` — a new unit-test file for the runner (no Postgres needed; we can mock yoyo's backend).

**Step 1: Write the failing test first**

Create `3-code/backlog-core/tests/test_migrations_runner.py`:

```python
"""Unit tests for app/migrations.py — the runner glue, not the SQL.

These tests do not require Postgres; they exercise URL transformation,
argv handling, and the cmd_status / cmd_apply branching logic by
substituting fake backends.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import patch

import pytest

from app.migrations import _backend_url, cmd_status


class _FakeBackend:
    """Minimal yoyo-like backend for unit tests."""

    def __init__(self, applied_ids: list[str], pending_ids: list[str], rollback_ids: list[str]):
        self._applied = applied_ids
        self._pending = pending_ids
        self._rollback = rollback_ids

    def to_apply(self, _all_migrations: Any) -> list[Any]:
        return [_FakeMigration(i) for i in self._pending]

    def to_rollback(self, _all_migrations: Any) -> list[Any]:
        return [_FakeMigration(i) for i in self._rollback]


class _FakeMigration:
    def __init__(self, mid: str) -> None:
        self.id = mid


def _patch_runner(
    *,
    pending: list[str],
    rollback: list[str],
) -> Any:
    """Monkey-patch yoyo loading so cmd_status reads our fakes."""
    backend = _FakeBackend(applied_ids=[], pending_ids=pending, rollback_ids=rollback)
    return patch.multiple(
        "app.migrations",
        get_backend=lambda _url: backend,
        read_migrations=lambda _path: [_FakeMigration(i) for i in (pending + rollback)],
    )


def test_cmd_status_exits_zero_when_no_unexpected_rollback() -> None:
    with _patch_runner(pending=["0002_foo"], rollback=[]):
        rc = cmd_status(database_url="postgresql://ignored")
    assert rc == 0


def test_cmd_status_exits_one_when_db_has_orphan_migrations() -> None:
    """Per DEC-postgres-migration-tool: migrations are immutable. A
    to_rollback() result means the DB has a migration the code base
    doesn't know about — a hard incident, not a warning."""
    with _patch_runner(pending=[], rollback=["0001_orphan-migration"]):
        rc = cmd_status(database_url="postgresql://ignored")
    assert rc == 1


def test_backend_url_rejects_missing_scheme() -> None:
    with pytest.raises(ValueError, match="postgresql://"):
        _backend_url("not-a-real-url")
```

**Step 2: Run the new tests — they fail**

```bash
cd /Users/benjaminpoersch/Projects/Vision/ai-sdlc-scaffold-main/3-code/backlog-core
uv run --frozen pytest tests/test_migrations_runner.py -v
```

Expected: `test_cmd_status_exits_one_when_db_has_orphan_migrations` FAILS because the current implementation returns 0 even with rollback warnings. The other two tests should pass (URL rejection is already implemented; status-exit-zero-when-clean already works).

**Step 3: Implement the change in `app/migrations.py`**

Find the `cmd_status` function. The current shape is:

```python
def cmd_status(database_url: str | None = None) -> int:
    ...
    if rollback:
        print(
            f"WARNING: {len(rollback)} migration(s) applied to DB but missing "
            f"from {_migrations_dir()} — investigate before running apply.",
            file=sys.stderr,
        )
        for m in rollback:
            print(f"  {m.id}", file=sys.stderr)
    return 0
```

Change the return on the rollback branch from `return 0` to `return 1` and tighten the wording:

```python
def cmd_status(database_url: str | None = None) -> int:
    ...
    if rollback:
        # Per DEC-postgres-migration-tool: migrations are immutable. Anything
        # in to_rollback() is a hard incident — a migration file was dropped
        # or renamed without a forward migration. Exit non-zero so CI / cron
        # health checks treat this as a fault, not a warning.
        print(
            f"ERROR: {len(rollback)} migration(s) applied to DB but missing "
            f"from {_migrations_dir()} — investigate immediately. "
            f"Per DEC-postgres-migration-tool, migrations are immutable.",
            file=sys.stderr,
        )
        for m in rollback:
            print(f"  {m.id}", file=sys.stderr)
        return 1
    return 0
```

**Step 4: Re-run the new tests — they all pass**

```bash
cd /Users/benjaminpoersch/Projects/Vision/ai-sdlc-scaffold-main/3-code/backlog-core
uv run --frozen pytest tests/test_migrations_runner.py -v
```

Expected: all 3 tests pass.

**Step 5: Run the full backlog-core suite (non-postgres) to confirm no regression**

```bash
uv run --frozen ruff check .
uv run --frozen mypy app
uv run --frozen pytest -q -m 'not postgres'
```

Expected:
- ruff: `All checks passed!`
- mypy: `Success: no issues found in 4 source files`
- pytest: `18 passed, 19 deselected` (15 prior + 3 new from test_migrations_runner.py)

**Step 6: Commit**

```bash
cd /Users/benjaminpoersch/Projects/Vision/ai-sdlc-scaffold-main
git add 3-code/backlog-core/app/migrations.py 3-code/backlog-core/tests/test_migrations_runner.py
git commit -m "$(cat <<'EOF'
fix(backlog-core): cmd_status exits 1 on unexpected rollback findings

Closes M-3 from the in-session review. yoyo's to_rollback() returns
migrations applied to the DB that no longer exist on disk. Per
DEC-postgres-migration-tool migrations are immutable, so any non-empty
result from to_rollback() is a hard incident: a migration file was
dropped or renamed without a forward migration. Previously we printed
a warning and exited 0; now we print an error and exit 1, so CI and
cron health checks fail visibly.

New tests/test_migrations_runner.py covers the runner glue (URL
transformation, status branching) without requiring Postgres.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 5: `_backend_url` rejects unsupported drivers (M-5)

**Why:** Operators who set `DATABASE_URL=postgresql+asyncpg://...` (an async-driver-explicit URL) would have it pass through unchanged into yoyo's psycopg2 backend, which would fail with a confusing "no driver named asyncpg" error. Reject the unsupported driver upfront with a clear message that names the right form.

**Files:**
- Modify: `3-code/backlog-core/app/migrations.py` — the `_backend_url` function.
- Modify: `3-code/backlog-core/tests/test_migrations_runner.py` — new test cases.

**Step 1: Write the failing test**

Append to `tests/test_migrations_runner.py`:

```python
def test_backend_url_passes_psycopg2_through_unchanged() -> None:
    assert _backend_url("postgresql+psycopg2://user:pw@host/db") == \
        "postgresql+psycopg2://user:pw@host/db"


def test_backend_url_rewrites_postgresql_scheme_to_psycopg2() -> None:
    assert _backend_url("postgresql://user:pw@host/db") == \
        "postgresql+psycopg2://user:pw@host/db"


def test_backend_url_rejects_explicit_asyncpg_driver() -> None:
    """Per the runner: yoyo uses psycopg2 (sync); explicit asyncpg URLs
    would silently fail at backend dispatch time. Reject early."""
    with pytest.raises(ValueError, match="psycopg2"):
        _backend_url("postgresql+asyncpg://user:pw@host/db")


def test_backend_url_rejects_explicit_aiopg_driver() -> None:
    with pytest.raises(ValueError, match="psycopg2"):
        _backend_url("postgresql+aiopg://user:pw@host/db")
```

**Step 2: Run — the asyncpg/aiopg rejection tests fail**

```bash
cd /Users/benjaminpoersch/Projects/Vision/ai-sdlc-scaffold-main/3-code/backlog-core
uv run --frozen pytest tests/test_migrations_runner.py -v
```

Expected: `test_backend_url_rejects_explicit_asyncpg_driver` and `test_backend_url_rejects_explicit_aiopg_driver` fail (the current passthrough accepts them). The other two pass (already-correct behaviours).

**Step 3: Implement the rejection**

Find `_backend_url` in `app/migrations.py`. Replace:

```python
def _backend_url(database_url: str) -> str:
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
```

With:

```python
# Drivers our yoyo backend actually supports (yoyo uses psycopg2 sync; an
# async-driver-explicit URL would dispatch to a backend that doesn't exist
# at install time).
_SUPPORTED_DRIVER_PREFIXES = ("postgresql+psycopg2://", "postgres+psycopg2://")


def _backend_url(database_url: str) -> str:
    """Convert an asyncpg-style URL to yoyo's expected format.

    The application uses ``postgresql://`` URLs read by asyncpg. yoyo's
    backend dispatch wants ``postgresql+psycopg2://`` to select the sync
    driver. We do the substitution here so callers (and the install runbook)
    don't need to know about the driver split.

    Already-prefixed URLs pass through unchanged when the driver is
    psycopg2; explicit non-psycopg2 driver prefixes (``+asyncpg``, ``+aiopg``)
    raise so the operator gets a clear message instead of a downstream
    "no driver named ..." error.
    """
    if database_url.startswith(_SUPPORTED_DRIVER_PREFIXES):
        return database_url
    if database_url.startswith(("postgresql+", "postgres+")):
        # An explicit driver suffix that isn't psycopg2 — reject early.
        scheme = database_url.split("://", 1)[0]
        raise ValueError(
            f"DATABASE_URL driver {scheme!r} is not supported by the migration "
            f"runner. yoyo-migrations uses psycopg2 — use 'postgresql://' "
            f"(no driver suffix; the runner adds psycopg2) or 'postgresql+psycopg2://'."
        )
    if database_url.startswith("postgresql://"):
        return "postgresql+psycopg2://" + database_url[len("postgresql://") :]
    if database_url.startswith("postgres://"):
        return "postgresql+psycopg2://" + database_url[len("postgres://") :]
    raise ValueError(
        f"DATABASE_URL must start with 'postgresql://' or 'postgres://'; "
        f"got prefix {database_url.split(':', 1)[0]!r}"
    )
```

**Step 4: Re-run the runner tests — all pass**

```bash
uv run --frozen pytest tests/test_migrations_runner.py -v
```

Expected: 7 passed (3 from Task 4 + 4 new).

**Step 5: Run the full backlog-core suite — confirm no regression**

```bash
uv run --frozen ruff check .
uv run --frozen mypy app
uv run --frozen pytest -q -m 'not postgres'
```

Expected: green; 22 passed (15 prior + 7 from test_migrations_runner.py), 19 deselected.

**Step 6: Commit**

```bash
cd /Users/benjaminpoersch/Projects/Vision/ai-sdlc-scaffold-main
git add 3-code/backlog-core/app/migrations.py 3-code/backlog-core/tests/test_migrations_runner.py
git commit -m "$(cat <<'EOF'
fix(backlog-core): _backend_url rejects unsupported driver prefixes

Closes M-5 from the in-session review. An operator setting
DATABASE_URL=postgresql+asyncpg://... would have it pass through
unchanged into yoyo's psycopg2 backend, producing a confusing
"no driver named asyncpg" error at apply time. Now reject explicit
non-psycopg2 driver prefixes at URL parse time with a message naming
the supported forms.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 6: DEC convention pin for `CREATE INDEX CONCURRENTLY` (M-4)

**Why:** This migration creates indexes on a freshly created (empty) table, so `CONCURRENTLY` is unnecessary. But the next migration that adds an index to a populated `events` table MUST use `CONCURRENTLY` to avoid locking writes during index build. Adding one line to the DEC's "Required patterns" makes this a checkable convention before the first time someone actually adds an index post-population.

**Files:**
- Modify: `decisions/DEC-postgres-migration-tool.md` — append one line to "Required patterns".

**Step 1: Locate the insertion point**

```bash
cd /Users/benjaminpoersch/Projects/Vision/ai-sdlc-scaffold-main
grep -n 'Required patterns' decisions/DEC-postgres-migration-tool.md
```

Expected: one match around line 70 in the Active record file.

**Step 2: Add the new bullet**

Find the existing "Required patterns" section in `decisions/DEC-postgres-migration-tool.md`. The last bullet currently reads:

```
- Testing: every migration is verified by at least one test in `tests/test_*_schema.py` that applies the migration to a real Postgres container, asserts the resulting schema (table existence, column types, indexes, constraints), and exercises behavior the migration enables (e.g., a CHECK constraint actually rejects an invalid value).
```

Insert this bullet immediately above it:

```
- Indexes added to **populated** tables MUST use `CREATE INDEX CONCURRENTLY` (and the migration runs outside yoyo's default transaction wrapper via the `__transactional__ = False` directive at the top of the SQL file, since `CONCURRENTLY` cannot run inside a transaction). Indexes on a freshly created table — like the parent `events` table in `0001_create-events-table.sql` — do not need `CONCURRENTLY` because the table has no rows yet. The trigger to use `CONCURRENTLY` is "table has rows", not "migration creates an index".
```

**Step 3: Verify the file still parses as Markdown and the existing structure is intact**

```bash
grep -c 'Required patterns' decisions/DEC-postgres-migration-tool.md  # still 1
grep -c 'CONCURRENTLY' decisions/DEC-postgres-migration-tool.md       # 2 (the new bullet uses it twice)
```

**Step 4: Append a changelog entry to the history file**

Find the changelog table at the bottom of `decisions/DEC-postgres-migration-tool.history.md`:

```
## Changelog

| Date | Change | Involvement |
|------|--------|-------------|
| 2026-05-02 | Initial decision — yoyo-migrations chosen as the schema migration tool for `backlog-core` | ai-proposed/human-approved |
```

Add the new row:

```
| 2026-05-02 | Added `CREATE INDEX CONCURRENTLY` convention pin to "Required patterns" (M-4 from in-session review of TASK-postgres-events-schema) | ai-proposed/human-approved |
```

**Step 5: Commit**

```bash
cd /Users/benjaminpoersch/Projects/Vision/ai-sdlc-scaffold-main
git add decisions/DEC-postgres-migration-tool.md decisions/DEC-postgres-migration-tool.history.md
git commit -m "$(cat <<'EOF'
docs(decisions): pin CREATE INDEX CONCURRENTLY convention in postgres-migration-tool

Closes M-4 from the in-session review of TASK-postgres-events-schema.
The first migration creates indexes on a fresh (empty) table where
CONCURRENTLY is unnecessary; future migrations adding indexes to a
populated events table must use CONCURRENTLY to avoid locking writes.
Encoded as a "Required patterns" bullet in DEC-postgres-migration-tool.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 7: Wire migrations into `install_vps.sh` and the install runbook (I-1)

**Why:** `DEC-postgres-migration-tool` § "Trigger conditions" says: *"Deploy phase: the install runbook runs `python -m app.migrations apply` after `docker compose up` and before the smoke test."* But neither `scripts/install_vps.sh` nor `4-deploy/runbooks/install.md` has been updated. A fresh-VPS install today would bring up Postgres without ever applying the migration; the smoke test would then fail because the events table doesn't exist; `vision health` would report `backlog-core` as `degraded`. Implement the obligation the DEC creates.

**Files:**
- Modify: `scripts/install_vps.sh` (add a new step between current Step 8 wait-for-healthy and current Step 9 ollama pull).
- Modify: `4-deploy/runbooks/install.md` (mention the migration step in the procedure).

**Step 1: Add a "Step 9: apply schema migrations" block to `install_vps.sh`**

Find the existing Step 9 (ollama pull) which currently reads:

```bash
# === Step 9: pull Ollama model ========================================
log "Pulling Ollama model (${OLLAMA_MODEL:-gemma3:4b})..."
bash "$REPO_ROOT/scripts/ollama-pull.sh"
ok "Ollama model ready"

# === Step 10: report next steps =======================================
```

Renumber: insert the new Step 9 (migrations) immediately above the Ollama pull, and renumber the subsequent steps to 10 and 11:

```bash
# === Step 9: apply backlog-core schema migrations =====================
# Per DEC-postgres-migration-tool: migrations are an explicit operator
# action, not a side effect of FastAPI startup. The backlog-core
# container's healthcheck reports `degraded` until the events table
# exists; smoke_test.sh would fail without this step.
log "Applying backlog-core schema migrations (yoyo)..."
docker compose exec -T backlog-core python -m app.migrations apply
ok "Migrations applied"

# === Step 10: pull Ollama model =======================================
log "Pulling Ollama model (${OLLAMA_MODEL:-gemma3:4b})..."
bash "$REPO_ROOT/scripts/ollama-pull.sh"
ok "Ollama model ready"

# === Step 11: report next steps =======================================
```

(Update the comment headers to reflect the new numbering. The body of each step is unchanged.)

**Step 2: Confirm `bash -n` and shellcheck both pass on the modified script**

```bash
cd /Users/benjaminpoersch/Projects/Vision/ai-sdlc-scaffold-main
bash -n scripts/install_vps.sh && echo "bash -n OK"
shellcheck scripts/install_vps.sh
```

Expected: `bash -n OK` and shellcheck silent (or only previously-known warnings; the new lines should not introduce new ones).

**Step 3: Update the install runbook**

Open `4-deploy/runbooks/install.md`. Find the section that describes `install_vps.sh`'s steps (around line 100 — the section with "compose up" / "smoke_test").

In the procedure section, locate this text:

```
6. `docker compose up -d`.
```

Add a new bullet immediately after it:

```
7. `docker compose exec -T backlog-core python -m app.migrations apply` — applies yoyo schema migrations per [`DEC-postgres-migration-tool`](../../decisions/DEC-postgres-migration-tool.md). Idempotent; re-running on an up-to-date DB is a no-op.
```

Renumber any subsequent numbered items in the same section so the list is sequential.

Also: in the Step-4 section ("Verify with `smoke_test.sh`") if it lists the script's expected output, leave it alone — the smoke test invocation is unchanged; it just runs *after* migrations have applied.

**Step 4: Confirm the runbook still reads coherently**

```bash
grep -nE '^[0-9]+\.' 4-deploy/runbooks/install.md | head -10
```

Expected: numbered items in the procedure section run sequentially without gaps.

**Step 5: Commit**

```bash
cd /Users/benjaminpoersch/Projects/Vision/ai-sdlc-scaffold-main
git add scripts/install_vps.sh 4-deploy/runbooks/install.md
git commit -m "$(cat <<'EOF'
feat(deploy): apply backlog-core migrations as install Step 9

Closes I-1 from the in-session review of TASK-postgres-events-schema.
DEC-postgres-migration-tool obligated the install runbook to run
'python -m app.migrations apply' after compose up and before the smoke
test, but the install_vps.sh script and 4-deploy/runbooks/install.md
hadn't been updated to actually do that. Added the migration step
between wait-for-healthy and ollama-pull (Step 9 of 11 now); the smoke
test invocation remains downstream and unchanged.

Verified: bash -n / shellcheck clean on the updated install_vps.sh.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 8: Verify migration + tests against a real Postgres (testcontainers run)

**Why:** The DEC's § "Required checks" #3 mandates: *"Confirm the migration applies cleanly via the test suite (testcontainers Postgres 16 must report no errors)."* The schema is the audit-chain trust boundary; shipping it without an integration-tested green-on-real-Postgres signal violates the convention we just authored.

**Prerequisite:** Docker daemon must be running. The local daemon is `colima` and it is currently stopped. Starting it consumes ~2GB RAM in a VM and is reversible (`colima stop` after).

**Files:** No code changes in this task. This is the verification gate.

**Step 1: Start colima**

```bash
colima start
```

Expected: ~30-60s warm-up, ending with output similar to:

```
INFO[...] starting colima
...
INFO[...] done
```

Verify with:

```bash
docker info | grep -i 'server version'
```

Expected: a "Server Version: ..." line (no error). If this fails, do not proceed — surface the failure to the user.

**Step 2: Run the postgres-marked schema tests**

```bash
cd /Users/benjaminpoersch/Projects/Vision/ai-sdlc-scaffold-main/3-code/backlog-core
uv run --frozen pytest -q -m 'postgres' 2>&1 | tail -30
```

Expected: `19 passed in <N>s` (assuming the 12-month partition test from Task 1 plus all the constraint / partition / default tests). The first run is slowest (~30-60s as testcontainers pulls the `postgres:16-alpine` image if not cached); subsequent runs are ~5-10s.

If any test fails, stop and report. Do not patch tests to make them pass — the failure indicates a real schema / runner issue that should be diagnosed first.

**Step 3: Run the full suite (postgres + non-postgres)**

```bash
cd /Users/benjaminpoersch/Projects/Vision/ai-sdlc-scaffold-main/3-code/backlog-core
uv run --frozen pytest -q 2>&1 | tail -10
```

Expected: 41 passed (15 health + 7 migrations-runner + 19 postgres schema), 0 failed, 0 skipped.

**Step 4: Run the 5-backend matrix smoke to confirm no other component regressed**

```bash
cd /Users/benjaminpoersch/Projects/Vision/ai-sdlc-scaffold-main
for c in whatsorga-ingest hermes-runtime backlog-core gbrain-bridge kanban-sync; do
  echo "=== $c ==="
  (cd 3-code/$c && uv run --frozen ruff check . | tail -1 && uv run --frozen mypy app | tail -1 && uv run --frozen pytest -q -m 'not postgres' | tail -1)
done
```

Expected: every component reports `All checks passed!`, `Success: no issues found in N source files`, `M passed`. The `-m 'not postgres'` filter is a no-op for components other than `backlog-core` (none of them have postgres-marked tests).

**Step 5: No commit in this task**

This task is verification only; no code changed. Move to Task 9.

If the verification succeeded, capture a one-line summary for the closeout note in Task 10:

> Verified locally on 2026-05-02: testcontainers Postgres 16 ran 19/19 postgres-marked schema tests green; full backlog-core suite 41/41; no regressions on other 4 backends.

---

## Task 9: Verify the plan-saving convention is sufficient (pre-existing observation)

**Why:** The review's "Pre-existing issues observed" section flagged that earlier tasks (canonical_json, bearer_auth) didn't save plan documents to `docs/plans/`, while this task (and the cast-quotes followup) did — calling it "convention drift". On reflection, the writing-plans skill **already** prescribes: *"Save plans to: `docs/plans/YYYY-MM-DD-<feature-name>.md`"* — so the convention is documented at the skill level. The "drift" was overstated: it's not a project-rule violation, it's that previous tasks were executed without invoking the writing-plans skill at all (they went straight from SDLC-execute-next-task to implementation).

This task confirms the assessment and either (a) leaves the convention as-is or (b) adds a one-line scaffold-level reminder.

**Files:** None to modify, *if* the assessment holds. Possibly modify `3-code/CLAUDE.code.md` if the reviewer concludes a scaffold-level reminder is warranted.

**Step 1: Verify the writing-plans skill's save-location directive**

```bash
grep -n 'Save plans to' /Users/benjaminpoersch/.claude/skills/writing-plans/SKILL.md 2>/dev/null \
  || grep -rn 'Save plans to' /Users/benjaminpoersch/.claude/ 2>/dev/null | head -3
```

Expected: at least one match of "Save plans to: `docs/plans/...`" in the writing-plans skill file. This confirms the convention is documented at the skill level — every `/writing-plans` invocation will be told to save the plan.

**Step 2: Verify previous tasks didn't bypass it**

```bash
cd /Users/benjaminpoersch/Projects/Vision/ai-sdlc-scaffold-main
ls docs/plans/
```

Expected: at least one plan file (the cast-quotes-followup from earlier today; this plan once saved). The absence of plans for canonical_json / bearer_auth is consistent with those tasks not having gone through `/writing-plans` — they were dispatched directly via SDLC-execute-next-task without an explicit plan document. That's a workflow choice, not a convention violation.

**Step 3: Decide — no scaffold amendment needed**

Conclusion: the convention is documented in the writing-plans skill itself. Adding a redundant reminder to `3-code/CLAUDE.code.md` would duplicate skill content into project state, which is exactly what the scaffold's `## Memory Policy` (in the root `CLAUDE.md`) tells us not to do: *"All project knowledge — domain context, team structure, constraints, decisions, and any other relevant information — must be captured exclusively through the SDLC artifact system."* Workflow conventions belong in the skill files; project state belongs in artifacts.

**Therefore this task is a documented no-op.** The "fix" is the documentation that no fix is needed — captured in this plan's prose so a future reviewer raising the same observation finds the resolution.

**Step 4: No commit in this task** — there's nothing to commit. The reasoning is recorded here.

If during Step 3 you (or the reviewing user) decide that a scaffold-level reminder *is* warranted after all, add this single bullet to `3-code/CLAUDE.code.md` under the existing `## Linking to Other Phases` section, then commit:

```
- Plans created via `/writing-plans` save to `docs/plans/YYYY-MM-DD-<feature-name>.md` per the writing-plans skill. Tasks executed without a plan (small fixes, follow-ups) don't require one — but if you do invoke `/writing-plans`, follow its save convention.
```

The default outcome of this task is the no-op (Step 3); the override path (Step 4 amendment) is here for completeness if the human decides differently.

---

## Task 10: Closeout — `tasks.md`, `CLAUDE.md` Current State, final commit, push

**Why:** The work is done; the trackers and the project narrative need to catch up. This is the same closeout shape the previous Phase-2 tasks used.

**Files:**
- Modify: `3-code/tasks.md` — flip `TASK-postgres-events-schema` row from `In Progress` to `Done` with a closeout Notes cell; narrow the `TASK-postgres-events-partitioning` row's Notes cell to reflect that this task already introduced the partitioning structure.
- Modify: `CLAUDE.md` — update Current State paragraph: 19/107 → 20/107, Phase 2 progress 2/16 → 3/16, decision count 15 → 16, mention the new DEC and the M-tier review fixes.

**Step 1: Update `tasks.md` — flip status to Done with closeout notes**

Find the `TASK-postgres-events-schema` row in `3-code/tasks.md`:

```
| TASK-postgres-events-schema | `events` table + indexes per `data-model.md` | P1 | In Progress | [REQ-SEC-audit-log](../1-spec/requirements/REQ-SEC-audit-log.md) | TASK-backlog-core-skeleton | 2026-05-02 | Per `DEC-postgres-as-event-store` |
```

Replace the Status from `In Progress` to `Done`, refresh the Updated date, and replace the Notes cell with a closeout summary. The full new row:

```
| TASK-postgres-events-schema | `events` table + indexes per `data-model.md` | P1 | Done | [REQ-SEC-audit-log](../1-spec/requirements/REQ-SEC-audit-log.md) | TASK-backlog-core-skeleton | 2026-05-02 | Per `DEC-postgres-as-event-store` and the new [`DEC-postgres-migration-tool`](../decisions/DEC-postgres-migration-tool.md) (16th active decision; chosen as the schema migration tool for backlog-core; raw-SQL forward-only). New `3-code/backlog-core/migrations/0001_create-events-table.sql` (~180 lines): partitioned events table per `data-model.md` § Partitioning + 12 months of pre-created partitions (May 2026 → April 2027 inclusive, narrowing `TASK-postgres-events-partitioning`'s scope to maintenance-rate cron); 5 indexes per `data-model.md` § Indexes (including the partial retention-sweep index); CHECK constraints closing the 28-event-type catalog and the 3-class retention vocabulary; redaction-consistency CHECK enforcing the redacted/redaction_run_id/redacted_at invariant per `DEC-hash-chain-over-payload-hash`. Composite PK `(event_id, created_at)` because partition-key participation is required by Postgres declarative partitioning — minor design clarification noted in the migration's inline comment. `app/migrations.py` runner wraps yoyo's programmatic API (`apply` and `status` subcommands; `cmd_status` exits 1 on unexpected rollback findings; `_backend_url` rejects non-psycopg2 driver prefixes). 19/19 postgres-marked schema tests green via testcontainers Postgres 16 + 7/7 unit tests for the runner glue + 15 prior backlog-core tests still green = 41/41 total; ruff clean; mypy strict clean. `install_vps.sh` Step 9 now applies migrations after compose-up healthy-check; `4-deploy/runbooks/install.md` updated to mirror. Code-review fixes covered: I-2 (12 months of partitions, not 2), I-1 (install pipeline integration), M-1 (unique actor IDs per test), M-2 (psycopg2.extras.Json wrapper), M-3 (cmd_status exits 1 on rollback), M-4 (DEC convention pin for `CREATE INDEX CONCURRENTLY` on populated tables), M-5 (`_backend_url` rejects unsupported drivers). Pre-existing observation re: plan-saving convention drift confirmed already documented at the writing-plans skill level — no scaffold amendment needed (recorded in `docs/plans/2026-05-02-task-postgres-events-schema-review-fixes.md` Task 9). Plan: [`docs/plans/2026-05-02-task-postgres-events-schema-review-fixes.md`](../docs/plans/2026-05-02-task-postgres-events-schema-review-fixes.md). |
```

(Use the Edit tool with the unique substring "Per `DEC-postgres-as-event-store`" in the existing row to make the replacement targeted; that string only appears in this row's Notes cell.)

**Step 2: Update `tasks.md` — narrow `TASK-postgres-events-partitioning` (Phase 2 #5)**

Find the row:

```
| TASK-postgres-events-partitioning | Monthly partitioning + partition-creation cron | P1 | Todo | [REQ-F-retention-sweep](../1-spec/requirements/REQ-F-retention-sweep.md) | TASK-postgres-events-schema | 2026-04-28 |  |
```

Replace the empty Notes cell with a scope-clarification note (since the partitioning structure already shipped in #3):

```
| TASK-postgres-events-partitioning | Monthly partitioning + partition-creation cron | P1 | Todo | [REQ-F-retention-sweep](../1-spec/requirements/REQ-F-retention-sweep.md) | TASK-postgres-events-schema | 2026-05-02 | Scope narrowed by `TASK-postgres-events-schema` (#3): the partitioned-table structure plus 12 months of pre-created partitions already shipped in `0001_create-events-table.sql`. This task now ships only the **rolling-future cron** that creates month N+12 each month, plus any retention-aware sweep helpers that depend on the partition layout. The 12-month buffer means the cron does not need to ship before 2027-04 to avoid any insert failure. |
```

**Step 3: Update `CLAUDE.md` Current State**

Find the existing "Implementation progress (2026-05-02)" paragraph in `CLAUDE.md`. The current text starts with:

```
**Implementation progress (2026-05-02):** 19 / 107 tasks Done. **Phase 1: Bootstrap & Deployment Foundation is complete (17/17). Phase 2: Consent Foundation + Audit Backbone is in progress (2/16).** Just completed: `TASK-bearer-auth-middleware` (Phase 2 #2) ...
```

Replace the leading sentences (just the "Just completed" sentence — leave the rest of the paragraph intact for now) with:

```
**Implementation progress (2026-05-02):** 20 / 107 tasks Done. **Phase 1: Bootstrap & Deployment Foundation is complete (17/17). Phase 2: Consent Foundation + Audit Backbone is in progress (3/16).** Just completed: `TASK-postgres-events-schema` (Phase 2 #3) — the events table is now real. New [`DEC-postgres-migration-tool`](decisions/DEC-postgres-migration-tool.md) (16th active decision; yoyo-migrations chosen for raw-SQL forward-only schema evolution); `3-code/backlog-core/migrations/0001_create-events-table.sql` ships the partitioned events table per `data-model.md` (12 months of pre-created partitions May 2026 → April 2027; 5 indexes; CHECK constraints closing the 28-event-type catalog and 3-class retention vocabulary; redaction-consistency CHECK per `DEC-hash-chain-over-payload-hash`). Verified via testcontainers Postgres 16 — 19/19 postgres-marked schema tests + 7/7 runner unit tests + 15 prior backlog-core tests = 41/41 green. `install_vps.sh` Step 9 now applies migrations after compose-up. Code-review fixes I-1, I-2, M-1, M-2, M-3, M-4, M-5 all addressed in the same commit chain. Earlier in Phase 2: `TASK-bearer-auth-middleware` (Phase 2 #2) ...
```

(The remainder of the paragraph from "Earlier in Phase 2" onwards stays unchanged — it already documents bearer_auth and canonical_json.)

Also update the "Next Phase 2 task" line at the very end of the paragraph from:

```
Next Phase 2 task: `TASK-postgres-events-schema` (P1; depends on `TASK-backlog-core-skeleton` ✓; defines the `events` table per `data-model.md` and unblocks the entire audit-backbone chain).
```

to:

```
Next Phase 2 task: `TASK-postgres-consent-schema` (P1; depends on `TASK-backlog-core-skeleton` ✓; ships the `consent_sources` and `consent_history` tables per `data-model.md` § Consent and `REQ-COMP-consent-record`).
```

**Step 4: Confirm both files still parse**

```bash
cd /Users/benjaminpoersch/Projects/Vision/ai-sdlc-scaffold-main
awk -F'|' '/^\| TASK-postgres-events-schema/ {print NF}' 3-code/tasks.md       # should be 10 or 11
awk -F'|' '/^\| TASK-postgres-events-partitioning/ {print NF}' 3-code/tasks.md  # should be 10 or 11
grep -c 'TASK-postgres-events-schema' CLAUDE.md                                # should be 1 or more (mention in Current State)
grep -c 'docs/plans/2026-05-02-task-postgres-events-schema-review-fixes' 3-code/tasks.md  # should be 1 (the plan link in the closeout note)
```

If any column count differs from neighboring rows by more than ±1 (the cells with backticked code snippets routinely shift by 1 because of unescaped pipes inside backticks; that's the documented pre-existing condition), inspect the relevant row.

**Step 5: Commit the closeout**

```bash
cd /Users/benjaminpoersch/Projects/Vision/ai-sdlc-scaffold-main
git add 3-code/tasks.md CLAUDE.md
git commit -m "$(cat <<'EOF'
docs(tasks): mark TASK-postgres-events-schema Done; narrow #5 scope

Phase 2 progress 2/16 → 3/16. tasks.md row flipped to Done with full
closeout note covering all review fixes (I-1, I-2, M-1..M-5) and the
plan reference. TASK-postgres-events-partitioning (#5) Notes cell
updated to reflect that the partitioning structure already shipped
in #3 — this task now ships only the rolling-future cron + retention
helpers. CLAUDE.md Current State narrative updated: progress count,
new DEC reference, next-task pointer to TASK-postgres-consent-schema.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

**Step 6: Now create the plan-and-DEC commit (everything except the closeout)**

Wait — re-read your git status. The earlier tasks made several commits already (Tasks 1-7). The closeout in this task is its own commit (just made). What about the original "Phase 2 #3 baseline commit" that includes the DEC, the migration, the runner, and the tests as they existed *before* the review fixes?

There are two valid commit-shape choices:

- **Choice A — single Phase-2-#3 commit at the end** (chosen): the work-in-progress files (DEC, migration, runner, tests, pyproject.toml, CLAUDE.component.md, 4-deploy/CLAUDE.deploy.md additions, lockfile) all sit uncommitted in the working tree at the start of this plan. Tasks 1-7 layer fixes *on top of* those uncommitted changes by editing the same files. The natural commit shape is to run `git add` on **all** the still-uncommitted files at the very end and ship them as one Phase-2-#3 commit, with the review-fix commits from Tasks 1-7 already landed on top.

  But that's order-inverted — review-fix commits would land *before* the baseline. That's confusing in `git log`.

- **Choice B — single combined commit** (recommended): instead of Tasks 1-7 producing separate commits and Task 10 doing one closeout, treat Tasks 1-7 as **edits to the still-uncommitted working tree** (no individual commits) and Task 10 produces ONE big "feat(backlog-core): events table schema + migration runner + DEC + install integration (TASK-postgres-events-schema)" commit that captures the entire reviewed-and-fixed implementation, plus a SEPARATE small "docs(tasks): mark Done + narrow #5 + update Current State" commit.

**Recommended actual shape:** Choice B. **Override the per-task commits in Tasks 1-7** — instead of `git commit` at the end of each, treat each task as an in-place edit to the uncommitted working tree. Run the toolchain at each task's verification step, but don't commit. Then in this Task 10:

1. First commit: the entire Phase-2-#3 implementation (Tasks 1-7's combined output + the original work-in-progress files) — title: `feat(backlog-core): events table schema + migration runner (TASK-postgres-events-schema)`.
2. Second commit (this Task 10's existing Step 5): the `tasks.md` + `CLAUDE.md` closeout.

**If the executor already committed per-task** — the per-task commit messages document the review-fix decisions cleanly, so leaving them is fine. The combined Phase-2-#3 view would then be the range `bece603..HEAD`, viewable via `git log --oneline bece603..HEAD`.

**Step 7: Push everything**

```bash
git push 2>&1 | tail -5
```

Expected: `bece603..<HEAD>  main -> main` (or rebase + push if the remote moved during the work).

If push is rejected (remote ahead), `git pull --rebase` and re-push.

---

## What's NOT in this plan (intentional out-of-scope)

These were considered and explicitly excluded:

- **CI tweak to ensure testcontainers tests run on the runner.** The GH ubuntu-latest runner has Docker daemon running by default; the existing `backlog-core-test` CI job already runs `pytest -q` which includes postgres-marked tests; the `_docker_daemon_reachable` check in `tests/test_events_schema.py` will pass on the runner. **No CI change needed.** First push reveals whether anything fails; iterate then.
- **A `vision migrate` operator-CLI subcommand.** Useful long-term but cleanly belongs to a Phase-2 / Phase-3 cli-component task, not this schema task. The install runbook calls `python -m app.migrations apply` directly today; that contract is stable enough that a future cli wrapper is purely additive.
- **The minor design clarification re: composite PK `(event_id, created_at)`.** The migration's inline comment documents it; updating `2-design/data-model.md` to add the same clarification is housekeeping that doesn't change behavior. If a future reviewer asks, point at the migration comment; the design doc can be brought into sync in the next routine `/SDLC-design` pass.
- **A separate `DEC-postgres-schema-test-strategy` decision** locking testcontainers-python as the test approach. The current `DEC-postgres-migration-tool` § "Required patterns" already mandates "testcontainers Postgres 16" implicitly via the schema-test rule — sufficient for now. Promote to a standalone DEC if the pattern proliferates beyond migration tests.

---

## Definition of done (full plan)

1. All 7 review issues resolved (I-1, I-2, M-1, M-2, M-3, M-4, M-5).
2. Pre-existing "convention drift" observation resolved (no-op, recorded in Task 9).
3. Verification gap closed: testcontainers Postgres 16 ran 19/19 postgres-marked schema tests green; full backlog-core suite 41/41 green.
4. `tasks.md` row for #3 flipped to Done; #5 row Notes narrowed.
5. `CLAUDE.md` Current State updated: 20/107 tasks, 16 active decisions, next-task pointer to `TASK-postgres-consent-schema`.
6. Commits land and push to `origin/main`.

If any verification fails at the end (e.g., a postgres test goes red on `colima` but green in CI), surface the discrepancy to the user before merging.
