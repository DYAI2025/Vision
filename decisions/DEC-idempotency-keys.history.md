# DEC-idempotency-keys: Trail

> Companion to `DEC-idempotency-keys.md`.

## Alternatives considered

### Option A: `Idempotency-Key` header on mutations (chosen)
- Pros: Standard HTTP pattern (Stripe, AWS, etc. use this); keys are explicit and client-controlled; works across HTTP/proxy boundaries; easy to debug (curl users see the header in their command); doesn't change request bodies.
- Cons: Requires server-side idempotency store; 24h TTL costs some storage; clients have to generate keys (small burden).

### Option B: Idempotency by content hash (server computes hash of request body and dedupes)
- Pros: Clients don't have to generate keys.
- Cons: Two genuinely-different requests with identical bodies (e.g., two CLI invocations of the same `vision rtbf <subject>` for two different but identical-shaped subjects — hypothetical but possible) would be incorrectly deduplicated; hashing the body has performance and privacy implications (bodies may contain sensitive data); doesn't allow the client to assert "this is the same logical operation as my previous attempt."

### Option C: No idempotency mechanism
- Pros: Simplest server.
- Cons: Retry-after-network-failure produces duplicates — incompatible with the proposal pipeline's "every mutation chains by proposal_id" semantics; would push idempotency burden onto every client (each would have to dedupe their own retries with no server help).

### Option D: Idempotency as a query parameter
- Pros: Slightly easier for some clients than a header.
- Cons: Less standard; query parameters can leak into logs more easily than headers; some HTTP cache layers strip or include them inconsistently.

## Reasoning

Option A was chosen because it's the established HTTP pattern for this problem, integrates cleanly with the existing API design, and gives clients explicit control over what counts as "the same logical operation." The natural fit with `proposal_id` (per `REQ-F-proposal-pipeline`) is the strongest signal — proposal-pipeline calls already have a unique id per logical proposal, so the idempotency mechanism is essentially free for the most-used mutation surface.

Option B's content-hash approach is appealing for "no client work" but the false-positive risk (different operations with identical bodies) and the performance cost (hashing every body) outweigh the convenience. Option C is unacceptable given the requirements.

Accepted trade-off: 24h TTL + per-call storage. Mitigation: storage cost is small at MVP scale; sweep job covers eviction.

## Human involvement

**Type**: ai-proposed/human-approved

**Notes**: Surfaced during API design (2026-04-27); user approved the API-design proposal which embedded this choice.

## Changelog

| Date | Change | Involvement |
|------|--------|-------------|
| 2026-04-27 | Initial decision recorded as part of api-design.md drafting | ai-proposed/human-approved |
