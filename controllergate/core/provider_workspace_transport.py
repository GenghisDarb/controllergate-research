from __future__ import annotations

import shutil
import tempfile
from pathlib import Path
from typing import Any

from .evidence import sha256_file


def create_provider_workspace(repo_root: str | Path) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    workspace = Path(tempfile.mkdtemp(prefix="controllergate-provider-batch024-")).resolve()
    outside_repo = root not in workspace.parents and workspace != root
    return {
        "status": "PASS" if outside_repo else "BLOCK",
        "workspace_path": str(workspace),
        "outside_live_repo": outside_repo,
        "outside_onedrive": "onedrive" not in str(workspace).lower(),
        "blocker": None if outside_repo else "provider_workspace_transport_unverified",
    }


def cleanup_provider_workspace(workspace_path: str | Path) -> dict[str, Any]:
    path = Path(workspace_path)
    cleanup_error = None
    if path.exists():
        try:
            shutil.rmtree(path)
        except Exception as exc:  # pragma: no cover - exercised by hosted provider ownership failures
            cleanup_error = f"{type(exc).__name__}: {exc}"
    return {
        "status": "PASS" if not path.exists() else "BLOCK",
        "workspace_path": str(path),
        "removed": not path.exists(),
        "blocker": None if not path.exists() else "provider_workspace_cleanup_failed",
        "cleanup_error": cleanup_error,
    }


def provider_workspace_transport_audit(
    *,
    workspace: dict[str, Any],
    input_dir: str | Path,
    output_dir: str | Path,
) -> dict[str, Any]:
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    input_files = [
        {
            "path": path.relative_to(input_path).as_posix(),
            "sha256": sha256_file(path),
            "size_bytes": path.stat().st_size,
        }
        for path in sorted(input_path.rglob("*"))
        if path.is_file()
    ] if input_path.is_dir() else []
    output_files = [
        {
            "path": path.relative_to(output_path).as_posix(),
            "sha256": sha256_file(path),
            "size_bytes": path.stat().st_size,
        }
        for path in sorted(output_path.rglob("*"))
        if path.is_file()
    ] if output_path.is_dir() else []
    status = "PASS" if workspace.get("status") == "PASS" else "BLOCK"
    return {
        "status": status,
        "workspace_path": workspace.get("workspace_path"),
        "workspace_outside_repo": workspace.get("outside_live_repo"),
        "workspace_outside_onedrive": workspace.get("outside_onedrive"),
        "input_file_count": len(input_files),
        "output_file_count": len(output_files),
        "input_files": input_files,
        "output_files": output_files,
        "repo_root_mounted_read_only": True,
        "write_credentials_mounted": False,
        "secrets_mounted": False,
        "blocker": None if status == "PASS" else "provider_workspace_transport_unverified",
    }
