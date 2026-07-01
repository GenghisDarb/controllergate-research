from __future__ import annotations

import hashlib
from pathlib import Path


def fresh_workspace_purity_policy() -> dict[str, object]:
    return {
        "status": "PASS",
        "workspace_must_be_outside_repo": True,
        "workspace_must_be_outside_onedrive": True,
        "requires_clean_recreated_root": True,
        "blockers": [
            "workspace_purity_failed",
            "stale_cache_contamination_detected",
            "workspace_inside_repo_blocked",
            "workspace_inside_onedrive_blocked",
        ],
    }


def _inside(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def workspace_root_hash(path: str | Path) -> str:
    return hashlib.sha256(str(Path(path)).replace("\\", "/").encode("utf-8")).hexdigest()


def audit_workspace_purity(
    workspace_root: str | Path | None,
    *,
    repo_root: str | Path,
    seed_present: bool,
    workspace_created: bool = False,
) -> dict[str, object]:
    if not seed_present:
        return {
            "status": "PASS",
            "workspace_purity_status": "READY_NO_SEED",
            "workspace_root": None,
            "workspace_creation_timestamp": "not_created_no_seed",
            "workspace_root_hash": workspace_root_hash("not_created_no_seed"),
            "stale_cache_contamination_count": 0,
            "venv_contamination_count": 0,
            "pycache_contamination_count": 0,
            "pytest_cache_contamination_count": 0,
            "workspace_created": False,
            "blocker": None,
        }
    if workspace_root is None:
        return {"status": "BLOCK", "workspace_purity_status": "MISSING", "blocker": "workspace_purity_failed"}
    root = Path(workspace_root)
    repo = Path(repo_root)
    if _inside(root, repo):
        return {"status": "BLOCK", "workspace_purity_status": "BLOCK", "workspace_root": str(root), "blocker": "workspace_inside_repo_blocked"}
    if "onedrive" in str(root).lower():
        return {"status": "BLOCK", "workspace_purity_status": "BLOCK", "workspace_root": str(root), "blocker": "workspace_inside_onedrive_blocked"}
    pycache = list(root.rglob("__pycache__")) if root.exists() else []
    pytest_cache = list(root.rglob(".pytest_cache")) if root.exists() else []
    venv = [path for name in [".venv", "venv", "env", "ENV"] for path in root.rglob(name)] if root.exists() else []
    stale = pycache + pytest_cache + venv
    blocker = "stale_cache_contamination_detected" if stale else None
    return {
        "status": "BLOCK" if stale else "PASS",
        "workspace_purity_status": "BLOCK" if stale else "PASS",
        "workspace_root": str(root),
        "workspace_creation_timestamp": "created" if workspace_created else "not_created",
        "workspace_root_hash": workspace_root_hash(root),
        "stale_cache_contamination_count": len(stale),
        "venv_contamination_count": len(venv),
        "pycache_contamination_count": len(pycache),
        "pytest_cache_contamination_count": len(pytest_cache),
        "workspace_created": workspace_created,
        "blocker": blocker,
    }
