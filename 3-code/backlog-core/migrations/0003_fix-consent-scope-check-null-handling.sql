-- 0003_fix-consent-scope-check-null-handling.sql
--
-- 0002_create-consent-tables originally allowed UNKNOWN CHECK results for
-- JSONB scopes that omitted required MVP flags because bare `?` predicates and
-- `jsonb_typeof(...) = 'boolean'` comparisons can evaluate to NULL/UNKNOWN.
-- Replacing the constraints in a forward migration ensures databases that have
-- already applied 0002 receive the corrected validation; yoyo never re-runs an
-- applied migration.

ALTER TABLE consent_sources
    DROP CONSTRAINT IF EXISTS consent_sources_scope_mvp_flags_check,
    ADD CONSTRAINT consent_sources_scope_mvp_flags_check CHECK (
        (consent_scope ? 'route_to_projects') IS TRUE
        AND (consent_scope ? 'summarize') IS TRUE
        AND (consent_scope ? 'extract_artifacts') IS TRUE
        AND (consent_scope ? 'learning_signal') IS TRUE
        AND (consent_scope ? 'remote_inference_allowed') IS TRUE
        AND (jsonb_typeof(consent_scope -> 'route_to_projects') = 'boolean') IS TRUE
        AND (jsonb_typeof(consent_scope -> 'summarize') = 'boolean') IS TRUE
        AND (jsonb_typeof(consent_scope -> 'extract_artifacts') = 'boolean') IS TRUE
        AND (jsonb_typeof(consent_scope -> 'learning_signal') = 'boolean') IS TRUE
        AND (jsonb_typeof(consent_scope -> 'remote_inference_allowed') = 'boolean') IS TRUE
    );

ALTER TABLE consent_history
    DROP CONSTRAINT IF EXISTS consent_history_new_scope_mvp_flags_check,
    ADD CONSTRAINT consent_history_new_scope_mvp_flags_check CHECK (
        (new_scope ? 'route_to_projects') IS TRUE
        AND (new_scope ? 'summarize') IS TRUE
        AND (new_scope ? 'extract_artifacts') IS TRUE
        AND (new_scope ? 'learning_signal') IS TRUE
        AND (new_scope ? 'remote_inference_allowed') IS TRUE
        AND (jsonb_typeof(new_scope -> 'route_to_projects') = 'boolean') IS TRUE
        AND (jsonb_typeof(new_scope -> 'summarize') = 'boolean') IS TRUE
        AND (jsonb_typeof(new_scope -> 'extract_artifacts') = 'boolean') IS TRUE
        AND (jsonb_typeof(new_scope -> 'learning_signal') = 'boolean') IS TRUE
        AND (jsonb_typeof(new_scope -> 'remote_inference_allowed') = 'boolean') IS TRUE
    );
