"""Canonical replay normalization without weakening raw-byte custody.

The normalizer produces a separate semantic view.  It never changes or
replaces the raw execution record used for custody and forensic review.
"""

from __future__ import annotations

import hashlib
import json
import re
from copy import deepcopy
from typing import Any, Iterable


DEFAULT_VOLATILE_FIELDS = frozenset(
    {
        "actual_start_time",
        "actual_end_time",
        "start_timestamp",
        "end_timestamp",
        "monotonic_duration",
        "operation_id",
        "execution_id",
        "nonce",
        "record_hash",
        "workspace_identity",
        "receipt_hash",
        "semantic_verifier_receipt",
        "order_position",
    }
)

_PATH = re.compile(r"(?:[A-Za-z]:\\|/)(?:[^\s:'\"]+[\\/])+[^\s:'\"]+")
_HEX_ADDRESS = re.compile(r"0x[0-9a-fA-F]+")
_DURATION = re.compile(r"\b\d+(?:\.\d+)?(?:ms|s|sec|seconds)\b", re.IGNORECASE)


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def canonical_hash(value: Any) -> str:
    return hashlib.sha256(canonical_json(value)).hexdigest()


def normalize_text(value: str) -> str:
    """Remove execution-local text while retaining scientific content."""

    text = value.replace("\r\n", "\n").replace("\r", "\n")
    text = _PATH.sub("${RUNTIME_PATH}", text)
    text = _HEX_ADDRESS.sub("0x<ADDRESS>", text)
    text = _DURATION.sub("<DURATION>", text)
    return "\n".join(line.rstrip() for line in text.splitlines()).strip()


def normalize_replay(
    record: Any,
    *,
    volatile_fields: Iterable[str] = DEFAULT_VOLATILE_FIELDS,
) -> Any:
    """Return a deterministic semantic replay projection."""

    volatile = set(volatile_fields)

    def visit(value: Any) -> Any:
        if isinstance(value, dict):
            return {key: visit(item) for key, item in sorted(value.items()) if key not in volatile}
        if isinstance(value, list):
            return [visit(item) for item in value]
        if isinstance(value, tuple):
            return [visit(item) for item in value]
        if isinstance(value, str):
            return normalize_text(value)
        return deepcopy(value)

    return visit(record)


def compare_replays(first: dict[str, Any], second: dict[str, Any]) -> dict[str, Any]:
    """Classify raw and semantic equality independently."""

    raw_first = canonical_hash(first)
    raw_second = canonical_hash(second)
    semantic_first_value = normalize_replay(first)
    semantic_second_value = normalize_replay(second)
    semantic_first = canonical_hash(semantic_first_value)
    semantic_second = canonical_hash(semantic_second_value)
    raw_identical = raw_first == raw_second
    semantically_reproducible = semantic_first == semantic_second
    if raw_identical:
        status = "RAW_IDENTICAL"
    elif semantically_reproducible:
        status = "SEMANTICALLY_REPRODUCIBLE"
    else:
        status = "SEMANTIC_DIVERGENCE"
    return {
        "status": status,
        "raw_identical": raw_identical,
        "semantically_reproducible": semantically_reproducible,
        "raw_hashes": [raw_first, raw_second],
        "semantic_hashes": [semantic_first, semantic_second],
        "authority_allowed": "replay reproducibility classification",
        "authority_forbidden": ["raw evidence replacement", "causal ownership", "patch", "repair count"],
    }
