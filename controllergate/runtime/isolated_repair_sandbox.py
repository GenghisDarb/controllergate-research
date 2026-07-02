from __future__ import annotations

import hashlib
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _inside(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def validate_sandbox_path(path: str | Path, repo_root: str | Path) -> dict[str, Any]:
    sandbox = Path(path)
    repo = Path(repo_root)
    parts = [part.lower() for part in sandbox.resolve().parts]
    contamination = [name for name in ["__pycache__", ".pytest_cache", ".venv", "venv"] if (sandbox / name).exists()]
    valid = not _inside(sandbox, repo) and "onedrive" not in parts and not contamination
    return {
        "status": "PASS" if valid else "BLOCK",
        "sandbox_path": str(sandbox),
        "outside_repo": not _inside(sandbox, repo),
        "outside_onedrive": "onedrive" not in parts,
        "contamination": contamination,
        "blocker": None if valid else "sandbox_path_or_contamination_invalid",
    }


def create_ephemeral_sandbox(repo_root: str | Path, prefix: str = "controllergate_batch015_") -> dict[str, Any]:
    root = Path(tempfile.mkdtemp(prefix=prefix))
    marker = root / "SANDBOX_READY.txt"
    marker.write_text("sandbox ready\n", encoding="utf-8", newline="\n")
    validation = validate_sandbox_path(root, repo_root)
    digest = hashlib.sha256(marker.read_bytes()).hexdigest()
    return {
        **validation,
        "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "sandbox_root_hash": digest,
        "committable": False,
    }
