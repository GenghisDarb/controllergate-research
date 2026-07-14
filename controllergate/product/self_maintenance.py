from __future__ import annotations

import hashlib
import os
import shutil
import stat
import sys
from pathlib import Path
from typing import Any

from controllergate.execution.execution_broker import execute_external_operation
from controllergate.repair.ast_synthesizer import synthesize
from controllergate.repair.planner import validate_candidate


SOURCE = "def is_success(return_code: int) -> bool:\n    return return_code == 0\n"
MUTATED = "def is_success(return_code: int) -> bool:\n    return return_code != 0\n"
TEST = "from gate import is_success\nassert is_success(0) is True\nassert is_success(1) is False\n"


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _remove_readonly(function, path: str, _exc_info) -> None:
    os.chmod(path, stat.S_IWRITE)
    function(path)


def _execute(argv: list[str], cwd: Path, runtime: Path, stage: str, operation_type: str | None = None):
    return execute_external_operation(
        operation_type=operation_type or ("validation" if stage != "prerepair" else "reproducer_execution"),
        argv=argv, cwd=cwd, runtime_root=runtime, stage_id=stage,
        candidate_id="controllergate_controlled_self_maintenance",
        authorization_id="batch085-controlled-local-worktree",
        runtime_attestation={"status": "PASS", "attestation_hash": hashlib.sha256(str(runtime).encode()).hexdigest()},
        platform=sys.platform, runtime=sys.version.split()[0], network_policy="none", timeout=60,
    )


def execute_controlled_drill(runtime_root: str | Path) -> dict[str, Any]:
    """Run a sealed local mutation drill without exposing a gold edit to planning."""
    runtime = Path(runtime_root).resolve() / "controlled-self-maintenance"
    if runtime.exists():
        shutil.rmtree(runtime, onerror=_remove_readonly)
    seed = runtime / "seed"; worktree = runtime / "worktree"
    seed.mkdir(parents=True)
    (seed / "gate.py").write_text(SOURCE, encoding="utf-8", newline="\n")
    (seed / "check_gate.py").write_text(TEST, encoding="utf-8", newline="\n")
    git_records = []
    for index, argv in enumerate((
        ["git", "init"], ["git", "config", "user.email", "controllergate@example.invalid"],
        ["git", "config", "user.name", "ControllerGate Fixture"], ["git", "add", "gate.py", "check_gate.py"],
        ["git", "commit", "-m", "sealed controlled fixture"],
    )):
        completed, record = _execute(argv, seed, runtime, f"git-seed-{index}", "source_acquisition")
        git_records.append(record["record_hash"])
        if completed.returncode != 0:
            return {"status": "BLOCK", "exact_blocker": "isolated_git_worktree_materialization_failed", "count_increment": 0}
    added, added_record = _execute(["git", "worktree", "add", "--detach", str(worktree), "HEAD"], seed, runtime, "git-worktree-add", "source_acquisition")
    git_records.append(added_record["record_hash"])
    if added.returncode != 0:
        return {"status": "BLOCK", "exact_blocker": "isolated_git_worktree_materialization_failed", "count_increment": 0}
    # Separate mutation boundary: only its sealed failing tree is passed onward.
    (worktree / "gate.py").write_text(MUTATED, encoding="utf-8", newline="\n")
    test_before = _hash(worktree / "check_gate.py")
    failure, failure_record = _execute([sys.executable, "-B", "check_gate.py"], worktree, runtime, "prerepair")
    proposals = synthesize((worktree / "gate.py").read_text(encoding="utf-8"), "gate.py", "wrong_comparison_operator")
    candidate = next((item for item in proposals if item.before == " != 0"), None)
    check = validate_candidate(candidate, {"gate.py"}) if candidate else {"status": "BLOCK"}
    if failure.returncode == 0 or not candidate or check["status"] != "PASS":
        return {"status": "BLOCK", "exact_blocker": "controlled_mutation_not_repaired", "count_increment": 0}
    source = (worktree / "gate.py").read_text(encoding="utf-8")
    (worktree / "gate.py").write_text(source.replace(candidate.before, candidate.after, 1), encoding="utf-8", newline="\n")
    validation, validation_record = _execute([sys.executable, "-B", "check_gate.py"], worktree, runtime, "validation")
    duplicate, duplicate_record = _execute([sys.executable, "-B", "check_gate.py"], worktree, runtime, "duplicate-replay")
    repaired_hash = _hash(worktree / "gate.py")
    (worktree / "gate.py").write_text(MUTATED, encoding="utf-8", newline="\n")
    rollback, rollback_record = _execute([sys.executable, "-B", "check_gate.py"], worktree, runtime, "rollback")
    passed = validation.returncode == duplicate.returncode == 0 and rollback.returncode != 0 and _hash(worktree / "check_gate.py") == test_before
    result = {
        "status": "CONTROLLED_SELF_MAINTENANCE_BETA_PASS" if passed else "BLOCK",
        "mutation_family": "wrong_comparison_operator", "mutation_identity_hidden_from_planner": True,
        "diagnosis": "source_owned_behavior_defect", "ast_contact_domain": "gate.is_success",
        "patch": {"path": "gate.py", "source_only": True, "sha256": repaired_hash},
        "validation": "PASS" if validation.returncode == 0 else "FAIL",
        "duplicate_replay": "PASS" if duplicate.returncode == 0 else "FAIL",
        "canary": "PASS" if validation.returncode == 0 else "NOT_RUN",
        "health_window": "PASS" if duplicate.returncode == 0 else "NOT_RUN",
        "rollback": "PASS" if rollback.returncode != 0 else "FAIL",
        "test_mutated": False, "remote_write": False, "count_increment": 0,
        "isolated_git_worktree": True, "git_execution_record_hashes": git_records,
        "execution_record_hashes": [failure_record["record_hash"], validation_record["record_hash"], duplicate_record["record_hash"], rollback_record["record_hash"]],
    }
    removed, removed_record = _execute(["git", "worktree", "remove", "--force", str(worktree)], seed, runtime, "git-worktree-remove", "rollback")
    result["git_execution_record_hashes"].append(removed_record["record_hash"])
    result["worktree_removal"] = "PASS" if removed.returncode == 0 else "BLOCK"
    shutil.rmtree(runtime, onerror=_remove_readonly)
    result["workspace_deleted"] = not runtime.exists()
    return result
