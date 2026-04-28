# REQ-F-bidirectional-links: Links between GBrain artifacts are atomic and bidirectional

**Type**: Functional

**Status**: Draft

**Priority**: Must-have

**Source**: [GOAL-durable-project-memory](../goals/GOAL-durable-project-memory.md), [CON-gbrain-no-raw-private-truth](../constraints/CON-gbrain-no-raw-private-truth.md)

**Source stakeholder**: [STK-vincent](../stakeholders.md), [STK-ben](../stakeholders.md)

## Description

When a GBrain artifact references another (project ↔ episode, decision ↔ project, learning ↔ source-event or learning ↔ project, person ↔ episodes, person ↔ sources, etc.), `gbrain-memory-write` maintains the link on **both ends** in a single atomic operation:

- Forward direction on artifact A — e.g., `episode.projects[]` includes `project_id`.
- Reverse direction on artifact B — e.g., `project.episodes[]` includes `episode_id`.

The operation is atomic from any external observer's perspective:

- A write that would create only the forward link is rejected with `link_not_bidirectional`.
- On internal failure midway through the back-link write, the entire operation is rolled back to the pre-write state — no half-link records persist.
- Deletes propagate symmetrically: an RTBF cascade or explicit archival that removes artifact B also removes A's reference to B in the same transaction.

The vault audit sweep ([REQ-MNT-vault-audit-sweep](REQ-MNT-vault-audit-sweep.md)) verifies bidirectional integrity and reports zero tolerance for half-links.

This requirement excludes link-like references that are intentionally one-directional in the schema (e.g., a `system_doc` page citing a project for context — the project does not need a back-link). Such cases must be declared in the schema as `unidirectional_ok: true` so audit and write logic can distinguish them.

## Acceptance Criteria

- Given a write that creates an A → B reference, when `gbrain-memory-write` completes, then both A's forward link and B's back link are present (verified by re-reading both pages).
- Given a write that creates only the forward link (e.g., due to a code bug), when the write is attempted, then it is rejected with `link_not_bidirectional` and neither side is modified.
- Given an RTBF cascade that deletes artifact B, when the cascade completes, then any A-page that previously linked to B no longer contains the reference; vault audit finds zero orphan back-links.

## Related Constraints

- [CON-gbrain-no-raw-private-truth](../constraints/CON-gbrain-no-raw-private-truth.md) — link integrity is part of "trustworthy memory."
- [CON-no-direct-agent-writes](../constraints/CON-no-direct-agent-writes.md) — link maintenance is a `gbrain-memory-write` responsibility, not callable code on the agent side.

## Related Assumptions

- [ASM-subject-reference-resolvable](../assumptions/ASM-subject-reference-resolvable.md) — link integrity for person-references depends on stable subject references.
