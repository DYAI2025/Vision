# canonical_json

Cross-cutting RFC 8785-style canonical JSON serialization helper for `project-agent-system`. Lives under `3-code/_common/` per [`DEC-shared-utility-path-deps`](../../../decisions/DEC-shared-utility-path-deps.md); consumed via uv path-dep by every backend component that needs to compute `payload_hash` per [`DEC-hash-chain-over-payload-hash`](../../../decisions/DEC-hash-chain-over-payload-hash.md).

## Public surface

```python
from canonical_json import canonical_json, canonical_json_str

canonical_json({"b": 2, "a": 1})       # b'{"a":1,"b":2}'
canonical_json_str({"b": 2, "a": 1})   # '{"a":1,"b":2}'
```

- `canonical_json(value) -> bytes` — UTF-8 encoded canonical form. Use this directly as input to `hashlib.sha256(...)` for `payload_hash`.
- `canonical_json_str(value) -> str` — same content as text; for logging or string comparison.

## Properties guaranteed

- Object keys sorted lexicographically at every nesting level.
- No whitespace between tokens.
- UTF-8 encoded; non-ASCII characters emitted as raw UTF-8 bytes (not `\uXXXX` escapes).
- `NaN`, `+Infinity`, `-Infinity` raise `ValueError` — JSON has no representation for these and the audit chain must not silently accept non-deterministic input.
- Non-JSON-native types (sets, bytes, datetimes, custom classes) raise `TypeError` — callers must convert upstream.
- Arrays preserve element order (only **object keys** are sorted).

## Why this exists

The audit chain hashes `SHA-256(canonical_json(payload))` once at INSERT and stores the result as `payload_hash`. The chain math reads `payload_hash`, never `payload` directly — so retention sweep and RTBF cascade can redact the payload column without breaking the chain (see `DEC-hash-chain-over-payload-hash`).

For that to work, two events with the same logical payload but different key insertion order **must** produce the same digest. Python's `dict` preserves insertion order, so a naive `json.dumps` would produce different bytes for `{"a": 1, "b": 2}` and `{"b": 2, "a": 1}`. This helper enforces a canonical form so the digest is reproducible.

## Layout

```
.
├── pyproject.toml             # canonical-json package, uv-managed
├── uv.lock                    # committed lockfile
├── .python-version            # 3.12
├── canonical_json/            # importable package
│   └── __init__.py            # public surface
├── tests/                     # pytest suite — round-trip + edge cases
│   ├── __init__.py
│   └── test_canonical_json.py
├── README.md
└── .gitignore
```

## Local development

```bash
cd 3-code/_common/canonical_json
uv sync --frozen
uv run --frozen ruff check .
uv run --frozen mypy canonical_json
uv run --frozen pytest -q
```

## CI

Per-package CI job `_common-canonical-json-test` mirrors the per-component pattern: `uv sync --frozen` → ruff → mypy strict → pytest.

## Consumed by

- `whatsorga-ingest` (input event normalization → emits to `backlog-core`)
- `hermes-runtime` (proposal payload hashing)
- `backlog-core` (event-emit primitive — primary consumer)
- `gbrain-bridge` (page-write payload hashing)
- `kanban-sync` (card-write payload hashing)

Each consumer declares the path-dep in its `pyproject.toml`:

```toml
[project]
dependencies = [
    "canonical-json",
]

[tool.uv.sources]
canonical-json = { path = "../_common/canonical_json", editable = true }
```

Each consumer's Dockerfile uses the **repo root** as build context and copies both the component dir and `3-code/_common/` into the builder stage so `uv sync --frozen` can resolve the relative path.

## Change policy

This package is part of the audit-chain trust boundary. Changes to the serialization function require:

1. A test demonstrating that existing `payload_hash` values remain stable (or a documented, intentional break with a migration plan in the consuming `DEC-hash-chain-over-payload-hash.history.md`).
2. Lockstep updates across all five consumers in the same commit.
3. CI green on the `_common-canonical-json-test` job and on every consuming `<component>-test` job.
