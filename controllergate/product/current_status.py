from __future__ import annotations

from pathlib import Path


def status_document(repo_root: str | Path) -> dict[str, object]:
    path = Path(repo_root) / "docs" / "CURRENT_STATUS.md"
    return {"status": "PASS" if path.is_file() else "BLOCK", "path": str(path),
            "bytes": path.stat().st_size if path.is_file() else 0}
