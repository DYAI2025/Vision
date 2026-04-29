# ASM-no-scalability-target: Horizontal scaling is not an MVP capability

**Category**: Business

**Status**: Unverified

**Risk if wrong**: Medium — if the system has to support more than two consented actors or hits sustained burst rates beyond the single-VPS reference target, we'd need to add a horizontal-scale dimension (sharding `backlog-core` by project, replicating `gbrain-bridge` read-side, deploying multi-host Ollama). The remediation is well-understood architecturally but adds operational complexity (multi-host networking, distributed audit-log integrity, cross-instance idempotency) — out of scope for the two-person MVP. The risk is bounded because (a) Phase-7 vertical-scale headroom on the reference VPS is sufficient for the documented user count and (b) the event-sourced design makes adding read replicas additive, not breaking.

## Statement

The MVP explicitly **deprioritizes horizontal scaling**. The system is designed and operated as a **single-VPS, vertically-scalable** deployment. No `REQ-SCA-*` (Scalability) requirements are produced, and the `REQ-SCA` class is intentionally empty. Phase-7 load-test tasks (`TASK-perf-ingest-latency-tests`, `TASK-perf-routing-throughput-tests`) are **non-binding for the MVP release** in the sense that they validate the documented single-VPS targets per `REQ-PERF-ingest-latency` and `REQ-PERF-routing-throughput` — they do not establish a horizontal-scale target.

Operationally this means:

- Postgres runs as a single instance, not a primary-with-replicas cluster.
- Ollama runs as a single process on the same host (or on the operator's separate inference host via the remote-inference profile).
- `gbrain-bridge` and `kanban-sync` operate against a single `vault` Docker volume — no concurrent multi-writer story.
- All HTTP traffic flows through a single ingress instance (Caddy or Tailscale), not a load-balancer fleet.

Vertical-scaling adjustments (more vCPU / RAM, faster disk, larger Postgres `max_connections`) are the only documented adjustment path before Phase 7's documented load tests bind.

## Rationale

Three reasons drive this scope:

1. **User count is bounded.** The system supports two consented human actors (`STK-vincent`, `STK-ben`) plus their consented sources. Per `GOAL-multi-source-project-ingestion`, MVP channels are WhatsApp / voice / repo / manual CLI for those two users — total ingest rate is well below the `REQ-PERF-routing-throughput` ≥10 events/min sustained target, so the throughput envelope already has substantial headroom.
2. **Operational team is two people.** Multi-host Postgres replication, Tailscale meshing across multiple hosts, and distributed Ollama serving each carry a real operations burden. Per `STK-ben`'s "low ops overhead" interest in `1-spec/stakeholders.md`, single-VPS is the right complexity level for the team.
3. **Architectural reversibility is high.** The event-sourced design at `backlog-core` (per `DEC-postgres-as-event-store`, `DEC-hash-chain-over-payload-hash`) admits a read-replica or sharded-by-project topology as an additive change. Adding scalability later is a deferred-cost option, not a forward-incompatibility.

The decision to not introduce a `REQ-SCA-*` artifact is therefore a deliberate scope choice, not an oversight. Recording the choice as an assumption (rather than a constraint) keeps the door open for re-evaluation if scope grows.

## Verification Plan

Three verification points in order of severity:

1. **Phase-7 load-test outcomes** (during `TASK-perf-ingest-latency-tests` and `TASK-perf-routing-throughput-tests`): if the reference VPS can meet `REQ-PERF-ingest-latency` and `REQ-PERF-routing-throughput` at the documented user count, this assumption is implicitly **Verified**. If the load tests show the system cannot meet targets without horizontal scaling, this assumption is **Invalidated** and the project must either (a) accept softer perf targets, (b) add `REQ-SCA-*` artifacts and a corresponding architecture revision, or (c) ship with the constraint that user count cannot grow beyond the verified envelope.
2. **First non-Vincent/Ben source registration**: at the point a third consented actor joins, re-evaluate whether single-VPS still fits. The natural review point coincides with `DEC-gdpr-legal-review-deferred`'s gating condition (legal review must complete before non-Vincent/Ben source registration), so the two reviews can be batched.
3. **First commercial / multi-tenant deployment**: if the project ever ships beyond the personal-use envelope, this assumption must be re-elicited with a new stakeholder model. Out of MVP scope by definition; flagged here so it isn't forgotten.

If invalidated at any of those three points, follow the assumption-invalidation procedure in `1-spec/CLAUDE.spec.md` § "Assumption invalidation": present the dependent artifacts, propose adjustments, wait for explicit approval before modifying anything.

## Related Artifacts

- [GOAL-multi-source-project-ingestion](../goals/GOAL-multi-source-project-ingestion.md) — bounded user / channel count is the precondition for single-VPS being sufficient.
- [GOAL-local-portable-deployment](../goals/GOAL-local-portable-deployment.md) — the Should-have deploy goal targets a single VPS by design; horizontal scaling would change this goal's nature.
- [REQ-PERF-ingest-latency](../requirements/REQ-PERF-ingest-latency.md), [REQ-PERF-routing-throughput](../requirements/REQ-PERF-routing-throughput.md) — the only quantitative perf targets; verification of this assumption depends on these tests passing.
- [CON-vps-portable-deployment](../constraints/CON-vps-portable-deployment.md) — single-VPS is the documented deployment model; this assumption explicitly says we don't extend beyond it.
- [CON-local-first-inference](../constraints/CON-local-first-inference.md) — single-Ollama-instance is part of the same scope choice.
