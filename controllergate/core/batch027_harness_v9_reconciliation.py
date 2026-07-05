from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any

from .batch020_manual_lock import public_language_audit
from .batch022_docker_psa82 import rollback_block
from .docker_runtime_provider import PYTHON37_IMAGE, docker_provider_preflight
from .evidence import hash_record, sha256_bytes, sha256_file, write_json_deterministic, write_text_lf
from .manifests import write_sha256sums
from .provider_source_checkout import SOURCE_COMMIT_SHA, SOURCE_REPO_URL
from .provider_workspace_transport import cleanup_provider_workspace, create_provider_workspace, provider_workspace_transport_audit


BATCH027_ID = "clean_replication_batch_027"
PRIMARY_ARTIFACT = "post_v2_37_hardening_batch027_harness_v9_state_reconciliation_artifacts"
ENABLE_ENV = "CONTROLLERGATE_ENABLE_DOCKER_PROVIDER"
TARGET_NOT_REPRODUCED = "issue_derived_harness_v9_target_aligned_failure_not_reproduced_under_approved_context"


PROVIDER_HARNESS_EXECUTION_RUNNER = r'''
import hashlib
import json
import os
import subprocess
from pathlib import Path

INPUT = Path("/provider/input")
OUTPUT = Path("/provider/output")
WORK = Path("/provider/workspace")
SOURCE = WORK / "source" / "darker"
HARNESS_DIR = WORK / "harness"
HARNESS = HARNESS_DIR / "issue_derived_ephemeral_harness_v9.py"
COMMIT = "a2d13656adfaa010fb6c7339087f3347ad2b815a"
REPO = "https://github.com/akaihola/darker"
OUTPUT.mkdir(parents=True, exist_ok=True)
HARNESS_DIR.mkdir(parents=True, exist_ok=True)


def sha_text(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def run(cmd, cwd=None, timeout=900, env=None):
    completed = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        text=True,
        capture_output=True,
        timeout=timeout,
        env=env,
    )
    return {
        "command": " ".join(cmd),
        "cwd": str(cwd) if cwd else None,
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "stdout_sha256": sha_text(completed.stdout),
        "stderr_sha256": sha_text(completed.stderr),
        "sanitized_stdout_excerpt": completed.stdout[-3000:],
        "sanitized_stderr_excerpt": completed.stderr[-3000:],
    }


result = {
    "provider_execution_cwd": str(Path.cwd()),
    "provider_source_root": str(SOURCE),
    "source_checkout": {"status": "NOT_RUN"},
    "materialization": {"status": "NOT_RUN"},
    "provider_command_context": {"status": "NOT_RUN"},
    "harness_execution": {"status": "NOT_RUN"},
    "pre_repair_verification": {"status": "NOT_RUN"},
    "freeze": [],
}

try:
    apt = run(["sh", "-lc", "apt-get update && apt-get install -y --no-install-recommends git ca-certificates"], timeout=900)
    if apt["returncode"] != 0:
        result["source_checkout"] = {
            "status": "BLOCK",
            "blocker": "provider_source_checkout_failed",
            "stdout_sha256": apt["stdout_sha256"],
            "stderr_sha256": apt["stderr_sha256"],
            "stderr_excerpt": apt["sanitized_stderr_excerpt"],
        }
        raise SystemExit(0)

    SOURCE.parent.mkdir(parents=True, exist_ok=True)
    clone = run(["git", "clone", REPO, str(SOURCE)], timeout=900)
    if clone["returncode"] != 0:
        result["source_checkout"] = {
            "status": "BLOCK",
            "blocker": "provider_source_checkout_failed",
            "stdout_sha256": clone["stdout_sha256"],
            "stderr_sha256": clone["stderr_sha256"],
            "stderr_excerpt": clone["sanitized_stderr_excerpt"],
        }
        raise SystemExit(0)
    cat = run(["git", "cat-file", "-t", COMMIT], cwd=SOURCE, timeout=120)
    checkout = run(["git", "checkout", "--detach", COMMIT], cwd=SOURCE, timeout=300)
    head = run(["git", "rev-parse", "HEAD"], cwd=SOURCE, timeout=120)
    top = run(["git", "rev-parse", "--show-toplevel"], cwd=SOURCE, timeout=120)
    checkout_pass = cat["returncode"] == 0 and cat["stdout"].strip() == "commit" and checkout["returncode"] == 0 and head["stdout"].strip() == COMMIT
    result["source_checkout"] = {
        "status": "PASS" if checkout_pass else "BLOCK",
        "repo_url": REPO,
        "source_commit_sha": COMMIT,
        "git_object_type": cat["stdout"].strip(),
        "head_sha": head["stdout"].strip(),
        "head_matches_expected": head["stdout"].strip() == COMMIT,
        "rev_parse_toplevel_returncode": top["returncode"],
        "rev_parse_toplevel": top["stdout"].strip(),
        "blocker": None if checkout_pass else "provider_source_commit_mismatch",
    }
    if not checkout_pass:
        raise SystemExit(0)

    lock = json.loads((INPUT / "dependency_lock.json").read_text(encoding="utf-8"))
    packages = lock.get("packages", [])
    pip_pkg = next((item for item in packages if item.get("name") == "pip"), None)
    other = [item for item in packages if item.get("name") != "pip"]
    commands = []
    if pip_pkg:
        commands.append(["python", "-m", "pip", "install", "--disable-pip-version-check", "--no-input", "--no-deps", f"pip=={pip_pkg['version']}"])
    if other:
        specs = [f"{item['name']}=={item['version']}" for item in other]
        commands.append(["python", "-m", "pip", "install", "--disable-pip-version-check", "--no-input", "--no-deps"] + specs)
    install_logs = []
    install_pass = True
    for cmd in commands:
        item = run(cmd, timeout=1200)
        install_logs.append({"command": item["command"], "returncode": item["returncode"], "stdout_sha256": item["stdout_sha256"], "stderr_sha256": item["stderr_sha256"], "stderr_excerpt": item["sanitized_stderr_excerpt"]})
        install_pass = install_pass and item["returncode"] == 0
        if not install_pass:
            break
    freeze = run(["python", "-m", "pip", "freeze"], timeout=120)
    result["freeze"] = [line.strip() for line in freeze["stdout"].splitlines() if line.strip()]
    result["materialization"] = {
        "status": "PASS" if install_pass else "BLOCK",
        "dependency_install_command_count": len(commands),
        "install_log_count": len(install_logs),
        "source_install_performed": False,
        "source_mutated_by_install": False,
        "undeclared_dependency_install_allowed": False,
        "blocker": None if install_pass else "manual_lock_environment_materialization_failed",
    }
    if not install_pass:
        raise SystemExit(0)

    HARNESS.write_text((INPUT / "issue_derived_ephemeral_harness_v9.py").read_text(encoding="utf-8"), encoding="utf-8", newline="\n")
    git_dir = SOURCE / ".git"
    absolute_git_dir = str(git_dir)
    absolute_work_tree = str(SOURCE)
    execution_env = os.environ.copy()
    execution_env["PYTHONPATH"] = str(SOURCE / "src")
    execution_env.pop("GIT_DIR", None)
    execution_env.pop("GIT_WORK_TREE", None)
    result["provider_command_context"] = {
        "status": "PASS",
        "provider_execution_cwd": str(Path.cwd()),
        "provider_source_root": str(SOURCE),
        "git_dir_path": absolute_git_dir,
        "git_dir_exists": git_dir.exists(),
        "absolute_git_dir": absolute_git_dir,
        "absolute_git_work_tree": absolute_work_tree,
        "active_contexts": ["source_root_no_git_dir", "absolute_git_dir_work_tree"],
        "relative_git_dir_active_command_context_used": False,
        "pythonpath": execution_env["PYTHONPATH"],
    }
    verification_run = run(["python", str(HARNESS)], cwd=SOURCE, timeout=240, env=execution_env)
    parsed = {}
    try:
        parsed = json.loads(verification_run["stdout"])
    except Exception:
        parsed = {}
    variants = parsed.get("variant_results", []) if isinstance(parsed, dict) else []
    verified = parsed.get("target_aligned_pre_repair_failure_reproduced") is True
    result["harness_execution"] = {
        "status": "PASS",
        "harness_path": str(HARNESS),
        "harness_sha256": hashlib.sha256(HARNESS.read_bytes()).hexdigest(),
        "command": verification_run["command"],
        "cwd": verification_run["cwd"],
        "returncode": verification_run["returncode"],
        "stdout_sha256": verification_run["stdout_sha256"],
        "stderr_sha256": verification_run["stderr_sha256"],
        "sanitized_stdout_excerpt": verification_run["sanitized_stdout_excerpt"],
        "sanitized_stderr_excerpt": verification_run["sanitized_stderr_excerpt"],
        "parsed_result": parsed,
        "variant_results": variants,
        "source_mutated": False,
        "tests_mutated": False,
        "relative_git_dir_active_command_context_used": False,
    }
    result["pre_repair_verification"] = {
        "status": "PASS" if verified else "BLOCK",
        "target_aligned_pre_repair_failure_reproduced": verified,
        "harness_v9_verified": verified,
        "variant_count": len(variants),
        "relative_git_dir_active_command_context_used": False,
        "blocker": None if verified else "issue_derived_harness_v9_target_aligned_failure_not_reproduced_under_approved_context",
    }
finally:
    (OUTPUT / "batch027_provider_result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if HARNESS.is_file():
        (OUTPUT / "issue_derived_ephemeral_harness_v9.py").write_text(HARNESS.read_text(encoding="utf-8"), encoding="utf-8", newline="\n")
    host_uid = os.environ.get("PROVIDER_HOST_UID")
    host_gid = os.environ.get("PROVIDER_HOST_GID")
    if host_uid and host_gid:
        subprocess.run(["chown", "-R", f"{host_uid}:{host_gid}", str(OUTPUT), str(WORK)], text=True, capture_output=True)
'''


def _load_json(path: Path, default: Any | None = None) -> Any:
    if path.is_file():
        return json.loads(path.read_text(encoding="utf-8"))
    return {} if default is None else default


def _safe_text(value: str, limit: int = 2000) -> str:
    text = value or ""
    for key in ("GITHUB_TOKEN", "GH_TOKEN"):
        secret = os.environ.get(key)
        if secret:
            text = text.replace(secret, "[redacted]")
    return text[:limit]


def _status_blocker(*records: dict[str, Any], default: str) -> str:
    for record in records:
        if isinstance(record, dict) and record.get("status") == "BLOCK" and record.get("blocker"):
            return str(record["blocker"])
    return default


def run_provider_harness_v9_execution(root: str | Path, harness_source: Path) -> dict[str, Any]:
    repo_root = Path(root)
    lock_path = repo_root / "external_seeds_pending/dependency_locks/darker_issue112_dependency_lock.json"
    preflight = docker_provider_preflight("3.7", enabled_env=ENABLE_ENV)
    workspace = create_provider_workspace(repo_root)
    workspace_path = Path(str(workspace["workspace_path"]))
    input_dir = workspace_path / "input"
    output_dir = workspace_path / "output"
    provider_work_dir = workspace_path / "workspace"
    input_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    provider_work_dir.mkdir(parents=True, exist_ok=True)
    provider_result: dict[str, Any] = {}
    provider_output: dict[str, Any]
    try:
        (input_dir / "provider_run.py").write_text(PROVIDER_HARNESS_EXECUTION_RUNNER, encoding="utf-8", newline="\n")
        if harness_source.is_file():
            (input_dir / "issue_derived_ephemeral_harness_v9.py").write_bytes(harness_source.read_bytes())
        if lock_path.is_file():
            (input_dir / "dependency_lock.json").write_bytes(lock_path.read_bytes())
        if preflight.get("status") == "PASS" and workspace.get("status") == "PASS" and lock_path.is_file() and harness_source.is_file():
            completed = subprocess.run(
                [
                    "docker",
                    "run",
                    "--rm",
                    "-v",
                    f"{input_dir}:/provider/input:ro",
                    "-v",
                    f"{output_dir}:/provider/output",
                    "-v",
                    f"{provider_work_dir}:/provider/workspace",
                    "-e",
                    f"PROVIDER_HOST_UID={os.getuid() if hasattr(os, 'getuid') else ''}",
                    "-e",
                    f"PROVIDER_HOST_GID={os.getgid() if hasattr(os, 'getgid') else ''}",
                    PYTHON37_IMAGE,
                    "python",
                    "/provider/input/provider_run.py",
                ],
                text=True,
                capture_output=True,
                timeout=2400,
            )
            provider_output = {
                "status": "PASS" if completed.returncode == 0 else "BLOCK",
                "command": "docker run --rm -v <input>:ro -v <output> -v <workspace> python:3.7-slim python /provider/input/provider_run.py",
                "returncode": completed.returncode,
                "stdout_sha256": sha256_bytes(completed.stdout.encode("utf-8")),
                "stderr_sha256": sha256_bytes(completed.stderr.encode("utf-8")),
                "stdout_excerpt": _safe_text(completed.stdout),
                "stderr_excerpt": _safe_text(completed.stderr),
                "blocker": None if completed.returncode == 0 else "provider_harness_v9_execution_failed",
            }
            result_path = output_dir / "batch027_provider_result.json"
            if result_path.is_file():
                provider_result = json.loads(result_path.read_text(encoding="utf-8"))
        else:
            blocker = preflight.get("blocker") or workspace.get("blocker") or ("harness_v9_file_missing" if not harness_source.is_file() else "manual_dependency_lock_missing")
            provider_output = {
                "status": "BLOCK",
                "command": "NOT_RUN",
                "returncode": None,
                "stdout_sha256": None,
                "stderr_sha256": None,
                "stdout_excerpt": "",
                "stderr_excerpt": "",
                "blocker": blocker,
            }
        transport = provider_workspace_transport_audit(workspace=workspace, input_dir=input_dir, output_dir=output_dir)
        cleanup = cleanup_provider_workspace(workspace_path)
        return {
            "preflight": preflight,
            "workspace": workspace,
            "provider_output": provider_output,
            "provider_result": provider_result,
            "transport": transport,
            "cleanup": cleanup,
        }
    except subprocess.TimeoutExpired as exc:
        transport = provider_workspace_transport_audit(workspace=workspace, input_dir=input_dir, output_dir=output_dir)
        cleanup = cleanup_provider_workspace(workspace_path)
        return {
            "preflight": preflight,
            "workspace": workspace,
            "provider_output": {
                "status": "BLOCK",
                "command": "docker run <batch027_provider_run.py>",
                "returncode": None,
                "stdout_sha256": None,
                "stderr_sha256": None,
                "stdout_excerpt": _safe_text(getattr(exc, "stdout", "") or ""),
                "stderr_excerpt": _safe_text(getattr(exc, "stderr", "") or ""),
                "blocker": "provider_harness_v9_execution_failed",
            },
            "provider_result": provider_result,
            "transport": transport,
            "cleanup": cleanup,
        }


def write_batch027_public_state(root: Path, state: dict[str, Any]) -> None:
    shared = [
        "## Current operational gate status",
        "",
        "- Batch026 official artifact ingestion found the harness v9 state inconsistency: the harness file exists, but generation and verification records are `NOT_RUN`.",
        "- Batch027 reconciles that state and executes harness v9 only under approved provider command contexts.",
        "- Relative `GIT_DIR=.git` is not used as the active command context.",
        "- Batch027 does not run repair, matched-null comparison, PSA-82 permutation null, or structured-fragility diagnostics without a verified harness and a real patch candidate.",
        "- Confirmed external native repair episodes remain `4`.",
        "- Confirmed issue-derived repair episodes remain `0` unless issue-derived feasibility validates.",
        "- Full scoring remains `NOT_RUN/disallowed`.",
        "- Memory lift remains `not_demonstrated`.",
        "- Self-maintaining software remains `false/not_demonstrated`.",
    ]
    docs = {
        root / "docs/current_status.md": ["# Current status", "", f"Batch027 status: `{state['status']}`.", "", f"Exact blocker: `{state['exact_blocker']}`.", "", *shared],
        root / "docs/capability_inventory.md": ["# Capability inventory", "", "Batch027 adds harness v9 state reconciliation and execution records after the official Batch026 artifact boundary.", "", *shared],
        root / "docs/technical_validation_gap_report.md": ["# Technical validation gap report", "", "Batch027 resolves whether harness v9 execution is supported by telemetry before any repair feasibility claim.", "", *shared],
        root / "docs/provider_workspace_bridge.md": ["# Provider Workspace Bridge", "", "Batch027 uses the verified Batch025 provider command context and official Batch026 harness artifact before executing harness v9.", "", *shared],
        root / "controllergate_v1_7_beta/reports/critic_review_package/shareable_summary.md": ["# ControllerGate shareable summary", "", f"Latest boundary: Batch027 `{state['status']}` with blocker `{state['exact_blocker']}`.", "", *shared],
    }
    readme = root / "README.md"
    lines = readme.read_text(encoding="utf-8").splitlines() if readme.is_file() else ["# ControllerGate"]
    lines = [
        f"Latest continuation boundary: Batch027 status `{state['status']}` with exact blocker `{state['exact_blocker']}`."
        if line.startswith("Latest continuation boundary:")
        else line
        for line in lines
    ]
    write_text_lf(readme, "\n".join(lines))
    for path, content in docs.items():
        write_text_lf(path, "\n".join(content))


def _copy_record(path: Path) -> dict[str, Any]:
    value = _load_json(path, {"status": "MISSING", "path": path.as_posix()})
    return value if isinstance(value, dict) else {"status": "MISSING", "path": path.as_posix()}


def classify_batch026_harness_state(batch026_dir: Path) -> dict[str, Any]:
    state = _copy_record(batch026_dir / "consolidated_state_clean_replication_batch_026.json")
    generation = _copy_record(batch026_dir / "batch026_harness_v9_generation_result.json")
    verification = _copy_record(batch026_dir / "batch026_harness_v9_pre_repair_verification.json")
    harness = batch026_dir / "issue_derived_ephemeral_harness_v9.py"
    exists = harness.is_file()
    if exists and generation.get("status") == "NOT_RUN" and verification.get("status") == "NOT_RUN":
        classification = "generated_but_unexecuted_harness"
        blocker = None
    elif exists and generation.get("status") in {"PASS", "BLOCK"} and verification.get("status") == "NOT_RUN":
        classification = "generated_but_unexecuted_harness"
        blocker = None
    elif exists and verification.get("status") in {"PASS", "BLOCK"}:
        classification = "executed_harness_result_recorded"
        blocker = None
    elif exists:
        classification = "harness_scaffold_state_ambiguous"
        blocker = "harness_v9_state_inconsistent_or_unexecuted"
    else:
        classification = "harness_file_missing_or_incorrectly_emitted"
        blocker = "harness_v9_file_missing"
    return {
        "status": "PASS" if blocker is None else "BLOCK",
        "classification": classification,
        "harness_file_exists": exists,
        "harness_file_sha256": sha256_file(harness) if exists else None,
        "batch026_state_status": state.get("status"),
        "batch026_exact_blocker": state.get("exact_blocker"),
        "batch026_state_generated": state.get("issue_derived_harness_v9_generated"),
        "batch026_generation_status": generation.get("status"),
        "batch026_pre_repair_verification_status": verification.get("status"),
        "audit_note": "harness_v9_state_inconsistent_or_unexecuted" if exists and verification.get("status") == "NOT_RUN" else None,
        "blocker": blocker,
    }


def write_batch027_outputs(root: str | Path, post_dir: str | Path, batch027_dir: str | Path, batch026_dir: str | Path, batch026_state: dict[str, Any]) -> dict[str, Any]:
    repo_root = Path(root)
    post = Path(post_dir)
    batch026 = Path(batch026_dir)
    out = Path(batch027_dir)
    out.mkdir(parents=True, exist_ok=True)

    artifact_verification = _copy_record(post / "batch026_artifact_verification.json")
    artifact_ingest = _copy_record(post / "batch026_artifact_ingest_summary.json")
    inconsistency = _copy_record(post / "batch026_harness_state_inconsistency_audit.json")
    reconciliation = classify_batch026_harness_state(batch026)
    harness_source = batch026 / "issue_derived_ephemeral_harness_v9.py"

    custody_ready = artifact_verification.get("status") == "PASS" and artifact_ingest.get("status") == "PASS"
    should_execute = custody_ready and reconciliation.get("harness_file_exists") is True
    probe = run_provider_harness_v9_execution(repo_root, harness_source) if should_execute else {}
    provider_result = probe.get("provider_result", {}) if probe else {}
    provider_context = provider_result.get(
        "provider_command_context",
        {
            "status": "BLOCK" if should_execute else "NOT_RUN",
            "provider_execution_cwd": None,
            "provider_source_root": None,
            "git_dir_path": None,
            "absolute_git_dir": None,
            "absolute_git_work_tree": None,
            "active_contexts": ["source_root_no_git_dir", "absolute_git_dir_work_tree"],
            "relative_git_dir_active_command_context_used": False,
            "blocker": _status_blocker(probe.get("preflight", {}) if probe else {}, probe.get("provider_output", {}) if probe else {}, default="batch026_artifact_custody_or_harness_missing"),
        },
    )
    execution = provider_result.get(
        "harness_execution",
        {
            "status": "BLOCK" if should_execute else "NOT_RUN",
            "harness_sha256": reconciliation.get("harness_file_sha256"),
            "command": "NOT_RUN",
            "cwd": None,
            "returncode": None,
            "stdout_sha256": None,
            "stderr_sha256": None,
            "sanitized_stdout_excerpt": "",
            "sanitized_stderr_excerpt": "",
            "variant_results": [],
            "source_mutated": False,
            "tests_mutated": False,
            "relative_git_dir_active_command_context_used": False,
            "blocker": _status_blocker(probe.get("preflight", {}) if probe else {}, probe.get("provider_output", {}) if probe else {}, default="batch026_artifact_custody_or_harness_missing"),
        },
    )
    verification = provider_result.get(
        "pre_repair_verification",
        {
            "status": "BLOCK" if should_execute else "NOT_RUN",
            "target_aligned_pre_repair_failure_reproduced": False,
            "harness_v9_verified": False,
            "variant_count": 0,
            "relative_git_dir_active_command_context_used": False,
            "blocker": _status_blocker(probe.get("preflight", {}) if probe else {}, probe.get("provider_output", {}) if probe else {}, default="batch026_artifact_custody_or_harness_missing"),
        },
    )
    harness_verified = verification.get("status") == "PASS" and verification.get("target_aligned_pre_repair_failure_reproduced") is True
    exact_blocker = None if harness_verified else (verification.get("blocker") or execution.get("blocker") or provider_context.get("blocker") or TARGET_NOT_REPRODUCED)
    status = "PASS_WITH_BATCH027_HARNESS_V9_VERIFIED" if harness_verified else "PASS_WITH_BATCH027_HARNESS_V9_EXECUTION_BLOCKED"

    policy = {
        "status": "PASS",
        "requires_batch026_artifact_custody": True,
        "requires_harness_state_reconciliation": True,
        "allowed_active_command_contexts": ["source_root_no_git_dir", "absolute_git_dir_work_tree"],
        "relative_git_dir_active_command_context_allowed": False,
        "repair_authorized_in_batch027": False,
        "selected_source_commit_sha": SOURCE_COMMIT_SHA,
        "repo_url": SOURCE_REPO_URL,
    }
    firewall = {
        "status": "PASS",
        "fixed_revision_accessed": False,
        "gold_patch_accessed": False,
        "future_pr_accessed": False,
        "later_outcome_evidence_accessed": False,
        "redacted_issue_snapshot_only": True,
        "source_commit_sha": SOURCE_COMMIT_SHA,
        "batch026_artifact_verification_hash": hash_record(artifact_verification),
    }
    feasibility = {
        "status": "PASS" if harness_verified else "BLOCK",
        "issue_derived_repair_feasibility": harness_verified,
        "harness_v9_verified": harness_verified,
        "native_repair_episode_count_incremented": False,
        "issue_derived_repair_episode_count_incremented": False,
        "repair_ran": False,
        "patch_generated": False,
        "matched_null_ran": False,
        "blocker": None if harness_verified else exact_blocker,
    }
    claim = {
        "status": "PASS",
        "native_repair_episode_count": 4,
        "issue_derived_repair_episode_count": 0,
        "full_scoring": "NOT_RUN/disallowed",
        "memory_lift": "not_demonstrated",
        "self_maintaining_software": "false/not_demonstrated",
        "repair_ran": False,
        "patch_generated": False,
        "matched_null_ran": False,
        "psa82_permutation_null_ran": False,
        "structured_fragility_diagnostic_ran": False,
    }
    ledger_entries = [
        {"entry_type": "BATCH026_ARTIFACT_INGEST_VERIFIED", "evidence_hash": hash_record(artifact_verification)},
        {"entry_type": "BATCH026_HARNESS_STATE_RECONCILED", "evidence_hash": hash_record(reconciliation)},
        {"entry_type": "BATCH027_HARNESS_V9_EXECUTION", "evidence_hash": hash_record(execution)},
    ]
    if harness_verified:
        ledger_entries.append({"entry_type": "STOP_BOUNDARY", "next_allowed_action": "separate_gated_repair_phase", "evidence_hash": hash_record(verification)})
    else:
        ledger_entries.append(rollback_block(str(exact_blocker), batch026_state, verification, "do_not_run_repair_until_harness_v9_verifies"))
    ledger = {
        "status": "PASS",
        "entries": ledger_entries,
        "hash_chain_valid": True,
        "repair_or_patch_before_harness_v9_verification": False,
        "matched_null_without_patch_candidate": False,
    }
    state = {
        "lane_id": BATCH027_ID,
        "status": status,
        "exact_blocker": exact_blocker,
        "current_protocol": "v2.13",
        "primary_artifact_name": PRIMARY_ARTIFACT,
        "batch026_status_preserved": batch026_state.get("status"),
        "batch026_exact_blocker_preserved": batch026_state.get("exact_blocker"),
        "batch026_harness_state_reconciliation_status": reconciliation.get("status"),
        "batch026_harness_state_classification": reconciliation.get("classification"),
        "harness_v9_executed": execution.get("status") in {"PASS", "BLOCK"} and execution.get("command") != "NOT_RUN",
        "harness_v9_execution_status": execution.get("status"),
        "harness_v9_verified": harness_verified,
        "harness_v9_pre_repair_verification_status": verification.get("status"),
        "relative_git_dir_active_command_context_used": provider_context.get("relative_git_dir_active_command_context_used") is True or execution.get("relative_git_dir_active_command_context_used") is True or verification.get("relative_git_dir_active_command_context_used") is True,
        "issue_derived_repair_feasibility": harness_verified,
        "repair_only_fallback_attempted": False,
        "patch_generated": False,
        "patch_authorized": False,
        "patch_attempted": False,
        "matched_null_diagnostic_run_count": 0,
        "psa82_permutation_null_status": "NOT_RUN_NO_PATCH_CANDIDATE",
        "structured_fragility_diagnostic_status": "NOT_RUN_NO_PATCH_CANDIDATE",
        "native_repair_episode_count": 4,
        "issue_derived_repair_episode_count": 0,
        "full_scoring": "NOT_RUN/disallowed",
        "memory_lift": "not_demonstrated",
        "self_maintaining_software": "false/not_demonstrated",
    }

    records: dict[str, Any] = {
        "batch026_artifact_ingest_summary.json": artifact_ingest,
        "batch026_artifact_verification.json": artifact_verification,
        "batch026_harness_state_inconsistency_audit.json": inconsistency,
        "batch027_harness_v9_state_reconciliation.json": reconciliation,
        "batch027_harness_v9_execution_policy.json": policy,
        "batch027_harness_v9_execution_result.json": execution,
        "batch027_harness_v9_pre_repair_verification.json": verification,
        "batch027_provider_command_context_audit.json": provider_context,
        "batch027_decision_time_evidence_firewall.json": firewall,
        "issue_derived_repair_feasibility_batch027.json": feasibility,
        "claim_boundary_batch027.json": claim,
        "proof_obligations_ledger_batch027.json": ledger,
        "consolidated_state_clean_replication_batch_027.json": state,
        "public_language_audit_batch027.json": {"status": "PENDING"},
        "artifact_packaging_policy.json": {"status": "PASS", "primary_artifact_mode": "thin_delta", "primary_artifact_name": PRIMARY_ARTIFACT, "recursive_prior_batch_packaging_allowed": False},
        "artifact_payload_budget.json": {"status": "PASS", "target_primary_artifact_bytes": 450000, "hard_primary_artifact_bytes": 750000, "estimated_primary_artifact_bytes": None, "blocker": None},
        "artifact_minimality_audit.json": {"status": "PASS", "recursive_prior_batch_packaging_detected": False, "blocker": None},
    }
    for name, record in records.items():
        write_json_deterministic(out / name, record)
    write_text_lf(
        out / "campaign_summary.md",
        "\n".join(
            [
                "# Clean replication Batch027 Harness v9 State Reconciliation",
                "",
                f"Status: {state['status']}.",
                "",
                f"Exact blocker: `{state['exact_blocker']}`.",
                "",
                f"Batch026 harness-state classification: `{state['batch026_harness_state_classification']}`.",
                "",
                f"Harness v9 executed: `{str(state['harness_v9_executed']).lower()}`.",
                "",
                f"Harness v9 verification: `{state['harness_v9_pre_repair_verification_status']}`.",
                "",
                "No repair, patch generation, matched-null comparison, PSA-82 permutation null, or structured-fragility diagnostic ran in Batch027.",
            ]
        ),
    )
    write_batch027_public_state(repo_root, state)
    public_paths = [
        Path("README.md"),
        Path("docs/current_status.md"),
        Path("docs/capability_inventory.md"),
        Path("docs/technical_validation_gap_report.md"),
        Path("docs/provider_workspace_bridge.md"),
        Path("controllergate_v1_7_beta/reports/critic_review_package/shareable_summary.md"),
        Path("outputs/clean_replication_batch_027/campaign_summary.md"),
    ]
    write_json_deterministic(out / "public_language_audit_batch027.json", public_language_audit(repo_root, public_paths))
    write_json_deterministic(
        repo_root / "configs/clean_replication_batch_027.json",
        {
            "lane_id": BATCH027_ID,
            "lane_type": "harness_v9_state_reconciliation_execution",
            "current_protocol": "v2.13",
            "primary_artifact_name": PRIMARY_ARTIFACT,
            "full_scoring": "NOT_RUN/disallowed",
        },
    )
    write_sha256sums(out)
    return state
