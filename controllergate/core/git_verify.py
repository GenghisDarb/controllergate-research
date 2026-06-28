from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path


def _run(args: list[str], cwd: str | Path, timeout: int = 120) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=str(cwd), text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout, check=False)


def clone_repo_to_temp_workspace(repo_url: str, prefix: str = "controllergate_") -> Path:
    root = Path(tempfile.mkdtemp(prefix=prefix)).resolve()
    result = _run(["git", "clone", "--filter=blob:none", "--no-checkout", repo_url, "checkout"], root, timeout=300)
    if result.returncode != 0:
        raise RuntimeError(result.stderr[-500:])
    return root / "checkout"


def resolve_commit(repo: str | Path, commit: str) -> str:
    result = _run(["git", "rev-parse", commit], repo)
    if result.returncode != 0:
        raise ValueError("commit did not resolve")
    return result.stdout.strip()


def verify_commit_object(repo: str | Path, commit: str) -> bool:
    result = _run(["git", "cat-file", "-t", commit], repo)
    return result.returncode == 0 and result.stdout.strip() == "commit"


def checkout_commit(repo: str | Path, commit: str) -> None:
    result = _run(["git", "checkout", "--detach", commit], repo, timeout=180)
    if result.returncode != 0:
        raise RuntimeError(result.stderr[-500:])


def list_changed_files_for_commit(repo: str | Path, commit: str) -> list[str]:
    result = _run(["git", "show", "--name-only", "--format=", commit], repo)
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def get_default_branch_commit_before_time(repo: str | Path, before_time: str, branch: str = "HEAD") -> str:
    result = _run(["git", "rev-list", "-n", "1", f"--before={before_time}", branch], repo)
    if result.returncode != 0 or not result.stdout.strip():
        raise ValueError("no commit before time")
    return result.stdout.strip()


def forbid_later_commit_inspection() -> bool:
    return True
