# gbrain-bridge

**Responsibility**: GBrain vault read/write with schema validation per `REQ-F-gbrain-schema`, bidirectional link integrity per `REQ-F-bidirectional-links`, redaction-precondition check per `REQ-SEC-redaction-precondition`, and the weekly vault audit sweep per `REQ-MNT-vault-audit-sweep`. Also hosts the **Obsidian command-palette watch script** that translates operator dispositions into HTTP calls to `backlog-core` per [`DEC-obsidian-as-review-ui`](../../decisions/DEC-obsidian-as-review-ui.md).

**Technology**: Python 3.12 + FastAPI per [`DEC-backend-stack-python-fastapi`](../../decisions/DEC-backend-stack-python-fastapi.md). Uniform across all five backend components.

## Interfaces

- **HTTP inbound**:
  - `POST /v1/pages` / `GET /v1/pages/:id` / `PATCH /v1/pages/:id` / `DELETE /v1/pages/:id` — from `hermes-runtime` (proposal pipeline) and `backlog-core` (cascade).
  - `DELETE /v1/pages?subject_ref=...&rtbf_run_id=...` — RTBF cascade fan-out from `backlog-core`.
  - `POST /v1/audit-sweep` / `GET /v1/audit-sweep/runs` — from `backlog-core` (scheduled) or operator CLI.
  - `POST /v1/dispositions` — internal loopback endpoint used by the watch script.
  - `GET /v1/health`.
- **HTTP outbound** to `backlog-core`:
  - `POST /v1/proposals/:id/disposition` and `POST /v1/review/:id/dispose` — translated from Obsidian command-palette events.
  - Audit events (e.g., `gbrain.page_mutated`, `gbrain.audit_swept`).
- **Filesystem** (mounted volume): read/write under `<vault>/`, **excluding** `<vault>/Kanban/` (owned by `kanban-sync`).
- **File-system watch**: monitors Obsidian command-palette command pages for operator dispositions.

## Bundled assets

- `obsidian-bindings/` — small repo-shipped configuration files operators import into their vault to enable command-palette commands (`Vision: Accept proposal`, `Vision: Reject with reason`, etc.). Per [`DEC-obsidian-as-review-ui`](../../decisions/DEC-obsidian-as-review-ui.md), no separate frontend service.

## Requirements Addressed

| File | Type | Priority | Summary |
|------|------|----------|---------|
| [REQ-F-gbrain-schema](../../1-spec/requirements/REQ-F-gbrain-schema.md) | Functional | Must-have | Every GBrain page validates against type-specific frontmatter at write time |
| [REQ-F-bidirectional-links](../../1-spec/requirements/REQ-F-bidirectional-links.md) | Functional | Must-have | Forward + back links atomic; half-link writes rejected; deletes propagate symmetrically |
| [REQ-MNT-vault-audit-sweep](../../1-spec/requirements/REQ-MNT-vault-audit-sweep.md) | Maintainability | Must-have | Weekly vault audit: ≥99% schema conformance, 0 half-links, 0 raw-content leaks in `derived_keep` |
| [REQ-SEC-redaction-precondition](../../1-spec/requirements/REQ-SEC-redaction-precondition.md) | Security | Must-have | Persistence-service writes to `derived_keep` reject payloads containing raw-content markers |
| [REQ-COMP-rtbf](../../1-spec/requirements/REQ-COMP-rtbf.md) | Compliance | Must-have | RTBF cascade endpoint — bulk delete by `subject_ref`; bidirectional link cleanup atomic |
| [REQ-COMP-purpose-limitation](../../1-spec/requirements/REQ-COMP-purpose-limitation.md) | Compliance | Must-have | Component-declared purposes checked at every endpoint |

## Relevant Decisions

| File | Title | Trigger |
|------|-------|---------|
| [DEC-backend-stack-python-fastapi](../../decisions/DEC-backend-stack-python-fastapi.md) | Python 3.12 + FastAPI as the uniform backend stack | Any task that creates or modifies source code, build configuration, or test infrastructure inside this component |
| [DEC-shared-utility-path-deps](../../decisions/DEC-shared-utility-path-deps.md) | Cross-component shared utilities live in `3-code/_common/<package>/` and are consumed via uv path-deps | Any task that adds or modifies a dependency on a `_common/<package>` helper, the Dockerfile, or this component's `build:` block in `docker-compose.yml` |
| [DEC-obsidian-as-review-ui](../../decisions/DEC-obsidian-as-review-ui.md) | Review queue and proposal-detail views as GBrain pages disposed via Obsidian command palette | Watch-script implementation; `obsidian-bindings/` asset bundle |
| [DEC-direct-http-between-services](../../decisions/DEC-direct-http-between-services.md) | Synchronous HTTP/REST between services at MVP | Inter-service call patterns |
| [DEC-api-versioning](../../decisions/DEC-api-versioning.md) | URL-path versioning (`/v1/...`) | Every endpoint route |
| [DEC-service-auth-bearer-tokens](../../decisions/DEC-service-auth-bearer-tokens.md) | Per-service bearer tokens with declared purposes | Authentication on every endpoint; purpose-limitation enforcement |
| [DEC-idempotency-keys](../../decisions/DEC-idempotency-keys.md) | `Idempotency-Key` header on mutations | Every mutation endpoint |
| [DEC-cursor-pagination-and-event-stream-conventions](../../decisions/DEC-cursor-pagination-and-event-stream-conventions.md) | Cursor pagination + long-poll/SSE event-stream | Any list endpoint exposed by this component (e.g., `GET /v1/audit-sweep/runs`); the watch script does not stream events |
| [DEC-gdpr-legal-review-deferred](../../decisions/DEC-gdpr-legal-review-deferred.md) | GDPR legal review deferred to Code phase | Any change to GBrain page schemas, retention semantics, or RTBF cascade behavior must include the fallback-if-invalidated note |
