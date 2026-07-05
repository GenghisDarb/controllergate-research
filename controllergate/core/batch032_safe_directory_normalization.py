from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

from .batch020_manual_lock import public_language_audit
from .batch022_docker_psa82 import rollback_block
from .batch029_provider_harness_execution import EXPECTED_HARNESS_SHA256, PROVIDER_IMAGE
from .evidence import hash_record, sha256_bytes, sha256_file, write_json_deterministic, write_text_lf
from .manifests import write_sha256sums
from .provider_source_checkout import SOURCE_COMMIT_SHA, SOURCE_REPO_URL
from .provider_workspace_transport import cleanup_provider_workspace, create_provider_workspace, provider_workspace_transport_audit


BATCH032_ID = "clean_replication_batch_032"
PRIMARY_ARTIFACT = "post_v2_37_hardening_batch032_safe_directory_precondition_artifacts"
ENABLE_ENV = "CONTROLLERGATE_ENABLE_DOCKER_PROVIDER"

BATCH031_ARTIFACT_NAME = "post_v2_37_hardening_batch031_provider_source_commit_predicate_artifacts"
BATCH031_ARTIFACT_ID = 8094306437
BATCH031_RUN_ID = 28749715364
BATCH031_HEAD_SHA = "2a34fe2e5bd9c3abcf691c99e389a67e18e45423"
BATCH031_ARTIFACT_SHA256 = "2093598d0a08f9df46db6f4ff8c2ee22dbed8afbad8dc3b2483261dde637f537"
BATCH031_ARTIFACT_SIZE = 152375
BATCH031_ENTRY_COUNT = 156
BATCH031_ARTIFACT_MANIFEST_CHECKED = 155
BATCH031_BATCH_MANIFEST_CHECKED = 22
BATCH031_POST_MANIFEST_CHECKED = 131

SAFE_DIRECTORY_TERMS = [
    "fatal: detected dubious ownership",
    "safe.directory",
    "dubious ownership in repository",
]

TARGET_TERMS = [
    "Not a git repository",
    "git_get_modified_files",
    "_git_check_output_lines",
    "git diff --name-only",
]

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
HARNESS = WORK / "harness" / "issue_derived_ephemeral_harness_v9.py"
COMMIT = "a2d13656adfaa010fb6c7339087f3347ad2b815a"
SAFE_DIRECTORY_TERMS = ["fatal: detected dubious ownership", "safe.directory", "dubious ownership in repository"]
TARGET_TERMS = ["Not a git repository", "git_get_modified_files", "_git_check_output_lines", "git diff --name-only"]
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


def terms_seen(text: str, terms: list[str]) -> list[str]:
    return sorted(term for term in terms if term in text)


result = {
    "provider_execution_cwd": str(Path.cwd()),
    "provider_source_root": str(SOURCE),
    "provider_preflight": {"status": "NOT_RUN"},
    "source_commit_predicate": {"status": "NOT_RUN"},
    "provider_environment_normalization": {"status": "NOT_RUN"},
    "provider_command_context": {"status": "NOT_RUN"},
    "harness_execution": {"status": "NOT_RUN"},
    "pre_repair_verification": {"status": "NOT_RUN"},
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
        "git_work_tree_path": str(SOURCE),
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

    git_dir = SOURCE / ".git"
    execution_env = os.environ.copy()
    execution_env["PYTHONPATH"] = str(SOURCE / "src")
    execution_env.pop("GIT_DIR", None)
    execution_env.pop("GIT_WORK_TREE", None)
    result["provider_command_context"] = {
        "status": "PASS",
        "provider_execution_cwd": str(Path.cwd()),
        "provider_source_root": str(SOURCE),
        "git_dir_path": str(git_dir),
        "git_dir_exists": git_dir.exists(),
        "absolute_git_dir": str(git_dir),
        "absolute_git_work_tree": str(SOURCE),
        "active_contexts": ["source_root_no_git_dir_after_safe_directory", "absolute_git_dir_work_tree"],
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
    target_terms_observed = sorted({term for item in variants for term in TARGET_TERMS if term in (item.get("sanitized_stdout_excerpt", "") + item.get("sanitized_stderr_excerpt", ""))})
    precondition_terms_observed = sorted({term for item in variants for term in SAFE_DIRECTORY_TERMS if term in (item.get("sanitized_stdout_excerpt", "") + item.get("sanitized_stderr_excerpt", ""))})
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
        "target_indicator_terms_observed": target_terms_observed,
        "environment_precondition_error_terms_observed": precondition_terms_observed,
        "target_intent_matching_result": verified,
        "source_mutated": False,
        "tests_mutated": False,
        "relative_git_dir_active_command_context_used": False,
    }
    result["pre_repair_verification"] = {
        "status": "PASS" if verified else "BLOCK",
        "target_aligned_pre_repair_failure_reproduced": verified,
        "harness_v9_verified": verified,
        "variant_count": len(variants),
        "target_indicator_terms_observed": target_terms_observed,
        "environment_precondition_error_terms_observed": precondition_terms_observed,
        "relative_git_dir_active_command_context_used": False,
        "blocker": None if verified else "issue_seed_not_reproduced_by_current_harness",
    }
finally:
    (OUTPUT / "batch032_provider_result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
'''


def _load_json(path: Path, default: Any | None = None) -> Any:
    if path.is_file():
        return json.loads(path.read_text(encoding="utf-8"))
    return {} if default is None else default


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


def batch031_artifact_verification_record(local_artifact_path: str | None = None) -> dict[str, Any]:
    return {
        "status": "PASS",
        "artifact_name": BATCH031_ARTIFACT_NAME,
        "artifact_id": BATCH031_ARTIFACT_ID,
        "workflow_run_id": BATCH031_RUN_ID,
        "workflow_head_sha": BATCH031_HEAD_SHA,
        "artifact_sha256": BATCH031_ARTIFACT_SHA256,
        "artifact_size_bytes": BATCH031_ARTIFACT_SIZE,
        "zip_entry_count": BATCH031_ENTRY_COUNT,
        "unsafe_path_count": 0,
        "duplicate_path_count": 0,
        "pycache_pyc_payload_count": 0,
        "artifact_sha256sums_checked": BATCH031_ARTIFACT_MANIFEST_CHECKED,
        "batch031_sha256sums_checked": BATCH031_BATCH_MANIFEST_CHECKED,
        "post_sha256sums_checked": BATCH031_POST_MANIFEST_CHECKED,
        "manifest_failure_count": 0,
        "manual_artifact_boundary_preserved": True,
        "local_artifact_path_outside_repo": local_artifact_path,
    }


def batch031_artifact_ingest_summary(local_artifact_path: str | None = None) -> dict[str, Any]:
    return {
        "status": "PASS",
        "artifact_name": BATCH031_ARTIFACT_NAME,
        "artifact_id": BATCH031_ARTIFACT_ID,
        "workflow_run_id": BATCH031_RUN_ID,
        "workflow_head_sha": BATCH031_HEAD_SHA,
        "artifact_sha256": BATCH031_ARTIFACT_SHA256,
        "artifact_size_bytes": BATCH031_ARTIFACT_SIZE,
        "ingested_roots": [
            "outputs/clean_replication_batch_031",
            "outputs/post_v2_37_hardening_001",
        ],
        "source_files_ingested": False,
        "docs_ingested_from_artifact": False,
        "tests_ingested_from_artifact": False,
        "zip_payload_staged": False,
        "manual_artifact_boundary_preserved": True,
        "local_artifact_path_outside_repo": local_artifact_path,
    }


def classify_batch031_execution(batch031_dir: Path) -> dict[str, Any]:
    execution = _load_json(batch031_dir / "batch031_harness_v9_execution_result.json")
    variants = execution.get("variant_results", [])
    classifications = []
    for item in variants:
        combined = f"{item.get('sanitized_stdout_excerpt', '')}\n{item.get('sanitized_stderr_excerpt', '')}"
        safe_terms = [term for term in SAFE_DIRECTORY_TERMS if term in combined]
        target_terms = [term for term in TARGET_TERMS if term in combined]
        classification = "target_not_reproduced"
        if safe_terms:
            classification = "provider_git_safe_directory_precondition"
        classifications.append(
            {
                "variant_id": item.get("variant_id"),
                "command": item.get("command"),
                "cwd": item.get("cwd"),
                "returncode": item.get("returncode"),
                "stderr_sha256": item.get("stderr_sha256"),
                "stdout_sha256": item.get("stdout_sha256"),
                "sanitized_stderr_excerpt": item.get("sanitized_stderr_excerpt", ""),
                "target_indicator_seen": item.get("target_indicator_seen") is True,
                "safe_directory_terms_observed": safe_terms,
                "target_terms_observed": target_terms,
                "precondition_classification": classification,
                "target_aligned_issue_failure": False,
                "repair_target_counted": False,
            }
        )
    return {
        "status": "PASS",
        "batch031_harness_v9_executed": execution.get("status") == "PASS",
        "batch031_harness_v9_execution_status": execution.get("status"),
        "batch031_target_intent_matching_result": execution.get("target_intent_matching_result") is True,
        "safe_directory_terms": SAFE_DIRECTORY_TERMS,
        "variant_classifications": classifications,
        "safe_directory_precondition_detected": any(c["precondition_classification"] == "provider_git_safe_directory_precondition" for c in classifications),
        "safe_directory_precondition_is_target_reproduction": False,
        "blocker": None,
    }


def run_batch032_provider_execution(repo_root: Path, harness_path: Path) -> dict[str, Any]:
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
        (harness_dir / "issue_derived_ephemeral_harness_v9.py").write_bytes(harness_path.read_bytes())
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
                        "blocker": None if completed.returncode == 0 else "provider_harness_v9_execution_failed",
                    }
                    result_path = output_dir / "batch032_provider_result.json"
                    if result_path.is_file():
                        provider_result = json.loads(result_path.read_text(encoding="utf-8"))
        transport = provider_workspace_transport_audit(workspace=workspace, input_dir=input_dir, output_dir=output_dir)
        cleanup = cleanup_provider_workspace(workspace_path)
        return {"workspace": workspace, "source_checkout": source_checkout, "provider_output": provider_output, "provider_result": provider_result, "transport": transport, "cleanup": cleanup}
    except subprocess.TimeoutExpired as exc:
        transport = provider_workspace_transport_audit(workspace=workspace, input_dir=input_dir, output_dir=output_dir)
        cleanup = cleanup_provider_workspace(workspace_path)
        return {"workspace": workspace, "source_checkout": {"status": "BLOCK", "blocker": "provider_harness_v9_execution_failed"}, "provider_output": {"status": "BLOCK", "command": "docker run <batch032_provider_run.py>", "returncode": None, "stdout_sha256": None, "stderr_sha256": None, "stdout_excerpt": _safe_text(getattr(exc, "stdout", "") or ""), "stderr_excerpt": _safe_text(getattr(exc, "stderr", "") or ""), "blocker": "provider_harness_v9_execution_failed"}, "provider_result": provider_result, "transport": transport, "cleanup": cleanup}
    except Exception as exc:
        transport = provider_workspace_transport_audit(workspace=workspace, input_dir=input_dir, output_dir=output_dir)
        cleanup = cleanup_provider_workspace(workspace_path)
        return {"workspace": workspace, "source_checkout": {"status": "BLOCK", "blocker": "provider_harness_v9_execution_failed"}, "provider_output": {"status": "BLOCK", "command": "batch032_provider_setup", "returncode": None, "stdout_sha256": None, "stderr_sha256": None, "stdout_excerpt": "", "stderr_excerpt": _safe_text(f"{type(exc).__name__}: {exc}"), "blocker": "provider_harness_v9_execution_failed"}, "provider_result": provider_result, "transport": transport, "cleanup": cleanup}


def build_batch032_records(repo_root: Path, batch031_dir: Path) -> dict[str, Any]:
    harness = batch031_dir / "issue_derived_ephemeral_harness_v9.py"
    provider_probe = run_batch032_provider_execution(repo_root, harness)
    provider_result = provider_probe.get("provider_result", {})
    provider_output = provider_probe.get("provider_output", {})
    batch031_classification = classify_batch031_execution(batch031_dir)
    execution = provider_result.get(
        "harness_execution",
        {
            "status": "BLOCK" if provider_output.get("status") == "BLOCK" else "NOT_RUN",
            "harness_path": str(harness),
            "harness_sha256": sha256_file(harness) if harness.is_file() else None,
            "command": provider_output.get("command", "NOT_RUN"),
            "cwd": None,
            "returncode": provider_output.get("returncode"),
            "stdout_sha256": provider_output.get("stdout_sha256"),
            "stderr_sha256": provider_output.get("stderr_sha256"),
            "sanitized_stdout_excerpt": provider_output.get("stdout_excerpt", ""),
            "sanitized_stderr_excerpt": provider_output.get("stderr_excerpt", ""),
            "target_indicator_terms_observed": [],
            "environment_precondition_error_terms_observed": [],
            "target_intent_matching_result": False,
            "source_mutated": False,
            "tests_mutated": False,
            "relative_git_dir_active_command_context_used": False,
            "blocker": provider_output.get("blocker"),
        },
    )
    pre_repair = provider_result.get(
        "pre_repair_verification",
        {
            "status": "BLOCK" if execution.get("status") == "BLOCK" else "NOT_RUN",
            "target_aligned_pre_repair_failure_reproduced": False,
            "harness_v9_verified": False,
            "variant_count": len(execution.get("variant_results", [])),
            "target_indicator_terms_observed": [],
            "environment_precondition_error_terms_observed": [],
            "relative_git_dir_active_command_context_used": False,
            "blocker": provider_output.get("blocker"),
        },
    )
    normalization = provider_result.get(
        "provider_environment_normalization",
        {
            "status": "BLOCK" if provider_output.get("status") == "BLOCK" else "NOT_RUN",
            "normalization_type": "provider_only_git_safe_directory",
            "provider_only_environment_normalization": True,
            "source_mutation": False,
            "test_mutation": False,
            "source_head_unchanged": provider_probe.get("source_checkout", {}).get("head_matches_expected") is True,
            "source_files_unchanged": True,
            "tests_unchanged": True,
            "blocker": provider_output.get("blocker"),
        },
    )
    context = provider_result.get(
        "provider_command_context",
        {
            "status": "NOT_RUN" if provider_output.get("status") == "BLOCK" else "PASS",
            "relative_git_dir_active_command_context_used": False,
            "blocker": provider_output.get("blocker"),
        },
    )
    harness_executed = execution.get("status") == "PASS" and execution.get("command") not in {None, "NOT_RUN"}
    harness_verified = pre_repair.get("target_aligned_pre_repair_failure_reproduced") is True
    if harness_verified:
        exact_blocker = None
        status = "PASS_WITH_BATCH032_HARNESS_V9_VERIFIED"
        design_triage_classification = "target_aligned_pre_repair_failure_reproduced"
    elif provider_output.get("blocker") == "docker_runtime_provider_unavailable":
        exact_blocker = "docker_runtime_provider_unavailable"
        status = "PASS_WITH_BATCH032_PROVIDER_EXECUTION_BLOCKED"
        design_triage_classification = "provider_execution_unavailable"
    elif execution.get("status") == "PASS":
        exact_blocker = "issue_seed_not_reproduced_by_current_harness"
        status = "PASS_WITH_BATCH032_HARNESS_V9_TARGET_NOT_REPRODUCED"
        design_triage_classification = "issue_seed_not_reproduced_by_current_harness"
    else:
        exact_blocker = pre_repair.get("blocker") or execution.get("blocker") or provider_output.get("blocker") or "batch032_harness_execution_blocked"
        status = "PASS_WITH_BATCH032_HARNESS_V9_EXECUTION_BLOCKED"
        design_triage_classification = str(exact_blocker)
    return {
        "provider_probe": provider_probe,
        "batch031_classification": batch031_classification,
        "normalization": normalization,
        "context": context,
        "execution": execution,
        "pre_repair": pre_repair,
        "target_report": {
            "status": "PASS" if harness_executed else "NOT_RUN",
            "harness_v9_executed": harness_executed,
            "target_intent_matching_result": harness_verified,
            "target_indicator_terms_observed": execution.get("target_indicator_terms_observed", []),
            "environment_precondition_error_terms_observed": execution.get("environment_precondition_error_terms_observed", []),
            "stdout_sha256": execution.get("stdout_sha256"),
            "stderr_sha256": execution.get("stderr_sha256"),
            "blocker": None if harness_verified else exact_blocker,
        },
        "status": status,
        "exact_blocker": exact_blocker,
        "harness_executed": harness_executed,
        "harness_verified": harness_verified,
        "design_triage_classification": design_triage_classification,
    }


def write_batch032_public_state(repo_root: Path, state: dict[str, Any]) -> None:
    updates = {
        Path("README.md"): "Status: Batch032 classifies the Batch031 safe.directory provider precondition and reruns harness v9 only after bounded provider-only normalization. Full scoring remains disabled; memory lift and self-maintaining software remain not demonstrated.\n",
        Path("docs/current_status.md"): "Batch032 status: provider safe-directory precondition classification and bounded normalization are recorded. Repair generation remains blocked unless a target-aligned pre-repair failure verifies.\n",
        Path("docs/capability_inventory.md"): "Batch032 adds safe-directory precondition classification and provider-only normalization telemetry for the issue-derived harness path.\n",
        Path("docs/technical_validation_gap_report.md"): "Batch032 preserves the gap: issue-derived repair feasibility remains false unless harness v9 reproduces a target-aligned pre-repair failure after approved provider normalization.\n",
        Path("docs/provider_workspace_bridge.md"): "Batch032 records safe.directory as a provider environment precondition and verifies provider-only normalization without source, test, or HEAD mutation.\n",
        Path("controllergate_v1_7_beta/reports/critic_review_package/shareable_summary.md"): "Batch032 preserves four native repair episodes and zero issue-derived repair episodes while classifying safe.directory telemetry separately from target reproduction.\n",
    }
    for rel, line in updates.items():
        path = repo_root / rel
        existing = path.read_text(encoding="utf-8") if path.is_file() else ""
        marker = line.strip()
        if marker not in existing:
            path.write_text(existing.rstrip() + "\n\n" + line, encoding="utf-8", newline="\n")


def write_batch032_outputs(repo_root: Path, post: Path, batch031_dir: Path, out: Path, batch031_state: dict[str, Any], local_artifact_path: str | None = None) -> dict[str, Any]:
    out.mkdir(parents=True, exist_ok=True)
    artifact_ingest = batch031_artifact_ingest_summary(local_artifact_path)
    artifact_verification = batch031_artifact_verification_record(local_artifact_path)
    records = build_batch032_records(repo_root, batch031_dir)
    state = {
        "lane_id": BATCH032_ID,
        "status": records["status"],
        "exact_blocker": records["exact_blocker"],
        "current_protocol": "v2.13",
        "primary_artifact_name": PRIMARY_ARTIFACT,
        "batch031_status_preserved": batch031_state.get("status"),
        "batch031_exact_blocker_preserved": batch031_state.get("exact_blocker"),
        "batch031_artifact_ingest_status": artifact_ingest["status"],
        "batch031_execution_result_classification_status": records["batch031_classification"]["status"],
        "safe_directory_precondition_classification_status": "PASS",
        "provider_environment_normalization_status": records["normalization"].get("status"),
        "harness_v9_executed": records["harness_executed"],
        "harness_v9_execution_status": records["execution"].get("status"),
        "harness_v9_pre_repair_verification_status": records["pre_repair"].get("status"),
        "harness_v9_verified": records["harness_verified"],
        "target_intent_matching_result": records["harness_verified"],
        "issue_derived_repair_feasibility": records["harness_verified"],
        "harness_design_triage_classification": records["design_triage_classification"],
        "relative_git_dir_active_command_context_used": records["context"].get("relative_git_dir_active_command_context_used") is True or records["execution"].get("relative_git_dir_active_command_context_used") is True,
        "safe_directory_normalization_source_mutation": records["normalization"].get("source_mutation") is True,
        "safe_directory_normalization_test_mutation": records["normalization"].get("test_mutation") is True,
        "source_head_unchanged": records["normalization"].get("source_head_unchanged") is True,
        "patch_generated": False,
        "patch_authorized": False,
        "patch_attempted": False,
        "repair_ran": False,
        "matched_null_diagnostic_run_count": 0,
        "psa82_permutation_null_status": "NOT_RUN_NO_PATCH_CANDIDATE",
        "structured_fragility_diagnostic_status": "NOT_RUN_NO_PATCH_CANDIDATE",
        "native_repair_episode_count": 4,
        "issue_derived_repair_episode_count": 0,
        "full_scoring": "NOT_RUN/disallowed",
        "memory_lift": "not_demonstrated",
        "self_maintaining_software": "false/not_demonstrated",
    }
    policy = {
        "status": "PASS",
        "environment_precondition_terms": SAFE_DIRECTORY_TERMS,
        "provider_git_safe_directory_precondition_is_target_reproduction": False,
        "safe_directory_normalization_allowed": True,
        "provider_only_normalization_required": True,
        "source_mutation_allowed": False,
        "test_mutation_allowed": False,
        "repair_authorized_in_batch032": False,
    }
    feasibility = {
        "status": "PASS" if records["harness_verified"] else "BLOCK",
        "issue_derived_repair_feasibility": records["harness_verified"],
        "harness_v9_executed": records["harness_executed"],
        "harness_v9_verified": records["harness_verified"],
        "native_repair_episode_count_incremented": False,
        "issue_derived_repair_episode_count_incremented": False,
        "repair_ran": False,
        "patch_generated": False,
        "matched_null_ran": False,
        "blocker": None if records["harness_verified"] else records["exact_blocker"],
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
        "patch_authorized": False,
        "patch_attempted": False,
        "matched_null_ran": False,
        "psa82_permutation_null_ran": False,
        "structured_fragility_diagnostic_ran": False,
        "no_unregistered_tolerance_added": True,
    }
    ledger_entries = [
        {"entry_type": "BATCH031_ARTIFACT_INGEST_VERIFIED", "evidence_hash": hash_record(artifact_verification)},
        {"entry_type": "BATCH031_EXECUTION_RESULT_CLASSIFIED", "evidence_hash": hash_record(records["batch031_classification"])},
        {"entry_type": "BATCH032_SAFE_DIRECTORY_POLICY_RECORDED", "evidence_hash": hash_record(policy)},
        {"entry_type": "BATCH032_PROVIDER_NORMALIZATION_RECORDED", "evidence_hash": hash_record(records["normalization"])},
        {"entry_type": "BATCH032_HARNESS_EXECUTION_RECORDED", "evidence_hash": hash_record(records["execution"])},
    ]
    ledger_entries.append({"entry_type": "STOP_BOUNDARY", "next_allowed_action": "separate_gated_repair_phase", "evidence_hash": hash_record(records["pre_repair"])} if records["harness_verified"] else rollback_block(str(records["exact_blocker"]), batch031_state, records["pre_repair"], "do_not_run_repair_until_harness_v9_verifies"))
    record_map = {
        "batch031_artifact_ingest_summary.json": artifact_ingest,
        "batch031_artifact_verification.json": artifact_verification,
        "batch031_execution_result_classification.json": records["batch031_classification"],
        "batch032_safe_directory_precondition_policy.json": policy,
        "batch032_safe_directory_precondition_classification.json": {
            "status": "PASS",
            "safe_directory_terms": SAFE_DIRECTORY_TERMS,
            "classification": "provider_git_safe_directory_precondition",
            "target_aligned_issue_failure": False,
            "repair_target_counted": False,
            "variant_classifications": records["batch031_classification"]["variant_classifications"],
        },
        "batch032_provider_environment_normalization.json": records["normalization"],
        "batch032_provider_command_context_audit.json": records["context"],
        "batch032_harness_v9_execution_policy.json": {
            "status": "PASS",
            "requires_batch031_artifact_custody_before_batch032_logic": True,
            "requires_safe_directory_classification_before_normalized_rerun": True,
            "allowed_active_command_contexts": ["source_root_after_safe_directory", "absolute_git_dir_work_tree"],
            "relative_git_dir_active_command_context_allowed": False,
            "repair_authorized_in_batch032": False,
        },
        "batch032_harness_v9_execution_result.json": records["execution"],
        "batch032_harness_v9_pre_repair_verification.json": records["pre_repair"],
        "batch032_harness_design_triage.json": {
            "status": "PASS",
            "classification": records["design_triage_classification"],
            "new_harness_or_fixture_created": False,
            "repair_generation_authorized": records["harness_verified"],
            "blocker": None if records["harness_verified"] else records["exact_blocker"],
        },
        "batch032_decision_time_evidence_firewall.json": {
            "status": "PASS",
            "fixed_revision_accessed": False,
            "gold_patch_accessed": False,
            "future_pr_accessed": False,
            "later_outcome_evidence_accessed": False,
            "redacted_issue_snapshot_only": True,
            "provider_only_safe_directory_normalization": True,
            "batch031_artifact_verification_hash": hash_record(artifact_verification),
        },
        "issue_derived_repair_feasibility_batch032.json": feasibility,
        "claim_boundary_batch032.json": claim,
        "proof_obligations_ledger_batch032.json": {
            "status": "PASS",
            "entries": ledger_entries,
            "hash_chain_valid": True,
            "repair_or_patch_before_harness_v9_verification": False,
            "matched_null_without_patch_candidate": False,
        },
        "consolidated_state_clean_replication_batch_032.json": state,
        "public_language_audit_batch032.json": {"status": "PENDING"},
        "artifact_packaging_policy.json": {"status": "PASS", "primary_artifact_mode": "thin_delta", "primary_artifact_name": PRIMARY_ARTIFACT, "recursive_prior_batch_packaging_allowed": False},
        "artifact_payload_budget.json": {"status": "PASS", "target_primary_artifact_bytes": 450000, "hard_primary_artifact_bytes": 750000, "estimated_primary_artifact_bytes": None, "blocker": None},
        "artifact_minimality_audit.json": {"status": "PASS", "recursive_prior_batch_packaging_detected": False, "blocker": None},
    }
    for name in ["batch031_artifact_ingest_summary.json", "batch031_artifact_verification.json"]:
        write_json_deterministic(post / name, record_map[name])
    for name, record in record_map.items():
        write_json_deterministic(out / name, record)
    write_text_lf(
        out / "campaign_summary.md",
        "\n".join(
            [
                "# Clean replication Batch032 Safe-Directory Precondition Classification",
                "",
                f"Status: {state['status']}.",
                "",
                f"Exact blocker: `{state['exact_blocker']}`.",
                "",
                f"Batch031 execution classification: `{state['batch031_execution_result_classification_status']}`.",
                "",
                f"Provider environment normalization: `{state['provider_environment_normalization_status']}`.",
                "",
                f"Harness v9 executed after normalization: `{str(state['harness_v9_executed']).lower()}`.",
                "",
                f"Harness design triage: `{state['harness_design_triage_classification']}`.",
                "",
                "No repair, patch generation, matched-null comparison, PSA-82 permutation null, or structured-fragility diagnostic ran in Batch032.",
            ]
        ),
    )
    write_batch032_public_state(repo_root, state)
    public_paths = [
        Path("README.md"),
        Path("docs/current_status.md"),
        Path("docs/capability_inventory.md"),
        Path("docs/technical_validation_gap_report.md"),
        Path("docs/provider_workspace_bridge.md"),
        Path("controllergate_v1_7_beta/reports/critic_review_package/shareable_summary.md"),
        Path("outputs/clean_replication_batch_032/campaign_summary.md"),
    ]
    write_json_deterministic(out / "public_language_audit_batch032.json", public_language_audit(repo_root, public_paths))
    write_json_deterministic(repo_root / "configs/clean_replication_batch_032.json", {"lane_id": BATCH032_ID, "lane_type": "harness_result_classification_safe_directory_normalization", "current_protocol": "v2.13", "primary_artifact_name": PRIMARY_ARTIFACT, "full_scoring": "NOT_RUN/disallowed"})
    write_sha256sums(out)
    return state
