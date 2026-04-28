# DEC-platform-bypass-review-checklist: Reviewer checklist of patterns rejected as platform-protection bypass

**Status**: Active

**Category**: Process

**Scope**: system-wide (Design + Code reviews touching ingestion paths)

**Source**: [CON-no-platform-bypass](../1-spec/constraints/CON-no-platform-bypass.md); gap-analysis finding M-1 (2026-04-27)

**Last updated**: 2026-04-27

## Context

`CON-no-platform-bypass` is a prohibition: features that circumvent third-party platform security mechanisms (encryption, login, 2FA, session integrity, anti-automation) are not allowed. Unlike obligation-shaped constraints, prohibitions don't generate verifiable acceptance criteria — they are enforced by reviewer judgment. Without an explicit checklist of rejected patterns, the prohibition gets interpreted unevenly across reviews.

Gap-analysis finding M-1 (2026-04-27) identified the missing review checklist as a Minor finding to be addressed in the Design phase. This decision closes that finding.

## Decision

A reviewer checklist documents the patterns that constitute "platform-protection bypass" and must be rejected in Design and Code review. The checklist is authoritative for `CON-no-platform-bypass` enforcement.

### Rejected patterns (non-exhaustive — reviewers should flag analogues)

1. **Credential extraction from a platform's session or local storage** beyond what the user explicitly provided (e.g., reading WhatsApp Web's IndexedDB to harvest tokens).
2. **Replay of session tokens or auth cookies** outside an interactive user-attached session.
3. **Headless / scripted login automation** that runs without a real user-attached session (e.g., Puppeteer / Playwright scripts that submit credentials).
4. **Anti-bot / CAPTCHA evasion** mechanisms (proxy rotation, fingerprint randomization, CAPTCHA-solving services).
5. **Encryption-protocol-level access** that bypasses the platform's E2EE design (e.g., extracting Signal-protocol keys for offline decryption).
6. **2FA / multi-device enrollment automation** without explicit per-event user authorization.
7. **Anti-detection patterns** like emulating human typing rhythms, randomized session fingerprints, or actions explicitly designed to evade platform anti-automation telemetry.
8. **Multi-account session sharing** that lets one device act on behalf of another's session without user authorization.

### Acceptable patterns (positive list of legitimate ingestion paths)

- A WhatsApp Web/desktop session attached by the user explicitly inside the system's UX (user clicks "attach session," confirms each step).
- An official multi-device API the platform exposes for this purpose, used as documented.
- A user-produced manual export uploaded into the system (chat history JSON, etc.).
- A user-controlled webhook the user has registered themselves with the platform.

## Enforcement

### Trigger conditions

- **Design phase**: any design that touches `whatsorga-ingest` adapters or any new channel adapter must be reviewed against this checklist before approval.
- **Code phase**: any pull request that touches an ingestion adapter, an authentication path, or a credential-handling code path must be reviewed against this checklist; reviewers explicitly cite the checklist in the review comment.

### Required checks

1. Reviewer reads the checklist before approving any change to ingestion code.
2. Reviewer rejects (and documents the rejection rationale) any change matching a rejected pattern.
3. New rejected patterns discovered through review experience are added to this decision via a documented update; the changelog in `*.history.md` is appended for each addition.

### Prohibited patterns

(See "Rejected patterns" above. Adding a feature that matches any pattern requires superseding this decision with explicit rationale.)

## Reconsider trigger

Revisit this decision if:

- A platform changes its terms or APIs in a way that makes a previously-rejected pattern explicitly allowed (e.g., publishes an official multi-device API where there wasn't one).
- A new platform is added as an ingestion source — review which patterns apply differently to that platform.
