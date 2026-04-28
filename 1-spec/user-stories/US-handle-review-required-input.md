# US-handle-review-required-input: Dispose of low-confidence or ambiguous-consent items via a review queue

**As an** operator, **I want** low-confidence or ambiguous-consent input to land in a review queue with explicit disposition options, **so that** edge cases reach me promptly instead of being silently dropped or silently auto-processed.

**Status**: Draft

**Priority**: Must-have

**Source stakeholder**: [STK-ben](../stakeholders.md)

**Related goal**: [GOAL-multi-source-project-ingestion](../goals/GOAL-multi-source-project-ingestion.md)

## Acceptance Criteria

- Given input that falls below the autonomy threshold or has ambiguous consent classification, when ingest processing completes, then the item appears in the review queue tagged with the reason for review and is not propagated to project state.
- Given a queue item, when the operator selects a disposition (reclassify, drop, forward to a specific actor), then the disposition is applied, audit-logged, and (if reclassify) the item re-enters the standard processing path.

## Derived Requirements

- [REQ-F-review-queue](../requirements/REQ-F-review-queue.md)
- [REQ-F-confidence-gate](../requirements/REQ-F-confidence-gate.md)
