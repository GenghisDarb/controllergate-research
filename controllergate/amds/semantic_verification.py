from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Callable


def verify_semantic_claim(probe: dict[str, Any], observation: dict[str, Any], recompute: Callable[[], dict[str, Any]] | None = None) -> dict[str, Any]:
    claim = observation.get("semantic_claim")
    if recompute is not None:
        result = recompute()
        passed = result.get("status") == "PASS" and result.get("semantic_claim") == claim
        return {"status": "PASS" if passed else "BLOCK", "recomputed": True, "claimed": claim, "observed": result.get("semantic_claim"), "evidence_hash": result.get("evidence_hash")}
    path = observation.get("semantic_source_path")
    expected = observation.get("semantic_source_sha256")
    if path and expected:
        target = Path(path)
        digest = hashlib.sha256(target.read_bytes()).hexdigest() if target.is_file() else None
        return {"status": "PASS" if digest == expected else "BLOCK", "recomputed": True, "claimed": claim, "observed_sha256": digest}
    return {"status": "NOT_ESTABLISHED", "recomputed": False, "claimed": claim, "reason": "semantic_recomputation_adapter_not_registered"}
