# ASM-channel-shape-convergeable: WhatsApp / voice / repo / manual CLI inputs can normalize into one shared `input_event` shape

**Category**: Technology

**Status**: Unverified

**Risk if wrong**: Medium — if false, the four channels' adapters cannot fully converge on one schema, and channel-specific concerns will leak into routing or extraction code. The remediation is bounded: routing and extraction would gain channel branches, the adapter contract would lose its strong "one shape" guarantee, and adding new channels would require touching more layers. Not architecture-breaking, but it weakens the maintainability and portability story and increases the surface area for channel-specific bugs.

## Statement

The four MVP input channels (WhatsApp messages, voice transcripts, repository events, manual CLI entries) can be normalized into one identically-shaped `input_event` schema, with channel-specific concerns confined to a `channel_metadata` extension field that downstream layers (routing, extraction, review) do not need to read for their primary logic. The four channels' metadata vocabularies are limited enough that a single extensible scheme works at MVP scale, without requiring downstream layers to special-case any channel.

## Rationale

The four channels share more than they differ: each produces a content payload, a sender identity, a timestamp, and a small amount of channel-specific context. The system's downstream operations (route to project, extract artifacts, dedupe, route through gate) operate on the content + sender + project context, not on channel mechanics. This is the same shape that worked for similar normalization layers in adjacent products (chat-to-ticket pipelines, multi-channel inboxes).

The risk concentrates in two places: (1) WhatsApp's threading and quote semantics may want to surface to extraction (e.g., "is this a reply to last week's thread?") in ways that other channels don't have an analog for, requiring a channel-specific signal that downstream code has to read; (2) voice transcripts carry confidence-of-transcription that influences confidence-of-routing, which could couple channel back into routing.

## Verification Plan

- **During Design phase:** sketch one realistic `input_event` example per channel and prove on paper (or in a prototype `input_event` validator) that routing and extraction prototypes operate on them identically except for declared `channel_metadata` reads. If reply-threading or transcription-confidence force routing/extraction to consult `channel_metadata`, capture that as either an `input_event` schema extension or a `DEC-input-event-shape` decision.
- **During Code phase:** before the second channel adapter is implemented, run a "swap-test" — implement adapter A and adapter B, then verify that switching between the two requires no changes to routing or extraction code. If the swap-test fails, the assumption is invalidated.
- **Trigger for re-verification:** any new channel added beyond the four MVP channels; any change that introduces channel-specific routing logic.

## Related Artifacts

- Goals: [GOAL-multi-source-project-ingestion](../goals/GOAL-multi-source-project-ingestion.md)
- Requirements: [REQ-F-input-event-normalization](../requirements/REQ-F-input-event-normalization.md), [REQ-PERF-ingest-latency](../requirements/REQ-PERF-ingest-latency.md)
- Constraints: [CON-no-platform-bypass](../constraints/CON-no-platform-bypass.md)
