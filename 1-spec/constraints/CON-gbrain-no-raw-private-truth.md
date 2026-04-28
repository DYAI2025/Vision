# CON-gbrain-no-raw-private-truth: GBrain stores derived artifacts, not durable raw content

**Category**: Operational

**Status**: Active

**Source stakeholder**: [STK-message-sender](../stakeholders.md), [STK-vincent](../stakeholders.md), [STK-ben](../stakeholders.md)

## Description

GBrain is a durable artifact store, not a raw-data archive. It is the **human-readable** semantic layer of the system, and it must not be used to circumvent the retention model.

GBrain may persist:

- Project artifacts (`PROJECT.md`, `PROFILE.md`, `CURRENT_STATE.md`, etc.)
- Summaries of episodes, conversations, voice content
- Decisions and their rationale
- Learnings (corrections, routing improvements, agent-behavior signals)
- References to source material (source ids, retention-class-bounded pointers, redacted excerpts)

GBrain may **not** persist as durable truth:

- Full message bodies
- Full voice transcripts
- Full repo event payloads
- Any other raw input content beyond what the source's retention class permits

Raw content may appear in GBrain only inside a `raw_30d`-classed envelope that the retention sweep can prune at age 30 days. Everything else stored in GBrain must be `derived_keep`. The `gbrain-memory-write` tool must reject any write whose claimed `retention_class` is `derived_keep` but whose payload contains raw content — the redaction step must run before the write.

## Rationale

Without this rule, the human-readable vault becomes a covert long-term archive of raw inputs — a 30-day delete on `raw_30d` content in `backlog-core` is meaningless if a copy lives forever in GBrain. The privacy posture and the retention model only hold if the durable layer is structurally incapable of being a side-channel.

GBrain is also the layer most likely to be opened in Obsidian and shared (screenshots, exports, vault sync). Constraining it to derived content keeps casual sharing safe and matches the layer's intended use as project memory.

## Impact

- GBrain page schemas carry `retention_class` in frontmatter. The schema rejects pages without it.
- `gbrain-memory-write` validates: payload type vs. claimed retention class, redaction precondition, source consent scope. Drives a `REQ-F-gbrain-write-validation` requirement.
- Drives a `REQ-SEC-redaction-precondition` requirement: WhatsOrga / voice-ingest / repo-ingest must produce derived artifacts (not just raw events) before content reaches GBrain.
- Pairs with [CON-tiered-retention](CON-tiered-retention.md) (defines the classes) and [CON-consent-required](CON-consent-required.md) (defines the scopes that gate what can be derived).
- Has audit implications: a sweep over GBrain looking for raw content masquerading as derived is a periodic safety check ([REQ-MNT-vault-audit-sweep], to be derived).
