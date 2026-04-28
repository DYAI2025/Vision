# whatsorga-ingest

**Responsibility**: Adapter layer + normalization. Hosts one adapter per input channel (WhatsApp, voice transcript, repository event, manual CLI) and produces channel-agnostic `input_event`s flowing into `backlog-core`. Performs the consent check at the system boundary.

**Technology**: Python 3.12 + FastAPI per [`DEC-backend-stack-python-fastapi`](../../decisions/DEC-backend-stack-python-fastapi.md). Uniform across all five backend components.

## Interfaces

- **HTTP outbound** to `backlog-core`: `POST /v1/inputs` to submit normalized `input_event`s. Idempotency key: `event_id`. Authenticated with this component's bearer token.
- **Per-adapter inbound contracts**:
  - WhatsApp adapter: user-attached Web/desktop session or official multi-device API (per [`DEC-platform-bypass-review-checklist`](../../decisions/DEC-platform-bypass-review-checklist.md) — no headless logins, no token replay).
  - Voice adapter: transcript ingestion from a local transcription pipeline.
  - Repo events adapter: webhook receiver from operator-controlled repositories.
  - Manual CLI adapter: invoked by the operator's `vision` CLI for ad-hoc input.
- **HTTP inbound** from operator CLI: source-registration adapter wiring (setup-time only — registers an adapter against a `source_id`).
- **Filesystem**: ephemeral storage for in-flight normalization buffers; no durable filesystem state.

## Requirements Addressed

| File | Type | Priority | Summary |
|------|------|----------|---------|
| [REQ-F-input-event-normalization](../../1-spec/requirements/REQ-F-input-event-normalization.md) | Functional | Must-have | Single normalization layer produces channel-agnostic `input_event`s; channel concerns confined to `channel_metadata` extension |
| [REQ-F-consent-revocation](../../1-spec/requirements/REQ-F-consent-revocation.md) | Functional | Must-have | Enforces consent-revoked drops at the ingest boundary; in-flight events for revoked sources never commit |

## Relevant Decisions

| File | Title | Trigger |
|------|-------|---------|
| [DEC-backend-stack-python-fastapi](../../decisions/DEC-backend-stack-python-fastapi.md) | Python 3.12 + FastAPI as the uniform backend stack | Any task that creates or modifies source code, build configuration, or test infrastructure inside this component |
| [DEC-direct-http-between-services](../../decisions/DEC-direct-http-between-services.md) | Synchronous HTTP/REST between services at MVP | Inter-service call patterns |
| [DEC-api-versioning](../../decisions/DEC-api-versioning.md) | URL-path versioning (`/v1/...`) | Endpoint construction on every outbound call |
| [DEC-service-auth-bearer-tokens](../../decisions/DEC-service-auth-bearer-tokens.md) | Per-service bearer tokens with declared purposes | Authentication on outbound + inbound calls |
| [DEC-idempotency-keys](../../decisions/DEC-idempotency-keys.md) | `Idempotency-Key` header on mutations | `POST /v1/inputs` carries `event_id` as the key |
| [DEC-platform-bypass-review-checklist](../../decisions/DEC-platform-bypass-review-checklist.md) | Reviewer checklist of patterns rejected as platform-protection bypass | Any change to channel adapters, auth-handling code, or session-management code |
