# backlog-core `cast()` quotes + closeout-note correction

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Resolve the false-positive ruff `TC006` claim that landed in `TASK-bearer-auth-middleware`'s closeout note. Apply the forward-compatible quoted-string style on the existing `cast(_PoolLike, pool)` in `3-code/backlog-core/app/db.py:85` (defense against any future ruff upgrade that does ship `TC006`), then correct the misleading note in `3-code/tasks.md`.

**Architecture:** Two tiny edits driven by the linter+test suite as the verification harness. No new modules, no new tests, no new decisions — just closing out an over-stated concern correctly. Treat the per-component ruff invocation (`uv run --frozen ruff check .` from inside `3-code/backlog-core`) as the canonical CI signal; that's exactly what `.github/workflows/ci.yml` runs.

**Tech Stack:** Python 3.12, ruff 0.7.4 (per-component selectors `E,W,F,I,B,UP,SIM,TCH,RUF`), mypy strict, pytest, uv. No tooling changes required.

**Worktree note:** Plan generated without a dedicated worktree (`/writing-plans` invoked directly, no preceding `/brainstorming`). Scope is two-line edits + one tasks.md cell; running on `main` is fine. If you'd rather isolate, create a worktree and re-point the executor there before Task 1.

---

## Background — why this plan exists

`TASK-bearer-auth-middleware`'s closeout note (in `3-code/tasks.md`) claims:

> **Pre-existing issue surfaced (out of scope):** running `uv run ruff` from the repo root rather than per-component scans `3-code/backlog-core` and reports 2 errors (`TC006` "Add quotes around `cast(_PoolLike, pool)`")…

Verification done while writing this plan:

- `cd 3-code/backlog-core && uv run --frozen ruff check .` → `All checks passed!`
- `uv run --frozen ruff check --select TCH app/db.py` → `All checks passed!`
- `uv run --frozen ruff check --select ALL app/db.py` → 11 findings, **none are TC006** (TRY003, EM101/102, COM812, BLE001, D203/211/212/213 only).
- `uv run --frozen ruff --version` → `ruff 0.7.4`. The `TC006` rule code does not exist at this version; `TC` is not even a valid selector prefix (only `TCH` is). The rule was added in a later ruff release.

So the original claim was wrong on two axes: (a) the per-component invocation that CI runs is clean, and (b) the rule code doesn't exist at our pinned ruff version. The cast itself is also semantically fine — `_PoolLike` is a runtime-resolvable Protocol class defined in the same module above the cast site.

Two reasonable actions follow:

1. **Apply the forward-compat style anyway** — change `cast(_PoolLike, pool)` to `cast("_PoolLike", pool)`. mypy strict accepts the string forward-reference identically (PEP 484). When/if ruff is upgraded to a version that does ship `TC006`, this site will already be clean.
2. **Correct the tasks.md closeout note** — replace the inaccurate "TC006 errors surface from repo root" wording with a brief, accurate note that the original observation was a misread of mixed ruff output.

That's it. Two-task plan.

---

## Task 1: Apply the forward-compat quoted-cast style

**Files:**
- Modify: `3-code/backlog-core/app/db.py:85`

**Step 1: Reproduce the current per-component ruff/mypy/pytest baseline**

Run from inside the component dir to make sure the working tree is clean before any edit (gives a baseline to compare against in Step 4):

```bash
cd 3-code/backlog-core
uv sync --frozen
uv run --frozen ruff check .
uv run --frozen mypy app
uv run --frozen pytest -q
```

Expected output:
- ruff: `All checks passed!`
- mypy: `Success: no issues found in 3 source files`
- pytest: `15 passed`

If any of those fail before you've changed anything, **stop** — the working tree has unrelated drift you need to investigate first.

**Step 2: Make the one-line edit**

Open `3-code/backlog-core/app/db.py`. The current line 85 reads:

```python
    return cast(_PoolLike, pool)
```

Change it to use the forward-reference string form:

```python
    return cast("_PoolLike", pool)
```

Why the string form: `cast(T, value)` evaluates `T` at runtime, which forces `_PoolLike` to be importable at runtime. With `cast("_PoolLike", value)`, mypy still resolves the type at type-check time, but the runtime cost is zero (mypy's `cast` is a no-op at runtime regardless). It also lets `_PoolLike` move under `TYPE_CHECKING` later without breaking the call site, and it's the form that newer ruff versions' `TC006` rule prefers.

Do **not** touch anything else in the file. The other lines have unrelated `--select ALL` findings (TRY003, EM101/102, COM812) that are intentionally not selected by our config.

**Step 3: Re-run the toolchain**

```bash
cd 3-code/backlog-core
uv run --frozen ruff check .
uv run --frozen mypy app
uv run --frozen pytest -q
```

Expected output: identical to Step 1 — `All checks passed!`, mypy clean (3 source files), `15 passed`.

If mypy newly complains about `"_PoolLike"` not being resolvable, double-check the spelling in the string and confirm the `_PoolLike` Protocol is still defined in `app/db.py` above the cast site (it should be, untouched).

**Step 4: Run the full backend matrix to be sure no consumer broke**

Quick smoke across all 5 backends (this is what the bearer-auth closeout did and is a known-fast pass):

```bash
cd /Users/benjaminpoersch/Projects/Vision/ai-sdlc-scaffold-main
for c in whatsorga-ingest hermes-runtime backlog-core gbrain-bridge kanban-sync; do
  echo "=== $c ==="
  (cd 3-code/$c && uv sync --frozen >/dev/null 2>&1 && uv run --frozen ruff check . | tail -1 && uv run --frozen mypy app | tail -1 && uv run --frozen pytest -q | tail -1)
done
```

Expected: every component's three lines read `All checks passed!`, `Success: no issues found in N source files`, `M passed in …s`. Nothing should regress because no consumer imports `_PoolLike` — it is `backlog-core`-internal.

**Step 5: Commit (do NOT include Task 2's edit yet — keep commits focused)**

```bash
git add 3-code/backlog-core/app/db.py
git commit -m "$(cat <<'EOF'
chore(backlog-core): quote forward-ref in cast(_PoolLike, pool)

Forward-compat with future ruff versions that ship TC006 ("Add quotes to
type expression in typing.cast()"). mypy strict treats the string and bare
forms identically; pytest unchanged (15/15 still green).

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 2: Correct the closeout note in `3-code/tasks.md`

**Files:**
- Modify: `3-code/tasks.md` — the `TASK-bearer-auth-middleware` row, specifically the `Notes` cell (a single long markdown table cell).

**Step 1: Locate the exact text to replace**

```bash
grep -n 'TC006' 3-code/tasks.md
```

Expected output: one match in the `TASK-bearer-auth-middleware` row's Notes cell. The phrase to replace begins with `**Pre-existing issue surfaced (out of scope):**` and ends just before the next `Convention pin (informational, not a new decision):` clause.

**Step 2: Use Edit tool to replace the inaccurate sentence**

Find this exact substring inside the `TASK-bearer-auth-middleware` Notes cell:

```
**Pre-existing issue surfaced (out of scope):** running `uv run ruff` from the repo root rather than per-component scans `3-code/backlog-core` and reports 2 errors (`TC006` "Add quotes around `cast(_PoolLike, pool)`"). The errors do not surface in CI because each backend test job runs ruff scoped to its own dir; they should be fixed when the next backlog-core task touches `app/db.py` (recommend either fixing in `TASK-postgres-events-schema` or adding a brief cleanup pass when convenient — non-blocking).
```

Replace it with this corrected wording:

```
**Pre-existing observation correction (closed by 2026-05-02-backlog-core-cast-quotes-followup):** The original closeout claimed `cast(_PoolLike, pool)` in `3-code/backlog-core/app/db.py:85` triggered ruff `TC006`. On verification this is not reproducible — ruff 0.7.4 (our pinned version) does not ship a `TC006` rule, and the per-component CI invocation (`uv run --frozen ruff check .` inside the component dir) is clean. The misread was likely an inadvertent ruff run that crossed config boundaries. The follow-up plan applied the forward-compatible `cast("_PoolLike", pool)` quoted-string form anyway (zero runtime cost; mypy strict accepts it identically) so a future ruff upgrade that does ship `TC006` will land green on this site.
```

**Step 3: Verify the edit**

```bash
grep -n 'TC006' 3-code/tasks.md
```

Expected: still one match, but now inside the corrected sentence (the new text references TC006 to explain what was checked) — confirm by reading the surrounding context with `grep -B1 -A1 TC006 3-code/tasks.md`.

```bash
grep -n 'cast-quotes-followup' 3-code/tasks.md
```

Expected: one match — the new wording's plan filename.

**Step 4: Confirm tasks.md is still well-formed markdown**

The Notes cell is a single very long pipe-delimited table cell. Make sure no embedded `|` was introduced (would break the table):

```bash
awk -F'|' '/TASK-bearer-auth-middleware/ {print NF}' 3-code/tasks.md
```

Expected: a single number (e.g., `10`) representing the column count. Compare against neighboring rows:

```bash
awk -F'|' '/^\| TASK-/ {print NF, $2}' 3-code/tasks.md | head -5
```

Every TASK row should report the same column count.

**Step 5: Commit**

```bash
git add 3-code/tasks.md
git commit -m "$(cat <<'EOF'
docs(tasks): correct TASK-bearer-auth-middleware closeout note

The original "Pre-existing issue surfaced" sentence claimed ruff TC006
errors in 3-code/backlog-core/app/db.py:85, but the per-component CI
invocation is clean and ruff 0.7.4 does not ship a TC006 rule. Replaced
with an accurate closeout that notes the misread, points at this plan,
and records that the forward-compatible quoted-cast form was applied
anyway as future-proofing.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Out of scope (do NOT do these)

These are intentionally NOT in this plan; raise them as separate tasks if the team wants them:

- **Upgrade ruff to a version that includes `TC006`.** Ruff version bumps cross every component's lockfile and CI cache; that is a `chore: ruff X.Y` PR of its own.
- **Tighten the per-component `select = [...]` list to enable more ruff rule families** (`TRY`, `EM`, `COM`, `D`, `BLE`, etc.). The `--select ALL` run surfaces 11 findings in `app/db.py` alone — addressing them is a code-style hardening pass that affects the whole monorepo and should be its own decision (`DEC-ruff-rule-set` or similar).
- **Add a CI guard that runs ruff from the repo root** to catch cross-config inconsistencies. Marginal value over the 5 per-component runs we already have; would need a per-component config aggregation strategy that doesn't exist yet.
- **Fix the other 11 `--select ALL` findings in `app/db.py`.** They are intentional under our current selector set (long error messages, f-strings in raises, missing trailing commas). Out of scope here.

---

## Definition of done

1. `3-code/backlog-core/app/db.py:85` reads `return cast("_PoolLike", pool)`.
2. Per-component `ruff check .`, `mypy app`, `pytest -q` for `backlog-core` are all green.
3. All 5 backend test suites still green (`5 + 14 + 15 + 14 + 19 = 67` tests).
4. `3-code/tasks.md` no longer contains the misleading "TC006 errors surface from repo root" wording. The corrected sentence references this plan filename.
5. Two focused commits land — one for the code change, one for the docs change. Don't squash them; the docs commit should be reverted independently if a later finding shows the original concern was real after all.

---

## If reality differs from this plan's assumptions

This plan is built on the verification done at write-time. If you start Task 1 and find:

- **The per-component `ruff check .` already returns errors** (any kind) before you've edited anything → stop, investigate, do not proceed. The repo has drifted since this plan was written.
- **`pytest -q` reports fewer than 15 passed in `backlog-core`** before any edit → stop, investigate. Some test was deleted or skipped, which would change the baseline this plan claims.
- **mypy strict objects to `cast("_PoolLike", pool)`** after the edit → stop, revert, and either keep the bare form OR move `_PoolLike` to module top before the cast site. Do not silence with `# type: ignore`.

In any of those cases, surface the discrepancy to the user before deciding how to proceed.
