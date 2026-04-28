# CON-tiered-retention: Three-tier retention enforced via per-artifact retention class

**Category**: Operational

**Status**: Active

**Source stakeholder**: [STK-message-sender](../stakeholders.md), [STK-ben](../stakeholders.md)

## Description

Every stored artifact carries a `retention_class` that governs its lifetime. There are exactly three classes:

- **`raw_30d`** — raw input content (full message bodies, full voice transcripts, full repo event payloads, voice waveforms). Hard-deleted **30 days from ingestion**, with no extension mechanism. The retention sweep is the only legitimate writer of raw content's deletion record.
- **`derived_keep`** — derived artifacts: project profiles, summaries, decisions, learnings, project state, kanban cards, audit metadata. Kept indefinitely, **subject to right-to-be-forgotten** ([CON-gdpr-applies](CON-gdpr-applies.md), Art. 17). Deletion is only triggered by an explicit subject erasure request or an explicit project-level archival action.
- **`review_required`** — content the classifier could not confidently assign to either of the above (e.g., ambiguous consent, mixed personal + project content, classification confidence below threshold). Routed to a human-review queue, **stored only as a review record** (subject reference + minimal context), not as durable input. Until reviewed, it is not processed by any downstream agent or sync; after review it is reclassified to `raw_30d`, `derived_keep`, or dropped.

`retention_class` is set at ingest time by the classifier, may be downgraded by review or by a human correction, and may not be silently upgraded (e.g., from `raw_30d` to `derived_keep`) — promoting requires producing a derived artifact, not relabeling the raw.

The retention sweep runs at least daily, is idempotent, and emits an audit event for every deletion (artifact id, class, age, sweep run id) without including the deleted content.

## Rationale

Operationalizes data minimization while preserving the durable project memory the system exists to provide. The `30d` floor on raw is short enough to qualify as minimization in a typical privacy review while long enough to recover from a misclassification or a correction loop. `derived_keep` is the layer that earns its keep — that's where project memory lives. `review_required` is the safety valve that keeps the classifier's failure mode bounded (route to human, don't guess).

## Impact

- Every storage tier (`backlog-core` events, GBrain pages, Kanban cards, raw blob cache) carries `retention_class` in its schema. There is no untyped storage path.
- Drives a scheduled retention-sweep service (`REQ-F-retention-sweep`) and a sweep audit log.
- Drives a review-queue service and UX (`REQ-F-review-queue`), with per-item disposition (reclassify-and-process / drop / forward to specific actor).
- Drives a per-class deletion path: `raw_30d` deletion is age-driven and one-way; `derived_keep` deletion is triggered by RTBF or archival; `review_required` deletion is triggered by review disposition.
- Affects [CON-gbrain-no-raw-private-truth](CON-gbrain-no-raw-private-truth.md) directly — GBrain may only persist `derived_keep` artifacts and `raw_30d`-classed envelopes; never untyped content.
- Backups must respect retention: a 30d-old raw artifact restored from a 90d-old backup is not "recovered" — the sweep must re-apply on restore.
