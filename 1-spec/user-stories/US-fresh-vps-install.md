# US-fresh-vps-install: Deploy from a clean clone to a working system on any VPS

**As an** operator, **I want** to deploy from a clean clone to a working system on any Docker-capable VPS using only `.env.example` filled in, **so that** I can stand up a new instance, migrate hosts, or recover from disaster without code changes or vendor-specific setup.

**Status**: Draft

**Priority**: Should-have

**Source stakeholder**: [STK-ben](../stakeholders.md)

**Related goal**: [GOAL-local-portable-deployment](../goals/GOAL-local-portable-deployment.md)

## Acceptance Criteria

- Given a fresh VPS with Docker and Docker Compose installed and the repository cloned, when the operator fills in `.env` from `.env.example` and runs `install_vps.sh`, then the install script brings the system up to a passing `smoke_test.sh` without further manual intervention.
- Given a freshly installed system, when the operator inspects the audit log after the smoke test, then no remote inference calls have been made — the default deployment is local-only.

## Derived Requirements

- [REQ-PORT-vps-deploy](../requirements/REQ-PORT-vps-deploy.md)
- [REQ-MNT-env-driven-config](../requirements/REQ-MNT-env-driven-config.md)
