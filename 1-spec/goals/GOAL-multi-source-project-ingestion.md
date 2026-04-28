# GOAL-multi-source-project-ingestion: Multi-channel inputs become structured, routed project work through a single pipeline

**Description**: Project knowledge today is scattered across WhatsApp messages, voice memos, repository events, and ad-hoc notes. This goal turns that fragmented stream into structured project artifacts — tasks, proposals, decisions, risks, open questions — assigned to the correct project, deduplicated, and ready for human review. All input channels flow through one normalization path so that adding a new channel does not require rebuilding routing or classification logic. This is the central capability the system exists to provide; without it nothing else matters.

**Status**: Approved

**Priority**: Must-have

**Source stakeholder**: [STK-vincent](../stakeholders.md), [STK-ben](../stakeholders.md)

## Success Criteria

- [ ] **Channel coverage**: all four MVP input channels (WhatsApp ingest, voice transcripts, repository events, manual CLI) produce `input_event`s through the same WhatsOrga-driven normalization path. New channels can be added by implementing a single adapter contract.
- [ ] **Routing accuracy**: ≥85% of `input_event`s with confidence ≥0.85 are assigned to the correct project on first attempt (measured against human-confirmed ground truth over a rolling 30-day window once the system is in regular use).
- [ ] **Artifact extraction**: ≥80% of project-relevant `input_event`s produce at least one structured artifact candidate (task / proposal / decision / risk / open question) within the same processing pass.
- [ ] **End-to-end latency (autonomous path)**: p95 from input arrival to Kanban card creation is **<5 minutes** for confidence ≥0.85 inputs whose `consent_scope` and auto-policy permit autonomous writes.
- [ ] **End-to-end latency (review path)**: p95 from input arrival to "ready for human review" notification is **<2 minutes** for inputs requiring middle-band review.
- [ ] **Duplicate suppression**: when the same underlying content arrives via two sources (e.g., a WhatsApp message and a manual repaste), duplicate tasks/cards are created in <5% of cases (verified against a labeled duplicate set).

## Related Artifacts

- Stakeholders: [STK-vincent](../stakeholders.md), [STK-ben](../stakeholders.md)
- Constraints: [CON-consent-required](../constraints/CON-consent-required.md), [CON-no-platform-bypass](../constraints/CON-no-platform-bypass.md), [CON-confidence-gated-autonomy](../constraints/CON-confidence-gated-autonomy.md), [CON-no-direct-agent-writes](../constraints/CON-no-direct-agent-writes.md)
- User stories: [US-ingest-from-any-channel](../user-stories/US-ingest-from-any-channel.md), [US-handle-review-required-input](../user-stories/US-handle-review-required-input.md), [US-see-extracted-artifacts](../user-stories/US-see-extracted-artifacts.md)
- Requirements: [REQ-F-input-event-normalization](../requirements/REQ-F-input-event-normalization.md), [REQ-F-project-routing](../requirements/REQ-F-project-routing.md), [REQ-F-artifact-extraction](../requirements/REQ-F-artifact-extraction.md), [REQ-F-duplicate-detection](../requirements/REQ-F-duplicate-detection.md), [REQ-F-review-queue](../requirements/REQ-F-review-queue.md), [REQ-F-confidence-gate](../requirements/REQ-F-confidence-gate.md), [REQ-PERF-ingest-latency](../requirements/REQ-PERF-ingest-latency.md), [REQ-PERF-routing-throughput](../requirements/REQ-PERF-routing-throughput.md)
- Assumptions: [ASM-confidence-scores-are-meaningful](../assumptions/ASM-confidence-scores-are-meaningful.md), [ASM-channel-shape-convergeable](../assumptions/ASM-channel-shape-convergeable.md)
