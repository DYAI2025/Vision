# US-secret-rotation: Rotate secrets without losing project state

**As an** operator, **I want** a documented procedure to rotate secrets (`.env` values, Tailscale keys, model-runtime credentials) on a running system, **so that** I can respond to suspected key compromise or routine rotation policy without rebuilding from backup.

**Status**: Draft

**Priority**: Should-have

**Source stakeholder**: [STK-ben](../stakeholders.md)

**Related goal**: [GOAL-local-portable-deployment](../goals/GOAL-local-portable-deployment.md)

## Acceptance Criteria

- Given a running system with one or more secrets to rotate, when the operator follows the rotation runbook, then the system continues running with the new secrets, project state and vault content are unchanged, and the rotation is recorded in the audit log.
- Given a rotation has completed, when the operator runs `smoke_test.sh`, then the system passes the smoke test using only the rotated credentials (i.e., no stale credentials remain in any container or volume).

## Derived Requirements

- [REQ-REL-secret-rotation](../requirements/REQ-REL-secret-rotation.md)
- [REQ-MNT-env-driven-config](../requirements/REQ-MNT-env-driven-config.md)
