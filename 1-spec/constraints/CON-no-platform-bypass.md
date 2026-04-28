# CON-no-platform-bypass: No circumvention of third-party platform security mechanisms

**Category**: Operational

**Status**: Active

**Source stakeholder**: [STK-message-sender](../stakeholders.md), [STK-ben](../stakeholders.md)

## Description

The system must not contain code, configuration, runbooks, or operational procedures that circumvent or weaken the security mechanisms of any third-party platform from which it ingests data. This includes (non-exhaustively):

- Encryption schemes (E2EE, transport encryption, at-rest encryption)
- Authentication and authorization (login flows, OAuth, 2FA, app-level credentials)
- Session integrity (session tokens, device-binding, multi-device pairing)
- Anti-automation measures (CAPTCHAs, rate limits, bot-detection signals)

Ingestion is restricted to **legitimate, user-driven, transparent paths** — for example: a Web/desktop session the user has explicitly attached, an official multi-device API the platform exposes for this purpose, or a manual export the user has produced and uploaded. Any feature that scrapes credentials, replays tokens, or runs against an account without an explicit user-initiated session is prohibited.

## Rationale

Two reasons. First, ethical and legal: ingesting other people's content via bypassed protections is surveillance regardless of consent records, and exposes Vincent and Ben to ToS, anti-circumvention, and potentially criminal liability. Second, structural: a system that needs to break platform security to function inherits permanent fragility — every protection update breaks ingestion.

## Impact

- WhatsApp ingestion path is constrained to user-attached sessions and/or official APIs. Headless / scripted login flows are out of scope at architecture, design, and implementation review.
- Any proposed feature touching authentication tokens, encryption keys, or session secrets of a third-party platform is rejected during design review and recorded as a `DEC-*` rejection if the proposal recurs.
- Operational runbooks must not document credential-replay, token-extraction, or anti-automation-evasion procedures.
- This constraint informs technology selection: any candidate library or service whose primary value is "bypasses platform protection X" is disqualified.
