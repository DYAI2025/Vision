# cli

**Responsibility**: The operator `vision` binary — covers source registration / consent management, RTBF cascade, data-subject export, review-queue CLI fallback, audit query, state-reconstruction preview, backup / restore, secret rotation, VPS install + smoke test, and aggregated health status across the stack. Per `architecture.md` and [`DEC-obsidian-as-review-ui`](../../decisions/DEC-obsidian-as-review-ui.md), the CLI is the surface for transactional / high-stakes operations; routine review actions go through Obsidian's command palette instead.

**Technology**: Python 3.12 + Typer per [`DEC-cli-stack-python-typer`](../../decisions/DEC-cli-stack-python-typer.md). Distributed primarily via `uv tool install`; secondary distribution mode is a profile-gated `cli` service in `docker-compose.yml` for in-stack invocation.

## Interfaces

- **HTTP outbound** to `backlog-core` (most commands):
  - `POST /v1/sources` / `PATCH /v1/sources/:id` / `POST /v1/sources/:id/revoke` / `GET /v1/sources` / `GET /v1/sources/:id/history`.
  - `POST /v1/rtbf` + `GET /v1/rtbf/:run_id`.
  - `POST /v1/exports` + `GET /v1/exports/:export_id`.
  - `GET /v1/review/queue` / `GET /v1/review/:id` / `POST /v1/review/:id/dispose`.
  - `GET /v1/audit/query` / `POST /v1/audit/verify-chain`.
  - `POST /v1/state/reconstruct`.
  - `POST /v1/reconciliation/run`.
- **HTTP outbound** to `gbrain-bridge` and `kanban-sync` (read-only): health checks and ad-hoc inspection.
- **Filesystem**: reads `.env` for token discovery and host configuration; writes backup archives produced by `backup.sh` / consumed by `restore.sh` when those scripts are wrapped in CLI commands.
- **Operator's terminal**: stdout/stderr; structured JSON via `--json`. Exit codes documented per command.

## Requirements Addressed

| File | Type | Priority | Summary |
|------|------|----------|---------|
| [REQ-F-source-registration](../../1-spec/requirements/REQ-F-source-registration.md) | Functional | Must-have | Operator UX for `vision source register / update` |
| [REQ-F-consent-revocation](../../1-spec/requirements/REQ-F-consent-revocation.md) | Functional | Must-have | Operator UX for `vision source revoke` |
| [REQ-COMP-rtbf](../../1-spec/requirements/REQ-COMP-rtbf.md) | Compliance | Must-have | Operator surface for `vision rtbf <subject>` |
| [REQ-COMP-data-export](../../1-spec/requirements/REQ-COMP-data-export.md) | Compliance | Must-have | Operator surface for `vision export <subject>` |
| [REQ-PORT-vps-deploy](../../1-spec/requirements/REQ-PORT-vps-deploy.md) | Portability | Should-have | `vision install` and `vision smoke-test` wrap `install_vps.sh` and `smoke_test.sh` |
| [REQ-MNT-env-driven-config](../../1-spec/requirements/REQ-MNT-env-driven-config.md) | Maintainability | Should-have | Reads `.env` at startup; structured error on missing required keys |
| [REQ-REL-backup-restore-fidelity](../../1-spec/requirements/REQ-REL-backup-restore-fidelity.md) | Reliability | Should-have | `vision backup` / `vision restore` surface; restore runs chain verification end-to-end before resuming writes |
| [REQ-REL-secret-rotation](../../1-spec/requirements/REQ-REL-secret-rotation.md) | Reliability | Should-have | `vision rotate <secret-category>` follows the rotation runbook; re-runs smoke test against rotated credentials |

## Relevant Decisions

| File | Title | Trigger |
|------|-------|---------|
| [DEC-cli-stack-python-typer](../../decisions/DEC-cli-stack-python-typer.md) | Python 3.12 + Typer for the operator CLI | Any task that creates or modifies source code, build configuration, or test infrastructure inside this component |
| [DEC-cursor-pagination-and-event-stream-conventions](../../decisions/DEC-cursor-pagination-and-event-stream-conventions.md) | Cursor pagination + long-poll/SSE event-stream | Any list command (`vision source list`, `vision audit query`, `vision review list`, `vision reconciliation runs`) — paginate to completion before printing OR stream pages to stdout under `--stream` |
| [DEC-direct-http-between-services](../../decisions/DEC-direct-http-between-services.md) | Synchronous HTTP/REST between services at MVP | All HTTP client code |
| [DEC-api-versioning](../../decisions/DEC-api-versioning.md) | URL-path versioning (`/v1/...`) | All HTTP endpoint construction |
| [DEC-service-auth-bearer-tokens](../../decisions/DEC-service-auth-bearer-tokens.md) | Per-service bearer tokens with declared purposes | Operator-token handling; never log token values |
| [DEC-idempotency-keys](../../decisions/DEC-idempotency-keys.md) | `Idempotency-Key` header on mutations | CLI generates a per-invocation UUID for retry-safe operations (RTBF, export, source registration) |
