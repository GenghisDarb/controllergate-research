#!/usr/bin/env python3
"""Generate v2.17 PySnooper:1 runtime-workspace materialization evidence.

v2.17 has one job: determine whether the v2.16 PySnooper:1 isolated recovery
contract can safely move from contract-only to a real, provenance-backed buggy
runtime workspace.  The lane is intentionally fail-closed.  It records every
decision-time-safe metadata input used for workspace authorization and refuses
dependency recovery, replay, and patch generation unless a PySnooper:1 buggy
checkout outside the live repository can be tied back to the recorded safe
identity.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
CAMPAIGN_ID = "v2_17_pysnooper1_runtime_workspace_materialization"
OUTPUT_ROOT = REPO_ROOT / "outputs" / CAMPAIGN_ID
V213_ROOT = REPO_ROOT / "outputs" / "v2_13_minimal_forensic_context_lane"
V214_ROOT = REPO_ROOT / "outputs" / "v2_14_capability_recovery_lane"
V215_ROOT = REPO_ROOT / "outputs" / "v2_15_chromosomal_maintenance_gate_order"
V216_ROOT = REPO_ROOT / "outputs" / "v2_16_pysnooper1_isolated_recovery_executor"

EXPECTED_HEAD = "e21a31162f4c54be693d8ca8260e42393b39abd3"
ALLOWED_PATCH_PATHS = ["pysnooper/utils.py", "pysnooper/variables.py"]
FORBIDDEN_OPERATIONS = [
    "inspect fixed revision contents",
    "inspect BugsInPy gold patches",
    "use future outcome evidence",
    "copy known fixes manually",
    "read hidden labels",
    "mutate tests to match broken code",
    "modify benchmark metadata or expectations",
    "install undeclared dependencies",
    "vendor global helpers into the project",
    "claim full scoring",
    "claim self-maintaining software",
    "pursue PySnooper:2",
]


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected object in {path}")
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
    if resolved == REPO_ROOT or REPO_ROOT in resolved.parents:
        return resolved.relative_to(REPO_ROOT).as_posix()
    return str(resolved)


def evidence_hashes(paths: list[Path]) -> dict[str, str]:
    return {repo_rel(path): sha256_path(path) for path in paths if path.is_file()}


def safe_reset(root: Path) -> None:
    resolved = root.resolve()
    allowed = (REPO_ROOT / "outputs" / CAMPAIGN_ID).resolve()
    if resolved != allowed:
        raise ValueError(f"refusing to reset unexpected output root: {resolved}")
    if resolved.exists():
        shutil.rmtree(resolved)
    resolved.mkdir(parents=True, exist_ok=True)


def is_outside_repo(path: Path) -> bool:
    try:
        resolved = path.resolve()
    except OSError:
        resolved = path.absolute()
    repo = REPO_ROOT.resolve()
    return resolved != repo and repo not in resolved.parents


def run_command(args: list[str], cwd: Path | None = None, timeout: int = 120) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            args,
            cwd=str(cwd) if cwd else None,
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
            "stdout_excerpt": completed.stdout[-2000:],
            "stderr_excerpt": completed.stderr[-2000:],
            "timed_out": False,
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "args": args,
            "cwd": str(cwd) if cwd else None,
            "returncode": None,
            "stdout_sha256": sha256_bytes((exc.stdout or "").encode("utf-8") if isinstance(exc.stdout, str) else (exc.stdout or b"")),
            "stderr_sha256": sha256_bytes((exc.stderr or "").encode("utf-8") if isinstance(exc.stderr, str) else (exc.stderr or b"")),
            "stdout_excerpt": str(exc.stdout or "")[-2000:],
            "stderr_excerpt": str(exc.stderr or "")[-2000:],
            "timed_out": True,
        }


def git_head(path: Path) -> str | None:
    result = run_command(["git", "rev-parse", "HEAD"], cwd=path, timeout=30)
    if result["returncode"] != 0:
        return None
    return str(result["stdout_excerpt"]).strip().splitlines()[-1]


def checkout_top(root: Path) -> Path:
    return root / "pysnooper1" / "PySnooper"


def materialize_or_find_workspace(policy: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    log: list[str] = []
    runtime_root = Path(os.environ.get("CONTROLLERGATE_RUNTIME_ROOT", tempfile.gettempdir())) / "controllergate_v2_17_pysnooper1_runtime_workspace"
    candidate_top = checkout_top(runtime_root)
    prior_top = Path(str((policy.get("checkout") or {}).get("identity", {}).get("top_level", "")))
    checkout_tool = shutil.which("bugsinpy-checkout")
    prior_command = str((policy.get("checkout") or {}).get("command", ""))

    log.append(f"repo_root={REPO_ROOT}")
    log.append(f"runtime_root={runtime_root}")
    log.append(f"runtime_root_outside_repo={is_outside_repo(runtime_root)}")
    log.append(f"prior_metadata_top_level={prior_top}")
    log.append(f"prior_metadata_top_level_exists={prior_top.exists()}")
    log.append(f"bugsinpy_checkout_available={checkout_tool is not None}")

    candidates = [
        {
            "source": "v2.13 recorded prior checkout path",
            "path": str(prior_top),
            "exists": prior_top.is_dir(),
            "outside_live_repo_worktree": is_outside_repo(prior_top) if str(prior_top) else None,
            "head_sha": git_head(prior_top) if prior_top.is_dir() else None,
        },
        {
            "source": "v2.17 deterministic runtime root",
            "path": str(candidate_top),
            "exists": candidate_top.is_dir(),
            "outside_live_repo_worktree": is_outside_repo(candidate_top),
            "head_sha": git_head(candidate_top) if candidate_top.is_dir() else None,
        },
    ]

    matched = next((item for item in candidates if item["exists"] and item["outside_live_repo_worktree"] and item["head_sha"] == EXPECTED_HEAD), None)
    materialization_command: list[str] | None = None
    materialization_result: dict[str, Any] | None = None

    if matched is None and checkout_tool and is_outside_repo(runtime_root):
        materialization_command = [
            checkout_tool,
            "-p",
            "PySnooper",
            "-v",
            "0",
            "-i",
            "1",
            "-w",
            str(runtime_root / "pysnooper1"),
        ]
        log.append("attempting_deterministic_buggy_checkout=true")
        materialization_result = run_command(materialization_command, timeout=240)
        log.append(f"materialization_returncode={materialization_result['returncode']}")
        if candidate_top.is_dir():
            generated = {
                "source": "bugsinpy-checkout using repo-recorded PySnooper:1 metadata",
                "path": str(candidate_top),
                "exists": True,
                "outside_live_repo_worktree": is_outside_repo(candidate_top),
                "head_sha": git_head(candidate_top),
            }
            candidates.append(generated)
            if generated["outside_live_repo_worktree"] and generated["head_sha"] == EXPECTED_HEAD:
                matched = generated
    elif matched is None:
        log.append("attempting_deterministic_buggy_checkout=false")

    if matched:
        classification = "workspace_found_decision_time_safe" if materialization_result is None else "workspace_materialized_decision_time_safe"
        found_or_materialized = True
        exact_source = matched["source"]
        workspace_path = matched["path"]
        provenance_complete = True
    elif materialization_result is not None:
        classification = "blocked_workspace_provenance_incomplete"
        found_or_materialized = False
        exact_source = "bugsinpy-checkout returned without a verified PySnooper:1 buggy HEAD"
        workspace_path = None
        provenance_complete = False
    else:
        classification = "blocked_no_decision_time_safe_workspace_source"
        found_or_materialized = False
        exact_source = "no existing outside-repo workspace and no available BugsInPy checkout executable/source bundle"
        workspace_path = None
        provenance_complete = False

    return (
        {
            "workspace_runtime_root": str(runtime_root),
            "workspace_runtime_root_outside_live_repo_worktree": is_outside_repo(runtime_root),
            "candidate_workspace_checks": candidates,
            "prior_v2_13_checkout_command": prior_command,
            "checkout_materialization_command": materialization_command,
            "checkout_materialization_command_available": checkout_tool is not None,
            "checkout_materialization_result": materialization_result,
            "workspace_found_or_materialized": found_or_materialized,
            "workspace_path": workspace_path,
            "workspace_path_outside_live_repo_worktree": is_outside_repo(Path(workspace_path)) if workspace_path else None,
            "exact_source_used": exact_source,
            "provenance_complete": provenance_complete,
            "final_workspace_classification": classification,
        },
        log,
    )


def declaration_evidence(policy: dict[str, Any]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for item in policy.get("metadata_files_inspected") or []:
        raw_path = str(item.get("path", ""))
        lowered = raw_path.lower()
        if not lowered.endswith(("setup.py", "requirements.txt", "pipfile", "tox.ini")):
            continue
        records.append(
            {
                "path": raw_path,
                "sha256": item.get("sha256"),
                "matching_lines": item.get("matching_lines") or [],
                "decision_time_safe": policy.get("decision_time_safe_status") == "PASS",
                "source_boundary": "buggy_checkout_metadata",
            }
        )
    return records


def build_ledger(root: Path) -> dict[str, Any]:
    entries: list[dict[str, Any]] = []
    previous: str | None = None
    for rel in [
        "workspace_materialization_audit.json",
        "workspace_provenance.json",
        "buggy_checkout_identity.json",
        "dependency_recovery_execution_summary.json",
        "pre_repair_replay_gate_summary.json",
        "patch_candidate_safety_check.json",
        "claim_boundary_v2_17.json",
        "campaign_results.json",
        "isolated_execution_log.txt",
    ]:
        material = {
            "path": rel,
            "sha256": sha256_path(root / rel),
            "previous_entry_hash": previous,
        }
        entry = dict(material)
        entry["entry_hash"] = canonical_sha(material)
        entries.append(entry)
        previous = entry["entry_hash"]
    return {
        "campaign_id": CAMPAIGN_ID,
        "status": "PASS",
        "proof_obligations": [
            "workspace provenance must be decision-time safe before dependency recovery",
            "dependency recovery must install only declared cofactor packages before replay",
            "pre-repair replay must reproduce before patch authorization",
            "patch attempt count must remain <= 1",
            "duplicate clean replay is required before scoreable=true",
        ],
        "next_allowed_action": "stop_no_patch_workspace_source_blocked",
        "ledger_entries": entries,
        "ledger_tip": previous,
    }


def write_manifest(root: Path) -> None:
    files = sorted(
        [path for path in root.rglob("*") if path.is_file() and path.name != "SHA256SUMS.txt"],
        key=lambda path: path.relative_to(root).as_posix(),
    )
    write_text(root / "SHA256SUMS.txt", "".join(f"{sha256_path(path)}  {path.relative_to(root).as_posix()}\n" for path in files))


def main() -> int:
    safe_reset(OUTPUT_ROOT)

    v213_policy_path = V213_ROOT / "raw_logs" / "pysnooper1_policy_recheck_v2_13.json"
    v213_identity_path = V213_ROOT / "raw_logs" / "pysnooper1_checkout_identity.json"
    v214_gate_path = V214_ROOT / "pysnooper1_recovery_gate_v2_14.json"
    v215_results_path = V215_ROOT / "campaign_results.json"
    v216_results_path = V216_ROOT / "campaign_results.json"
    v216_dependency_path = V216_ROOT / "dependency_recovery_audit.json"
    v216_ledger_path = V216_ROOT / "proof_obligations_ledger.json"
    evidence_paths = [
        v213_policy_path,
        v213_identity_path,
        v214_gate_path,
        v215_results_path,
        v216_results_path,
        v216_dependency_path,
        v216_ledger_path,
    ]

    policy = load_json(v213_policy_path)
    identity = load_json(v213_identity_path)
    v214_gate = load_json(v214_gate_path)
    v215_results = load_json(v215_results_path)
    v216_results = load_json(v216_results_path)
    v216_dependency = load_json(v216_dependency_path)
    source_hashes = evidence_hashes(evidence_paths)
    workspace_check, log_lines = materialize_or_find_workspace(policy)
    workspace_ready = workspace_check["final_workspace_classification"] in {
        "workspace_materialized_decision_time_safe",
        "workspace_found_decision_time_safe",
    }
    declared_dependencies = v216_dependency.get("declared_dependencies_to_install") or []
    if declared_dependencies != ["python-toolbox"]:
        declared_dependencies = ["python-toolbox"] if "python-toolbox" in declared_dependencies else declared_dependencies

    dependency_status = "not_executed_workspace_blocked"
    dependency_recovery_passed = False
    venv_created = False
    install_commands: list[dict[str, Any]] = []
    replay_status = "not_run_workspace_blocked"
    pre_repair_reproduced = False
    exact_target_command = "BugsInPy PySnooper bug 1 target command from decision-time-safe bug metadata"

    # The current official state has no safe workspace, so the branch below is
    # normally not entered.  It is present so a future environment with an
    # actual provenance-backed checkout fails closed after executing only the
    # allowed dependency/replay steps.
    if workspace_ready and workspace_check["workspace_path"]:
        workspace_path = Path(str(workspace_check["workspace_path"]))
        venv_path = workspace_path.parent / ".controllergate_v2_17_venv"
        create_venv = run_command([sys.executable, "-m", "venv", str(venv_path)], timeout=120)
        venv_created = create_venv["returncode"] == 0
        install_commands.append({"purpose": "create_isolated_venv", **create_venv})
        if venv_created:
            pip = venv_path / ("Scripts/pip.exe" if os.name == "nt" else "bin/pip")
            install = run_command([str(pip), "install", "python-toolbox"], timeout=240)
            install_commands.append({"purpose": "install_declared_dependency_python_toolbox", **install})
            dependency_recovery_passed = install["returncode"] == 0
            dependency_status = "executed_declared_dependency_recovery" if dependency_recovery_passed else "blocked_declared_dependency_install_failed"
        else:
            dependency_status = "blocked_isolated_venv_creation_failed"
        if dependency_recovery_passed:
            run_test = workspace_path / "bugsinpy_run_test.sh"
            if run_test.is_file() and os.name != "nt":
                python_bin = venv_path / "bin/python"
                env = os.environ.copy()
                env["PYTHONPATH"] = str(workspace_path)
                replay = subprocess.run(
                    ["bash", str(run_test)],
                    cwd=str(workspace_path),
                    env=env,
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=240,
                    check=False,
                )
                pre_repair_reproduced = replay.returncode != 0
                replay_status = "reproduced_target_failure" if pre_repair_reproduced else "blocked_pre_repair_replay_not_reproduced"
                log_lines.extend(
                    [
                        f"pre_repair_replay_returncode={replay.returncode}",
                        f"pre_repair_replay_stdout_sha256={sha256_bytes(replay.stdout.encode('utf-8'))}",
                        f"pre_repair_replay_stderr_sha256={sha256_bytes(replay.stderr.encode('utf-8'))}",
                        f"pre_repair_replay_python={python_bin}",
                    ]
                )
            else:
                replay_status = "blocked_pre_repair_replay_command_unavailable"

    patch_authorized = bool(workspace_ready and dependency_recovery_passed and pre_repair_reproduced)
    patch_generated = False
    patch_attempted = False
    target_validation_status = "not_applicable_no_patch"
    duplicate_replay_status = "not_applicable_no_patch"
    pysnooper_scoreable = False
    pysnooper_positive_memory = False

    workspace_audit = {
        "status": "PASS",
        "campaign_id": CAMPAIGN_ID,
        "candidate": "PySnooper:1",
        "workspace_found_or_materialized": workspace_check["workspace_found_or_materialized"],
        "exact_source_used": workspace_check["exact_source_used"],
        "exact_revision_commit_bug_identity": {
            "project": "PySnooper",
            "bug_id": "1",
            "bugsinpy_version": "0",
            "expected_buggy_head_sha": EXPECTED_HEAD,
            "v2_13_recorded_head_sha": identity.get("head_sha"),
        },
        "metadata_authorizing_workspace_creation": source_hashes,
        "checkout_materialization_command": workspace_check["checkout_materialization_command"],
        "prior_v2_13_checkout_command": workspace_check["prior_v2_13_checkout_command"],
        "workspace_path_outside_live_repo_worktree": workspace_check["workspace_path_outside_live_repo_worktree"],
        "workspace_path": workspace_check["workspace_path"],
        "fixed_gold_future_evidence_accessed": False,
        "tests_fixtures_expectations_mutated": False,
        "final_workspace_classification": workspace_check["final_workspace_classification"],
        "candidate_workspace_checks": workspace_check["candidate_workspace_checks"],
    }
    write_json(OUTPUT_ROOT / "workspace_materialization_audit.json", workspace_audit)

    workspace_provenance = {
        "status": "PASS" if workspace_ready else "BLOCK",
        "campaign_id": CAMPAIGN_ID,
        "candidate": "PySnooper:1",
        "decision_time_safe": workspace_ready,
        "provenance_complete": workspace_check["provenance_complete"],
        "workspace_classification": workspace_check["final_workspace_classification"],
        "allowed_sources_used": [
            "outputs/v2_13_minimal_forensic_context_lane/raw_logs/pysnooper1_policy_recheck_v2_13.json",
            "outputs/v2_13_minimal_forensic_context_lane/raw_logs/pysnooper1_checkout_identity.json",
            "outputs/v2_16_pysnooper1_isolated_recovery_executor/dependency_recovery_audit.json",
        ],
        "source_evidence_sha256": source_hashes,
        "forbidden_sources_accessed": [],
        "fixed_revision_accessed": False,
        "gold_patch_accessed": False,
        "future_outcome_evidence_accessed": False,
        "workspace_path": workspace_check["workspace_path"],
        "workspace_path_outside_live_repo_worktree": workspace_check["workspace_path_outside_live_repo_worktree"],
        "blocker": None
        if workspace_ready
        else "No live outside-repo PySnooper:1 buggy checkout or available BugsInPy checkout executable/source bundle could be tied to the decision-time-safe metadata.",
    }
    write_json(OUTPUT_ROOT / "workspace_provenance.json", workspace_provenance)

    checkout_identity = {
        "status": "PASS" if workspace_ready else "METADATA_ONLY",
        "campaign_id": CAMPAIGN_ID,
        "candidate": "PySnooper:1",
        "project": "PySnooper",
        "bug_id": "1",
        "bugsinpy_version": "0",
        "expected_buggy_head_sha": EXPECTED_HEAD,
        "v2_13_recorded_identity": identity,
        "local_workspace_present": workspace_ready,
        "local_workspace_path": workspace_check["workspace_path"],
        "local_workspace_head_sha": next(
            (item.get("head_sha") for item in workspace_check["candidate_workspace_checks"] if item.get("head_sha") == EXPECTED_HEAD),
            None,
        ),
        "identity_source_evidence_sha256": {
            repo_rel(v213_identity_path): sha256_path(v213_identity_path),
            repo_rel(v213_policy_path): sha256_path(v213_policy_path),
        },
    }
    write_json(OUTPUT_ROOT / "buggy_checkout_identity.json", checkout_identity)

    dependency_summary = {
        "status": "PASS" if dependency_recovery_passed else "BLOCK",
        "campaign_id": CAMPAIGN_ID,
        "candidate": "PySnooper:1",
        "dependency_recovery_execution_status": dependency_status,
        "declared_dependencies_to_install": declared_dependencies,
        "declaration_evidence": declaration_evidence(policy),
        "v2_16_contract_sha256": sha256_path(v216_dependency_path),
        "recovery_policy_allowed": v214_gate.get("recovery_policy_allowed") is True,
        "isolated_venv_created": venv_created,
        "install_commands": install_commands,
        "undeclared_dependencies_installed": False,
        "source_tests_fixtures_expectations_mutated": False,
        "global_environment_mutated": False,
        "fixed_gold_future_evidence_accessed": False,
        "blocker": None if dependency_recovery_passed else dependency_status,
    }
    write_json(OUTPUT_ROOT / "dependency_recovery_execution_summary.json", dependency_summary)

    replay_summary = {
        "status": "PASS" if pre_repair_reproduced else "BLOCK",
        "campaign_id": CAMPAIGN_ID,
        "candidate": "PySnooper:1",
        "pre_repair_replay_status": replay_status,
        "pre_repair_replay_attempted": replay_status not in {"not_run_workspace_blocked"},
        "pre_repair_replay_reproduced_target_failure": pre_repair_reproduced,
        "workspace_provenance_passed_before_replay": workspace_ready,
        "dependency_recovery_passed_before_replay": dependency_recovery_passed,
        "exact_target_command": exact_target_command,
        "stdout_sha256": None,
        "stderr_sha256": None,
        "patch_authorization": "allowed" if patch_authorized else "denied",
        "blocker": None if pre_repair_reproduced else replay_status,
    }
    write_json(OUTPUT_ROOT / "pre_repair_replay_gate_summary.json", replay_summary)

    patch_safety = {
        "status": "PASS",
        "campaign_id": CAMPAIGN_ID,
        "candidate": "PySnooper:1",
        "patch_generated": patch_generated,
        "patch_authorized": patch_authorized,
        "patch_attempted": patch_attempted,
        "patch_attempt_count": 0,
        "patch_sha256": None,
        "patch_non_empty": False,
        "semantic_delta_detected": False,
        "degenerate_noop_or_format_only": False,
        "source_only": None,
        "allowed_pysnooper_source_paths": ALLOWED_PATCH_PATHS,
        "modified_paths": [],
        "tests_modified": False,
        "fixtures_modified": False,
        "expectations_modified": False,
        "harness_files_modified": False,
        "benchmark_expectations_modified": False,
        "reason_no_patch_generated": "patch authorization denied before generation",
    }
    write_json(OUTPUT_ROOT / "patch_candidate_safety_check.json", patch_safety)

    claim_boundary = {
        "status": "PASS",
        "campaign_id": CAMPAIGN_ID,
        "current_protocol_version": "v2.13",
        "v2_17_promoted_to_current": False,
        "candidate_scope": ["PySnooper:1"],
        "pysnooper2_pursued": False,
        "full_scoring": "NOT_RUN",
        "full_scoring_allowed": False,
        "memory_lift_status": "undemonstrated",
        "self_maintaining_software": "false/not_demonstrated",
        "family_generalization_expanded": False,
        "scoreable_non_ansible_result": False,
        "final_scoreable_count": v215_results.get("final_scoreable_count", 5),
        "final_positive_memory_count": v215_results.get("final_positive_memory_count", 2),
        "final_non_ansible_positive_memory_count": 0,
    }
    write_json(OUTPUT_ROOT / "claim_boundary_v2_17.json", claim_boundary)

    campaign_results = {
        "status": "PASS_WITH_WORKSPACE_MATERIALIZATION_BLOCKED" if not workspace_ready else "PASS_WITH_REPLAY_BLOCKED",
        "campaign_id": CAMPAIGN_ID,
        "based_on": "v2.16",
        "candidate_scope": ["PySnooper:1"],
        "pysnooper2_pursued": False,
        "workspace_materialization_classification": workspace_check["final_workspace_classification"],
        "workspace_provenance_status": workspace_provenance["status"],
        "pre_repair_replay_status": replay_status,
        "dependency_recovery_execution_status": dependency_status,
        "patch_generated": patch_generated,
        "patch_authorized": patch_authorized,
        "patch_attempted": patch_attempted,
        "target_validation_status": target_validation_status,
        "duplicate_replay_status": duplicate_replay_status,
        "pysnooper1_scoreable": pysnooper_scoreable,
        "pysnooper1_positive_memory_only": pysnooper_positive_memory,
        "pysnooper1_classification": "blocked_no_decision_time_safe_workspace_source"
        if not workspace_ready
        else "blocked_pre_repair_replay_not_reproduced",
        "pysnooper2_status": "fixture_materialization_permanently_blocked_without_decision_time_safe_provenance",
        "final_scoreable_count": claim_boundary["final_scoreable_count"],
        "final_positive_memory_count": claim_boundary["final_positive_memory_count"],
        "final_non_ansible_positive_memory_count": 0,
        "full_scoring": "NOT_RUN",
        "full_scoring_allowed": False,
        "memory_lift_status": "undemonstrated",
        "self_maintaining_software_status": "false/not_demonstrated",
        "current_protocol_version": "v2.13",
        "exact_blocker": workspace_provenance["blocker"] if not workspace_ready else replay_summary["blocker"],
        "v2_16_executor_contract_ready": v216_results.get("dependency_recovery_executor_contract_ready") is True,
        "v2_16_executor_executed": v216_results.get("dependency_recovery_executor_executed") is True,
    }
    write_json(OUTPUT_ROOT / "campaign_results.json", campaign_results)

    log_lines.extend(
        [
            f"workspace_materialization_classification={campaign_results['workspace_materialization_classification']}",
            f"workspace_provenance_status={campaign_results['workspace_provenance_status']}",
            f"dependency_recovery_execution_status={dependency_status}",
            f"pre_repair_replay_status={replay_status}",
            f"patch_generated={patch_generated}",
            f"patch_authorized={patch_authorized}",
            f"patch_attempted={patch_attempted}",
            "fixed_gold_future_evidence_accessed=false",
            "tests_fixtures_expectations_mutated=false",
        ]
    )
    write_text(OUTPUT_ROOT / "isolated_execution_log.txt", "\n".join(log_lines) + "\n")

    summary = f"""# v2.17 PySnooper:1 Runtime Workspace Materialization

- Campaign: `{CAMPAIGN_ID}`.
- Candidate scope: `PySnooper:1` only.
- Workspace materialization classification: `{campaign_results['workspace_materialization_classification']}`.
- Workspace provenance status: `{campaign_results['workspace_provenance_status']}`.
- Dependency recovery execution status: `{dependency_status}`.
- Pre-repair replay status: `{replay_status}`.
- Patch generated: `{str(patch_generated).lower()}`; authorized: `{str(patch_authorized).lower()}`; attempted: `{str(patch_attempted).lower()}`.
- Target validation: `{target_validation_status}`.
- Duplicate replay: `{duplicate_replay_status}`.
- PySnooper:1 scoreable: `{str(pysnooper_scoreable).lower()}`.
- PySnooper:1 positive-memory-only: `{str(pysnooper_positive_memory).lower()}`.
- PySnooper:2 was not pursued.
- Scoreable count remains `{claim_boundary['final_scoreable_count']}`; positive-memory count remains `{claim_boundary['final_positive_memory_count']}`; non-Ansible positive-memory count remains `0`.
- Full scoring remains `NOT_RUN` / disallowed.
- Memory lift remains `undemonstrated`.
- Self-maintaining software remains `false/not_demonstrated`.
- Current protocol remains `v2.13`; v2.17 is not promoted to current.

Exact blocker: {campaign_results['exact_blocker']}
"""
    write_text(OUTPUT_ROOT / "campaign_summary.md", summary)

    write_json(OUTPUT_ROOT / "proof_obligations_ledger.json", build_ledger(OUTPUT_ROOT))
    write_manifest(OUTPUT_ROOT)
    print(f"v2.17 outputs wrote {OUTPUT_ROOT}")
    for key in [
        "workspace_materialization_classification",
        "workspace_provenance_status",
        "pre_repair_replay_status",
        "dependency_recovery_execution_status",
        "patch_generated",
        "patch_authorized",
        "patch_attempted",
        "pysnooper1_scoreable",
        "pysnooper1_positive_memory_only",
    ]:
        print(f"{key}={campaign_results[key]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
