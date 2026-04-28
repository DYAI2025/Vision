# US-ingest-from-any-channel: Capture project work from any consented channel without changing tools

**As a** collaborator, **I want** any consented input channel I use (WhatsApp, voice memo, repository event, manual CLI entry) to flow through the same routing pipeline, **so that** project work is captured wherever it happens without me having to remember which tool it should go in.

**Status**: Draft

**Priority**: Must-have

**Source stakeholder**: [STK-vincent](../stakeholders.md), [STK-ben](../stakeholders.md)

**Related goal**: [GOAL-multi-source-project-ingestion](../goals/GOAL-multi-source-project-ingestion.md)

## Acceptance Criteria

- Given a consented source on any of the four MVP channels, when content arrives via that channel, then it produces an `input_event` through the WhatsOrga normalization path with consistent shape and metadata regardless of channel.
- Given an `input_event` whose confidence and consent permit autonomous routing, when classification completes, then the event is assigned to the correct project and an artifact extraction pass runs in the same processing cycle.

## Derived Requirements

- [REQ-F-input-event-normalization](../requirements/REQ-F-input-event-normalization.md)
- [REQ-F-project-routing](../requirements/REQ-F-project-routing.md)
- [REQ-PERF-ingest-latency](../requirements/REQ-PERF-ingest-latency.md)
