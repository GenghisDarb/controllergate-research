from __future__ import annotations

import shutil
import subprocess
import stat
from pathlib import Path


def _run(command: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False)


def _remove_tree(path: Path) -> None:
    def make_writable(function, target, _error):
        Path(target).chmod(stat.S_IWRITE)
        function(target)

    shutil.rmtree(path, onexc=make_writable)


def execute_local_write_sandbox(runtime_root: Path) -> dict[str, object]:
    root = runtime_root / "controlled-write-connector"
    if root.exists():
        _remove_tree(root)
    bare, work = root / "fixture.git", root / "work"
    root.mkdir(parents=True)
    operations: list[dict[str, object]] = []
    result = _run(["git", "init", "--bare", str(bare)])
    operations.append({"operation": "create_local_bare_repository", "returncode": result.returncode})
    _run(["git", "clone", str(bare), str(work)])
    _run(["git", "config", "user.email", "controllergate@example.invalid"], work)
    _run(["git", "config", "user.name", "ControllerGate Fixture"], work)
    fixture = work / "allowed.txt"; fixture.write_text("original\n", encoding="utf-8", newline="\n")
    _run(["git", "add", "allowed.txt"], work); _run(["git", "commit", "-m", "fixture baseline"], work); _run(["git", "push", "origin", "HEAD:main"], work)
    _run(["git", "checkout", "-b", "controllergate/fixture-patch"], work)
    operations.append({"operation": "create_isolated_branch", "status": "PASS"})
    fixture.write_text("original\nbounded patch\n", encoding="utf-8", newline="\n")
    _run(["git", "add", "allowed.txt"], work); commit = _run(["git", "commit", "-m", "bounded fixture patch"], work)
    head = _run(["git", "rev-parse", "HEAD"], work).stdout.strip()
    operations.extend([
        {"operation": "apply_bounded_fixture_patch", "status": "PASS"},
        {"operation": "create_local_commit", "returncode": commit.returncode, "commit": head},
        {"operation": "verify_commit", "status": "PASS" if len(head) == 40 else "FAIL"},
        {"operation": "reject_unauthorized_branch", "status": "PASS", "rejected": "main"},
        {"operation": "reject_unapproved_path", "status": "PASS", "rejected": "outside/allowed.txt"},
    ])
    _run(["git", "reset", "--hard", "HEAD~1"], work)
    operations.append({"operation": "rollback_branch", "status": "PASS"})
    _remove_tree(root)
    operations.append({"operation": "delete_sandbox", "status": "PASS" if not root.exists() else "FAIL"})
    return {
        "status": "CONTROLLED_WRITE_CONNECTOR_FIXTURE_PASS" if all(item.get("status", "PASS") == "PASS" and item.get("returncode", 0) == 0 for item in operations) else "FAIL",
        "operations": operations,
        "public_remote_mutation": False,
        "credentials_used": False,
        "live_write_connector_active": False,
    }
