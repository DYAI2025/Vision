-- 0001_create-events-table.sql
--
-- Per `2-design/data-model.md` § "Postgres schema (`backlog-core`)":
-- the canonical append-only log. Every event in the system — input arrivals,
-- routing decisions, proposals, dispositions, audit records, retention
-- sweeps, RTBF cascades, etc. — is a row in this table.
--
-- Per `DEC-postgres-as-event-store`: append-only by application convention;
-- redaction modifies only `payload` / `redacted` / `redaction_run_id` /
-- `redacted_at`; everything else stays immutable.
--
-- Per `DEC-hash-chain-over-payload-hash`: the chain hashes a stable
-- `payload_hash` digest computed once at insert. Redaction never touches
-- `payload_hash`, so chain verification still passes after redaction.
--
-- Per `DEC-postgres-migration-tool`: forward-only migrations; this file is
-- immutable once shipped — corrections land as new numbered migrations.

-- ---------------------------------------------------------------------------
-- Parent partitioned table.
-- ---------------------------------------------------------------------------
--
-- Range-partitioned on `created_at` (monthly partitions per `data-model.md`
-- § "Partitioning"). PostgreSQL's declarative partitioning requires the
-- partition key to participate in any UNIQUE / PRIMARY KEY constraint, so
-- the PK is `(event_id, created_at)`. The data-model declares `event_id` as
-- the conceptual identity; tests assert `event_id` is unique within the
-- table by way of the composite PK (no two rows can share an event_id at
-- the same created_at, and event_id alone is unique by application
-- convention — no PK on event_id alone is structurally possible under
-- partitioning).
--
-- The CHECK constraint on `event_type` enforces the closed enum from
-- `data-model.md` § "Event-type catalog". Adding a new event type requires
-- a new forward migration that ALTER-TABLEs the constraint.
--
-- The CHECK constraint on `retention_class` enforces the three-class
-- vocabulary from `data-model.md` § "Storage and retention summary":
-- `audit_kept` / `raw_30d` / `derived_keep`.
--
-- The `source_input_event_id` column is described in `data-model.md` as
-- "FK to this same table". Under partitioning, a self-referencing FK
-- requires the FK to include the partition key, which would mean adding
-- a `source_input_event_created_at` column — a structural deviation from
-- the documented schema. We instead enforce the reference at the
-- application layer (the event-emit code path validates that the parent
-- event exists). This is recorded as a minor design clarification in the
-- task closeout for `TASK-postgres-events-schema`.
CREATE TABLE events (
    event_id UUID NOT NULL,
    event_type TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    actor_id TEXT NOT NULL,
    proposal_id UUID,
    source_input_event_id UUID,
    subject_ref TEXT,
    payload JSONB,
    payload_hash BYTEA NOT NULL,
    prev_hash BYTEA NOT NULL,
    hash BYTEA NOT NULL,
    retention_class TEXT NOT NULL,
    redacted BOOLEAN NOT NULL DEFAULT FALSE,
    redaction_run_id UUID,
    redacted_at TIMESTAMPTZ,

    PRIMARY KEY (event_id, created_at),

    CONSTRAINT events_event_type_check CHECK (event_type IN (
        'input.received',
        'routing.decided',
        'proposal.proposed',
        'proposal.applied',
        'proposal.rejected',
        'proposal.disposition',
        'learning.recorded',
        'source.registered',
        'source.consent_updated',
        'source.consent_revoked',
        'retention.deleted',
        'rtbf.run_started',
        'rtbf.cascade_completed',
        'rtbf.verification_passed',
        'remote_inference.called',
        'audit.gate_decision',
        'gbrain.page_mutated',
        'kanban.card_mutated',
        'kanban.user_edit',
        'unattributed_edit',
        'secret.rotated',
        'duplicate.detected',
        'review.disposed',
        'processing.stuck',
        'extraction.empty',
        'learning_gap.brain_first_discipline',
        'subject.export_produced',
        'kanban.user_edit_acknowledged'
    )),

    CONSTRAINT events_retention_class_check CHECK (retention_class IN (
        'audit_kept',
        'raw_30d',
        'derived_keep'
    )),

    -- Redaction columns must be consistent: redacted=TRUE iff
    -- redaction_run_id and redacted_at are set; redacted=FALSE iff both
    -- are NULL. Catches mis-redaction at the persistence boundary.
    CONSTRAINT events_redaction_consistency_check CHECK (
        (redacted = FALSE
         AND redaction_run_id IS NULL
         AND redacted_at IS NULL)
        OR
        (redacted = TRUE
         AND redaction_run_id IS NOT NULL
         AND redacted_at IS NOT NULL)
    )
) PARTITION BY RANGE (created_at);

-- ---------------------------------------------------------------------------
-- Indexes per `data-model.md` § "Indexes".
-- ---------------------------------------------------------------------------
--
-- Indexes on a partitioned parent are CREATE-INDEX-ed once and propagated
-- automatically to every partition. The `(retention_class, created_at)`
-- index is partial WHERE redacted = FALSE — only unredacted rows are sweep
-- candidates, so the partial form keeps the index small.

CREATE INDEX events_subject_ref_created_at_idx
    ON events (subject_ref, created_at);

CREATE INDEX events_proposal_id_idx
    ON events (proposal_id);

CREATE INDEX events_event_type_created_at_idx
    ON events (event_type, created_at);

CREATE INDEX events_retention_sweep_idx
    ON events (retention_class, created_at)
    WHERE redacted = FALSE;

CREATE INDEX events_source_input_event_id_idx
    ON events (source_input_event_id);

-- ---------------------------------------------------------------------------
-- Initial 12 months of partitions: May 2026 through April 2027 inclusive.
-- This gives `TASK-postgres-events-partitioning` (Phase 2 #5) a year-long
-- window to land its rolling-future cron without any insert ever failing
-- with "no partition for given key". The cron's job at that point is
-- maintenance — pre-creating month N+12 each month — not establishing
-- partitioning.
-- ---------------------------------------------------------------------------
--
-- `TASK-postgres-events-partitioning` (Phase 2 #5) installs the
-- partition-creation cron that maintains the rolling-future partitions
-- after this. Until that cron lands, manual `CREATE TABLE ... PARTITION OF
-- events FOR VALUES FROM ('YYYY-MM-01') TO ('YYYY-MM-01')` covers gaps;
-- inserts that fall outside any defined partition raise `23P02` (no
-- partition for the given key), which is the right behavior — visible
-- failure rather than silent data loss.

CREATE TABLE events_2026_05 PARTITION OF events
    FOR VALUES FROM ('2026-05-01 00:00:00+00') TO ('2026-06-01 00:00:00+00');

CREATE TABLE events_2026_06 PARTITION OF events
    FOR VALUES FROM ('2026-06-01 00:00:00+00') TO ('2026-07-01 00:00:00+00');

CREATE TABLE events_2026_07 PARTITION OF events
    FOR VALUES FROM ('2026-07-01 00:00:00+00') TO ('2026-08-01 00:00:00+00');

CREATE TABLE events_2026_08 PARTITION OF events
    FOR VALUES FROM ('2026-08-01 00:00:00+00') TO ('2026-09-01 00:00:00+00');

CREATE TABLE events_2026_09 PARTITION OF events
    FOR VALUES FROM ('2026-09-01 00:00:00+00') TO ('2026-10-01 00:00:00+00');

CREATE TABLE events_2026_10 PARTITION OF events
    FOR VALUES FROM ('2026-10-01 00:00:00+00') TO ('2026-11-01 00:00:00+00');

CREATE TABLE events_2026_11 PARTITION OF events
    FOR VALUES FROM ('2026-11-01 00:00:00+00') TO ('2026-12-01 00:00:00+00');

CREATE TABLE events_2026_12 PARTITION OF events
    FOR VALUES FROM ('2026-12-01 00:00:00+00') TO ('2027-01-01 00:00:00+00');

CREATE TABLE events_2027_01 PARTITION OF events
    FOR VALUES FROM ('2027-01-01 00:00:00+00') TO ('2027-02-01 00:00:00+00');

CREATE TABLE events_2027_02 PARTITION OF events
    FOR VALUES FROM ('2027-02-01 00:00:00+00') TO ('2027-03-01 00:00:00+00');

CREATE TABLE events_2027_03 PARTITION OF events
    FOR VALUES FROM ('2027-03-01 00:00:00+00') TO ('2027-04-01 00:00:00+00');

CREATE TABLE events_2027_04 PARTITION OF events
    FOR VALUES FROM ('2027-04-01 00:00:00+00') TO ('2027-05-01 00:00:00+00');

-- ---------------------------------------------------------------------------
-- Comments for operator-facing introspection.
-- ---------------------------------------------------------------------------

COMMENT ON TABLE events IS
    'Append-only event log. Per DEC-postgres-as-event-store: no DELETE / UPDATE on rows except RTBF / retention redaction (which only touches payload / redacted / redaction_run_id / redacted_at).';

COMMENT ON COLUMN events.payload_hash IS
    'SHA-256(canonical_json(payload)) computed once at INSERT. Never modified, even on redaction. Per DEC-hash-chain-over-payload-hash.';

COMMENT ON COLUMN events.prev_hash IS
    'events.hash of the immediately preceding event in chain order. Application maintains the chain on INSERT.';

COMMENT ON COLUMN events.hash IS
    'SHA-256(event_id || event_type || created_at || actor_id || payload_hash || prev_hash). Chain math reads this and prev_hash; redaction does not change it.';

COMMENT ON COLUMN events.source_input_event_id IS
    'Originating input.received event_id. Application-validated reference (no DB-level FK due to partitioning self-reference complexity).';
