# CON-gdpr-applies: System processes personal data within scope of EU GDPR

**Category**: Operational

**Status**: Active

**Source stakeholder**: [STK-message-sender](../stakeholders.md), [STK-vincent](../stakeholders.md), [STK-ben](../stakeholders.md)

## Description

The system processes personal data (chat messages, voice content, identifiable references to natural persons) and is therefore in scope of the **EU General Data Protection Regulation (Regulation (EU) 2016/679, GDPR)**.

**Lawful basis.** Processing relies on **consent** under Art. 6(1)(a). Consent is recorded per source ([CON-consent-required](CON-consent-required.md)), is purpose-scoped (`consent_scope`), is freely revocable, and may not be assumed from inactivity, defaults, or platform-level relationships.

**Data subject rights** must be supported operationally for the lifetime of any data the system retains, without manual database surgery:

- **Access** (Art. 15) — produce a per-subject export of all stored data.
- **Rectification** (Art. 16) — correct inaccuracies on request.
- **Erasure / Right to be forgotten** (Art. 17) — delete a subject's data across all storage layers, subject to the retention floor in [CON-tiered-retention](CON-tiered-retention.md).
- **Restriction** (Art. 18) — mark a subject's data as locked from further processing without deleting.
- **Portability** (Art. 20) — provide an export in a machine-readable format.

**Purpose limitation and data minimization** apply at every layer: components may only access data fields necessary for their task; raw content beyond a derived artifact's needs must not be carried forward through processing chains.

The system makes **no claim** of GDPR certification or formal DPO appointment; this constraint defines the operational floor, not a compliance attestation. If commercial use is added later, a separate review is required.

## Rationale

Makes the regulatory regime explicit so downstream requirements (`REQ-COMP-*`, `REQ-SEC-*`) have a concrete legal anchor. Without an explicit constraint, "we do GDPR things" devolves into ad-hoc privacy hacks that are neither verifiable nor defensible.

The named legal basis (consent, not legitimate-interest) closes the door on creep — features that would require a legitimate-interest argument are out of scope unless this constraint is amended.

## Impact

- Drives explicit `REQ-COMP-*` requirements: `REQ-COMP-consent-record` (consent is recorded, scoped, revocable), `REQ-COMP-rtbf` (subject erasure end-to-end), `REQ-COMP-data-export` (subject access + portability), `REQ-COMP-purpose-limitation` (per-component purpose declarations enforced).
- Drives `REQ-SEC-*` requirements around audit-log integrity, retention sweep correctness, and access control to subject data.
- Architectural impact: data subject queries need a per-subject index that spans Backlog-Core events, GBrain pages, Kanban cards, and any raw-content cache. This is non-trivial — it forces a subject-keyed lookup in every storage layer.
- Operational runbooks: a documented procedure for handling each Art. 15–20 request, with a target response window.
- Pairs with [CON-tiered-retention](CON-tiered-retention.md) (retention as data minimization), [CON-consent-required](CON-consent-required.md) (lawful basis), [CON-gbrain-no-raw-private-truth](CON-gbrain-no-raw-private-truth.md) (minimization in the durable layer), and [CON-local-first-inference](CON-local-first-inference.md) (data flow boundary).
