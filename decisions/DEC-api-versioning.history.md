# DEC-api-versioning: Trail

> Companion to `DEC-api-versioning.md`.

## Alternatives considered

### Option A: URL-path versioning (chosen)
- Pros: Most visible — version is in the URL, easy to grep, easy to route in proxies (Caddy / Tailscale ingress); easy to serve multiple versions in parallel during migration; cache-friendly; familiar to most contributors.
- Cons: Slightly more verbose URLs; introduces a path segment that's "noise" before the system has multiple versions.

### Option B: Content negotiation (`Accept: application/vnd.vision.v1+json`)
- Pros: URLs stay clean; version is metadata, not structure; easier for clients that operate on resources rather than endpoints.
- Cons: Less visible — easy to miss in code review; harder to debug (curl users have to remember the header); some HTTP middleware ignores `Accept` for routing decisions; not standard across the broader HTTP ecosystem.

### Option C: No versioning at MVP
- Pros: Simplest possible; fewer paths to maintain; faster initial development.
- Cons: Adding versioning later is harder than starting with it (every existing path becomes "the unversioned legacy path"); breaking changes during MVP iteration require version coordination by side-channel; doesn't scale to a future where any client lags a deploy.

## Reasoning

Option A was chosen because the cost of starting with URL-path versioning is small (one extra path segment), the convention is widely understood, and the future-cost of *not* having it from day one is high (retroactive versioning is awkward). The visibility benefit (version-in-URL is easy to read in logs, code, and ingress configuration) outweighs the verbosity cost. Option C was tempting at MVP but rejected because the project explicitly aims for a long-lived deployment that can tolerate future evolution — versioning is exactly the kind of forward-compatibility cost that's cheap when paid early.

Accepted trade-off: URLs carry a `/v1` segment that's currently redundant. Mitigation: it's one segment; it costs nothing operationally and pays off the first time any endpoint contract changes meaningfully.

## Human involvement

**Type**: ai-proposed/human-approved

**Notes**: Surfaced during API design (2026-04-27); user approved the API-design proposal which embedded this choice.

## Changelog

| Date | Change | Involvement |
|------|--------|-------------|
| 2026-04-27 | Initial decision recorded as part of api-design.md drafting | ai-proposed/human-approved |
