# GOAL-local-portable-deployment: One operator deploys the system to any VPS in under an hour, with default-zero remote inference and tested recovery

**Description**: The system must be operationally cheap to run for a single operator, recoverable from a backup in a known time, and free of vendor lock-in. Ben (sole operator) should be able to bring up a fresh deployment from a clean clone on any Docker-capable VPS, run a smoke test, and have a usable system in under an hour — without code changes, without a cloud-LLM contract, and without a host-specific configuration step. Recovery from backup is tested before the system is considered production-shaped; default behavior makes zero remote inference calls, so privacy-by-default holds even if the operator forgets to configure something.

**Status**: Approved

**Priority**: Should-have

**Source stakeholder**: [STK-ben](../stakeholders.md)

## Success Criteria

- [ ] **Fresh-VPS install time**: from `git clone` to a passing smoke test on a vanilla Ubuntu/Debian VPS with only Docker and Docker Compose pre-installed is **<60 minutes**, using only `.env.example` filled in. No interactive setup beyond the documented `.env` values.
- [ ] **Cross-host portability**: smoke test passes on at least **two different VPS providers** (e.g., Hetzner + Contabo, or any pair Ben designates) without modification to code or Compose files.
- [ ] **Zero-remote default**: a freshly deployed system makes **0 remote inference calls** during the first 24h of operation, regardless of network configuration. Verified by audit-log query showing only local-inference entries.
- [ ] **Backup + restore round-trip**: a full backup taken on host A and restored on host B reproduces project state, GBrain vault, Kanban boards, and audit log identically (modulo timestamps); tested end-to-end at least once before phase-gate transition to Code completion.
- [ ] **Tailscale optional**: system runs end-to-end behind any reverse-proxy choice (Caddy with public hostname or behind Tailscale) driven by a single `.env` flag; both modes pass smoke test.
- [ ] **Operator runbook coverage**: documented runbooks exist and have been dry-run executed for: install, upgrade, backup, restore, secret rotation, RTBF request handling, and rollback of a project state.

## Related Artifacts

- Stakeholders: [STK-ben](../stakeholders.md)
- Constraints: [CON-vps-portable-deployment](../constraints/CON-vps-portable-deployment.md), [CON-local-first-inference](../constraints/CON-local-first-inference.md)
- User stories: [US-fresh-vps-install](../user-stories/US-fresh-vps-install.md), [US-backup-restore-cycle](../user-stories/US-backup-restore-cycle.md), [US-secret-rotation](../user-stories/US-secret-rotation.md)
- Requirements: [REQ-PORT-vps-deploy](../requirements/REQ-PORT-vps-deploy.md), [REQ-MNT-env-driven-config](../requirements/REQ-MNT-env-driven-config.md), [REQ-REL-backup-restore-fidelity](../requirements/REQ-REL-backup-restore-fidelity.md), [REQ-REL-secret-rotation](../requirements/REQ-REL-secret-rotation.md), [REQ-PERF-routing-throughput](../requirements/REQ-PERF-routing-throughput.md)
- Assumptions: [ASM-vps-docker-baseline-stable](../assumptions/ASM-vps-docker-baseline-stable.md)
