from __future__ import annotations

import hashlib
from pathlib import Path


def verify_hashes(root: Path, closure: dict[str, object]) -> dict[str, object]:
    expected = closure.get("resolved_hashes", {})
    mismatches = [rel for rel, digest in expected.items()
                  if not (root / rel).is_file() or hashlib.sha256((root / rel).read_bytes()).hexdigest() != digest]
    return {"status": "PASS" if closure.get("status") == "PASS" and not mismatches else "BLOCK",
            "mismatches": mismatches, "verified_file_count": len(expected) - len(mismatches)}
