from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path
from typing import Any

from controllergate.core.evidence import hash_record


def _run(argv: list[str], cwd: Path, timeout: int = 180) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            argv,
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
        )
        return {
            "argv": argv,
            "returncode": completed.returncode,
            "stdout_sha256": hashlib.sha256(completed.stdout.encode()).hexdigest(),
            "stderr_sha256": hashlib.sha256(completed.stderr.encode()).hexdigest(),
            "stdout_tail": completed.stdout[-1000:],
            "stderr_tail": completed.stderr[-1000:],
        }
    except subprocess.TimeoutExpired as exc:
        stdout = str(exc.stdout or "")
        stderr = str(exc.stderr or "")
        return {
            "argv": argv,
            "returncode": 124,
            "timed_out": True,
            "stdout_sha256": hashlib.sha256(stdout.encode()).hexdigest(),
            "stderr_sha256": hashlib.sha256(stderr.encode()).hexdigest(),
            "stdout_tail": stdout[-1000:],
            "stderr_tail": stderr[-1000:],
        }


def verify_source_object(repo_url: str, candidate_sha: str, workspace: Path) -> dict[str, Any]:
    """Acquire and independently verify one pinned Git commit and tree.

    The result deliberately has no caller-supplied success flag.  A PASS is
    derived only from the fetched object, detached HEAD, and tree identity.
    """

    workspace.mkdir(parents=True, exist_ok=True)
    attempts = [
        _run(["git", "init", "-q"], workspace),
        _run(["git", "remote", "add", "origin", repo_url], workspace),
        _run(["git", "fetch", "-q", "--depth", "1", "origin", candidate_sha], workspace, 300),
        _run(["git", "checkout", "-q", "--detach", "FETCH_HEAD"], workspace),
    ]
    head = _run(["git", "rev-parse", "HEAD"], workspace)
    object_type = _run(["git", "cat-file", "-t", candidate_sha], workspace)
    tree = _run(["git", "rev-parse", "HEAD^{tree}"], workspace)
    head_value = head.get("stdout_tail", "").strip().splitlines()[-1:] or [""]
    type_value = object_type.get("stdout_tail", "").strip().splitlines()[-1:] or [""]
    tree_value = tree.get("stdout_tail", "").strip().splitlines()[-1:] or [""]
    passed = (
        all(item.get("returncode") == 0 for item in attempts)
        and head.get("returncode") == object_type.get("returncode") == tree.get("returncode") == 0
        and head_value[0] == candidate_sha
        and type_value[0] == "commit"
        and len(tree_value[0]) == 40
    )
    record = {
        "status": "PASS" if passed else "BLOCK",
        "repo_url": repo_url,
        "requested_sha": candidate_sha,
        "head": head_value[0],
        "object_type": type_value[0],
        "tree_hash": tree_value[0],
        "commit_object_verified": passed,
        "head_verified": passed,
        "tree_identity_verified": passed,
        "workspace": str(workspace),
        "attempts": attempts,
    }
    record["verification_hash"] = hash_record(record)
    return record
