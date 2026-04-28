# GOAL-durable-project-memory: GBrain is a usable, queryable, human-readable project memory — without becoming a raw archive

**Description**: Project work spans months. Without a durable memory, every conversation, decision, and learning has to be re-discovered. This goal makes GBrain that memory: a markdown vault navigable in Obsidian, with stable IDs, frontmatter, and bidirectional links between projects, people, episodes, decisions, and learnings; queryable by agents through a brain-first lookup pattern (read before acting); and structurally constrained so it cannot become a covert long-term archive of raw input content. The vault is the layer humans collaborate with; it must remain trustworthy enough that anyone can open it and not encounter raw private content that should have aged out.

**Status**: Approved

**Priority**: Must-have

**Source stakeholder**: [STK-vincent](../stakeholders.md), [STK-ben](../stakeholders.md)

## Success Criteria

- [ ] **Per-project completeness**: every active project has at minimum a populated `PROJECT.md`, `PROFILE.md`, and `CURRENT_STATE.md`, plus current `BACKLOG_SUMMARY.md` and `OPEN_QUESTIONS.md` reflecting the latest backlog state.
- [ ] **Schema conformance**: ≥99% of GBrain pages pass schema validation on stable id presence, required frontmatter fields (`type`, `retention_class`, `created_at`, `updated_at`, source links where applicable), and bidirectional link integrity.
- [ ] **Brain-first lookup discipline**: ≥95% of agent routing decisions are accompanied by a recorded query against GBrain whose result was considered (citation present in the proposal's metadata). Below 95%, the agent surfaces this as a learning gap.
- [ ] **No raw-content leakage in the durable layer**: a periodic vault audit sweep finds **0 pages** with `retention_class=derived_keep` containing recognizable raw input content (full message bodies, full transcripts) at end-of-cycle.
- [ ] **RTBF cascade**: a subject erasure request propagates correctly through linked GBrain pages — episodes, references, learnings — within the same 24h window as the rest of the system, with bidirectional link integrity preserved (no orphaned references).
- [ ] **Human navigation**: the vault is usable in Obsidian without setup beyond opening the folder — internal links resolve, frontmatter renders, Kanban boards display, and a new reader can locate the current state of a known project in <2 minutes.

## Related Artifacts

- Stakeholders: [STK-vincent](../stakeholders.md), [STK-ben](../stakeholders.md)
- Constraints: [CON-gbrain-no-raw-private-truth](../constraints/CON-gbrain-no-raw-private-truth.md), [CON-tiered-retention](../constraints/CON-tiered-retention.md), [CON-no-direct-agent-writes](../constraints/CON-no-direct-agent-writes.md), [CON-gdpr-applies](../constraints/CON-gdpr-applies.md)
- User stories: [US-browse-project-memory](../user-stories/US-browse-project-memory.md)
- Requirements: [REQ-F-gbrain-schema](../requirements/REQ-F-gbrain-schema.md), [REQ-F-bidirectional-links](../requirements/REQ-F-bidirectional-links.md), [REQ-F-brain-first-lookup](../requirements/REQ-F-brain-first-lookup.md), [REQ-MNT-vault-audit-sweep](../requirements/REQ-MNT-vault-audit-sweep.md), [REQ-SEC-redaction-precondition](../requirements/REQ-SEC-redaction-precondition.md), [REQ-COMP-rtbf](../requirements/REQ-COMP-rtbf.md), [REQ-USA-kanban-obsidian-fidelity](../requirements/REQ-USA-kanban-obsidian-fidelity.md)
- Assumptions: [ASM-derived-artifacts-gdpr-permissible](../assumptions/ASM-derived-artifacts-gdpr-permissible.md), [ASM-subject-reference-resolvable](../assumptions/ASM-subject-reference-resolvable.md)
