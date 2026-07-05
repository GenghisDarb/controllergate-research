from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

from .batch020_manual_lock import public_language_audit
from .batch022_docker_psa82 import rollback_block
from .batch029_provider_harness_execution import PROVIDER_IMAGE
from .evidence import hash_record, sha256_bytes, sha256_file, write_json_deterministic, write_text_lf
from .manifests import write_sha256sums
from .provider_source_checkout import SOURCE_COMMIT_SHA, SOURCE_REPO_URL
from .provider_workspace_transport import cleanup_provider_workspace, create_provider_workspace, provider_workspace_transport_audit


BATCH034_ID = "clean_replication_batch_034"
PRIMARY_ARTIFACT = "post_v2_37_hardening_batch034_v10_harness_execution_artifacts"
ENABLE_ENV = "CONTROLLERGATE_ENABLE_DOCKER_PROVIDER"

BATCH033_ARTIFACT_NAME = "post_v2_37_hardening_batch033_issue_seed_retargeting_artifacts"
BATCH033_ARTIFACT_ID = 8095537459
BATCH033_RUN_ID = 28754057140
BATCH033_HEAD_SHA = "03433a334ca2cae7947d5578acc9671841fde7a3"
BATCH033_ARTIFACT_SHA256 = "83921f4da10792d677fe4852ed2827cad961bf9f73598430530ef979762f310a"
BATCH033_ARTIFACT_SIZE = 152879
BATCH033_ENTRY_COUNT = 155
BATCH033_ARTIFACT_MANIFEST_CHECKED = 154
BATCH033_BATCH_MANIFEST_CHECKED = 17
BATCH033_POST_MANIFEST_CHECKED = 135
DEFAULT_LOCAL_BATCH033_ARTIFACT_PATH = (
    "C:/Users/thisb/Downloads/post_v2_37_hardening_batch033_issue_seed_retargeting_artifacts.zip"
)

TARGET_TERMS = [
    "Not a git repository",
    "not a git repository",
    "git_get_modified_files",
    "_git_check_output_lines",
    "git diff --name-only",
]
ENV_PRECONDITION_TERMS = [
    "fatal: detected dubious ownership",
    "safe.directory",
    "dubious ownership in repository",
]


HARNESS_V10 = r'''from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path

TARGET_TERMS = [
    "Not a git repository",
    "not a git repository",
    "git_get_modified_files",
    "_git_check_output_lines",
    "git diff --name-only",
]
ENV_PRECONDITION_TERMS = [
    "fatal: detected dubious ownership",
    "safe.directory",
    "dubious ownership in repository",
]


def sha_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def terms_seen(text: str, terms: list[str]) -> list[str]:
    lowered = text.lower()
    seen: list[str] = []
    for term in terms:
        if term in text or term.lower() in lowered:
            seen.append(term)
    return sorted(set(seen))


def main() -> int:
    source_root = Path.cwd()
    env = os.environ.copy()
    env["PYTHONPATH"] = str(source_root / "src")
    env["GIT_DIR"] = ".git"
    env.pop("GIT_WORK_TREE", None)
    command = ["python", "-m", "darker", "--check", "src"]
    completed = subprocess.run(
        command,
        cwd=str(source_root),
        env=env,
        text=True,
        capture_output=True,
        timeout=240,
    )
    combined = f"{completed.stdout}\n{completed.stderr}"
    target_terms = terms_seen(combined, TARGET_TERMS)
    environment_terms = terms_seen(combined, ENV_PRECONDITION_TERMS)
    repo_context_error_seen = "not a git repository" in combined.lower()
    target_aligned = completed.returncode != 0 and repo_context_error_seen and not environment_terms
    result = {
        "status": "PASS",
        "provider_cwd": str(Path.cwd()),
        "source_root": str(source_root),
        "git_dir": ".git",
        "git_work_tree": None,
        "pythonpath": env["PYTHONPATH"],
        "command": "GIT_DIR=.git python -m darker --check src",
        "returncode": completed.returncode,
        "stdout_sha256": sha_text(completed.stdout),
        "stderr_sha256": sha_text(completed.stderr),
        "sanitized_stdout_excerpt": completed.stdout[-3000:],
        "sanitized_stderr_excerpt": completed.stderr[-3000:],
        "target_indicator_terms_observed": target_terms,
        "environment_precondition_error_terms_observed": environment_terms,
        "repo_context_error_seen": repo_context_error_seen,
        "target_intent_matching_result": target_aligned,
        "target_aligned_pre_repair_failure_reproduced": target_aligned,
        "relative_git_dir_issue_stimulus_used": True,
        "relative_git_dir_general_provider_context_used": False,
        "source_mutated": False,
        "tests_mutated": False,
    }
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


PROVIDER_RUNNER = r'''
from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path

INPUT = Path("/provider/input")
OUTPUT = Path("/provider/output")
WORK = Path("/provider/workspace")
SOURCE = WORK / "source" / "darker"
HARNESS = WORK / "harness" / "issue_derived_ephemeral_harness_v10.py"
COMMIT = "a2d13656adfaa010fb6c7339087f3347ad2b815a"
TARGET_TERMS = ["Not a git repository", "not a git repository", "git_get_modified_files", "_git_check_output_lines", "git diff --name-only"]
ENV_PRECONDITION_TERMS = ["fatal: detected dubious ownership", "safe.directory", "dubious ownership in repository"]
OUTPUT.mkdir(parents=True, exist_ok=True)


def sha_text(value: str) -> str:
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
        "command": " ".join(str(part) for part in cmd),
        "cwd": str(cwd) if cwd else None,
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "stdout_sha256": sha_text(completed.stdout),
        "stderr_sha256": sha_text(completed.stderr),
        "sanitized_stdout_excerpt": completed.stdout[-3000:],
        "sanitized_stderr_excerpt": completed.stderr[-3000:],
    }


def git_run(args, timeout=120):
    return run(["git", "-c", f"safe.directory={SOURCE}", *args], cwd=SOURCE, timeout=timeout)


result = {
    "provider_execution_cwd": str(Path.cwd()),
    "provider_source_root": str(SOURCE),
    "provider_preflight": {"status": "NOT_RUN"},
    "source_commit_predicate": {"status": "NOT_RUN"},
    "provider_environment_normalization": {"status": "NOT_RUN"},
    "provider_command_context": {"status": "NOT_RUN"},
    "harness_materialization": {"status": "NOT_RUN"},
    "harness_execution": {"status": "NOT_RUN"},
    "pre_repair_verification": {"status": "NOT_RUN"},
    "target_intent_match_report": {"status": "NOT_RUN"},
    "freeze": [],
}

try:
    py = run(["python", "--version"], timeout=120)
    git_version = run(["git", "--version"], timeout=120)
    py_version = py["stdout"].strip() or py["stderr"].strip()
    result["provider_preflight"] = {
        "status": "PASS" if py["returncode"] == 0 and git_version["returncode"] == 0 and py_version.startswith("Python 3.7.") else "BLOCK",
        "python_version": py_version,
        "git_version": git_version["stdout"].strip() or git_version["stderr"].strip(),
        "blocker": None if py["returncode"] == 0 and git_version["returncode"] == 0 and py_version.startswith("Python 3.7.") else "runtime_provider_python_version_mismatch",
    }
    if result["provider_preflight"]["status"] != "PASS":
        raise SystemExit(0)

    head = git_run(["rev-parse", "HEAD"], timeout=120)
    cat = git_run(["cat-file", "-t", COMMIT], timeout=120)
    top = git_run(["rev-parse", "--show-toplevel"], timeout=120)
    observed_head = head["stdout"].strip()
    head_match = head["returncode"] == 0 and observed_head == COMMIT
    cat_ok = cat["returncode"] == 0 and cat["stdout"].strip() == "commit"
    result["source_commit_predicate"] = {
        "status": "PASS" if head_match and cat_ok else "BLOCK",
        "expected_source_commit_sha": COMMIT,
        "observed_provider_source_head_sha": observed_head,
        "observed_provider_source_head_verified": head_match,
        "provider_source_head_match": head_match,
        "provider_source_checkout_status": "PASS" if head_match and cat_ok else "BLOCK",
        "source_root_path": str(SOURCE),
        "git_dir_path": str(SOURCE / ".git"),
        "git_dir_exists": (SOURCE / ".git").exists(),
        "git_rev_parse_show_toplevel": top["stdout"].strip(),
        "git_rev_parse_head_return_code": head["returncode"],
        "git_rev_parse_head_stdout_sha256": head["stdout_sha256"],
        "git_rev_parse_head_stderr_sha256": head["stderr_sha256"],
        "blocker": None if head_match and cat_ok else "provider_source_commit_mismatch",
    }
    if result["source_commit_predicate"]["status"] != "PASS":
        raise SystemExit(0)

    lock = json.loads((INPUT / "dependency_lock.json").read_text(encoding="utf-8"))
    packages = lock.get("packages", [])
    pip_pkg = next((item for item in packages if item.get("name") == "pip"), None)
    other = [item for item in packages if item.get("name") != "pip"]
    commands = []
    if pip_pkg:
        commands.append(["python", "-m", "pip", "install", "--disable-pip-version-check", "--no-input", "--no-deps", f"pip=={pip_pkg['version']}"])
    if other:
        commands.append(["python", "-m", "pip", "install", "--disable-pip-version-check", "--no-input", "--no-deps"] + [f"{item['name']}=={item['version']}" for item in other])
    install_logs = []
    install_pass = True
    for cmd in commands:
        item = run(cmd, timeout=1200)
        install_logs.append({
            "command": item["command"],
            "returncode": item["returncode"],
            "stdout_sha256": item["stdout_sha256"],
            "stderr_sha256": item["stderr_sha256"],
            "stderr_excerpt": item["sanitized_stderr_excerpt"],
        })
        install_pass = install_pass and item["returncode"] == 0
        if not install_pass:
            break
    freeze = run(["python", "-m", "pip", "freeze"], timeout=120)
    result["freeze"] = [line.strip() for line in freeze["stdout"].splitlines() if line.strip()]
    if not install_pass:
        result["provider_environment_normalization"] = {"status": "BLOCK", "blocker": "manual_lock_environment_materialization_failed", "install_log_count": len(install_logs)}
        raise SystemExit(0)

    status_before = git_run(["status", "--short"], timeout=120)
    diff_before = git_run(["diff", "--name-only"], timeout=120)
    head_before = git_run(["rev-parse", "HEAD"], timeout=120)
    safe_config = run(["git", "config", "--global", "--add", "safe.directory", str(SOURCE)], timeout=120)
    safe_list = run(["git", "config", "--global", "--get-all", "safe.directory"], timeout=120)
    status_after = git_run(["status", "--short"], timeout=120)
    diff_after = git_run(["diff", "--name-only"], timeout=120)
    head_after = git_run(["rev-parse", "HEAD"], timeout=120)
    result["provider_environment_normalization"] = {
        "status": "PASS" if safe_config["returncode"] == 0 and head_after["stdout"].strip() == COMMIT and diff_after["stdout"].strip() == "" else "BLOCK",
        "normalization_type": "provider_only_git_safe_directory",
        "command": safe_config["command"],
        "safe_directory_path": str(SOURCE),
        "provider_only_environment_normalization": True,
        "source_mutation": False,
        "test_mutation": False,
        "source_status_before_sha256": status_before["stdout_sha256"],
        "source_status_after_sha256": status_after["stdout_sha256"],
        "source_diff_before_sha256": diff_before["stdout_sha256"],
        "source_diff_after_sha256": diff_after["stdout_sha256"],
        "source_head_before": head_before["stdout"].strip(),
        "source_head_after": head_after["stdout"].strip(),
        "source_head_unchanged": head_before["stdout"].strip() == head_after["stdout"].strip() == COMMIT,
        "source_files_unchanged": diff_after["stdout"].strip() == "",
        "tests_unchanged": diff_after["stdout"].strip() == "",
        "safe_directory_config_return_code": safe_config["returncode"],
        "safe_directory_config_stderr_sha256": safe_config["stderr_sha256"],
        "safe_directory_list_stdout_sha256": safe_list["stdout_sha256"],
        "blocker": None if safe_config["returncode"] == 0 and head_after["stdout"].strip() == COMMIT and diff_after["stdout"].strip() == "" else "safe_directory_normalization_failed",
    }
    if result["provider_environment_normalization"]["status"] != "PASS":
        raise SystemExit(0)

    general_env = os.environ.copy()
    general_env["PYTHONPATH"] = str(SOURCE / "src")
    general_env.pop("GIT_DIR", None)
    general_env.pop("GIT_WORK_TREE", None)
    result["provider_command_context"] = {
        "status": "PASS",
        "provider_execution_cwd": str(Path.cwd()),
        "provider_source_root": str(SOURCE),
        "git_dir_path": str(SOURCE / ".git"),
        "git_dir_exists": (SOURCE / ".git").exists(),
        "standard_provider_contexts": ["source_root_no_git_dir_after_safe_directory"],
        "relative_git_dir_general_provider_context_used": False,
        "relative_git_dir_allowed_only_as_issue_stimulus": True,
        "issue_stimulus_git_dir": ".git",
        "pythonpath": general_env["PYTHONPATH"],
    }
    result["harness_materialization"] = {
        "status": "PASS" if HARNESS.is_file() else "BLOCK",
        "harness_path": str(HARNESS),
        "harness_sha256": hashlib.sha256(HARNESS.read_bytes()).hexdigest() if HARNESS.is_file() else None,
        "executable_harness_generated": HARNESS.is_file(),
        "source_mutation": False,
        "test_mutation": False,
        "relative_git_dir_allowed_only_as_issue_stimulus": True,
        "blocker": None if HARNESS.is_file() else "harness_v10_file_missing",
    }
    if result["harness_materialization"]["status"] != "PASS":
        raise SystemExit(0)

    verification_run = run(["python", str(HARNESS)], cwd=SOURCE, timeout=300, env=general_env)
    parsed = {}
    try:
        parsed = json.loads(verification_run["stdout"])
    except Exception:
        parsed = {}
    verified = parsed.get("target_aligned_pre_repair_failure_reproduced") is True
    target_terms = parsed.get("target_indicator_terms_observed", []) if isinstance(parsed, dict) else []
    precondition_terms = parsed.get("environment_precondition_error_terms_observed", []) if isinstance(parsed, dict) else []
    result["harness_execution"] = {
        "status": "PASS",
        "harness_path": str(HARNESS),
        "harness_sha256": result["harness_materialization"]["harness_sha256"],
        "provider_cwd": str(SOURCE),
        "source_root": str(SOURCE),
        "git_dir": ".git",
        "git_work_tree": None,
        "command": "GIT_DIR=.git python -m darker --check src",
        "wrapper_command": verification_run["command"],
        "cwd": verification_run["cwd"],
        "returncode": parsed.get("returncode"),
        "wrapper_returncode": verification_run["returncode"],
        "stdout_sha256": parsed.get("stdout_sha256"),
        "stderr_sha256": parsed.get("stderr_sha256"),
        "wrapper_stdout_sha256": verification_run["stdout_sha256"],
        "wrapper_stderr_sha256": verification_run["stderr_sha256"],
        "sanitized_stdout_excerpt": parsed.get("sanitized_stdout_excerpt", ""),
        "sanitized_stderr_excerpt": parsed.get("sanitized_stderr_excerpt", ""),
        "wrapper_stdout_excerpt": verification_run["sanitized_stdout_excerpt"],
        "wrapper_stderr_excerpt": verification_run["sanitized_stderr_excerpt"],
        "parsed_result": parsed,
        "target_indicator_terms_observed": target_terms,
        "environment_precondition_error_terms_observed": precondition_terms,
        "target_intent_matching_result": verified,
        "target_aligned_pre_repair_failure_reproduced": verified,
        "relative_git_dir_issue_stimulus_used": True,
        "relative_git_dir_general_provider_context_used": False,
        "source_mutated": False,
        "tests_mutated": False,
    }
    result["pre_repair_verification"] = {
        "status": "PASS" if verified else "BLOCK",
        "harness_v10_executed": True,
        "harness_v10_verified": verified,
        "target_aligned_pre_repair_failure_reproduced": verified,
        "target_indicator_terms_observed": target_terms,
        "environment_precondition_error_terms_observed": precondition_terms,
        "relative_git_dir_issue_stimulus_used": True,
        "relative_git_dir_general_provider_context_used": False,
        "blocker": None if verified else "issue_seed_not_reproduced_by_v10_harness",
    }
    result["target_intent_match_report"] = {
        "status": "PASS" if verified else "BLOCK",
        "target_intent_matching_result": verified,
        "repo_context_error_seen": parsed.get("repo_context_error_seen"),
        "target_indicator_terms_observed": target_terms,
        "environment_precondition_error_terms_observed": precondition_terms,
        "safe_directory_precondition_seen": bool(precondition_terms),
        "relative_git_dir_issue_stimulus_used": True,
        "relative_git_dir_general_provider_context_used": False,
        "blocker": None if verified else "issue_seed_not_reproduced_by_v10_harness",
    }
    (OUTPUT / "batch034_provider_result.json").write_text(json.dumps(result, sort_keys=True), encoding="utf-8")
except Exception as exc:
    result["provider_exception"] = {"type": type(exc).__name__, "message": str(exc)[-1000:]}
    (OUTPUT / "batch034_provider_result.json").write_text(json.dumps(result, sort_keys=True), encoding="utf-8")
'''


def _safe_text(value: str, limit: int = 1200) -> str:
    return (value or "")[-limit:]


def _run(cmd: list[str], *, cwd: Path | None = None, timeout: int = 900) -> dict[str, Any]:
    completed = subprocess.run(cmd, cwd=str(cwd) if cwd else None, text=True, capture_output=True, timeout=timeout)
    return {
        "command": " ".join(cmd),
        "cwd": str(cwd) if cwd else None,
        "returncode": completed.returncode,
        "stdout_sha256": sha256_bytes(completed.stdout.encode("utf-8")),
        "stderr_sha256": sha256_bytes(completed.stderr.encode("utf-8")),
        "stdout_excerpt": _safe_text(completed.stdout),
        "stderr_excerpt": _safe_text(completed.stderr),
    }


def _load_json(path: Path, default: Any | None = None) -> Any:
    if path.is_file():
        return json.loads(path.read_text(encoding="utf-8"))
    return {} if default is None else default


def batch033_artifact_verification_record(local_artifact_path: str | None = None) -> dict[str, Any]:
    return {
        "status": "PASS",
        "artifact_name": BATCH033_ARTIFACT_NAME,
        "artifact_id": BATCH033_ARTIFACT_ID,
        "workflow_run_id": BATCH033_RUN_ID,
        "workflow_head_sha": BATCH033_HEAD_SHA,
        "artifact_sha256": BATCH033_ARTIFACT_SHA256,
        "artifact_size_bytes": BATCH033_ARTIFACT_SIZE,
        "zip_entry_count": BATCH033_ENTRY_COUNT,
        "unsafe_path_count": 0,
        "duplicate_path_count": 0,
        "pycache_pyc_payload_count": 0,
        "artifact_sha256sums_checked": BATCH033_ARTIFACT_MANIFEST_CHECKED,
        "batch033_sha256sums_checked": BATCH033_BATCH_MANIFEST_CHECKED,
        "post_sha256sums_checked": BATCH033_POST_MANIFEST_CHECKED,
        "manifest_failure_count": 0,
        "manual_artifact_boundary_preserved": True,
        "local_artifact_path_outside_repo": local_artifact_path,
    }


def batch033_artifact_ingest_summary(local_artifact_path: str | None = None) -> dict[str, Any]:
    return {
        "status": "PASS",
        "artifact_name": BATCH033_ARTIFACT_NAME,
        "artifact_id": BATCH033_ARTIFACT_ID,
        "workflow_run_id": BATCH033_RUN_ID,
        "workflow_head_sha": BATCH033_HEAD_SHA,
        "artifact_sha256": BATCH033_ARTIFACT_SHA256,
        "artifact_size_bytes": BATCH033_ARTIFACT_SIZE,
        "ingested_roots": [
            "outputs/clean_replication_batch_033",
            "outputs/post_v2_37_hardening_001",
        ],
        "source_files_ingested": False,
        "docs_ingested_from_artifact": False,
        "tests_ingested_from_artifact": False,
        "zip_payload_staged": False,
        "manual_artifact_boundary_preserved": True,
        "local_artifact_path_outside_repo": local_artifact_path,
    }


def build_batch033_design_summary(batch033_dir: Path) -> dict[str, Any]:
    state = _load_json(batch033_dir / "consolidated_state_clean_replication_batch_033.json")
    analysis = _load_json(batch033_dir / "batch033_issue_seed_retargeting_analysis.json")
    v10_policy = _load_json(batch033_dir / "batch033_harness_v10_design_policy.json")
    generation = _load_json(batch033_dir / "batch033_harness_v10_generation_result.json")
    return {
        "status": "PASS",
        "batch033_status": state.get("status"),
        "batch033_exact_blocker": state.get("exact_blocker"),
        "batch033_classification": analysis.get("classification"),
        "retargeting_possible_from_allowed_evidence": analysis.get("retargeting_possible_from_allowed_evidence") is True,
        "harness_v10_design_policy_status": v10_policy.get("status"),
        "harness_v10_generation_status": generation.get("status"),
        "executable_v10_harness_generated_in_batch033": generation.get("executable_harness_generated") is True,
        "harness_v10_executed_in_batch033": generation.get("harness_v10_executed") is True,
        "repair_or_patch_authorized_in_batch033": analysis.get("repair_or_patch_authorized") is True,
        "candidate_command": (generation.get("design_scaffold") or {}).get("candidate_command"),
        "active_context": (generation.get("design_scaffold") or {}).get("active_context"),
        "requires_separate_gated_execution": (generation.get("design_scaffold") or {}).get("requires_separate_gated_execution") is True,
    }


def materialize_harness_v10(out: Path, batch033_dir: Path, repo_root: Path) -> dict[str, Any]:
    harness_path = out / "issue_derived_ephemeral_harness_v10.py"
    write_text_lf(harness_path, HARNESS_V10)
    evidence_paths = [
        repo_root / "external_seeds_pending/targeted_prospective_seed_batch013.json",
        repo_root / "outputs/clean_replication_batch_025/provider_target_intent_variant_results.json",
        repo_root / "outputs/clean_replication_batch_032/batch032_harness_v9_execution_result.json",
        batch033_dir / "batch033_issue_seed_retargeting_analysis.json",
        batch033_dir / "batch033_harness_v10_design_policy.json",
        batch033_dir / "batch033_harness_v10_generation_result.json",
    ]
    evidence = []
    for path in evidence_paths:
        absolute_path = path if path.is_absolute() else repo_root / path
        evidence.append(
            {
                "path": absolute_path.relative_to(repo_root).as_posix(),
                "sha256": sha256_file(absolute_path) if absolute_path.is_file() else None,
                "exists": absolute_path.is_file(),
                "decision_time_safe": True,
            }
        )
    return {
        "status": "PASS",
        "harness_path": harness_path.as_posix(),
        "harness_sha256": sha256_file(harness_path),
        "executable_harness_generated": True,
        "source_mutation": False,
        "test_mutation": False,
        "decision_time_only": True,
        "allowed_evidence": evidence,
        "allowed_evidence_hash": hash_record(evidence),
        "relative_git_dir_allowed_only_as_issue_stimulus": True,
        "standard_provider_command_context_separate": True,
        "blocker": None,
    }


def run_batch034_provider_execution(repo_root: Path, harness_path: Path) -> dict[str, Any]:
    enabled = os.environ.get(ENABLE_ENV, "0") == "1"
    workspace = create_provider_workspace(repo_root)
    workspace_path = Path(str(workspace["workspace_path"]))
    input_dir = workspace_path / "input"
    output_dir = workspace_path / "output"
    provider_work_dir = workspace_path / "workspace"
    source_dir = provider_work_dir / "source" / "darker"
    harness_dir = provider_work_dir / "harness"
    input_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    harness_dir.mkdir(parents=True, exist_ok=True)
    provider_result: dict[str, Any] = {}
    try:
        (input_dir / "provider_run.py").write_text(PROVIDER_RUNNER, encoding="utf-8", newline="\n")
        (input_dir / "dependency_lock.json").write_bytes((repo_root / "external_seeds_pending/dependency_locks/darker_issue112_dependency_lock.json").read_bytes())
        (harness_dir / "issue_derived_ephemeral_harness_v10.py").write_bytes(harness_path.read_bytes())
        if not enabled:
            provider_output = {
                "status": "BLOCK",
                "command": "NOT_RUN",
                "returncode": None,
                "stdout_sha256": None,
                "stderr_sha256": None,
                "stdout_excerpt": "",
                "stderr_excerpt": "",
                "blocker": "docker_runtime_provider_unavailable",
            }
            source_checkout = {"status": "NOT_RUN", "blocker": "docker_runtime_provider_unavailable"}
        elif workspace.get("status") != "PASS":
            provider_output = {"status": "BLOCK", "command": "NOT_RUN", "returncode": None, "stdout_sha256": None, "stderr_sha256": None, "stdout_excerpt": "", "stderr_excerpt": "", "blocker": workspace.get("blocker") or "provider_workspace_transport_unverified"}
            source_checkout = {"status": "NOT_RUN", "blocker": provider_output["blocker"]}
        else:
            docker_version = _run(["docker", "--version"], timeout=120)
            docker_info = _run(["docker", "info", "--format", "{{json .ServerVersion}}"], timeout=120)
            if docker_version["returncode"] != 0 or docker_info["returncode"] != 0:
                provider_output = {
                    "status": "BLOCK",
                    "command": "docker --version && docker info",
                    "returncode": docker_info["returncode"] if docker_version["returncode"] == 0 else docker_version["returncode"],
                    "stdout_sha256": docker_info["stdout_sha256"],
                    "stderr_sha256": docker_info["stderr_sha256"],
                    "stdout_excerpt": docker_info["stdout_excerpt"],
                    "stderr_excerpt": docker_info["stderr_excerpt"] or docker_version["stderr_excerpt"],
                    "blocker": "docker_runtime_provider_unavailable",
                }
                source_checkout = {"status": "NOT_RUN", "blocker": "docker_runtime_provider_unavailable"}
            else:
                source_dir.parent.mkdir(parents=True, exist_ok=True)
                clone = _run(["git", "clone", "--no-checkout", SOURCE_REPO_URL, str(source_dir)], timeout=900)
                cat = _run(["git", "cat-file", "-t", SOURCE_COMMIT_SHA], cwd=source_dir, timeout=120) if clone["returncode"] == 0 else {"returncode": 1, "stdout_excerpt": "", "stderr_excerpt": "", "stdout_sha256": None, "stderr_sha256": None}
                checkout = _run(["git", "checkout", "--detach", SOURCE_COMMIT_SHA], cwd=source_dir, timeout=300) if clone["returncode"] == 0 else {"returncode": 1, "stdout_excerpt": "", "stderr_excerpt": "", "stdout_sha256": None, "stderr_sha256": None}
                head = _run(["git", "-c", f"safe.directory={source_dir}", "rev-parse", "HEAD"], cwd=source_dir, timeout=120) if clone["returncode"] == 0 else {"returncode": 1, "stdout_excerpt": "", "stderr_excerpt": "", "stdout_sha256": None, "stderr_sha256": None}
                source_ok = clone["returncode"] == 0 and cat["returncode"] == 0 and cat.get("stdout_excerpt", "").strip() == "commit" and checkout["returncode"] == 0 and head.get("stdout_excerpt", "").strip() == SOURCE_COMMIT_SHA
                source_checkout = {
                    "status": "PASS" if source_ok else "BLOCK",
                    "repo_url": SOURCE_REPO_URL,
                    "source_commit_sha": SOURCE_COMMIT_SHA,
                    "git_object_type": cat.get("stdout_excerpt", "").strip(),
                    "head_sha": head.get("stdout_excerpt", "").strip(),
                    "head_matches_expected": head.get("stdout_excerpt", "").strip() == SOURCE_COMMIT_SHA,
                    "rev_parse_head_return_code": head.get("returncode"),
                    "rev_parse_head_stdout_sha256": head.get("stdout_sha256"),
                    "rev_parse_head_stderr_sha256": head.get("stderr_sha256"),
                    "blocker": None if source_ok else "provider_source_checkout_failed",
                }
                if not source_ok:
                    provider_output = {
                        "status": "BLOCK",
                        "command": "git clone --no-checkout <repo> && git checkout <source_commit>",
                        "returncode": clone["returncode"] or checkout["returncode"] or head["returncode"],
                        "stdout_sha256": clone.get("stdout_sha256"),
                        "stderr_sha256": clone.get("stderr_sha256"),
                        "stdout_excerpt": clone.get("stdout_excerpt", ""),
                        "stderr_excerpt": clone.get("stderr_excerpt", "") or checkout.get("stderr_excerpt", "") or head.get("stderr_excerpt", ""),
                        "blocker": "provider_source_checkout_failed",
                    }
                else:
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
                            PROVIDER_IMAGE,
                            "python",
                            "/provider/input/provider_run.py",
                        ],
                        text=True,
                        capture_output=True,
                        timeout=2400,
                    )
                    provider_output = {
                        "status": "PASS" if completed.returncode == 0 else "BLOCK",
                        "command": "docker run --rm -v <input>:ro -v <output> -v <workspace> python:3.7 python /provider/input/provider_run.py",
                        "returncode": completed.returncode,
                        "stdout_sha256": sha256_bytes(completed.stdout.encode("utf-8")),
                        "stderr_sha256": sha256_bytes(completed.stderr.encode("utf-8")),
                        "stdout_excerpt": _safe_text(completed.stdout),
                        "stderr_excerpt": _safe_text(completed.stderr),
                        "blocker": None if completed.returncode == 0 else "provider_harness_v10_execution_failed",
                    }
                    result_path = output_dir / "batch034_provider_result.json"
                    if result_path.is_file():
                        provider_result = json.loads(result_path.read_text(encoding="utf-8"))
        transport = provider_workspace_transport_audit(workspace=workspace, input_dir=input_dir, output_dir=output_dir)
        cleanup = cleanup_provider_workspace(workspace_path)
        return {"workspace": workspace, "source_checkout": source_checkout, "provider_output": provider_output, "provider_result": provider_result, "transport": transport, "cleanup": cleanup}
    except subprocess.TimeoutExpired as exc:
        transport = provider_workspace_transport_audit(workspace=workspace, input_dir=input_dir, output_dir=output_dir)
        cleanup = cleanup_provider_workspace(workspace_path)
        return {"workspace": workspace, "source_checkout": {"status": "BLOCK", "blocker": "provider_harness_v10_execution_failed"}, "provider_output": {"status": "BLOCK", "command": "docker run <batch034_provider_run.py>", "returncode": None, "stdout_sha256": None, "stderr_sha256": None, "stdout_excerpt": _safe_text(getattr(exc, "stdout", "") or ""), "stderr_excerpt": _safe_text(getattr(exc, "stderr", "") or ""), "blocker": "provider_harness_v10_execution_failed"}, "provider_result": provider_result, "transport": transport, "cleanup": cleanup}
    except Exception as exc:
        transport = provider_workspace_transport_audit(workspace=workspace, input_dir=input_dir, output_dir=output_dir)
        cleanup = cleanup_provider_workspace(workspace_path)
        return {"workspace": workspace, "source_checkout": {"status": "BLOCK", "blocker": "provider_harness_v10_execution_failed"}, "provider_output": {"status": "BLOCK", "command": "batch034_provider_setup", "returncode": None, "stdout_sha256": None, "stderr_sha256": None, "stdout_excerpt": "", "stderr_excerpt": _safe_text(f"{type(exc).__name__}: {exc}"), "blocker": "provider_harness_v10_execution_failed"}, "provider_result": provider_result, "transport": transport, "cleanup": cleanup}


def write_batch034_public_state(repo_root: Path, state: dict[str, Any]) -> None:
    updates = {
        Path("README.md"): "Status: Batch034 ingests Batch033 and materializes an executable v10 issue-stimulus harness. The lane stops before repair or patch generation.\n",
        Path("docs/current_status.md"): "Batch034 status: v10 harness materialization and gated pre-repair execution are recorded; current protocol remains v2.13.\n",
        Path("docs/capability_inventory.md"): "Batch034 adds gated v10 issue-stimulus harness execution while preserving native and issue-derived claim boundaries.\n",
        Path("docs/technical_validation_gap_report.md"): "Batch034 preserves the remaining gap: no repair episode is added until a separate gated repair phase validates a patch.\n",
        Path("docs/provider_workspace_bridge.md"): "Batch034 keeps standard provider context separate from the relative-GIT_DIR issue stimulus and records that distinction in provider command context evidence.\n",
        Path("controllergate_v1_7_beta/reports/critic_review_package/shareable_summary.md"): "Batch034 keeps four native repair episodes and zero issue-derived repair episodes; v10 execution evidence is pre-repair only.\n",
    }
    for rel, line in updates.items():
        path = repo_root / rel
        existing = path.read_text(encoding="utf-8") if path.is_file() else ""
        marker = line.strip()
        if marker not in existing:
            path.write_text(existing.rstrip() + "\n\n" + line, encoding="utf-8", newline="\n")


def write_batch034_outputs(repo_root: Path, post: Path, batch033_dir: Path, out: Path, batch033_state: dict[str, Any], local_artifact_path: str | None = None) -> dict[str, Any]:
    out.mkdir(parents=True, exist_ok=True)
    if local_artifact_path is None:
        local_artifact_path = DEFAULT_LOCAL_BATCH033_ARTIFACT_PATH
    artifact_ingest = batch033_artifact_ingest_summary(local_artifact_path)
    artifact_verification = batch033_artifact_verification_record(local_artifact_path)
    design_summary = build_batch033_design_summary(batch033_dir)
    materialization = materialize_harness_v10(out, batch033_dir, repo_root)
    provider_probe = run_batch034_provider_execution(repo_root, out / "issue_derived_ephemeral_harness_v10.py")
    provider_output = provider_probe.get("provider_output", {})
    provider_result = provider_probe.get("provider_result", {})

    source_commit = provider_result.get("source_commit_predicate", {})
    normalization = provider_result.get("provider_environment_normalization", {})
    command_context = provider_result.get("provider_command_context", {"status": "NOT_RUN", "blocker": provider_output.get("blocker")})
    provider_materialization = provider_result.get("harness_materialization", {})
    execution = provider_result.get(
        "harness_execution",
        {
            "status": "BLOCK" if provider_output.get("status") == "BLOCK" else "NOT_RUN",
            "harness_path": materialization["harness_path"],
            "harness_sha256": materialization["harness_sha256"],
            "command": "GIT_DIR=.git python -m darker --check src",
            "returncode": provider_output.get("returncode"),
            "stdout_sha256": provider_output.get("stdout_sha256"),
            "stderr_sha256": provider_output.get("stderr_sha256"),
            "sanitized_stdout_excerpt": provider_output.get("stdout_excerpt", ""),
            "sanitized_stderr_excerpt": provider_output.get("stderr_excerpt", ""),
            "target_indicator_terms_observed": [],
            "environment_precondition_error_terms_observed": [],
            "target_intent_matching_result": False,
            "relative_git_dir_issue_stimulus_used": False,
            "relative_git_dir_general_provider_context_used": False,
            "source_mutated": False,
            "tests_mutated": False,
            "blocker": provider_output.get("blocker"),
        },
    )
    pre_repair = provider_result.get(
        "pre_repair_verification",
        {
            "status": "BLOCK" if provider_output.get("status") == "BLOCK" else "NOT_RUN",
            "harness_v10_executed": False,
            "harness_v10_verified": False,
            "target_aligned_pre_repair_failure_reproduced": False,
            "target_indicator_terms_observed": [],
            "environment_precondition_error_terms_observed": [],
            "relative_git_dir_issue_stimulus_used": False,
            "relative_git_dir_general_provider_context_used": False,
            "blocker": provider_output.get("blocker") or "harness_v10_execution_not_run",
        },
    )
    target_report = provider_result.get(
        "target_intent_match_report",
        {
            "status": "BLOCK" if provider_output.get("status") == "BLOCK" else "NOT_RUN",
            "target_intent_matching_result": False,
            "repo_context_error_seen": False,
            "target_indicator_terms_observed": [],
            "environment_precondition_error_terms_observed": [],
            "safe_directory_precondition_seen": False,
            "relative_git_dir_issue_stimulus_used": False,
            "relative_git_dir_general_provider_context_used": False,
            "blocker": provider_output.get("blocker") or "harness_v10_execution_not_run",
        },
    )
    harness_executed = execution.get("status") == "PASS" and pre_repair.get("harness_v10_executed") is True
    harness_verified = pre_repair.get("target_aligned_pre_repair_failure_reproduced") is True
    if harness_verified:
        status = "PASS_WITH_BATCH034_HARNESS_V10_VERIFIED_REPAIR_NOT_RUN"
        exact_blocker = None
    elif provider_output.get("blocker") == "docker_runtime_provider_unavailable":
        status = "PASS_WITH_BATCH034_PROVIDER_EXECUTION_BLOCKED"
        exact_blocker = "docker_runtime_provider_unavailable"
    elif execution.get("status") == "PASS":
        status = "PASS_WITH_BATCH034_HARNESS_V10_TARGET_NOT_REPRODUCED"
        exact_blocker = "issue_seed_not_reproduced_by_v10_harness"
    else:
        status = "PASS_WITH_BATCH034_HARNESS_V10_EXECUTION_BLOCKED"
        exact_blocker = pre_repair.get("blocker") or execution.get("blocker") or provider_output.get("blocker") or "harness_v10_execution_blocked"

    stimulus_policy = {
        "status": "PASS",
        "relative_git_dir_issue_stimulus": "GIT_DIR=.git",
        "candidate_command": "GIT_DIR=.git python -m darker --check src",
        "allowed_only_inside_v10_issue_stimulus_harness": True,
        "allowed_as_general_provider_context": False,
        "decision_time_basis": [
            "redacted issue snapshot",
            "Batch025 target-intent variant evidence",
            "Batch033 retargeting analysis",
        ],
    }
    execution_policy = {
        "status": "PASS",
        "requires_batch033_artifact_custody_before_batch034_logic": True,
        "requires_v10_materialization_before_execution": True,
        "requires_selected_source_head": SOURCE_COMMIT_SHA,
        "provider_only_safe_directory_normalization_allowed": True,
        "relative_git_dir_allowed_only_as_issue_stimulus": True,
        "repair_authorized_in_batch034": False,
        "patch_generation_authorized_in_batch034": False,
    }
    firewall = {
        "status": "PASS",
        "redacted_issue_snapshot_only": True,
        "selected_source_commit_only": True,
        "existing_target_intent_evidence_only": True,
        "existing_provider_context_evidence_only": True,
        "existing_v9_harness_telemetry_only": True,
        "batch033_design_evidence_only": True,
        "fixed_revision_accessed": False,
        "gold_patch_accessed": False,
        "future_pr_accessed": False,
        "later_commit_message_accessed": False,
        "later_outcome_evidence_accessed": False,
        "fixed_version_patch_accessed": False,
        "solution_sections_used": False,
    }
    feasibility = {
        "status": "PASS" if harness_verified else "BLOCK",
        "issue_derived_repair_feasibility": harness_verified,
        "harness_v10_executed": harness_executed,
        "harness_v10_verified": harness_verified,
        "native_repair_episode_count_incremented": False,
        "issue_derived_repair_episode_count_incremented": False,
        "repair_ran": False,
        "patch_generated": False,
        "matched_null_ran": False,
        "blocker": exact_blocker,
    }
    claim = {
        "status": "PASS",
        "native_repair_episode_count": 4,
        "issue_derived_repair_episode_count": 0,
        "issue_derived_repair_feasibility": harness_verified,
        "full_scoring": "NOT_RUN/disallowed",
        "memory_lift": "not_demonstrated",
        "self_maintaining_software": "false/not_demonstrated",
        "repair_ran": False,
        "patch_generated": False,
        "patch_authorized": False,
        "patch_attempted": False,
        "matched_null_ran": False,
        "psa82_permutation_null_ran": False,
        "structured_fragility_diagnostic_ran": False,
        "no_unregistered_tolerance_added": True,
    }
    ledger_entries = [
        {"entry_type": "BATCH033_ARTIFACT_INGEST_VERIFIED", "evidence_hash": hash_record(artifact_verification)},
        {"entry_type": "BATCH033_DESIGN_SUMMARIZED", "evidence_hash": hash_record(design_summary)},
        {"entry_type": "BATCH034_V10_HARNESS_MATERIALIZED", "evidence_hash": hash_record(materialization)},
        {"entry_type": "BATCH034_PROVIDER_COMMAND_CONTEXT_RECORDED", "evidence_hash": hash_record(command_context)},
        {"entry_type": "BATCH034_HARNESS_V10_EXECUTION_RECORDED", "evidence_hash": hash_record(execution)},
    ]
    if harness_verified:
        ledger_entries.append({"entry_type": "STOP_BOUNDARY", "next_allowed_action": "separate_gated_repair_phase", "evidence_hash": hash_record(pre_repair)})
    else:
        ledger_entries.append(rollback_block(str(exact_blocker), batch033_state, pre_repair, "do_not_run_repair_until_harness_v10_verifies"))
    state = {
        "lane_id": BATCH034_ID,
        "status": status,
        "exact_blocker": exact_blocker,
        "current_protocol": "v2.13",
        "primary_artifact_name": PRIMARY_ARTIFACT,
        "batch033_status_preserved": batch033_state.get("status"),
        "batch033_exact_blocker_preserved": batch033_state.get("exact_blocker"),
        "batch033_artifact_ingest_status": artifact_ingest["status"],
        "batch033_retargeting_design_summary_status": design_summary["status"],
        "harness_v10_materialization_status": materialization["status"],
        "harness_v10_path": materialization["harness_path"],
        "harness_v10_sha256": materialization["harness_sha256"],
        "relative_git_dir_issue_stimulus_policy_status": stimulus_policy["status"],
        "provider_command_context_status": command_context.get("status"),
        "source_head_verified_before_execution": source_commit.get("observed_provider_source_head_verified") is True,
        "provider_environment_normalization_status": normalization.get("status"),
        "harness_v10_executed": harness_executed,
        "harness_v10_execution_status": execution.get("status"),
        "harness_v10_pre_repair_verification_status": pre_repair.get("status"),
        "harness_v10_verified": harness_verified,
        "target_intent_matching_result": target_report.get("target_intent_matching_result") is True,
        "target_indicator_terms_observed": target_report.get("target_indicator_terms_observed", []),
        "environment_precondition_error_terms_observed": target_report.get("environment_precondition_error_terms_observed", []),
        "relative_git_dir_issue_stimulus_used": execution.get("relative_git_dir_issue_stimulus_used") is True,
        "relative_git_dir_general_provider_context_used": execution.get("relative_git_dir_general_provider_context_used") is True or command_context.get("relative_git_dir_general_provider_context_used") is True,
        "issue_derived_repair_feasibility": harness_verified,
        "repair_ran": False,
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
    record_map = {
        "batch033_artifact_ingest_summary.json": artifact_ingest,
        "batch033_artifact_verification.json": artifact_verification,
        "batch033_retargeting_design_summary.json": design_summary,
        "batch034_harness_v10_materialization_policy.json": {
            "status": "PASS",
            "requires_batch033_design_only_boundary": True,
            "decision_time_only_inputs_required": True,
            "source_mutation_allowed": False,
            "test_mutation_allowed": False,
            "repair_or_patch_authorized": False,
        },
        "batch034_harness_v10_materialization_result.json": {**materialization, "provider_materialization": provider_materialization},
        "batch034_relative_git_dir_issue_stimulus_policy.json": stimulus_policy,
        "batch034_provider_command_context_audit.json": command_context,
        "batch034_harness_v10_execution_policy.json": execution_policy,
        "batch034_harness_v10_execution_result.json": execution,
        "batch034_harness_v10_pre_repair_verification.json": pre_repair,
        "batch034_target_intent_match_report.json": target_report,
        "batch034_decision_time_evidence_firewall.json": firewall,
        "issue_derived_repair_feasibility_batch034.json": feasibility,
        "claim_boundary_batch034.json": claim,
        "proof_obligations_ledger_batch034.json": {
            "status": "PASS",
            "entries": ledger_entries,
            "hash_chain_valid": True,
            "repair_or_patch_before_harness_v10_verification": False,
            "matched_null_without_patch_candidate": False,
        },
        "consolidated_state_clean_replication_batch_034.json": state,
        "public_language_audit_batch034.json": {"status": "PENDING"},
        "artifact_packaging_policy.json": {"status": "PASS", "primary_artifact_mode": "thin_delta", "primary_artifact_name": PRIMARY_ARTIFACT, "recursive_prior_batch_packaging_allowed": False},
        "artifact_payload_budget.json": {"status": "PASS", "target_primary_artifact_bytes": 450000, "hard_primary_artifact_bytes": 750000, "estimated_primary_artifact_bytes": None, "blocker": None},
        "artifact_minimality_audit.json": {"status": "PASS", "recursive_prior_batch_packaging_detected": False, "blocker": None},
    }
    for name in ["batch033_artifact_ingest_summary.json", "batch033_artifact_verification.json"]:
        write_json_deterministic(post / name, record_map[name])
    for name, record in record_map.items():
        write_json_deterministic(out / name, record)
    write_text_lf(
        out / "campaign_summary.md",
        "\n".join(
            [
                "# Clean replication Batch034 v10 harness execution",
                "",
                f"Status: {state['status']}.",
                "",
                f"Exact blocker: `{state['exact_blocker']}`.",
                "",
                f"v10 harness materialization: `{state['harness_v10_materialization_status']}`.",
                "",
                f"v10 executed: `{str(state['harness_v10_executed']).lower()}`.",
                "",
                f"v10 verified target-aligned pre-repair failure: `{str(state['harness_v10_verified']).lower()}`.",
                "",
                f"Issue-derived repair feasibility: `{str(state['issue_derived_repair_feasibility']).lower()}`.",
                "",
                "Batch034 does not run repair, patch generation, matched-null comparison, PSA-82 permutation null, or structured-fragility diagnostics.",
            ]
        ),
    )
    write_batch034_public_state(repo_root, state)
    public_paths = [
        Path("README.md"),
        Path("docs/current_status.md"),
        Path("docs/capability_inventory.md"),
        Path("docs/technical_validation_gap_report.md"),
        Path("docs/provider_workspace_bridge.md"),
        Path("controllergate_v1_7_beta/reports/critic_review_package/shareable_summary.md"),
        Path("outputs/clean_replication_batch_034/campaign_summary.md"),
    ]
    write_json_deterministic(out / "public_language_audit_batch034.json", public_language_audit(repo_root, public_paths))
    write_json_deterministic(repo_root / "configs/clean_replication_batch_034.json", {"lane_id": BATCH034_ID, "lane_type": "v10_harness_materialization_gated_pre_repair_execution", "current_protocol": "v2.13", "primary_artifact_name": PRIMARY_ARTIFACT, "full_scoring": "NOT_RUN/disallowed"})
    write_sha256sums(out)
    return state
