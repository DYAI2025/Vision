# US-backup-restore-cycle: Take a backup and restore it on a different host

**As an** operator, **I want** to take a backup on host A and restore it on host B using the documented scripts, **so that** I can recover from data loss, migrate hosts, or verify backup integrity on a routine basis.

**Status**: Draft

**Priority**: Should-have

**Source stakeholder**: [STK-ben](../stakeholders.md)

**Related goal**: [GOAL-local-portable-deployment](../goals/GOAL-local-portable-deployment.md)

## Acceptance Criteria

- Given a running system on host A, when the operator runs `backup.sh`, then a single host-independent backup artifact is produced containing project state (`backlog-core`), GBrain vault, Kanban boards, and audit log.
- Given a fresh deployment on host B and the backup artifact from host A, when the operator runs `restore.sh`, then the restored system reproduces project state, vault content, kanban boards, and audit log identically (modulo timestamps and host-specific paths) and the retention sweep correctly re-applies on restored data.

## Derived Requirements

- [REQ-REL-backup-restore-fidelity](../requirements/REQ-REL-backup-restore-fidelity.md)
