# REQ-MNT-vault-audit-sweep: Weekly vault audit sweep verifies schema, links, redaction, and retention integrity

**Type**: Maintainability

**Status**: Draft

**Priority**: Must-have

**Source**: [GOAL-durable-project-memory](../goals/GOAL-durable-project-memory.md), [CON-gbrain-no-raw-private-truth](../constraints/CON-gbrain-no-raw-private-truth.md), [CON-tiered-retention](../constraints/CON-tiered-retention.md)

**Source stakeholder**: [STK-vincent](../stakeholders.md), [STK-ben](../stakeholders.md), [STK-message-sender](../stakeholders.md)

## Description

A scheduled vault audit sweep runs at least once per week (configurable cadence, ≥1×/week) and verifies four properties across the entire GBrain vault:

1. **Schema conformance** — every page validates against its type's frontmatter requirements per [REQ-F-gbrain-schema](REQ-F-gbrain-schema.md). Non-conformant pages are listed with their failing fields.
2. **Bidirectional link integrity** — every forward link has a matching back link, every back link has a matching forward link, per [REQ-F-bidirectional-links](REQ-F-bidirectional-links.md). Half-links and orphan back-links are listed.
3. **Redaction integrity** — every page tagged `retention_class = derived_keep` is scanned for raw-content markers (full message bodies above N tokens, full transcripts, untyped raw payload references not bounded by a `raw_30d` envelope), per [REQ-SEC-redaction-precondition](REQ-SEC-redaction-precondition.md). Any leak is reported per page.
4. **Retention-class consistency** — `raw_30d` envelopes inside `derived_keep` pages are correctly typed and within their 30-day age. Expired raw envelopes that [REQ-F-retention-sweep](REQ-F-retention-sweep.md) failed to remove are listed (a non-zero count is itself an alert: the retention sweep is failing).

Each sweep produces a `derived_keep` report stored at `05_Learnings/vault-audit/<run-date>.md` with per-check counts, lists of affected page ids, a per-run summary, and a comparison against the previous sweep (drift indicators).

**Targets:**

- Schema conformance: **≥99%** of pages pass.
- Half-links / orphan back-links: **0** (any non-zero is an alert).
- Raw-content leaks in `derived_keep` pages: **0** (any non-zero is a high-priority alert).
- Expired raw envelopes: **0** (any non-zero is a high-priority alert — the retention sweep is failing).

Findings above thresholds (or any non-zero in zero-tolerance categories) trigger alerts and per-page remediation tasks queued through the standard review-queue surface. Operators dispose of remediation tasks via the same accept / edit / reject flow as agent proposals.

## Acceptance Criteria

- Given a vault with one deliberately injected raw-content leak (a full message body in a `derived_keep` GBrain page), when the next vault audit sweep runs, then the leak is detected, the leak count is non-zero, the high-priority alert fires, and a remediation task for the offending page is queued.
- Given a clean vault, when the sweep runs, then schema conformance ≥99%, half-links = 0, raw leaks = 0, expired envelopes = 0; the report records this clean state with drift indicators against the previous sweep.
- Given a vault with one deliberately injected half-link (an A → B link with B's back-link manually removed), when the sweep runs, then the half-link is detected and listed; an alert fires and a remediation task is queued.

## Related Constraints

- [CON-gbrain-no-raw-private-truth](../constraints/CON-gbrain-no-raw-private-truth.md) — sweep is the periodic safety check that this constraint holds in practice.
- [CON-tiered-retention](../constraints/CON-tiered-retention.md) — sweep verifies retention sweep ([REQ-F-retention-sweep](REQ-F-retention-sweep.md)) is not failing silently.
