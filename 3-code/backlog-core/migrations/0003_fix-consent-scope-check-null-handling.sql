-- 0003_fix-consent-scope-check-null-handling.sql
--
-- Some databases may already have an older 0002_create-consent-tables
-- constraint definition that allowed UNKNOWN CHECK results for JSONB scopes
-- omitting required MVP flags, because it used bare `?` predicates and
-- `jsonb_typeof(...) = 'boolean'` comparisons without `... IS TRUE` guards.
-- This migration adds the replacement constraints as NOT VALID so databases
-- that already contain rows admitted by the old bug can still apply 0003.
-- PostgreSQL enforces NOT VALID CHECK constraints for new/updated rows, while
-- leaving existing violations for an explicit cleanup/VALIDATE CONSTRAINT path.

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
    ) NOT VALID;

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
    ) NOT VALID;
