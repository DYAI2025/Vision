# ASM-confidence-scores-are-meaningful: The confidence-scoring function is calibrated enough that the band thresholds are decision-relevant

**Category**: Technology

**Status**: Unverified

**Risk if wrong**: High — if false, the entire confidence-gate construct becomes performative rather than functional. Events at "0.86" would not be systematically more correctly routed than events at "0.84"; the `0.55 / 0.85` thresholds would be arbitrary cuts that ratchet up review queue size without improving correctness, or worse, would let through low-quality autonomous writes that should have been reviewed. The remediation cost is large: every action site already wired to the gate would need its scoring function replaced or re-calibrated, and the default thresholds would need to be re-derived per scoring function and possibly per project.

## Statement

The confidence-scoring function the system uses (model log-likelihood proxy, semantic similarity to project profile, learnings density, or some combination of these) correlates well enough with downstream human-correction outcomes that the default band thresholds (`0.55` and `0.85`) are decision-relevant — i.e., events at confidence `0.86` are systematically more likely to be correctly routed than events at `0.84`, and events below `0.55` are systematically more likely to be wrong than events at `0.60`.

Specifically: the calibration curve (predicted confidence vs. actual correctness rate on a labeled sample) is monotonic and shows non-trivial separation at the chosen thresholds.

## Rationale

The plausibility comes from how the score is intended to be constructed: not a single model output, but a composite of signals that have empirical support individually (semantic similarity to project profile, recency-weighted learning density, source-confidence prior). The combination is more robust than any one signal, and the thresholds are conservative defaults rather than razor-thin cuts.

The risk is that early in the system's life, before learnings have accumulated, the scoring function relies heavily on the semantic similarity component, which may be noisy on short messages or messages with sparse project-profile context. Cold-start projects are the most likely failure mode for this assumption.

## Verification Plan

- **During Code phase:** instrument the routing layer to record `(confidence, eventual_disposition)` pairs for every event whose disposition is eventually known (operator accept / operator correct / operator reject in review queue). Build a calibration curve at end of each working week during early operation.
- **Decision point:** before making the autonomous-band defaults available to a project (i.e., before operators can flip `auto_policy` to autonomous for any action class on that project), the project's calibration curve must be reviewed. If the curve is flat or non-monotonic at the default thresholds, raise the project's autonomous threshold or restrict autonomous action classes.
- **Trigger for re-verification:** scoring function change; new project type with markedly different content distribution; calibration curve drifts more than 10 percentage points week-over-week.

## Related Artifacts

- Goals: [GOAL-multi-source-project-ingestion](../goals/GOAL-multi-source-project-ingestion.md), [GOAL-trustworthy-supervised-agent](../goals/GOAL-trustworthy-supervised-agent.md)
- Requirements: [REQ-F-confidence-gate](../requirements/REQ-F-confidence-gate.md), [REQ-F-project-routing](../requirements/REQ-F-project-routing.md), [REQ-F-artifact-extraction](../requirements/REQ-F-artifact-extraction.md)
- Constraints: [CON-confidence-gated-autonomy](../constraints/CON-confidence-gated-autonomy.md)
