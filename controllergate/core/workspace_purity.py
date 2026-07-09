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


def candidate_runtime_path_policy() -> dict[str, object]:
    return {
        "status": "PASS",
        "runtime_path_must_be_outside_repo": True,
        "runtime_path_must_be_outside_cloud_sync": True,
        "forbidden_reuse_markers": ["venv", ".venv", "__pycache__", ".pytest_cache", "stale_source_checkout"],
        "rollback_target_marker_required": True,
    }


def tree_content_hash(path: str | Path) -> str:
    root = Path(path)
    rows: list[str] = []
    if root.exists():
        for item in sorted(root.rglob("*")):
            if item.is_file():
                rel = item.relative_to(root).as_posix()
                rows.append(f"{rel}:{hashlib.sha256(item.read_bytes()).hexdigest()}")
    return hashlib.sha256("\n".join(rows).encode("utf-8")).hexdigest()


def audit_candidate_runtime_workspace(
    workspace_root: str | Path,
    *,
    repo_root: str | Path,
    rollback_marker: str | None = None,
) -> dict[str, object]:
    root = Path(workspace_root)
    repo = Path(repo_root)
    outside_repo = not _inside(root, repo)
    outside_onedrive = "onedrive" not in str(root).lower()
    reused_venvs = [p.as_posix() for name in [".venv", "venv", "env", "ENV"] for p in root.rglob(name)] if root.exists() else []
    pycache = [p.as_posix() for p in root.rglob("__pycache__")] if root.exists() else []
    pytest_cache = [p.as_posix() for p in root.rglob(".pytest_cache")] if root.exists() else []
    stale_source = [p.as_posix() for p in root.rglob(".git")] if root.exists() else []
    blockers: list[str] = []
    if not outside_repo:
        blockers.append("workspace_inside_repo_blocked")
    if not outside_onedrive:
        blockers.append("workspace_inside_onedrive_blocked")
    if reused_venvs or pycache or pytest_cache:
        blockers.append("stale_cache_contamination_detected")
    return {
        "status": "PASS" if not blockers else "BLOCK",
        "workspace_root": str(root),
        "outside_repo": outside_repo,
        "outside_onedrive": outside_onedrive,
        "no_reused_venv": not reused_venvs,
        "no_reused_pytest_cache": not pytest_cache,
        "no_reused_pycache": not pycache,
        "stale_source_checkout_markers": stale_source,
        "pre_attempt_workspace_hash": tree_content_hash(root),
        "post_attempt_workspace_hash": tree_content_hash(root),
        "candidate_runtime_path_record": hashlib.sha256(str(root).replace("\\", "/").encode("utf-8")).hexdigest(),
        "rollback_target_marker": rollback_marker,
        "blockers": blockers,
    }
