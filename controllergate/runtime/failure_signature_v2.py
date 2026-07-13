from __future__ import annotations

import hashlib
import re
from typing import Any

EMPTY_OUTPUT_HASH = hashlib.sha256(b"").hexdigest()


def normalize_failure_output(text: str) -> str:
    value = text.replace("\r\n", "\n").strip()
    value = re.sub(r"(?:[A-Za-z]:)?[/\\](?:[^\s:]+[/\\])+", "<path>/", value)
    value = re.sub(r"\b0x[0-9a-fA-F]+\b", "<address>", value)
    value = re.sub(r"\b\d+(?:\.\d+)?s\b", "<duration>", value)
    value = re.sub(r"\n{3,}", "\n\n", value)
    return value


def semantic_failure_signature(text: str, *, target: str, ownership_events: list[str] | None = None) -> dict[str, Any]:
    normalized = normalize_failure_output(text)
    raw_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
    if not normalized:
        return {
            "status": "REJECTED_EMPTY_OUTPUT",
            "raw_output_sha256": raw_hash,
            "normalized_output_sha256": EMPTY_OUTPUT_HASH,
            "semantic_failure_signature": None,
            "signature_label": "EMPTY_OUTPUT_HASH",
            "target": target,
            "ownership_events": ownership_events or [],
        }
    payload = "\n".join([target, normalized, *(ownership_events or [])])
    return {
        "status": "PASS",
        "raw_output_sha256": raw_hash,
        "normalized_output_sha256": hashlib.sha256(normalized.encode("utf-8")).hexdigest(),
        "semantic_failure_signature": hashlib.sha256(payload.encode("utf-8")).hexdigest(),
        "signature_label": "NONEMPTY_SEMANTIC_FAILURE_SIGNATURE",
        "target": target,
        "ownership_events": ownership_events or [],
    }
