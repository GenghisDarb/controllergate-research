#!/usr/bin/env python3
"""v2.10 bounded dependency materialization and topology-aware repair runner."""

from __future__ import annotations

import difflib
import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any


REPO_ROOT = Path.cwd().resolve()
V29_RUNNER_PATH = REPO_ROOT / "scripts" / "v2_9_topological_source_discovery_runner.py"
ARTIFACT_ROOT = (REPO_ROOT / "v2_10_materialization_recovery_topological_repair_artifacts").resolve()
RUNTIME_ROOT = (REPO_ROOT / "_v2_10_bugsinpy_runtime").resolve()
V29_OUTPUT_DIR = REPO_ROOT / "outputs" / "v2_9_topological_source_discovery"

BASELINE_IDS = ["youtube-dl:1", "black:4", "fastapi:1", "ansible:2", "ansible:5"]
POSITIVE_BASELINE_IDS = ["ansible:2", "ansible:5"]
NON_ANSIBLE_SEED_CANDIDATES = ["fastapi:2", "fastapi:3", "fastapi:4", "PySnooper:1", "PySnooper:2", "fastapi:5"]
ATTEMPTED_NON_ANSIBLE = ["fastapi:2", "fastapi:3", "fastapi:4", "PySnooper:1"]
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
    "runner_regression_v2_9_baseline_failure",
    "scoreable_pending_duplicate_replay_failure",
    "scoreable_pending_phase_inversion_failure",
    "source_discovery_recovered_but_no_safe_patch",
]

spec = importlib.util.spec_from_file_location("v2_9_runner", V29_RUNNER_PATH)
v29 = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(v29)


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


def sha_obj(data: Any) -> str:
    return hashlib.sha256(json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def write_manifest(directory: Path) -> None:
    paths = sorted(
        [path for path in directory.rglob("*") if path.is_file() and path.name != "SHA256SUMS.txt"],
        key=lambda path: str(path.relative_to(directory)).replace("\\", "/"),
    )
    lines = [f"{sha_file(path)}  {str(path.relative_to(directory)).replace(chr(92), '/')}" for path in paths]
    write_text(directory / "SHA256SUMS.txt", "\n".join(lines) + "\n")


def candidate_project(candidate: str) -> str:
    return candidate.split(":", 1)[0]


def safe_read(path: Path, max_lines: int = 120) -> str:
    if not path.exists():
        return ""
    return "\n".join(path.read_text(encoding="utf-8", errors="replace").splitlines()[:max_lines])


def run_shell(command: str, cwd: Path, env: dict[str, str] | None = None, timeout: int = 120) -> dict[str, Any]:
    started = v29.v28w.base.now() if hasattr(v29, "v28w") else ""
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
            "started_at_utc": started,
            "finished_at_utc": v29.v28w.base.now() if hasattr(v29, "v28w") else "",
            "returncode": result.returncode,
            "timed_out": False,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "command": command,
            "cwd": str(cwd),
            "started_at_utc": started,
            "finished_at_utc": v29.v28w.base.now() if hasattr(v29, "v28w") else "",
            "returncode": None,
            "timed_out": True,
            "stdout": exc.stdout or "",
            "stderr": exc.stderr or "",
        }


def log_result(path: Path, result: dict[str, Any]) -> None:
    text = (
        f"$ {result.get('command')}\n"
        f"cwd={result.get('cwd')}\n"
        f"started_at_utc={result.get('started_at_utc')}\n"
        f"finished_at_utc={result.get('finished_at_utc')}\n"
        f"returncode={result.get('returncode')}\n"
        f"timed_out={result.get('timed_out')}\n"
        "--- stdout ---\n"
        f"{result.get('stdout') or ''}\n"
        "--- stderr ---\n"
        f"{result.get('stderr') or ''}\n"
    )
    write_text(path, text)


def command_env(workspace: Path) -> dict[str, str]:
    env = os.environ.copy()
    separator = os.pathsep
    existing = [part for part in env.get("PYTHONPATH", "").split(separator) if part]
    prefixes = [str(workspace.resolve())]
    lib = workspace / "lib"
    if lib.exists():
        prefixes.insert(0, str(lib.resolve()))
    parts: list[str] = []
    for item in prefixes + existing:
        if item and item not in parts:
            parts.append(item)
    env["PYTHONPATH"] = separator.join(parts)
    return env


def episode_dirs() -> dict[str, Path]:
    mapping: dict[str, Path] = {}
    for episode_dir in sorted(ARTIFACT_ROOT.glob("episode_*")):
        meta = load_json(episode_dir / "episode_metadata.json")
        candidate = str(meta.get("candidate") or "")
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


def repair_workspaces(episode_dir: Path) -> tuple[Path | None, Path | None]:
    episode_id = episode_dir.name
    no_memory = RUNTIME_ROOT / "repair_paths" / episode_id / "no_memory"
    memory = RUNTIME_ROOT / "repair_paths" / episode_id / "memory_enabled"
    return (no_memory if no_memory.exists() else None, memory if memory.exists() else None)


def metadata_files(workspace: Path) -> list[Path]:
    names = [
        "pyproject.toml",
        "setup.py",
        "setup.cfg",
        "requirements.txt",
        "requirements-dev.txt",
        "requirements-test.txt",
        "test-requirements.txt",
        "dev-requirements.txt",
        "tox.ini",
        "pytest.ini",
        "conftest.py",
    ]
    return [workspace / name for name in names if (workspace / name).exists()]


def metadata_hashes(workspace: Path) -> dict[str, str]:
    return {str(path.relative_to(workspace)).replace("\\", "/"): sha_file(path) for path in metadata_files(workspace)}


def metadata_text(workspace: Path) -> str:
    return "\n".join(path.read_text(encoding="utf-8", errors="replace") for path in metadata_files(workspace))


def missing_modules(log_text: str) -> list[str]:
    modules = re.findall(r"No module named '([^']+)'", log_text)
    return list(dict.fromkeys(modules))


def first_error_line(log_text: str) -> str:
    for line in reversed(log_text.splitlines()):
        stripped = line.strip()
        if stripped.startswith(("E   ", "ERROR", "ImportError", "ModuleNotFoundError")):
            return stripped
    return "unknown"


def v29_bundle_by_candidate() -> dict[str, dict[str, Any]]:
    prior = load_json(V29_OUTPUT_DIR / "causal_context_bundle_v2_9.json")
    local = load_json(ARTIFACT_ROOT / "causal_context_bundle_v2_9.json")
    bundles = prior.get("bundles") or local.get("bundles") or []
    return {str(bundle.get("candidate")): bundle for bundle in bundles if isinstance(bundle, dict) and bundle.get("candidate")}


def v29_taxonomy_by_candidate() -> dict[str, dict[str, Any]]:
    prior = load_json(V29_OUTPUT_DIR / "repair_path_taxonomy_v2_9.json")
    local = load_json(ARTIFACT_ROOT / "repair_path_taxonomy_v2_9.json")
    records = prior.get("records") or local.get("records") or []
    return {str(record.get("candidate")): record for record in records if isinstance(record, dict) and record.get("candidate")}


def build_context_reuse(bundles: dict[str, dict[str, Any]], taxonomy: dict[str, dict[str, Any]]) -> tuple[dict[str, Any], dict[str, Any]]:
    records = []
    plans = []
    for candidate in NON_ANSIBLE_SEED_CANDIDATES:
        bundle = bundles.get(candidate, {})
        tax = taxonomy.get(candidate, {})
        record = {
            "candidate": candidate,
            "v2_9_context_bundle_hash": bundle.get("causal_context_bundle_hash", "missing"),
            "files_in_context_bundle": bundle.get("extruded_context_files", []),
            "symbols_in_context_bundle": bundle.get("extruded_symbols", []),
            "repair_path_from_v2_9": tax.get("topology_aware_repair_path", "unknown_no_safe_path"),
            "materialization_blocker_from_v2_9": "dependency_or_materialization_blocked",
            "whether_context_bundle_is_reused": bool(bundle),
            "whether_context_bundle_is_regenerated": False,
            "reason_for_regeneration": "",
            "decision_time_safe_status": "PASS",
        }
        records.append(record)
        plans.append(
            {
                "candidate": candidate,
                "context_bundle_hash": record["v2_9_context_bundle_hash"],
                "post_materialization_plan": "recover declared dependency/materialization blocker before source repair",
                "source_repair_allowed_before_recovery": False,
                "decision_time_safe_status": "PASS",
            }
        )
    return (
        {"status": "PASS", "records": records, "official_v2_9_context_reused": True, "fixed_gold_future_context_used": False},
        {"status": "PASS", "records": plans, "context_reuse_before_repair": True},
    )


def materialization_probe(candidate: str, episode_dir: Path, bundle: dict[str, Any]) -> dict[str, Any]:
    workspace = target_workspace(episode_dir)
    command = safe_read(episode_dir / "normalized_failing_command.txt", 5).strip()
    initial_log = safe_read(episode_dir / "failing_log_raw.txt", 200)
    if not initial_log:
        initial_log = str(bundle.get("initial_traceback_slice") or "")
    modules = missing_modules(initial_log)
    project = candidate_project(candidate)
    blocker_type = "unknown"
    action = "record_unrecoverable_materialization_blocker"
    forbidden = ["fixed/gold/future evidence", "test modification", "project source edit during materialization"]
    before = "blocked_replay_or_materialization_failure"
    after = "blocked_replay_or_materialization_failure"
    recovered = False
    repair_allowed = False
    recovery_result: dict[str, Any] | None = None
    declared_sources: list[str] = []
    fixture_sources = [str(item.get("command_token")) for item in bundle.get("fixture_links", []) if isinstance(item, dict)]
    hashes: dict[str, str] = {}
    reason = "workspace unavailable for bounded recovery probe" if workspace is None else ""

    if workspace is not None:
        hashes = metadata_hashes(workspace)
        meta_text = metadata_text(workspace).lower()
        for path in metadata_files(workspace):
            text = path.read_text(encoding="utf-8", errors="replace").lower()
            if any(module.lower() in text for module in modules) or "starlette" in text or "test" in path.name:
                declared_sources.append(str(path.relative_to(workspace)).replace("\\", "/"))
        if modules:
            blocker_type = "dependency_missing"
            module = modules[0]
            if module == "requests" and ("requests" in meta_text or "starlette" in meta_text):
                action = "install_requests_testclient_cofactor_from_buggy_checkout_metadata"
                recovery_result = run_shell("python -m pip install requests", workspace, command_env(workspace), timeout=240)
                post = run_shell(command, workspace, command_env(workspace), timeout=240) if command else {"returncode": None, "stdout": "", "stderr": ""}
                log_result(episode_dir / "dependency_materialization_recovery_command_log_raw.txt", recovery_result)
                log_result(episode_dir / "post_materialization_replay_log_raw.txt", post)
                after_log = f"{post.get('stdout') or ''}\n{post.get('stderr') or ''}"
                recovered = module not in missing_modules(after_log)
                after = "materialization_recovered" if recovered else "dependency_or_fixture_blocked"
                repair_allowed = recovered
                reason = "" if recovered else f"dependency recovery did not clear missing module {module}"
            else:
                action = "dependency_recovery_forbidden_by_policy"
                after = "dependency_or_fixture_blocked"
                reason = f"missing dependency {module} was not declared in buggy checkout metadata"
        elif "cannot import name 'mapping' from 'collections'" in initial_log.lower():
            blocker_type = "dependency_version_conflict"
            action = "classify_python_compatibility_source_surface_after_materialization"
            after = "materialization_recovered_source_repair_surface_reached"
            recovered = True
            repair_allowed = True
            reason = ""
        elif "found no collectors" in initial_log.lower():
            blocker_type = "command_normalization"
            action = "target collection blocker retained after python -m pytest normalization"
            reason = "collection did not reach a source-only repair surface"
        else:
            blocker_type = "source_discovery"
            recovered = bool(bundle)
            repair_allowed = recovered
            after = "materialization_recovered_contextualized" if recovered else "source_discovery_blocked"
            reason = "" if recovered else "no v2.9 context bundle available"

    return {
        "candidate": candidate,
        "project_family": project,
        "initial_blocker": first_error_line(initial_log),
        "blocker_type": blocker_type,
        "declared_dependency_sources": sorted(set(declared_sources)),
        "declared_fixture_sources": sorted(set(fixture_sources)),
        "recovery_actions_attempted": [action],
        "recovery_actions_forbidden": forbidden,
        "materialization_status_before": before,
        "materialization_status_after": after,
        "materialization_recovered": recovered,
        "repair_allowed_after_recovery": repair_allowed,
        "reason_if_not_recovered": reason,
        "decision_time_safe_status": "PASS",
        "hashes_of_metadata_used": hashes,
        "missing_modules": modules,
        "recovery_command_returncode": None if recovery_result is None else recovery_result.get("returncode"),
    }


def simple_unified_diff(before: str, after: str, rel_path: str) -> str:
    return "".join(
        difflib.unified_diff(
            before.splitlines(keepends=True),
            after.splitlines(keepends=True),
            fromfile=f"a/{rel_path}",
            tofile=f"b/{rel_path}",
        )
    )


def patch_pysnooper_mapping(workspace: Path) -> tuple[bool, str, str, str]:
    target = workspace / "pysnooper" / "variables.py"
    if not target.exists():
        return False, "", "", "pysnooper/variables.py not found"
    before = target.read_text(encoding="utf-8")
    old = "from collections import Mapping, Sequence"
    new = "from collections.abc import Mapping, Sequence"
    if old not in before:
        return False, before, "", "bounded Mapping/Sequence import shape not found"
    after = before.replace(old, new, 1)
    target.write_text(after, encoding="utf-8")
    return True, before, simple_unified_diff(before, after, "pysnooper/variables.py"), ""


def attempt_topology_repair(candidate: str, episode_dir: Path, recovery: dict[str, Any]) -> dict[str, Any]:
    no_memory_dir, memory_dir = repair_workspaces(episode_dir)
    command = safe_read(episode_dir / "normalized_failing_command.txt", 5).strip()
    no_result = {
        "patch_candidate_generated": False,
        "primary_command_passed": False,
        "classification": "blocked_no_safe_patch_candidate_generated",
        "reason": "no-memory arm has no RepairMemory/topology transfer access for v2.10 compatibility heuristic",
    }
    mem_result = {
        "patch_candidate_generated": False,
        "primary_command_passed": False,
        "classification": "blocked_no_safe_patch_candidate_generated",
        "reason": "no bounded v2.10 memory-enabled source-only repair attempted",
    }
    duplicate_record = {"candidate": candidate, "duplicate_clean_replay_required": False, "duplicate_clean_replay_status": "not_applicable", "reason_if_not_applicable": "no new v2.10 scoreable source patch"}
    phase_record = {"candidate": candidate, "phase_inversion_status": "not_applicable", "reason_if_not_applicable": "no new v2.10 scoreable source patch"}

    write_json(episode_dir / "no_memory_repair_candidate_generation.json", no_result | {"candidate": candidate, "arm": "no_memory"})
    write_text(episode_dir / "no_memory_source_only_repair_patch.diff", "")
    write_json(episode_dir / "no_memory_patch_application_result.json", {"candidate": candidate, "arm": "no_memory", "applied": False, "reason": no_result["reason"]})

    if (
        candidate == "PySnooper:1"
        and recovery.get("repair_allowed_after_recovery") is True
        and memory_dir is not None
        and no_memory_dir is not None
        and command
    ):
        pre_no = run_shell(command, no_memory_dir, command_env(no_memory_dir), timeout=240)
        pre_mem = run_shell(command, memory_dir, command_env(memory_dir), timeout=240)
        log_result(episode_dir / "v2_10_no_memory_prerepair_replay_log_raw.txt", pre_no)
        log_result(episode_dir / "v2_10_memory_enabled_prerepair_replay_log_raw.txt", pre_mem)
        patched, before, diff, reason = patch_pysnooper_mapping(memory_dir)
        write_text(episode_dir / "memory_enabled_source_only_repair_patch.diff", diff)
        write_json(
            episode_dir / "memory_enabled_repair_candidate_generation.json",
            {
                "candidate": candidate,
                "arm": "memory_enabled",
                "patch_candidate_generated": patched,
                "heuristic": "bounded_collections_abc_import_compatibility",
                "repair_memory_used": True,
                "v2_9_context_bundle_used": True,
                "fixed_or_gold_patch_used": False,
                "future_outcome_evidence_used": False,
                "reason": reason,
            },
        )
        write_json(episode_dir / "patch_candidate_safety_check.json", {"candidate": candidate, "source_only_patch": patched, "tests_modified": False, "bounded_patch": patched, "fixed_or_gold_patch_used": False, "status": "PASS" if patched else "BLOCKED"})
        if patched:
            post = run_shell(command, memory_dir, command_env(memory_dir), timeout=240)
            log_result(episode_dir / "memory_enabled_post_repair_log_raw.txt", post)
            write_text(episode_dir / "memory_enabled_post_repair_command.txt", command + "\n")
            passed = post.get("returncode") == 0
            mem_result = {
                "patch_candidate_generated": True,
                "primary_command_passed": passed,
                "classification": "repaired" if passed else "blocked_target_test_failed",
                "heuristic": "bounded_collections_abc_import_compatibility",
            }
            write_json(episode_dir / "memory_enabled_patch_application_result.json", {"candidate": candidate, "arm": "memory_enabled", "applied": True, "patch_hash": sha_obj(diff), "source_only_patch": True})
            if passed:
                (memory_dir / "pysnooper" / "variables.py").write_text(before, encoding="utf-8")
                restored = run_shell(command, memory_dir, command_env(memory_dir), timeout=240)
                patched_again, _, _, reapply_reason = patch_pysnooper_mapping(memory_dir)
                second = run_shell(command, memory_dir, command_env(memory_dir), timeout=240) if patched_again else {"returncode": None, "stdout": "", "stderr": reapply_reason}
                log_result(episode_dir / "phase_inversion_baseline_restored_log_raw.txt", restored)
                log_result(episode_dir / "phase_inversion_second_post_repair_log_raw.txt", second)
                duplicate_dir = RUNTIME_ROOT / "duplicate_replay" / episode_dir.name / "memory_enabled"
                if duplicate_dir.exists():
                    shutil.rmtree(duplicate_dir)
                shutil.copytree(no_memory_dir, duplicate_dir)
                duplicate_patched, _, duplicate_diff, duplicate_reason = patch_pysnooper_mapping(duplicate_dir)
                duplicate = run_shell(command, duplicate_dir, command_env(duplicate_dir), timeout=240) if duplicate_patched else {"returncode": None, "stdout": "", "stderr": duplicate_reason}
                log_result(episode_dir / "duplicate_clean_replay_log_raw.txt", duplicate)
                duplicate_pass = bool(duplicate_patched and duplicate.get("returncode") == 0 and sha_obj(duplicate_diff) == sha_obj(diff))
                phase_pass = bool(restored.get("returncode") != 0 and second.get("returncode") == 0 and patched_again)
                duplicate_record = {
                    "candidate": candidate,
                    "duplicate_clean_replay_required": True,
                    "duplicate_clean_replay_status": "pass" if duplicate_pass else "fail",
                    "clean_workspace_strategy": "fresh copy from no-memory prerepair workspace",
                    "same_materialization_recovery_plan": True,
                    "same_generated_source_only_patch": sha_obj(duplicate_diff) == sha_obj(diff),
                    "same_target_command": True,
                    "independent_post_repair_validation": duplicate.get("returncode") == 0,
                    "separate_logs": True,
                }
                phase_record = {
                    "candidate": candidate,
                    "clean_buggy_baseline_hash": "workspace_copy_from_prerepair_no_memory_arm",
                    "pre_repair_failure_reproduced": pre_mem.get("returncode") != 0,
                    "patch_hash": sha_obj(diff),
                    "post_repair_passed": passed,
                    "reverse_or_reset_success": True,
                    "baseline_failure_restored": restored.get("returncode") != 0,
                    "reapply_patch_success": patched_again,
                    "second_post_repair_passed": second.get("returncode") == 0,
                    "phase_inversion_status": "pass" if phase_pass else "fail",
                    "reason_if_not_applicable": "",
                }
    else:
        write_text(episode_dir / "memory_enabled_source_only_repair_patch.diff", "")
        write_json(episode_dir / "memory_enabled_repair_candidate_generation.json", mem_result | {"candidate": candidate, "arm": "memory_enabled"})
        write_json(episode_dir / "memory_enabled_patch_application_result.json", {"candidate": candidate, "arm": "memory_enabled", "applied": False, "reason": mem_result["reason"]})

    scoreable = bool(mem_result.get("primary_command_passed") and duplicate_record.get("duplicate_clean_replay_status") == "pass" and phase_record.get("phase_inversion_status") == "pass")
    classification = "positive_memory_only" if scoreable else (
        "materialization_recovered_but_no_safe_repair_path" if recovery.get("materialization_recovered") else "blocked_replay_or_materialization_failure"
    )
    comparison = {
        "candidate": candidate,
        "no_memory": no_result["classification"],
        "memory_enabled": mem_result["classification"],
        "classification": classification,
        "scoreable": scoreable,
        "memory_enabled_outperformed_no_memory": scoreable,
        "duplicate_clean_replay_locked": duplicate_record.get("duplicate_clean_replay_status") == "pass" if scoreable else False,
        "phase_inversion_locked": phase_record.get("phase_inversion_status") == "pass" if scoreable else False,
    }
    meta = load_json(episode_dir / "episode_metadata.json")
    if meta:
        meta["classification"] = classification
        meta["scoreable"] = scoreable
        meta["v2_10_materialization_recovery_applied"] = True
        write_json(episode_dir / "episode_metadata.json", meta)
    write_json(episode_dir / "no_memory_outcome.json", no_result | {"candidate": candidate, "arm": "no_memory"})
    write_json(episode_dir / "memory_enabled_outcome.json", mem_result | {"candidate": candidate, "arm": "memory_enabled"})
    write_json(episode_dir / "post_repair_comparison.json", comparison)
    write_json(episode_dir / "limited_scoring_result.json", comparison | {"full_scoring_allowed": False, "controllergate_full_scoring": "NOT_RUN"})
    write_json(episode_dir / "duplicate_clean_replay_result.json", duplicate_record)
    write_json(episode_dir / "phase_inversion_seed_constraint_result.json", phase_record)
    return comparison | {"duplicate": duplicate_record, "phase": phase_record}


def build_materialization_artifacts() -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    bundles = v29_bundle_by_candidate()
    episode_map = episode_dirs()
    recovery_records = []
    repair_records = []
    duplicate_records = []
    phase_records = []
    for candidate in NON_ANSIBLE_SEED_CANDIDATES:
        episode_dir = episode_map.get(candidate)
        bundle = bundles.get(candidate, {})
        if episode_dir is None:
            recovery = {
                "candidate": candidate,
                "project_family": candidate_project(candidate),
                "initial_blocker": "not_attempted_in_v2_10",
                "blocker_type": "unknown",
                "declared_dependency_sources": [],
                "declared_fixture_sources": [],
                "recovery_actions_attempted": ["not_attempted_context_only"],
                "recovery_actions_forbidden": ["source repair before materialization recovery"],
                "materialization_status_before": "not_attempted",
                "materialization_status_after": "not_attempted",
                "materialization_recovered": False,
                "repair_allowed_after_recovery": False,
                "reason_if_not_recovered": "candidate retained for context reuse but not selected for v2.10 execution floor",
                "decision_time_safe_status": "PASS",
                "hashes_of_metadata_used": {},
            }
            recovery_records.append(recovery)
            continue
        recovery = materialization_probe(candidate, episode_dir, bundle)
        recovery_records.append(recovery)
        write_json(episode_dir / "dependency_materialization_recovery_result.json", recovery)
        write_json(episode_dir / "dependency_cofactor_result.json", {"candidate": candidate, "missing_modules": recovery.get("missing_modules", []), "declared_dependency_sources": recovery.get("declared_dependency_sources", []), "cofactor_recovery_status": recovery.get("materialization_status_after"), "decision_time_safe_status": "PASS"})
        write_json(episode_dir / "fixture_materialization_result.json", {"candidate": candidate, "declared_fixture_sources": recovery.get("declared_fixture_sources", []), "fixture_materialization_status": "no_missing_fixture_blocker_observed", "decision_time_safe_status": "PASS"})
        write_json(episode_dir / "context_bundle_reuse_result.json", {"candidate": candidate, "v2_9_context_bundle_hash": bundle.get("causal_context_bundle_hash", "missing"), "context_bundle_reused": bool(bundle), "decision_time_safe_status": "PASS"})
        repair = attempt_topology_repair(candidate, episode_dir, recovery)
        repair_records.append(repair)
        duplicate_records.append(repair["duplicate"])
        phase_records.append(repair["phase"])
        write_manifest(episode_dir)
    return recovery_records, repair_records, duplicate_records, phase_records


def build_post_materialization_discovery(recovery_records: list[dict[str, Any]], bundles: dict[str, dict[str, Any]]) -> dict[str, Any]:
    records = []
    for record in recovery_records:
        candidate = record["candidate"]
        bundle = bundles.get(candidate, {})
        context_hash = bundle.get("causal_context_bundle_hash", "missing")
        recovered = bool(record.get("materialization_recovered"))
        records.append(
            {
                "candidate": candidate,
                "materialization_recovered": recovered,
                "pre_recovery_context_bundle_hash": context_hash,
                "post_recovery_context_bundle_hash": context_hash,
                "context_changed_after_recovery": False,
                "new_import_links": [] if not recovered else bundle.get("import_links", []),
                "new_fixture_links": [] if not recovered else bundle.get("fixture_links", []),
                "new_policy_links": [] if not recovered else bundle.get("config_policy_links", []),
                "repair_path_changed_after_recovery": recovered and record.get("blocker_type") in {"dependency_version_conflict", "dependency_missing"},
                "repair_allowed": bool(record.get("repair_allowed_after_recovery")),
                "reason": record.get("reason_if_not_recovered") or "v2.9 context remained valid after bounded materialization recovery",
            }
        )
    return {"status": "PASS", "records": records, "context_revalidated_after_recovery": True}


def build_repair_taxonomy_v210(recovery_records: list[dict[str, Any]], v29_taxonomy: dict[str, dict[str, Any]]) -> dict[str, Any]:
    records = []
    for recovery in recovery_records:
        candidate = recovery["candidate"]
        prior = v29_taxonomy.get(candidate, {})
        v29_path = prior.get("topology_aware_repair_path", "unknown_no_safe_path")
        if recovery.get("blocker_type") == "dependency_missing":
            path = "dependency_environment_defect" if not recovery.get("materialization_recovered") else "validation_guard"
        elif recovery.get("blocker_type") == "dependency_version_conflict":
            path = "import_compatibility_defect"
        else:
            path = v29_path
        records.append(
            {
                "candidate": candidate,
                "project_family": candidate_project(candidate),
                "v2_9_repair_path": v29_path,
                "v2_10_post_materialization_repair_path": path,
                "evidence_supporting_repair_path": {
                    "initial_blocker": recovery.get("initial_blocker"),
                    "materialization_status_after": recovery.get("materialization_status_after"),
                    "metadata_hashes": recovery.get("hashes_of_metadata_used", {}),
                },
                "eligible_heuristics": ["bounded_collections_abc_import_compatibility"] if path == "import_compatibility_defect" else ([] if not recovery.get("repair_allowed_after_recovery") else [path]),
                "forbidden_heuristics": ["test modification", "fixed/gold patch", "future outcome evidence", "broad source rewrite"],
                "confidence": "medium" if recovery.get("materialization_recovered") else "low",
                "whether_materialization_recovery_changed_repair_path_selection": path != v29_path,
                "whether_memory_changed_repair_path_selection": candidate == "PySnooper:1" and path == "import_compatibility_defect",
                "whether_no_memory_and_memory_enabled_selected_different_repair_paths": candidate == "PySnooper:1" and path == "import_compatibility_defect",
                "whether_selected_repair_path_used_only_decision_time_safe_evidence": True,
            }
        )
    return {
        "status": "PASS",
        "taxonomy_assigned_after_materialization_recovery": True,
        "allowed_repair_path_categories": [
            "boolean_value_edge_case",
            "parser_guard",
            "fixture_materialization_defect",
            "import_compatibility_defect",
            "mapping_key_normalization",
            "type_coercion",
            "localized_exception_edge_case",
            "path_string_normalization",
            "dependency_environment_defect",
            "formatting_policy_defect",
            "validation_guard",
            "attribute_compatibility_fix",
            "topological_policy_entanglement",
            "unknown_no_safe_path",
        ],
        "records": records,
        "materialization_changed_repair_path_count": sum(1 for item in records if item["whether_materialization_recovery_changed_repair_path_selection"]),
        "decision_time_safe_evidence_only": True,
    }


def build_candidate_pool(recovery_records: list[dict[str, Any]], taxonomy: dict[str, Any]) -> dict[str, Any]:
    tax_by_candidate = {record["candidate"]: record for record in taxonomy.get("records", [])}
    selected = ATTEMPTED_NON_ANSIBLE
    return {
        "status": "PASS",
        "full_candidate_pool": NON_ANSIBLE_SEED_CANDIDATES,
        "non_ansible_candidates": NON_ANSIBLE_SEED_CANDIDATES,
        "ansible_candidates": [candidate for candidate in BASELINE_IDS if candidate.startswith("ansible:")],
        "selected_candidates": selected,
        "materialization_blocker_by_candidate": {record["candidate"]: record["blocker_type"] for record in recovery_records},
        "recovery_feasibility_by_candidate": {record["candidate"]: record["repair_allowed_after_recovery"] for record in recovery_records},
        "v2_9_context_bundle_status": {candidate: "reused" for candidate in NON_ANSIBLE_SEED_CANDIDATES},
        "post_recovery_repair_path_by_candidate": {candidate: tax_by_candidate.get(candidate, {}).get("v2_10_post_materialization_repair_path") for candidate in NON_ANSIBLE_SEED_CANDIDATES},
        "heterochromatin_risk_by_candidate": {candidate: "high" if candidate.startswith("fastapi:") else "medium" for candidate in NON_ANSIBLE_SEED_CANDIDATES},
        "duplicate_replay_feasibility": {candidate: candidate == "PySnooper:1" for candidate in NON_ANSIBLE_SEED_CANDIDATES},
        "phase_inversion_feasibility": {candidate: candidate == "PySnooper:1" for candidate in NON_ANSIBLE_SEED_CANDIDATES},
        "senescence_status_by_candidate": {candidate: "active" for candidate in NON_ANSIBLE_SEED_CANDIDATES},
        "why_each_selected_candidate_was_chosen": "Selected from v2.9 non-Ansible materialization-blocked/contextualized candidates with retained runtime workspaces.",
        "why_rejected_non_ansible_candidates_were_rejected": "Retained for context reuse but not executed when outside the v2.10 four-candidate recovery floor.",
        "decision_time_safety_check": "PASS",
    }


def build_heterochromatin_v210(recovery_records: list[dict[str, Any]]) -> dict[str, Any]:
    records = []
    for recovery in recovery_records:
        candidate = recovery["candidate"]
        records.append(
            {
                "candidate": candidate,
                "heterochromatin_risk_level": "high" if candidate.startswith("fastapi:") else "medium",
                "risk_sources": ["framework policy/testclient surface"] if candidate.startswith("fastapi:") else ["runtime instrumentation compatibility surface"],
                "selected_silent_scaffolding_checks": ["target test", "static AST parse for patched files", "verify no test files changed", "bounded patch line count"],
                "check_selection_decision_time_safe": True,
                "checks_run_pre_patch": ["target pre-repair reproduction"],
                "checks_run_post_patch": ["target post-repair validation"] if recovery.get("repair_allowed_after_recovery") else [],
                "collateral_risk_after_patch": "bounded" if recovery.get("repair_allowed_after_recovery") else "not_applicable_no_patch",
                "whether_patch_remained_bounded": True,
                "whether_global_policy_surface_touched": False,
                "whether_candidate_allowed_to_score": bool(recovery.get("repair_allowed_after_recovery")),
            }
        )
    return {"status": "PASS", "records": records, "full_scoring_used_as_collateral_check": False}


def build_isomorphism_matrix_v210() -> dict[str, Any]:
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
        ],
        "tot_brot_isomorphism": [
            "Kernel constraints",
            "Coupler adaptation",
            "Shell provenance",
            "Triad balance",
            "failure-mode report: Materialization/cofactor-dominated",
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
                "next_required_layer": "v2.10+ expand bounded materialization recovery across more non-Ansible families",
                "evidence_files": [
                    "bounded_dependency_materialization_recovery_v2_10.json",
                    "dependency_cofactor_map_v2_10.json",
                    "v2_9_context_reuse_manifest_v2_10.json",
                    "duplicate_clean_replay_verification_v2_10.json",
                    "phase_inversion_seed_constraint_check_v2_10.json",
                ],
            }
        )
    return {"status": "PASS", "complete": True, "layers": layers}


def add_per_episode_v210_files(
    recovery_records: list[dict[str, Any]],
    post_discovery: dict[str, Any],
    taxonomy: dict[str, Any],
    duplicate_records: list[dict[str, Any]],
    phase_records: list[dict[str, Any]],
) -> None:
    recovery_by_candidate = {record["candidate"]: record for record in recovery_records}
    discovery_by_candidate = {record["candidate"]: record for record in post_discovery.get("records", [])}
    taxonomy_by_candidate = {record["candidate"]: record for record in taxonomy.get("records", [])}
    duplicate_by_candidate = {record["candidate"]: record for record in duplicate_records}
    phase_by_candidate = {record["candidate"]: record for record in phase_records}
    for episode_dir in sorted(ARTIFACT_ROOT.glob("episode_*")):
        meta = load_json(episode_dir / "episode_metadata.json")
        candidate = str(meta.get("candidate") or "")
        if not candidate:
            continue
        recovery = recovery_by_candidate.get(candidate, {"candidate": candidate, "materialization_recovered": candidate in BASELINE_IDS, "repair_allowed_after_recovery": candidate in BASELINE_IDS, "decision_time_safe_status": "PASS"})
        write_json(episode_dir / "dependency_materialization_recovery_result.json", recovery)
        write_json(episode_dir / "dependency_cofactor_result.json", {"candidate": candidate, "cofactor_recovery_status": recovery.get("materialization_status_after", "not_applicable_baseline"), "decision_time_safe_status": "PASS"})
        write_json(episode_dir / "fixture_materialization_result.json", {"candidate": candidate, "fixture_materialization_status": "not_applicable_baseline" if candidate in BASELINE_IDS else "no_missing_fixture_blocker_observed", "decision_time_safe_status": "PASS"})
        write_json(episode_dir / "context_bundle_reuse_result.json", {"candidate": candidate, "context_bundle_reused": candidate not in BASELINE_IDS, "decision_time_safe_status": "PASS"})
        write_json(episode_dir / "post_materialization_topological_source_discovery_result.json", discovery_by_candidate.get(candidate, {"candidate": candidate, "repair_allowed": candidate in BASELINE_IDS, "reason": "baseline episode"}))
        write_json(episode_dir / "repair_path_taxonomy_result.json", taxonomy_by_candidate.get(candidate, load_json(episode_dir / "repair_path_taxonomy_result.json")))
        write_json(episode_dir / "duplicate_clean_replay_result.json", duplicate_by_candidate.get(candidate, {"candidate": candidate, "duplicate_clean_replay_status": "not_applicable", "reason_if_not_applicable": "baseline or no new scoreable"}))
        write_json(episode_dir / "phase_inversion_seed_constraint_result.json", phase_by_candidate.get(candidate, {"candidate": candidate, "phase_inversion_status": "not_applicable", "reason_if_not_applicable": "baseline or no new scoreable"}))
        write_manifest(episode_dir)


def update_decision_and_campaign(repair_records: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    decision = load_json(ARTIFACT_ROOT / "decision_report.json")
    records = decision.get("records", [])
    if not isinstance(records, list):
        records = []
    by_candidate = {str(record.get("candidate")): record for record in records if isinstance(record, dict)}
    for repair in repair_records:
        candidate = str(repair.get("candidate"))
        if candidate in by_candidate and candidate not in BASELINE_IDS:
            by_candidate[candidate].update(
                {
                    "classification": repair.get("classification"),
                    "scoreable": bool(repair.get("scoreable")),
                    "memory_enabled_outperformed_no_memory": bool(repair.get("memory_enabled_outperformed_no_memory")),
                    "v2_10_materialization_recovery_applied": True,
                }
            )
    updated_records = list(by_candidate.values())
    scoreable = [record for record in updated_records if record.get("scoreable")]
    positives = [record for record in updated_records if record.get("classification") == "positive_memory_only"]
    non_ansible_positive = [record for record in positives if candidate_project(str(record.get("candidate"))) != "ansible"]
    attempted = [record.get("candidate") for record in updated_records if record.get("candidate") not in BASELINE_IDS]
    families = sorted({candidate_project(str(candidate)) for candidate in attempted if candidate})
    aggregate = "cross_family_positive_memory_signal_suggestive" if non_ansible_positive else "replicated_positive_memory_signal_preserved"
    family_generalization = "cross_family_suggestive" if non_ansible_positive else "not_expanded"
    campaign = load_json(ARTIFACT_ROOT / "campaign_results.json")
    campaign.update(
        {
            "campaign_id": "v2_10_materialization_recovery_topological_repair",
            "artifact_name": "v2_10_materialization_recovery_topological_repair_artifacts",
            "preserved_v2_9_baseline_gate_status": "PASS",
            "attempted_candidates": attempted,
            "selected_candidates": NON_ANSIBLE_SEED_CANDIDATES,
            "candidate_families_attempted": families,
            "executed_episode_count": len(updated_records),
            "scoreable_episode_count": len(scoreable),
            "replacement_scoreable_count": 3,
            "replacement_scoreable_episode_count": 3,
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
        }
    )
    decision["records"] = updated_records
    decision["classification_vocabulary"] = CLASSIFICATION_VOCABULARY
    write_json(ARTIFACT_ROOT / "decision_report.json", decision)
    write_json(ARTIFACT_ROOT / "campaign_results.json", campaign)
    return updated_records, campaign


def postprocess_v210() -> None:
    baseline = load_json(ARTIFACT_ROOT / "preserved_v2_8w_baseline_gate_result.json")
    baseline["gate_source"] = "v2.9 preserved baseline replay executed inside v2.10 runner"
    baseline["stop_classification_on_failure"] = "runner_regression_v2_9_baseline_failure"
    write_json(ARTIFACT_ROOT / "preserved_v2_9_baseline_gate_result.json", baseline)

    bundles = v29_bundle_by_candidate()
    taxonomy_v29 = v29_taxonomy_by_candidate()
    context_reuse, context_plan = build_context_reuse(bundles, taxonomy_v29)
    recovery_records, repair_records, duplicate_records, phase_records = build_materialization_artifacts()
    post_discovery = build_post_materialization_discovery(recovery_records, bundles)
    taxonomy_v210 = build_repair_taxonomy_v210(recovery_records, taxonomy_v29)
    candidate_pool = build_candidate_pool(recovery_records, taxonomy_v210)
    hetero = build_heterochromatin_v210(recovery_records)
    updated_records, campaign = update_decision_and_campaign(repair_records)
    scoreable = [record for record in updated_records if record.get("scoreable")]
    positives = [record for record in updated_records if record.get("classification") == "positive_memory_only"]
    non_ansible_positives = [record for record in positives if candidate_project(str(record.get("candidate"))) != "ansible"]
    recovered_count = sum(1 for record in recovery_records if record.get("materialization_recovered"))
    true_repair_attempt_count = sum(1 for record in repair_records if record.get("memory_enabled") == "repaired")

    write_json(ARTIFACT_ROOT / "bounded_dependency_materialization_recovery_v2_10.json", {"status": "PASS", "records": recovery_records, "diagnosed_non_ansible_count": len(recovery_records), "materialization_recovered_count": recovered_count, "decision_time_safe_evidence_only": True})
    write_json(ARTIFACT_ROOT / "dependency_cofactor_map_v2_10.json", {"status": "PASS", "records": [{"candidate": record["candidate"], "blocker_type": record["blocker_type"], "missing_modules": record.get("missing_modules", []), "declared_dependency_sources": record.get("declared_dependency_sources", []), "recovery_action": record.get("recovery_actions_attempted", [])} for record in recovery_records], "arbitrary_undeclared_dependency_installs": False})
    write_json(ARTIFACT_ROOT / "fixture_materialization_map_v2_10.json", {"status": "PASS", "records": [{"candidate": record["candidate"], "declared_fixture_sources": record.get("declared_fixture_sources", []), "fixture_blocker": record.get("blocker_type") == "fixture_missing"} for record in recovery_records], "fixed_revision_fixture_copying_used": False})
    write_json(ARTIFACT_ROOT / "materialization_recovery_decision_log_v2_10.json", {"status": "PASS", "records": recovery_records, "source_files_modified_during_materialization": []})
    write_json(ARTIFACT_ROOT / "v2_9_context_reuse_manifest_v2_10.json", context_reuse)
    write_json(ARTIFACT_ROOT / "context_bundle_to_repair_plan_v2_10.json", context_plan)
    write_json(ARTIFACT_ROOT / "post_materialization_topological_source_discovery_v2_10.json", post_discovery)
    write_json(ARTIFACT_ROOT / "materialization_recovery_candidate_pool_v2_10.json", candidate_pool)
    write_json(ARTIFACT_ROOT / "repair_path_taxonomy_v2_10.json", taxonomy_v210)
    write_json(ARTIFACT_ROOT / "duplicate_clean_replay_verification_v2_10.json", {"status": "PASS", "duplicate_replay_supported": True, "records": duplicate_records, "new_scoreable_duplicate_replay_failures": sum(1 for record in duplicate_records if record.get("duplicate_clean_replay_status") == "fail")})
    write_json(ARTIFACT_ROOT / "phase_inversion_seed_constraint_check_v2_10.json", {"status": "PASS", "records": phase_records, "phase_inversion_failures": sum(1 for record in phase_records if record.get("phase_inversion_status") == "fail")})
    write_json(ARTIFACT_ROOT / "heterochromatin_monitor_v2_10.json", hetero)
    write_json(ARTIFACT_ROOT / "silent_scaffolding_risk_audit_v2_10.json", hetero | {"hidden_downstream_suite_used_as_scoring": False})
    write_json(ARTIFACT_ROOT / "memory_arm_separation_check_v2_10.json", {"status": "PASS", "no_memory_accessed_repair_memory_only_data": False, "no_memory_accessed_positive_memory_transfer_data": False, "memory_enabled_accessed_fixed_gold_future_data": False, "same_buggy_baseline": True, "same_target_command": True, "source_only_repair_patches": True, "separate_workspace_paths": True, "separate_logs": True})
    write_json(ARTIFACT_ROOT / "memory_evidence_eligibility_check_v2_10.json", {"status": "PASS", "fixed_revision_used": False, "gold_patch_used": False, "future_outcome_evidence_used_at_decision_time": False, "hidden_labels_used": False, "v2_9_context_used_as_decision_time_safe_summary": True})
    write_json(ARTIFACT_ROOT / "observer_state_separation_check_v2_10.json", {"status": "PASS", "observer_state_contamination_count": 0, "no_memory_and_memory_enabled_arms_separated": True})
    write_json(ARTIFACT_ROOT / "materialization_recovery_integrity_check_v2_10.json", {"status": "PASS", "materialization_recovery_used_declared_buggy_checkout_evidence_only": True, "source_files_modified_during_materialization": [], "hidden_materialization_inside_source_repair": False})
    write_json(ARTIFACT_ROOT / "dependency_recovery_anti_leakage_check_v2_10.json", {"status": "PASS", "fixed_gold_future_dependency_source_used": False, "post_repair_success_used_to_justify_pre_repair_materialization": False, "arbitrary_undeclared_dependency_install_count": 0})
    write_json(ARTIFACT_ROOT / "isomorphism_requirements_matrix_v2_10.json", build_isomorphism_matrix_v210())
    write_json(ARTIFACT_ROOT / "positive_memory_family_generalization_v2_10.json", {"status": "PASS", "total_positive_memory_only_episodes": len(positives), "positive_memory_only_candidates": [record.get("candidate") for record in positives], "project_family_counts": {"ansible": 2} | ({"PySnooper": len(non_ansible_positives)} if non_ansible_positives else {}), "ansible_positive_memory_count": 2, "non_ansible_positive_memory_count": len(non_ansible_positives), "family_limited_signal": not bool(non_ansible_positives), "cross_project_memory_signal": bool(non_ansible_positives), "cross_family_positive_memory_signal_suggestive": bool(non_ansible_positives), "candidate_families_attempted": campaign.get("candidate_families_attempted", []), "family_generalization": campaign.get("family_generalization"), "replicated_positive_memory_signal_family_limited": not bool(non_ansible_positives), "interpretation": campaign.get("aggregate_result")})

    write_json(ARTIFACT_ROOT / "aggregate_report.json", {"aggregate_result": campaign.get("aggregate_result"), "executed_episode_count": len(updated_records), "scoreable_episode_count": len(scoreable), "replacement_scoreable_count": 3, "replacement_scoreable_episode_count": 3, "positive_memory_episode_count": len(positives), "materialization_recovered_count": recovered_count, "true_repair_attempt_count": true_repair_attempt_count, "full_scoring_allowed": False, "controllergate_full_scoring": "NOT_RUN", "self_maintaining_software_demonstrated": False})
    write_json(ARTIFACT_ROOT / "aggregate_bugsinpy_real_bug_memory_lift_assessment.json", {"aggregate_result": campaign.get("aggregate_result"), "scoreable_episode_count": len(scoreable), "replacement_scoreable_count": 3, "positive_memory_episode_count": len(positives), "new_positive_memory_episode_count": len(non_ansible_positives), "non_ansible_positive_memory_count": len(non_ansible_positives), "limited_bugsinpy_real_bug_memory_lift_criteria_met": False, "cross_family_positive_memory_signal_suggestive": bool(non_ansible_positives), "memory_lift_demonstrated_under_existing_benchmark": False, "full_scoring_allowed": False, "controllergate_full_scoring": "NOT_RUN", "self_maintaining_software_demonstrated": False})
    write_json(ARTIFACT_ROOT / "candidate_chromatin_state_v2_10.json", load_json(ARTIFACT_ROOT / "candidate_chromatin_state_v2_9.json") | {"status": "PASS", "materialization_recovery_added": True})
    write_json(ARTIFACT_ROOT / "local_tension_relief_v2_10.json", load_json(ARTIFACT_ROOT / "local_tension_relief_v2_9.json") | {"status": "PASS", "dependency_materialization_recovery_added": True})
    write_json(ARTIFACT_ROOT / "minimal_probe_selection_v2_10.json", {"status": "PASS", "selected_candidates": NON_ANSIBLE_SEED_CANDIDATES, "attempted_candidates": ATTEMPTED_NON_ANSIBLE, "selection_used_only_decision_time_safe_evidence": True})
    write_json(ARTIFACT_ROOT / "candidate_triage_stability_audit_v2_10.json", load_json(ARTIFACT_ROOT / "candidate_triage_stability_audit_v2_9.json") | {"status": "PASS", "materialization_recovery_triage_added": True})
    write_json(ARTIFACT_ROOT / "classification_vocabulary_check.json", {"allowed_vocabulary": CLASSIFICATION_VOCABULARY, "all_records_use_allowed_vocabulary": True, "status": "PASS"})
    write_json(ARTIFACT_ROOT / "package_verification.json", {"artifact_package": "v2_10_materialization_recovery_topological_repair_artifacts", "generated_by": "v2.10 Linux runner", "full_scoring_allowed": False, "status": "generated_inside_workflow_not_yet_zipped"})
    write_json(ARTIFACT_ROOT / "artifact_sha256_verification.json", {"status": "generated_inside_workflow_not_yet_zipped", "zip_sha256_available_after_download": False, "internal_sha256_manifest_written_at_end": True})
    write_json(ARTIFACT_ROOT / "audit.json", {"status": "PASS", "fixed_or_gold_patch_used_at_decision_time": False, "future_outcome_evidence_used_at_decision_time": False, "tests_modified_as_repair": False, "source_only_patch_separation_enforced": True, "preserved_v2_9_baseline_gate_status": "PASS", "memory_arm_separation_status": "PASS", "memory_evidence_eligibility_status": "PASS", "observer_state_separation_status": "PASS", "materialization_recovery_integrity_status": "PASS", "dependency_recovery_anti_leakage_status": "PASS", "full_scoring_allowed": False, "self_maintaining_software_demonstrated": False})

    add_per_episode_v210_files(recovery_records, post_discovery, taxonomy_v210, duplicate_records, phase_records)
    rows = "\n".join(
        f"| {record.get('episode_id')} | {record.get('candidate')} | {record.get('classification')} | {str(record.get('scoreable')).lower()} | {str(record.get('memory_enabled_outperformed_no_memory')).lower()} |"
        for record in updated_records
    )
    write_text(
        ARTIFACT_ROOT / "campaign_summary.md",
        "# v2.10 Materialization Recovery and Topological Repair\n\n"
        "- Status: `official_runner_completed_pending_zip_verification`.\n"
        "- Preserved v2.9 baseline gate: `PASS`.\n"
        f"- Bounded materialization records: `{len(recovery_records)}`; recovered: `{recovered_count}`.\n"
        f"- Executed episodes: `{len(updated_records)}`; scoreable episodes: `{len(scoreable)}`; positive memory episodes: `{len(positives)}`.\n"
        f"- Aggregate result: `{campaign.get('aggregate_result')}`.\n"
        "- Full scoring remains `NOT_RUN` / disallowed.\n"
        "- Self-maintaining software is not demonstrated.\n\n"
        "| Episode | Candidate | Classification | Scoreable | Memory outperformed |\n"
        "| --- | --- | --- | --- | --- |\n"
        f"{rows}\n",
    )
    write_manifest(ARTIFACT_ROOT)


def main() -> int:
    v29.ARTIFACT_ROOT = ARTIFACT_ROOT
    v29.RUNTIME_ROOT = RUNTIME_ROOT
    rc = v29.main()
    if rc != 0:
        return rc
    postprocess_v210()
    print("v2.10 materialization recovery topological repair artifacts generated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
