# DEC-platform-bypass-review-checklist: Trail

> Companion to `DEC-platform-bypass-review-checklist.md`.

## Alternatives considered

### Option A: Explicit reviewer checklist (chosen)
- Pros: Concrete and reviewable; makes the prohibition operationally enforceable; can be referenced from PR descriptions.
- Cons: Lists are never fully exhaustive — reviewers must still apply judgment to analogues; the checklist needs upkeep as platforms evolve.

### Option B: Leave the constraint as-is, rely on case-by-case reviewer judgment
- Pros: No upkeep; flexibility per case.
- Cons: Inconsistent enforcement; new reviewers don't have prior cases to draw on; the prohibition risks becoming theatrical.

### Option C: Automated lint that blocks specific imports / call patterns
- Pros: Hard enforcement at code-review time.
- Cons: Many bypass patterns are not detectable from imports alone (e.g., a script that does headless login could use generic libraries); creates a false sense of completeness; brittle to refactors.

## Reasoning

Option A was chosen because the prohibition is fundamentally about intent and shape of features, which lint can't fully capture; an explicit checklist gives reviewers and contributors a shared reference. Option C remains available as a *complement* — lint can catch a subset of patterns — but is not a substitute. Option B was rejected on the inconsistent-enforcement risk: without a written checklist, the prohibition tends to dilute over time.

## Human involvement

**Type**: ai-proposed/human-approved

**Notes**: Proposed during the architecture-design session (2026-04-27) as the resolution to gap-analysis finding M-1; user approved the architecture proposal which embedded this commitment.

## Changelog

| Date | Change | Involvement |
|------|--------|-------------|
| 2026-04-27 | Initial decision; checklist seeded from `CON-no-platform-bypass`'s description | ai-proposed/human-approved |
