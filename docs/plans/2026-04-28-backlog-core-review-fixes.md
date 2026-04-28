# backlog-core Review Findings Cleanup Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Address every MEDIUM and LOW finding from the 2026-04-28 code review of `TASK-backlog-core-skeleton` (commit `23219e8`) in a single efficient sweep, with TDD discipline where behavior changes and pure refactor where types/names tighten.

**Architecture:** Five small, focused tasks ordered to land lowest-risk refactors first, then the one behavior change (`/v1/health` → 503 on degraded), then `.env`-tunable pool size, then test-fixture symmetry, then a final review and bundled commit set. Each task is verified locally with the existing toolchain (`uv run --frozen pytest / ruff check / mypy`) before moving on.

**Tech Stack:** Python 3.12 + FastAPI + Pydantic + asyncpg + pytest + httpx + ruff + mypy strict, all per `DEC-backend-stack-python-fastapi`.

**Scope (findings to close):**
- MEDIUM 1: `/v1/health` returns 200 with `status: "degraded"` — Compose marks healthy when DB is down.
- MEDIUM 2: `_PoolLike` Protocol's `acquire() -> object` requires `# type: ignore[attr-defined]`.
- LOW 3: Pool `min_size=1, max_size=10` hardcoded.
- LOW 4: `get_pool(app)` ↔ `_pool_dependency(request)` adapter is redundant.
- LOW 5: `client_with_down_pool` fixture lives in `test_health.py` instead of `conftest.py`.
- LOW 6: `client_with_pool(...) -> Iterator[Any]` should be `Iterator[TestClient]`.

**Out of scope:** semantically-similar future-proofing for `whatsorga-ingest` and `hermes-runtime` health endpoints (their `/v1/health` always returns ok at skeleton level — the 503-on-degraded pattern only matters once they wire real downstream checks). Cross-component health-readiness conventions can be revisited when `gbrain-bridge` and `kanban-sync` skeletons land.

---

### Task 1: Tighten `_PoolLike` Protocol and simplify `get_pool` signature (MEDIUM 2 + LOW 4)

**Files:**
- Modify: `3-code/backlog-core/app/db.py`
- Modify: `3-code/backlog-core/app/main.py`

**Rationale:** Both findings are `app/db.py` type/signature improvements. Bundling them keeps a single touch on the file. Pure refactor — existing tests must still pass.

**Step 1: Update `_PoolLike` Protocol to use `AbstractAsyncContextManager`**

In `3-code/backlog-core/app/db.py`, change:

```python
class _PoolLike(Protocol):
    """Subset of `asyncpg.Pool` we depend on. Lets tests substitute fakes."""

    def acquire(self) -> object: ...

    async def close(self) -> None: ...
```

to:

```python
class _PoolLike(Protocol):
    """Subset of `asyncpg.Pool` we depend on. Lets tests substitute fakes."""

    def acquire(self) -> AbstractAsyncContextManager[Any]: ...

    async def close(self) -> None: ...
```

Add `AbstractAsyncContextManager` to imports:

```python
from contextlib import AbstractAsyncContextManager, asynccontextmanager
```

**Step 2: Drop the `# type: ignore[attr-defined]` in `ping()`**

```python
async def ping(pool: _PoolLike) -> bool:
    """Return True if the pool can complete a `SELECT 1`. Never raises."""
    try:
        async with pool.acquire() as conn:
            value: Any = await conn.fetchval("SELECT 1")
            return bool(value == 1)
    except Exception:
        return False
```

**Step 3: Change `get_pool` to take `Request` directly**

Replace:

```python
async def get_pool(app: FastAPI) -> _PoolLike:
    """FastAPI dependency: returns the pool created by `lifespan`.
    ...
    """
    pool: Any = getattr(app.state, "pool", None)
    if pool is None:
        raise RuntimeError(...)
    return cast(_PoolLike, pool)
```

with:

```python
async def get_pool(request: Request) -> _PoolLike:
    """FastAPI dependency: returns the pool created by `lifespan`.

    Raises if the lifespan didn't run (e.g., default TestClient usage). Tests
    that don't go through lifespan must override this dependency.
    """
    pool: Any = getattr(request.app.state, "pool", None)
    if pool is None:
        raise RuntimeError(
            "connection pool not initialized — lifespan must run, "
            "or get_pool must be overridden in tests"
        )
    return cast(_PoolLike, pool)
```

Update imports in `db.py`:
- Remove `if TYPE_CHECKING: from fastapi import FastAPI`
- Add `from fastapi import Request` (runtime, since it's a dependency parameter type)

**Step 4: Update `app/main.py` to call `get_pool` directly**

Remove the `_pool_dependency` adapter:

```python
# Before:
async def _pool_dependency(request: Request) -> _PoolLike:
    return await get_pool(request.app)

PoolDep = Annotated[_PoolLike, Depends(_pool_dependency)]

# After:
PoolDep = Annotated[_PoolLike, Depends(get_pool)]
```

Update the import from `app.db`: drop `_pool_dependency`-related comment.

**Step 5: Update test fixtures referencing `_pool_dependency`**

In `3-code/backlog-core/tests/conftest.py` and `3-code/backlog-core/tests/test_health.py`, replace every `_pool_dependency` reference with `get_pool`. Specifically:

- `conftest.py`: change `from app.main import _pool_dependency, app` → `from app.db import get_pool` + `from app.main import app`. Replace `app.dependency_overrides[_pool_dependency] = ...` → `app.dependency_overrides[get_pool] = ...`.
- `test_health.py`: same substitutions.

**Step 6: Run the test suite to verify no regressions**

```bash
cd 3-code/backlog-core
uv run --frozen pytest -q
```

Expected: 11 passed.

**Step 7: Lint + type-check**

```bash
uv run --frozen ruff check .
uv run --frozen mypy app
```

Expected: both clean. Critically, the `# type: ignore[attr-defined]` is now gone but `mypy app` still passes — confirming the tightened Protocol type-checks correctly.

**Step 8: Commit**

```bash
git add 3-code/backlog-core/app/db.py 3-code/backlog-core/app/main.py 3-code/backlog-core/tests/conftest.py 3-code/backlog-core/tests/test_health.py
git commit -m "refactor(backlog-core): tighten _PoolLike Protocol and simplify get_pool signature

Closes MED-2 and LOW-4 from the 2026-04-28 code review of
TASK-backlog-core-skeleton:

- _PoolLike.acquire now returns AbstractAsyncContextManager[Any], so
  app/db.py:ping no longer needs # type: ignore[attr-defined].
- get_pool now takes Request directly, dropping the _pool_dependency
  adapter in app/main.py and the corresponding indirection in tests.

Pure refactor — same 11/11 tests pass; ruff + mypy strict clean."
```

---

### Task 2: `/v1/health` returns 503 on degraded (MEDIUM 1)

**Files:**
- Modify: `3-code/backlog-core/app/main.py`
- Modify: `3-code/backlog-core/tests/test_health.py`

**Rationale:** This is the only behavior change in the cleanup. TDD: failing test first, then the one-line fix, then verify the existing `status: "degraded"` shape still matches `api-design.md`.

**Step 1: Write the failing test**

Add to `3-code/backlog-core/tests/test_health.py` (after `test_health_reports_degraded_when_postgres_is_down`):

```python
def test_health_returns_503_when_postgres_is_down(
    client_with_down_pool: TestClient,
) -> None:
    """Compose's HTTP-status-only healthcheck must mark the container
    unhealthy when Postgres is unreachable. The body still carries the
    full {status, version, checks} shape per api-design.md."""
    response = client_with_down_pool.get("/v1/health")
    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "degraded"
    assert body["checks"]["postgres"] == "down"
```

**Step 2: Run the test to verify it fails**

```bash
cd 3-code/backlog-core
uv run --frozen pytest tests/test_health.py::test_health_returns_503_when_postgres_is_down -v
```

Expected: FAIL with `assert 200 == 503`.

**Step 3: Implement the fix**

In `3-code/backlog-core/app/main.py`, change the `/v1/health` handler to return a `Response` with explicit status when degraded:

```python
from fastapi import Depends, FastAPI, Response, status as http_status
from fastapi.responses import JSONResponse
```

Replace:

```python
@app.get("/v1/health", response_model=HealthResponse, tags=["health"])
async def health(pool: PoolDep) -> HealthResponse:
    postgres_ok = await ping(pool)
    return HealthResponse(
        status="ok" if postgres_ok else "degraded",
        version=__version__,
        checks={"postgres": "ok" if postgres_ok else "down"},
    )
```

with:

```python
@app.get(
    "/v1/health",
    response_model=HealthResponse,
    tags=["health"],
    responses={
        200: {"description": "All checked dependencies healthy."},
        503: {"description": "One or more dependencies are degraded or down."},
    },
)
async def health(pool: PoolDep, response: Response) -> HealthResponse:
    postgres_ok = await ping(pool)
    if not postgres_ok:
        response.status_code = http_status.HTTP_503_SERVICE_UNAVAILABLE
    return HealthResponse(
        status="ok" if postgres_ok else "degraded",
        version=__version__,
        checks={"postgres": "ok" if postgres_ok else "down"},
    )
```

The `Response` parameter is FastAPI's idiomatic way to mutate the outgoing status while still serializing the Pydantic body via the existing `response_model`.

**Step 4: Run the new test to verify it passes**

```bash
uv run --frozen pytest tests/test_health.py::test_health_returns_503_when_postgres_is_down -v
```

Expected: PASS.

**Step 5: Run the full suite to verify no regressions**

```bash
uv run --frozen pytest -q
```

Expected: 12 passed (11 prior + 1 new).

**Existing test sanity check:** `test_health_returns_200_when_postgres_is_ok` and `test_health_payload_shape_matches_api_design` use `client_with_pool` (the ok fixture), which still returns 200. `test_health_reports_degraded_when_postgres_is_down` only asserts `body["status"] == "degraded"` — it doesn't assert 200, so it stays green. No existing test regresses.

**Step 6: Lint + type-check**

```bash
uv run --frozen ruff check .
uv run --frozen mypy app
```

Expected: both clean.

**Step 7: Commit**

```bash
git add 3-code/backlog-core/app/main.py 3-code/backlog-core/tests/test_health.py
git commit -m "fix(backlog-core): return 503 from /v1/health when Postgres is degraded

Closes MED-1 from the 2026-04-28 code review of TASK-backlog-core-
skeleton: previously the endpoint always returned 200, even with
status: degraded in the body, which made the Compose healthcheck
(HTTP-status-only) report the container healthy when its database
was unreachable.

Now returns 503 when ping(pool) reports false. Body shape unchanged
(matches 2-design/api-design.md § Health and observability:
{status, version, checks}). Compose will correctly mark the
container unhealthy under DB outage; LB / orchestrator behavior
follows from there."
```

---

### Task 3: Env-tunable connection-pool size (LOW 3)

**Files:**
- Modify: `3-code/backlog-core/app/db.py`
- Modify: `3-code/backlog-core/tests/test_db.py`
- Modify: `docker-compose.yml` (inject the env vars into `backlog-core`)
- Modify: `.env.example` (declare the keys)

**Rationale:** Hardcoded `min_size=1, max_size=10` should follow the env-driven config principle (`REQ-MNT-env-driven-config`). Defaults stay the same; operators can tune for production load tests later.

**Step 1: Write a failing test for the env-var-reading helper**

Add to `3-code/backlog-core/tests/test_db.py` (after `test_database_url_raises_when_unset`):

```python
def test_pool_size_returns_defaults_when_env_unset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("BACKLOG_CORE_DB_POOL_MIN", raising=False)
    monkeypatch.delenv("BACKLOG_CORE_DB_POOL_MAX", raising=False)

    from app.db import _pool_size

    assert _pool_size() == (1, 10)


def test_pool_size_reads_env_overrides(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BACKLOG_CORE_DB_POOL_MIN", "4")
    monkeypatch.setenv("BACKLOG_CORE_DB_POOL_MAX", "32")

    from app.db import _pool_size

    assert _pool_size() == (4, 32)


def test_pool_size_rejects_min_greater_than_max(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("BACKLOG_CORE_DB_POOL_MIN", "20")
    monkeypatch.setenv("BACKLOG_CORE_DB_POOL_MAX", "10")

    from app.db import _pool_size

    with pytest.raises(RuntimeError, match="POOL_MIN .* exceeds .* POOL_MAX"):
        _pool_size()
```

**Step 2: Run tests to verify they fail**

```bash
cd 3-code/backlog-core
uv run --frozen pytest tests/test_db.py::test_pool_size_returns_defaults_when_env_unset tests/test_db.py::test_pool_size_reads_env_overrides tests/test_db.py::test_pool_size_rejects_min_greater_than_max -v
```

Expected: 3 FAIL with `ImportError: cannot import name '_pool_size'`.

**Step 3: Implement `_pool_size()` and wire it into `lifespan`**

In `3-code/backlog-core/app/db.py`, add:

```python
DEFAULT_POOL_MIN = 1
DEFAULT_POOL_MAX = 10


def _pool_size() -> tuple[int, int]:
    """Read pool sizing from env with safe defaults; validate min <= max."""
    min_size = int(os.environ.get("BACKLOG_CORE_DB_POOL_MIN", DEFAULT_POOL_MIN))
    max_size = int(os.environ.get("BACKLOG_CORE_DB_POOL_MAX", DEFAULT_POOL_MAX))
    if min_size > max_size:
        raise RuntimeError(
            f"BACKLOG_CORE_DB_POOL_MIN ({min_size}) exceeds "
            f"BACKLOG_CORE_DB_POOL_MAX ({max_size}) — refusing to start."
        )
    return min_size, max_size
```

Modify `lifespan` to use it:

```python
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Create the connection pool on startup; close it on shutdown."""
    min_size, max_size = _pool_size()
    pool = await asyncpg.create_pool(
        dsn=_database_url(), min_size=min_size, max_size=max_size
    )
    app.state.pool = pool
    try:
        yield
    finally:
        await pool.close()
```

**Step 4: Run new tests to verify they pass**

```bash
uv run --frozen pytest tests/test_db.py -v
```

Expected: 8 passed (5 prior + 3 new).

**Step 5: Update `docker-compose.yml`'s `backlog-core` service**

Add to the `environment:` block (right after `DATABASE_URL`):

```yaml
      # Connection-pool sizing — overridable for production load tuning.
      BACKLOG_CORE_DB_POOL_MIN: ${BACKLOG_CORE_DB_POOL_MIN:-1}
      BACKLOG_CORE_DB_POOL_MAX: ${BACKLOG_CORE_DB_POOL_MAX:-10}
```

**Step 6: Update `.env.example`**

After the existing service-token section, add:

```bash
# =====================================================================
# backlog-core connection pool (DEC-postgres-as-event-store)
# =====================================================================

# Minimum / maximum pool size for backlog-core's asyncpg connection pool.
# Defaults are sane for a single-VPS MVP (Postgres has 100 max_connections by
# default). Bump for higher concurrency once load tests in Phase 7 run.
BACKLOG_CORE_DB_POOL_MIN=1
BACKLOG_CORE_DB_POOL_MAX=10
```

**Step 7: Verify drift check still passes**

```bash
cd /Users/benjaminpoersch/Projects/Vision/ai-sdlc-scaffold-main
bash scripts/check-env-drift.sh
```

Expected: `OK: ... 18 keys checked.` (was 16; +2 new).

**Step 8: Lint + type-check + full pytest**

```bash
cd 3-code/backlog-core
uv run --frozen ruff check .
uv run --frozen mypy app
uv run --frozen pytest -q
```

Expected: ruff clean, mypy strict clean, 15 passed (12 prior + 3 new).

**Step 9: Commit**

```bash
cd /Users/benjaminpoersch/Projects/Vision/ai-sdlc-scaffold-main
git add 3-code/backlog-core/app/db.py 3-code/backlog-core/tests/test_db.py docker-compose.yml .env.example
git commit -m "feat(backlog-core): make connection-pool size .env-tunable

Closes LOW-3 from the 2026-04-28 code review. Pool size was previously
hardcoded to (1, 10). Defaults unchanged; operators can now tune via
BACKLOG_CORE_DB_POOL_MIN / BACKLOG_CORE_DB_POOL_MAX in .env without a
code change, per REQ-MNT-env-driven-config.

Validates min <= max at startup with a RuntimeError if violated.
Drift check now at 18 keys."
```

---

### Task 4: Test-fixture cleanup (LOW 5 + LOW 6)

**Files:**
- Modify: `3-code/backlog-core/tests/conftest.py`
- Modify: `3-code/backlog-core/tests/test_health.py`

**Rationale:** Pure org tightening — symmetry between `client_with_pool` (ok fixture, in conftest) and `client_with_down_pool` (down fixture, currently in test_health.py); plus narrow `Iterator[Any]` to `Iterator[TestClient]`.

**Step 1: Move `client_with_down_pool` to `conftest.py`**

In `3-code/backlog-core/tests/conftest.py`, add (mirroring `client_with_pool`):

```python
@pytest.fixture
def client_with_down_pool(fake_pool_down: FakePool) -> Iterator[TestClient]:
    """A FastAPI TestClient whose get_pool dependency returns a failing fake pool."""
    from fastapi.testclient import TestClient

    from app.db import get_pool
    from app.main import app

    async def _override() -> FakePool:
        return fake_pool_down

    app.dependency_overrides[get_pool] = _override
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.pop(get_pool, None)
```

**Step 2: Tighten `client_with_pool`'s return annotation**

In the same file, change:

```python
@pytest.fixture
def client_with_pool(fake_pool_ok: FakePool) -> Iterator[Any]:
```

to:

```python
@pytest.fixture
def client_with_pool(fake_pool_ok: FakePool) -> Iterator[TestClient]:
```

Add to the TYPE_CHECKING block at the top:

```python
if TYPE_CHECKING:
    from collections.abc import Iterator

    from fastapi.testclient import TestClient
```

(`TestClient` is only used as a return annotation; runtime imports stay inside the fixture body.)

**Step 3: Remove the duplicated fixture from `test_health.py`**

In `3-code/backlog-core/tests/test_health.py`, remove the `client_with_down_pool` fixture definition entirely (lines roughly 19-31). The fixture name will be auto-discovered from `conftest.py` by pytest.

The two `from app.db import get_pool` / `from app.main import _pool_dependency, app` blocks at the top become unused — clean them up. The TYPE_CHECKING block also no longer needs `Iterator` since the fixture moved.

**Step 4: Run the full suite to verify nothing broke**

```bash
cd 3-code/backlog-core
uv run --frozen pytest -q
```

Expected: 15 passed.

**Step 5: Lint + type-check**

```bash
uv run --frozen ruff check .
uv run --frozen mypy app
```

Expected: both clean.

**Step 6: Commit**

```bash
git add 3-code/backlog-core/tests/conftest.py 3-code/backlog-core/tests/test_health.py
git commit -m "refactor(backlog-core): consolidate test fixtures in conftest.py

Closes LOW-5 and LOW-6 from the 2026-04-28 code review:

- client_with_down_pool moved from test_health.py to conftest.py for
  symmetry with client_with_pool. Future test files can now use it
  without re-defining.
- client_with_pool's return annotation tightened from Iterator[Any]
  to Iterator[TestClient].

Pure refactor — 15/15 tests still pass."
```

---

### Task 5: Final code review pass + push

**Files:**
- (No code changes; verification only.)

**Step 1: Run the full local verification chain**

```bash
cd /Users/benjaminpoersch/Projects/Vision/ai-sdlc-scaffold-main
bash scripts/check-env-drift.sh
uv run --quiet python3 -c "import yaml; yaml.safe_load(open('docker-compose.yml')); yaml.safe_load(open('.github/workflows/ci.yml'))"
cd 3-code/backlog-core
uv run --frozen pytest -q
uv run --frozen ruff check .
uv run --frozen mypy app
```

Expected: drift OK (18 keys), YAML valid, 15/15 tests, ruff clean, mypy strict clean.

**Step 2: Diff review**

```bash
cd /Users/benjaminpoersch/Projects/Vision/ai-sdlc-scaffold-main
git log --oneline 23219e8..HEAD
git diff --stat 23219e8..HEAD
```

Expected: 4 commits ahead of `23219e8`. Each commit references the specific finding(s) it closes.

**Step 3: Targeted code review on the consolidated diff**

Read the full diff and confirm:

- **MED-1 closed:** `/v1/health` body still matches `api-design.md` § health (`{status, version, checks}`); HTTP status now 503 when degraded; existing payload-shape test still passes (it doesn't assert status code, only body).
- **MED-2 closed:** No more `# type: ignore[attr-defined]` in `app/db.py`.
- **LOW-3 closed:** Two new env keys present in `.env.example` (drift +2 keys, was 16 → 18); compose uses `${VAR:-default}` form so omitted values fall back; `_pool_size()` validates `min <= max`.
- **LOW-4 closed:** `_pool_dependency` adapter in `app/main.py` is gone; `Annotated[..., Depends(get_pool)]` directly.
- **LOW-5 / LOW-6 closed:** `client_with_down_pool` moved to `conftest.py`; `client_with_pool` typed as `Iterator[TestClient]`.

If anything looks off (extra noise in the diff, an unintended side effect, an opportunity flagged by the diff that wasn't on the original review list), surface it before pushing.

**Step 4: Push the bundle**

```bash
git push origin main
```

**Step 5: Watch CI**

```bash
sleep 6
RUN_ID=$(gh run list --workflow=ci.yml --limit 1 --json databaseId --jq '.[0].databaseId')
until gh run view "$RUN_ID" --json status --jq '.status' | grep -q completed; do sleep 6; done
gh run view "$RUN_ID" --json conclusion,jobs --jq '{conclusion, jobs: [.jobs[] | {name, conclusion}]}'
```

Expected: 7 jobs all green.

---

## Done criteria

- [ ] All 6 review findings (MED-1, MED-2, LOW-3, LOW-4, LOW-5, LOW-6) closed.
- [ ] No new `# type: ignore` comments anywhere in `3-code/backlog-core/`.
- [ ] `uv run --frozen pytest` reports 15/15 (was 11/11; +1 from Task 2, +3 from Task 3).
- [ ] `uv run --frozen ruff check .` clean.
- [ ] `uv run --frozen mypy app` strict clean.
- [ ] `bash scripts/check-env-drift.sh` reports 18 keys.
- [ ] CI green on the merged commit set.

---

## Notes for the engineer

- **Don't touch the other two skeletons.** `whatsorga-ingest` and `hermes-runtime` `/v1/health` endpoints don't yet have downstream dependencies, so the `200 vs 503` distinction doesn't apply. When `gbrain-bridge` and `kanban-sync` skeletons land, they should follow the same 503-on-degraded pattern — but extending it preemptively is YAGNI.
- **Don't refactor the FakePool** — it's small enough that "make it instrument-counter, configurable success-mode" is right where it should be. Leaving it alone.
- **Why the env-driven pool size in this cleanup, not a future task** — it's a one-liner Compose change + two `.env.example` keys + 3 test cases. Doing it now keeps the cross-cutting "all runtime config in `.env`" invariant from `REQ-MNT-env-driven-config` whole.
- **Compose `${VAR:-default}` semantics** — `${BACKLOG_CORE_DB_POOL_MIN:-1}` resolves to `1` if the env var is unset OR empty. That's the right semantics for optional tuning vars.
- **Why Task 1 bundles MED-2 + LOW-4 but Task 2 stands alone** — Task 1 is pure refactor; combining both touches one module once and tests verify nothing regressed. Task 2 is a behavior change with a new test, which deserves its own commit so a `git revert` would isolate the semantic shift cleanly.

## Related artifacts

- Code review: 2026-04-28 review of commit `23219e8` (in conversation, not committed).
- Component spec: `3-code/backlog-core/CLAUDE.component.md`.
- Stack decision: `decisions/DEC-backend-stack-python-fastapi.md`.
- Storage decision: `decisions/DEC-postgres-as-event-store.md`.
- Env-driven config requirement: `1-spec/requirements/REQ-MNT-env-driven-config.md`.
- API health spec: `2-design/api-design.md` § Health and observability.
- Drift check: `scripts/check-env-drift.sh`.
- CI: `.github/workflows/ci.yml` (`backlog-core-test` job).
