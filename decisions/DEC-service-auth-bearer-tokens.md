# DEC-service-auth-bearer-tokens: Service-to-service auth via per-service bearer tokens with declared purposes

**Status**: Active

**Category**: Architecture

**Scope**: system-wide (inter-service auth)

**Source**: [CON-no-direct-agent-writes](../1-spec/constraints/CON-no-direct-agent-writes.md), [REQ-COMP-purpose-limitation](../1-spec/requirements/REQ-COMP-purpose-limitation.md), [REQ-REL-secret-rotation](../1-spec/requirements/REQ-REL-secret-rotation.md), [DEC-confidence-gate-as-middleware](DEC-confidence-gate-as-middleware.md)

**Last updated**: 2026-04-27

## Context

Inter-service HTTP calls must authenticate the calling service so persistence services (`backlog-core`, `gbrain-bridge`, `kanban-sync`) can:

1. Reject calls from unrecognized callers (defense-in-depth for `CON-no-direct-agent-writes`).
2. Enforce per-purpose access control per `REQ-COMP-purpose-limitation`.
3. Distinguish operator-issued calls from agent-issued calls in audit logs.

Choices: per-service bearer tokens (HTTP `Authorization` header), mTLS (mutual TLS with per-service certificates), API keys (similar to bearer but less standard), unauthenticated (rejected — defeats the purpose).

## Decision

Inter-service authentication uses **per-service bearer tokens** sent in the `Authorization: Bearer <token>` HTTP header.

Specific shape:

- One token per **calling service identity** (e.g., `hermes-runtime` has a token recognized by `backlog-core`, `gbrain-bridge`, `kanban-sync`; `whatsorga-ingest` has its own token; the operator CLI has its own token; `gbrain-bridge`'s Obsidian watch script uses the operator token).
- Tokens are **`.env`-driven** per `REQ-MNT-env-driven-config`. Each service's `.env` declares the tokens it accepts (with the calling-identity name) and the tokens it sends (one per outbound peer).
- Each token maps to a **declared purposes set** in the receiving service's config. The receiving service checks the calling identity's declared purposes against the action's required purpose at every endpoint, satisfying `REQ-COMP-purpose-limitation`.
- Tokens are rotated per `REQ-REL-secret-rotation`. Each rotation produces a `secret.rotated` audit event with the secret category (no values logged).
- Tokens are **opaque random strings** (≥256 bits of entropy from a CSPRNG). They are not JWTs and do not encode claims — claims (purposes, identity) live in the receiving service's config keyed by token hash.

## Enforcement

### Trigger conditions

- **Design phase**: any new inter-service endpoint specifies which calling identities are accepted and what purposes they need.
- **Code phase**: every persistence-service HTTP entry checks the bearer token against the configured calling identities; declared purposes are checked against the action's required purpose; mismatches return `403 purpose_denied`.
- **Deploy phase**: `.env.example` declares the token slots; install runbook generates initial tokens; rotation runbook covers per-category rotation.

### Required patterns

- HTTP entry middleware extracts the bearer token, looks up the calling identity in the service's config, validates declared purposes for the action.
- Auth failures return structured `401 auth_required` (no token), `401 auth_invalid` (token unrecognized), or `403 purpose_denied` (token recognized but purpose not granted).
- Tokens are stored in `.env` only; never committed to the repo; never logged in audit events (event records the calling identity name, not the token).
- Token comparison uses constant-time comparison to avoid timing side channels.

### Required checks

1. Before merging an endpoint, confirm middleware checks (a) bearer present, (b) token recognized, (c) calling identity has the action's required purpose.
2. Penetration-style test: a deliberately malformed `Authorization` header is rejected with `401`.
3. Penetration-style test: a recognized token whose calling identity lacks the required purpose is rejected with `403 purpose_denied`.
4. Rotation test: after `vision rotate <secret-category>`, all services authenticate with new tokens; old tokens are rejected.

### Prohibited patterns

- Storing tokens in code, in committed configuration files, or in log entries.
- Using the same token across calling identities.
- "Master" tokens that bypass purpose checks.
- Long-lived tokens with no rotation plan.
- Returning verbose auth error details (e.g., "this is the right token but you're missing purpose X") that aid an attacker — keep error responses structured but minimal.

## Reconsider trigger

Revisit this decision if:

- A regulatory or threat-model change requires mTLS or stronger PKI-based auth.
- The system grows to support external (non-co-deployed) callers, where token distribution becomes complex.
- A token leak incident exposes a structural weakness (would prompt review of rotation cadence, key derivation, and storage).
