from __future__ import annotations

from pathlib import Path
from typing import Any

from controllergate.core.evidence import sha256_file


def verify_provider_artifacts(artifacts: list[dict[str, Any]]) -> dict[str, Any]:
    failures: list[str] = []
    for item in artifacts:
        path = Path(str(item.get("path", "")))
        if not path.is_file() or sha256_file(path) != item.get("sha256"):
            failures.append(str(path))
    return {"status": "PASS" if artifacts and not failures else "BLOCK", "verified_artifact_count": len(artifacts) - len(failures), "failures": failures}
