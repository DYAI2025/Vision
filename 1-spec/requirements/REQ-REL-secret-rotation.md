# REQ-REL-secret-rotation: Secret rotation preserves running state and leaves no stale credentials

**Type**: Reliability

**Status**: Draft

**Priority**: Should-have

**Source**: [US-secret-rotation](../user-stories/US-secret-rotation.md), [CON-vps-portable-deployment](../constraints/CON-vps-portable-deployment.md)

**Source stakeholder**: [STK-ben](../stakeholders.md)

## Description

A documented rotation procedure for runtime secrets preserves running state and project data. Secrets in scope:

- `.env` values (DB credentials, audit-log signing keys, default project tokens, etc.)
- Tailscale keys (when Tailscale ingress mode is enabled)
- Model-runtime credentials (e.g., for an enabled remote-inference profile)

**Procedure** (executed by the operator following `4-deploy/runbooks/secret-rotation.md`):

1. Operator updates `.env` with new secret values.
2. Operator runs the rotation script (or follows the documented manual steps) which restarts **only** the services depending on the rotated secret(s) — not the full stack.
3. `smoke_test.sh` is run against the rotated credentials.
4. A `secret.rotated` audit-log event is written referencing the secret category (e.g., `db_credentials`, `tailscale_authkey`) — **no secret values are logged**, only the category and timestamp.
5. If any verification step fails, the runbook describes how to roll back to the previous secret without losing state.

**Required behaviors:**

- Project state (`backlog-core` events, GBrain pages, Kanban cards, audit log content) is **unchanged in content and identity** by the rotation. The audit log gains one new event; nothing else changes.
- After rotation, **no stale credentials remain anywhere in the running system** — no container env var, no in-memory cache, no volume file, no log artifact contains the prior secret value. A deliberate verification scan against the running system (`grep`-equivalent or explicit credential-scan tool) finds zero references to the prior secret values.
- Rotation does not require destroying or recreating any persistent volume.
- Rotation completes within 10 minutes for any single secret category on the reference VPS spec.

**Failure handling:**

- If service restart fails after secret update, the runbook directs the operator to revert `.env` and restart again — no orphaned state.
- If the audit-log signing key is rotated, the chain transition is recorded explicitly so verification ([REQ-SEC-audit-log](REQ-SEC-audit-log.md)) can validate across the rotation boundary.

## Acceptance Criteria

- Given a running system with seed project state, when the operator rotates `.env` secrets following the runbook, then verification queries (event count, vault page count, kanban card count, audit chain) match pre-rotation state with one additional `secret.rotated` audit event; `smoke_test.sh` passes against the rotated credentials.
- Given a completed rotation, when the operator runs the credential-scan check, then zero references to the prior secret values are found in any running container, env var, volume, or log; a deliberate test injection confirms the scan can detect a stale credential.
- Given an audit-log signing-key rotation, when the audit-log chain is verified across the rotation boundary, then verification passes — the rotation event is the documented bridge between chains.

## Related Constraints

- [CON-vps-portable-deployment](../constraints/CON-vps-portable-deployment.md) — secret rotation is part of the operator-feasibility story.
