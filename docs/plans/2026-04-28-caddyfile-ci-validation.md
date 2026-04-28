# Caddyfile CI Validation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** CI catches Caddyfile syntax errors before merge by running `caddy validate` against `4-deploy/ingress/Caddyfile` on every PR and main-branch push.

**Architecture:** A new GitHub Actions job `caddyfile-validate` runs the official `caddy:2-alpine` image with the repo's Caddyfile mounted read-only. The image's `caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile` exits non-zero on any syntax or semantic error, failing the PR check. The job depends on `structure-check` (so it runs only after the Caddyfile path is confirmed) and runs in parallel with `compose-validate` and `env-drift-check`.

**Tech Stack:** GitHub Actions, Docker, Caddy 2.x (`caddy:2-alpine`).

**Mapping to SDLC scaffold:** This plan corresponds to a deferred-hardening item recorded in `TASK-ingress-caddy-config`'s "Pre-existing issues observed" notes ("Caddyfile syntax not locally validatable"). Once implemented, treat as a new task `TASK-ci-caddyfile-validate` in `3-code/tasks.md` (Deploy & Operations section, P2, Done after Task 3 completes). See Task 4 below.

---

### Task 1: Add the `caddyfile-validate` job to CI

**Files:**
- Modify: `.github/workflows/ci.yml` — insert a new job after the existing `env-drift-check` job, before the trailing comment.

**Step 1: Read the current ci.yml to confirm structure**

```bash
cat .github/workflows/ci.yml | head -100
```

Expected: jobs `structure-check`, `compose-validate`, `env-drift-check`, followed by a trailing comment about per-component lint/test jobs.

**Step 2: Insert the new job**

Use Edit to add the following block immediately before the existing line `# Per-component lint / test jobs are added by per-component skeleton tasks` in `.github/workflows/ci.yml`:

```yaml
  caddyfile-validate:
    name: Caddyfile syntax check
    runs-on: ubuntu-latest
    timeout-minutes: 5
    needs: structure-check
    steps:
      - uses: actions/checkout@v4

      - name: Validate Caddyfile syntax
        run: |
          docker run --rm \
            -v "$PWD/4-deploy/ingress/Caddyfile:/etc/caddy/Caddyfile:ro" \
            caddy:2-alpine \
            caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile

```

**Step 3: Verify the YAML still parses**

```bash
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))"
```

Expected: silent success (no output, exit code 0). If it fails with a YAML parse error, fix indentation and re-run.

**Step 4: Commit**

```bash
git add .github/workflows/ci.yml
git commit -m "ci: add Caddyfile syntax validation job"
```

---

### Task 2: Push and verify the new job runs green

**Files:** none — verification only.

**Step 1: Push to main**

```bash
git push origin main
```

**Step 2: Watch CI on the GitHub Actions UI**

Open: https://github.com/DYAI2025/Vision/actions/workflows/ci.yml

Expected: a CI run kicks off; jobs include `Repository structure check`, `docker-compose syntax check`, `.env.example drift check`, and the new `Caddyfile syntax check`. **All four pass.**

**Step 3: If the new job fails, read the log**

Click into the failing run → `caddyfile-validate` job → expand the "Validate Caddyfile syntax" step. Caddy will print a precise error like:

```
Error: parsing caddyfile tokens for 'handle': /etc/caddy/Caddyfile:42 - Token  - unrecognized directive: foo
```

Fix the offending line in `4-deploy/ingress/Caddyfile`, commit, push.

**Step 4: If a different job fails**

Diagnose separately — likely unrelated to this plan. The most likely culprit is `structure-check` if a required file was renamed; check `git diff main~1 main`.

---

### Task 3: Verify the negative path on a throwaway PR

**Goal:** Prove the new job actually catches syntax errors. Without this, you can't be sure it's not silently passing.

**Files:**
- (temporarily) Modify: `4-deploy/ingress/Caddyfile`

**Step 1: Branch off main**

```bash
git checkout main && git pull
git checkout -b ci-test/caddyfile-syntax-failure
```

**Step 2: Inject a deliberate syntax error**

```bash
cat >> 4-deploy/ingress/Caddyfile <<'EOF'

# Deliberate syntax error for CI verification — will be reverted.
{ unclosed_brace
EOF
```

**Step 3: Commit and push the branch**

```bash
git add 4-deploy/ingress/Caddyfile
git commit -m "test: inject deliberate Caddyfile syntax error"
git push origin ci-test/caddyfile-syntax-failure
```

**Step 4: Open a draft PR**

```bash
gh pr create --draft \
  --title "test: verify caddyfile-validate catches syntax errors" \
  --body "Throwaway PR — verifies the new caddyfile-validate CI job fails on syntax error. Will be closed without merge."
```

**Step 5: Watch CI on the PR fail correctly**

Expected:
- `Repository structure check` — **PASS**
- `docker-compose syntax check` — **PASS**
- `.env.example drift check` — **PASS**
- `Caddyfile syntax check` — **FAIL** with an error message pointing at the unclosed brace

If the `Caddyfile syntax check` job **passes** despite the deliberate error, the validation isn't actually working — investigate before closing the PR.

**Step 6: Close the PR without merging**

```bash
gh pr close --delete-branch --comment "Verification complete: CI correctly caught the syntax error."
```

**Step 7: Confirm main is clean**

```bash
git checkout main && git pull
bash scripts/check-env-drift.sh
```

Expected: drift check `OK: ... 16 keys checked`; main's CI is green.

---

### Task 4: Track as `TASK-ci-caddyfile-validate` in `3-code/tasks.md`

**Goal:** Bring this hardening into the SDLC scaffold's task tracker so progress / decisions / dependencies stay coherent with the rest of the implementation plan.

**Files:**
- Modify: `3-code/tasks.md` — add a row in the **Deploy & Operations** section + add the task ID to the Execution Plan's Phase 1 task list.
- Modify: `CLAUDE.md` — bump the implementation-progress counter.

**Step 1: Add the task row**

Use Edit to add this row at the end of the **Deploy & Operations** task table (immediately before the table that closes the section, i.e. before the `### Phase 7 manual-testing` row or after `TASK-phase-1-manual-testing`, depending on grouping):

```markdown
| TASK-ci-caddyfile-validate | CI Caddyfile syntax validation job | P2 | Done | [REQ-MNT-env-driven-config](../1-spec/requirements/REQ-MNT-env-driven-config.md) | TASK-ingress-caddy-config | 2026-04-28 | New `caddyfile-validate` job in `.github/workflows/ci.yml` runs `caddy validate` against the mounted Caddyfile via the `caddy:2-alpine` image. Closes the deferred-hardening item from `TASK-ingress-caddy-config`'s "Pre-existing issues observed". Negative-path verification recorded in commit / PR history. |
```

**Step 2: Add the task ID to the Phase 1 list in the Execution Plan**

Find the `### Phase 1: Bootstrap & Deployment Foundation` heading in `3-code/tasks.md`. Add `- TASK-ci-caddyfile-validate` to the Phase 1 task list, ordered after `TASK-ingress-caddy-config` (its dependency) but before `TASK-phase-1-manual-testing`.

**Step 3: Update CLAUDE.md Current State**

Bump the implementation-progress sentence:
- `7 / 105 tasks Done` (was `6 / 105`)
- `Phase 1: 7/16 tasks complete` (was `6/16`)

Add a sentence:
> Just completed: `TASK-ci-caddyfile-validate` — new `caddyfile-validate` CI job validates `4-deploy/ingress/Caddyfile` syntax on every PR and main-branch push (closes hardening item from `TASK-ingress-caddy-config`).

**Step 4: Commit the tracking updates**

```bash
git add 3-code/tasks.md CLAUDE.md
git commit -m "docs(tasks): record TASK-ci-caddyfile-validate as Done"
git push origin main
```

---

## Done criteria

- [ ] `caddyfile-validate` job exists in `.github/workflows/ci.yml` with `timeout-minutes: 5` and `needs: structure-check`.
- [ ] Main-branch CI passes the new job (Task 2 step 3 confirmed green).
- [ ] Negative-path verification done on a throwaway PR (Task 3 step 5 confirmed FAIL on injected error, then PR closed).
- [ ] `TASK-ci-caddyfile-validate` recorded as `Done` in `3-code/tasks.md` and reflected in `CLAUDE.md` Current State (Task 4).
- [ ] All commits pushed to `origin/main`.

---

## Notes for the engineer

- **Don't over-engineer.** The Docker-image-based validation is intentionally simple. If multiple Caddyfiles or snippets get added later, consider switching to an installed-Caddy-on-runner approach (e.g., the `download` step from Caddy's GitHub releases) — but only when the simpler approach genuinely breaks down.
- **The negative-path verification is one-time.** Do **not** leave a deliberate-error commit on any branch other than the throwaway test branch. Task 3's branch is closed and deleted before Task 4 starts.
- **Cold-cache cost:** the first run of the new job pulls `caddy:2-alpine` (~30 MB compressed). Adds ~5–10 s on first runner. Subsequent runs reuse the cached image. Acceptable.
- **Don't bypass the structure-check dependency.** The new job is `needs: structure-check` so it only runs after the Caddyfile's parent dir is confirmed present. If structure-check itself ever moves, update this dependency too.
- **If you need to debug the Caddy validate command locally** before pushing, run it directly against your filesystem (requires Docker installed locally):
  ```bash
  docker run --rm \
    -v "$PWD/4-deploy/ingress/Caddyfile:/etc/caddy/Caddyfile:ro" \
    caddy:2-alpine \
    caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile
  ```
  Same command CI runs — so if it passes locally, it'll pass on CI.

## Related artifacts

- Source plan input: pre-existing-issues-observed note in `TASK-ingress-caddy-config` summary.
- CI workflow: `.github/workflows/ci.yml`.
- Caddyfile being validated: `4-deploy/ingress/Caddyfile`.
- Task tracker: `3-code/tasks.md` (after Task 4 lands).
- Operator reference: `4-deploy/ingress/README.md` already mentions `caddy validate` as the local-verification command (Task 4 step 2 of the original ingress task's "Updating routes" section).
