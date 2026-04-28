# REQ-MNT-env-driven-config: All runtime configuration via `.env`; zero source-code edits to redeploy

**Type**: Maintainability

**Status**: Draft

**Priority**: Should-have

**Source**: [US-fresh-vps-install](../user-stories/US-fresh-vps-install.md), [US-secret-rotation](../user-stories/US-secret-rotation.md), [CON-vps-portable-deployment](../constraints/CON-vps-portable-deployment.md)

**Source stakeholder**: [STK-ben](../stakeholders.md)

## Description

Every runtime configuration value is supplied via `.env` files consumed by `docker-compose.yml` and the services it composes. **Zero source-code edits** are required to redeploy on a new host, switch reverse-proxy modes, enable a remote-inference profile, change retention windows, or rotate secrets.

Configuration scope covered by `.env`:

- Hostnames, ports, ingress mode (Caddy public hostname / Tailscale)
- Volume paths (within container-managed volumes only)
- Secret references (DB credentials, Tailscale keys, model endpoint credentials, audit-log signing keys)
- Feature flags (`remote_inference_profiles`, default `auto_policy`, default confidence thresholds, retention sweep cadence, audit reconciliation cadence)
- Service-specific runtime values (model endpoint URLs, Ollama model name, embedding model, retention windows in days)

**`.env.example` discipline:**

- Every key the system reads at runtime is present in `.env.example` with: a documented default value (or `# REQUIRED — no default` annotation), an explanatory comment, and (where relevant) the allowed value range or enumeration.
- A periodic check (CI step or pre-deploy script) compares the keys actually read by services against `.env.example` and **fails** on drift in either direction (key in `.env.example` but unused; key read by code but missing from `.env.example`).

**Failure behaviors:**

- Missing required `.env` keys cause the affected service to **fail-fast at startup** with a clear error naming the key. No fallback to undocumented defaults.
- Optional keys with documented defaults must work when omitted.
- No service may contain a hardcoded production hostname, IP address, vendor-specific endpoint, or path outside container volumes.

## Acceptance Criteria

- Given a service started with its `.env` missing a required key, when the container starts, then it exits non-zero within 5 seconds with a stderr message naming the missing key; no partial state is written.
- Given the periodic `.env.example` drift check, when run against the current code base, then it passes; a deliberate test injecting a new code-read key without updating `.env.example` causes the check to fail.
- Given a fresh deployment on a new host with only `.env.example` filled in, when the system is brought up, then no source-code edits are required for it to pass `smoke_test.sh`.

## Related Constraints

- [CON-vps-portable-deployment](../constraints/CON-vps-portable-deployment.md) — `.env`-driven configuration is the structural enforcement of host independence.
