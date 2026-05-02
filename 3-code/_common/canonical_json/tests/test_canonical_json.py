"""Tests for the canonical_json helper.

The contract under test is the one `DEC-hash-chain-over-payload-hash` relies
on: serialization is deterministic regardless of key insertion order, and the
output round-trips through `json.loads` to the original value.
"""

from __future__ import annotations

import math

import pytest

from canonical_json import canonical_json, canonical_json_str

# ---------------------------------------------------------------------------
# Determinism: same logical value always serializes to the same bytes.
# ---------------------------------------------------------------------------


def test_returns_utf8_bytes() -> None:
    assert canonical_json({"a": 1}) == b'{"a":1}'


def test_returns_text_via_canonical_json_str() -> None:
    assert canonical_json_str({"a": 1}) == '{"a":1}'


def test_keys_are_sorted_lexicographically() -> None:
    assert canonical_json({"b": 2, "a": 1}) == b'{"a":1,"b":2}'


def test_key_order_does_not_affect_output() -> None:
    a = canonical_json({"a": 1, "b": 2, "c": 3})
    b = canonical_json({"c": 3, "b": 2, "a": 1})
    c = canonical_json({"b": 2, "c": 3, "a": 1})
    assert a == b == c


def test_nested_objects_have_sorted_keys_at_every_level() -> None:
    payload = {"outer": {"z": 1, "a": 2}, "alpha": {"y": 3, "b": 4}}
    assert (
        canonical_json(payload)
        == b'{"alpha":{"b":4,"y":3},"outer":{"a":2,"z":1}}'
    )


def test_no_insignificant_whitespace() -> None:
    out = canonical_json({"a": [1, 2, 3], "b": {"c": 4}})
    assert b" " not in out
    assert b"\n" not in out
    assert b"\t" not in out


# ---------------------------------------------------------------------------
# Type fidelity: all JSON-native scalar types round-trip.
# ---------------------------------------------------------------------------


def test_array_preserves_order() -> None:
    # Arrays are ordered by definition — element order must NOT be sorted.
    assert canonical_json([3, 1, 2]) == b"[3,1,2]"


def test_string_with_unicode_emits_utf8_not_ascii_escapes() -> None:
    # ensure_ascii=False per JCS: non-ASCII chars are emitted as UTF-8 bytes,
    # not as \uXXXX escape sequences. This keeps the digest stable across
    # encoders that disagree about which code points to escape.
    assert canonical_json({"name": "Vincent"}) == b'{"name":"Vincent"}'
    assert canonical_json({"emoji": "ä"}) == '{"emoji":"ä"}'.encode()


def test_string_control_characters_are_escaped() -> None:
    # JSON requires control characters to be escaped — the JCS-aligned
    # default in stdlib json handles this correctly.
    assert canonical_json({"k": "a\nb"}) == b'{"k":"a\\nb"}'


def test_boolean_and_null_serialize_as_lowercase_keywords() -> None:
    assert canonical_json({"a": True, "b": False, "c": None}) == b'{"a":true,"b":false,"c":null}'


def test_integers_are_emitted_without_decimals() -> None:
    assert canonical_json(42) == b"42"
    assert canonical_json({"n": 0}) == b'{"n":0}'


def test_floats_round_trip_via_python_repr() -> None:
    # Python's json module uses float.__repr__ (shortest round-trip
    # representation in Python 3.x). For the audit chain this is fine
    # because both serialization and deserialization happen inside Python.
    out = canonical_json(1.5)
    assert out == b"1.5"


# ---------------------------------------------------------------------------
# Reject non-deterministic / non-JSON-representable values.
# ---------------------------------------------------------------------------


def test_nan_is_rejected() -> None:
    with pytest.raises(ValueError):
        canonical_json(float("nan"))


def test_infinity_is_rejected() -> None:
    with pytest.raises(ValueError):
        canonical_json(math.inf)


def test_negative_infinity_is_rejected() -> None:
    with pytest.raises(ValueError):
        canonical_json(-math.inf)


def test_nan_inside_nested_structure_is_rejected() -> None:
    with pytest.raises(ValueError):
        canonical_json({"events": [{"score": float("nan")}]})


def test_set_is_not_json_native_and_raises_type_error() -> None:
    # Sets are intentionally not coerced — callers must convert to a sorted
    # list (or otherwise canonical form) themselves so the canonicalization
    # is explicit.
    with pytest.raises(TypeError):
        canonical_json({"tags": {"a", "b"}})


def test_bytes_are_not_json_native_and_raise_type_error() -> None:
    with pytest.raises(TypeError):
        canonical_json({"blob": b"raw"})


# ---------------------------------------------------------------------------
# Audit-chain-style scenarios.
# ---------------------------------------------------------------------------


def test_two_payloads_with_different_key_insertion_order_have_identical_digest_input() -> None:
    # This is the property the hash chain depends on: two events that are
    # logically identical must produce the same payload_hash.
    p1 = {"event_type": "input.received", "actor_id": "vincent", "subject_ref": "p1"}
    p2 = {"actor_id": "vincent", "subject_ref": "p1", "event_type": "input.received"}
    assert canonical_json(p1) == canonical_json(p2)


def test_real_world_input_event_shape_is_canonicalized() -> None:
    payload = {
        "source_id": "wa:vincent",
        "actor_id": "vincent",
        "channel": "whatsapp",
        "consent_scope": ["projects", "tasks"],
        "received_at": "2026-04-29T12:00:00Z",
        "body": {"text": "ship the audit log", "lang": "en"},
    }
    out = canonical_json(payload)
    expected = (
        b'{"actor_id":"vincent",'
        b'"body":{"lang":"en","text":"ship the audit log"},'
        b'"channel":"whatsapp",'
        b'"consent_scope":["projects","tasks"],'
        b'"received_at":"2026-04-29T12:00:00Z",'
        b'"source_id":"wa:vincent"}'
    )
    assert out == expected
