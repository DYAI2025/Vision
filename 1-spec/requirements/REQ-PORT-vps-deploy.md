# REQ-PORT-vps-deploy: Fresh-VPS install completes to passing smoke test in under 60 minutes

**Type**: Portability

**Status**: Draft

**Priority**: Should-have

**Source**: [US-fresh-vps-install](../user-stories/US-fresh-vps-install.md), [CON-vps-portable-deployment](../constraints/CON-vps-portable-deployment.md)

**Source stakeholder**: [STK-ben](../stakeholders.md)

## Description

A fresh-VPS install on any Docker-capable Linux host completes from `git clone` to a passing `smoke_test.sh` in **under 60 minutes** without code edits, host-specific patches, or interactive prompts beyond the documented `.env` values.

**Reference baseline:** vanilla Ubuntu 22.04 / 24.04 or Debian 12, Docker Engine ≥ 24, Docker Compose v2, 4 vCPU, 8 GB RAM, ≥ 50 GB disk. Lower-spec hardware may not meet timing targets and is acceptable with documented degraded-mode expectations.

**Cross-host portability:** the install + smoke test must succeed identically on **at least two unrelated VPS providers** designated by the operator (e.g., Hetzner + Contabo). Provider-specific issues, if any, are captured as `DEC-vps-provider-quirk-*` decisions with documented workarounds.

**Smoke test coverage** (`smoke_test.sh`) — the test exercises the end-to-end MVP flow at minimum scale:

- Ingest a synthetic event on each of the four MVP channels (manual CLI, mocked WhatsApp, mocked voice, mocked repo event) with a registered consent record.
- Confirm normalization produces an `input_event` per channel with the shared schema.
- Confirm routing produces a `routing.decided` event with a non-null `cited_pages` (or explicit `lookup_summary` reason).
- Confirm one autonomous-band event produces a Kanban card and a project-page update via the proposal pipeline.
- Confirm one mid-band event lands in the review queue with structured reason.
- Confirm a sample RTBF cascade on a synthetic subject reference resolves to zero rows in the verification query.
- Confirm `smoke_test.sh` exits 0 with no `processing.stuck` alerts in the audit log.

`install_vps.sh`, `smoke_test.sh`, and the supporting runbook live in `scripts/` and `4-deploy/runbooks/install.md`. Required `.env` keys, exit codes, and provider-specific notes are documented there.

## Acceptance Criteria

- Given a vanilla Ubuntu/Debian VPS at the reference baseline with Docker + Compose pre-installed, when the operator clones the repo, fills in `.env` from `.env.example`, and runs `install_vps.sh`, then the install completes and `smoke_test.sh` exits 0 within 60 minutes total elapsed wall time.
- Given the same procedure on a second VPS provider, when run identically, then the install + smoke test produce the same result with no script modifications; any deviations are captured as a `DEC-*` decision.
- Given a fresh install, when the operator inspects the audit log immediately after the smoke test, then no remote inference calls have been recorded — the default deployment is local-only per [CON-local-first-inference](../constraints/CON-local-first-inference.md).

## Related Constraints

- [CON-vps-portable-deployment](../constraints/CON-vps-portable-deployment.md) — anchors the host-independence requirement.
- [CON-local-first-inference](../constraints/CON-local-first-inference.md) — default-zero-remote on fresh install.

## Related Assumptions

- [ASM-vps-docker-baseline-stable](../assumptions/ASM-vps-docker-baseline-stable.md) — assumes the Docker-capable-VPS baseline is stable enough across providers.
