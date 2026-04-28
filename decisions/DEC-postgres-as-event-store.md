# DEC-postgres-as-event-store: Postgres is the event store for `backlog-core`

**Status**: Active

**Category**: Architecture

**Scope**: backend (`backlog-core` service)

**Source**: [GOAL-trustworthy-supervised-agent](../1-spec/goals/GOAL-trustworthy-supervised-agent.md), [REQ-SEC-audit-log](../1-spec/requirements/REQ-SEC-audit-log.md), [REQ-F-state-reconstruction](../1-spec/requirements/REQ-F-state-reconstruction.md), [REQ-REL-event-replay-correctness](../1-spec/requirements/REQ-REL-event-replay-correctness.md), [REQ-REL-backup-restore-fidelity](../1-spec/requirements/REQ-REL-backup-restore-fidelity.md)

**Last updated**: 2026-04-27

## Context

`backlog-core` requires:

- An append-only event log with hash-chain integrity (`REQ-SEC-audit-log`).
- Crash-safe, deterministic replay (`REQ-REL-event-replay-correctness`).
- Concurrent reads while writes are committing (operator queries during agent activity).
- A backup format that round-trips host-independent (`REQ-REL-backup-restore-fidelity`).
- Subject-keyed indexing for RTBF cascades (`REQ-COMP-rtbf`).

A choice between Postgres, SQLite, and bespoke event-store libraries is required at the start of `backlog-core` design.

## Decision

The event store is **PostgreSQL 16+** running as a Compose service alongside `backlog-core`'s service container, with a dedicated database per deployment. The event-log table is append-only by application convention — no DELETE / UPDATE on event rows except RTBF redaction, which is an in-place column update on tombstone-marker fields, with the event id, type, timestamp, and chain hash preserved.

Specific choices:

- One Postgres instance per deployment; no replication at MVP.
- Event-log table partitioned by month for retention-sweep efficiency.
- Subject-keyed materialized views for fast RTBF cascade queries; refreshed on consent-record changes and on bulk RTBF runs.
- WAL-based backups via `pg_dump --format=directory --jobs=N` (or equivalent) into a host-independent archive consumed by `restore.sh`.
- Application code maintains the hash chain on every INSERT and verifies it on every state-reconstruction or audit-verification operation.

## Enforcement

### Trigger conditions

- **Specification phase**: n/a.
- **Design phase**: any design that touches `backlog-core`'s storage layer must consult this decision; changes to schema, indexing strategy, or backup format trigger an update to this decision before implementation.
- **Code phase**: implementation of `backlog-core` uses Postgres-compatible drivers and SQL; no code path may bypass the database for direct file I/O of event data.
- **Deploy phase**: production deployment includes Postgres as a Compose service; `backup.sh` and `restore.sh` target Postgres-formatted archives; the smoke test exercises a backup → restore round-trip.

### Required patterns

- Event-log table is append-only by application convention (no row DELETE / UPDATE except RTBF tombstoning on designated columns).
- Hash chain maintained on every INSERT; verified on every reconstruction or audit run.
- Subject-keyed materialized views refreshed on consent-record changes and bulk RTBF runs.
- Backups produced via `pg_dump`-style host-independent archives; restore script validates archive version.

### Required checks

1. Before merging any change to `backlog-core`'s schema, confirm it is forward-compatible with existing event data (no destructive migration of historical events).
2. On every restore, run hash-chain verification end-to-end before allowing the restored system to accept new writes.
3. On retention-sweep runs, the partition strategy lets the sweep delete expired raw artifacts without walking the entire event log.

### Prohibited patterns

- Direct DELETE or UPDATE on event-log rows (other than RTBF tombstone redaction on designated columns).
- Writing event data to a non-Postgres path (e.g., direct file writes for "performance").
- Postgres-specific features that have no documented portability path to a future store choice — the deployment is single-vendor by choice; this prohibition is forward-looking only.
