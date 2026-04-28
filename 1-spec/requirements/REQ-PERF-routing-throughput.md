# REQ-PERF-routing-throughput: Sustained and burst throughput targets for the routing pipeline

**Type**: Performance

**Status**: Draft

**Priority**: Should-have

**Source**: [GOAL-multi-source-project-ingestion](../goals/GOAL-multi-source-project-ingestion.md)

**Source stakeholder**: [STK-ben](../stakeholders.md)

## Description

The routing pipeline (normalization → consent check → routing decision → branch to extraction or review) sustains throughput at MVP hardware spec:

- **Sustained throughput:** ≥ **10 routed events per minute** on a single VPS (reference spec: 4 vCPU, 8 GB RAM, local Ollama + Gemma model) without violating [REQ-PERF-ingest-latency](REQ-PERF-ingest-latency.md) p95 targets over a 1-hour load window.
- **Burst tolerance:** sustains **≥ 30 events per minute for 2 minutes** without violating the autonomous-path p95 target measured on the burst window itself; queue depth must drain back to steady-state within 5 minutes after burst ends.

The reference VPS spec is documented in `4-deploy/` runbooks; lower-spec hardware may not meet these targets and is acceptable, with the targets adjusted per documented hardware tier in the deployment manifest.

Throughput targets account for local-first inference latency (Gemma response time on local hardware). Remote inference, when configured, may improve burst tolerance but is not assumed in the baseline.

## Acceptance Criteria

- Given a load-test harness on the reference VPS spec, when sustained 10 events/min load runs for 1 hour, then p95 autonomous-path latency stays < 5 min and p95 review-path latency stays < 2 min.
- Given the same harness, when a 30 events/min burst is injected for 2 min on top of the sustained load, then p95 autonomous-path latency on the burst window stays < 5 min; queue depth returns to pre-burst level within 5 minutes after burst end.
- Given a deployment on hardware below the reference spec, when the operator runs the load test, then the test produces a clear "below target" report with the actually-measured throughput and latency, rather than failing silently.

## Related Constraints

- [CON-vps-portable-deployment](../constraints/CON-vps-portable-deployment.md) — throughput targets are tied to a documented hardware tier, not a specific host.
- [CON-local-first-inference](../constraints/CON-local-first-inference.md) — throughput baseline assumes local inference.
