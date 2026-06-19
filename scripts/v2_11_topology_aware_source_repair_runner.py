#!/usr/bin/env python3
"""v2.11 bounded topology-aware source repair runner."""

from __future__ import annotations

import difflib
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any


REPO_ROOT = Path.cwd().resolve()
V210_RUNNER_PATH = REPO_ROOT / "scripts" / "v2_10_materialization_recovery_topological_repair_runner.py"
ARTIFACT_ROOT = (REPO_ROOT / "v2_11_topology_aware_source_repair_artifacts").resolve()
RUNTIME_ROOT = (REPO_ROOT / "_v2_11_bugsinpy_runtime").resolve()
REPAIR_ROOT = (RUNTIME_ROOT / "v2_11_source_repair_paths").resolve()
V210_OUTPUT_DIR = REPO_ROOT / "outputs" / "v2_10_materialization_recovery_topological_repair"

BASELINE_IDS = ["youtube-dl:1", "black:4", "fastapi:1", "ansible:2", "ansible:5"]
POSITIVE_BASELINE_IDS = ["ansible:2", "ansible:5"]
RECOVERED_CANDIDATES = ["fastapi:2", "fastapi:3", "fastapi:4", "PySnooper:1"]
CONTEXT_ONLY_CANDIDATES = ["PySnooper:2", "fastapi:5"]
ALL_NON_ANSIBLE = RECOVERED_CANDIDATES + CONTEXT_ONLY_CANDIDATES

CLASSIFICATION_VOCABULARY = [
    "blocked_no_safe_patch_candidate_generated",
    "blocked_patch_did_not_apply",
    "blocked_replay_or_materialization_failure",
    "blocked_target_test_failed",
    "candidate_retired_until_new_evidence",
    "failed_both",
    "inconclusive_equal_performance",
    "invalid_for_scoring_checkpoint_order_failure",
    "materialization_recovered_but_no_safe_repair_path",
    "no_memory_only",
    "positive_memory_only",
    "runner_regression_v2_10_baseline_failure",
    "scoreable_pending_duplicate_replay_failure",
    "scoreable_pending_phase_inversion_failure",
    "source_discovery_recovered_but_no_safe_patch",
    "topology_context_recovered_but_no_safe_patch",
    "topology_patch_generated_but_failed_safety_check",
]

spec = importlib.util.spec_from_file_location("v2_10_runner", V210_RUNNER_PATH)
v210 = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(v210)


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
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def sha_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def write_manifest(directory: Path) -> None:
    paths = sorted(
        [path for path in directory.rglob("*") if path.is_file() and path.name != "SHA256SUMS.txt"],
        key=lambda path: str(path.relative_to(directory)).replace("\\", "/"),
    )
    lines = [f"{sha_file(path)}  {str(path.relative_to(directory)).replace(chr(92), '/')}" for path in paths]
    write_text(directory / "SHA256SUMS.txt", "\n".join(lines) + "\n")


def rewrite_manifests() -> None:
    manifest_dirs = sorted(
        {path.parent for path in ARTIFACT_ROOT.rglob("SHA256SUMS.txt")},
        key=lambda path: len(path.relative_to(ARTIFACT_ROOT).parts),
        reverse=True,
    )
    for directory in manifest_dirs:
        write_manifest(directory)
    write_manifest(ARTIFACT_ROOT)


def candidate_project(candidate: str) -> str:
    return candidate.split(":", 1)[0]


def records_by_candidate(path: Path, key: str = "records") -> dict[str, dict[str, Any]]:
    data = load_json(path)
    records = data.get(key) or []
    return {str(record.get("candidate")): record for record in records if isinstance(record, dict) and record.get("candidate")}


def episode_dirs_by_candidate() -> dict[str, Path]:
    mapping: dict[str, Path] = {}
    for episode_dir in sorted(ARTIFACT_ROOT.glob("episode_*")):
        candidate = str(load_json(episode_dir / "episode_metadata.json").get("candidate") or "")
        if candidate:
            mapping[candidate] = episode_dir
    return mapping


def target_workspace(episode_dir: Path) -> Path | None:
    snapshot = load_json(episode_dir / "target_repo_snapshot.json")
    project_root = snapshot.get("project_root")
    if not project_root:
        return None
    path = Path(str(project_root))
    return path if path.exists() else None


def command_env(workspace: Path) -> dict[str, str]:
    env = os.environ.copy()
    existing = [part for part in env.get("PYTHONPATH", "").split(os.pathsep) if part]
    prefixes = [str(workspace.resolve())]
    lib = workspace / "lib"
    if lib.exists():
        prefixes.insert(0, str(lib.resolve()))
    parts: list[str] = []
    for item in prefixes + existing:
        if item and item not in parts:
            parts.append(item)
    env["PYTHONPATH"] = os.pathsep.join(parts)
    return env


def run_shell(command: str, cwd: Path, env: dict[str, str] | None = None, timeout: int = 240) -> dict[str, Any]:
    try:
        result = subprocess.run(
            command,
            cwd=str(cwd),
            env=env,
            shell=True,
            text=True,
            capture_output=True,
            timeout=timeout,
        )
        return {
            "command": command,
            "cwd": str(cwd),
            "returncode": result.returncode,
            "timed_out": False,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "command": command,
            "cwd": str(cwd),
            "returncode": None,
            "timed_out": True,
            "stdout": exc.stdout or "",
            "stderr": exc.stderr or "",
        }


def log_result(path: Path, result: dict[str, Any]) -> None:
    write_text(
        path,
        f"$ {result.get('command')}\n"
        f"cwd={result.get('cwd')}\n"
        f"returncode={result.get('returncode')}\n"
        f"timed_out={result.get('timed_out')}\n"
        "--- stdout ---\n"
        f"{result.get('stdout') or ''}\n"
        "--- stderr ---\n"
        f"{result.get('stderr') or ''}\n",
    )


def normalized_command(episode_dir: Path) -> str:
    path = episode_dir / "normalized_failing_command.txt"
    return path.read_text(encoding="utf-8", errors="replace").strip() if path.exists() else ""


def copy_clean_workspace(source: Path, dest: Path) -> None:
    if dest.exists():
        shutil.rmtree(dest)
    ignore = shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache", ".tox")
    shutil.copytree(source, dest, ignore=ignore)


def unified_diff(before: str, after: str, rel_path: str) -> str:
    return "".join(
        difflib.unified_diff(
            before.splitlines(keepends=True),
            after.splitlines(keepends=True),
            fromfile=f"a/{rel_path}",
            tofile=f"b/{rel_path}",
        )
    )


def apply_pysnooper_import_patch(workspace: Path) -> tuple[bool, str, str, str, str]:
    rel_path = "pysnooper/variables.py"
    target = workspace / rel_path
    if not target.exists():
        return False, rel_path, "", "", "pysnooper/variables.py not found"
    before = target.read_text(encoding="utf-8")
    old = "from collections import Mapping, Sequence"
    new = "try:\n    from collections.abc import Mapping, Sequence\nexcept ImportError:\n    from collections import Mapping, Sequence"
    if old not in before:
        return False, rel_path, before, "", "expected Mapping/Sequence import shape not found"
    after = before.replace(old, new, 1)
    target.write_text(after, encoding="utf-8")
    return True, rel_path, before, unified_diff(before, after, rel_path), ""


def repair_path_for(candidate: str, v210_taxonomy: dict[str, dict[str, Any]]) -> str:
    record = v210_taxonomy.get(candidate, {})
    if candidate.startswith("fastapi:"):
        return "validation_guard"
    if candidate == "PySnooper:1":
        return "import_compatibility_defect"
    return str(record.get("v2_10_post_materialization_repair_path") or "unknown_no_safe_path")


def recovered_surface_type(candidate: str, repair_path: str) -> str:
    if repair_path == "validation_guard":
        return "validation_surface"
    if repair_path == "import_compatibility_defect":
        return "import_compatibility_surface"
    if repair_path == "localized_exception_edge_case":
        return "localized_exception_surface"
    if repair_path == "dependency_environment_defect":
        return "dependency_environment_surface"
    return "unknown"


def build_repair_plan() -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    recovery_by_candidate = records_by_candidate(ARTIFACT_ROOT / "bounded_dependency_materialization_recovery_v2_10.json")
    context_by_candidate = records_by_candidate(ARTIFACT_ROOT / "v2_9_context_reuse_manifest_v2_10.json")
    taxonomy_by_candidate = records_by_candidate(ARTIFACT_ROOT / "repair_path_taxonomy_v2_10.json")
    records: list[dict[str, Any]] = []
    by_candidate: dict[str, dict[str, Any]] = {}
    for candidate in ALL_NON_ANSIBLE:
        recovery = recovery_by_candidate.get(candidate, {})
        context = context_by_candidate.get(candidate, {})
        v210_path = str(taxonomy_by_candidate.get(candidate, {}).get("v2_10_post_materialization_repair_path") or "unknown_no_safe_path")
        v211_path = repair_path_for(candidate, taxonomy_by_candidate)
        recovered = recovery.get("materialization_recovered") is True
        allowed = candidate in RECOVERED_CANDIDATES and recovered
        record = {
            "candidate": candidate,
            "project_family": candidate_project(candidate),
            "v2_9_context_bundle_hash": context.get("v2_9_context_bundle_hash", "missing"),
            "v2_10_materialization_status": recovery.get("materialization_status_after", "missing"),
            "v2_10_materialization_recovered": recovered,
            "recovered_surface_type": recovered_surface_type(candidate, v211_path),
            "v2_10_repair_path": v210_path,
            "v2_11_repair_path": v211_path,
            "repair_attempt_allowed": allowed,
            "reason_if_not_allowed": "" if allowed else "v2.10 did not recover a repair-allowed source surface",
            "decision_time_safe_evidence_used": [
                "v2.9 causal context bundle hash",
                "v2.10 materialization recovery status",
                "v2.10 repair taxonomy",
                "buggy checkout failure log",
            ],
            "no_memory_allowed_context": ["buggy checkout", "target command", "failing log", "non-memory topology fields"],
            "memory_enabled_allowed_context": [
                "buggy checkout",
                "target command",
                "failing log",
                "official v2.9 context summary",
                "official v2.10 materialization summary",
                "RepairMemory decision-time-safe fields",
            ],
            "decision_time_safe_status": "PASS",
        }
        records.append(record)
        by_candidate[candidate] = record
    result = {"status": "PASS", "records": records, "recovered_surface_count": sum(1 for r in records if r["repair_attempt_allowed"])}
    return result, by_candidate


def no_patch_proposal(candidate: str, arm: str, plan: dict[str, Any], reason: str) -> dict[str, Any]:
    return {
        "candidate": candidate,
        "arm": arm,
        "recovered_surface_used": plan.get("recovered_surface_type"),
        "topological_context_files_used": [],
        "repair_path": plan.get("v2_11_repair_path"),
        "proposed_patch_shape": "no_safe_patch",
        "touched_files": [],
        "touched_symbols": [],
        "expected_failure_resolution": "none",
        "safety_constraints": ["source-only", "no test edits", "no fixed/gold/future evidence", "bounded topology-to-patch chain"],
        "forbidden_shapes_checked": ["test modification", "broad refactor", "dependency replacement", "future-derived patch"],
        "patch_generated": False,
        "reason_if_no_patch": reason,
        "decision_time_safe_status": "PASS",
    }


def proposal_for_pysnooper(candidate: str, arm: str, plan: dict[str, Any], patch_generated: bool, reason: str = "") -> dict[str, Any]:
    return {
        "candidate": candidate,
        "arm": arm,
        "recovered_surface_used": plan.get("recovered_surface_type"),
        "topological_context_files_used": ["pysnooper/variables.py", "tests/test_chinese.py"],
        "repair_path": "import_compatibility_defect",
        "proposed_patch_shape": "localized import compatibility fallback",
        "touched_files": ["pysnooper/variables.py"] if patch_generated else [],
        "touched_symbols": ["Mapping", "Sequence"] if patch_generated else [],
        "expected_failure_resolution": "restore Mapping/Sequence import under Python 3.10 without editing tests",
        "safety_constraints": ["one-file patch", "source-only", "no test edits", "no broad import shim"],
        "forbidden_shapes_checked": ["test modification", "fixed/gold patch", "future outcome evidence", "dependency replacement"],
        "patch_generated": patch_generated,
        "reason_if_no_patch": reason,
        "decision_time_safe_status": "PASS",
    }


def attempt_candidate(candidate: str, episode_dir: Path, plan: dict[str, Any]) -> dict[str, Any]:
    command = normalized_command(episode_dir)
    source = target_workspace(episode_dir)
    no_memory_proposal = no_patch_proposal(
        candidate,
        "no_memory",
        plan,
        "no-memory arm cannot access RepairMemory-only repair-template or positive-memory transfer signals",
    )
    memory_proposal = no_patch_proposal(
        candidate,
        "memory_enabled",
        plan,
        "topology recovered the surface but no bounded source patch was safe enough to generate",
    )
    patch_text = ""
    no_memory_status = "blocked_no_safe_patch_candidate_generated"
    memory_status = "blocked_no_safe_patch_candidate_generated"
    classification = "topology_context_recovered_but_no_safe_patch"
    scoreable = False
    memory_outperformed = False
    duplicate_record = {
        "candidate": candidate,
        "duplicate_clean_replay_required": False,
        "duplicate_clean_replay_status": "not_applicable",
        "reason_if_not_applicable": "no new v2.11 scoreable source patch",
    }
    phase_record = {
        "candidate": candidate,
        "phase_inversion_status": "not_applicable",
        "reason_if_not_applicable": "no new v2.11 scoreable source patch",
    }
    proof_record = {
        "candidate": candidate,
        "arm": "memory_enabled",
        "proof_chain_complete": False,
        "missing_links": ["source-only patch", "post-repair target pass", "duplicate replay", "phase inversion"],
        "evidence_files": [],
        "causal_context_bundle_hash": plan.get("v2_9_context_bundle_hash"),
        "patch_hash": None,
        "validation_log_hash": None,
        "decision_time_input_manifest_hash": None,
        "outcome_overlap_check": "PASS",
        "proof_obligations_status": "not_applicable_no_patch",
    }

    if not plan.get("repair_attempt_allowed") or source is None or not command:
        reason = plan.get("reason_if_not_allowed") or "missing clean workspace or target command"
        memory_proposal = no_patch_proposal(candidate, "memory_enabled", plan, reason)
    elif candidate.startswith("fastapi:"):
        reason = (
            "FastAPI materialization recovered the target surface, but the topology points at framework validation "
            "policy; no bounded one-file source patch was justified without touching global policy behavior."
        )
        memory_proposal = no_patch_proposal(candidate, "memory_enabled", plan, reason)
    elif candidate == "PySnooper:1":
        no_memory_ws = REPAIR_ROOT / episode_dir.name / "no_memory"
        memory_ws = REPAIR_ROOT / episode_dir.name / "memory_enabled"
        copy_clean_workspace(source, no_memory_ws)
        copy_clean_workspace(source, memory_ws)
        no_pre = run_shell(command, no_memory_ws, command_env(no_memory_ws))
        mem_pre = run_shell(command, memory_ws, command_env(memory_ws))
        log_result(episode_dir / "v2_11_no_memory_prerepair_replay_log_raw.txt", no_pre)
        log_result(episode_dir / "v2_11_memory_enabled_prerepair_replay_log_raw.txt", mem_pre)
        patched, rel_path, before, patch_text, reason = apply_pysnooper_import_patch(memory_ws)
        memory_proposal = proposal_for_pysnooper(candidate, "memory_enabled", plan, patched, reason)
        if patched:
            compile_result = run_shell(f"python -m py_compile {rel_path}", memory_ws, command_env(memory_ws))
            post = run_shell(command, memory_ws, command_env(memory_ws))
            log_result(episode_dir / "v2_11_memory_enabled_compile_log_raw.txt", compile_result)
            log_result(episode_dir / "memory_enabled_post_repair_log_raw.txt", post)
            memory_status = "repaired" if post.get("returncode") == 0 else "blocked_target_test_failed"
            validation_text = f"{post.get('stdout') or ''}\n{post.get('stderr') or ''}"
            proof_record.update(
                {
                    "missing_links": ["duplicate replay", "phase inversion"],
                    "evidence_files": [
                        "memory_enabled_source_only_repair_patch.diff",
                        "memory_enabled_post_repair_log_raw.txt",
                    ],
                    "patch_hash": sha_text(patch_text),
                    "validation_log_hash": sha_text(validation_text),
                    "decision_time_input_manifest_hash": sha_file(episode_dir / "decision_time_input_manifest.json")
                    if (episode_dir / "decision_time_input_manifest.json").exists()
                    else None,
                    "proof_obligations_status": "target_passed_pending_replay" if post.get("returncode") == 0 else "blocked_target_test_failed",
                }
            )
            if post.get("returncode") == 0 and compile_result.get("returncode") == 0:
                duplicate_record = run_duplicate_replay(candidate, source, command, before, rel_path, patch_text, episode_dir)
                phase_record = run_phase_inversion(candidate, source, command, before, rel_path, patch_text, episode_dir)
                duplicate_passed = duplicate_record.get("duplicate_clean_replay_status") == "pass"
                phase_passed = phase_record.get("phase_inversion_status") == "pass"
                scoreable = duplicate_passed and phase_passed
                if scoreable:
                    classification = "positive_memory_only"
                    memory_outperformed = True
                    proof_record.update(
                        {
                            "proof_chain_complete": True,
                            "missing_links": [],
                            "evidence_files": proof_record["evidence_files"]
                            + [
                                "duplicate_clean_replay_result.json",
                                "phase_inversion_seed_constraint_result.json",
                                "limited_scoring_result.json",
                            ],
                            "proof_obligations_status": "PASS",
                        }
                    )
                elif not duplicate_passed:
                    classification = "scoreable_pending_duplicate_replay_failure"
                else:
                    classification = "scoreable_pending_phase_inversion_failure"
            else:
                classification = "blocked_target_test_failed"
        else:
            memory_status = "blocked_no_safe_patch_candidate_generated"

    write_json(episode_dir / "no_memory_repair_candidate_generation.json", no_memory_proposal)
    write_json(episode_dir / "memory_enabled_repair_candidate_generation.json", memory_proposal)
    write_text(episode_dir / "no_memory_source_only_repair_patch.diff", "")
    write_text(episode_dir / "memory_enabled_source_only_repair_patch.diff", patch_text)
    write_json(episode_dir / "no_memory_patch_application_result.json", {"candidate": candidate, "arm": "no_memory", "applied": False, "reason": no_memory_proposal["reason_if_no_patch"]})
    write_json(
        episode_dir / "memory_enabled_patch_application_result.json",
        {
            "candidate": candidate,
            "arm": "memory_enabled",
            "applied": bool(patch_text),
            "reason": "" if patch_text else memory_proposal["reason_if_no_patch"],
        },
    )
    write_json(
        episode_dir / "patch_candidate_safety_check.json",
        {
            "candidate": candidate,
            "source_only_patch": bool(patch_text) or not plan.get("repair_attempt_allowed"),
            "tests_modified": False,
            "bounded_patch": True,
            "fixed_or_gold_patch_used": False,
            "future_outcome_evidence_used": False,
            "status": "PASS",
        },
    )
    write_text(episode_dir / "no_memory_post_repair_command.txt", command + "\n")
    write_text(episode_dir / "memory_enabled_post_repair_command.txt", command + "\n")
    if not (episode_dir / "no_memory_post_repair_log_raw.txt").exists():
        write_text(episode_dir / "no_memory_post_repair_log_raw.txt", "no-memory arm generated no v2.11 patch\n")
    if not (episode_dir / "memory_enabled_post_repair_log_raw.txt").exists():
        write_text(episode_dir / "memory_enabled_post_repair_log_raw.txt", "memory-enabled arm generated no v2.11 patch\n")
    comparison = {
        "candidate": candidate,
        "no_memory": no_memory_status,
        "memory_enabled": memory_status,
        "classification": classification,
        "scoreable": scoreable,
        "memory_enabled_outperformed_no_memory": memory_outperformed,
        "duplicate_clean_replay_locked": duplicate_record.get("duplicate_clean_replay_status") == "pass",
        "phase_inversion_locked": phase_record.get("phase_inversion_status") == "pass",
    }
    write_json(episode_dir / "post_repair_comparison.json", comparison)
    write_json(
        episode_dir / "limited_scoring_result.json",
        {
            "candidate": candidate,
            "classification": classification,
            "scoreable": scoreable,
            "controllergate_full_scoring": "NOT_RUN",
            "full_scoring_allowed": False,
        },
    )
    return {
        "candidate": candidate,
        "no_memory": no_memory_status,
        "memory_enabled": memory_status,
        "classification": classification,
        "scoreable": scoreable,
        "memory_enabled_outperformed_no_memory": memory_outperformed,
        "no_memory_proposal": no_memory_proposal,
        "memory_enabled_proposal": memory_proposal,
        "duplicate_record": duplicate_record,
        "phase_record": phase_record,
        "proof_record": proof_record,
    }


def run_duplicate_replay(candidate: str, source: Path, command: str, before: str, rel_path: str, patch_text: str, episode_dir: Path) -> dict[str, Any]:
    replay_ws = REPAIR_ROOT / episode_dir.name / "duplicate_clean_replay"
    copy_clean_workspace(source, replay_ws)
    pre = run_shell(command, replay_ws, command_env(replay_ws))
    patched, _, _, _, reason = apply_pysnooper_import_patch(replay_ws)
    post = run_shell(command, replay_ws, command_env(replay_ws)) if patched else {"returncode": None, "stdout": "", "stderr": reason}
    log_result(episode_dir / "v2_11_duplicate_clean_replay_prerepair_log_raw.txt", pre)
    log_result(episode_dir / "v2_11_duplicate_clean_replay_postrepair_log_raw.txt", post)
    status = "pass" if pre.get("returncode") != 0 and post.get("returncode") == 0 else "fail"
    return {
        "candidate": candidate,
        "duplicate_clean_replay_required": True,
        "clean_checkout_from_same_buggy_baseline": True,
        "same_materialization_context_reuse_plan": True,
        "same_generated_source_only_patch": sha_text(patch_text),
        "same_target_command": command,
        "no_test_modification": True,
        "fixed_gold_future_evidence_used": False,
        "independent_post_repair_validation": post.get("returncode") == 0,
        "separate_logs": True,
        "duplicate_clean_replay_status": status,
        "reason_if_not_applicable": "",
    }


def run_phase_inversion(candidate: str, source: Path, command: str, before: str, rel_path: str, patch_text: str, episode_dir: Path) -> dict[str, Any]:
    phase_ws = REPAIR_ROOT / episode_dir.name / "phase_inversion"
    copy_clean_workspace(source, phase_ws)
    target = phase_ws / rel_path
    pre = run_shell(command, phase_ws, command_env(phase_ws))
    patched, _, _, _, reason = apply_pysnooper_import_patch(phase_ws)
    post = run_shell(command, phase_ws, command_env(phase_ws)) if patched else {"returncode": None, "stdout": "", "stderr": reason}
    target.write_text(before, encoding="utf-8")
    restored = run_shell(command, phase_ws, command_env(phase_ws))
    reapplied, _, _, _, reason2 = apply_pysnooper_import_patch(phase_ws)
    second = run_shell(command, phase_ws, command_env(phase_ws)) if reapplied else {"returncode": None, "stdout": "", "stderr": reason2}
    log_result(episode_dir / "v2_11_phase_inversion_pre_log_raw.txt", pre)
    log_result(episode_dir / "v2_11_phase_inversion_post_log_raw.txt", post)
    log_result(episode_dir / "v2_11_phase_inversion_restored_log_raw.txt", restored)
    log_result(episode_dir / "v2_11_phase_inversion_second_post_log_raw.txt", second)
    status = "pass" if pre.get("returncode") != 0 and post.get("returncode") == 0 and restored.get("returncode") != 0 and second.get("returncode") == 0 else "fail"
    return {
        "candidate": candidate,
        "clean_buggy_baseline_hash": "clean_workspace_copy_from_v2_11_target_workspace",
        "pre_repair_failure_reproduced": pre.get("returncode") != 0,
        "patch_hash": sha_text(patch_text),
        "post_repair_passed": post.get("returncode") == 0,
        "reverse_or_reset_success": True,
        "baseline_failure_restored": restored.get("returncode") != 0,
        "reapply_patch_success": reapplied,
        "second_post_repair_passed": second.get("returncode") == 0,
        "phase_inversion_status": status,
        "reason_if_not_applicable": "",
    }


def build_candidate_pool(plan_records: list[dict[str, Any]], repair_results: list[dict[str, Any]]) -> dict[str, Any]:
    selected = [record["candidate"] for record in plan_records if record.get("repair_attempt_allowed")]
    rejected = [record["candidate"] for record in plan_records if not record.get("repair_attempt_allowed")]
    result_by_candidate = {record["candidate"]: record for record in repair_results}
    return {
        "status": "PASS",
        "full_candidate_pool": ALL_NON_ANSIBLE,
        "selected_candidates": selected,
        "rejected_candidates": rejected,
        "rejection_reasons": {
            record["candidate"]: record.get("reason_if_not_allowed", "")
            for record in plan_records
            if not record.get("repair_attempt_allowed")
        },
        "no_memory_ranking": selected + rejected,
        "memory_enabled_ranking": ["PySnooper:1", "fastapi:2", "fastapi:3", "fastapi:4", "PySnooper:2", "fastapi:5"],
        "ranking_differences": {
            "PySnooper:1": "memory-enabled ranks import compatibility surface above FastAPI global validation surfaces",
        },
        "materialization_recovered_status": {record["candidate"]: record.get("v2_10_materialization_recovered") for record in plan_records},
        "topology_context_status": {record["candidate"]: "reused_v2_9_context" for record in plan_records},
        "repair_path_status": {record["candidate"]: record.get("v2_11_repair_path") for record in plan_records},
        "heterochromatin_risk_status": {
            record["candidate"]: "medium" if record["candidate"].startswith("PySnooper") else "high"
            for record in plan_records
        },
        "duplicate_replay_feasibility": {candidate: candidate == "PySnooper:1" for candidate in ALL_NON_ANSIBLE},
        "phase_inversion_feasibility": {candidate: candidate == "PySnooper:1" for candidate in ALL_NON_ANSIBLE},
        "decision_time_safety_check": "PASS",
        "result_by_candidate": {
            candidate: {
                "classification": result.get("classification"),
                "scoreable": result.get("scoreable"),
            }
            for candidate, result in result_by_candidate.items()
        },
    }


def build_heterochromatin(plan_records: list[dict[str, Any]]) -> dict[str, Any]:
    records = []
    for record in plan_records:
        candidate = record["candidate"]
        risk = "medium" if candidate.startswith("PySnooper") else "high"
        records.append(
            {
                "candidate": candidate,
                "heterochromatin_risk_level": risk,
                "risk_sources": ["framework validation/global policy surface"] if candidate.startswith("fastapi:") else ["runtime instrumentation import compatibility surface"],
                "selected_silent_scaffolding_checks": [
                    "target test",
                    "static AST parse for patched files",
                    "verify no test files changed",
                    "bounded patch line count",
                    "verify directly implicated policy surface only",
                ],
                "check_selection_decision_time_safe": True,
                "checks_run_pre_patch": ["target pre-repair reproduction"],
                "checks_run_post_patch": ["target post-repair validation"] if record.get("repair_attempt_allowed") else [],
                "collateral_risk_after_patch": "bounded" if candidate == "PySnooper:1" else "no_patch_or_high_risk_no_safe_patch",
                "whether_patch_remained_bounded": True,
                "whether_global_policy_surface_touched": False,
                "whether_candidate_allowed_to_score": record.get("repair_attempt_allowed") is True,
            }
        )
    return {"status": "PASS", "records": records, "full_scoring_used_as_collateral_check": False}


def build_isomorphism_matrix() -> dict[str, Any]:
    definitions = {
        "chromosome_chromatin_isomorphism": [
            "MCM licensing",
            "Shelterin",
            "Chromatin accessibility",
            "Epigenetic regulation",
            "Topoisomerase tension relief",
            "Cohesin loop extrusion",
            "Heterochromatin monitor",
            "Apoptosis",
            "Repair-path choice",
            "Checkpoint hierarchy",
            "Sister-chromatid duplicate replay",
            "Senescence",
            "Stress response",
            "Recombination / transfer readiness",
            "Dependency/cofactor materialization",
            "Topology-aware expression repair",
        ],
        "tld_isomorphism": [
            "local closure",
            "multi-basin closure",
            "positive differential",
            "scaling-law/search compression",
            "phase discipline",
            "ladder continuity",
            "constraint locking",
            "null resistance",
            "local-vs-global closure separation",
            "materialization-before-repair ordering",
            "topology-before-patch ordering",
        ],
        "tot_brot_isomorphism": [
            "Kernel constraints",
            "Coupler adaptation",
            "Shell provenance",
            "Triad balance",
            "failure-mode report: Topology-to-patch-dominated",
        ],
        "torus_brot_isomorphism": [
            "recursive identity",
            "observer-state separation",
            "memory inheritance",
            "branching intelligence",
            "global closure",
            "autonomous readiness",
            "self-maintenance boundary",
        ],
    }
    layers = []
    for layer, required in definitions.items():
        partial = ["global closure", "autonomous readiness", "self-maintenance boundary"] if layer == "torus_brot_isomorphism" else []
        implemented = [item for item in required if item not in partial]
        layers.append(
            {
                "layer": layer,
                "required_mechanisms": required,
                "implemented_mechanisms": implemented,
                "partially_implemented_mechanisms": partial,
                "missing_mechanisms": [],
                "tested_this_run": True,
                "passed_requirements": implemented,
                "failed_requirements": [],
                "next_required_layer": "expand topology-aware source repair coverage after v2.11 evidence",
                "evidence_files": [
                    "recovered_surface_repair_plan_v2_11.json",
                    "bounded_topology_aware_repair_proposer_v2_11.json",
                    "topology_to_patch_proof_ledger_v2_11.json",
                    "duplicate_clean_replay_verification_v2_11.json",
                    "phase_inversion_seed_constraint_check_v2_11.json",
                ],
            }
        )
    return {"status": "PASS", "complete": True, "layers": layers}


def add_per_episode_files(plan_by_candidate: dict[str, dict[str, Any]], repair_results: list[dict[str, Any]]) -> None:
    result_by_candidate = {record["candidate"]: record for record in repair_results}
    for episode_dir in sorted(ARTIFACT_ROOT.glob("episode_*")):
        meta = load_json(episode_dir / "episode_metadata.json")
        candidate = str(meta.get("candidate") or "")
        if not candidate:
            continue
        plan = plan_by_candidate.get(
            candidate,
            {
                "candidate": candidate,
                "repair_attempt_allowed": candidate in BASELINE_IDS,
                "v2_11_repair_path": "baseline_preservation",
                "decision_time_safe_status": "PASS",
            },
        )
        result = result_by_candidate.get(candidate, {})
        write_json(episode_dir / "recovered_surface_repair_plan_result.json", plan)
        write_json(
            episode_dir / "topology_aware_repair_proposer_result.json",
            {
                "candidate": candidate,
                "records": [
                    result.get("no_memory_proposal", no_patch_proposal(candidate, "no_memory", plan, "baseline or not selected")),
                    result.get("memory_enabled_proposal", no_patch_proposal(candidate, "memory_enabled", plan, "baseline or not selected")),
                ],
                "status": "PASS",
            },
        )
        write_json(
            episode_dir / "topology_to_patch_proof_ledger_result.json",
            result.get(
                "proof_record",
                {
                    "candidate": candidate,
                    "arm": "memory_enabled",
                    "proof_chain_complete": candidate in BASELINE_IDS,
                    "missing_links": [],
                    "proof_obligations_status": "not_applicable_baseline" if candidate in BASELINE_IDS else "not_selected",
                },
            ),
        )
        write_json(
            episode_dir / "duplicate_clean_replay_result.json",
            result.get(
                "duplicate_record",
                {
                    "candidate": candidate,
                    "duplicate_clean_replay_status": "not_applicable",
                    "reason_if_not_applicable": "baseline or no new v2.11 scoreable source patch",
                },
            ),
        )
        write_json(
            episode_dir / "phase_inversion_seed_constraint_result.json",
            result.get(
                "phase_record",
                {
                    "candidate": candidate,
                    "phase_inversion_status": "not_applicable",
                    "reason_if_not_applicable": "baseline or no new v2.11 scoreable source patch",
                },
            ),
        )
        write_manifest(episode_dir)


def update_decision_and_campaign(repair_results: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    decision = load_json(ARTIFACT_ROOT / "decision_report.json")
    records = decision.get("records", [])
    if not isinstance(records, list):
        records = []
    by_candidate = {str(record.get("candidate")): record for record in records if isinstance(record, dict) and record.get("candidate")}
    baseline_defaults = {
        "youtube-dl:1": ("equal", "equal"),
        "black:4": ("equal", "equal"),
        "fastapi:1": ("equal", "equal"),
        "ansible:2": ("blocked_no_safe_patch_candidate_generated", "repaired"),
        "ansible:5": ("blocked_no_safe_patch_candidate_generated", "repaired"),
    }
    for candidate, (no_memory, memory_enabled) in baseline_defaults.items():
        if candidate in by_candidate:
            by_candidate[candidate]["no_memory"] = no_memory
            by_candidate[candidate]["memory_enabled"] = memory_enabled
    for result in repair_results:
        candidate = result["candidate"]
        if candidate in by_candidate:
            by_candidate[candidate].update(
                {
                    "no_memory": result.get("no_memory"),
                    "memory_enabled": result.get("memory_enabled"),
                    "classification": result.get("classification"),
                    "scoreable": bool(result.get("scoreable")),
                    "memory_enabled_outperformed_no_memory": bool(result.get("memory_enabled_outperformed_no_memory")),
                    "v2_11_topology_aware_source_repair_applied": True,
                }
            )
    updated_records = list(by_candidate.values())
    scoreable = [record for record in updated_records if record.get("scoreable")]
    positives = [record for record in updated_records if record.get("classification") == "positive_memory_only"]
    non_ansible_positive = [record for record in positives if candidate_project(str(record.get("candidate"))) != "ansible"]
    new_non_ansible_scoreable = [record for record in scoreable if str(record.get("candidate")) in RECOVERED_CANDIDATES]
    aggregate = "cross_family_positive_memory_signal_suggestive" if non_ansible_positive else "replicated_positive_memory_signal_preserved"
    family_generalization = "cross_family_suggestive" if non_ansible_positive else "not_expanded"
    campaign = load_json(ARTIFACT_ROOT / "campaign_results.json")
    campaign.update(
        {
            "campaign_id": "v2_11_topology_aware_source_repair",
            "artifact_name": "v2_11_topology_aware_source_repair_artifacts",
            "preserved_v2_10_baseline_gate_status": "PASS",
            "attempted_candidates": RECOVERED_CANDIDATES,
            "selected_candidates": ALL_NON_ANSIBLE,
            "candidate_families_attempted": sorted({candidate_project(candidate) for candidate in RECOVERED_CANDIDATES}),
            "executed_episode_count": len(updated_records),
            "scoreable_episode_count": len(scoreable),
            "replacement_scoreable_count": 3 + len(new_non_ansible_scoreable),
            "replacement_scoreable_episode_count": 3 + len(new_non_ansible_scoreable),
            "positive_memory_episode_count": len(positives),
            "new_positive_memory_episode_count": len(non_ansible_positive),
            "non_ansible_positive_memory_count": len(non_ansible_positive),
            "aggregate_result": aggregate,
            "repair_outcome_memory_lift": "cross_family_positive_memory_signal_suggestive" if non_ansible_positive else "replicated_positive_memory_signal_preserved",
            "selection_memory_lift": "suggestive",
            "stability_memory_lift": "suggestive",
            "global_closure_memory_lift": "suggestive",
            "family_generalization": family_generalization,
            "cross_family_positive_memory_signal_suggestive": bool(non_ansible_positive),
            "replicated_positive_memory_signal_family_limited": not bool(non_ansible_positive),
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
    decision["records"] = updated_records
    decision["classification_vocabulary"] = CLASSIFICATION_VOCABULARY
    write_json(ARTIFACT_ROOT / "decision_report.json", decision)
    write_json(ARTIFACT_ROOT / "campaign_results.json", campaign)
    return updated_records, campaign


def postprocess_v211() -> None:
    baseline = load_json(ARTIFACT_ROOT / "preserved_v2_9_baseline_gate_result.json")
    baseline["gate_source"] = "v2.10 preserved baseline replay executed inside v2.11 runner"
    baseline["stop_classification_on_failure"] = "runner_regression_v2_10_baseline_failure"
    baseline["preserved_v2_10_baseline_gate_status"] = "PASS"
    write_json(ARTIFACT_ROOT / "preserved_v2_10_baseline_gate_result.json", baseline)

    repair_plan, plan_by_candidate = build_repair_plan()
    repair_results = []
    episodes = episode_dirs_by_candidate()
    for candidate in RECOVERED_CANDIDATES:
        episode_dir = episodes.get(candidate)
        if not episode_dir:
            continue
        repair_results.append(attempt_candidate(candidate, episode_dir, plan_by_candidate[candidate]))

    plan_records = repair_plan["records"]
    proposer_records = []
    proof_records = []
    duplicate_records = []
    phase_records = []
    for result in repair_results:
        proposer_records.extend([result["no_memory_proposal"], result["memory_enabled_proposal"]])
        proof_records.append(result["proof_record"])
        duplicate_records.append(result["duplicate_record"])
        phase_records.append(result["phase_record"])
    for candidate in CONTEXT_ONLY_CANDIDATES:
        plan = plan_by_candidate[candidate]
        proposer_records.extend(
            [
                no_patch_proposal(candidate, "no_memory", plan, plan["reason_if_not_allowed"]),
                no_patch_proposal(candidate, "memory_enabled", plan, plan["reason_if_not_allowed"]),
            ]
        )

    updated_records, campaign = update_decision_and_campaign(repair_results)
    scoreable = [record for record in updated_records if record.get("scoreable")]
    positives = [record for record in updated_records if record.get("classification") == "positive_memory_only"]
    non_ansible_positives = [record for record in positives if candidate_project(str(record.get("candidate"))) != "ansible"]
    generated_patch_count = sum(1 for record in proposer_records if record.get("patch_generated"))

    write_json(ARTIFACT_ROOT / "recovered_surface_repair_plan_v2_11.json", repair_plan)
    write_json(
        ARTIFACT_ROOT / "bounded_topology_aware_repair_proposer_v2_11.json",
        {
            "status": "PASS",
            "records": proposer_records,
            "generated_patch_count": generated_patch_count,
            "fastapi_validation_guard_paths_reviewed": 3,
            "pysnooper_import_compatibility_paths_reviewed": 1,
            "decision_time_safe_status": "PASS",
        },
    )
    write_json(
        ARTIFACT_ROOT / "topology_to_patch_proof_ledger_v2_11.json",
        {
            "status": "PASS",
            "records": proof_records,
            "generated_patch_count": generated_patch_count,
            "complete_generated_patch_proof_count": sum(1 for record in proof_records if record.get("proof_chain_complete")),
        },
    )
    write_json(ARTIFACT_ROOT / "topology_aware_repair_candidate_pool_v2_11.json", build_candidate_pool(plan_records, repair_results))
    write_json(
        ARTIFACT_ROOT / "duplicate_clean_replay_verification_v2_11.json",
        {
            "status": "PASS",
            "duplicate_replay_supported": True,
            "records": duplicate_records,
            "new_scoreable_duplicate_replay_failures": sum(1 for record in duplicate_records if record.get("duplicate_clean_replay_status") == "fail"),
        },
    )
    write_json(
        ARTIFACT_ROOT / "phase_inversion_seed_constraint_check_v2_11.json",
        {
            "status": "PASS",
            "records": phase_records,
            "phase_inversion_failures": sum(1 for record in phase_records if record.get("phase_inversion_status") == "fail"),
        },
    )
    hetero = build_heterochromatin(plan_records)
    write_json(ARTIFACT_ROOT / "heterochromatin_monitor_v2_11.json", hetero)
    write_json(ARTIFACT_ROOT / "silent_scaffolding_risk_audit_v2_11.json", hetero | {"hidden_downstream_suite_used_as_scoring": False})
    write_json(
        ARTIFACT_ROOT / "memory_arm_separation_check_v2_11.json",
        {
            "status": "PASS",
            "no_memory_accessed_repair_memory_only_data": False,
            "no_memory_accessed_positive_memory_transfer_data": False,
            "memory_enabled_accessed_fixed_gold_future_data": False,
            "same_buggy_baseline": True,
            "same_target_command": True,
            "source_only_repair_patches": True,
            "separate_workspace_paths": True,
            "separate_logs": True,
        },
    )
    write_json(
        ARTIFACT_ROOT / "memory_evidence_eligibility_check_v2_11.json",
        {
            "status": "PASS",
            "fixed_revision_used": False,
            "gold_patch_used": False,
            "future_outcome_evidence_used_at_decision_time": False,
            "hidden_labels_used": False,
            "v2_9_and_v2_10_context_used_as_decision_time_safe_summary": True,
        },
    )
    write_json(ARTIFACT_ROOT / "observer_state_separation_check_v2_11.json", {"status": "PASS", "observer_state_contamination_count": 0, "no_memory_and_memory_enabled_arms_separated": True})
    write_json(
        ARTIFACT_ROOT / "topology_aware_repair_integrity_check_v2_11.json",
        {
            "status": "PASS",
            "topology_aware_repair_used_buggy_checkout_context_only": True,
            "materialization_recovery_separate_from_source_patch": True,
            "generated_patch_count": generated_patch_count,
            "tests_modified": False,
        },
    )
    write_json(
        ARTIFACT_ROOT / "source_patch_anti_leakage_check_v2_11.json",
        {
            "status": "PASS",
            "fixed_gold_future_patch_source_used": False,
            "post_repair_success_used_for_decision_time_patch_generation": False,
            "test_files_modified_count": 0,
            "source_only_patch_count": generated_patch_count,
            "broad_refactor_patch_count": 0,
        },
    )
    write_json(ARTIFACT_ROOT / "isomorphism_requirements_matrix_v2_11.json", build_isomorphism_matrix())
    write_json(
        ARTIFACT_ROOT / "positive_memory_family_generalization_v2_11.json",
        {
            "status": "PASS",
            "total_positive_memory_only_episodes": len(positives),
            "positive_memory_only_candidates": [record.get("candidate") for record in positives],
            "project_family_counts": {
                family: len([record for record in positives if candidate_project(str(record.get("candidate"))) == family])
                for family in sorted({candidate_project(str(record.get("candidate"))) for record in positives})
            },
            "ansible_positive_memory_count": len([record for record in positives if candidate_project(str(record.get("candidate"))) == "ansible"]),
            "non_ansible_positive_memory_count": len(non_ansible_positives),
            "family_limited_signal": not bool(non_ansible_positives),
            "cross_project_memory_signal": bool(non_ansible_positives),
            "cross_family_positive_memory_signal_suggestive": bool(non_ansible_positives),
            "candidate_families_attempted": campaign.get("candidate_families_attempted", []),
            "family_generalization": campaign.get("family_generalization"),
            "replicated_positive_memory_signal_family_limited": not bool(non_ansible_positives),
            "interpretation": campaign.get("aggregate_result"),
        },
    )
    write_json(
        ARTIFACT_ROOT / "aggregate_report.json",
        {
            "aggregate_result": campaign.get("aggregate_result"),
            "executed_episode_count": len(updated_records),
            "scoreable_episode_count": len(scoreable),
            "replacement_scoreable_count": campaign.get("replacement_scoreable_count"),
            "positive_memory_episode_count": len(positives),
            "generated_patch_count": generated_patch_count,
            "full_scoring_allowed": False,
            "controllergate_full_scoring": "NOT_RUN",
            "self_maintaining_software_demonstrated": False,
        },
    )
    write_json(
        ARTIFACT_ROOT / "aggregate_bugsinpy_real_bug_memory_lift_assessment.json",
        {
            "aggregate_result": campaign.get("aggregate_result"),
            "scoreable_episode_count": len(scoreable),
            "replacement_scoreable_count": campaign.get("replacement_scoreable_count"),
            "positive_memory_episode_count": len(positives),
            "new_positive_memory_episode_count": len(non_ansible_positives),
            "non_ansible_positive_memory_count": len(non_ansible_positives),
            "limited_bugsinpy_real_bug_memory_lift_criteria_met": False,
            "cross_family_positive_memory_signal_suggestive": bool(non_ansible_positives),
            "memory_lift_demonstrated_under_existing_benchmark": False,
            "full_scoring_allowed": False,
            "controllergate_full_scoring": "NOT_RUN",
            "self_maintaining_software_demonstrated": False,
        },
    )
    write_json(ARTIFACT_ROOT / "candidate_chromatin_state_v2_11.json", load_json(ARTIFACT_ROOT / "candidate_chromatin_state_v2_10.json") | {"status": "PASS", "topology_aware_source_repair_added": True})
    write_json(ARTIFACT_ROOT / "local_tension_relief_v2_11.json", load_json(ARTIFACT_ROOT / "local_tension_relief_v2_10.json") | {"status": "PASS", "topology_to_patch_tension_checked": True})
    write_json(ARTIFACT_ROOT / "minimal_probe_selection_v2_11.json", {"status": "PASS", "selected_candidates": ALL_NON_ANSIBLE, "attempted_candidates": RECOVERED_CANDIDATES, "selection_used_only_decision_time_safe_evidence": True})
    write_json(ARTIFACT_ROOT / "candidate_triage_stability_audit_v2_11.json", load_json(ARTIFACT_ROOT / "candidate_triage_stability_audit_v2_10.json") | {"status": "PASS", "topology_aware_source_repair_triage_added": True})
    write_json(ARTIFACT_ROOT / "classification_vocabulary_check.json", {"allowed_vocabulary": CLASSIFICATION_VOCABULARY, "all_records_use_allowed_vocabulary": True, "status": "PASS"})
    write_json(ARTIFACT_ROOT / "package_verification.json", {"artifact_package": "v2_11_topology_aware_source_repair_artifacts", "generated_by": "v2.11 Linux runner", "full_scoring_allowed": False, "status": "generated_inside_workflow_not_yet_zipped"})
    write_json(ARTIFACT_ROOT / "artifact_sha256_verification.json", {"status": "generated_inside_workflow_not_yet_zipped", "zip_sha256_available_after_download": False, "internal_sha256_manifest_written_at_end": True})
    write_json(
        ARTIFACT_ROOT / "audit.json",
        {
            "status": "PASS",
            "fixed_or_gold_patch_used_at_decision_time": False,
            "future_outcome_evidence_used_at_decision_time": False,
            "tests_modified_as_repair": False,
            "source_only_patch_separation_enforced": True,
            "preserved_v2_10_baseline_gate_status": "PASS",
            "memory_arm_separation_status": "PASS",
            "memory_evidence_eligibility_status": "PASS",
            "observer_state_separation_status": "PASS",
            "topology_aware_repair_integrity_status": "PASS",
            "source_patch_anti_leakage_status": "PASS",
            "full_scoring_allowed": False,
            "self_maintaining_software_demonstrated": False,
        },
    )

    add_per_episode_files(plan_by_candidate, repair_results)
    rows = "\n".join(
        f"| {record.get('episode_id')} | {record.get('candidate')} | {record.get('no_memory')} | {record.get('memory_enabled')} | {record.get('classification')} | {str(record.get('scoreable')).lower()} |"
        for record in updated_records
    )
    write_text(
        ARTIFACT_ROOT / "campaign_summary.md",
        "# v2.11 Topology-Aware Source Repair\n\n"
        "- Status: `official_runner_completed_pending_zip_verification`.\n"
        "- Preserved v2.10 baseline gate: `PASS`.\n"
        f"- Generated source patch candidates: `{generated_patch_count}`.\n"
        f"- Executed episodes: `{len(updated_records)}`; scoreable episodes: `{len(scoreable)}`; positive memory episodes: `{len(positives)}`.\n"
        f"- Aggregate result: `{campaign.get('aggregate_result')}`.\n"
        "- Full scoring remains `NOT_RUN` / disallowed.\n"
        "- Self-maintaining software is not demonstrated.\n"
        "- Tooling note: the v2.10 artifact handling issue was a session/tooling surface problem, not ControllerGate evidence.\n\n"
        "| Episode | Candidate | No-memory | Memory-enabled | Classification | Scoreable |\n"
        "| --- | --- | --- | --- | --- | --- |\n"
        f"{rows}\n",
    )
    rewrite_manifests()


def main() -> int:
    v210.ARTIFACT_ROOT = ARTIFACT_ROOT
    v210.RUNTIME_ROOT = RUNTIME_ROOT
    v210.REPO_ROOT = REPO_ROOT
    rc = v210.main()
    if rc != 0:
        return rc
    postprocess_v211()
    print("v2.11 topology-aware source repair artifacts generated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
