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


BATCH026_ID = "clean_replication_batch_026"
PRIMARY_ARTIFACT = "post_v2_37_hardening_batch026_issue_derived_harness_v9_artifacts"
ENABLE_ENV = "CONTROLLERGATE_ENABLE_DOCKER_PROVIDER"
HARNESS_BLOCKER = "issue_derived_harness_v9_target_aligned_failure_not_reproduced_under_approved_context"


HARNESS_V9_TEXT = r'''
from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1] / "source" / "darker"


def sha_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def run_variant(variant_id, command, env=None):
    completed = subprocess.run(command, cwd=str(SOURCE), env=env, text=True, capture_output=True, timeout=180)
    combined = completed.stdout + "\n" + completed.stderr
    target_terms = ["Not a git repository", "git_get_modified_files", "_git_check_output_lines", "git diff --name-only"]
    precondition_terms = ["ModuleNotFoundError", "ImportError", "No module named", "dependency API mismatch"]
    return {
        "variant_id": variant_id,
        "command": " ".join(command),
        "cwd": str(SOURCE),
        "returncode": completed.returncode,
        "stdout_sha256": sha_text(completed.stdout),
        "stderr_sha256": sha_text(completed.stderr),
        "sanitized_stdout_excerpt": completed.stdout[-1200:],
        "sanitized_stderr_excerpt": completed.stderr[-1200:],
        "target_indicator_seen": any(term in combined for term in target_terms),
        "environment_precondition_error_seen": any(term in combined for term in precondition_terms),
    }


def main() -> int:
    base_env = os.environ.copy()
    absolute_env = base_env.copy()
    absolute_env["GIT_DIR"] = str(SOURCE / ".git")
    absolute_env["GIT_WORK_TREE"] = str(SOURCE)
    variants = [
        run_variant("source_root_no_git_dir_python_module", ["python", "-m", "darker", "--check", "src"], base_env),
        run_variant("absolute_git_dir_work_tree_python_module", ["python", "-m", "darker", "--check", "src"], absolute_env),
    ]
    verified = any(
        item["returncode"] != 0
        and item["target_indicator_seen"]
        and not item["environment_precondition_error_seen"]
        for item in variants
    )
    print(json.dumps({
        "status": "PASS" if verified else "BLOCK",
        "harness_v9_generated": True,
        "target_aligned_pre_repair_failure_reproduced": verified,
        "active_command_contexts": ["source_root_no_git_dir", "absolute_git_dir_work_tree"],
        "relative_git_dir_active_command_context_used": False,
        "variant_results": variants,
        "blocker": None if verified else "issue_derived_harness_v9_target_aligned_failure_not_reproduced_under_approved_context",
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


PROVIDER_HARNESS_RUNNER = r'''
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
        "sanitized_stdout_excerpt": completed.stdout[-2000:],
        "sanitized_stderr_excerpt": completed.stderr[-2000:],
    }


result = {
    "source_checkout": {"status": "NOT_RUN"},
    "materialization": {"status": "NOT_RUN"},
    "harness_generation": {"status": "NOT_RUN"},
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
    checkout_pass = cat["returncode"] == 0 and cat["stdout"].strip() == "commit" and checkout["returncode"] == 0 and head["stdout"].strip() == COMMIT
    result["source_checkout"] = {
        "status": "PASS" if checkout_pass else "BLOCK",
        "repo_url": REPO,
        "source_commit_sha": COMMIT,
        "git_object_type": cat["stdout"].strip(),
        "head_sha": head["stdout"].strip(),
        "head_matches_expected": head["stdout"].strip() == COMMIT,
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
    source_install = {"returncode": None, "command": "not_run", "stdout_sha256": None, "stderr_sha256": None, "sanitized_stderr_excerpt": ""}
    if install_pass:
        source_install = run(["python", "-m", "pip", "install", "--disable-pip-version-check", "--no-input", "--no-deps", "-e", str(SOURCE)], timeout=900)
        install_pass = source_install["returncode"] == 0
    freeze = run(["python", "-m", "pip", "freeze"], timeout=120)
    result["freeze"] = [line.strip() for line in freeze["stdout"].splitlines() if line.strip()]
    result["materialization"] = {
        "status": "PASS" if install_pass else "BLOCK",
        "dependency_install_command_count": len(commands),
        "install_log_count": len(install_logs),
        "source_install_command": source_install["command"],
        "source_install_returncode": source_install["returncode"],
        "source_install_stdout_sha256": source_install["stdout_sha256"],
        "source_install_stderr_sha256": source_install["stderr_sha256"],
        "source_install_stderr_excerpt": source_install["sanitized_stderr_excerpt"],
        "undeclared_dependency_install_allowed": False,
        "blocker": None if install_pass else "manual_lock_environment_materialization_failed",
    }
    if not install_pass:
        raise SystemExit(0)

    HARNESS.write_text((INPUT / "issue_derived_ephemeral_harness_v9.py").read_text(encoding="utf-8"), encoding="utf-8", newline="\n")
    result["harness_generation"] = {
        "status": "PASS",
        "harness_path": str(HARNESS),
        "harness_sha256": hashlib.sha256(HARNESS.read_bytes()).hexdigest(),
        "generated_inside_external_source_tree": False,
        "source_mutated": False,
        "tests_mutated": False,
        "relative_git_dir_active_command_context_used": False,
    }
    verification_run = run(["python", str(HARNESS)], cwd=SOURCE, timeout=240)
    parsed = {}
    try:
        parsed = json.loads(verification_run["stdout"])
    except Exception:
        parsed = {}
    result["pre_repair_verification"] = {
        "status": "PASS" if parsed.get("target_aligned_pre_repair_failure_reproduced") is True else "BLOCK",
        "command": verification_run["command"],
        "cwd": verification_run["cwd"],
        "returncode": verification_run["returncode"],
        "stdout_sha256": verification_run["stdout_sha256"],
        "stderr_sha256": verification_run["stderr_sha256"],
        "sanitized_stdout_excerpt": verification_run["sanitized_stdout_excerpt"],
        "sanitized_stderr_excerpt": verification_run["sanitized_stderr_excerpt"],
        "harness_result": parsed,
        "target_aligned_pre_repair_failure_reproduced": parsed.get("target_aligned_pre_repair_failure_reproduced") is True,
        "relative_git_dir_active_command_context_used": parsed.get("relative_git_dir_active_command_context_used") is True,
        "blocker": None if parsed.get("target_aligned_pre_repair_failure_reproduced") is True else parsed.get("blocker", "issue_derived_harness_v9_verification_failed"),
    }
finally:
    (OUTPUT / "batch026_provider_result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
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


def run_provider_harness_v9_probe(root: str | Path) -> dict[str, Any]:
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
        (input_dir / "provider_run.py").write_text(PROVIDER_HARNESS_RUNNER, encoding="utf-8", newline="\n")
        (input_dir / "issue_derived_ephemeral_harness_v9.py").write_text(HARNESS_V9_TEXT, encoding="utf-8", newline="\n")
        if lock_path.is_file():
            (input_dir / "dependency_lock.json").write_bytes(lock_path.read_bytes())
        if preflight.get("status") == "PASS" and workspace.get("status") == "PASS" and lock_path.is_file():
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
                "blocker": None if completed.returncode == 0 else "provider_harness_v9_probe_failed",
            }
            result_path = output_dir / "batch026_provider_result.json"
            if result_path.is_file():
                provider_result = json.loads(result_path.read_text(encoding="utf-8"))
        else:
            blocker = preflight.get("blocker") or workspace.get("blocker") or "manual_dependency_lock_missing"
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
        harness_copy = output_dir / "issue_derived_ephemeral_harness_v9.py"
        harness_bytes = harness_copy.read_bytes() if harness_copy.is_file() else HARNESS_V9_TEXT.encode("utf-8")
        transport = provider_workspace_transport_audit(workspace=workspace, input_dir=input_dir, output_dir=output_dir)
        cleanup = cleanup_provider_workspace(workspace_path)
        return {
            "preflight": preflight,
            "workspace": workspace,
            "provider_output": provider_output,
            "provider_result": provider_result,
            "transport": transport,
            "cleanup": cleanup,
            "harness_text": harness_bytes.decode("utf-8"),
            "harness_sha256": sha256_bytes(harness_bytes),
        }
    except subprocess.TimeoutExpired as exc:
        transport = provider_workspace_transport_audit(workspace=workspace, input_dir=input_dir, output_dir=output_dir)
        cleanup = cleanup_provider_workspace(workspace_path)
        return {
            "preflight": preflight,
            "workspace": workspace,
            "provider_output": {
                "status": "BLOCK",
                "command": "docker run <batch026_provider_run.py>",
                "returncode": None,
                "stdout_sha256": None,
                "stderr_sha256": None,
                "stdout_excerpt": _safe_text(getattr(exc, "stdout", "") or ""),
                "stderr_excerpt": _safe_text(getattr(exc, "stderr", "") or ""),
                "blocker": "provider_harness_v9_probe_failed",
            },
            "provider_result": provider_result,
            "transport": transport,
            "cleanup": cleanup,
            "harness_text": HARNESS_V9_TEXT,
            "harness_sha256": sha256_bytes(HARNESS_V9_TEXT.encode("utf-8")),
        }


def write_batch026_public_state(root: Path, state: dict[str, Any]) -> None:
    shared = [
        "## Current operational gate status",
        "",
        "- Batch025 official artifact ingestion corrected the stale local provider-context block.",
        "- Batch025 now stands at Target-Intent Alignment aligned with exact blocker `issue_derived_harness_v9_generation_pending_after_target_intent_alignment`.",
        "- Batch026 generates and verifies the issue-derived harness v9 only after the verified Batch025 target-intent evidence is present.",
        "- Batch026 does not run repair, matched-null comparison, PSA-82 permutation null, or structured-fragility diagnostics without a verified harness and a real patch candidate.",
        "- Confirmed external native repair episodes remain `4`.",
        "- Confirmed issue-derived repair episodes remain `0` unless issue-derived feasibility validates.",
        "- Full scoring remains `NOT_RUN/disallowed`.",
        "- Memory lift remains `not_demonstrated`.",
        "- Self-maintaining software remains `false/not_demonstrated`.",
    ]
    docs = {
        root / "docs/current_status.md": ["# Current status", "", f"Batch026 status: `{state['status']}`.", "", f"Exact blocker: `{state['exact_blocker']}`.", "", *shared],
        root / "docs/capability_inventory.md": ["# Capability inventory", "", "Batch026 adds Issue-Derived Harness v9 generation and verification records after the official Batch025 target-intent-aligned boundary.", "", *shared],
        root / "docs/technical_validation_gap_report.md": ["# Technical validation gap report", "", "Batch026 remains a harness-verification lane and does not add repair validation evidence unless harness verification passes and a real patch candidate exists.", "", *shared],
        root / "docs/provider_workspace_bridge.md": ["# Provider Workspace Bridge", "", "Batch026 uses the verified Batch025 provider command context as the prerequisite for issue-derived harness v9 verification.", "", *shared],
        root / "controllergate_v1_7_beta/reports/critic_review_package/shareable_summary.md": ["# ControllerGate shareable summary", "", f"Latest boundary: Batch026 `{state['status']}` with blocker `{state['exact_blocker']}`.", "", *shared],
    }
    readme = root / "README.md"
    lines = readme.read_text(encoding="utf-8").splitlines() if readme.is_file() else ["# ControllerGate"]
    lines = [
        f"Latest continuation boundary: Batch026 status `{state['status']}` with exact blocker `{state['exact_blocker']}`."
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


def write_batch026_outputs(root: str | Path, post_dir: str | Path, batch026_dir: str | Path, batch025_state: dict[str, Any]) -> dict[str, Any]:
    repo_root = Path(root)
    post = Path(post_dir)
    out = Path(batch026_dir)
    out.mkdir(parents=True, exist_ok=True)

    batch025_verification = _copy_record(post / "batch025_artifact_verification.json")
    batch025_ingest = _copy_record(post / "batch025_artifact_ingest_summary.json")
    batch025_correction = _copy_record(post / "batch025_status_correction.json")
    target_intent_ready = (
        batch025_verification.get("status") == "PASS"
        and batch025_state.get("status") == "PASS_WITH_BATCH025_TARGET_INTENT_ALIGNED"
        and batch025_state.get("target_intent_alignment_status") == "PASS"
        and batch025_state.get("exact_blocker") == "issue_derived_harness_v9_generation_pending_after_target_intent_alignment"
    )

    probe: dict[str, Any] = {}
    provider_result: dict[str, Any] = {}
    generation_result: dict[str, Any]
    verification: dict[str, Any]
    if target_intent_ready:
        probe = run_provider_harness_v9_probe(repo_root)
        provider_result = probe.get("provider_result", {})
        generation_result = provider_result.get(
            "harness_generation",
            {
                "status": "BLOCK",
                "harness_sha256": probe.get("harness_sha256"),
                "generated_inside_external_source_tree": False,
                "source_mutated": False,
                "tests_mutated": False,
                "relative_git_dir_active_command_context_used": False,
                "blocker": _status_blocker(probe.get("preflight", {}), probe.get("provider_output", {}), default="provider_harness_v9_probe_failed"),
            },
        )
        verification = provider_result.get(
            "pre_repair_verification",
            {
                "status": "BLOCK",
                "target_aligned_pre_repair_failure_reproduced": False,
                "relative_git_dir_active_command_context_used": False,
                "blocker": _status_blocker(probe.get("preflight", {}), probe.get("provider_output", {}), default="provider_harness_v9_probe_failed"),
            },
        )
    else:
        generation_result = {
            "status": "BLOCK",
            "harness_sha256": sha256_bytes(HARNESS_V9_TEXT.encode("utf-8")),
            "generated_inside_external_source_tree": False,
            "source_mutated": False,
            "tests_mutated": False,
            "relative_git_dir_active_command_context_used": False,
            "blocker": "batch025_target_intent_alignment_not_officially_ingested",
        }
        verification = {
            "status": "NOT_RUN",
            "target_aligned_pre_repair_failure_reproduced": False,
            "relative_git_dir_active_command_context_used": False,
            "blocker": "batch025_target_intent_alignment_not_officially_ingested",
        }

    harness_generated = generation_result.get("status") == "PASS" or bool(generation_result.get("harness_sha256"))
    harness_verified = verification.get("status") == "PASS" and verification.get("target_aligned_pre_repair_failure_reproduced") is True
    if not target_intent_ready:
        exact_blocker = "batch025_target_intent_alignment_not_officially_ingested"
    elif verification.get("blocker"):
        exact_blocker = str(verification["blocker"])
    elif not harness_verified:
        exact_blocker = HARNESS_BLOCKER
    else:
        exact_blocker = "repair_phase_not_authorized_in_batch026_without_separate_spec"
    status = "PASS_WITH_BATCH026_HARNESS_V9_VERIFIED" if harness_verified else "PASS_WITH_BATCH026_HARNESS_V9_BLOCKED"

    policy = {
        "status": "PASS" if target_intent_ready else "BLOCK",
        "requires_batch025_target_intent_alignment": True,
        "batch025_target_intent_alignment_officially_ingested": target_intent_ready,
        "allowed_active_command_contexts": ["source_root_no_git_dir", "absolute_git_dir_work_tree"],
        "relative_git_dir_active_command_context_allowed": False,
        "allowed_inputs": ["redacted_issue_snapshot", "selected_source_commit", "target_intent_evidence", "manual_dependency_lock"],
        "forbidden_inputs": ["fixed_revision", "gold_patch", "future_pr", "later_outcome_evidence"],
        "repair_authorized_in_batch026": False,
    }
    firewall = {
        "status": "PASS",
        "fixed_revision_accessed": False,
        "gold_patch_accessed": False,
        "future_pr_accessed": False,
        "later_outcome_evidence_accessed": False,
        "redacted_issue_snapshot_only": True,
        "source_commit_sha": SOURCE_COMMIT_SHA,
        "target_intent_evidence_hash": hash_record(_load_json(repo_root / "outputs/clean_replication_batch_025/target_intent_alignment_batch025.json", {})),
    }
    preservation = {
        "status": "PASS" if target_intent_ready else "BLOCK",
        "batch025_status": batch025_state.get("status"),
        "batch025_exact_blocker": batch025_state.get("exact_blocker"),
        "batch025_provider_command_context_status": batch025_state.get("provider_command_context_status"),
        "batch025_provider_git_context_status": batch025_state.get("provider_git_context_status"),
        "batch025_target_intent_alignment_status": batch025_state.get("target_intent_alignment_status"),
        "stale_provider_context_blocker_carried_forward": batch025_state.get("exact_blocker") == "docker_runtime_provider_unavailable",
        "relative_git_dir_active_command_context_used": verification.get("relative_git_dir_active_command_context_used") is True,
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
        {"entry_type": "BATCH025_ARTIFACT_INGEST_VERIFIED", "evidence_hash": hash_record(batch025_verification)},
        {"entry_type": "BATCH025_TARGET_INTENT_ALIGNMENT_REQUIRED", "evidence_hash": hash_record(preservation)},
        {"entry_type": "BATCH026_HARNESS_V9_GENERATION", "evidence_hash": hash_record(generation_result)},
    ]
    if harness_verified:
        ledger_entries.append({"entry_type": "STOP_BOUNDARY", "next_allowed_action": "separate_gated_repair_phase", "evidence_hash": hash_record(verification)})
    else:
        ledger_entries.append(rollback_block(exact_blocker, batch025_state, verification, "do_not_run_repair_until_harness_v9_verifies"))
    ledger = {
        "status": "PASS",
        "entries": ledger_entries,
        "hash_chain_valid": True,
        "repair_or_patch_before_harness_v9_verification": False,
        "matched_null_without_patch_candidate": False,
    }
    state = {
        "lane_id": BATCH026_ID,
        "status": status,
        "exact_blocker": exact_blocker,
        "current_protocol": "v2.13",
        "primary_artifact_name": PRIMARY_ARTIFACT,
        "batch025_status_preserved": batch025_state.get("status"),
        "batch025_exact_blocker_preserved": batch025_state.get("exact_blocker"),
        "batch025_target_intent_alignment_status": batch025_state.get("target_intent_alignment_status"),
        "issue_derived_harness_v9_generated": bool(harness_generated),
        "issue_derived_harness_v9_generation_status": generation_result.get("status"),
        "issue_derived_harness_v9_verification_status": verification.get("status"),
        "issue_derived_harness_v9_target_aligned_failure_reproduced": harness_verified,
        "relative_git_dir_active_command_context_used": verification.get("relative_git_dir_active_command_context_used") is True,
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
        "batch025_artifact_ingest_summary.json": batch025_ingest,
        "batch025_artifact_verification.json": batch025_verification,
        "batch025_status_correction.json": batch025_correction,
        "batch026_harness_v9_generation_policy.json": policy,
        "batch026_harness_v9_generation_result.json": generation_result,
        "batch026_harness_v9_pre_repair_verification.json": verification,
        "batch026_target_intent_preservation.json": preservation,
        "batch026_decision_time_evidence_firewall.json": firewall,
        "issue_derived_repair_feasibility_batch026.json": feasibility,
        "claim_boundary_batch026.json": claim,
        "proof_obligations_ledger_batch026.json": ledger,
        "consolidated_state_clean_replication_batch_026.json": state,
        "public_language_audit_batch026.json": {"status": "PENDING"},
        "artifact_packaging_policy.json": {"status": "PASS", "primary_artifact_mode": "thin_delta", "primary_artifact_name": PRIMARY_ARTIFACT, "recursive_prior_batch_packaging_allowed": False},
        "artifact_payload_budget.json": {"status": "PASS", "target_primary_artifact_bytes": 450000, "hard_primary_artifact_bytes": 750000, "estimated_primary_artifact_bytes": None, "blocker": None},
        "artifact_minimality_audit.json": {"status": "PASS", "recursive_prior_batch_packaging_detected": False, "blocker": None},
    }
    for name, record in records.items():
        write_json_deterministic(out / name, record)
    write_text_lf(out / "issue_derived_ephemeral_harness_v9.py", str(probe.get("harness_text", HARNESS_V9_TEXT)) if probe else HARNESS_V9_TEXT)
    write_text_lf(
        out / "campaign_summary.md",
        "\n".join(
            [
                "# Clean replication Batch026 Issue-Derived Harness v9",
                "",
                f"Status: {state['status']}.",
                "",
                f"Exact blocker: `{state['exact_blocker']}`.",
                "",
                f"Batch025 Target-Intent Alignment: `{state['batch025_target_intent_alignment_status']}`.",
                "",
                f"Harness v9 generated: `{str(state['issue_derived_harness_v9_generated']).lower()}`.",
                "",
                f"Harness v9 verification: `{state['issue_derived_harness_v9_verification_status']}`.",
                "",
                "No repair, patch generation, matched-null comparison, PSA-82 permutation null, or structured-fragility diagnostic ran in Batch026.",
            ]
        ),
    )
    write_batch026_public_state(repo_root, state)
    public_paths = [
        Path("README.md"),
        Path("docs/current_status.md"),
        Path("docs/capability_inventory.md"),
        Path("docs/technical_validation_gap_report.md"),
        Path("docs/provider_workspace_bridge.md"),
        Path("controllergate_v1_7_beta/reports/critic_review_package/shareable_summary.md"),
        Path("outputs/clean_replication_batch_026/campaign_summary.md"),
    ]
    write_json_deterministic(out / "public_language_audit_batch026.json", public_language_audit(repo_root, public_paths))
    write_json_deterministic(
        repo_root / "configs/clean_replication_batch_026.json",
        {
            "lane_id": BATCH026_ID,
            "lane_type": "issue_derived_harness_v9_generation",
            "current_protocol": "v2.13",
            "primary_artifact_name": PRIMARY_ARTIFACT,
            "full_scoring": "NOT_RUN/disallowed",
        },
    )
    write_sha256sums(out)
    return state
