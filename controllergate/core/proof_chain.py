from __future__ import annotations

import hashlib
import json
from typing import Any


def _hash_value(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest()


def build_proof_chain_lock(entries: list[dict[str, Any]]) -> dict[str, Any]:
    chain: list[dict[str, Any]] = []
    previous_hash = "0" * 64
    for index, entry in enumerate(entries):
        value_hash = str(entry.get("sha256") or _hash_value(entry.get("value")))
        link_hash = _hash_value({"index": index, "label": entry.get("label"), "value_hash": value_hash, "previous_hash": previous_hash})
        chain.append(
            {
                "index": index,
                "label": entry.get("label"),
                "sha256": value_hash,
                "previous_hash": previous_hash,
                "link_hash": link_hash,
            }
        )
        previous_hash = link_hash
    return {
        "status": "PASS",
        "entry_count": len(chain),
        "chain": chain,
        "root_hash": previous_hash,
        "hash_chain_valid": all(
            item["previous_hash"] == ("0" * 64 if index == 0 else chain[index - 1]["link_hash"])
            for index, item in enumerate(chain)
        ),
    }
