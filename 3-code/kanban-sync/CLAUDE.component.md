# kanban-sync

**Responsibility**: Obsidian Kanban markdown file I/O. Maintains the **sync-owned vs. user-owned** card-frontmatter boundary per `REQ-USA-kanban-obsidian-fidelity`; detects manual column moves and unattributed edits and emits the corresponding events to `backlog-core`.

**Technology**: Python 3.12 + FastAPI per [`DEC-backend-stack-python-fastapi`](../../decisions/DEC-backend-stack-python-fastapi.md). Uniform across all five backend components.

## Interfaces

- **HTTP inbound**:
  - `POST /v1/cards` / `GET /v1/cards/:id` / `PATCH /v1/cards/:id` / `DELETE /v1/cards/:id` — from `hermes-runtime` (proposal pipeline) and `backlog-core` (cascade).
  - `DELETE /v1/cards?subject_ref=...&rtbf_run_id=...` — RTBF cascade fan-out from `backlog-core`.
  - `POST /v1/sync` — sync trigger from `backlog-core` (scheduled) or operator CLI.
  - `GET /v1/boards/:project_id` — board snapshot read.
  - `GET /v1/health`.
- **HTTP outbound** to `backlog-core`:
  - `kanban.card_mutated` events for every applied proposal.
  - `kanban.user_edit` events for human-initiated column moves and sync-field edits.
  - `unattributed_edit` events for human edits to sync-owned fields (routed to the review queue for formal disposition).
- **Filesystem** (mounted volume): read/write under `<vault>/Kanban/` only. Reads under `<vault>/` are read-only (for project-page link resolution).

## Requirements Addressed

| File | Type | Priority | Summary |
|------|------|----------|---------|
| [REQ-USA-kanban-obsidian-fidelity](../../1-spec/requirements/REQ-USA-kanban-obsidian-fidelity.md) | Usability | Must-have | Boards open in stock Obsidian without parse errors; sync only touches declared sync-owned fields; human edits to non-sync fields preserved; manual column moves detected |
| [REQ-COMP-rtbf](../../1-spec/requirements/REQ-COMP-rtbf.md) | Compliance | Must-have | RTBF cascade endpoint — bulk delete cards by `subject_ref` |
| [REQ-COMP-purpose-limitation](../../1-spec/requirements/REQ-COMP-purpose-limitation.md) | Compliance | Must-have | Component-declared purposes checked at every endpoint |

## Relevant Decisions

| File | Title | Trigger |
|------|-------|---------|
| [DEC-backend-stack-python-fastapi](../../decisions/DEC-backend-stack-python-fastapi.md) | Python 3.12 + FastAPI as the uniform backend stack | Any task that creates or modifies source code, build configuration, or test infrastructure inside this component |
| [DEC-shared-utility-path-deps](../../decisions/DEC-shared-utility-path-deps.md) | Cross-component shared utilities live in `3-code/_common/<package>/` and are consumed via uv path-deps | Any task that adds or modifies a dependency on a `_common/<package>` helper, the Dockerfile, or this component's `build:` block in `docker-compose.yml` |
| [DEC-direct-http-between-services](../../decisions/DEC-direct-http-between-services.md) | Synchronous HTTP/REST between services at MVP | Inter-service call patterns |
| [DEC-api-versioning](../../decisions/DEC-api-versioning.md) | URL-path versioning (`/v1/...`) | Every endpoint route |
| [DEC-service-auth-bearer-tokens](../../decisions/DEC-service-auth-bearer-tokens.md) | Per-service bearer tokens with declared purposes | Authentication on every endpoint; purpose-limitation enforcement |
| [DEC-idempotency-keys](../../decisions/DEC-idempotency-keys.md) | `Idempotency-Key` header on mutations | Every mutation endpoint |
| [DEC-cursor-pagination-and-event-stream-conventions](../../decisions/DEC-cursor-pagination-and-event-stream-conventions.md) | Cursor pagination + long-poll/SSE event-stream | List endpoints exposed by this component (`GET /v1/cards`, `GET /v1/boards`, `GET /v1/boards/:project_id`); kanban-sync does not stream events directly |
| [DEC-obsidian-as-review-ui](../../decisions/DEC-obsidian-as-review-ui.md) | Review queue and proposal-detail views as GBrain pages disposed via Obsidian command palette | `unattributed_edit` events on Kanban cards feed the same review-queue surface |
