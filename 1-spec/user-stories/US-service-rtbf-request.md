# US-service-rtbf-request: Service a right-to-be-forgotten request end-to-end

**As an** operator, **I want** to service an RTBF request keyed on a registered subject reference and confirm completion across all storage layers, **so that** I can defensibly respond to a data-subject erasure request within the legal response window without manual database surgery.

**Status**: Draft

**Priority**: Must-have

**Source stakeholder**: [STK-ben](../stakeholders.md)

**Related goal**: [GOAL-auditable-consent-and-privacy](../goals/GOAL-auditable-consent-and-privacy.md)

## Acceptance Criteria

- Given a known subject reference, when the operator initiates an RTBF action, then all subject-attributable data is removed from `backlog-core` (events redacted to retain audit shape), GBrain pages, Kanban cards, and any raw cache, with the cascade audit-logged.
- Given an RTBF cascade has completed, when the operator runs the per-subject verification query, then it returns zero rows of subject-attributable content across all storage layers.

## Derived Requirements

- [REQ-COMP-rtbf](../requirements/REQ-COMP-rtbf.md)
- [REQ-COMP-data-export](../requirements/REQ-COMP-data-export.md)
