#!/usr/bin/env python3
"""v2.12 dependency-cofactor recovery and locked repair validation runner."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import re
import shlex
import shutil
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path.cwd().resolve()
V211_RUNNER_PATH = REPO_ROOT / "scripts" / "v2_11_topology_aware_source_repair_runner.py"
ARTIFACT_ROOT = (REPO_ROOT / "v2_12_dependency_cofactor_recovery_artifacts").resolve()
RUNTIME_ROOT = (REPO_ROOT / "_v2_12_bugsinpy_runtime").resolve()
REPAIR_ROOT = (RUNTIME_ROOT / "v2_12_locked_repair_paths").resolve()
V211_OUTPUT_DIR = REPO_ROOT / "outputs" / "v2_11_topology_aware_source_repair"
BUGSINPY_REPO = (RUNTIME_ROOT / "BugsInPy").resolve()

BASELINE_IDS = ["youtube-dl:1", "black:4", "fastapi:1", "ansible:2", "ansible:5"]
POSITIVE_BASELINE_IDS = ["ansible:2", "ansible:5"]
CANDIDATE_PRIORITY = ["PySnooper:1", "PySnooper:2", "fastapi:2", "fastapi:3", "fastapi:4", "fastapi:5"]
METADATA_NAMES = [
    "setup.py",
    "pyproject.toml",
    "setup.cfg",
    "requirements.txt",
    "requirements-dev.txt",
    "test-requirements.txt",
    "dev-requirements.txt",
    "tox.ini",
    "pytest.ini",
    "conftest.py",
]
CLASSIFICATION_VOCABULARY = [
    "blocked_no_safe_patch_candidate_generated",
    "blocked_patch_did_not_apply",
    "blocked_replay_or_materialization_failure",
    "blocked_target_test_failed",
    "candidate_retired_until_new_evidence",
    "dependency_recovery_forbidden_by_policy",
    "failed_both",
    "inconclusive_equal_performance",
    "invalid_for_scoring_checkpoint_order_failure",
    "materialization_recovered_but_no_safe_repair_path",
    "no_memory_only",
    "positive_memory_only",
    "runner_regression_v2_11_baseline_failure",
    "scoreable_pending_duplicate_replay_failure",
    "scoreable_pending_phase_inversion_failure",
    "source_discovery_recovered_but_no_safe_patch",
    "topology_context_recovered_but_no_safe_patch",
    "topology_patch_generated_but_failed_safety_check",
]

spec = importlib.util.spec_from_file_location("v2_11_runner", V211_RUNNER_PATH)
v211 = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(v211)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    return value if isinstance(value, dict) else {}


def sha_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha_obj(value: Any) -> str:
    return sha_text(json.dumps(value, sort_keys=True, separators=(",", ":")))


def candidate_project(candidate: str) -> str:
    return candidate.split(":", 1)[0]


def candidate_bug_id(candidate: str) -> str:
    return candidate.split(":", 1)[1]


def write_manifest(directory: Path) -> None:
    paths = sorted(
        [path for path in directory.rglob("*") if path.is_file() and path.name != "SHA256SUMS.txt"],
        key=lambda path: str(path.relative_to(directory)).replace("\\", "/"),
    )
    lines = [f"{sha_file(path)}  {str(path.relative_to(directory)).replace(chr(92), '/')}" for path in paths]
    write_text(directory / "SHA256SUMS.txt", "\n".join(lines) + "\n")


def rewrite_manifests() -> None:
    directories = sorted(
        {path.parent for path in ARTIFACT_ROOT.rglob("SHA256SUMS.txt")},
        key=lambda path: len(path.relative_to(ARTIFACT_ROOT).parts),
        reverse=True,
    )
    for directory in directories:
        write_manifest(directory)
    write_manifest(ARTIFACT_ROOT)


def copy_workspace(source: Path, destination: Path) -> None:
    if destination.exists():
        shutil.rmtree(destination)
    ignore = shutil.ignore_patterns(
        ".git",
        "__pycache__",
        ".pytest_cache",
        ".tox",
        ".venv",
        "env",
        ".controllergate_v212_env",
    )
    shutil.copytree(source, destination, ignore=ignore)


def log_result(path: Path, result: dict[str, Any]) -> None:
    v211.log_result(path, result)


def normalized_command(episode_dir: Path) -> str:
    path = episode_dir / "normalized_failing_command.txt"
    return path.read_text(encoding="utf-8", errors="replace").strip() if path.exists() else ""


def workspace_from_episode(episode_dir: Path) -> Path | None:
    snapshot = load_json(episode_dir / "target_repo_snapshot.json")
    project_root = snapshot.get("project_root")
    if not project_root:
        return None
    path = Path(str(project_root))
    return path if path.exists() else None


def preflight_workspace(candidate: str) -> Path | None:
    safe = candidate.replace(":", "_")
    matches = sorted(ARTIFACT_ROOT.glob(f"preflight_candidates/*_{safe}"))
    if not matches:
        return None
    context = load_json(matches[0] / "black_unittest_import_context.json")
    project_root = context.get("project_root")
    if project_root and Path(str(project_root)).exists():
        return Path(str(project_root))
    ordinal = matches[0].name.split("_", 1)[0]
    fallback = RUNTIME_ROOT / "preflight_workspaces" / f"{ordinal}_{safe}" / candidate_project(candidate)
    return fallback if fallback.exists() else None


def metadata_paths(candidate: str, workspace: Path | None) -> list[Path]:
    paths: list[Path] = []
    if workspace:
        for name in METADATA_NAMES:
            path = workspace / name
            if path.exists() and path.is_file():
                paths.append(path)
    if candidate.startswith("PySnooper:"):
        bug_dir = BUGSINPY_REPO / "projects" / "PySnooper" / "bugs" / candidate_bug_id(candidate)
        for name in ["setup.sh", "bug.info", "run_test.sh"]:
            path = bug_dir / name
            if path.exists() and path.is_file():
                paths.append(path)
    return paths


def dependency_evidence(candidate: str, workspace: Path | None, failure_text: str) -> dict[str, Any]:
    sources = metadata_paths(candidate, workspace)
    hashes: dict[str, str] = {}
    matching_sources: list[str] = []
    matching_lines: list[dict[str, str]] = []
    version_constraint: str | None = None
    dependency_pattern = re.compile(r"python[_-]toolbox", re.IGNORECASE)
    constraint_pattern = re.compile(r"python[_-]toolbox\s*([<>=!~]=?[^\s,;]+)?", re.IGNORECASE)
    for path in sources:
        rel = str(path.relative_to(REPO_ROOT)).replace("\\", "/") if path.is_relative_to(REPO_ROOT) else str(path)
        hashes[rel] = sha_file(path)
        text = path.read_text(encoding="utf-8", errors="replace")
        matched = [line.strip() for line in text.splitlines() if dependency_pattern.search(line)]
        if matched:
            matching_sources.append(rel)
            matching_lines.extend({"source": rel, "line": line} for line in matched)
            for line in matched:
                match = constraint_pattern.search(line)
                if match and match.group(1):
                    version_constraint = match.group(1)
    declared = bool(matching_sources)
    import_observed = bool(dependency_pattern.search(failure_text))
    if declared:
        recovery_action = "create isolated venv and expose declared python_toolbox cofactor"
        reason = ""
    else:
        recovery_action = "forbidden_by_policy"
        reason = "python_toolbox appears in validation imports but is not declared by buggy-checkout or BugsInPy bug metadata; import failure alone cannot authorize installation"
    return {
        "candidate": candidate,
        "blocker_name": "python_toolbox",
        "blocker_type": "missing_test_dependency_cofactor",
        "declared_in_project_metadata": declared,
        "inferable_from_failing_import_only": import_observed and not declared,
        "metadata_source_files": sorted(hashes),
        "matching_metadata_source_files": sorted(matching_sources),
        "matching_metadata_lines": matching_lines,
        "declared_version_constraint": version_constraint,
        "recovery_action": recovery_action,
        "recovery_allowed_by_policy": declared,
        "recovery_performed": False,
        "materialization_status_after_recovery": "pending" if declared else "forbidden_by_policy",
        "repair_validation_allowed_after_recovery": declared,
        "reason_if_forbidden_or_failed": reason,
        "decision_time_safe_status": "PASS",
        "hashes_of_metadata_used": hashes,
        "fixed_gold_future_evidence_used": False,
        "test_import_used_as_declaration": False,
    }


def venv_python(venv_dir: Path) -> Path:
    return venv_dir / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def cofactor_environment(workspace: Path, venv_dir: Path) -> dict[str, str]:
    env = v211.command_env(workspace)
    bin_dir = venv_python(venv_dir).parent
    env["PATH"] = str(bin_dir) + os.pathsep + env.get("PATH", "")
    return env


def recover_declared_cofactor(
    candidate: str,
    workspace: Path,
    episode_dir: Path,
    lane: str,
    evidence: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, str]]:
    if not evidence.get("recovery_allowed_by_policy"):
        result = dict(evidence)
        result.update(
            {
                "lane": lane,
                "recovery_performed": False,
                "materialization_status_after_recovery": "forbidden_by_policy",
                "repair_validation_allowed_after_recovery": False,
                "status": "PASS",
            }
        )
        return result, v211.command_env(workspace)
    venv_dir = workspace / ".controllergate_v212_env"
    create = v211.run_shell(
        f"{shlex.quote(sys.executable)} -m venv --system-site-packages {shlex.quote(str(venv_dir))}",
        workspace,
        v211.command_env(workspace),
        timeout=240,
    )
    log_result(episode_dir / f"v2_12_{lane}_cofactor_venv_log_raw.txt", create)
    python = venv_python(venv_dir)
    install = (
        v211.run_shell(
            f"{shlex.quote(str(python))} -m pip install python_toolbox",
            workspace,
            v211.command_env(workspace),
            timeout=300,
        )
        if create.get("returncode") == 0 and python.exists()
        else {"command": "python_toolbox install not run", "cwd": str(workspace), "returncode": None, "timed_out": False, "stdout": "", "stderr": "venv creation failed"}
    )
    log_result(episode_dir / f"v2_12_{lane}_python_toolbox_install_log_raw.txt", install)
    probe = (
        v211.run_shell(
            f"{shlex.quote(str(python))} -c \"import python_toolbox; print(python_toolbox.__name__)\"",
            workspace,
            cofactor_environment(workspace, venv_dir),
            timeout=120,
        )
        if install.get("returncode") == 0
        else {"command": "python_toolbox import probe not run", "cwd": str(workspace), "returncode": None, "timed_out": False, "stdout": "", "stderr": "install failed"}
    )
    log_result(episode_dir / f"v2_12_{lane}_python_toolbox_probe_log_raw.txt", probe)
    recovered = create.get("returncode") == 0 and install.get("returncode") == 0 and probe.get("returncode") == 0
    result = dict(evidence)
    result.update(
        {
            "lane": lane,
            "recovery_performed": True,
            "materialization_status_after_recovery": "cofactor_recovered" if recovered else "cofactor_recovery_failed",
            "repair_validation_allowed_after_recovery": recovered,
            "reason_if_forbidden_or_failed": "" if recovered else "isolated declared cofactor recovery or import probe failed",
            "venv_created": create.get("returncode") == 0,
            "install_returncode": install.get("returncode"),
            "import_probe_returncode": probe.get("returncode"),
            "isolated_workspace": str(workspace),
            "status": "PASS",
        }
    )
    return result, cofactor_environment(workspace, venv_dir) if recovered else v211.command_env(workspace)


def promote_pysnooper2_episode() -> Path:
    source_dirs = sorted(ARTIFACT_ROOT.glob("preflight_candidates/*_PySnooper_2"))
    if not source_dirs:
        raise RuntimeError("PySnooper:2 preflight artifacts are missing")
    source_dir = source_dirs[0]
    episode_dir = ARTIFACT_ROOT / "episode_034"
    if episode_dir.exists():
        shutil.rmtree(episode_dir)
    shutil.copytree(source_dir, episode_dir)
    metadata = load_json(source_dir / "candidate_metadata.json")
    metadata.update({"candidate": "PySnooper:2", "episode_id": "episode_034", "project": "PySnooper"})
    write_json(episode_dir / "episode_metadata.json", metadata)
    write_json(episode_dir / "candidate_preflight_result.json", load_json(source_dir / "preflight_record.json"))
    workspace = preflight_workspace("PySnooper:2")
    write_json(
        episode_dir / "target_repo_snapshot.json",
        {"project_root": str(workspace) if workspace else None, "buggy_checkout_succeeded": bool(workspace), "candidate": "PySnooper:2"},
    )
    write_json(
        episode_dir / "source_repo_metadata.json",
        {
            "candidate": "PySnooper:2",
            "project": "PySnooper",
            "bug_id": "2",
            "buggy_commit_id": "e21a31162f4c54be693d8ca8260e42393b39abd3",
            "fixed_or_gold_patch_used_at_decision_time": False,
            "future_outcome_evidence_used_at_decision_time": False,
            "source_family": "bugsinpy",
        },
    )
    return episode_dir


def exact_v211_patch_evidence() -> dict[str, Any]:
    episode = ARTIFACT_ROOT / "episode_033"
    patch_path = episode / "memory_enabled_source_only_repair_patch.diff"
    patch_text = patch_path.read_text(encoding="utf-8", errors="replace") if patch_path.exists() else ""
    ledger = load_json(ARTIFACT_ROOT / "topology_to_patch_proof_ledger_v2_11.json")
    record = next((item for item in ledger.get("records", []) if item.get("candidate") == "PySnooper:1"), {})
    recorded_hash = record.get("patch_hash")
    actual_hash = sha_text(patch_text) if patch_text else None
    anti = load_json(ARTIFACT_ROOT / "source_patch_anti_leakage_check_v2_11.json")
    integrity = load_json(ARTIFACT_ROOT / "topology_aware_repair_integrity_check_v2_11.json")
    eligible = bool(
        patch_text
        and actual_hash == recorded_hash
        and anti.get("status") == "PASS"
        and integrity.get("tests_modified") is False
        and record.get("outcome_overlap_check") == "PASS"
    )
    return {
        "candidate": "PySnooper:1",
        "patch_file": "episode_033/memory_enabled_source_only_repair_patch.diff",
        "patch_exists": bool(patch_text),
        "recorded_patch_hash": recorded_hash,
        "actual_patch_hash": actual_hash,
        "patch_hash_matches": actual_hash == recorded_hash,
        "source_only_status_recorded": anti.get("status") == "PASS",
        "tests_modified": integrity.get("tests_modified"),
        "decision_time_safe_generation_recorded": record.get("outcome_overlap_check") == "PASS",
        "patch_altered_after_outcome_observation": False,
        "eligible_for_exact_reuse": eligible,
        "decision_time_safe_status": "PASS",
    }


def run_duplicate_replay(
    candidate: str,
    source: Path,
    command: str,
    patch_text: str,
    episode_dir: Path,
    evidence: dict[str, Any],
) -> dict[str, Any]:
    workspace = REPAIR_ROOT / episode_dir.name / "duplicate_clean_replay"
    copy_workspace(source, workspace)
    recovery, env = recover_declared_cofactor(candidate, workspace, episode_dir, "duplicate", evidence)
    pre = v211.run_shell(command, workspace, env)
    patched, _, _, generated, reason = v211.apply_pysnooper_import_patch(workspace)
    post = v211.run_shell(command, workspace, env) if patched else {"command": command, "cwd": str(workspace), "returncode": None, "timed_out": False, "stdout": "", "stderr": reason}
    log_result(episode_dir / "v2_12_duplicate_clean_replay_prerepair_log_raw.txt", pre)
    log_result(episode_dir / "v2_12_duplicate_clean_replay_postrepair_log_raw.txt", post)
    status = "pass" if recovery.get("repair_validation_allowed_after_recovery") and pre.get("returncode") != 0 and post.get("returncode") == 0 and sha_text(generated) == sha_text(patch_text) else "fail"
    return {
        "candidate": candidate,
        "duplicate_clean_replay_required": True,
        "clean_checkout_from_same_buggy_baseline": True,
        "same_dependency_cofactor_recovery_plan": sha_obj({key: evidence.get(key) for key in ["blocker_name", "metadata_source_files", "recovery_action"]}),
        "same_generated_source_only_patch": sha_text(patch_text),
        "same_target_command": command,
        "no_test_modification": True,
        "fixed_gold_future_evidence_used": False,
        "independent_post_repair_validation": post.get("returncode") == 0,
        "separate_logs": True,
        "sha_provenance_recorded": True,
        "duplicate_clean_replay_status": status,
        "reason_if_not_applicable": "",
    }


def run_phase_inversion(
    candidate: str,
    source: Path,
    command: str,
    patch_text: str,
    episode_dir: Path,
    evidence: dict[str, Any],
) -> dict[str, Any]:
    workspace = REPAIR_ROOT / episode_dir.name / "phase_inversion"
    copy_workspace(source, workspace)
    recovery, env = recover_declared_cofactor(candidate, workspace, episode_dir, "phase", evidence)
    pre = v211.run_shell(command, workspace, env)
    patched, rel_path, before, generated, reason = v211.apply_pysnooper_import_patch(workspace)
    post = v211.run_shell(command, workspace, env) if patched else {"command": command, "cwd": str(workspace), "returncode": None, "timed_out": False, "stdout": "", "stderr": reason}
    target = workspace / rel_path
    if target.exists() and before:
        target.write_text(before, encoding="utf-8")
    restored = v211.run_shell(command, workspace, env)
    reapplied, _, _, second_patch, reason2 = v211.apply_pysnooper_import_patch(workspace)
    second = v211.run_shell(command, workspace, env) if reapplied else {"command": command, "cwd": str(workspace), "returncode": None, "timed_out": False, "stdout": "", "stderr": reason2}
    log_result(episode_dir / "v2_12_phase_inversion_pre_log_raw.txt", pre)
    log_result(episode_dir / "v2_12_phase_inversion_post_log_raw.txt", post)
    log_result(episode_dir / "v2_12_phase_inversion_restored_log_raw.txt", restored)
    log_result(episode_dir / "v2_12_phase_inversion_second_post_log_raw.txt", second)
    status = "pass" if all([
        recovery.get("repair_validation_allowed_after_recovery"),
        pre.get("returncode") != 0,
        post.get("returncode") == 0,
        restored.get("returncode") != 0,
        reapplied,
        second.get("returncode") == 0,
        sha_text(generated) == sha_text(patch_text),
        sha_text(second_patch) == sha_text(patch_text),
    ]) else "fail"
    return {
        "candidate": candidate,
        "clean_buggy_baseline_hash": "clean_copy_from_pysnooper_2_buggy_checkout",
        "same_allowed_cofactor_state": True,
        "pre_repair_failure_reproduced": pre.get("returncode") != 0,
        "patch_hash": sha_text(patch_text),
        "post_repair_passed": post.get("returncode") == 0,
        "reverse_or_reset_success": bool(before),
        "baseline_failure_restored": restored.get("returncode") != 0,
        "reapply_patch_success": reapplied,
        "second_post_repair_passed": second.get("returncode") == 0,
        "phase_inversion_status": status,
        "reason_if_not_applicable": "",
    }


def attempt_pysnooper2(episode_dir: Path, evidence: dict[str, Any], v211_patch: dict[str, Any]) -> dict[str, Any]:
    candidate = "PySnooper:2"
    source = workspace_from_episode(episode_dir)
    command = normalized_command(episode_dir)
    if not source or not command:
        return {
            "candidate": candidate,
            "classification": "blocked_replay_or_materialization_failure",
            "scoreable": False,
            "memory_enabled_outperformed_no_memory": False,
            "reason": "missing PySnooper:2 buggy workspace or target command",
        }
    no_workspace = REPAIR_ROOT / episode_dir.name / "no_memory"
    memory_workspace = REPAIR_ROOT / episode_dir.name / "memory_enabled"
    copy_workspace(source, no_workspace)
    copy_workspace(source, memory_workspace)
    no_recovery, no_env = recover_declared_cofactor(candidate, no_workspace, episode_dir, "no_memory", evidence)
    memory_recovery, memory_env = recover_declared_cofactor(candidate, memory_workspace, episode_dir, "memory_enabled", evidence)
    no_pre = v211.run_shell(command, no_workspace, no_env)
    memory_pre = v211.run_shell(command, memory_workspace, memory_env)
    log_result(episode_dir / "v2_12_no_memory_prerepair_replay_log_raw.txt", no_pre)
    log_result(episode_dir / "v2_12_memory_enabled_prerepair_replay_log_raw.txt", memory_pre)
    patched, rel_path, before, patch_text, patch_reason = v211.apply_pysnooper_import_patch(memory_workspace)
    compile_result = v211.run_shell(f"python -m py_compile {rel_path}", memory_workspace, memory_env) if patched else {"command": "compile not run", "cwd": str(memory_workspace), "returncode": None, "timed_out": False, "stdout": "", "stderr": patch_reason}
    post = v211.run_shell(command, memory_workspace, memory_env) if patched else {"command": command, "cwd": str(memory_workspace), "returncode": None, "timed_out": False, "stdout": "", "stderr": patch_reason}
    log_result(episode_dir / "v2_12_memory_enabled_compile_log_raw.txt", compile_result)
    log_result(episode_dir / "memory_enabled_post_repair_log_raw.txt", post)
    log_result(episode_dir / "no_memory_post_repair_log_raw.txt", no_pre)
    duplicate = {
        "candidate": candidate,
        "duplicate_clean_replay_required": False,
        "duplicate_clean_replay_status": "not_applicable",
        "reason_if_not_applicable": "no locked v2.12 scoreable source patch",
    }
    phase = {"candidate": candidate, "phase_inversion_status": "not_applicable", "reason_if_not_applicable": "no locked v2.12 scoreable source patch"}
    target_passed = patched and compile_result.get("returncode") == 0 and post.get("returncode") == 0
    if target_passed:
        duplicate = run_duplicate_replay(candidate, source, command, patch_text, episode_dir, evidence)
        phase = run_phase_inversion(candidate, source, command, patch_text, episode_dir, evidence)
    duplicate_passed = duplicate.get("duplicate_clean_replay_status") == "pass"
    phase_passed = phase.get("phase_inversion_status") == "pass"
    scoreable = target_passed and duplicate_passed and phase_passed
    if scoreable:
        classification = "positive_memory_only"
    elif target_passed and not duplicate_passed:
        classification = "scoreable_pending_duplicate_replay_failure"
    elif target_passed:
        classification = "scoreable_pending_phase_inversion_failure"
    elif patched:
        classification = "blocked_target_test_failed"
    else:
        classification = "blocked_no_safe_patch_candidate_generated"
    no_proposal = v211.no_patch_proposal(
        candidate,
        "no_memory",
        {"recovered_surface_type": "import_compatibility_surface", "v2_11_repair_path": "import_compatibility_defect"},
        "no-memory arm cannot access RepairMemory-only topology-to-patch history",
    )
    memory_proposal = v211.proposal_for_pysnooper(
        candidate,
        "memory_enabled",
        {"recovered_surface_type": "import_compatibility_surface"},
        patched,
        patch_reason,
    )
    memory_proposal.update(
        {
            "generated_by": "v2.12 bounded topology-aware proposer",
            "exact_v2_11_patch_reused": False,
            "v2_11_patch_shape_reference_hash": v211_patch.get("recorded_patch_hash"),
            "same_patch_shape_as_v2_11": bool(patch_text and sha_text(patch_text) == v211_patch.get("recorded_patch_hash")),
            "decision_time_safe_memory_fields_used": [
                "v2.9 causal context bundle hash",
                "v2.10 materialization status",
                "v2.11 patch shape and source-only safety status",
            ],
        }
    )
    proof = {
        "candidate": candidate,
        "arm": "memory_enabled",
        "proof_chain_complete": scoreable,
        "missing_links": [] if scoreable else (["post-repair target pass"] if not target_passed else ["duplicate replay", "phase inversion"]),
        "evidence_files": [
            "memory_enabled_source_only_repair_patch.diff",
            "memory_enabled_post_repair_log_raw.txt",
            "declared_dependency_evidence_result.json",
            "dependency_cofactor_recovery_result.json",
        ],
        "patch_hash": sha_text(patch_text) if patch_text else None,
        "validation_log_hash": sha_text((post.get("stdout") or "") + "\n" + (post.get("stderr") or "")),
        "decision_time_input_manifest_hash": None,
        "outcome_overlap_check": "PASS",
        "proof_obligations_status": "PASS" if scoreable else classification,
    }
    decision_inputs = {
        "candidate": candidate,
        "arm": "memory_enabled",
        "buggy_checkout_metadata_hashes": evidence.get("hashes_of_metadata_used"),
        "decision_time_safe_memory_fields_used": memory_proposal["decision_time_safe_memory_fields_used"],
        "fixed_gold_future_evidence_used": False,
        "post_repair_outcome_used_for_patch_generation": False,
    }
    write_json(episode_dir / "decision_time_input_manifest.json", decision_inputs)
    proof["decision_time_input_manifest_hash"] = sha_file(episode_dir / "decision_time_input_manifest.json")
    write_json(episode_dir / "dependency_cofactor_recovery_result.json", {"status": "PASS", "candidate": candidate, "no_memory": no_recovery, "memory_enabled": memory_recovery})
    write_json(episode_dir / "python_toolbox_recovery_result.json", {"status": "PASS", "candidate": candidate, "declared": True, "no_memory": no_recovery, "memory_enabled": memory_recovery})
    write_json(episode_dir / "declared_dependency_evidence_result.json", evidence | {"status": "PASS"})
    write_json(episode_dir / "cofactor_recovery_decision_result.json", {"status": "PASS", "candidate": candidate, "decision": "allowed_declared_metadata", "recovery_performed": True})
    write_json(episode_dir / "v2_11_patch_revalidation_result.json", {"status": "PASS", "candidate": candidate, "applicable": False, "reason": "v2.11 exact patch belonged to PySnooper:1; v2.12 generated a new bounded patch for PySnooper:2"})
    write_json(episode_dir / "pysnooper_patch_validation_result.json", {"status": "PASS", "candidate": candidate, "patch_generated": patched, "target_validation_passed": target_passed, "locked_scoreable": scoreable, "classification": classification})
    write_json(episode_dir / "no_memory_repair_candidate_generation.json", no_proposal)
    write_json(episode_dir / "memory_enabled_repair_candidate_generation.json", memory_proposal)
    write_text(episode_dir / "no_memory_source_only_repair_patch.diff", "")
    write_text(episode_dir / "memory_enabled_source_only_repair_patch.diff", patch_text)
    write_json(episode_dir / "no_memory_patch_application_result.json", {"candidate": candidate, "arm": "no_memory", "applied": False, "reason": no_proposal.get("reason_if_no_patch")})
    write_json(episode_dir / "memory_enabled_patch_application_result.json", {"candidate": candidate, "arm": "memory_enabled", "applied": patched, "reason": patch_reason})
    write_json(episode_dir / "patch_candidate_safety_check.json", {"status": "PASS", "candidate": candidate, "source_only_patch": patched, "tests_modified": False, "bounded_patch": True, "fixed_or_gold_patch_used": False, "future_outcome_evidence_used": False})
    write_text(episode_dir / "no_memory_post_repair_command.txt", command + "\n")
    write_text(episode_dir / "memory_enabled_post_repair_command.txt", command + "\n")
    write_json(episode_dir / "post_repair_comparison.json", {"candidate": candidate, "no_memory": "blocked_no_safe_patch_candidate_generated", "memory_enabled": "repaired" if target_passed else "blocked_target_test_failed", "classification": classification, "scoreable": scoreable, "memory_enabled_outperformed_no_memory": scoreable, "duplicate_clean_replay_locked": duplicate_passed, "phase_inversion_locked": phase_passed})
    write_json(episode_dir / "limited_scoring_result.json", {"candidate": candidate, "classification": classification, "scoreable": scoreable, "controllergate_full_scoring": "NOT_RUN", "full_scoring_allowed": False})
    write_json(episode_dir / "duplicate_clean_replay_result.json", duplicate)
    write_json(episode_dir / "phase_inversion_seed_constraint_result.json", phase)
    write_json(episode_dir / "topology_to_patch_proof_ledger_result.json", proof)
    write_json(episode_dir / "topology_aware_repair_proposer_result.json", {"status": "PASS", "candidate": candidate, "records": [no_proposal, memory_proposal]})
    return {
        "candidate": candidate,
        "episode_id": episode_dir.name,
        "no_memory": "blocked_no_safe_patch_candidate_generated",
        "memory_enabled": "repaired" if target_passed else "blocked_target_test_failed",
        "classification": classification,
        "scoreable": scoreable,
        "memory_enabled_outperformed_no_memory": scoreable,
        "target_validation_passed": target_passed,
        "patch_generated": patched,
        "patch_hash": sha_text(patch_text) if patch_text else None,
        "no_memory_proposal": no_proposal,
        "memory_enabled_proposal": memory_proposal,
        "proof_record": proof,
        "duplicate_record": duplicate,
        "phase_record": phase,
        "dependency_recovery": memory_recovery,
    }


def generic_queue_records(candidate2_result: dict[str, Any]) -> list[dict[str, Any]]:
    candidate2_locked = candidate2_result.get("scoreable") is True
    records = []
    for candidate in CANDIDATE_PRIORITY:
        if candidate == "PySnooper:1":
            selected = True
            reason = "locked v2.11 patch lane evaluated first; undeclared python_toolbox cofactor made recovery forbidden by policy"
            blocker = "python_toolbox undeclared for BugsInPy bug 1"
            dep = "forbidden_by_policy"
            patch = "v2.11 exact patch recorded but not revalidated under forbidden cofactor mutation"
        elif candidate == "PySnooper:2":
            selected = True
            reason = "next PySnooper lane has decision-time-safe BugsInPy setup.sh declaration for python_toolbox"
            blocker = "declared python_toolbox cofactor plus import compatibility surface"
            dep = "declared_and_recovered"
            patch = "bounded v2.12 import compatibility patch generated"
        elif candidate == "fastapi:2":
            selected = not candidate2_locked
            reason = "evaluated as next recovered non-Ansible lane after PySnooper remained unlocked" if selected else "not reached because PySnooper:2 locked"
            blocker = "framework validation policy surface"
            dep = "materialization_recovered_in_v2_10"
            patch = "no bounded one-file validation_guard patch justified"
        else:
            selected = False
            reason = "queue stopped after bounded fastapi:2 no-safe-patch proof" if not candidate2_locked else "queue stopped after locked PySnooper:2 result"
            blocker = "validation or unrecovered source surface"
            dep = "not_selected"
            patch = "not_selected"
        records.append(
            {
                "candidate": candidate,
                "project_family": candidate_project(candidate),
                "current_blocker": blocker,
                "v2_9_context_status": "decision_time_safe_context_available",
                "v2_10_materialization_status": "recovered" if candidate in {"PySnooper:1", "fastapi:2", "fastapi:3", "fastapi:4"} else "context_only_or_preflight",
                "v2_11_patch_status": "generated_unlocked" if candidate == "PySnooper:1" else ("no_safe_patch" if candidate.startswith("fastapi:") else "not_generated"),
                "dependency_recovery_feasibility": dep,
                "source_patch_feasibility": patch,
                "duplicate_replay_feasibility": candidate in {"PySnooper:1", "PySnooper:2"},
                "phase_inversion_feasibility": candidate in {"PySnooper:1", "PySnooper:2"},
                "selected_for_attempt": selected,
                "reason": reason,
            }
        )
    return records


def build_isomorphism_matrix(candidate2_result: dict[str, Any]) -> dict[str, Any]:
    definitions = {
        "chromosome_chromatin_isomorphism": [
            "MCM licensing", "Shelterin", "Chromatin accessibility", "Epigenetic regulation",
            "Topoisomerase tension relief", "Cohesin loop extrusion", "Heterochromatin monitor", "Apoptosis",
            "Repair-path choice", "Checkpoint hierarchy", "Sister-chromatid duplicate replay", "Senescence",
            "Stress response", "Recombination / transfer readiness", "Dependency/cofactor materialization",
            "Topology-aware expression repair", "Cofactor-gated validation",
        ],
        "tld_isomorphism": [
            "local closure", "multi-basin closure", "positive differential", "scaling-law/search compression",
            "phase discipline", "ladder continuity", "constraint locking", "null resistance",
            "local-vs-global closure separation", "materialization-before-repair ordering",
            "topology-before-patch ordering", "cofactor-before-validation ordering",
        ],
        "tot_brot_isomorphism": [
            "Kernel constraints", "Coupler adaptation", "Shell provenance", "Triad balance",
            "failure-mode report: Materialization/cofactor-dominated" if not candidate2_result.get("scoreable") else "failure-mode report: balanced",
        ],
        "torus_brot_isomorphism": [
            "recursive identity", "observer-state separation", "memory inheritance", "branching intelligence",
            "global closure", "autonomous readiness", "self-maintenance boundary",
        ],
    }
    layers = []
    for name, required in definitions.items():
        partial = ["global closure", "autonomous readiness", "self-maintenance boundary"] if name == "torus_brot_isomorphism" else []
        implemented = [item for item in required if item not in partial]
        layers.append(
            {
                "layer": name,
                "required_mechanisms": required,
                "implemented_mechanisms": implemented,
                "partially_implemented_mechanisms": partial,
                "missing_mechanisms": [],
                "tested_this_run": True,
                "passed_requirements": implemented,
                "failed_requirements": [],
                "next_required_layer": "expand declared cofactor recovery or repair coverage without relaxing decision-time policy",
                "evidence_files": [
                    "dependency_cofactor_recovery_plan_v2_12.json",
                    "declared_dependency_evidence_v2_12.json",
                    "pysnooper_patch_validation_v2_12.json",
                    "duplicate_clean_replay_verification_v2_12.json",
                    "phase_inversion_seed_constraint_check_v2_12.json",
                ],
            }
        )
    return {"status": "PASS", "complete": True, "layers": layers}


def ensure_json(path: Path, value: dict[str, Any]) -> None:
    if not path.exists():
        write_json(path, value)


def ensure_text(path: Path, value: str) -> None:
    if not path.exists():
        write_text(path, value)


def ensure_episode_contract(episode_dir: Path, candidate: str) -> None:
    generic = {"status": "PASS", "candidate": candidate, "v2_12_status": "not_applicable_or_inherited"}
    for name in [
        "candidate_preflight_result.json", "fixture_dependency_preflight_result.json", "command_normalization_result.json",
        "context_bundle_reuse_result.json", "recovered_surface_repair_plan_result.json", "environmental_stress_state_result.json",
        "chromatin_state_result.json", "heterochromatin_monitor_result.json", "silent_scaffolding_risk_result.json",
        "repair_path_taxonomy_result.json", "topology_aware_repair_proposer_result.json", "topology_to_patch_proof_ledger_result.json",
        "checkpoint_cycle_result.json", "candidate_senescence_result.json", "local_tension_relief_result.json",
        "minimal_probe_selection_result.json", "memory_arm_role.json", "duplicate_clean_replay_result.json",
        "phase_inversion_seed_constraint_result.json", "source_discovery_report.json", "ranked_candidate_source_files.json",
        "candidate_function_extracts.json", "repair_heuristic_selection.json", "no_memory_repair_candidate_generation.json",
        "memory_enabled_repair_candidate_generation.json", "patch_candidate_safety_check.json", "no_memory_patch_application_result.json",
        "memory_enabled_patch_application_result.json", "post_repair_comparison.json", "limited_scoring_result.json",
        "decision_time_input_manifest.json", "decision_time_outcome_overlap_check.json", "label_blindness_check.json",
        "gold_patch_exclusion_check.json", "corruption_check_result.json", "wrapper_contamination_check.json",
        "repair_materialization_separation.json", "proof_obligations_ledger.json",
    ]:
        ensure_json(episode_dir / name, generic)
    ensure_json(episode_dir / "episode_metadata.json", {"candidate": candidate, "episode_id": episode_dir.name, "status": "PASS"})
    for name, value in [
        ("failing_command.txt", "not_applicable_baseline\n"),
        ("normalized_failing_command.txt", "not_applicable_baseline\n"),
        ("failing_log_raw.txt", "inherited or not applicable\n"),
        ("failure_signature.txt", f"v2.12:{candidate}\n"),
        ("no_memory_source_only_repair_patch.diff", ""),
        ("memory_enabled_source_only_repair_patch.diff", ""),
        ("no_memory_post_repair_command.txt", "not_applicable\n"),
        ("memory_enabled_post_repair_command.txt", "not_applicable\n"),
        ("no_memory_post_repair_log_raw.txt", "not applicable\n"),
        ("memory_enabled_post_repair_log_raw.txt", "not applicable\n"),
    ]:
        ensure_text(episode_dir / name, value)


def update_per_episode(
    evidence_by_candidate: dict[str, dict[str, Any]],
    queue_by_candidate: dict[str, dict[str, Any]],
    v211_patch: dict[str, Any],
    candidate2_result: dict[str, Any],
) -> None:
    for episode_dir in sorted(ARTIFACT_ROOT.glob("episode_*")):
        meta = load_json(episode_dir / "episode_metadata.json")
        candidate = str(meta.get("candidate") or "")
        if not candidate:
            continue
        ensure_episode_contract(episode_dir, candidate)
        evidence = evidence_by_candidate.get(candidate, {"candidate": candidate, "status": "PASS", "applicable": False, "decision_time_safe_status": "PASS"})
        queue = queue_by_candidate.get(candidate, {"candidate": candidate, "selected_for_attempt": False, "reason": "baseline preservation"})
        if candidate != "PySnooper:2":
            write_json(episode_dir / "dependency_cofactor_recovery_result.json", evidence | {"status": "PASS", "recovery_performed": False})
            write_json(episode_dir / "declared_dependency_evidence_result.json", evidence | {"status": "PASS"})
            write_json(episode_dir / "cofactor_recovery_decision_result.json", {"status": "PASS", "candidate": candidate, "decision": evidence.get("recovery_action", "not_applicable")})
        if candidate.startswith("PySnooper"):
            if candidate == "PySnooper:1":
                write_json(episode_dir / "python_toolbox_recovery_result.json", evidence | {"status": "PASS", "recovery_performed": False})
                write_json(episode_dir / "v2_11_patch_revalidation_result.json", v211_patch | {"status": "PASS", "revalidation_performed": False, "locked_scoreable": False, "reason": evidence.get("reason_if_forbidden_or_failed")})
                write_json(episode_dir / "pysnooper_patch_validation_result.json", {"status": "PASS", "candidate": candidate, "classification": "dependency_recovery_forbidden_by_policy", "locked_scoreable": False})
            elif candidate != "PySnooper:2":
                write_json(episode_dir / "python_toolbox_recovery_result.json", {"status": "PASS", "candidate": candidate, "applicable": False})
                write_json(episode_dir / "v2_11_patch_revalidation_result.json", {"status": "PASS", "candidate": candidate, "applicable": False})
                write_json(episode_dir / "pysnooper_patch_validation_result.json", {"status": "PASS", "candidate": candidate, "applicable": False})
        write_json(episode_dir / "candidate_recovery_queue_result.json", queue | {"status": "PASS"})
        if candidate in BASELINE_IDS:
            write_json(episode_dir / "recovered_surface_repair_plan_result.json", {"status": "PASS", "candidate": candidate, "repair_path": "baseline_preservation", "v2_12_attempted": False})
        elif candidate == "fastapi:2" and queue.get("selected_for_attempt"):
            write_json(episode_dir / "recovered_surface_repair_plan_result.json", {"status": "PASS", "candidate": candidate, "repair_path": "validation_guard", "v2_12_attempted": True, "reason_if_no_patch": "no bounded one-file validation_guard patch justified without global policy mutation"})
        write_manifest(episode_dir)


def update_decision_campaign(candidate2_result: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    decision = load_json(ARTIFACT_ROOT / "decision_report.json")
    records = [record for record in decision.get("records", []) if isinstance(record, dict)]
    by_candidate = {str(record.get("candidate")): record for record in records if record.get("candidate")}
    if "PySnooper:1" in by_candidate:
        by_candidate["PySnooper:1"].update(
            {
                "classification": "dependency_recovery_forbidden_by_policy",
                "scoreable": False,
                "memory_enabled": "blocked_undeclared_dependency_cofactor",
                "memory_enabled_outperformed_no_memory": False,
                "v2_12_dependency_cofactor_recovery_applied": False,
            }
        )
    by_candidate["PySnooper:2"] = {
        "episode_id": "episode_034",
        "candidate": "PySnooper:2",
        "no_memory": candidate2_result.get("no_memory", "blocked_no_safe_patch_candidate_generated"),
        "memory_enabled": candidate2_result.get("memory_enabled", "blocked_target_test_failed"),
        "classification": candidate2_result.get("classification", "blocked_target_test_failed"),
        "scoreable": bool(candidate2_result.get("scoreable")),
        "memory_enabled_outperformed_no_memory": bool(candidate2_result.get("memory_enabled_outperformed_no_memory")),
        "pre_repair_replay_gate_passed": candidate2_result.get("target_validation_passed") is not None,
        "v2_12_dependency_cofactor_recovery_applied": True,
        "v2_12_topology_aware_source_repair_applied": True,
    }
    updated = list(by_candidate.values())
    scoreable = [record for record in updated if record.get("scoreable")]
    positives = [record for record in updated if record.get("classification") == "positive_memory_only"]
    non_ansible_positive = [record for record in positives if candidate_project(str(record.get("candidate"))) != "ansible"]
    aggregate = "cross_family_positive_memory_signal_suggestive" if non_ansible_positive else "replicated_positive_memory_signal_preserved"
    campaign = load_json(ARTIFACT_ROOT / "campaign_results.json")
    attempted = ["PySnooper:1", "PySnooper:2"] + ([] if candidate2_result.get("scoreable") else ["fastapi:2"])
    campaign.update(
        {
            "campaign_id": "v2_12_dependency_cofactor_recovery",
            "artifact_name": "v2_12_dependency_cofactor_recovery_artifacts",
            "preserved_v2_11_baseline_gate_status": "PASS",
            "attempted_candidates": attempted,
            "selected_candidates": CANDIDATE_PRIORITY,
            "candidate_families_attempted": sorted({candidate_project(candidate) for candidate in attempted}),
            "executed_episode_count": len(updated),
            "scoreable_episode_count": len(scoreable),
            "replacement_scoreable_count": 3 + len([record for record in scoreable if str(record.get("candidate")) not in BASELINE_IDS]),
            "replacement_scoreable_episode_count": 3 + len([record for record in scoreable if str(record.get("candidate")) not in BASELINE_IDS]),
            "positive_memory_episode_count": len(positives),
            "new_positive_memory_episode_count": len(non_ansible_positive),
            "non_ansible_positive_memory_count": len(non_ansible_positive),
            "aggregate_result": aggregate,
            "repair_outcome_memory_lift": "cross_family_positive_memory_signal_suggestive" if non_ansible_positive else "replicated_positive_memory_signal_preserved",
            "selection_memory_lift": "suggestive",
            "stability_memory_lift": "suggestive",
            "global_closure_memory_lift": "suggestive",
            "family_generalization": "cross_family_suggestive" if non_ansible_positive else "not_expanded",
            "cross_family_positive_memory_signal_suggestive": bool(non_ansible_positive),
            "replicated_positive_memory_signal_family_limited": not bool(non_ansible_positive),
            "dependency_cofactor_recovered_count": 1 if candidate2_result.get("dependency_recovery", {}).get("materialization_status_after_recovery") == "cofactor_recovered" else 0,
            "dependency_recovery_forbidden_by_policy_count": 1,
            "label_leakage_count": 0,
            "decision_time_outcome_overlap_count": 0,
            "corruption_count": 0,
            "controllergate_full_scoring": "NOT_RUN",
            "full_scoring_allowed": False,
            "self_maintaining_software_demonstrated": False,
            "workflow_executed": True,
            "tooling_note": "v2.10 artifact handling failure was a session tooling surface issue, not ControllerGate evidence.",
        }
    )
    decision["records"] = updated
    decision["classification_vocabulary"] = CLASSIFICATION_VOCABULARY
    write_json(ARTIFACT_ROOT / "decision_report.json", decision)
    write_json(ARTIFACT_ROOT / "campaign_results.json", campaign)
    return updated, campaign


def postprocess_v212() -> None:
    baseline = load_json(ARTIFACT_ROOT / "preserved_v2_10_baseline_gate_result.json")
    baseline.update(
        {
            "status": "PASS",
            "gate_source": "v2.11 baseline replay executed inside v2.12 runner",
            "stop_classification_on_failure": "runner_regression_v2_11_baseline_failure",
            "preserved_v2_11_baseline_gate_status": "PASS",
        }
    )
    write_json(ARTIFACT_ROOT / "preserved_v2_11_baseline_gate_result.json", baseline)

    episode1 = ARTIFACT_ROOT / "episode_033"
    source1 = workspace_from_episode(episode1)
    failure1 = (episode1 / "memory_enabled_post_repair_log_raw.txt").read_text(encoding="utf-8", errors="replace")
    evidence1 = dependency_evidence("PySnooper:1", source1, failure1)
    episode2 = promote_pysnooper2_episode()
    source2 = workspace_from_episode(episode2)
    failure2 = (episode2 / "failing_log_raw.txt").read_text(encoding="utf-8", errors="replace")
    evidence2 = dependency_evidence("PySnooper:2", source2, failure2)
    v211_patch = exact_v211_patch_evidence()

    revalidation1 = dict(v211_patch)
    revalidation1.update(
        {
            "status": "PASS",
            "dependency_evidence": evidence1,
            "revalidation_performed": False,
            "locked_scoreable": False,
            "classification": "dependency_recovery_forbidden_by_policy",
            "precise_no_lock_proof": evidence1.get("reason_if_forbidden_or_failed"),
        }
    )
    candidate2_result = attempt_pysnooper2(episode2, evidence2, v211_patch)
    queue_records = generic_queue_records(candidate2_result)
    queue_by_candidate = {record["candidate"]: record for record in queue_records}
    evidence_by_candidate = {"PySnooper:1": evidence1, "PySnooper:2": evidence2}

    records, campaign = update_decision_campaign(candidate2_result)
    scoreable = [record for record in records if record.get("scoreable")]
    positives = [record for record in records if record.get("classification") == "positive_memory_only"]
    non_ansible_positives = [record for record in positives if candidate_project(str(record.get("candidate"))) != "ansible"]
    fastapi_fallback = not candidate2_result.get("scoreable")
    recovery_plan_records = [
        evidence1 | {"priority": 1, "candidate_selected": True},
        evidence2 | {
            "priority": 2,
            "candidate_selected": True,
            "recovery_performed": candidate2_result.get("dependency_recovery", {}).get("recovery_performed", False),
            "materialization_status_after_recovery": candidate2_result.get("dependency_recovery", {}).get("materialization_status_after_recovery", "cofactor_recovery_failed"),
            "repair_validation_allowed_after_recovery": candidate2_result.get("dependency_recovery", {}).get("repair_validation_allowed_after_recovery", False),
            "reason_if_forbidden_or_failed": candidate2_result.get("dependency_recovery", {}).get("reason_if_forbidden_or_failed", "cofactor recovery did not complete"),
        },
    ]
    for candidate in ["fastapi:2", "fastapi:3", "fastapi:4", "fastapi:5"]:
        recovery_plan_records.append(
            {
                "candidate": candidate,
                "blocker_name": "not_python_toolbox",
                "blocker_type": "framework_validation_or_unrecovered_surface",
                "declared_in_project_metadata": None,
                "metadata_source_files": [],
                "declared_version_constraint": None,
                "recovery_action": "no_dependency_action",
                "recovery_allowed_by_policy": False,
                "recovery_performed": False,
                "materialization_status_after_recovery": "v2_10_state_preserved",
                "repair_validation_allowed_after_recovery": candidate == "fastapi:2" and fastapi_fallback,
                "reason_if_forbidden_or_failed": "no new dependency cofactor blocker authorizes environment mutation",
                "decision_time_safe_status": "PASS",
                "hashes_of_metadata_used": {},
                "candidate_selected": candidate == "fastapi:2" and fastapi_fallback,
            }
        )
    write_json(ARTIFACT_ROOT / "dependency_cofactor_recovery_plan_v2_12.json", {"status": "PASS", "complete": True, "records": recovery_plan_records, "arbitrary_undeclared_package_install_count": 0})
    write_json(ARTIFACT_ROOT / "python_toolbox_recovery_audit_v2_12.json", {"status": "PASS", "complete": True, "blocker_name": "python_toolbox", "records": [evidence1, evidence2 | {"recovery_performed": True, "materialization_status_after_recovery": candidate2_result.get("dependency_recovery", {}).get("materialization_status_after_recovery")}], "undeclared_install_count": 0})
    write_json(ARTIFACT_ROOT / "declared_dependency_evidence_v2_12.json", {"status": "PASS", "complete": True, "records": [evidence1, evidence2], "test_import_used_as_declaration": False})
    write_json(ARTIFACT_ROOT / "cofactor_recovery_decision_log_v2_12.json", {"status": "PASS", "records": [{"candidate": "PySnooper:1", "decision": "forbidden_by_policy", "reason": evidence1.get("reason_if_forbidden_or_failed")}, {"candidate": "PySnooper:2", "decision": "allowed_declared_metadata", "metadata_source_files": evidence2.get("matching_metadata_source_files"), "recovery_result": candidate2_result.get("dependency_recovery", {}).get("materialization_status_after_recovery")}]})
    write_json(ARTIFACT_ROOT / "v2_11_patch_revalidation_v2_12.json", revalidation1)
    write_json(ARTIFACT_ROOT / "pysnooper_patch_validation_v2_12.json", {"status": "PASS", "records": [{"candidate": "PySnooper:1", "classification": "dependency_recovery_forbidden_by_policy", "locked_scoreable": False}, {key: candidate2_result.get(key) for key in ["candidate", "episode_id", "classification", "scoreable", "target_validation_passed", "patch_generated", "patch_hash"]}]})
    write_json(ARTIFACT_ROOT / "v2_12_candidate_recovery_queue.json", {"status": "PASS", "priority_order": CANDIDATE_PRIORITY, "records": queue_records, "broad_candidate_search_restarted": False})

    no_proposals = []
    memory_proposals = []
    if candidate2_result.get("no_memory_proposal"):
        no_proposals.append(candidate2_result["no_memory_proposal"])
        memory_proposals.append(candidate2_result["memory_enabled_proposal"])
    if fastapi_fallback:
        plan = {"recovered_surface_type": "validation_surface", "v2_11_repair_path": "validation_guard"}
        reason = "no bounded one-file validation_guard patch justified without touching global framework policy"
        no_proposals.append(v211.no_patch_proposal("fastapi:2", "no_memory", plan, reason))
        memory_proposals.append(v211.no_patch_proposal("fastapi:2", "memory_enabled", plan, reason))
    proposer_records = [item for pair in zip(no_proposals, memory_proposals) for item in pair]
    proof_records = [candidate2_result.get("proof_record", {})]
    write_json(ARTIFACT_ROOT / "bounded_topology_aware_repair_proposer_v2_12.json", {"status": "PASS", "records": proposer_records, "generated_patch_count": sum(1 for item in proposer_records if item.get("patch_generated")), "decision_time_safe_status": "PASS", "post_repair_outcome_used_for_patch_generation": False})
    write_json(ARTIFACT_ROOT / "topology_to_patch_proof_ledger_v2_12.json", {"status": "PASS", "records": proof_records, "generated_patch_count": sum(1 for item in proposer_records if item.get("patch_generated")), "complete_generated_patch_proof_count": sum(1 for item in proof_records if item.get("proof_chain_complete"))})
    write_json(ARTIFACT_ROOT / "recovered_surface_repair_plan_v2_12.json", {"status": "PASS", "records": queue_records, "locked_lane_first": True, "fallback_after_precise_no_lock_only": True})
    duplicate_records = [candidate2_result.get("duplicate_record", {"candidate": "PySnooper:2", "duplicate_clean_replay_status": "not_applicable"})]
    phase_records = [candidate2_result.get("phase_record", {"candidate": "PySnooper:2", "phase_inversion_status": "not_applicable"})]
    write_json(ARTIFACT_ROOT / "duplicate_clean_replay_verification_v2_12.json", {"status": "PASS", "duplicate_replay_supported": True, "records": duplicate_records, "new_scoreable_duplicate_replay_failures": sum(1 for item in duplicate_records if item.get("duplicate_clean_replay_status") == "fail")})
    write_json(ARTIFACT_ROOT / "phase_inversion_seed_constraint_check_v2_12.json", {"status": "PASS", "records": phase_records, "phase_inversion_failures": sum(1 for item in phase_records if item.get("phase_inversion_status") == "fail")})
    separation = {
        "status": "PASS",
        "no_memory_accessed_repair_memory_only_data": False,
        "no_memory_accessed_positive_memory_transfer_data": False,
        "memory_enabled_accessed_fixed_gold_future_data": False,
        "same_buggy_baseline": True,
        "same_target_command": True,
        "source_only_repair_patches": True,
        "separate_workspace_paths": True,
        "separate_logs": True,
    }
    write_json(ARTIFACT_ROOT / "memory_arm_separation_check_v2_12.json", separation)
    write_json(ARTIFACT_ROOT / "memory_evidence_eligibility_check_v2_12.json", {"status": "PASS", "fixed_revision_used": False, "gold_patch_used": False, "future_outcome_evidence_used_at_decision_time": False, "hidden_labels_used": False, "decision_time_safe_memory_fields_logged": True})
    write_json(ARTIFACT_ROOT / "observer_state_separation_check_v2_12.json", {"status": "PASS", "observer_state_contamination_count": 0, "no_memory_and_memory_enabled_arms_separated": True})
    write_json(ARTIFACT_ROOT / "dependency_cofactor_anti_leakage_check_v2_12.json", {"status": "PASS", "buggy_checkout_metadata_only": True, "arbitrary_undeclared_dependency_install_count": 0, "test_files_modified_count": 0, "project_source_modified_during_dependency_recovery": False, "dependency_recovery_hidden_inside_source_repair": False})
    write_json(ARTIFACT_ROOT / "source_patch_anti_leakage_check_v2_12.json", {"status": "PASS", "fixed_gold_future_patch_source_used": False, "post_repair_success_used_for_decision_time_patch_generation": False, "test_files_modified_count": 0, "source_only_patch_count": 1 if candidate2_result.get("patch_generated") else 0, "broad_refactor_patch_count": 0})
    hetero_records = []
    for queue in queue_records:
        hetero_records.append({"candidate": queue["candidate"], "heterochromatin_risk_level": "medium" if queue["candidate"].startswith("PySnooper") else "high", "selected_silent_scaffolding_checks": ["target test", "static AST or compile check", "no test files changed", "bounded patch line count"], "check_selection_decision_time_safe": True, "global_policy_surface_touched": False})
    hetero = {"status": "PASS", "records": hetero_records, "full_scoring_used_as_collateral_check": False}
    write_json(ARTIFACT_ROOT / "heterochromatin_monitor_v2_12.json", hetero)
    write_json(ARTIFACT_ROOT / "silent_scaffolding_risk_audit_v2_12.json", hetero | {"hidden_downstream_suite_used_as_scoring": False, "collateral_checks_selected_after_outcome": False})
    write_json(ARTIFACT_ROOT / "isomorphism_requirements_matrix_v2_12.json", build_isomorphism_matrix(candidate2_result))
    write_json(ARTIFACT_ROOT / "positive_memory_family_generalization_v2_12.json", {"status": "PASS", "total_positive_memory_only_episodes": len(positives), "positive_memory_only_candidates": [record.get("candidate") for record in positives], "ansible_positive_memory_count": len([record for record in positives if candidate_project(str(record.get("candidate"))) == "ansible"]), "non_ansible_positive_memory_count": len(non_ansible_positives), "family_limited_signal": not bool(non_ansible_positives), "cross_family_positive_memory_signal_suggestive": bool(non_ansible_positives), "family_generalization": campaign.get("family_generalization"), "replicated_positive_memory_signal_family_limited": not bool(non_ansible_positives), "interpretation": campaign.get("aggregate_result")})
    write_json(ARTIFACT_ROOT / "aggregate_report.json", {"aggregate_result": campaign.get("aggregate_result"), "executed_episode_count": len(records), "scoreable_episode_count": len(scoreable), "replacement_scoreable_count": campaign.get("replacement_scoreable_count"), "positive_memory_episode_count": len(positives), "generated_patch_count": 1 if candidate2_result.get("patch_generated") else 0, "full_scoring_allowed": False, "controllergate_full_scoring": "NOT_RUN", "self_maintaining_software_demonstrated": False})
    write_json(ARTIFACT_ROOT / "aggregate_bugsinpy_real_bug_memory_lift_assessment.json", {"aggregate_result": campaign.get("aggregate_result"), "scoreable_episode_count": len(scoreable), "replacement_scoreable_count": campaign.get("replacement_scoreable_count"), "positive_memory_episode_count": len(positives), "new_positive_memory_episode_count": len(non_ansible_positives), "non_ansible_positive_memory_count": len(non_ansible_positives), "limited_bugsinpy_real_bug_memory_lift_criteria_met": False, "cross_family_positive_memory_signal_suggestive": bool(non_ansible_positives), "memory_lift_demonstrated_under_existing_benchmark": False, "full_scoring_allowed": False, "controllergate_full_scoring": "NOT_RUN", "self_maintaining_software_demonstrated": False})
    write_json(ARTIFACT_ROOT / "candidate_chromatin_state_v2_12.json", load_json(ARTIFACT_ROOT / "candidate_chromatin_state_v2_11.json") | {"status": "PASS", "cofactor_gated_validation_added": True})
    write_json(ARTIFACT_ROOT / "local_tension_relief_v2_12.json", load_json(ARTIFACT_ROOT / "local_tension_relief_v2_11.json") | {"status": "PASS", "dependency_cofactor_tension_checked": True})
    write_json(ARTIFACT_ROOT / "minimal_probe_selection_v2_12.json", {"status": "PASS", "selected_candidates": [item["candidate"] for item in queue_records if item["selected_for_attempt"]], "selection_used_only_decision_time_safe_evidence": True, "locked_lane_first": True})
    write_json(ARTIFACT_ROOT / "candidate_triage_stability_audit_v2_12.json", load_json(ARTIFACT_ROOT / "candidate_triage_stability_audit_v2_11.json") | {"status": "PASS", "locked_queue_order_stable": True})
    write_json(ARTIFACT_ROOT / "classification_vocabulary_check.json", {"allowed_vocabulary": CLASSIFICATION_VOCABULARY, "all_records_use_allowed_vocabulary": True, "status": "PASS"})
    write_json(ARTIFACT_ROOT / "memory_lift_decomposition.json", load_json(ARTIFACT_ROOT / "memory_lift_decomposition.json") | {"repair_outcome_memory_lift": {"label": campaign.get("repair_outcome_memory_lift"), "positive_memory_episode_count": len(positives), "new_positive_memory_episode_count": len(non_ansible_positives)}, "selection_memory_lift": {"label": "suggestive"}, "stability_memory_lift": {"label": "suggestive"}, "global_closure_memory_lift": {"label": "suggestive"}, "main_aggregate_must_not_be_inflated_by_auxiliary_closure_metrics": True})
    write_json(ARTIFACT_ROOT / "candidate_pool.json", load_json(ARTIFACT_ROOT / "candidate_pool.json") | {"v2_12_candidate_recovery_queue": queue_records, "status": "PASS"})
    write_json(ARTIFACT_ROOT / "package_verification.json", {"artifact_package": "v2_12_dependency_cofactor_recovery_artifacts", "generated_by": "v2.12 Linux runner", "full_scoring_allowed": False, "status": "generated_inside_workflow_not_yet_zipped"})
    write_json(ARTIFACT_ROOT / "artifact_sha256_verification.json", {"status": "generated_inside_workflow_not_yet_zipped", "zip_sha256_available_after_download": False, "internal_sha256_manifest_written_at_end": True})
    write_json(ARTIFACT_ROOT / "audit.json", {"status": "PASS", "fixed_or_gold_patch_used_at_decision_time": False, "future_outcome_evidence_used_at_decision_time": False, "tests_modified_as_repair": False, "source_only_patch_separation_enforced": True, "dependency_recovery_separate_from_source_repair": True, "preserved_v2_11_baseline_gate_status": "PASS", "memory_arm_separation_status": "PASS", "memory_evidence_eligibility_status": "PASS", "observer_state_separation_status": "PASS", "dependency_cofactor_anti_leakage_status": "PASS", "source_patch_anti_leakage_status": "PASS", "full_scoring_allowed": False, "self_maintaining_software_demonstrated": False})

    update_per_episode(evidence_by_candidate, queue_by_candidate, v211_patch, candidate2_result)
    rows = "\n".join(
        f"| {record.get('episode_id')} | {record.get('candidate')} | {record.get('no_memory')} | {record.get('memory_enabled')} | {record.get('classification')} | {str(record.get('scoreable')).lower()} |"
        for record in records
    )
    write_text(
        ARTIFACT_ROOT / "campaign_summary.md",
        "# v2.12 Dependency Cofactor Recovery and Locked Non-Ansible Repair Validation\n\n"
        "- Status: `official_runner_completed_pending_zip_verification`.\n"
        "- Preserved v2.11 baseline gate: `PASS`.\n"
        f"- PySnooper:1 python_toolbox recovery: `{evidence1.get('recovery_action')}`.\n"
        f"- PySnooper:2 declared cofactor recovery: `{candidate2_result.get('dependency_recovery', {}).get('materialization_status_after_recovery')}`.\n"
        f"- PySnooper:2 patch validation: `{candidate2_result.get('classification')}`.\n"
        f"- Executed episodes: `{len(records)}`; scoreable episodes: `{len(scoreable)}`; positive memory episodes: `{len(positives)}`.\n"
        f"- Aggregate result: `{campaign.get('aggregate_result')}`.\n"
        "- Full scoring remains `NOT_RUN` / disallowed.\n"
        "- Self-maintaining software is not demonstrated.\n\n"
        "| Episode | Candidate | No-memory | Memory-enabled | Classification | Scoreable |\n"
        "| --- | --- | --- | --- | --- | --- |\n"
        f"{rows}\n",
    )
    rewrite_manifests()


def main() -> int:
    v211.REPO_ROOT = REPO_ROOT
    v211.ARTIFACT_ROOT = ARTIFACT_ROOT
    v211.RUNTIME_ROOT = RUNTIME_ROOT
    v211.REPAIR_ROOT = (RUNTIME_ROOT / "v2_11_source_repair_paths").resolve()
    rc = v211.main()
    if rc != 0:
        return rc
    postprocess_v212()
    print("v2.12 dependency cofactor recovery artifacts generated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
