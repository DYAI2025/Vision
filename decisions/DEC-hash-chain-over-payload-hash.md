# DEC-hash-chain-over-payload-hash: Audit chain hashes a stable payload digest, not the payload itself

**Status**: Active

**Category**: Architecture

**Scope**: backend (`backlog-core` events table)

**Source**: [REQ-SEC-audit-log](../1-spec/requirements/REQ-SEC-audit-log.md), [REQ-COMP-rtbf](../1-spec/requirements/REQ-COMP-rtbf.md), [REQ-F-retention-sweep](../1-spec/requirements/REQ-F-retention-sweep.md), [REQ-F-state-reconstruction](../1-spec/requirements/REQ-F-state-reconstruction.md)

**Last updated**: 2026-04-27

## Context

The audit log requires hash-chain integrity (`REQ-SEC-audit-log`) and must remain verifiable end-to-end after RTBF cascades redact subject-attributable content (`REQ-COMP-rtbf`: "audit shape preserved") and after retention sweeps redact raw payloads at 30 days (`REQ-F-retention-sweep`).

If the chain hashes the row's `payload` directly, redaction breaks chain verification — once the payload is replaced with a tombstone, the recomputed hash no longer matches the stored chain, and verification fails for every event downstream of the redaction. The alternatives are (a) "no redaction is allowed" (incompatible with retention and RTBF), (b) "redaction breaks the chain by design" (incompatible with `REQ-SEC-audit-log`'s tamper-evidence claim), or (c) decouple the chain from the payload's mutable bytes.

## Decision

The hash chain incorporates a **stable digest of the payload (`payload_hash`) computed once at insert** rather than the payload itself. Specifically:

- `payload_hash = SHA-256(canonical_json(payload))` — computed once at INSERT, stored in the row, **never modified**.
- `hash = SHA-256(event_id ‖ event_type ‖ created_at ‖ actor_id ‖ payload_hash ‖ prev_hash)`.
- `prev_hash = events.hash` of the immediately preceding event in chain order.

When retention sweep or RTBF cascade redacts a row's `payload` (replacing with a tombstone marker, setting `redacted = TRUE`), `payload_hash` is **not** modified. Chain verification recomputes `hash` from the row's static fields plus `payload_hash` and validates the chain end-to-end — verification still passes after redaction.

A secondary integrity check, where the row's `payload IS NOT NULL`, additionally verifies `SHA-256(canonical_json(payload)) == payload_hash`. This catches accidental payload mutation on non-redacted events.

## Enforcement

### Trigger conditions

- **Specification phase**: n/a.
- **Design phase**: any design that touches the events table schema, the audit-log verification routine, or the redaction mechanism must consult this decision.
- **Code phase**: implementation of `backlog-core`'s event-emit, retention-sweep, RTBF cascade, and audit-verification code paths must follow the patterns below.
- **Deploy phase**: post-restore audit verification (per `REQ-REL-backup-restore-fidelity`) runs against the chain using `payload_hash`.

### Required patterns

- Compute `payload_hash` exactly once, at the INSERT moment, using `canonical_json` (sorted keys, no insignificant whitespace) so the digest is reproducible.
- Compute `hash` using only the static fields + `payload_hash` + `prev_hash`. Never include the mutable `payload` directly.
- The redaction routine sets `payload`, `redacted`, `redaction_run_id`, `redacted_at` — and **only** these columns. It must not modify `payload_hash`, `hash`, `prev_hash`, `event_id`, `event_type`, `created_at`, `actor_id`, `proposal_id`, `source_input_event_id`, or `subject_ref`.
- The chain-verification routine accepts a redacted event as valid as long as the chain math checks out using `payload_hash`. It does **not** require `payload IS NOT NULL`.
- The secondary integrity check (`SHA-256(canonical_json(payload)) == payload_hash` where `payload IS NOT NULL`) is run on a sampled basis as a sanity check, not as part of the chain verification itself.

### Required checks

1. Unit test: insert a chain of events, redact a middle event's payload, run chain verification — verification passes.
2. Unit test: insert a chain of events, deliberately corrupt `payload` on a non-redacted event without updating `payload_hash` — secondary integrity check detects the corruption; chain verification still passes (because `payload_hash` is what the chain reads).
3. Unit test: insert a chain, deliberately corrupt `payload_hash` on a row — chain verification fails at that row.
4. Restore-and-verify flow: after `restore.sh`, chain verification runs end-to-end before the system accepts new writes; runtime errors out if chain is broken.

### Prohibited patterns

- Hashing `payload` directly in any chain or verification code path.
- Recomputing `payload_hash` on UPDATE (would break the chain).
- Storing the canonical JSON of `payload` in a separate column to "fix" the redaction problem (defeats the purpose; doubles storage; adds a second mutation surface).
- Using a non-cryptographic hash (e.g., MD5, FNV) for either `payload_hash` or `hash` — both must be cryptographic to satisfy tamper-evidence.

## Reconsider trigger

Revisit this decision if:

- A regulatory change requires a chain mechanism that stores the canonical payload immutably (would force a redesign — likely a separate "redacted_payload" column with strict access controls).
- A future event store choice (per `DEC-postgres-as-event-store`'s reconsider trigger) provides a built-in chain mechanism that handles redaction differently.
