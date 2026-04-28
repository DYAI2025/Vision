# ASM-subject-reference-resolvable: A stable subject reference can be indexed across all storage layers

**Category**: Technology

**Status**: Unverified

**Risk if wrong**: Medium — if false, RTBF and data export queries cannot be performed via a single subject-keyed lookup; they require either (a) full-text scans across all storage layers (slow, not 24h-feasible at non-trivial scale), or (b) a redesign of every storage schema to introduce a subject-keyed index column. Either alternative is significant rework, but not architecture-breaking — it changes the implementation route for [REQ-COMP-rtbf](../requirements/REQ-COMP-rtbf.md) and [REQ-COMP-data-export](../requirements/REQ-COMP-data-export.md), not their existence.

## Statement

A stable subject reference (e.g., a phone number, an email, a GitHub handle, a normalized name + role pair) can be used as an indexable key across `backlog-core` events, GBrain pages, and Kanban cards without redesigning the storage schemas of those layers. Subject-keyed lookup is feasible at MVP scale (low thousands of events per project, low tens of projects) within seconds-not-hours latency.

## Rationale

The ingestion path produces `input_event`s that already carry `actor_id` (and source-derived subject identifiers like sender phone). Derived artifacts are linked to their source events via stable references. A `subject_index` mapping subject ref → set of artifact ids across all layers is plausible to maintain without schema-level changes — it can be a derived view or a side-table updated on writes.

The fragile part is normalization: the same subject may appear under multiple identifiers (different phone numbers, name spelling variants). A naive `subject_index` keyed only on raw identifiers will under-resolve subjects with multiple representations. The mitigation is an explicit subject-reference normalization step at registration time, but that step's correctness is what makes this assumption load-bearing rather than free.

## Verification Plan

- **During Code phase:** prototype a `subject_index` populated on writes across `backlog-core`, GBrain, and Kanban; benchmark a representative RTBF query on a synthesized 5,000-event corpus to confirm seconds-scale latency.
- **Decision point:** if normalization complexity grows (multi-identifier subjects, fuzzy names), upgrade `subject_ref` to a multi-identifier subject record with explicit linking decisions, recorded as `learning_event`s.
- **Trigger for re-verification:** event volume per project crosses ~100k; subjects with >2 identifiers each become common.

## Related Artifacts

- Goals: [GOAL-auditable-consent-and-privacy](../goals/GOAL-auditable-consent-and-privacy.md)
- Requirements: [REQ-F-consent-revocation](../requirements/REQ-F-consent-revocation.md), [REQ-COMP-rtbf](../requirements/REQ-COMP-rtbf.md), [REQ-COMP-data-export](../requirements/REQ-COMP-data-export.md)
