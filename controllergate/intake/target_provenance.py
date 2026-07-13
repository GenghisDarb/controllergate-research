from __future__ import annotations

from pathlib import Path
from typing import Any

from controllergate.core.evidence import sha256_file


def target_provenance(source_root: Path, path: str, node: str | None = None) -> dict[str, Any]:
    target = source_root / path
    return {
        "status": "PASS" if target.is_file() else "BLOCK",
        "path": path, "node": node, "physically_present": target.is_file(),
        "sha256": sha256_file(target) if target.is_file() else None,
        "source_root": str(source_root.resolve()),
    }
