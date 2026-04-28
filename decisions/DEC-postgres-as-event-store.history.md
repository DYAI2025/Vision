# DEC-postgres-as-event-store: Trail

> Companion to `DEC-postgres-as-event-store.md`.

## Alternatives considered

### Option A: PostgreSQL (chosen)
- Pros: Mature, well-known operationally; strong concurrency story (MVCC); strong WAL-based backup story; rich indexing including partial and expression indexes useful for subject-keyed RTBF queries; standard SQL keeps future migration paths open.
- Cons: Heavier than SQLite; requires operating a database service; backup/restore is slightly more complex than a file-copy approach.

### Option B: SQLite
- Pros: Simplest possible operations — single file; trivially backed up by file copy; zero service to manage.
- Cons: Concurrency story (single writer at a time) is fine for MVP volume but becomes a bottleneck if event throughput grows; WAL backup with concurrent writes requires care; subject-keyed materialized views are less ergonomic; restore-on-different-host with a running writer is awkward.

### Option C: Dedicated event-store library (Marten, EventStoreDB, etc.)
- Pros: Purpose-built for event sourcing — built-in projections, snapshotting, replay primitives.
- Cons: Heavy dependency; locks the system to a specific event-store vendor's lifecycle; less operational mileage on small VPS deployments; backup tooling is more bespoke than `pg_dump`.

## Reasoning

Option A was chosen because the system's event-sourcing needs (append-only, hash-chained, subject-keyed RTBF queries, host-independent backup) are fully expressible in standard SQL with mature tooling. The bespoke-event-store advantage (built-in replay primitives) is offset by the implementation burden of replay being mostly application logic anyway, and by the operational maturity disadvantage. SQLite was rejected on the concurrency-during-active-agent-work consideration: the agent runs continuously, the operator runs queries while the agent works, and Postgres MVCC handles this without the WAL-mode caveats SQLite adds.

Accepted trade-off: one extra Compose service to operate. Mitigations: (a) the operator (Ben) is already comfortable with Postgres; (b) `pg_dump` produces host-independent archives needed for `REQ-REL-backup-restore-fidelity`; (c) Postgres' WAL backup story is the most mature in this category.

## Human involvement

**Type**: ai-proposed/human-approved

**Notes**: Proposed during the architecture-design session (2026-04-27); user approved the architecture proposal which embedded this choice. No alternatives debated extensively in conversation — the proposal preempted the question with a recommendation and the user accepted.

## Changelog

| Date | Change | Involvement |
|------|--------|-------------|
| 2026-04-27 | Initial decision recorded as part of architecture.md drafting | ai-proposed/human-approved |
