from __future__ import annotations

import hashlib
from pathlib import Path


def rollback(path: Path, original: bytes, expected_hash: str) -> dict[str, object]:
    path.write_bytes(original)
    observed = hashlib.sha256(path.read_bytes()).hexdigest()
    return {"status": "ROLLBACK_DRILL_PASSED" if observed == expected_hash else "CANARY_REJECTED",
            "restored_source_hash": observed, "expected_source_hash": expected_hash}
