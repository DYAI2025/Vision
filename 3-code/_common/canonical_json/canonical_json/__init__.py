"""RFC 8785 canonical JSON serialization.

The audit hash chain hashes a stable digest of the event payload (see
`DEC-hash-chain-over-payload-hash`). For that digest to be reproducible after
a round-trip through Postgres `jsonb` (which does not preserve key order or
insignificant whitespace), the canonical form must be deterministic: keys
sorted lexicographically, no insignificant whitespace, no platform-dependent
number formatting, no NaN/Infinity (which JSON does not define).

This module implements the JSON Canonicalization Scheme (JCS) per RFC 8785
to the extent the audit chain requires:

- object keys sorted by their UTF-16 code-unit order (Python's default
  string ordering is UTF-16/UCS-4-aware enough for ASCII keys; the project's
  payload schemas use ASCII-only keys per `data-model.md`)
- no whitespace between tokens
- UTF-8 output
- NaN / Infinity / -Infinity rejected
- duplicate object keys rejected at the input layer (Python dicts make this
  structurally impossible; nothing extra to do)

The function returns `bytes` (UTF-8) so callers can hash the output directly
without an extra encode step. A convenience `canonical_json_str` returns the
text form for callers that want to log or compare strings.
"""

from __future__ import annotations

import json
from typing import Any

__all__ = ["canonical_json", "canonical_json_str"]


def canonical_json(value: Any) -> bytes:
    """Serialize ``value`` to canonical JSON (RFC 8785-style) UTF-8 bytes.

    Raises ``ValueError`` on NaN, Infinity, or -Infinity (JSON has no
    representation for these and the audit chain must not silently accept
    non-deterministic inputs). Raises ``TypeError`` on values not JSON-
    representable (sets, bytes, datetimes, etc.) — callers must convert to
    JSON-native types upstream.
    """
    return canonical_json_str(value).encode("utf-8")


def canonical_json_str(value: Any) -> str:
    """Serialize ``value`` to canonical JSON text.

    See :func:`canonical_json` for the contract.
    """
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    )
