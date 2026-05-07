-- 0002_create-consent-tables.sql
--
-- Per `2-design/data-model.md` § `consent_sources` / `consent_history`:
-- backlog-core owns the current consent record and its immutable version
-- history. This migration creates the schema foundation for
-- `TASK-postgres-consent-schema`; endpoint and CLI tasks append events and
-- maintain these rows in later increments.
--
-- Per `REQ-COMP-consent-record`, the only MVP lawful basis is `consent`.
-- The consent scope stays JSONB-extensible for future GDPR fallback flags,
-- while CHECK constraints ensure all MVP purpose flags are explicit booleans.
--
-- Per `DEC-postgres-migration-tool`: forward-only migrations; this file is
-- immutable once shipped — corrections land as new numbered migrations.

-- ---------------------------------------------------------------------------
-- Shared immutable helper for consent-history append-only enforcement.
-- ---------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION reject_consent_history_mutation()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION 'consent_history is append-only; append a new version instead'
        USING ERRCODE = '55000';
END;
$$;

-- ---------------------------------------------------------------------------
-- Current consent state per source.
-- ---------------------------------------------------------------------------

CREATE TABLE consent_sources (
    source_id TEXT PRIMARY KEY,
    actor_id TEXT NOT NULL,
    lawful_basis TEXT NOT NULL DEFAULT 'consent',
    consent_scope JSONB NOT NULL DEFAULT '{
        "route_to_projects": false,
        "summarize": false,
        "extract_artifacts": false,
        "learning_signal": false,
        "remote_inference_allowed": false
    }'::jsonb,
    retention_policy TEXT NOT NULL,
    current_state TEXT NOT NULL DEFAULT 'active',
    granted_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    granted_by TEXT NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT consent_sources_lawful_basis_check CHECK (lawful_basis = 'consent'),
    CONSTRAINT consent_sources_retention_policy_check CHECK (retention_policy IN (
        'raw_30d',
        'derived_keep',
        'review_required'
    )),
    CONSTRAINT consent_sources_current_state_check CHECK (current_state IN (
        'active',
        'revoked'
    )),
    CONSTRAINT consent_sources_scope_is_object_check CHECK (
        jsonb_typeof(consent_scope) = 'object'
    ),
    CONSTRAINT consent_sources_scope_mvp_flags_check CHECK (
        jsonb_typeof(consent_scope -> 'route_to_projects') = 'boolean'
        AND jsonb_typeof(consent_scope -> 'summarize') = 'boolean'
        AND jsonb_typeof(consent_scope -> 'extract_artifacts') = 'boolean'
        AND jsonb_typeof(consent_scope -> 'learning_signal') = 'boolean'
        AND jsonb_typeof(consent_scope -> 'remote_inference_allowed') = 'boolean'
    )
);

CREATE INDEX consent_sources_actor_id_idx
    ON consent_sources (actor_id);

CREATE INDEX consent_sources_current_state_idx
    ON consent_sources (current_state);

-- ---------------------------------------------------------------------------
-- Append-only source consent history.
-- ---------------------------------------------------------------------------
--
-- `event_id` points to the corresponding source.* event by application
-- convention. The partitioned `events` table has a composite primary key
-- `(event_id, created_at)`, so a database FK on event_id alone is not
-- structurally possible without adding an extra event_created_at column that
-- is absent from the documented data model. The source endpoint validates
-- the event exists before inserting history in a later task.

CREATE TABLE consent_history (
    history_id UUID PRIMARY KEY,
    source_id TEXT NOT NULL REFERENCES consent_sources (source_id),
    changed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    prior_scope JSONB,
    new_scope JSONB NOT NULL,
    prior_retention TEXT,
    new_retention TEXT NOT NULL,
    prior_state TEXT,
    new_state TEXT NOT NULL,
    change_reason TEXT,
    event_id UUID NOT NULL,

    CONSTRAINT consent_history_new_scope_is_object_check CHECK (
        jsonb_typeof(new_scope) = 'object'
    ),
    CONSTRAINT consent_history_new_scope_mvp_flags_check CHECK (
        jsonb_typeof(new_scope -> 'route_to_projects') = 'boolean'
        AND jsonb_typeof(new_scope -> 'summarize') = 'boolean'
        AND jsonb_typeof(new_scope -> 'extract_artifacts') = 'boolean'
        AND jsonb_typeof(new_scope -> 'learning_signal') = 'boolean'
        AND jsonb_typeof(new_scope -> 'remote_inference_allowed') = 'boolean'
    ),
    CONSTRAINT consent_history_prior_scope_is_object_check CHECK (
        prior_scope IS NULL OR jsonb_typeof(prior_scope) = 'object'
    ),
    CONSTRAINT consent_history_retention_policy_check CHECK (
        (prior_retention IS NULL OR prior_retention IN (
            'raw_30d',
            'derived_keep',
            'review_required'
        ))
        AND new_retention IN (
            'raw_30d',
            'derived_keep',
            'review_required'
        )
    ),
    CONSTRAINT consent_history_state_check CHECK (
        (prior_state IS NULL OR prior_state IN ('active', 'revoked'))
        AND new_state IN ('active', 'revoked')
    ),
    CONSTRAINT consent_history_registration_shape_check CHECK (
        (prior_scope IS NULL AND prior_retention IS NULL AND prior_state IS NULL)
        OR
        (prior_scope IS NOT NULL AND prior_retention IS NOT NULL AND prior_state IS NOT NULL)
    )
);

CREATE INDEX consent_history_source_changed_at_idx
    ON consent_history (source_id, changed_at DESC);

CREATE INDEX consent_history_event_id_idx
    ON consent_history (event_id);

CREATE TRIGGER consent_history_reject_update
    BEFORE UPDATE ON consent_history
    FOR EACH ROW EXECUTE FUNCTION reject_consent_history_mutation();

CREATE TRIGGER consent_history_reject_delete
    BEFORE DELETE ON consent_history
    FOR EACH ROW EXECUTE FUNCTION reject_consent_history_mutation();

-- ---------------------------------------------------------------------------
-- Comments for operator-facing introspection.
-- ---------------------------------------------------------------------------

COMMENT ON TABLE consent_sources IS
    'Current consent state per registered ingestion source. lawful_basis is constrained to consent for the MVP.';

COMMENT ON TABLE consent_history IS
    'Append-only consent version history. Read-as-of uses (source_id, changed_at DESC). Updates/deletes are rejected; append a new row instead.';

COMMENT ON COLUMN consent_sources.consent_scope IS
    'JSONB purpose flags. MVP flags must be explicit booleans; future flags are additive and default to false at the application layer.';

COMMENT ON COLUMN consent_history.event_id IS
    'Corresponding source.registered/source.consent_updated/source.consent_revoked event_id, application-validated because events is partitioned by created_at.';
