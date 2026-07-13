from __future__ import annotations

import os
from pathlib import Path
from typing import Any


LOCAL_ROOT = Path(r"C:\Dev\ControllerGate_Runtime")
CI_ROOT_ENV = "RUNNER_TEMP"
SYNC_MARKERS = ("onedrive", "dropbox", "google drive", "sharepoint")


def expected_runtime_root(env: dict[str, str] | None = None) -> Path:
    values = env or os.environ
    if values.get("GITHUB_ACTIONS", "").lower() == "true":
        return Path(values[CI_ROOT_ENV]) / "controllergate-runtime"
    return LOCAL_ROOT


def validate_runtime_root(path: str | Path, *, repo_root: str | Path, env: dict[str, str] | None = None) -> dict[str, Any]:
    candidate = Path(path).resolve()
    repo = Path(repo_root).resolve()
    expected = expected_runtime_root(env).resolve()
    lowered = str(candidate).lower()
    reasons: list[str] = []
    if candidate != expected and expected not in candidate.parents: reasons.append("undeclared_runtime_root")
    if candidate == repo or repo in candidate.parents: reasons.append("runtime_inside_git_checkout")
    if "incoming_artifacts" in lowered: reasons.append("runtime_inside_incoming_artifacts")
    if any(marker in lowered for marker in SYNC_MARKERS): reasons.append("synchronized_runtime_root")
    if not (env or os.environ).get("GITHUB_ACTIONS") and candidate.drive.upper() == "E:": reasons.append("e_drive_authoritative_execution_prohibited")
    return {
        "status": "PASS" if not reasons else "BLOCK",
        "absolute_root": str(candidate), "expected_root": str(expected), "drive": candidate.drive,
        "reasons": reasons, "exact_blocker": None if not reasons else "RUNTIME_STORAGE_BOUNDARY",
    }


def candidate_workspace(runtime_root: str | Path, candidate_id: str, execution_id: str) -> Path:
    safe = "".join(character if character.isalnum() or character in "-_" else "_" for character in candidate_id)
    return Path(runtime_root) / "candidates" / safe / execution_id
