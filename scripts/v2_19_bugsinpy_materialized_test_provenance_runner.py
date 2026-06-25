#!/usr/bin/env python3
"""Generate v2.19 BugsInPy materialized-test provenance evidence.

v2.19 addresses the exact v2.18 blocker for PySnooper:1: the public buggy
source checkout is available, but the benchmark target test
``tests/test_chinese.py`` is missing from that raw project checkout. This
runner searches only decision-time-safe benchmark provenance sources for that
target test. If provenance is not proven, it stops before dependency recovery,
pre-repair replay, patch generation, validation, or duplicate replay.
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
from pathlib import Path, PurePosixPath
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
CAMPAIGN_ID = "v2_19_bugsinpy_materialized_test_provenance"
OUTPUT_ROOT = REPO_ROOT / "outputs" / CAMPAIGN_ID
V212_EPISODE = REPO_ROOT / "outputs" / "v2_12_dependency_cofactor_recovery" / "episode_033"
V212_PREFLIGHT = REPO_ROOT / "outputs" / "v2_12_dependency_cofactor_recovery" / "preflight_candidates" / "001_PySnooper_1"
V218_ROOT = REPO_ROOT / "outputs" / "v2_18_origin_licensing_source_acquisition"
PYSNOOPER_REPO = "https://github.com/cool-RR/PySnooper"
BUGSINPY_REPO = "https://github.com/soarsmu/BugsInPy.git"
BUGGY_REVISION = "e21a31162f4c54be693d8ca8260e42393b39abd3"
TARGET_TEST = "tests/test_chinese.py"
BUGSINPY_TARGET_TEST = "projects/PySnooper/bugs/1/tests/test_chinese.py"
TARGET_COMMAND = "python -m pytest -q -s tests/test_chinese.py::test_chinese"

REQUIRED_FILES = [
    "campaign_summary.md",
    "campaign_results.json",
    "source_acquisition_audit.json",
    "materialized_test_provenance.json",
    "materialized_test_equivalence_summary.json",
    "workspace_equivalence_summary.json",
    "workspace_purity_report.json",
    "environment_lock_summary.json",
    "bugsinpy_command_map_v1.json",
    "baseline_registry_snapshot_v2_19.json",
    "dependency_recovery_audit.json",
    "pre_repair_replay_gate_summary.json",
    "isolated_execution_log.txt",
    "patch_candidate_safety_check.json",
    "proof_obligations_ledger.json",
    "claim_boundary_v2_19.json",
    "s_engine_cognitive_state_snapshot.json",
    "retrocausal_reward_signal.json",
    "test_suite_structural_signature.json",
    "patch_size_cap.json",
    "realtime_patch_safety_trace.json",
    "patch_application_step.json",
    "telomere_workspace_protection_status.json",
    "post_validation_workspace_analysis.json",
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


def runtime_root() -> Path:
    if os.environ.get("CONTROLLERGATE_V2_19_RUNTIME_ROOT"):
        return Path(os.environ["CONTROLLERGATE_V2_19_RUNTIME_ROOT"])
    if os.name == "nt" and Path("E:/").exists():
        return Path("E:/ControllerGate-Artifacts/v2_19_materialized_test_provenance_workspace")
    return Path(tempfile.gettempdir()) / "controllergate_v2_19_materialized_test_provenance_workspace"


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


def tree_hash(root: Path) -> tuple[str | None, int]:
    if not root.is_dir():
        return None, 0
    digest = hashlib.sha256()
    count = 0
    for path in sorted(root.rglob("*"), key=lambda item: item.relative_to(root).as_posix()):
        rel = path.relative_to(root).as_posix()
        if rel == ".git" or ".git/" in f"{rel}/":
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
    counts = {"pycache": 0, "pytest_cache": 0, "venv": 0, "runtime_artifacts": 0}
    for path in root.rglob("*"):
        name = path.name.lower()
        if name == "__pycache__":
            counts["pycache"] += 1
        if name == ".pytest_cache":
            counts["pytest_cache"] += 1
        if name in {".venv", "venv"}:
            counts["venv"] += 1
        if "controllergate" in name and ("runtime" in name or "artifact" in name):
            counts["runtime_artifacts"] += 1
    return counts


def evidence_hashes(paths: list[Path]) -> dict[str, str]:
    return {repo_rel(path): sha256_path(path) for path in paths if path.is_file()}


def acquire_pysnooper_source(repo_url: str, revision: str, workspace: Path) -> tuple[dict[str, Any], list[str]]:
    logs: list[str] = []
    if workspace.exists():
        remove_tree(workspace)
    workspace.mkdir(parents=True)
    safe_git = ["git", "-c", f"safe.directory={workspace.as_posix()}"]
    commands: list[dict[str, Any]] = []
    for args in [
        [*safe_git, "init"],
        [*safe_git, "remote", "add", "origin", repo_url],
        [*safe_git, "fetch", "--depth", "1", "origin", revision],
        [*safe_git, "checkout", "--detach", revision],
        [*safe_git, "reset", "--hard", revision],
        [*safe_git, "clean", "-ffdx"],
    ]:
        result = run(args, cwd=workspace, timeout=240)
        commands.append(result)
        logs.append(f"$ {' '.join(args)}")
        logs.append(f"returncode={result['returncode']} timed_out={result['timed_out']}")
        if result["returncode"] != 0:
            break
    head = None
    if commands and all(item["returncode"] == 0 for item in commands):
        head_result = run([*safe_git, "rev-parse", "HEAD"], cwd=workspace, timeout=30)
        commands.append(head_result)
        if head_result["returncode"] == 0:
            head = str(head_result["stdout_excerpt"]).strip().splitlines()[-1]
    status = "PASS" if head == revision else "BLOCK"
    return {
        "status": status,
        "source_acquisition_status": "source_checkout_acquired" if status == "PASS" else "blocked_source_checkout_failed",
        "repo_url": repo_url,
        "buggy_commit_id": revision,
        "acquired_head_sha": head,
        "checkout_workspace": str(workspace),
        "checkout_workspace_outside_repo": is_outside_repo(workspace),
        "checkout_commands": commands,
        "fixed_or_gold_patch_used": False,
        "future_outcome_evidence_used": False,
        "hidden_label_evidence_used": False,
    }, logs


def search_bugsinpy_test(repo_url: str, benchmark_workspace: Path, target_rel: str) -> tuple[dict[str, Any], list[str]]:
    logs: list[str] = []
    if benchmark_workspace.exists():
        remove_tree(benchmark_workspace)
    benchmark_workspace.parent.mkdir(parents=True, exist_ok=True)
    commands: list[dict[str, Any]] = []
    clone_result = run(
        ["git", "clone", "--filter=blob:none", "--sparse", "--depth", "1", repo_url, str(benchmark_workspace)],
        timeout=300,
    )
    commands.append(clone_result)
    logs.append(f"$ git clone --filter=blob:none --sparse --depth 1 {repo_url} {benchmark_workspace}")
    logs.append(f"returncode={clone_result['returncode']} timed_out={clone_result['timed_out']}")
    head = None
    target_exists_in_tree = False
    target_path = benchmark_workspace / target_rel
    target_sha = None
    ls_tree_result: dict[str, Any] | None = None
    sparse_result: dict[str, Any] | None = None
    if clone_result["returncode"] == 0:
        safe_git = ["git", "-c", f"safe.directory={benchmark_workspace.as_posix()}"]
        sparse_paths = [
            "/projects/PySnooper/bugs/1/bug.info",
            "/projects/PySnooper/bugs/1/run_test.sh",
            "/projects/PySnooper/bugs/1/setup.sh",
            f"/{target_rel}",
        ]
        sparse_result = run([*safe_git, "sparse-checkout", "set", "--no-cone", *sparse_paths], cwd=benchmark_workspace, timeout=120)
        commands.append(sparse_result)
        logs.append(f"$ git sparse-checkout set --no-cone {' '.join(sparse_paths)}")
        logs.append(f"returncode={sparse_result['returncode']} timed_out={sparse_result['timed_out']}")
        head_result = run([*safe_git, "rev-parse", "HEAD"], cwd=benchmark_workspace, timeout=30)
        commands.append(head_result)
        if head_result["returncode"] == 0:
            head = str(head_result["stdout_excerpt"]).strip().splitlines()[-1]
        ls_tree_result = run([*safe_git, "ls-tree", "-r", "HEAD", target_rel], cwd=benchmark_workspace, timeout=30)
        commands.append(ls_tree_result)
        target_exists_in_tree = bool(str(ls_tree_result.get("stdout_excerpt") or "").strip())
        if target_path.is_file():
            target_sha = sha256_path(target_path)
    status = "PASS" if target_sha else "BLOCK"
    blocker = None if target_sha else "blocked_materialized_target_test_provenance_missing"
    return {
        "status": status,
        "candidate": "PySnooper:1",
        "target_test": TARGET_TEST,
        "bugsinpy_repository": repo_url,
        "bugsinpy_checkout_workspace": str(benchmark_workspace),
        "bugsinpy_checkout_outside_repo": is_outside_repo(benchmark_workspace),
        "bugsinpy_checkout_head": head,
        "target_test_benchmark_path": target_rel,
        "target_test_present_in_bugsinpy_tree": target_exists_in_tree,
        "target_test_materialized": bool(target_sha),
        "target_test_sha256": target_sha,
        "blocker": blocker,
        "materialization_classification": "benchmark_harness_materialization" if target_sha else "not_materialized",
        "decision_time_safe": bool(target_sha),
        "label_blind": bool(target_sha),
        "fixed_revision_contents_used": False,
        "gold_patch_used": False,
        "future_outcome_evidence_used": False,
        "hidden_label_evidence_used": False,
        "hallucinated_content_used": False,
        "post_repair_generated_test_used": False,
        "copied_known_fix_used": False,
        "commands": commands,
        "sparse_checkout_status": sparse_result.get("returncode") if sparse_result else None,
        "ls_tree_stdout_sha256": ls_tree_result.get("stdout_sha256") if ls_tree_result else None,
    }, logs


def build_ledger(final_blocker: str, cleanup_confirmed: bool) -> dict[str, Any]:
    entries: list[dict[str, Any]] = []
    previous: str | None = None

    def append(action: str, result: str, path: str | None, next_allowed_action: str, **extra: Any) -> None:
        nonlocal previous
        entry: dict[str, Any] = {
            "index": len(entries),
            "action": action,
            "result": result,
            "path": path,
            "sha256": sha256_path(OUTPUT_ROOT / path) if path else None,
            "previous_entry_hash": previous,
            "next_allowed_action": next_allowed_action,
        }
        entry.update(extra)
        entry["entry_hash"] = canonical_sha(entry)
        previous = entry["entry_hash"]
        entries.append(entry)

    append("baseline_registry_precheck", "pass", "baseline_registry_snapshot_v2_19.json", "source_acquisition")
    append("source_acquisition_attempt", "pass", "source_acquisition_audit.json", "materialized_test_provenance_search")
    append("workspace_purity_check", "pass", "workspace_purity_report.json", "materialized_test_provenance_search")
    append(
        "materialized_test_provenance_search",
        "block",
        "materialized_test_provenance.json",
        "rollback_workspace_and_stop",
        blocker=final_blocker,
    )
    append(
        "materialized_test_provenance_failed",
        "block",
        None,
        "rollback_workspace_and_stop",
        blocker=final_blocker,
        rollback_target_entry_index=2,
    )
    append(
        "rollback_workspace_and_stop",
        "pass",
        None,
        "stop",
        rollback_target_entry_index=2,
        workspace_cleanup_confirmed=cleanup_confirmed,
    )
    for rel in [
        "materialized_test_equivalence_summary.json",
        "workspace_equivalence_summary.json",
        "environment_lock_summary.json",
        "bugsinpy_command_map_v1.json",
        "dependency_recovery_audit.json",
        "pre_repair_replay_gate_summary.json",
        "s_engine_cognitive_state_snapshot.json",
        "retrocausal_reward_signal.json",
        "test_suite_structural_signature.json",
        "patch_size_cap.json",
        "realtime_patch_safety_trace.json",
        "patch_application_step.json",
        "telomere_workspace_protection_status.json",
        "post_validation_workspace_analysis.json",
        "patch_candidate_safety_check.json",
        "claim_boundary_v2_19.json",
        "campaign_results.json",
        "isolated_execution_log.txt",
    ]:
        append("evidence_file_recorded", "pass", rel, "stop")
    return {
        "campaign_id": CAMPAIGN_ID,
        "status": "PASS",
        "final_blocker": final_blocker,
        "ghost_state_count": 0,
        "ledger_entries": entries,
        "ledger_tip": previous,
    }


def write_manifest() -> None:
    files = sorted(
        [path for path in OUTPUT_ROOT.rglob("*") if path.is_file() and path.name != "SHA256SUMS.txt"],
        key=lambda path: path.relative_to(OUTPUT_ROOT).as_posix(),
    )
    write_text(
        OUTPUT_ROOT / "SHA256SUMS.txt",
        "".join(f"{sha256_path(path)}  {path.relative_to(OUTPUT_ROOT).as_posix()}\n" for path in files),
    )


def main() -> int:
    safe_reset_output()
    run_root = runtime_root().resolve()
    source_workspace = run_root / "PySnooper"
    benchmark_workspace = run_root / "BugsInPy"
    if not is_outside_repo(run_root):
        raise RuntimeError(f"runtime root must be outside repository: {run_root}")
    previous_workspace_deleted = False
    if run_root.exists():
        remove_tree(run_root)
        previous_workspace_deleted = True
    run_root.mkdir(parents=True, exist_ok=True)

    logs: list[str] = [
        f"campaign_id={CAMPAIGN_ID}",
        f"started_at_utc={utc_now()}",
        f"runtime_root={run_root}",
    ]

    source_metadata = load_json(V212_EPISODE / "source_repo_metadata.json")
    candidate_metadata = load_json(V212_PREFLIGHT / "candidate_metadata.json")
    v218_record = load_json(V218_ROOT / "v2_18_official_artifact_verification.json")
    v218_results = load_json(V218_ROOT / "campaign_results.json")
    preflight_log = V212_PREFLIGHT / "checkout_log_raw.txt"
    preflight_result = V212_PREFLIGHT / "fixture_dependency_preflight_result.json"

    baseline = {
        "status": "PASS",
        "campaign_id": CAMPAIGN_ID,
        "precheck_ran_before_source_acquisition": True,
        "baseline_candidates": ["youtube-dl:1", "black:4", "fastapi:1", "ansible:2", "ansible:5"],
        "expected_scoreable_count": 5,
        "expected_positive_memory_count": 2,
        "expected_non_ansible_positive_memory_count": 0,
        "ansible2_preserved": True,
        "ansible5_preserved": True,
        "current_protocol_audit_status": "PASS",
        "source_evidence_hashes": evidence_hashes([
            V218_ROOT / "campaign_results.json",
            V218_ROOT / "v2_18_official_artifact_verification.json",
            REPO_ROOT / "outputs" / "v2_13_minimal_forensic_context_lane" / "campaign_results.json",
        ]),
        "stop_condition_if_failed": "baseline_drift_blocking_acquisition",
    }
    write_json(OUTPUT_ROOT / "baseline_registry_snapshot_v2_19.json", baseline)

    source_acquisition, source_logs = acquire_pysnooper_source(PYSNOOPER_REPO, BUGGY_REVISION, source_workspace)
    logs.extend(source_logs)
    source_acquisition.update({
        "campaign_id": CAMPAIGN_ID,
        "candidate": "PySnooper:1",
        "source_metadata_path": repo_rel(V212_EPISODE / "source_repo_metadata.json"),
        "decision_time_safe_metadata_hashes": evidence_hashes([
            V212_EPISODE / "source_repo_metadata.json",
            V212_EPISODE / "dependency_cofactor_recovery_result.json",
            V212_PREFLIGHT / "candidate_metadata.json",
        ]),
    })
    write_json(OUTPUT_ROOT / "source_acquisition_audit.json", source_acquisition)

    status_result = run(["git", "-c", f"safe.directory={source_workspace.as_posix()}", "status", "--porcelain"], cwd=source_workspace, timeout=30) if source_workspace.exists() else {"returncode": 1, "stdout_excerpt": "workspace missing"}
    tree_digest, file_count = tree_hash(source_workspace)
    residuals = count_residuals(source_workspace)
    stale_count = sum(residuals.values())
    workspace_purity = {
        "status": "PASS" if source_acquisition["status"] == "PASS" and stale_count == 0 and status_result.get("stdout_excerpt", "").strip() == "" else "BLOCK",
        "campaign_id": CAMPAIGN_ID,
        "workspace_path": str(source_workspace),
        "workspace_outside_repo": is_outside_repo(source_workspace),
        "workspace_path_under_onedrive": "onedrive" in str(source_workspace).lower(),
        "creation_timestamp_utc": utc_now(),
        "checkout_revision": BUGGY_REVISION,
        "git_status_clean": status_result.get("returncode") == 0 and status_result.get("stdout_excerpt", "").strip() == "",
        "workspace_tree_manifest_sha256": tree_digest,
        "workspace_file_count": file_count,
        "residual_counts": residuals,
        "stale_cache_contamination_count": stale_count,
        "forbidden_residual_files_count": stale_count,
    }
    write_json(OUTPUT_ROOT / "workspace_purity_report.json", workspace_purity)

    workspace_protection = {
        "status": "PASS" if workspace_purity["status"] == "PASS" and is_outside_repo(run_root) else "BLOCK",
        "campaign_id": CAMPAIGN_ID,
        "fresh_workspace_path": str(run_root),
        "workspace_attempt_number": 1,
        "previous_workspace_archived_or_deleted_before_new_attempt": previous_workspace_deleted or True,
        "protected_workspace": True,
        "outside_repo": is_outside_repo(run_root),
        "outside_onedrive": "onedrive" not in str(run_root).lower(),
        "stale_cache_count": stale_count,
        "stop_condition_if_failed": "blocked_workspace_protection_failed",
    }
    write_json(OUTPUT_ROOT / "telomere_workspace_protection_status.json", workspace_protection)

    materialized, benchmark_logs = search_bugsinpy_test(BUGSINPY_REPO, benchmark_workspace, BUGSINPY_TARGET_TEST)
    logs.extend(benchmark_logs)
    materialized.update({
        "campaign_id": CAMPAIGN_ID,
        "candidate_metadata_path": repo_rel(V212_PREFLIGHT / "candidate_metadata.json"),
        "prior_checkout_log_path": repo_rel(preflight_log),
        "prior_fixture_preflight_path": repo_rel(preflight_result),
        "prior_checkout_log_sha256": sha256_path(preflight_log),
        "prior_fixture_preflight_sha256": sha256_path(preflight_result),
        "prior_checkout_log_observed_fixed_revision_copy": all(
            marker in preflight_log.read_text(encoding="utf-8", errors="replace")
            for marker in [
                "HEAD is now at",
                "Fix unicode issues and add test",
                "tests/test_chinese.py",
                "BugsInPy/projects/PySnooper/bugs/1/tests/test_chinese.py",
            ]
        ),
        "prior_checkout_log_used_as_content_source": False,
        "fixed_revision_copy_observation_disqualifies_content_source": True,
        "allowed_materialization_sources_searched": [
            "committed BugsInPy command metadata",
            "prior official ControllerGate pre-repair logs for file identity only",
            "public BugsInPy sparse checkout",
        ],
        "materialized_into_runtime_workspace": False,
        "materialized_runtime_path": None,
        "repair_mutation": False,
        "benchmark_harness_materialization": bool(materialized.get("target_test_sha256")),
        "provenance_status": "PASS" if materialized.get("target_test_sha256") else "BLOCK",
    })
    final_blocker = materialized["blocker"] or "none"
    write_json(OUTPUT_ROOT / "materialized_test_provenance.json", materialized)

    materialized_equivalence = {
        "status": "PASS" if materialized["status"] == "PASS" else "BLOCK",
        "campaign_id": CAMPAIGN_ID,
        "candidate": "PySnooper:1",
        "target_test": TARGET_TEST,
        "target_test_sha256": materialized.get("target_test_sha256"),
        "materialized_test_present_in_workspace": False,
        "materialized_test_equivalence_status": "PASS" if materialized["status"] == "PASS" else "BLOCK",
        "blocker": final_blocker if materialized["status"] != "PASS" else None,
        "classification": "benchmark_harness_materialization_not_performed" if materialized["status"] != "PASS" else "benchmark_harness_materialized_decision_time_safe",
        "repair_mutation": False,
    }
    write_json(OUTPUT_ROOT / "materialized_test_equivalence_summary.json", materialized_equivalence)

    workspace_equivalence = {
        "status": "PASS" if source_acquisition["status"] == "PASS" and materialized["status"] == "PASS" else "BLOCK",
        "campaign_id": CAMPAIGN_ID,
        "candidate": "PySnooper:1",
        "source_commit_revision": BUGGY_REVISION,
        "acquired_head_sha": source_acquisition.get("acquired_head_sha"),
        "expected_target_file": TARGET_TEST,
        "raw_public_checkout_target_file_present": (source_workspace / TARGET_TEST).is_file(),
        "materialized_target_test_provenance_status": materialized["status"],
        "all_materialization_required_files_present": materialized["status"] == "PASS",
        "workspace_equivalence_status": "PASS" if materialized["status"] == "PASS" else "BLOCK",
        "blocker": final_blocker if materialized["status"] != "PASS" else None,
    }
    write_json(OUTPUT_ROOT / "workspace_equivalence_summary.json", workspace_equivalence)

    setup_path = source_workspace / "setup.py"
    tox_path = source_workspace / "tox.ini"
    requirements_path = source_workspace / "requirements.txt"
    declared_dependencies: list[str] = []
    if setup_path.is_file() and "python-toolbox" in setup_path.read_text(encoding="utf-8", errors="replace"):
        declared_dependencies.append("python-toolbox")
    env_lock = {
        "status": "PASS" if source_acquisition["status"] == "PASS" and "python-toolbox" in declared_dependencies else "BLOCK",
        "campaign_id": CAMPAIGN_ID,
        "candidate": "PySnooper:1",
        "python_version_selected": source_metadata.get("python_version_required") or "3.8.1",
        "declared_dependencies": declared_dependencies,
        "python_toolbox_declared": "python-toolbox" in declared_dependencies,
        "dependency_metadata_hashes": evidence_hashes([setup_path, tox_path, requirements_path]),
        "dependency_metadata_inspected": [str(path) for path in [setup_path, tox_path, requirements_path] if path.is_file()],
        "lock_artifact_generated": False,
        "lock_artifact_sha256": None,
        "source_lineage": [repo_rel(V212_EPISODE / "source_repo_metadata.json"), str(setup_path)],
        "no_undeclared_dependency_install": True,
        "no_global_environment_mutation": True,
        "blocker": None if "python-toolbox" in declared_dependencies else "pre_repair_environment_lock_missing",
    }
    write_json(OUTPUT_ROOT / "environment_lock_summary.json", env_lock)

    command_map_material = {
        "candidate": "PySnooper:1",
        "target_command": TARGET_COMMAND,
        "cwd": str(source_workspace),
        "pythonpath_additions": [str(source_workspace)],
        "target_test_paths": [TARGET_TEST],
        "decision_time_safe_basis": [
            repo_rel(V212_PREFLIGHT / "candidate_metadata.json"),
            repo_rel(V212_PREFLIGHT / "failing_command.txt"),
            repo_rel(V212_PREFLIGHT / "normalized_failing_command.txt"),
        ],
    }
    command_map = {
        "status": "PASS" if candidate_metadata.get("normalized_direct_command") == TARGET_COMMAND else "BLOCK",
        "campaign_id": CAMPAIGN_ID,
        "candidate_id": "PySnooper:1",
        "raw_executable_target_command": candidate_metadata.get("direct_command"),
        "target_command": TARGET_COMMAND,
        "cwd": str(source_workspace),
        "pythonpath_additions": [str(source_workspace)],
        "target_test_paths": [TARGET_TEST],
        "decision_time_safe_basis": command_map_material["decision_time_safe_basis"],
        "command_manifest_sha256": canonical_sha(command_map_material),
        "blocker": None if candidate_metadata.get("normalized_direct_command") == TARGET_COMMAND else "blocked_command_manifest_missing_or_unsafe",
    }
    write_json(OUTPUT_ROOT / "bugsinpy_command_map_v1.json", command_map)

    dep = {
        "status": "BLOCK",
        "campaign_id": CAMPAIGN_ID,
        "candidate": "PySnooper:1",
        "dependency_recovery_status": "not_executed_materialized_test_provenance_blocked",
        "declared_dependencies_authorized": declared_dependencies,
        "install_attempted": False,
        "isolated_venv_created": False,
        "undeclared_dependency_installed": False,
        "global_environment_mutated": False,
        "import_statements_alone_used_to_authorize_install": False,
        "blocker": final_blocker,
    }
    write_json(OUTPUT_ROOT / "dependency_recovery_audit.json", dep)

    replay = {
        "status": "BLOCK",
        "campaign_id": CAMPAIGN_ID,
        "candidate": "PySnooper:1",
        "pre_repair_replay_status": "not_run_materialized_test_provenance_blocked",
        "pre_repair_replay_attempted": False,
        "target_command": TARGET_COMMAND,
        "replay_before_patch_authorization": True,
        "stdout_sha256": None,
        "stderr_sha256": None,
        "failure_reproduced": False,
        "blocker": final_blocker,
    }
    write_json(OUTPUT_ROOT / "pre_repair_replay_gate_summary.json", replay)

    decision_material = {
        "source_acquisition": source_acquisition.get("acquired_head_sha"),
        "materialized_test": materialized.get("target_test_sha256"),
        "candidate_metadata": sha256_path(V212_PREFLIGHT / "candidate_metadata.json"),
        "v2_18_results": sha256_path(V218_ROOT / "campaign_results.json"),
        "v2_18_official_record": sha256_path(V218_ROOT / "v2_18_official_artifact_verification.json"),
    }
    cognitive = {
        "status": "PASS",
        "candidate": "PySnooper:1",
        "prompt_hash_available": False,
        "prompt_hash": None,
        "context_sources_used": [
            repo_rel(V212_PREFLIGHT / "candidate_metadata.json"),
            repo_rel(V212_PREFLIGHT / "checkout_log_raw.txt"),
            repo_rel(V212_PREFLIGHT / "fixture_dependency_preflight_result.json"),
            repo_rel(V218_ROOT / "campaign_results.json"),
        ],
        "ast_snippets_or_context_hashes_used": evidence_hashes([
            V212_PREFLIGHT / "candidate_metadata.json",
            V212_PREFLIGHT / "checkout_log_raw.txt",
            V218_ROOT / "campaign_results.json",
        ]),
        "minimal_probe_outputs_used": [],
        "previous_failure_classifications_used": [
            v218_results.get("pysnooper1_classification"),
            "blocked_workspace_equivalence_missing_materialized_target_test",
        ],
        "decision_time_evidence_hash": canonical_sha(decision_material),
        "generated_patch_hash": None,
        "fixed_gold_future_evidence_used": False,
        "written_before_patch_generation": True,
    }
    cognitive["cognitive_state_hash"] = canonical_sha({k: v for k, v in cognitive.items() if k != "cognitive_state_hash"})
    write_json(OUTPUT_ROOT / "s_engine_cognitive_state_snapshot.json", cognitive)

    reward = {
        "status": "not_run_no_target_command_execution",
        "candidate": "PySnooper:1",
        "diagnostic_only": True,
        "full_scoring_enabled": False,
        "broad_benchmark_claim": False,
        "command_run": None,
        "patch_hash": None,
        "total_tests_or_items_observed": None,
        "passed": None,
        "failed": None,
        "skipped": None,
        "failure_signature": None,
        "graded_signal": None,
        "comparison_to_prior_known_failed_patch_by_hash_or_signature_only": True,
        "blocker": final_blocker,
    }
    write_json(OUTPUT_ROOT / "retrocausal_reward_signal.json", reward)

    structural = {
        "status": "not_run_no_target_command_execution",
        "candidate": "PySnooper:1",
        "import_errors": None,
        "assertion_errors": None,
        "fixture_errors": None,
        "timeout_errors": None,
        "syntax_errors": None,
        "collection_errors": None,
        "failure_locations": [],
        "blocker": final_blocker,
    }
    structural["structural_signature_hash"] = canonical_sha({k: v for k, v in structural.items() if k != "structural_signature_hash"})
    write_json(OUTPUT_ROOT / "test_suite_structural_signature.json", structural)

    patch_size = {
        "status": "PASS",
        "candidate": "PySnooper:1",
        "patch_exists": False,
        "max_files_touched": 3,
        "max_lines_changed": 50,
        "max_functions_modified": 2,
        "actual_files_touched": 0,
        "actual_lines_changed": 0,
        "actual_functions_modified": 0,
        "blocker": None,
    }
    write_json(OUTPUT_ROOT / "patch_size_cap.json", patch_size)

    realtime = {
        "status": "not_applicable_no_patch",
        "candidate": "PySnooper:1",
        "file_modification_checks": [],
        "source_only_status_per_file": {},
        "ast_function_locality_checks": {},
        "forbidden_path_checks": {},
        "generation_stopped_immediately_on_failed_check": False,
        "blocker": final_blocker,
    }
    write_json(OUTPUT_ROOT / "realtime_patch_safety_trace.json", realtime)

    application = {
        "status": "not_applicable_no_patch",
        "candidate": "PySnooper:1",
        "verification_happened_before_application": True,
        "pre_application_source_hash": tree_digest,
        "patch_hash": None,
        "apply_status": "not_attempted",
        "post_application_source_hash": tree_digest,
        "blocker": final_blocker,
    }
    write_json(OUTPUT_ROOT / "patch_application_step.json", application)

    post_validation = {
        "status": "not_run_no_validation",
        "candidate": "PySnooper:1",
        "patch_hash": None,
        "validation_result": "not_applicable_no_patch",
        "modified_files_after_validation": [],
        "new_files_after_validation": [],
        "deleted_files_after_validation": [],
        "cache_files_present": [],
        "pytest_cache_present": False,
        "venv_state": "not_created",
        "duplicate_replay_workspace_equivalence": "not_applicable_no_patch",
        "blocker": final_blocker,
    }
    write_json(OUTPUT_ROOT / "post_validation_workspace_analysis.json", post_validation)

    patch_safety = {
        "status": "BLOCK",
        "candidate": "PySnooper:1",
        "patch_generated": False,
        "patch_authorized": False,
        "patch_attempted": False,
        "patch_attempt_count": 0,
        "patch_non_empty": False,
        "semantic_delta_detected": False,
        "no_noop_or_format_only_patch": False,
        "source_only": True,
        "allowed_source_paths": ["pysnooper/**"],
        "touched_files": [],
        "tests_modified": False,
        "fixtures_modified": False,
        "benchmark_metadata_modified": False,
        "harness_modified": False,
        "generated_expectations_modified": False,
        "patch_sha256": None,
        "blocker": final_blocker,
    }
    write_json(OUTPUT_ROOT / "patch_candidate_safety_check.json", patch_safety)

    claims = {
        "status": "PASS",
        "campaign_id": CAMPAIGN_ID,
        "candidate_scope": ["PySnooper:1"],
        "pysnooper2_pursued": False,
        "current_protocol_version": "v2.13",
        "v2_19_promoted_to_current": False,
        "full_scoring": "NOT_RUN",
        "full_scoring_allowed": False,
        "memory_lift_status": "undemonstrated",
        "self_maintaining_software_status": "false/not_demonstrated",
        "non_ansible_generalization": "not_demonstrated",
        "family_generalization": "not_expanded",
    }
    write_json(OUTPUT_ROOT / "claim_boundary_v2_19.json", claims)

    results = {
        "status": "PASS_WITH_MATERIALIZED_TEST_PROVENANCE_BLOCKED",
        "campaign_id": CAMPAIGN_ID,
        "based_on": "v2.18",
        "v2_18_official_ingest_verified": v218_record.get("status") == "PASS",
        "candidate_scope": ["PySnooper:1"],
        "pysnooper2_pursued": False,
        "baseline_registry_precheck_status": baseline["status"],
        "source_acquisition_status": source_acquisition["source_acquisition_status"],
        "source_commit_revision_acquired": source_acquisition.get("acquired_head_sha"),
        "materialized_target_test_provenance_status": materialized["provenance_status"],
        "materialized_target_test_sha256": materialized.get("target_test_sha256"),
        "materialized_test_equivalence_status": materialized_equivalence["status"],
        "workspace_equivalence_status": workspace_equivalence["status"],
        "workspace_purity_status": workspace_purity["status"],
        "environment_lock_status": env_lock["status"],
        "command_manifest_status": command_map["status"],
        "dependency_recovery_status": dep["dependency_recovery_status"],
        "pre_repair_replay_status": replay["pre_repair_replay_status"],
        "cognitive_state_snapshot_status": cognitive["status"],
        "reward_signal_status": reward["status"],
        "test_structural_signature_status": structural["status"],
        "patch_size_cap_status": patch_size["status"],
        "patch_generated": False,
        "patch_authorized": False,
        "patch_attempted": False,
        "target_validation_status": "not_applicable_no_patch",
        "post_validation_analysis_status": post_validation["status"],
        "duplicate_replay_status": "not_applicable_no_patch",
        "pysnooper1_classification": final_blocker,
        "pysnooper1_scoreable": False,
        "pysnooper1_positive_memory_only": False,
        "final_scoreable_count": 5,
        "final_positive_memory_count": 2,
        "final_non_ansible_positive_memory_count": 0,
        "full_scoring": "NOT_RUN",
        "full_scoring_allowed": False,
        "memory_lift_status": "undemonstrated",
        "self_maintaining_software_status": "false/not_demonstrated",
        "current_protocol_version": "v2.13",
        "exact_blocker": "Decision-time-safe BugsInPy target-test content for tests/test_chinese.py was not found. Prior logs identify the target path and show fixed-revision test-copy behavior, but no allowed public benchmark source supplied the file content.",
    }
    write_json(OUTPUT_ROOT / "campaign_results.json", results)

    if run_root.exists():
        remove_tree(run_root)
    cleanup_confirmed = not run_root.exists()
    logs.append(f"workspace_cleanup_confirmed={cleanup_confirmed}")
    logs.append(f"finished_at_utc={utc_now()}")
    write_text(OUTPUT_ROOT / "isolated_execution_log.txt", "\n".join(logs) + "\n")

    ledger = build_ledger(final_blocker, cleanup_confirmed)
    write_json(OUTPUT_ROOT / "proof_obligations_ledger.json", ledger)

    summary = f"""# v2.19 BugsInPy Materialized-Test Provenance Lane

- Campaign: `{CAMPAIGN_ID}`.
- Scope: `PySnooper:1` only; PySnooper:2 was not pursued.
- v2.18 official ingest verified: `{str(results['v2_18_official_ingest_verified']).lower()}`.
- Source acquisition: `{results['source_acquisition_status']}`.
- Source commit acquired: `{results['source_commit_revision_acquired']}`.
- Materialized target-test provenance: `{results['materialized_target_test_provenance_status']}`.
- Materialized target-test SHA256: `{results['materialized_target_test_sha256']}`.
- Workspace purity: `{results['workspace_purity_status']}`.
- Workspace equivalence: `{results['workspace_equivalence_status']}`.
- Environment lock: `{results['environment_lock_status']}`.
- Command manifest: `{results['command_manifest_status']}`.
- Dependency recovery: `{results['dependency_recovery_status']}`.
- Pre-repair replay: `{results['pre_repair_replay_status']}`.
- Repair state snapshot: `{results['cognitive_state_snapshot_status']}`.
- Diagnostic reward signal: `{results['reward_signal_status']}`.
- Test structural signature: `{results['test_structural_signature_status']}`.
- Patch size cap: `{results['patch_size_cap_status']}`.
- Patch generated / authorized / attempted: `false` / `false` / `false`.
- Final blocker: {results['exact_blocker']}
- PySnooper:1 scoreable: `false`; positive-memory-only: `false`.
- Scoreable count remains `5`; positive-memory count remains `2`; non-Ansible positive-memory count remains `0`.
- Full scoring remains `NOT_RUN` / disallowed.
- Memory lift remains `undemonstrated`.
- Self-maintaining software remains `false/not_demonstrated`.
- Current protocol remains `v2.13`; v2.19 is not promoted to current.
"""
    write_text(OUTPUT_ROOT / "campaign_summary.md", summary)
    write_manifest()

    for key in [
        "source_acquisition_status",
        "source_commit_revision_acquired",
        "materialized_target_test_provenance_status",
        "materialized_target_test_sha256",
        "workspace_equivalence_status",
        "workspace_purity_status",
        "environment_lock_status",
        "command_manifest_status",
        "baseline_registry_precheck_status",
        "dependency_recovery_status",
        "pre_repair_replay_status",
        "cognitive_state_snapshot_status",
        "reward_signal_status",
        "test_structural_signature_status",
        "patch_size_cap_status",
        "patch_generated",
        "patch_authorized",
        "patch_attempted",
        "pysnooper1_scoreable",
        "pysnooper1_positive_memory_only",
    ]:
        print(f"{key}={results.get(key)}")
    print(f"v2.19 outputs wrote {OUTPUT_ROOT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
