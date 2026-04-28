# REQ-REL-event-replay-correctness: Replay is idempotent, deterministic, crash-safe, and fails fast on corrupted chains

**Type**: Reliability

**Status**: Draft

**Priority**: Must-have

**Source**: [GOAL-trustworthy-supervised-agent](../goals/GOAL-trustworthy-supervised-agent.md), [CON-no-direct-agent-writes](../constraints/CON-no-direct-agent-writes.md)

**Source stakeholder**: [STK-vincent](../stakeholders.md), [STK-ben](../stakeholders.md)

## Description

Replay (used by [REQ-F-state-reconstruction](REQ-F-state-reconstruction.md), the rollback flow, and audit verification) must satisfy four reliability properties:

1. **Determinism** — given the same event log and the same code version, replay produces bit-identical state on every run.
2. **Idempotence** — replaying the same range of events more than once produces the same end state as replaying it once. There are no "side accumulators" that grow with re-replay.
3. **Crash safety** — replay interrupted mid-run (process kill, host restart, OOM) resumes from the last-committed event without double-application or skipped events. Replay maintains a per-run progress checkpoint so resumption is precise, not bracketed.
4. **Fail-fast on corruption** — replay against a corrupted event chain (missing event in the middle, broken hash chain, schema-incompatible event) fails with a structured `replay_chain_corrupt` error naming the offending event id and corruption category. **Replay must never produce partial state** that could be mistaken for valid reconstruction.

A replay-correctness test harness exercises all four properties on a representative event log and is run as part of the smoke-test suite ([REQ-PORT-vps-deploy](REQ-PORT-vps-deploy.md)) — replay correctness is verified before each deploy, not just in dev.

This requirement complements [REQ-F-state-reconstruction](REQ-F-state-reconstruction.md): that requirement defines *what* reconstruction produces; this one defines the *correctness properties* of the replay engine that backs it.

## Acceptance Criteria

- Given a representative event log, when replay is invoked twice consecutively, then both runs produce bit-identical end state (determinism + idempotence).
- Given a replay run that is killed mid-execution and then restarted, when the restart completes, then the resulting state is bit-identical to a single uninterrupted replay over the same log range; no event is double-applied or skipped.
- Given an event log with a deliberately broken hash chain (one event removed or modified), when replay runs, then it fails with `replay_chain_corrupt` naming the offending event id within seconds; partial state is not exposed.

## Related Constraints

- [CON-no-direct-agent-writes](../constraints/CON-no-direct-agent-writes.md) — replay correctness underpins the audit-log's value as a record of truth.
