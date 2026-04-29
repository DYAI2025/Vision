# Phase-1 Code-Review Fixes Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Address the HIGH and LOW findings from the 2026-04-29 code review of `TASK-smoke-test-skeleton` + `TASK-phase-1-manual-testing` (the uncommitted Phase-1 finish-line work).

**Architecture:** Three small, focused fixes on the uncommitted working tree, then ship the full Phase-1 finish-line bundle. HIGH 1 (Scenario 3 simulator broken) is the only behavioral fix — adds a `${VAULT_PATH:-/vault}` env-var reference and one new `.env.example` row. LOW 1, 2, 3 are pure UX improvements (pre-build cli image; uv-precheck inline; token-generation reminder). MEDIUM 1 (tailscale-mode `vision health` broken end-to-end) is **out of scope** — it's a pre-existing architectural gap that needs its own tracked task, not a doc fix.

**Tech Stack:** bash, docker-compose YAML, markdown.

**Scope (findings to close):**
- **HIGH 1:** install.md Scenario 3 demonstration is wrong — `VAULT_PATH=...` shell override doesn't reach the gbrain-bridge container because compose hardcodes the value.
- **LOW 1:** `install_vps.sh` doesn't pre-build the cli image; first `smoke_test.sh` invocation incurs ~30-60s build delay.
- **LOW 2:** `runbook` Step 5A and the `README` quickstart silently assume `uv` is installed.
- **LOW 3:** README quickstart skips a token-generation reminder.

**Out of scope:**
- MEDIUM 1 (tailscale-mode `vision health` broken). Captured as a new tracked task `TASK-tailscale-health-aggregation` in the final cleanup commit; resolution comes from a separate plan when the cli stack and `tailscale-serve.json` get a coordinated update.

---

### Task 1: HIGH 1 — Make `VAULT_PATH` env-tunable in compose so Scenario 3 works (and opens the path to operators wanting a non-default vault location)

**Files:**
- Modify: `docker-compose.yml` (gbrain-bridge service block)
- Modify: `.env.example` (add VAULT_PATH row)

**Step 1: Locate the gbrain-bridge `VAULT_PATH` line**

Run:

```bash
grep -n "VAULT_PATH" docker-compose.yml
```

Expected output: 2 matches (gbrain-bridge + kanban-sync). Both currently hardcode `VAULT_PATH: /vault`.

**Step 2: Modify compose to use `${VAULT_PATH:-/vault}` for both services**

In `docker-compose.yml`, change:

```yaml
# In gbrain-bridge service block:
    environment:
      ...
      VAULT_PATH: /vault
```

to:

```yaml
    environment:
      ...
      VAULT_PATH: ${VAULT_PATH:-/vault}
```

Apply the same change to `kanban-sync` service block. Both services must agree on the env-var name + default so they end up reading from the same vault root.

**Step 3: Add VAULT_PATH to `.env.example`**

In `.env.example`, add a new section after the Caddy ingress section (before the Tailscale section):

```bash
# =====================================================================
# Vault filesystem path (gbrain-bridge + kanban-sync)
# =====================================================================

# Path inside containers where the GBrain markdown vault is mounted.
# Optional; defaults to "/vault". Override only when binding the vault
# Docker volume to a non-default path (e.g., a real Obsidian vault
# mounted from the host). Both gbrain-bridge and kanban-sync read this
# value; they must agree on the location.
VAULT_PATH=/vault
```

**Step 4: Verify drift check passes (key count goes 18 → 19)**

```bash
bash scripts/check-env-drift.sh
```

Expected: `OK: .env.example matches docker-compose.yml exactly (19 keys checked).`

**Step 5: Verify YAML still parses**

```bash
uv run --quiet python3 -c "import yaml; yaml.safe_load(open('docker-compose.yml')); print('YAML OK')"
```

Expected: `YAML OK`.

**Step 6: Verify the runbook's Scenario 3 still reads correctly**

The Scenario 3 example in `4-deploy/runbooks/install.md` expects the operator to set `VAULT_PATH=/does-not-exist` on the command line. With this change, that override now flows through to the container as the `${VAULT_PATH:-/vault}` substitution picks up the shell value before docker compose passes it through.

Read `4-deploy/runbooks/install.md` lines around the Scenario 3 block to confirm no further runbook edit is needed. The current text:

```bash
docker compose stop gbrain-bridge
docker compose rm -f gbrain-bridge
# Temporarily point gbrain-bridge at a nonexistent vault path:
VAULT_PATH=/does-not-exist docker compose up -d gbrain-bridge
```

is now correct semantically. Add a clarifying inline comment if helpful (optional; skip if the diff is already explanatory enough).

**Step 7: Update LOW 1 prep — pre-flight verify install_vps.sh's required-key check still works**

`install_vps.sh` currently checks 8 required keys (none with defaults). `VAULT_PATH` has a default, so it must NOT be added to the required-keys list — the install script's `${!key:-}` empty check would fail-fast if `.env.example` is unmodified. Confirm by inspecting `install_vps.sh`:

```bash
grep -A 12 "REQUIRED_KEYS=" scripts/install_vps.sh
```

Expected: 8 names (`COMPOSE_PROFILES`, `POSTGRES_PASSWORD`, 6× tokens). `VAULT_PATH` should NOT be in the list. No change to the script needed.

---

### Task 2: LOW 1 — Pre-build the cli image during install so the first smoke test is fast

**Files:**
- Modify: `scripts/install_vps.sh` (Step 6 — `docker compose build`)

**Step 1: Locate the build line**

```bash
grep -n "docker compose build" scripts/install_vps.sh
```

Expected: 1 match around line ~167.

**Step 2: Add `--profile cli` to the build invocation**

In `scripts/install_vps.sh`, change:

```bash
# === Step 6: build local components ===================================
log "Building per-component images (whatsorga-ingest, hermes-runtime, ...) ..."
docker compose build
```

to:

```bash
# === Step 6: build local components ===================================
# `--profile cli` builds the cli image too (otherwise it builds lazily
# on first `docker compose --profile cli run`, adding 30-60s to the
# first smoke_test.sh run). Other profile-gated services (caddy,
# tailscale) are image-based, not built, so this only affects cli.
log "Building per-component images (whatsorga-ingest, hermes-runtime, ..., cli) ..."
docker compose --profile cli build
```

**Step 3: Verify bash syntax still clean**

```bash
bash -n scripts/install_vps.sh
```

Expected: silent success.

---

### Task 3: LOW 2 — Add `uv` precheck inline in the runbook + README

**Files:**
- Modify: `4-deploy/runbooks/install.md` (Step 5 Option A)
- Modify: `README.md` (Install quickstart)

**Step 1: Update the runbook's Step 5 Option A**

In `4-deploy/runbooks/install.md`, change:

```bash
# Requires uv: `curl -LsSf https://astral.sh/uv/install.sh | sh` if not already present.
uv tool install --from ./3-code/cli vision-cli
vision --version
vision health
```

to:

```bash
# Install uv if not already present (one-time):
command -v uv >/dev/null || curl -LsSf https://astral.sh/uv/install.sh | sh
# Install the CLI:
uv tool install --from ./3-code/cli vision-cli
vision --version
vision health
```

**Step 2: Update the README quickstart**

In `README.md`, the Install section's CLI block. Change:

```bash
uv tool install --from ./3-code/cli vision-cli
vision health
```

to:

```bash
# Install uv first if you don't have it:
command -v uv >/dev/null || curl -LsSf https://astral.sh/uv/install.sh | sh
uv tool install --from ./3-code/cli vision-cli
vision health
```

---

### Task 4: LOW 3 — Add token-generation reminder to README quickstart

**Files:**
- Modify: `README.md` (Install quickstart)

**Step 1: Locate the Install quickstart block**

```bash
grep -n "git clone https://github.com/DYAI2025/Vision" README.md
```

Expected: 1 match in the "## Install" section.

**Step 2: Add the token-generation hint as an inline comment**

In `README.md`, change:

```bash
git clone https://github.com/DYAI2025/Vision.git && cd Vision
cp .env.example .env && $EDITOR .env       # generate tokens with: openssl rand -hex 32
bash scripts/install_vps.sh                 # ~10 min on a fresh host
bash scripts/smoke_test.sh                  # Phase-1 healthcheck-only verification
```

The inline comment `# generate tokens with: openssl rand -hex 32` already exists at the right spot. **Verify by reading lines 9-15 of README.md.** If the comment is present (it should be), this task is a no-op. If absent, add it as shown above.

This task may resolve as zero-diff after verification; that's fine — recording the check is the value.

---

### Task 5: Verify, capture out-of-scope task, and ship

**Files:**
- Modify: `3-code/tasks.md` (record `TASK-tailscale-health-aggregation` for MEDIUM 1)
- (No code changes; verification + tracker addition only.)

**Step 1: Run the full local verification chain**

```bash
cd /Users/benjaminpoersch/Projects/Vision/ai-sdlc-scaffold-main
bash scripts/check-env-drift.sh
uv run --quiet python3 -c "import yaml; yaml.safe_load(open('docker-compose.yml')); yaml.safe_load(open('.github/workflows/ci.yml')); print('YAML OK')"
bash -n scripts/install_vps.sh && bash -n scripts/smoke_test.sh
```

Expected: drift OK (19 keys after Task 1), YAML valid, bash syntax clean for both scripts.

**Step 2: Add `TASK-tailscale-health-aggregation` to tasks.md**

Add a new row in the `### Setup & Infrastructure` section of `3-code/tasks.md` after the existing cross-cutting tasks (`TASK-subject-ref-normalization` etc.) — or in `### Deploy & Operations` if that fits better:

```markdown
| TASK-tailscale-health-aggregation | Make `vision health` work in tailscale-only mode | P2 | Todo | [REQ-PORT-vps-deploy](../1-spec/requirements/REQ-PORT-vps-deploy.md) | TASK-cross-provider-verification | 2026-04-29 | Closes MEDIUM 1 from the 2026-04-29 code review of `TASK-phase-1-manual-testing`. The cli compose service hardcodes `VISION_BASE_URL=http://ingress-caddy`, but `ingress-caddy` doesn't run in tailscale-only mode. Three independent fixes are possible: (a) add per-service `/v1/health/<service>` aliases on each backend FastAPI app + expose them in `tailscale-serve.json`; (b) make the cli compose service's `VISION_BASE_URL` env-overridable so tailscale operators can point at the Tailnet hostname; (c) add a `--per-service` mode to `vision health` that bypasses Caddy aggregation. Pick a path during the task and document the decision. Until then, tailscale operators can run with both profiles enabled (`COMPOSE_PROFILES=caddy,tailscale`) so Caddy provides the aggregation paths over the Tailnet via tailscale-serve.json. |
```

Add the same task ID to the Phase 7 list in the Execution Plan (after `TASK-cross-provider-verification`). Increment task counts in CLAUDE.md (106 → 107; Phase 7 19 → 20).

**Step 3: Trim the runbook's "Tailscale-mode operator verification" section**

In `4-deploy/runbooks/install.md`, replace the existing "Tailscale-mode operator verification" sub-section (the for-loop with empty body that doesn't actually do anything) with:

```markdown
### Tailscale-mode operator verification

Phase 1's `vision health` aggregator targets Caddy's `/v1/health/<service>`
path-rewriting routes, which Tailscale serve does not support (no URL-rewrite
primitive). Tailscale-only operators have two practical options:

1. **Enable both ingresses** by setting `COMPOSE_PROFILES=caddy,tailscale`
   in `.env`. Caddy provides the aggregation paths over the Tailnet via
   the routes declared in `4-deploy/ingress/tailscale-serve.json`. This is
   the easiest path until tailscale-native aggregation lands.
2. **Wait for `TASK-tailscale-health-aggregation`** (see `3-code/tasks.md`),
   which adds either per-service health routes to `tailscale-serve.json`
   or a `--per-service` mode to `vision health`.
```

This replaces the misleading for-loop with truthful current-state advice.

**Step 4: Read the consolidated diff**

```bash
git status --short
git diff --stat
```

Expected: 6 files changed (compose, .env.example, install.md, install_vps.sh, README.md, tasks.md, CLAUDE.md). Plus the still-uncommitted Phase-1-finish-line files from the prior tasks (smoke_test.sh new + others).

**Step 5: Ship — three commits**

Three commits to keep the trail clean:

```bash
# Commit 1: HIGH 1 + LOW 1 review fixes (the actual review-pass diffs)
git add docker-compose.yml .env.example scripts/install_vps.sh \
    4-deploy/runbooks/install.md README.md
git commit -m "fix(phase-1): address HIGH 1 + LOW 1-3 from code review

HIGH 1: docker-compose.yml + .env.example — VAULT_PATH is now
\${VAULT_PATH:-/vault} on both gbrain-bridge and kanban-sync, so
the Scenario 3 demonstration in install.md works end-to-end (and
operators can now bind-mount a real Obsidian vault if desired).
.env.example gains a VAULT_PATH=/vault entry; drift check now at
19 keys.

LOW 1: install_vps.sh — \`docker compose build\` is now
\`docker compose --profile cli build\` so the cli image builds
during install instead of during the first smoke_test.sh run
(saves 30-60s on first verification).

LOW 2: README + install runbook — added a one-line uv-presence
check before \`uv tool install\` so operators on hosts without uv
get the install command inline rather than as a parenthetical.

LOW 3: README quickstart — verified the openssl-rand-hex-32 token-
generation hint is present after the .env copy step (zero-diff for
this finding; the hint was already in place).

Closes HIGH 1, LOW 1, LOW 2, LOW 3 from the 2026-04-29 code review
of TASK-phase-1-manual-testing."

# Commit 2: out-of-scope tracking (MEDIUM 1)
git add 3-code/tasks.md CLAUDE.md
git commit -m "docs(tasks): record TASK-tailscale-health-aggregation for MEDIUM 1

The 2026-04-29 code review of TASK-phase-1-manual-testing surfaced
an architectural gap (MEDIUM 1): tailscale-only operators have no
working \`vision health\` aggregator path because the cli Compose
service hardcodes VISION_BASE_URL=http://ingress-caddy. This is
not a doc bug — it's a real gap that needs a coordinated update
across the cli stack and tailscale-serve.json.

Recorded as TASK-tailscale-health-aggregation (P2, Phase 7) so
the deferred-hardening item is visible in the implementation plan
rather than only in code-review history. Until the task lands,
the documented workaround is enabling both ingress profiles
(COMPOSE_PROFILES=caddy,tailscale).

Total task count 106 → 107; Phase 7 19 → 20."

# Commit 3: ship the original Phase-1 finish-line work + this review pass
git add scripts/smoke_test.sh
git commit -m "feat(phase-1): smoke_test.sh + install runbook + Phase-1 milestone

Final Phase-1 finish-line work:
- TASK-smoke-test-skeleton: scripts/smoke_test.sh — Phase-1
  healthcheck-only smoke test. 4-step flow, 6 named exit codes,
  caddy-mode-only at Phase 1 with documented tailscale-mode gap.
- TASK-phase-1-manual-testing: 4-deploy/runbooks/install.md
  (~280-line install runbook) + README.md refresh + per-component
  README spot-check.

Phase 1 (Bootstrap & Deployment Foundation) is now complete:
17/17 tasks done. All 6 component skeletons shipped, install +
smoke scripts in place, canonical install runbook with
verification scenarios + troubleshooting + GDPR-deferral gate +
rollback procedure. 14 active decisions; 11 CI jobs (4
infra-validation + 6 component-test + 1 scripts-lint).

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"

# Push the bundle
git push origin main
```

**Step 6: Watch CI**

```bash
sleep 8
RUN_ID=$(gh run list --workflow=ci.yml --limit 1 --json databaseId --jq '.[0].databaseId')
until gh run view "$RUN_ID" --json status --jq '.status' | grep -q completed; do sleep 6; done
gh run view "$RUN_ID" --json conclusion,jobs --jq '{conclusion, jobs: [.jobs[] | {name, conclusion}]}'
```

Expected: 11 jobs all green. Particularly: scripts-lint must pass against the modified `install_vps.sh`; env-drift must show 19 keys.

---

## Done criteria

- [ ] HIGH 1 closed: `VAULT_PATH=/does-not-exist docker compose up -d gbrain-bridge` actually flows through to the container; runbook Scenario 3 works as written.
- [ ] LOW 1 closed: `install_vps.sh` builds the cli image during install.
- [ ] LOW 2 closed: runbook + README quickstart have inline `uv` precheck.
- [ ] LOW 3 verified (zero-diff or one-line): README quickstart has token-generation hint.
- [ ] MEDIUM 1 captured as `TASK-tailscale-health-aggregation` (P2, Phase 7).
- [ ] Drift check at 19 keys.
- [ ] CI green on the merged commit set.

---

## Notes for the engineer

- **Don't expand scope.** The MEDIUM 1 fix needs its own plan with a path decision (per-service health routes vs. cli env override vs. `--per-service` flag); doing it here would balloon a documentation cleanup into an architecture change.
- **Compose default-value pattern (`${VAR:-default}`) is the project's idiom** — already used for `OLLAMA_MODEL`, `BACKLOG_CORE_DB_POOL_MIN/MAX`, `CADDY_HTTP_PORT/HTTPS_PORT`, etc. Adding `VAULT_PATH` to that list is consistent.
- **Why VAULT_PATH on both gbrain-bridge and kanban-sync but not whatsorga-ingest / hermes-runtime / backlog-core** — only the two filesystem-bound components read the vault. The other three don't need this env var.
- **Drift check expectation:** 18 keys → 19 after Task 1's `VAULT_PATH=/vault` row. The CI compose-validate step provides dummy values for required-only keys; `VAULT_PATH` has a default so it doesn't need a CI dummy.

## Related artifacts

- Code review: 2026-04-29 review of uncommitted Phase-1 finish-line work (in conversation, not committed).
- Install runbook: `4-deploy/runbooks/install.md`.
- Smoke test: `scripts/smoke_test.sh`.
- Install script: `scripts/install_vps.sh`.
- Active decisions referenced: `DEC-cli-stack-python-typer`, `DEC-cursor-pagination-and-event-stream-conventions` (the latter only for the tailscale-mode rewrite-limitation note).
