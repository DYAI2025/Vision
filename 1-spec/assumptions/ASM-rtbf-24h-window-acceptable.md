# ASM-rtbf-24h-window-acceptable: A 24-hour RTBF completion window is acceptable for this deployment

**Category**: Regulatory

**Status**: Unverified

**Risk if wrong**: Medium — if false, [REQ-COMP-rtbf](../requirements/REQ-COMP-rtbf.md) needs a tighter completion target. The cascade design and storage layout would need re-engineering to support sub-hour or near-real-time deletion across all layers; the operator runbook becomes time-critical rather than next-business-day. Most cost lives in re-engineering the GBrain link cleanup and the audit-log redaction path, both of which are currently designed assuming an hours-not-seconds window.

## Statement

A 24-hour completion window from operator acceptance to verified RTBF completion is acceptable under the regulatory profile applicable to this deployment (personal use; co-owners Vincent and Ben as data controllers; small-scale subject base of personal contacts and consented chat senders). No subject-base regulatory profile applicable to MVP imposes a stricter window.

## Rationale

GDPR Art. 12(3) gives controllers up to **one month** to respond to data-subject requests, extendable to three months in complex cases. 24 hours is well inside that window. Deployments under stricter regulators (HIPAA, certain financial regulators) or with formal SLAs to data subjects might require faster turnaround, but those are out of scope for the MVP.

The risk is asymmetric: choosing a tighter window early would force significant engineering cost; choosing a looser window later (if regulation tightens) requires only operational and code changes to the cascade scheduler.

## Verification Plan

- **At Spec → Design gate:** reviewer confirms the deployment's regulatory profile is consistent with personal use under GDPR Art. 12 timing.
- **Trigger for re-verification:** any commercial use; any onboarding of external (non-Vincent, non-Ben) operator-roles that might change the controller/processor relationship; explicit subject demand for a faster window.

## Related Artifacts

- Goals: [GOAL-auditable-consent-and-privacy](../goals/GOAL-auditable-consent-and-privacy.md)
- Requirements: [REQ-COMP-rtbf](../requirements/REQ-COMP-rtbf.md), [REQ-COMP-data-export](../requirements/REQ-COMP-data-export.md)
- Constraints: [CON-gdpr-applies](../constraints/CON-gdpr-applies.md)
