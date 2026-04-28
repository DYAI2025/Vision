# Stakeholders

Everyone with a stake in the system: those who use it, fund it, maintain it, or are affected by it. Every requirement should trace back to a stakeholder need.

## Influence Levels

- **High** — can approve or veto decisions; priority conflicts resolved in their favor
- **Medium** — consulted during review; concerns addressed but may be overruled
- **Low** — informed of decisions; needs considered but not blocking

## Stakeholder Table

| ID | Role | Description | Interests | Influence |
|----|------|-------------|-----------|-----------|
| STK-vincent | User / Collaborator | Named human collaborator; one of two consented actors driving project work through the system. | Accurate semantic routing of his inputs; trustworthy agent proposals (no silent autonomous writes); low-friction correction loop; ownership and consent control over his sources; privacy of off-topic / personal content. | High |
| STK-ben | User / Collaborator + Operator | Named human collaborator (peer to Vincent) and system operator responsible for deployment, infrastructure, secrets, and ops. | All STK-vincent interests, plus operator concerns: VPS deployability, reproducible builds, healthchecks and structured logs, automated backups with tested restore, simple secret rotation via `.env`, low ops overhead, ability to roll back project state. | High |
| STK-message-sender | Affected Non-User | Person whose WhatsApp / chat / voice content flows through a watched source. Does not interact with the system but is subject to ingestion, classification, and retention. | Explicit consent before ingestion with clear scope; hard retention limits enforced per `retention_class`; off-topic / private content filtered, redacted, or blocked; right to be forgotten on request; no covert surveillance. | Low |

## Tiebreaker Rule (Vincent ↔ Ben)

Both `STK-vincent` and `STK-ben` are `High`-influence. The system is co-owned with no hierarchy between them, so the influence tiebreaker that normally drives conflict resolution is unavailable.

**Rule (consensus required):** any conflict between Vincent and Ben on a Specification, Design, or Code artifact must be resolved between them before the agent acts on the conflicting items. If consensus cannot be reached, the affected proposal or change is **parked** (status held, not silently picked) until they decide. The agent never picks a side and never times out the conflict in either direction.

**Floor:** `STK-message-sender` interests cannot be overruled by Vincent + Ben consensus. Consent, retention, and privacy obligations stand regardless — they are encoded as non-negotiable constraints, not as preferences subject to negotiation.

This rule should be formalized as a decision (e.g., `DEC-stakeholder-tiebreaker-consensus`) before the next conflict-resolution event so that downstream phases reference it consistently.
