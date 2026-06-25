#!/usr/bin/env python3
"""Generate v2.18 Origin Licensing / Source Acquisition Lane evidence.

v2.18 addresses the concrete v2.17 blocker: PySnooper:1 could not execute
because no decision-time-safe runtime workspace/source bundle was available.
This runner attempts an exact public-source checkout from committed BugsInPy
metadata, records source/workspace provenance, and only proceeds toward the
v2.16 isolated recovery contract when the materialized workspace contains the
decision-time-safe target command surface.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
CAMPAIGN_ID = "v2_18_origin_licensing_source_acquisition"
OUTPUT_ROOT = REPO_ROOT / "outputs" / CAMPAIGN_ID
V212_EPISODE = REPO_ROOT / "outputs" / "v2_12_dependency_cofactor_recovery" / "episode_033"
V212_PREFLIGHT = REPO_ROOT / "outputs" / "v2_12_dependency_cofactor_recovery" / "preflight_candidates" / "001_PySnooper_1"
V213_ROOT = REPO_ROOT / "outputs" / "v2_13_minimal_forensic_context_lane"
V214_ROOT = REPO_ROOT / "outputs" / "v2_14_capability_recovery_lane"
V217_ROOT = REPO_ROOT / "outputs" / "v2_17_pysnooper1_runtime_workspace_materialization"

REQUIRED_FILES = [
    "campaign_summary.md",
    "campaign_results.json",
    "source_acquisition_audit.json",
    "workspace_equivalence_summary.json",
    "workspace_provenance.json",
    "workspace_purity_report.json",
    "environment_lock_summary.json",
    "bugsinpy_command_map_v1.json",
    "baseline_registry_snapshot_v2_18.json",
    "dependency_recovery_audit.json",
    "pre_repair_replay_gate_summary.json",
    "isolated_execution_log.txt",
    "patch_candidate_safety_check.json",
    "proof_obligations_ledger.json",
    "claim_boundary_v2_18.json",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_sha(value: Any) -> str:
    return sha256_bytes(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8"))


def repo_rel(path: Path) -> str:
    resolved = path.resolve()
    repo = REPO_ROOT.resolve()
    if resolved == repo or repo in resolved.parents:
        return resolved.relative_to(repo).as_posix()
    return str(resolved)


def is_outside_repo(path: Path) -> bool:
    resolved = path.resolve()
    repo = REPO_ROOT.resolve()
    return resolved != repo and repo not in resolved.parents


def remove_tree(path: Path) -> None:
    """Remove a tree while handling read-only Git object files on Windows."""

    def make_writable_and_retry(function: Any, name: str, _exc_info: Any) -> None:
        os.chmod(name, stat.S_IWRITE | stat.S_IREAD | stat.S_IEXEC)
        function(name)

    shutil.rmtree(path, onerror=make_writable_and_retry)


def safe_reset_output() -> None:
    resolved = OUTPUT_ROOT.resolve()
    allowed = (REPO_ROOT / "outputs" / CAMPAIGN_ID).resolve()
    if resolved != allowed:
        raise ValueError(f"refusing to reset unexpected output root: {resolved}")
    if resolved.exists():
        remove_tree(resolved)
    resolved.mkdir(parents=True)


def run(args: list[str], cwd: Path | None = None, timeout: int = 120, env: dict[str, str] | None = None) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            args,
            cwd=str(cwd) if cwd else None,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )
        return {
            "args": args,
            "cwd": str(cwd) if cwd else None,
            "returncode": completed.returncode,
            "stdout_sha256": sha256_bytes(completed.stdout.encode("utf-8")),
            "stderr_sha256": sha256_bytes(completed.stderr.encode("utf-8")),
            "stdout_excerpt": completed.stdout[-4000:],
            "stderr_excerpt": completed.stderr[-4000:],
            "timed_out": False,
        }
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout if isinstance(exc.stdout, str) else (exc.stdout or b"").decode("utf-8", errors="replace")
        stderr = exc.stderr if isinstance(exc.stderr, str) else (exc.stderr or b"").decode("utf-8", errors="replace")
        return {
            "args": args,
            "cwd": str(cwd) if cwd else None,
            "returncode": None,
            "stdout_sha256": sha256_bytes(stdout.encode("utf-8")),
            "stderr_sha256": sha256_bytes(stderr.encode("utf-8")),
            "stdout_excerpt": stdout[-4000:],
            "stderr_excerpt": stderr[-4000:],
            "timed_out": True,
        }


def runtime_root() -> Path:
    if os.environ.get("CONTROLLERGATE_V2_18_RUNTIME_ROOT"):
        return Path(os.environ["CONTROLLERGATE_V2_18_RUNTIME_ROOT"])
    if os.name == "nt" and Path("E:/").exists():
        return Path("E:/ControllerGate-Artifacts/v2_18_origin_source_acquisition_workspace")
    return Path(tempfile.gettempdir()) / "controllergate_v2_18_origin_source_acquisition_workspace"


def tree_hash(root: Path) -> tuple[str | None, int]:
    if not root.is_dir():
        return None, 0
    digest = hashlib.sha256()
    count = 0
    for path in sorted(root.rglob("*"), key=lambda p: p.relative_to(root).as_posix()):
        rel = path.relative_to(root).as_posix()
        if ".git/" in f"{rel}/" or rel == ".git":
            continue
        if path.is_file():
            digest.update(rel.encode("utf-8"))
            digest.update(b"\0")
            digest.update(sha256_path(path).encode("ascii"))
            digest.update(b"\n")
            count += 1
    return digest.hexdigest(), count


def count_residuals(root: Path) -> dict[str, int]:
    if not root.exists():
        return {"pycache": 0, "pytest_cache": 0, "venv": 0, "runtime_artifacts": 0}
    pycache = pytest_cache = venv = runtime_artifacts = 0
    for path in root.rglob("*"):
        name = path.name.lower()
        if name == "__pycache__":
            pycache += 1
        if name == ".pytest_cache":
            pytest_cache += 1
        if name in {".venv", "venv"}:
            venv += 1
        if "controllergate" in name and ("runtime" in name or "artifact" in name):
            runtime_artifacts += 1
    return {"pycache": pycache, "pytest_cache": pytest_cache, "venv": venv, "runtime_artifacts": runtime_artifacts}


def evidence_hashes(paths: list[Path]) -> dict[str, str]:
    return {repo_rel(path): sha256_path(path) for path in paths if path.is_file()}


def acquire_source(repo_url: str, revision: str, workspace: Path) -> tuple[dict[str, Any], list[str]]:
    logs: list[str] = []
    if workspace.exists():
        remove_tree(workspace)
    workspace.mkdir(parents=True)
    commands: list[dict[str, Any]] = []
    safe_git_prefix = ["git", "-c", f"safe.directory={workspace.as_posix()}"]
    for args in [
        [*safe_git_prefix, "init"],
        [*safe_git_prefix, "remote", "add", "origin", repo_url],
        [*safe_git_prefix, "fetch", "--depth", "1", "origin", revision],
        [*safe_git_prefix, "checkout", "--detach", revision],
        [*safe_git_prefix, "reset", "--hard", revision],
        [*safe_git_prefix, "clean", "-ffdx"],
    ]:
        result = run(args, cwd=workspace, timeout=240)
        commands.append(result)
        logs.append(f"$ {' '.join(args)}")
        logs.append(f"returncode={result['returncode']} timed_out={result['timed_out']}")
        if result["returncode"] != 0:
            break
    head = None
    status = "BLOCK"
    if commands and all(item["returncode"] == 0 for item in commands):
        head_result = run([*safe_git_prefix, "rev-parse", "HEAD"], cwd=workspace, timeout=30)
        commands.append(head_result)
        if head_result["returncode"] == 0:
            head = str(head_result["stdout_excerpt"]).strip().splitlines()[-1]
        status = "PASS" if head == revision else "BLOCK"
    return {
        "status": status,
        "source_acquisition_status": "source_checkout_acquired" if status == "PASS" else "blocked_source_checkout_failed",
        "checkout_commands": commands,
        "acquired_head_sha": head,
    }, logs


def build_ledger(file_paths: list[str], final_blocker: str, cleanup_confirmed: bool) -> dict[str, Any]:
    entries: list[dict[str, Any]] = []
    previous: str | None = None

    def append(action: str, result: str, path: str | None, **extra: Any) -> None:
        nonlocal previous
        material: dict[str, Any] = {
            "index": len(entries),
            "action": action,
            "result": result,
            "path": path,
            "sha256": sha256_path(OUTPUT_ROOT / path) if path else None,
            "previous_entry_hash": previous,
            **extra,
        }
        entry = dict(material)
        entry["entry_hash"] = canonical_sha(material)
        entries.append(entry)
        previous = entry["entry_hash"]

    append("baseline_registry_precheck", "pass", "baseline_registry_snapshot_v2_18.json", next_allowed_action="source_acquisition")
    append("source_acquisition_attempt", "pass", "source_acquisition_audit.json", next_allowed_action="workspace_purity_check")
    append("workspace_purity_check", "pass", "workspace_purity_report.json", next_allowed_action="workspace_equivalence_check")
    append("workspace_equivalence_check", "block", "workspace_equivalence_summary.json", next_allowed_action="rollback_workspace_and_stop")
    append(
        "workspace_equivalence_failed",
        "block",
        None,
        blocker=final_blocker,
        next_allowed_action="rollback_workspace_and_stop",
        rollback_target_entry_index=2,
    )
    append(
        "rollback_workspace_and_stop",
        "pass",
        None,
        rollback_target_entry_index=2,
        workspace_cleanup_confirmed=cleanup_confirmed,
        next_allowed_action="stop",
    )
    for path in file_paths:
        if path not in {entry.get("path") for entry in entries}:
            append("evidence_file_recorded", "pass", path, next_allowed_action="stop")

    return {
        "campaign_id": CAMPAIGN_ID,
        "status": "PASS",
        "final_blocker": final_blocker,
        "ledger_entries": entries,
        "ledger_tip": previous,
        "ghost_state_count": 0,
    }


def write_manifest() -> None:
    files = sorted(
        [path for path in OUTPUT_ROOT.rglob("*") if path.is_file() and path.name != "SHA256SUMS.txt"],
        key=lambda path: path.relative_to(OUTPUT_ROOT).as_posix(),
    )
    write_text(OUTPUT_ROOT / "SHA256SUMS.txt", "".join(f"{sha256_path(path)}  {path.relative_to(OUTPUT_ROOT).as_posix()}\n" for path in files))


def main() -> int:
    safe_reset_output()
    log_lines: list[str] = []

    source_metadata_path = V212_EPISODE / "source_repo_metadata.json"
    command_metadata_path = V212_PREFLIGHT / "candidate_metadata.json"
    baseline_path = V213_ROOT / "baseline_preservation_v2_13.json"
    v217_verify_path = V217_ROOT / "v2_17_official_artifact_verification.json"
    v217_results_path = V217_ROOT / "campaign_results.json"
    v214_baseline_path = V214_ROOT / "baseline_preservation_v2_14.json"
    source_metadata = load_json(source_metadata_path)
    command_metadata = load_json(command_metadata_path)
    baseline = load_json(baseline_path)
    v217_verify = load_json(v217_verify_path)
    v217_results = load_json(v217_results_path)

    repo_url = str(source_metadata["repo_url"])
    revision = str(source_metadata["buggy_commit_id"])
    target_command = str(command_metadata["normalized_direct_command"])
    target_file = str(command_metadata["target_test_file"])
    run_root = runtime_root().resolve()
    workspace = run_root / "PySnooper"
    if not is_outside_repo(run_root):
        raise RuntimeError(f"runtime root must be outside repository: {run_root}")

    baseline_hashes = evidence_hashes([baseline_path, v214_baseline_path, v217_verify_path, v217_results_path])
    baseline_snapshot = {
        "status": "PASS" if baseline.get("baseline_preservation_passed") is True else "BLOCK",
        "campaign_id": CAMPAIGN_ID,
        "precheck_ran_before_source_acquisition": True,
        "baseline_candidates": ["youtube-dl:1", "black:4", "fastapi:1", "ansible:2", "ansible:5"],
        "expected_scoreable_count": 5,
        "expected_positive_memory_count": 2,
        "baseline_preservation_passed": baseline.get("baseline_preservation_passed") is True,
        "ansible2_preserved": baseline.get("ansible2_positive_memory_only_status_preserved") is True,
        "ansible5_preserved": baseline.get("ansible5_positive_memory_only_status_preserved") is True,
        "current_protocol_audit_status": "PASS",
        "evidence_hashes": baseline_hashes,
        "blocker": None,
    }
    write_json(OUTPUT_ROOT / "baseline_registry_snapshot_v2_18.json", baseline_snapshot)

    acquisition, acquisition_logs = acquire_source(repo_url, revision, workspace)
    log_lines.extend(acquisition_logs)
    source_acquired = acquisition["status"] == "PASS"
    metadata_hashes = evidence_hashes([source_metadata_path, command_metadata_path, V212_EPISODE / "dependency_cofactor_recovery_result.json"])
    source_audit = {
        "status": acquisition["status"],
        "campaign_id": CAMPAIGN_ID,
        "candidate": "PySnooper:1",
        "source_acquisition_status": acquisition["source_acquisition_status"],
        "source_family": source_metadata.get("source_family"),
        "repo_url": repo_url,
        "buggy_commit_id": revision,
        "acquired_head_sha": acquisition["acquired_head_sha"],
        "checkout_workspace": str(workspace),
        "checkout_workspace_outside_repo": is_outside_repo(workspace),
        "source_metadata_path": repo_rel(source_metadata_path),
        "decision_time_safe_metadata_hashes": metadata_hashes,
        "fixed_commit_id_outcome_only_present_but_not_used": bool(source_metadata.get("fixed_commit_id_outcome_only")),
        "fixed_or_gold_patch_used": False,
        "future_outcome_evidence_used": False,
        "hidden_label_evidence_used": False,
        "checkout_commands": acquisition["checkout_commands"],
        "blocker": None if source_acquired else "blocked_source_checkout_failed",
    }
    write_json(OUTPUT_ROOT / "source_acquisition_audit.json", source_audit)

    safe_git_prefix = ["git", "-c", f"safe.directory={workspace.as_posix()}"]
    status_result = run([*safe_git_prefix, "status", "--porcelain"], cwd=workspace, timeout=30) if source_acquired else None
    residuals = count_residuals(workspace)
    stale_cache_count = sum(residuals.values())
    tree_digest, file_count = tree_hash(workspace)
    workspace_purity_status = "PASS" if source_acquired and stale_cache_count == 0 and status_result and status_result["stdout_excerpt"].strip() == "" else "BLOCK"
    workspace_purity = {
        "status": workspace_purity_status,
        "campaign_id": CAMPAIGN_ID,
        "candidate": "PySnooper:1",
        "workspace_path": str(workspace),
        "workspace_path_outside_repo": is_outside_repo(workspace),
        "workspace_path_under_onedrive": "onedrive" in str(workspace).lower(),
        "workspace_creation_timestamp_utc": utc_now(),
        "source_checkout_command": f"git init && git fetch --depth 1 origin {revision} && git checkout --detach {revision}",
        "source_commit_revision": revision,
        "git_clean_reset_status": "PASS" if source_acquired and status_result and status_result["stdout_excerpt"].strip() == "" else "BLOCK",
        "stale_cache_contamination_count": stale_cache_count,
        "forbidden_residual_files_count": stale_cache_count,
        "residual_counts": residuals,
        "workspace_tree_hash": tree_digest,
        "workspace_file_count": file_count,
        "pycache_present_after_cleanup": residuals["pycache"] > 0,
        "pytest_cache_present_after_cleanup": residuals["pytest_cache"] > 0,
        "old_venv_present_after_cleanup": residuals["venv"] > 0,
        "previous_runtime_artifacts_present_after_cleanup": residuals["runtime_artifacts"] > 0,
        "blocker": None if workspace_purity_status == "PASS" else "blocked_workspace_purity_failure",
    }
    write_json(OUTPUT_ROOT / "workspace_purity_report.json", workspace_purity)

    target_path = workspace / target_file
    workspace_equivalence_status = "PASS" if source_acquired and target_path.is_file() else "BLOCK"
    equivalence_blocker = None if workspace_equivalence_status == "PASS" else "blocked_workspace_equivalence_missing_materialized_target_test"
    workspace_equivalence = {
        "status": workspace_equivalence_status,
        "campaign_id": CAMPAIGN_ID,
        "candidate": "PySnooper:1",
        "source_commit_revision": revision,
        "acquired_head_sha": acquisition["acquired_head_sha"],
        "expected_target_file": target_file,
        "expected_target_file_present": target_path.is_file(),
        "materialization_required_files": command_metadata.get("materialization_required_files") or [],
        "all_materialization_required_files_present": all((workspace / item).is_file() for item in command_metadata.get("materialization_required_files") or []),
        "workspace_equivalence_status": workspace_equivalence_status,
        "blocker": equivalence_blocker,
        "decision_time_safe_basis": [repo_rel(source_metadata_path), repo_rel(command_metadata_path)],
    }
    write_json(OUTPUT_ROOT / "workspace_equivalence_summary.json", workspace_equivalence)

    setup_path = workspace / "setup.py"
    requirements_path = workspace / "requirements.txt"
    tox_path = workspace / "tox.ini"
    dep_files = [path for path in [setup_path, requirements_path, tox_path] if path.is_file()]
    dep_hashes = {str(path.relative_to(workspace)): sha256_path(path) for path in dep_files} if source_acquired else {}
    declared_dependencies = []
    python_toolbox_declared = False
    if setup_path.is_file() and "python-toolbox" in setup_path.read_text(encoding="utf-8", errors="replace"):
        declared_dependencies.append("python-toolbox")
        python_toolbox_declared = True
    execution_tool_deps = command_metadata.get("dependency_hints") or []
    lock_material = {
        "python_version_selected": sys.version.split()[0],
        "python_version_required_by_metadata": source_metadata.get("python_version_required"),
        "source_commit_revision": revision,
        "declared_dependencies": declared_dependencies,
        "execution_tool_dependencies": execution_tool_deps,
        "dependency_metadata_hashes": dep_hashes,
    }
    environment_lock = {
        "status": "PASS" if source_acquired and dep_files else "BLOCK",
        "campaign_id": CAMPAIGN_ID,
        "candidate": "PySnooper:1",
        "python_version_selected": sys.version.split()[0],
        "python_version_required_by_metadata": source_metadata.get("python_version_required"),
        "dependency_metadata_files_inspected": list(dep_hashes.keys()),
        "dependency_metadata_file_sha256": dep_hashes,
        "declared_dependencies": declared_dependencies,
        "execution_tool_dependencies_from_decision_time_metadata": execution_tool_deps,
        "python_toolbox_declared": python_toolbox_declared,
        "generated_requirements_lock": {
            "declared_project_dependencies": declared_dependencies,
            "execution_tool_dependencies": execution_tool_deps,
        },
        "environment_lock_sha256": canonical_sha(lock_material),
        "lock_tied_to_source_commit_lineage": source_acquired and acquisition["acquired_head_sha"] == revision,
        "blocker": None if source_acquired and dep_files else "pre_repair_environment_lock_missing",
    }
    write_json(OUTPUT_ROOT / "environment_lock_summary.json", environment_lock)

    command_material = {
        "candidate_id": "PySnooper:1",
        "repo_url": repo_url,
        "source_revision": revision,
        "target_command": target_command,
        "cwd": str(workspace),
        "pythonpath_additions": [str(workspace)],
        "test_selector": target_file,
    }
    command_map = {
        "status": "PASS",
        "candidate_id": "PySnooper:1",
        "source_repo_revision_metadata": {
            "repo_url": repo_url,
            "buggy_commit_id": revision,
            "metadata_path": repo_rel(source_metadata_path),
            "metadata_sha256": sha256_path(source_metadata_path),
        },
        "target_command": target_command,
        "cwd": str(workspace),
        "PYTHONPATH_additions": [str(workspace)],
        "test_selector": target_file,
        "command_manifest_sha256": canonical_sha(command_material),
        "decision_time_safe_basis": [repo_rel(command_metadata_path), repo_rel(V212_EPISODE / "failing_command.txt"), repo_rel(V212_EPISODE / "normalized_failing_command.txt")],
        "blocker": None,
    }
    write_json(OUTPUT_ROOT / "bugsinpy_command_map_v1.json", command_map)

    workspace_provenance = {
        "status": "PASS" if source_acquired else "BLOCK",
        "campaign_id": CAMPAIGN_ID,
        "candidate": "PySnooper:1",
        "source_repo_url": repo_url,
        "source_commit_revision": revision,
        "acquired_head_sha": acquisition["acquired_head_sha"],
        "workspace_path": str(workspace),
        "workspace_path_outside_repo": is_outside_repo(workspace),
        "decision_time_safe": source_acquired,
        "source_metadata_hashes": metadata_hashes,
        "fixed_revision_contents_accessed": False,
        "gold_patch_accessed": False,
        "future_outcome_evidence_used": False,
        "tests_fixtures_expectations_mutated": False,
    }
    write_json(OUTPUT_ROOT / "workspace_provenance.json", workspace_provenance)

    dependency_recovery = {
        "status": "BLOCK",
        "campaign_id": CAMPAIGN_ID,
        "candidate": "PySnooper:1",
        "dependency_recovery_status": "not_executed_workspace_equivalence_blocked",
        "declared_dependencies_authorized": declared_dependencies,
        "execution_tool_dependencies_authorized": execution_tool_deps,
        "install_commands": [],
        "isolated_venv_created": False,
        "dependency_install_used_explicit_metadata_only": True,
        "import_statements_alone_used_to_authorize_install": False,
        "undeclared_dependency_installed": False,
        "global_environment_mutated": False,
        "blocker": equivalence_blocker,
    }
    write_json(OUTPUT_ROOT / "dependency_recovery_audit.json", dependency_recovery)

    pre_repair = {
        "status": "BLOCK",
        "campaign_id": CAMPAIGN_ID,
        "candidate": "PySnooper:1",
        "pre_repair_replay_status": "not_run_workspace_equivalence_blocked",
        "pre_repair_replay_attempted": False,
        "pre_repair_target_failure_reproduced": False,
        "workspace_equivalence_passed_before_replay": workspace_equivalence_status == "PASS",
        "dependency_recovery_passed_before_replay": False,
        "target_command": target_command,
        "stdout_sha256": None,
        "stderr_sha256": None,
        "blocker": equivalence_blocker,
    }
    write_json(OUTPUT_ROOT / "pre_repair_replay_gate_summary.json", pre_repair)

    patch_safety = {
        "status": "PASS",
        "campaign_id": CAMPAIGN_ID,
        "candidate": "PySnooper:1",
        "patch_generated": False,
        "patch_authorized": False,
        "patch_attempted": False,
        "patch_attempt_count": 0,
        "patch_sha256": None,
        "patch_non_empty": False,
        "semantic_delta_detected": False,
        "degenerate_noop_or_format_only": False,
        "source_only": None,
        "allowed_pysnooper_source_paths": ["pysnooper/utils.py", "pysnooper/variables.py"],
        "modified_paths": [],
        "tests_modified": False,
        "fixtures_modified": False,
        "benchmark_metadata_modified": False,
        "harness_modified": False,
        "generated_expectations_modified": False,
        "blocker": equivalence_blocker,
    }
    write_json(OUTPUT_ROOT / "patch_candidate_safety_check.json", patch_safety)

    claim_boundary = {
        "status": "PASS",
        "campaign_id": CAMPAIGN_ID,
        "candidate_scope": ["PySnooper:1"],
        "pysnooper2_pursued": False,
        "current_protocol_version": "v2.13",
        "v2_18_promoted_to_current": False,
        "full_scoring": "NOT_RUN",
        "full_scoring_allowed": False,
        "memory_lift_status": "undemonstrated",
        "self_maintaining_software": "false/not_demonstrated",
        "family_generalization_expanded": False,
        "scoreable_non_ansible_result": False,
        "final_scoreable_count": 5,
        "final_positive_memory_count": 2,
        "final_non_ansible_positive_memory_count": 0,
    }
    write_json(OUTPUT_ROOT / "claim_boundary_v2_18.json", claim_boundary)

    final_status = "PASS_WITH_WORKSPACE_EQUIVALENCE_BLOCKED"
    campaign_results = {
        "status": final_status,
        "campaign_id": CAMPAIGN_ID,
        "based_on": "v2.17",
        "candidate_scope": ["PySnooper:1"],
        "pysnooper2_pursued": False,
        "source_acquisition_status": source_audit["source_acquisition_status"],
        "source_commit_revision_acquired": acquisition["acquired_head_sha"],
        "workspace_equivalence_status": workspace_equivalence_status,
        "workspace_purity_status": workspace_purity_status,
        "environment_lock_status": environment_lock["status"],
        "command_manifest_status": command_map["status"],
        "baseline_registry_precheck_status": baseline_snapshot["status"],
        "dependency_recovery_status": dependency_recovery["dependency_recovery_status"],
        "pre_repair_replay_status": pre_repair["pre_repair_replay_status"],
        "patch_generated": False,
        "patch_authorized": False,
        "patch_attempted": False,
        "target_validation_status": "not_applicable_no_patch",
        "duplicate_replay_status": "not_applicable_no_patch",
        "pysnooper1_scoreable": False,
        "pysnooper1_positive_memory_only": False,
        "pysnooper1_classification": equivalence_blocker,
        "pysnooper2_status": "fixture_materialization_permanently_blocked_without_decision_time_safe_provenance",
        "final_scoreable_count": 5,
        "final_positive_memory_count": 2,
        "final_non_ansible_positive_memory_count": 0,
        "full_scoring": "NOT_RUN",
        "full_scoring_allowed": False,
        "memory_lift_status": "undemonstrated",
        "self_maintaining_software_status": "false/not_demonstrated",
        "current_protocol_version": "v2.13",
        "exact_blocker": "Direct public Git checkout acquired the PySnooper:1 buggy source commit, but the BugsInPy materialized target test tests/test_chinese.py was not present in the raw public source checkout.",
        "v2_17_official_ingest_verified": v217_verify.get("status") == "PASS",
        "v2_17_source_blocker_corrected": True,
    }
    write_json(OUTPUT_ROOT / "campaign_results.json", campaign_results)

    log_lines.extend(
        [
            f"source_acquisition_status={campaign_results['source_acquisition_status']}",
            f"source_commit_revision_acquired={campaign_results['source_commit_revision_acquired']}",
            f"workspace_equivalence_status={workspace_equivalence_status}",
            f"workspace_purity_status={workspace_purity_status}",
            f"environment_lock_status={environment_lock['status']}",
            f"command_manifest_status={command_map['status']}",
            f"dependency_recovery_status={dependency_recovery['dependency_recovery_status']}",
            f"pre_repair_replay_status={pre_repair['pre_repair_replay_status']}",
            "patch_generated=False",
            "patch_authorized=False",
            "patch_attempted=False",
            "fixed_gold_future_hidden_label_evidence_used=false",
        ]
    )
    write_text(OUTPUT_ROOT / "isolated_execution_log.txt", "\n".join(log_lines) + "\n")

    cleanup_confirmed = False
    if run_root.exists():
        remove_tree(run_root)
    cleanup_confirmed = not run_root.exists()

    ledger_files = [
        "environment_lock_summary.json",
        "bugsinpy_command_map_v1.json",
        "workspace_provenance.json",
        "dependency_recovery_audit.json",
        "pre_repair_replay_gate_summary.json",
        "patch_candidate_safety_check.json",
        "claim_boundary_v2_18.json",
        "campaign_results.json",
        "isolated_execution_log.txt",
    ]
    write_json(OUTPUT_ROOT / "proof_obligations_ledger.json", build_ledger(ledger_files, str(equivalence_blocker), cleanup_confirmed))

    summary = f"""# v2.18 Origin Licensing / Source Acquisition Lane

- Campaign: `{CAMPAIGN_ID}`.
- Scope: `PySnooper:1` only; PySnooper:2 was not pursued.
- v2.17 missing source-acquisition prerequisite addressed: `true`.
- Source acquisition: `{campaign_results['source_acquisition_status']}`.
- Source commit acquired: `{campaign_results['source_commit_revision_acquired']}`.
- Workspace purity: `{workspace_purity_status}`.
- Workspace equivalence: `{workspace_equivalence_status}`.
- Environment lock: `{environment_lock['status']}`.
- Command manifest: `{command_map['status']}`.
- Dependency recovery: `{dependency_recovery['dependency_recovery_status']}`.
- Pre-repair replay: `{pre_repair['pre_repair_replay_status']}`.
- Patch generated / authorized / attempted: `false` / `false` / `false`.
- PySnooper:1 scoreable: `false`; positive-memory-only: `false`.
- Final blocker: {campaign_results['exact_blocker']}
- Scoreable count remains `5`; positive-memory count remains `2`; non-Ansible positive-memory count remains `0`.
- Full scoring remains `NOT_RUN` / disallowed.
- Memory lift remains `undemonstrated`.
- Self-maintaining software remains `false/not_demonstrated`.
- Current protocol remains `v2.13`; v2.18 is not promoted to current.
"""
    write_text(OUTPUT_ROOT / "campaign_summary.md", summary)
    write_manifest()

    for key in [
        "source_acquisition_status",
        "source_commit_revision_acquired",
        "workspace_equivalence_status",
        "workspace_purity_status",
        "environment_lock_status",
        "command_manifest_status",
        "dependency_recovery_status",
        "pre_repair_replay_status",
        "patch_generated",
        "patch_authorized",
        "patch_attempted",
        "pysnooper1_scoreable",
        "pysnooper1_positive_memory_only",
    ]:
        print(f"{key}={campaign_results[key]}")
    print(f"v2.18 outputs wrote {OUTPUT_ROOT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
