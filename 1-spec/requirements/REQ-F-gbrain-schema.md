# REQ-F-gbrain-schema: Every GBrain page validates against type-specific frontmatter requirements at write time

**Type**: Functional

**Status**: Draft

**Priority**: Must-have

**Source**: [GOAL-durable-project-memory](../goals/GOAL-durable-project-memory.md), [CON-tiered-retention](../constraints/CON-tiered-retention.md), [CON-gbrain-no-raw-private-truth](../constraints/CON-gbrain-no-raw-private-truth.md)

**Source stakeholder**: [STK-vincent](../stakeholders.md), [STK-ben](../stakeholders.md), [STK-message-sender](../stakeholders.md)

## Description

Every page in the GBrain vault carries frontmatter that declares its type and identity. `gbrain-memory-write` validates the frontmatter on every insert and update; writes that fail validation are rejected with a structured `schema_violation` error naming the missing or invalid field, and no page is created or modified.

**Required for all pages** (regardless of type):

- `id` — stable, type-prefixed (e.g., `project_<uuid>`, `episode_<uuid>`)
- `type` — one of `project`, `episode`, `decision`, `learning`, `person`, `routing_rules`, `reconciliation`, `system_doc`
- `retention_class` — `derived_keep` or `raw_30d`
- `created_at` — ISO 8601
- `updated_at` — ISO 8601

**Required per type:**

- `project`: `name`, `status` (`active` / `paused` / `archived`), `owners[]`, `confidence_policy`, `tags[]`
- `episode`: `source`, `source_ref`, `actors[]`, `projects[]`, `consent_scope`, `confidence`, `privacy_status` (`clean` / `redacted` / `sensitive` / `blocked`)
- `decision`: `decision_id`, `scope`, `status` (`active` / `deprecated` / `superseded`), `linked_projects[]`, `human_involvement`
- `learning`: `learning_type`, `trigger_event_id`, `project_id`, `before`, `after`, `human_feedback` (optional), `confidence_before`, `confidence_after`, `applies_to[]`
- `person`: `display_name`, `subject_ref`, `consent_status`, `linked_sources[]`
- `routing_rules`: `project_id`, `rule_set_version`, `derived_from[]` (learning event ids that produced these rules)
- `reconciliation`: `run_date`, `unmatched_mutations`, `gate_bypasses`, `orphan_audits`
- `system_doc`: free-form (e.g., the `00_System/` access policy, agent contract pages); minimum required fields only.

Existing pages found out-of-schema by [REQ-MNT-vault-audit-sweep](REQ-MNT-vault-audit-sweep.md) are flagged with the specific missing/invalid fields and queued for repair via the standard correction-action surface (per [REQ-F-correction-actions](REQ-F-correction-actions.md)).

## Acceptance Criteria

- Given a page-write payload missing one or more required fields for its declared type, when `gbrain-memory-write` is invoked, then the write is rejected with `schema_violation` naming each missing or invalid field; no page is created or modified.
- Given a vault with mostly-conformant pages, when [REQ-MNT-vault-audit-sweep](REQ-MNT-vault-audit-sweep.md) runs, then ≥99% of pages validate; non-conformant pages are listed with the failing fields.
- Given a page with an unknown `type` value, when the write is invoked, then it is rejected at the schema boundary; new types must be added to the schema explicitly before writes can use them.

## Related Constraints

- [CON-tiered-retention](../constraints/CON-tiered-retention.md) — `retention_class` is required on every page.
- [CON-gbrain-no-raw-private-truth](../constraints/CON-gbrain-no-raw-private-truth.md) — schema gates a layer that cannot become a raw archive.
- [CON-no-direct-agent-writes](../constraints/CON-no-direct-agent-writes.md) — schema validation lives on the persistence service boundary.
