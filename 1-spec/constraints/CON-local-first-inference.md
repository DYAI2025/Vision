# CON-local-first-inference: Default-local model inference, opt-in remote with audit

**Category**: Technical

**Status**: Active

**Source stakeholder**: [STK-ben](../stakeholders.md), [STK-message-sender](../stakeholders.md)

## Description

Default model inference (LLM calls, embeddings, transcription) runs locally via Ollama with a Gemma-family model. The system must run end-to-end with no remote LLM dependency and no remote embedding dependency.

Remote inference is permitted **only as an explicit per-task opt-in by the operator (Ben)**, and only when **all** of the following hold:

- The calling tool / skill is on a named "remote-allowed" list in the operator's deployment configuration.
- The data class being sent (raw input vs. derived artifact vs. metadata-only) is permitted by the same configuration.
- The source's `consent_scope` includes `remote_inference_allowed: true` (default false) — see [CON-consent-required](CON-consent-required.md).
- The remote call is audited with: caller (skill/tool), data class, source `consent_scope`, model identifier, operator approval reference (which config flipped it on, when).

No remote inference path is enabled by default. Defaults must be set such that a freshly deployed system has zero remote calls regardless of network configuration. Remote inference may not be used for content from sources that lack `remote_inference_allowed` consent — including for "metadata-only" calls if those calls would leak content via the prompt.

## Rationale

Two motivations. First, privacy posture: data minimization at the network boundary is more enforceable than data minimization inside the agent runtime. Sending content to a third-party model provider creates a data flow that's hard to audit and hard to revoke; making remote inference an explicit, named, audited exception preserves the audit story. Second, vendor independence: a hard cloud-LLM dependency creates a single point of operational and commercial failure that the rest of the architecture is specifically designed to avoid.

The opt-in carve-out exists because some tasks (high-quality transcription of long voice memos, niche multilingual cases) genuinely benefit from cloud models, and forbidding them outright would push Ben to build a separate workaround pipeline outside the system's audit surface — a worse outcome.

## Impact

- Hermes runtime must support a model-routing layer with default-local + named-remote profiles.
- `consent_scope` schema (CON-consent-required) must include `remote_inference_allowed: bool`, defaulting to `false`.
- Audit-log schema must distinguish local vs. remote inference, with the remote-call fields above.
- Drives a deployment configuration item: `remote_inference_profiles` (list of named profiles, each with allowed callers / data classes / model endpoints), default empty.
- Drives an operator runbook: how to add and revoke a remote profile, and how to verify no source consent silently inherits an opened profile.
- Embedding model and transcription model must be selectable as local-first defaults; remote alternatives are only candidates if the local default also exists.
