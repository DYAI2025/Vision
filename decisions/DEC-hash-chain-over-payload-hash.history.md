# DEC-hash-chain-over-payload-hash: Trail

> Companion to `DEC-hash-chain-over-payload-hash.md`.

## Alternatives considered

### Option A: Hash a stable payload digest (`payload_hash`) (chosen)
- Pros: Chain remains verifiable after RTBF and retention-sweep redaction; redaction is a clean column update on `payload`-only fields; `payload_hash` is stable so the chain math never needs to be redone; secondary integrity check catches accidental payload mutation on non-redacted rows.
- Cons: Slightly more complex than naive payload-hashing; requires canonical JSON (sorted keys, no insignificant whitespace) for reproducibility; an extra column (`payload_hash`) per row.

### Option B: Hash the payload directly
- Pros: Simplest possible chain.
- Cons: Redaction breaks the chain — once `payload` is replaced with a tombstone, the recomputed hash no longer matches; either (a) RTBF / retention sweep cannot redact (incompatible with `REQ-COMP-rtbf` and `REQ-F-retention-sweep`) or (b) chain integrity is lost on redaction (incompatible with `REQ-SEC-audit-log`'s tamper-evidence claim).

### Option C: Two parallel chains — one over content, one over metadata
- Pros: Lets the metadata-chain remain valid post-redaction even if the content-chain is broken.
- Cons: Doubles the chain machinery; verification semantics get fuzzy ("which chain is authoritative for which question?"); doesn't actually solve the redaction problem unless one of the chains is essentially Option A.

### Option D: Append-only, no in-place redaction; redaction = mark a tombstone in a separate table
- Pros: Original chain stays untouched.
- Cons: The unredacted row still contains the subject's content — RTBF requires the content to be unrecoverable from the row, not just "marked as redacted." Either we delete the original row (chain breaks) or we leave the content (RTBF non-compliance). Both are unacceptable.

## Reasoning

Option A was chosen because it is the only option that satisfies all three constraints simultaneously: chain verifiability end-to-end (`REQ-SEC-audit-log`), RTBF redaction across the audit log without breaking the chain (`REQ-COMP-rtbf`), and retention-sweep redaction at 30 days (`REQ-F-retention-sweep`). The added complexity (one extra column, canonical-JSON discipline) is small relative to these benefits. The pattern is well-established in regulated audit-log designs.

Option B's simplicity is appealing but the failure mode (chain breaks on redaction) directly contradicts requirements. Options C and D either don't solve the problem or solve it at higher cost than A.

The accepted trade-off: the canonical-JSON discipline must be enforced consistently. Mitigation: a single `canonical_json` helper used at every emit site, plus the secondary integrity check that catches drift on a sampled basis.

## Human involvement

**Type**: ai-proposed/human-approved

**Notes**: Surfaced during data-model drafting (2026-04-27); user approved the data-model proposal which embedded this choice. The trade-off (extra column + canonical-JSON discipline vs. chain-survives-redaction) was presented and accepted.

## Changelog

| Date | Change | Involvement |
|------|--------|-------------|
| 2026-04-27 | Initial decision recorded as part of data-model.md drafting | ai-proposed/human-approved |
