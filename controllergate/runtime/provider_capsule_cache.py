from __future__ import annotations

from pathlib import Path
from typing import Any

from controllergate.core.evidence import sha256_file


def verify_provider_bytes(root: Path, artifacts: list[dict[str, Any]]) -> dict[str, Any]:
    records = []
    for artifact in artifacts:
        path = root / str(artifact.get("filename", ""))
        actual = sha256_file(path) if path.is_file() else None
        records.append({"filename": artifact.get("filename"), "expected_sha256": artifact.get("sha256"), "observed_sha256": actual, "verified": actual == artifact.get("sha256")})
    return {"status": "PASS" if records and all(item["verified"] for item in records) else "BLOCK", "records": records, "cache_is_temporary": True}
