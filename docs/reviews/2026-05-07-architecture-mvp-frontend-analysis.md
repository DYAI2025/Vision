# Architecture, UI, backend service and MVP analysis — 2026-05-07

## Executive summary

The current repository is a strong deployment and service-boundary bootstrap, not yet an end-to-end semantic memory product. What works today is the operational shell: Docker Compose, Postgres and Ollama sidecars, Caddy/Tailscale ingress routes, per-service FastAPI health endpoints, service-token configuration, the CLI health aggregator, and vault/Kanban readiness probes. The core product loop is still open: ingesting communications, normalizing them with consent, semantically summarizing them, proposing Evermemos placement, reviewing proposals, and writing approved Markdown pages.

The MVP should therefore avoid broad channel coverage and focus on a single vertical path: manual communication intake → event persistence → local Hermes summary and placement proposal → review → GBrain/Evermemos Markdown write. The Railway frontend added in `3-code/frontend` is shaped around that vertical slice: it can be deployed independently, visualizes current backend readiness, and gives operators a usable manual semantic-intake preview while backend endpoints are completed.

## What currently works

### Deployment and service architecture

- The architecture is cleanly separated into five backend services plus Postgres, Ollama, ingress and the operator CLI.
- Docker Compose already wires service discovery through a single internal network and exposes only ingress-facing routes.
- Caddy has a route matrix for health, backlog-core, gbrain-bridge, kanban-sync and hermes-runtime paths.
- `.env.example` captures environment-driven configuration for ingress, Postgres, vault paths, Ollama model and bearer tokens.
- Healthcheck-only smoke testing is a realistic Phase-1 acceptance target because only readiness endpoints are implemented across most services.

### Backend services

- `backlog-core` has the strongest backend readiness because it checks a real asyncpg Postgres pool in `/v1/health`.
- `gbrain-bridge` verifies that the configured vault path is readable.
- `kanban-sync` verifies that the Kanban subtree exists and is writable.
- `whatsorga-ingest` and `hermes-runtime` expose basic health endpoints but do not yet exercise dependencies.
- The CLI can aggregate service health through ingress paths, which is also the most useful first capability for the frontend.

### UI state before this change

No runnable frontend existed in the repository. Operators had the CLI, Obsidian was planned as a review surface, and the root ingress responded with text only. That left no browser-based entry point for understanding architecture state or trying the semantic-memory workflow.

## What is still open

### Product loop gaps

1. Consent records and audit log must become real before production semantic processing.
2. A minimal `POST /v1/inputs` endpoint is needed to persist manual communication events.
3. Hermes needs the first semantic skill: summarize communication, extract action/decision/context, suggest an Evermemos page or cluster, and return a confidence score.
4. backlog-core needs a proposal lifecycle so low-confidence outputs become review-required instead of being applied automatically.
5. gbrain-bridge needs Markdown page CRUD, schema validation and bidirectional-link writing.
6. The frontend needs to switch from local preview mode to backend-backed review and apply actions once those endpoints exist.

### MVP scope recommendation

Do not start with WhatsApp automation, voice adapters, Kanban automation, retention jobs or advanced learning. Those are valuable, but they expand risk before the semantic memory loop is proven. Start with manual input and a single Evermemos/GBrain write path, because it validates the core value while preserving consent and review control.

## Frontend preparation added for Railway

The new frontend is a Vite/React application under `3-code/frontend`. It is intentionally simple and deployable as an independent Railway service with the service root set to `3-code/frontend`.

It provides:

- An architecture/status dashboard for the five services.
- Calls to existing `/v1/health/<service>` ingress routes.
- Caddy CORS headers so a Railway-hosted frontend can call the existing ingress from the browser.
- A manual communication textarea and Evermemos context input.
- Local semantic-preview generation: summary, tags, suggested memo target, confidence and future `/v1/inputs` payload.
- A guarded “apply to backend” action that tries `POST /v1/inputs` and clearly reports that the backend endpoint is not ready yet when it fails.

This lets users work in the frontend today without pretending the backend is finished. It also defines the frontend contract that the backend MVP can implement next.

## Next steps to a useful MVP

1. Implement bearer-auth enforcement consistently on MVP endpoints.
2. Add consent source registration and read-as-of checks in backlog-core.
3. Add `POST /v1/inputs` for manual communication events.
4. Add Hermes `/v1/agent/summarize` or an event consumer that creates summary-and-placement proposals from input events.
5. Add proposal list/detail/update endpoints in backlog-core.
6. Add gbrain-bridge Markdown page create/update with schema validation and links.
7. Replace the frontend's local preview with backend-generated proposals while keeping local preview as an offline fallback.
8. Add review actions in the frontend: accept, edit, reject and apply to Evermemos.
