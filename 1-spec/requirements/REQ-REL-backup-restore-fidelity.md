# REQ-REL-backup-restore-fidelity: Backup + restore round-trip preserves project state bit-identically

**Type**: Reliability

**Status**: Draft

**Priority**: Should-have

**Source**: [US-backup-restore-cycle](../user-stories/US-backup-restore-cycle.md), [CON-vps-portable-deployment](../constraints/CON-vps-portable-deployment.md)

**Source stakeholder**: [STK-ben](../stakeholders.md)

## Description

A backup taken on host A with `backup.sh` and restored on host B with `restore.sh` reproduces system state with the following fidelity:

**Bit-identical** (must match exactly):

- `backlog-core` event log: identical event ids, types, payloads, ordering, hash chain.
- GBrain vault: identical page contents, frontmatter, file paths within the vault, link integrity (forward + back, per [REQ-F-bidirectional-links](REQ-F-bidirectional-links.md)).
- Kanban boards: identical card content, column placement, ordering.
- Audit log: identical entries, chain integrity preserved end-to-end.
- Consent records: identical per-source state including append-only history.
- `proposal_id` chains: identical, traceable across all linked events.

**Tolerated non-identities** (must be limited to):

- Restore-operation timestamps: `restored_at`, `restored_on_host` (added by `restore.sh`).
- Host-specific paths inside container volumes (when these change, they must be transparent to all services — services read paths from `.env` per [REQ-MNT-env-driven-config](REQ-MNT-env-driven-config.md)).

**Retention sweep correctness on restored data:**

The retention sweep ([REQ-F-retention-sweep](REQ-F-retention-sweep.md)) re-evaluates against **original ingest timestamps**, not restore timestamps. A restored 60-day-old `raw_30d` artifact does not return as "fresh" — the sweep re-deletes it on the next run after restore. RTBF cascades that completed before the backup remain effective on restore (no subject content reappears).

**Backup artifact format:**

- Host-independent archive (e.g., a single `.tar.gz` or directory with a documented schema).
- No host-bound paths embedded in the archive content (paths are relative within the archive).
- Versioned format header (e.g., `vision-backup-v1`) so future format changes can be detected and migrated.

**Round-trip is tested before phase-gate transition to Code completion** — not just in theory. The test is part of the smoke-test suite ([REQ-PORT-vps-deploy](REQ-PORT-vps-deploy.md)).

## Acceptance Criteria

- Given a backup taken on host A and restored on host B, when verification queries are run on B, then event count, hash-chain head, vault page count, kanban card count, audit chain head, and consent record count all match the source within tolerated non-identities.
- Given a restored system with raw artifacts whose original ingest timestamps make them due for deletion, when the next retention sweep runs after restore, then those artifacts are deleted on schedule (sweep evaluates against original timestamps, not restore timestamps).
- Given a backup format change in a future version, when the operator attempts to restore an older-version archive without migration, then `restore.sh` detects the version mismatch and exits with a structured error rather than producing a corrupt restore.

## Related Constraints

- [CON-vps-portable-deployment](../constraints/CON-vps-portable-deployment.md) — backup artifact must be host-independent.
- [CON-tiered-retention](../constraints/CON-tiered-retention.md) — retention sweep must re-apply on restored data.
