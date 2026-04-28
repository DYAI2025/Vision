# REQ-F-input-event-normalization: Single normalization layer produces channel-agnostic input events

**Type**: Functional

**Status**: Draft

**Priority**: Must-have

**Source**: [US-ingest-from-any-channel](../user-stories/US-ingest-from-any-channel.md), [CON-consent-required](../constraints/CON-consent-required.md), [CON-no-platform-bypass](../constraints/CON-no-platform-bypass.md)

**Source stakeholder**: [STK-vincent](../stakeholders.md), [STK-ben](../stakeholders.md)

## Description

A single normalization layer (the `whatsorga-ingest` service) takes inputs from any channel-specific adapter and produces an `input_event` of identical shape regardless of channel. Each `input_event` carries:

- `event_id` — stable unique id assigned at normalization
- `source_id` — references the registered consent record
- `actor_id` — resolved from consent record
- `arrived_at` — timestamp of arrival at the normalization layer
- `consent_snapshot` — point-in-time `consent_scope` and `retention_policy` resolved from the source's record (per [REQ-COMP-consent-record](REQ-COMP-consent-record.md))
- `consent_check_result` — `permitted` / `dropped` with reason; events with `dropped` are not propagated downstream
- `content_payload` — raw input content, classified as `raw_30d`
- `channel_metadata` — channel-specific extension fields (declared per adapter); never read by routing or extraction

Channel-specific concerns must not leak past this layer: routing, classification, extraction, and review logic operate only on the shared fields. Adapters implement a defined contract (one input function returning an `input_event` candidate, one consent-check hook, one `channel_metadata` schema declaration). Adding a new channel must not require modifying routing or extraction code.

## Acceptance Criteria

- Given input arriving from any of the four MVP adapters (WhatsApp, voice, repo events, manual CLI), when normalization completes, then the resulting `input_event` validates against one shared JSON schema; no schema variant per channel exists.
- Given a routing or extraction component, when it processes an `input_event`, then it reaches a correct decision without reading `channel_metadata` for any logic outside explicitly declared channel-aware features (verified by static check on read paths).
- Given a hypothetical fifth channel adapter, when it is added by implementing the adapter contract only, then routing, extraction, and review code require no changes for the new channel to function end-to-end.

## Related Constraints

- [CON-consent-required](../constraints/CON-consent-required.md) — consent check happens at normalization, before propagation.
- [CON-no-platform-bypass](../constraints/CON-no-platform-bypass.md) — adapter contracts disallow ingest paths that bypass platform protections.

## Related Assumptions

- [ASM-channel-shape-convergeable](../assumptions/ASM-channel-shape-convergeable.md) — assumes the four MVP channels can converge on one shape.
