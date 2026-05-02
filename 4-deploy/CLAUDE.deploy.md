Phase-specific instructions for the **Deploy** phase. Extends [../CLAUDE.md](../CLAUDE.md).

## Purpose

This phase handles **deployment and operations**. Focus on reliability, repeatability, and observability.

---

## Decisions Relevant to This Phase

| File | Title | Trigger |
|------|-------|---------|
| [DEC-gdpr-legal-review-deferred](../decisions/DEC-gdpr-legal-review-deferred.md) | GDPR legal review deferred from Spec → Design gate to Code phase | Any production / non-development deploy — operator must confirm `ASM-derived-artifacts-gdpr-permissible.Status == Verified` before proceeding; production deploy is blocked under the deferred state |
| [DEC-postgres-as-event-store](../decisions/DEC-postgres-as-event-store.md) | Postgres is the event store for `backlog-core` | Production deployment includes Postgres as a Compose service; `backup.sh` / `restore.sh` target Postgres-formatted archives; smoke test exercises a backup → restore round-trip |
| [DEC-postgres-migration-tool](../decisions/DEC-postgres-migration-tool.md) | yoyo-migrations is the schema migration tool | Install runbook runs `python -m app.migrations apply` after `docker compose up` and before the smoke test; restore runbook reapplies migrations after restore in case the backup-source DB was on an older migration generation |
<!-- Add rows as decisions are recorded. File column: [DEC-kebab-name](../decisions/DEC-kebab-name.md) -->

---

## AI Guidelines

### Infrastructure as Code

1. Check `2-design/` for architecture design docs.
2. Apply all decisions from the index above whose trigger conditions match.
3. Write declarative, idempotent configurations.
4. Document resource dependencies in comments or in `infrastructure/README.md`.
5. Flag non-obvious cost drivers to the user.
6. Never hardcode secrets — use environment variables or a secret manager.

### Deployment Scripts

1. Make every script idempotent.
2. Exit on failure, log the failed step, emit a clear error message.
3. Provide a rollback path or document why one is not possible.

### Runbooks

1. Use the [runbook template](runbooks/_template.md).
2. Reference specific deployment scripts and infrastructure resources.
3. Link back to requirements where relevant (e.g., availability targets from REQ-REL).
4. Cross-check procedures against actual scripts and infrastructure.
5. Keep procedures short — move detailed background into a separate document if needed.

### Common Decision Triggers
When a significant decision emerges, follow [CLAUDE.md — Decisions](../CLAUDE.md#when-recording-decisions). Common triggers: secret management, environment promotion rules, rollback procedures, IaC tooling, CI/CD conventions.

---

## Linking to Other Phases

- Infrastructure design comes from `2-design/`
- Deploys build artifacts from `3-code/`
- Operational requirements come from `1-spec/`
