# DEC-api-versioning: URL-path versioning for inter-service APIs

**Status**: Active

**Category**: Convention

**Scope**: system-wide (all HTTP APIs)

**Source**: [DEC-direct-http-between-services](DEC-direct-http-between-services.md), [REQ-MNT-env-driven-config](../1-spec/requirements/REQ-MNT-env-driven-config.md)

**Last updated**: 2026-04-27

## Context

The system has multiple services exposing HTTP APIs to each other and to operator tooling (CLI, Obsidian watch script). Even at MVP — single deployment, services updated together — a versioning convention reduces coordination cost when an endpoint's contract evolves later. Without an explicit versioning convention, evolution gets ad-hoc (different services pick different schemes, or version skew is detected only at runtime).

Choices: URL-path versioning, content negotiation (`Accept` header), no versioning at MVP.

## Decision

All inter-service APIs use **URL-path versioning** (`/v1/...`). The MVP ships with `v1` across all services. Versioning rules:

- **Additive changes** (new optional fields in request/response, new optional headers, new endpoints) stay within the current major version.
- **Breaking changes** (removed fields, changed field types, changed semantics, removed endpoints) require a new major version (`/v2/...`). Both versions are served in parallel during the transition window; the deprecated version is removed only after all callers are migrated.
- **Internal-only endpoints** (between services in the same Compose stack) follow the same convention; the deployment is currently single-version-everywhere, but the convention keeps the door open for blue-green deploys or partial upgrades later.

Operator-facing APIs (CLI surface) are versioned the same way; CLI commands talk to `/v1/...`.

## Enforcement

### Trigger conditions

- **Design phase**: any new endpoint design uses `/v1/...`. New major versions require a `DEC-*` recording the trigger.
- **Code phase**: HTTP server code routes under `/v1/...`; clients construct URLs with the version path included; no version-less endpoints exist.

### Required patterns

- Endpoint paths: `/<version>/<resource>/...` (e.g., `/v1/proposals`, `/v1/sources/:id`).
- Response bodies do **not** carry a version field by default — the URL is authoritative. (Exception: error responses include the API version that handled the request, for diagnostics.)
- Adding a new endpoint at the existing major version is allowed and routine.
- Adding an optional field to an existing endpoint's request body is allowed (clients may omit it; servers default it).
- Removing a field, renaming a field, or changing a field's type → new major version.

### Required checks

1. Any PR that introduces a new endpoint confirms the URL path begins with the active major version.
2. Any PR that proposes a breaking change to an endpoint also introduces the corresponding `/v<n+1>/...` route and a `DEC-*` recording the version bump.
3. Health endpoint (`/v1/health`) returns the major version in its response so operators can confirm what's deployed.

### Prohibited patterns

- Version-less endpoints (`/proposals`, no `/v1` prefix) at any service.
- Mixing versioning schemes across services (some URL-path, some content-negotiation).
- Silently changing a field's type or semantics without a version bump.

## Reconsider trigger

Revisit this decision if:

- The system grows to enough endpoints that path-based versioning becomes burdensome (unlikely at MVP scale).
- An external consumer requires content-negotiation versioning for compatibility reasons.
- Multiple major versions need to be served in parallel for a long period (would prompt a separate decision on deprecation policy).
