# DEC-service-auth-bearer-tokens: Trail

> Companion to `DEC-service-auth-bearer-tokens.md`.

## Alternatives considered

### Option A: Per-service bearer tokens (chosen)
- Pros: Standard HTTP auth pattern; widely supported in libraries and proxies; rotation is straightforward (`.env` swap + restart of dependent services); maps cleanly to per-service-identity declaration of purposes; easy to reason about in code review.
- Cons: Tokens are bearer credentials — anyone holding the token can authenticate. Mitigated by short rotation cadence and storage in `.env` only; no transit risk on internal Docker network.

### Option B: mTLS with per-service certificates
- Pros: Strongest authentication — service identity is cryptographically bound; key compromise harder than token leak; standard for production-grade microservices.
- Cons: Significant operational overhead — certificate issuance, distribution, rotation, validation; PKI on a single VPS is overkill at MVP scale; would require either an embedded CA or a public CA, both adding moving parts; debugging certificate issues is harder than debugging token issues.

### Option C: API keys (similar pattern, less standard naming)
- Pros: Functionally equivalent to bearer tokens; familiar to operators of consumer APIs.
- Cons: "API key" implies external-consumer semantics; for inter-service auth, "bearer token" is the more standard terminology and better aligned with HTTP `Authorization` header semantics.

### Option D: No auth between services on internal Docker network
- Pros: Simplest possible.
- Cons: Defeats `CON-no-direct-agent-writes`'s defense-in-depth — a compromised `hermes-runtime` could bypass the gate by calling persistence services directly with crafted payloads. Also defeats `REQ-COMP-purpose-limitation` enforcement, which depends on knowing the calling identity at every endpoint.

## Reasoning

Option A was chosen because it provides the right amount of security at MVP scale without the operational burden of PKI. The bearer-token pattern integrates naturally with the existing `.env`-driven configuration story (`REQ-MNT-env-driven-config`) and rotation runbook (`REQ-REL-secret-rotation`). The Docker-internal network mitigates the bearer-token "anyone can use this" concern — tokens never traverse the public network unless an external client is added later, at which point this decision is reconsidered.

Option B's stronger authentication doesn't pay off at MVP — the threat model is "compromised internal service" rather than "external attacker forging service identity," and bearer tokens already protect against the former. Adding mTLS for the latter is premature optimization and a significant ops burden for the operator (Ben).

Accepted trade-off: bearer tokens are vulnerable to leak. Mitigations: store in `.env` only; rotate on schedule per `REQ-REL-secret-rotation`; never log; secret-rotation runbook tested as part of `REQ-REL-secret-rotation`'s acceptance criteria.

## Human involvement

**Type**: ai-proposed/human-approved

**Notes**: Surfaced during API design (2026-04-27); user approved the API-design proposal which embedded this choice.

## Changelog

| Date | Change | Involvement |
|------|--------|-------------|
| 2026-04-27 | Initial decision recorded as part of api-design.md drafting | ai-proposed/human-approved |
