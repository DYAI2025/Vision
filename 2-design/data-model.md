# Data Model

## Purpose

This document defines the data structures that the system's storage layers persist and the cross-cutting payload shapes that flow between components. It is the schema-level companion to [`architecture.md`](architecture.md). The design principle remains: **the simplest schema that makes every approved requirement satisfiable** — including future-proofing only where the cost of getting it wrong is high (e.g., audit-log integrity, RTBF semantics).

The data is split across three storage layers, each owned by exactly one service:

- **Postgres** — owned by [`backlog-core`](architecture.md). Holds the event log, consent records, audit metadata, and materialized views for cross-cutting queries.
- **GBrain vault** (filesystem) — owned by [`gbrain-bridge`](architecture.md). Holds human-readable markdown pages with structured frontmatter.
- **Obsidian Kanban** (filesystem subtree) — owned by [`kanban-sync`](architecture.md). Holds Kanban boards as markdown files with sync-owned + user-owned card frontmatter.

A small number of payload shapes flow across all three layers (`input_event`, `proposal`, `learning_event`); these are defined once in this document and referenced everywhere they appear.

---

## Postgres schema (`backlog-core`)

### `events` — single discriminated event table

The canonical append-only log. Every event in the system — input arrivals, routing decisions, proposals, dispositions, audit records, retention sweeps, RTBF cascades, etc. — is a row in this table.

| Column | Type | Notes |
|---|---|---|
| `event_id` | UUID PK | generated at emit (UUIDv7 preferred for time-sortable ids) |
| `event_type` | TEXT NOT NULL | enum-like; full catalog below; CHECK constraint enforces the allowed set |
| `created_at` | TIMESTAMPTZ NOT NULL DEFAULT now() | event time; defines chain order |
| `actor_id` | TEXT NOT NULL | who emitted: `hermes`, `STK-vincent`, `STK-ben`, `system`, `whatsorga-ingest`, etc. |
| `proposal_id` | UUID, nullable | links chains across propose → validate → apply → disposition → learning |
| `source_input_event_id` | UUID, nullable | originating `input.received` event; FK to this same table |
| `subject_ref` | TEXT, nullable | indexable subject reference for RTBF (phone, email, GitHub handle, normalized name) |
| `payload` | JSONB | type-specific content; full event body |
| `payload_hash` | BYTEA NOT NULL | `SHA-256(canonical_json(payload))` at insert; **never modified** |
| `prev_hash` | BYTEA NOT NULL | `events.hash` of the immediately preceding event in chain order |
| `hash` | BYTEA NOT NULL | `SHA-256(event_id ‖ event_type ‖ created_at ‖ actor_id ‖ payload_hash ‖ prev_hash)` |
| `retention_class` | TEXT NOT NULL | `audit_kept` / `raw_30d` / `derived_keep`; CHECK constraint |
| `redacted` | BOOLEAN NOT NULL DEFAULT FALSE | `TRUE` after retention sweep or RTBF cascade |
| `redaction_run_id` | UUID, nullable | id of the sweep / RTBF run that redacted this row |
| `redacted_at` | TIMESTAMPTZ, nullable | |

**Append-only by application convention.** No `DELETE` on this table outside the retention-sweep service or the RTBF cascade engine. No `UPDATE` outside redaction (`payload`, `redacted`, `redaction_run_id`, `redacted_at`) — and even those updates never touch chain-affecting columns.

#### Hash chain mechanic

The hash chain incorporates `payload_hash` (a stable digest computed once at insert) rather than hashing `payload` directly — see [`DEC-hash-chain-over-payload-hash`](../decisions/DEC-hash-chain-over-payload-hash.md). Consequence:

- When retention sweep or RTBF redacts a row's `payload`, `payload_hash` is **not** modified.
- Chain verification recomputes `hash` from the row's static fields + `payload_hash` and validates against `prev_hash` chain. Verification still passes after redaction.
- Optional secondary check: where `payload IS NOT NULL`, verify `SHA-256(canonical_json(payload)) == payload_hash`. Catches accidental mutation on non-redacted rows.

This satisfies `REQ-SEC-audit-log`'s tamper-evidence-after-RTBF requirement and `REQ-COMP-rtbf`'s "audit shape preserved" requirement.

#### Partitioning

The `events` table is **range-partitioned by month** on `created_at`. Per-month partitions let:

- Retention sweep target only the partitions that contain due `raw_30d` rows (current month - 1 and earlier).
- RTBF cascade walk by partition for time-bounded subject queries.
- Old fully-swept partitions persist (the chain must be reconstructible end-to-end) — they hold rows whose `payload` is redacted but whose `payload_hash` and chain integrity are intact.

Partitions are not dropped at MVP. If event volume grows to where partition retention becomes a concern, the cold-tier strategy is recorded in a future `DEC-*`.

#### Indexes

| Index | Purpose |
|---|---|
| `(subject_ref, created_at)` | RTBF / data-export per-subject queries |
| `(proposal_id)` | chain walking from proposal id to applied / rejected / disposition |
| `(event_type, created_at)` | type-specific scans (daily reconciliation enumerates `proposal.applied` etc.) |
| `(retention_class, created_at)` partial WHERE `redacted = FALSE` | sweep candidate selection |
| `(source_input_event_id)` | tracing an input through the pipeline |

#### Event-type catalog

Every `event_type` and its `payload` shape is documented here. Default `retention_class` is shown but can be overridden per event when justified (e.g., a `proposal.proposed` carrying raw quoted content might be `raw_30d`).

| `event_type` | Payload shape (key fields) | Default `retention_class` |
|---|---|---|
| `input.received` | `input_event` (see Cross-cutting payloads) | `raw_30d` |
| `routing.decided` | `{routing_decision, cited_pages[], lookup_summary}` | `derived_keep` |
| `proposal.proposed` | `proposal` (see Cross-cutting payloads) | `derived_keep` |
| `proposal.applied` | `{result_event_ids[], applied_at}` | `audit_kept` |
| `proposal.rejected` | `{rejection_reason, gate_band?, validation_failure?}` | `audit_kept` |
| `proposal.disposition` | `{actor_id, disposition (accept / edit_and_accept / reject), diff?, human_feedback?}` | `audit_kept` |
| `learning.recorded` | `learning_event` (see Cross-cutting payloads) | `derived_keep` |
| `source.registered` | `{source_id, actor_id, consent_scope, retention_policy, granted_at, granted_by}` | `audit_kept` |
| `source.consent_updated` | `{source_id, prior_scope, new_scope, prior_retention, new_retention, change_reason}` | `audit_kept` |
| `source.consent_revoked` | `{source_id, prior_scope, prior_state, change_reason}` | `audit_kept` |
| `retention.deleted` | `{event_id, retention_class, age_days, sweep_run_id}` | `audit_kept` |
| `rtbf.run_started` | `{rtbf_run_id, subject_ref, requested_by}` | `audit_kept` |
| `rtbf.cascade_completed` | `{rtbf_run_id, subject_ref, layer_counts: {events, gbrain, kanban, raw_cache}, completed_at}` | `audit_kept` |
| `rtbf.verification_passed` | `{rtbf_run_id, layer_counts, verified_at}` | `audit_kept` |
| `remote_inference.called` | `{caller, data_class, source_id, consent_scope_snapshot, model_id, profile, request_size, response_size, latency_ms, outcome}` | `audit_kept` |
| `audit.gate_decision` | `{action_site, gate_band, confidence, consent_state, whitelist_entry, auto_policy, demotion_reason?, outcome}` | `audit_kept` |
| `gbrain.page_mutated` | `{page_id, mutation_type (created/updated/deleted), before_hash, after_hash}` | `audit_kept` |
| `kanban.card_mutated` | `{card_id, board, mutation_type, before_hash, after_hash}` | `audit_kept` |
| `kanban.user_edit` | `{card_id, before, after, actor_id}` | `derived_keep` |
| `unattributed_edit` | `{card_id, diff, detected_at}` | `audit_kept` |
| `secret.rotated` | `{secret_category, rotated_at}` (no values logged) | `audit_kept` |
| `duplicate.detected` | `{existing_artifact_id, new_input_event_id, semantic_score, lexical_score}` | `derived_keep` |
| `review.disposed` | `{review_id, disposition, actor_id}` | `audit_kept` |
| `processing.stuck` | `{event_id, last_step, elapsed_ms}` | `audit_kept` |
| `extraction.empty` | `{input_event_id, reason}` | `audit_kept` |
| `learning_gap.brain_first_discipline` | `{project_id, citation_rate, window}` | `derived_keep` |
| `subject.export_produced` | `{subject_ref, formats[], byte_size}` | `audit_kept` |
| `kanban.user_edit_acknowledged` | `{card_id, kanban_user_edit_event_id, disposition}` | `audit_kept` |

Adding a new event type requires:
1. Adding it to the `event_type` CHECK constraint in `events`.
2. Documenting its payload shape in this table.
3. Setting its default `retention_class`.
4. Updating the daily reconciliation query if it participates in mutation chains.

### `consent_sources` — current consent state per source

| Column | Type | Notes |
|---|---|---|
| `source_id` | TEXT PK | stable, unique |
| `actor_id` | TEXT NOT NULL | source owner |
| `lawful_basis` | TEXT NOT NULL | constant `consent`; CHECK constraint enforces `= 'consent'` per `REQ-COMP-consent-record` |
| `consent_scope` | JSONB NOT NULL | booleans; default all `false` until granted |
| `retention_policy` | TEXT NOT NULL | enum `raw_30d` / `derived_keep` / `review_required` |
| `current_state` | TEXT NOT NULL | `active` / `revoked`; default `active` on registration |
| `granted_at` | TIMESTAMPTZ NOT NULL | |
| `granted_by` | TEXT NOT NULL | actor / channel of consent |
| `updated_at` | TIMESTAMPTZ NOT NULL | |

**`consent_scope` shape:**

```json
{
  "route_to_projects": false,
  "summarize": false,
  "extract_artifacts": false,
  "learning_signal": false,
  "remote_inference_allowed": false
}
```

All flags default `false`. New flags can be added forward-compatibly (e.g., `derivative_retention_consent` per the GDPR-deferral fallback) — old sources read `false` for new keys until updated.

### `consent_history` — append-only history

| Column | Type | Notes |
|---|---|---|
| `history_id` | UUID PK | |
| `source_id` | TEXT NOT NULL FK → `consent_sources` | |
| `changed_at` | TIMESTAMPTZ NOT NULL | |
| `prior_scope` | JSONB | NULL on first registration |
| `new_scope` | JSONB NOT NULL | |
| `prior_retention` | TEXT | NULL on first registration |
| `new_retention` | TEXT NOT NULL | |
| `prior_state` | TEXT | NULL on first registration |
| `new_state` | TEXT NOT NULL | |
| `change_reason` | TEXT | optional |
| `event_id` | UUID NOT NULL FK → `events.event_id` | the corresponding `source.registered` / `source.consent_updated` / `source.consent_revoked` event |

**Append-only.** No `DELETE` or `UPDATE`. RTBF cascades may set `prior_scope`, `new_scope`, `change_reason` to a tombstone value but preserve `history_id`, `source_id`, `changed_at`, and `event_id` for audit shape.

#### Read-as-of query (for `REQ-COMP-consent-record`)

```sql
SELECT new_scope, new_retention, new_state
FROM consent_history
WHERE source_id = $1
  AND changed_at <= $2
ORDER BY changed_at DESC
LIMIT 1;
```

Index: `(source_id, changed_at DESC)` makes this a single seek.

### `subject_index` — materialized view for fast RTBF / export

```sql
CREATE MATERIALIZED VIEW subject_index AS
  SELECT
    subject_ref,
    event_id,
    event_type,
    retention_class,
    created_at,
    redacted
  FROM events
  WHERE subject_ref IS NOT NULL;

CREATE INDEX subject_index_subject_ref_idx ON subject_index (subject_ref);
CREATE INDEX subject_index_redacted_idx ON subject_index (redacted) WHERE redacted = FALSE;
```

Refresh schedule:
- On every `consent_history` insert (small, fast — affects rows for that source's `subject_ref`).
- On every RTBF run completion (refresh the affected `subject_ref` rows only — incremental refresh via a stored procedure rather than full mat-view refresh).
- Daily full refresh as a safety check.

This view powers `REQ-COMP-rtbf` and `REQ-COMP-data-export` per-subject scans without walking the full event log.

#### Subject-reference normalization

`subject_ref` is **populated by `whatsorga-ingest`** at event ingest, computed from one or more identifiers carried by the channel (phone number, email, GitHub handle, normalized name) and validated against the source's known actor identifiers. The normalization function is shared with the `person` GBrain page schema's `subject_ref` field — both must produce the same key for the same human.

Pending verification: `ASM-subject-reference-resolvable` (Code phase). If multi-identifier subjects are common, the index becomes a join over a `person.linked_identifiers[]` table, recorded as a future decision.

### Retention partitioning + sweep semantics

Retention sweep ([`REQ-F-retention-sweep`](../1-spec/requirements/REQ-F-retention-sweep.md)) runs at least daily. For each partition older than today:

1. `SELECT event_id FROM events_<partition> WHERE retention_class = 'raw_30d' AND created_at < now() - interval '30 days' AND redacted = FALSE`
2. For each row found, `UPDATE events SET payload = '{"_redacted": true, "_reason": "retention_sweep", "_run_id": ...}'::jsonb, redacted = TRUE, redaction_run_id = $1, redacted_at = now() WHERE event_id = $2`
3. Emit a `retention.deleted` event with the original event metadata.
4. Refresh the affected rows in `subject_index`.

The sweep is idempotent — re-running on the same partitions skips already-redacted rows. Crash safety: a sweep run records its `sweep_run_id` and a "started_at" event; if interrupted, the next run resumes from the highest committed redaction id.

### Backup format

`pg_dump --format=directory --jobs=N --no-owner --no-privileges` produces a host-independent archive consumed by `restore.sh`. The archive includes the events partitions, consent tables, and a sequence-number reset on restore. Hash-chain verification runs end-to-end on the restored database before the system accepts new writes — see `REQ-REL-backup-restore-fidelity`.

---

## Cross-cutting payload shapes

These payloads flow across services and are defined once.

### `input_event`

The canonical shape produced by `whatsorga-ingest`'s normalization layer for any channel.

```json
{
  "source_id": "string",
  "actor_id": "string",
  "arrived_at": "iso8601",
  "consent_snapshot": {
    "consent_scope": {
      "route_to_projects": true,
      "summarize": true,
      "extract_artifacts": true,
      "learning_signal": true,
      "remote_inference_allowed": false
    },
    "retention_policy": "raw_30d",
    "consent_history_id": "uuid"
  },
  "consent_check_result": {
    "permitted": true,
    "reason": null
  },
  "content_payload": "...",
  "channel_metadata": {
    "channel": "whatsapp | voice | repo | manual",
    "...": "channel-specific extension"
  }
}
```

`content_payload` is the raw input content — its shape is channel-specific (text body, transcript fragments, repo event payload, CLI input). Routing and extraction operate on the rest of the fields and treat `content_payload` as opaque except when explicitly extracting from it. See `REQ-F-input-event-normalization`.

`consent_snapshot` is captured at ingest time so that downstream processing operates on the consent state that was active at arrival, even if the source's consent has been updated since.

### `proposal`

Emitted by `hermes-runtime` for every proposed mutation and persisted as a `proposal.proposed` event. Threaded through validation → apply / reject via `proposal_id`.

```json
{
  "proposal_id": "uuid",
  "tool_id": "backlog-core | gbrain-bridge | kanban-sync",
  "content": {
    "...": "tool-specific schema (a kanban-sync proposal contains card content; a gbrain-bridge proposal contains page content)"
  },
  "gate_inputs": {
    "confidence": 0.91,
    "gate_band": "high",
    "consent_snapshot": { "...": "see input_event" },
    "whitelist_entry": true,
    "auto_policy": {
      "this_action_class": "autonomous"
    },
    "demotion_reason": null
  },
  "source_input_event_id": "uuid",
  "cited_pages": ["project_<uuid>", "episode_<uuid>"],
  "learnings_applied": ["learning_<uuid>"]
}
```

`gate_inputs` is recorded so [`REQ-REL-audit-reconciliation`](../1-spec/requirements/REQ-REL-audit-reconciliation.md) can detect bypasses (gate-decision absent → bypass). `cited_pages` and `learnings_applied` satisfy `REQ-F-decision-inspection` and `REQ-F-brain-first-lookup`.

### `learning_event`

Emitted on every disposition, recorded as a `learning.recorded` event, also written as a GBrain page (see Vault layer).

```json
{
  "learning_type": "routing | confidence | correction | project_structure | agent_behavior",
  "trigger_event_id": "uuid",
  "project_id": "project_<uuid>",
  "before": "string (snippet/summary of pre-correction proposal)",
  "after": "string (snippet/summary of post-correction outcome)",
  "actor_id": "STK-vincent | STK-ben",
  "applies_to": ["routing/project_X", "extraction/project_X"],
  "confidence_before": 0.62,
  "confidence_after": 1.0,
  "human_feedback": "string (optional)"
}
```

`confidence_after = 1.0` for human dispositions per `REQ-F-correction-actions`. `applies_to` is a list of scope identifiers the learning bears on, used by the learning-loop in `hermes-runtime` to decide which subsequent proposals consult this learning.

---

## GBrain page schemas

All GBrain pages are markdown files with YAML frontmatter, persisted under `<vault>/` (vault root). `gbrain-bridge` validates frontmatter on every insert and update — out-of-schema writes are rejected with a structured `schema_violation` error per `REQ-F-gbrain-schema`.

### Common frontmatter (required on every page)

```yaml
id: <type>_<uuid>
type: <one of the type values below>
retention_class: derived_keep
created_at: iso8601
updated_at: iso8601
```

`gbrain-bridge` rejects any page missing any of these fields.

### Per-type schemas

#### `project` — `<vault>/01_Projects/<project_slug>/PROJECT.md`

```yaml
id: project_<uuid>
type: project
retention_class: derived_keep
created_at: iso8601
updated_at: iso8601
name: string
status: active | paused | archived
owners: [string]                     # subject_refs of human owners
confidence_policy: default_0_85 | tuned
auto_policy:
  routing: autonomous | review-only | blocked
  extraction: autonomous | review-only | blocked
  proposal_apply: autonomous | review-only | blocked
band_thresholds:
  low: 0.55
  high: 0.85
tags: [string]
linked_episodes: [episode_<uuid>]
linked_decisions: [decision_<uuid>]
linked_learnings: [learning_<uuid>]
linked_owners: [person_<uuid>]
```

Adjacent pages in the project subtree (`PROFILE.md`, `CURRENT_STATE.md`, `BACKLOG_SUMMARY.md`, `OPEN_QUESTIONS.md`, `RISKS.md`, `DECISIONS.md`, `LEARNINGS.md`) link back to the project page via the project's `id`.

#### `episode` — `<vault>/03_Episodes/YYYY-MM-DD/<episode_id>.md`

```yaml
id: episode_<uuid>
type: episode
retention_class: derived_keep
created_at: iso8601
updated_at: iso8601
source: whatsapp | voice | repo | manual | obsidian
source_event_id: <event_uuid>        # the input.received event in backlog-core
actors: [string]                     # subject_refs
projects: [project_<uuid>]
consent_scope: { ... }               # snapshot at ingest
confidence: number
privacy_status: clean | redacted | sensitive | blocked
```

Episodes are **always `derived_keep` summaries** at MVP. Raw transcripts / message bodies live in `backlog-core`'s `input.received` events and are swept at 30 days. If raw content is needed in the vault for context, it lives in a separately-classed `raw_30d` envelope page that the episode links to; the redaction-precondition check in `gbrain-bridge` rejects raw content embedded directly in episode summaries.

#### `decision` — `<vault>/04_Decisions/<decision_id>.md`

> Note: this is a **project-level decision** recorded by Hermes/operators about project work — distinct from the SDLC-scaffold's `DEC-*` decisions which live under `decisions/` and govern the system itself.

```yaml
id: decision_<uuid>
type: decision
retention_class: derived_keep
created_at: iso8601
updated_at: iso8601
decision_id: kebab-name              # short descriptive name
scope: project | system | personal
status: active | deprecated | superseded
linked_projects: [project_<uuid>]
linked_episodes: [episode_<uuid>]
human_involvement: human-decided | ai-proposed/human-approved | ai-proposed/auto-accepted
```

#### `learning` — `<vault>/05_Learnings/<category>/<learning_id>.md`

Categories: `routing/`, `confidence/`, `corrections/`, `project-structure/`, `agent-behavior/`.

```yaml
id: learning_<uuid>
type: learning
retention_class: derived_keep
created_at: iso8601
updated_at: iso8601
learning_type: routing | confidence | correction | project_structure | agent_behavior
trigger_event_id: <event_uuid>
project_id: project_<uuid>
before: string
after: string
human_feedback: string               # optional
confidence_before: number
confidence_after: number
applies_to: [string]
```

Reconciliation reports go under `<vault>/05_Learnings/agent-behavior/reconciliation/<run-date>.md` (see `reconciliation` type).

#### `person` — `<vault>/02_People/<person_id>.md`

```yaml
id: person_<uuid>
type: person
retention_class: derived_keep
created_at: iso8601
updated_at: iso8601
display_name: string
subject_ref: string                  # the indexable key (matches events.subject_ref)
consent_status: active | revoked
linked_sources: [source_id]          # consent_sources rows owned by or referencing this person
linked_episodes: [episode_<uuid>]
linked_projects: [project_<uuid>]
```

`subject_ref` here must match the normalization used by `whatsorga-ingest` so RTBF cascades on a subject can find both the events and the person page.

#### `routing_rules` — `<vault>/01_Projects/<project_slug>/ROUTING_RULES.md`

```yaml
id: routing_rules_<project_uuid>
type: routing_rules
retention_class: derived_keep
created_at: iso8601
updated_at: iso8601
project_id: project_<uuid>
rule_set_version: int
derived_from: [learning_<uuid>]      # learnings that produced these rules
```

The page body contains the human-readable rules (e.g., "messages from sender X with topic Y route to project Z at confidence ≥0.8"). The structured shape is kept light because routing rules are read by humans and the agent's prompt-context layer, not parsed mechanically.

#### `reconciliation` — `<vault>/05_Learnings/agent-behavior/reconciliation/<YYYY-MM-DD>.md`

```yaml
id: reconciliation_<run_id>
type: reconciliation
retention_class: derived_keep
created_at: iso8601
updated_at: iso8601
run_date: iso8601
unmatched_mutations: int
gate_bypasses: int
orphan_audits: int
```

Generated by [`REQ-REL-audit-reconciliation`](../1-spec/requirements/REQ-REL-audit-reconciliation.md). Body lists affected event ids by category.

#### `system_doc` — `<vault>/00_System/<doc_slug>.md`

```yaml
id: system_<slug>
type: system_doc
retention_class: derived_keep
created_at: iso8601
updated_at: iso8601
title: string
```

Free-form pages defining the vault's own conventions: `ACCESS_POLICY.md`, `AGENT_CONTRACT.md`, `CONFIDENCE_POLICY.md`, `MEMORY_SCHEMA.md`, `ROUTING_POLICY.md`, `RETENTION_POLICY.md`.

#### `review_queue_item` — `<vault>/09_Inbox/review-queue/<review_id>.md`

(Per [`DEC-obsidian-as-review-ui`](../decisions/DEC-obsidian-as-review-ui.md).)

```yaml
id: review_<uuid>
type: review_queue_item
retention_class: derived_keep
created_at: iso8601
updated_at: iso8601
input_event_id: <event_uuid>
proposal_id: <uuid>                  # optional — review items can predate proposals
reason: confidence_mid_band | consent_ambiguous | classifier_review_required | manual_flag
proposed_dispositions:
  - reclassify_to_project: <project_uuid>
  - reclassify_as_non_project
  - drop
  - forward_to_actor: <actor_id>
proposed_at: iso8601
status: pending | disposed
disposed_at: iso8601                 # if disposed
disposed_by: actor_id                # if disposed
disposition: string                  # if disposed
```

Operators dispose via Obsidian command palette → watch script in `gbrain-bridge` → POST to `backlog-core` disposition endpoint.

#### `proposal_detail` — `<vault>/09_Inbox/proposals/<proposal_id>.md`

(Per [`DEC-obsidian-as-review-ui`](../decisions/DEC-obsidian-as-review-ui.md).)

```yaml
id: proposal_detail_<proposal_uuid>
type: proposal_detail
retention_class: derived_keep
created_at: iso8601
updated_at: iso8601
proposal_id: <uuid>
confidence: number
gate_band: low | mid | high
suppression_reason: confidence_low_band | consent_scope_missing | tool_not_whitelisted | auto_policy_disabled | subject_floor_breach | tooling_error_<id>
cited_pages: [page_id]
learnings_applied: [learning_<uuid>]
input_event_id: <event_uuid>
tool_id: backlog-core | gbrain-bridge | kanban-sync
status: pending_review | accepted | edited_and_accepted | rejected | suppressed
disposed_at: iso8601                 # if disposed
disposed_by: actor_id                # if disposed
```

Satisfies `REQ-F-decision-inspection` — opening this page in Obsidian shows the full proposal context. Suppressed proposals appear here with `status: suppressed` and a non-null `suppression_reason`.

### Bidirectional links

Per [`REQ-F-bidirectional-links`](../1-spec/requirements/REQ-F-bidirectional-links.md): every `linked_*` array on one page has a back-link on the referenced page (e.g., `project.linked_episodes[]` corresponds to `episode.projects[]`). `gbrain-memory-write` updates both ends atomically; half-link writes are rejected.

`unidirectional_ok: true` may appear on certain frontmatter fields where the link is intentionally one-directional (e.g., a `system_doc` page citing a project for context — the project does not need a back-link). Such cases are declared in the schema, and the audit sweep ignores them.

### Raw envelope pages (rare)

`retention_class = raw_30d` pages are allowed only as separate, linked pages from a `derived_keep` page (e.g., a transcript snippet linked from an episode summary). They follow the same common-frontmatter rules but are subject to vault-side retention sweep at 30 days.

The redaction-precondition check ([`REQ-SEC-redaction-precondition`](../1-spec/requirements/REQ-SEC-redaction-precondition.md)) enforces that no `derived_keep` page contains raw-content markers; a separate `raw_30d` envelope is the only legitimate way for raw content to appear in the vault.

---

## Kanban card schema

Kanban boards live under `<vault>/Kanban/` (per the namespacing decision in [`architecture.md`](architecture.md)). Each board is a markdown file with the [Obsidian Kanban](https://github.com/mgmeyers/obsidian-kanban) plugin's column / card structure. Cards carry frontmatter that distinguishes sync-owned fields from user-owned fields per [`REQ-USA-kanban-obsidian-fidelity`](../1-spec/requirements/REQ-USA-kanban-obsidian-fidelity.md).

### Sync-owned fields

`kanban-sync` writes and updates these. The set is **declared as schema** with a version tag — adding a field is a deliberate change.

```yaml
_sync_schema_version: 1
proposal_id: uuid
extraction_confidence: number
source_input_event_id: uuid
artifact_type: task | proposal | decision_candidate | risk | open_question
cited_pages: [page_id]
learnings_applied: [learning_<uuid>]
created_by_proposal_at: iso8601
last_synced_at: iso8601
duplicate_of: <card_id>              # set if confirmed duplicate
status: open | closed
```

### User-owned fields

Anything **not** in the sync-owned set is treated as user-owned. `kanban-sync` preserves these fields unchanged across sync. Examples (not exhaustive — operators may add anything):

- `note`, `priority`, `due_date`, `tags`, `follow_up`, custom labels.

### Sync-vs-edit boundary detection

On each `kanban-sync` run:

1. Compute the snapshot of sync-owned fields for each card based on the last-applied proposal.
2. Compare to the card's current frontmatter.
3. Branch:
   - **Sync-owned field changed by human** → emit `unattributed_edit` event; write a `review_queue_item` page for the operator to formally accept / edit / reject.
   - **Non-sync-owned field added or changed** → preserve unchanged on next sync.
   - **Card moved between columns by human** → emit `kanban.user_edit` event; the move is preserved (operator wins per `CON-human-correction-priority`); operator can later acknowledge via `kanban.user_edit_acknowledged`.
4. Persist the new sync-snapshot for the next run.

The sync-owned field set version (`_sync_schema_version`) lets `kanban-sync` migrate cards forward when the sync-owned set changes — a card with version 1 can be migrated to version 2 on next sync, with the migration recorded as an audit event.

---

## Storage and retention summary

| Layer | Owner | Retention enforcement |
|---|---|---|
| `events` table | `backlog-core` | retention sweep at 30d for `raw_30d` rows; redaction preserves chain |
| `consent_sources` / `consent_history` | `backlog-core` | `audit_kept` semantics; immutable history; RTBF redacts content fields |
| GBrain pages | `gbrain-bridge` | `derived_keep` (default) survives indefinitely subject to RTBF; `raw_30d` envelopes swept at 30d |
| Kanban cards | `kanban-sync` | tied to source `derived_keep` artifacts; cleaned up on RTBF cascade |
| Ollama model storage | sidecar | not subject to retention; model artifacts only |

## Constraint compliance (data-model-specific)

| Constraint | Data-model element |
|---|---|
| `CON-tiered-retention` | `retention_class` on every event row + every GBrain page; sweep targets `raw_30d` |
| `CON-gbrain-no-raw-private-truth` | `gbrain-bridge` rejects `derived_keep` pages with raw-content markers; raw_30d envelopes allowed only as separate linked pages |
| `CON-no-direct-agent-writes` | `proposal_id` is required on every agent-emitted event; persistence services reject mutations without it |
| `CON-confidence-gated-autonomy` | `audit.gate_decision` event records every gate evaluation with full inputs |
| `CON-gdpr-applies` | `subject_ref` indexed; `consent_history` immutable; export tool joins cross-table |
| `CON-consent-required` | `consent_check_result` recorded on every `input_event` payload |
| `CON-human-correction-priority` | `learning_event` payload required on every `proposal.disposition`; preserved as both an event and a GBrain page |

## Approved-requirement coverage (data-model-specific)

| Requirement | Data-model element |
|---|---|
| `REQ-F-source-registration` | `consent_sources` insert + `consent_history` first-version row |
| `REQ-F-consent-revocation` | `consent_history` append + `consent_sources.current_state = 'revoked'`; in-flight events read `current_state` at consent-check time |
| `REQ-F-retention-sweep` | partition-aware sweep over `events WHERE retention_class = 'raw_30d' AND created_at < now() - 30d` |
| `REQ-COMP-consent-record` | `consent_sources` + `consent_history` schema; `lawful_basis` CHECK constraint; read-as-of query |
| `REQ-COMP-rtbf` | `subject_index` mat-view; redaction mechanic on `events`; per-layer cascade events |
| `REQ-COMP-data-export` | export tool joins `consent_history` + events filtered by `subject_index` |
| `REQ-COMP-purpose-limitation` | `consent_scope` JSONB read at every persistence-service boundary |
| `REQ-SEC-audit-log` | hash chain over `payload_hash`; verification routine; tombstone via redaction columns |
| `REQ-SEC-redaction-precondition` | `gbrain-bridge` validates before insert; raw-content markers detected by content scanner |
| `REQ-SEC-remote-inference-audit` | `remote_inference.called` event with full required fields |

## Dependency on `ASM-derived-artifacts-gdpr-permissible`

(Per [`DEC-gdpr-legal-review-deferred`](../decisions/DEC-gdpr-legal-review-deferred.md), required fallback note for design content depending on this assumption.)

**Where the data model depends on the assumption:**

- GBrain pages default to `retention_class = derived_keep` with indefinite retention.
- `consent_scope` JSONB does **not** include a `derivative_retention_consent` flag at MVP.
- The RTBF cascade redacts derivatives but does not time-bound them.

**Fallback if invalidated:**

- Add `derivative_retention_consent` (boolean, default `false`) to `consent_scope` JSONB. Forward-compatible: existing sources read `false` for the new key until an operator explicitly grants it through a `consent_updated` event.
- Add `derivative_retention_expires_at` (TIMESTAMPTZ, nullable) to GBrain `derived_keep` page schemas. If non-null, `gbrain-bridge`'s sweep deletes the page at the timestamp.
- Migrate existing pages: set `derivative_retention_expires_at = (source's raw envelope swept_at) + interval '90 days'` for derivatives whose source's `consent_scope.derivative_retention_consent = false`.
- Add `gbrain.derivative_swept` event type (default `audit_kept`).
- No structural change to the `events` table, the hash-chain mechanic, the `consent_history` immutability, or the `subject_index` view. The migration is purely additive.

The schema's append-only consent history + JSONB-extensible `consent_scope` are the structural properties that make this migration cheap. Both are required by `REQ-COMP-consent-record` independently of this assumption.

## Decisions referenced by this data model

- [`DEC-postgres-as-event-store`](../decisions/DEC-postgres-as-event-store.md)
- [`DEC-hash-chain-over-payload-hash`](../decisions/DEC-hash-chain-over-payload-hash.md)
- [`DEC-direct-http-between-services`](../decisions/DEC-direct-http-between-services.md)
- [`DEC-obsidian-as-review-ui`](../decisions/DEC-obsidian-as-review-ui.md)
- [`DEC-gdpr-legal-review-deferred`](../decisions/DEC-gdpr-legal-review-deferred.md)
