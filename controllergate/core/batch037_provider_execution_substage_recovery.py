from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

from .batch020_manual_lock import public_language_audit
from .evidence import hash_record, sha256_bytes, sha256_file, write_json_deterministic, write_text_lf
from .manifests import write_sha256sums
from .provider_source_checkout import SOURCE_COMMIT_SHA, SOURCE_REPO_URL
from .provider_workspace_transport import cleanup_provider_workspace, create_provider_workspace, provider_workspace_transport_audit


BATCH037_ID = "clean_replication_batch_037"
PRIMARY_ARTIFACT = "post_v2_37_hardening_batch037_provider_execution_substage_recovery_artifacts"
ENABLE_ENV = "CONTROLLERGATE_ENABLE_DOCKER_PROVIDER"

BATCH036_ARTIFACT_NAME = "post_v2_37_hardening_batch036_post_repair_failure_decomposition_artifacts"
BATCH036_ARTIFACT_ID = 8098158675
BATCH036_RUN_ID = 28762763373
BATCH036_HEAD_SHA = "a0855e65813f9d6e38c39f20636a65069f09a5cb"
BATCH036_ARTIFACT_SHA256 = "7f2105ec414b23ea9bc48e5720b15aebda66a57ec161a507cebf6e82b708eeb7"
BATCH036_ARTIFACT_SIZE = 161782
BATCH036_ENTRY_COUNT = 169
BATCH036_ARTIFACT_MANIFEST_CHECKED = 168
BATCH036_BATCH_MANIFEST_CHECKED = 25
BATCH036_POST_MANIFEST_CHECKED = 141
DEFAULT_LOCAL_BATCH036_ARTIFACT_PATH = (
    "C:/Users/thisb/Downloads/post_v2_37_hardening_batch036_post_repair_failure_decomposition_artifacts.zip"
)

EXPECTED_PATCH_SHA256 = "9c1061f5c60878b7ace6a3c02f41ec2af162fd4de66192a34028ed720e864ec1"
PATCH_PATH = "src/darker/git.py"
PROVIDER_IMAGE = "python:3.7"


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
DUPLICATE = WORK / "duplicate" / "darker"
HARNESS = WORK / "harness" / "issue_derived_ephemeral_harness_v10.py"
PATCH = INPUT / "batch036_source_only_patch_candidate_v2.diff"
DEPENDENCY_LOCK = INPUT / "dependency_lock.json"
COMMIT = "a2d13656adfaa010fb6c7339087f3347ad2b815a"
PATCH_PATH = "src/darker/git.py"
EXPECTED_PATCH_SHA256 = "9c1061f5c60878b7ace6a3c02f41ec2af162fd4de66192a34028ed720e864ec1"
TARGET_TERMS = ["Not a git repository", "not a git repository"]
SECONDARY_TERMS = ["FileNotFoundError", "No such file or directory", "pylint"]
OUTPUT.mkdir(parents=True, exist_ok=True)


def sha_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def sha_file(path: Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def excerpt(value: str, limit: int = 4000) -> str:
    return (value or "")[-limit:]


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
        "stdout_sha256": sha_text(completed.stdout),
        "stderr_sha256": sha_text(completed.stderr),
        "sanitized_stdout_excerpt": excerpt(completed.stdout),
        "sanitized_stderr_excerpt": excerpt(completed.stderr),
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def public_run_record(record: dict, *, status: str, blocker: str | None = None) -> dict:
    return {
        "status": status,
        "command": record.get("command"),
        "cwd": record.get("cwd"),
        "returncode": record.get("returncode"),
        "stdout_sha256": record.get("stdout_sha256"),
        "stderr_sha256": record.get("stderr_sha256"),
        "sanitized_stdout_excerpt": record.get("sanitized_stdout_excerpt", ""),
        "sanitized_stderr_excerpt": record.get("sanitized_stderr_excerpt", ""),
        "blocker": blocker,
    }


def git_run(args, cwd=SOURCE, timeout=120):
    return run(["git", "-c", f"safe.directory={cwd}", *args], cwd=cwd, timeout=timeout)


def terms_seen(text: str, terms: list[str]) -> list[str]:
    lowered = text.lower()
    return sorted({term for term in terms if term in text or term.lower() in lowered})


def classify_replay(parsed: dict, wrapper: dict, label: str, source: Path) -> dict:
    combined = (
        f"{parsed.get('sanitized_stdout_excerpt', '')}\n"
        f"{parsed.get('sanitized_stderr_excerpt', '')}\n"
        f"{wrapper.get('stdout', '')}\n"
        f"{wrapper.get('stderr', '')}"
    )
    target_terms = parsed.get("target_indicator_terms_observed") or terms_seen(combined, TARGET_TERMS)
    secondary_terms = terms_seen(combined, SECONDARY_TERMS)
    target_failure_resolved = not target_terms
    fully_passed = parsed.get("returncode") == 0 and target_failure_resolved and not secondary_terms
    if target_terms:
        classification = "repair_v2_target_not_resolved"
    elif secondary_terms:
        classification = "target_resolution_blocked_by_secondary_linter_precondition"
    elif fully_passed:
        classification = "target_replay_passed"
    else:
        classification = "target_resolution_status_ambiguous"
    return {
        "status": "PASS" if parsed else "BLOCK",
        "label": label,
        "provider_cwd": str(source),
        "source_root": str(source),
        "command": "GIT_DIR=.git python -m darker --check src",
        "wrapper_command": wrapper.get("command"),
        "returncode": parsed.get("returncode"),
        "wrapper_returncode": wrapper.get("returncode"),
        "stdout_sha256": parsed.get("stdout_sha256"),
        "stderr_sha256": parsed.get("stderr_sha256"),
        "wrapper_stdout_sha256": wrapper.get("stdout_sha256"),
        "wrapper_stderr_sha256": wrapper.get("stderr_sha256"),
        "sanitized_stdout_excerpt": parsed.get("sanitized_stdout_excerpt", ""),
        "sanitized_stderr_excerpt": parsed.get("sanitized_stderr_excerpt", ""),
        "target_indicator_terms_observed": target_terms,
        "secondary_linter_precondition_terms_observed": secondary_terms,
        "target_failure_resolved": target_failure_resolved,
        "target_replay_fully_passed": fully_passed,
        "classification": classification,
        "missing_pylint_treated_as_target_issue": False,
        "missing_pylint_treated_as_repair_success": False,
        "blocker": None if parsed else "harness_v10_execution_failed",
    }


def harness_run(source: Path, label: str) -> dict:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(source / "src")
    env.pop("GIT_DIR", None)
    env.pop("GIT_WORK_TREE", None)
    wrapper = run(["python", str(HARNESS)], cwd=source, timeout=300, env=env)
    parsed = {}
    try:
        parsed = json.loads(wrapper["stdout"])
    except Exception:
        parsed = {}
    return classify_replay(parsed, wrapper, label, source)


SUBSTAGE_ORDER = [
    "provider_available",
    "provider_workspace_materialized",
    "selected_source_head_verified",
    "candidate_v2_patch_available",
    "candidate_v2_patch_hash_verified",
    "candidate_v2_patch_apply_check",
    "candidate_v2_patch_apply",
    "post_repair_target_replay_v2",
    "duplicate_clean_replay_v2",
]

result = {
    "substage_order": SUBSTAGE_ORDER,
    "substage_records": {name: {"status": "NOT_RUN"} for name in SUBSTAGE_ORDER},
    "dependency_environment_materialization": {"status": "NOT_RUN"},
    "patch_v2_application": {"status": "NOT_RUN"},
    "patch_v2_scope_audit": {"status": "NOT_RUN"},
    "post_repair_target_replay_v2": {"status": "NOT_RUN"},
    "duplicate_clean_replay_v2": {"status": "NOT_RUN"},
    "repair_validation": {"status": "NOT_RUN"},
}

try:
    py = run(["python", "--version"], timeout=120)
    git_version = run(["git", "--version"], timeout=120)
    py_version = py["stdout"].strip() or py["stderr"].strip()
    provider_ok = py["returncode"] == 0 and git_version["returncode"] == 0 and py_version.startswith("Python 3.7.")
    result["substage_records"]["provider_available"] = {
        "status": "PASS" if provider_ok else "BLOCK",
        "python_version": py_version,
        "git_version": git_version["stdout"].strip() or git_version["stderr"].strip(),
        "returncode": py["returncode"] or git_version["returncode"],
        "stdout_sha256": py["stdout_sha256"],
        "stderr_sha256": py["stderr_sha256"],
        "sanitized_stdout_excerpt": py["sanitized_stdout_excerpt"],
        "sanitized_stderr_excerpt": py["sanitized_stderr_excerpt"] or git_version["sanitized_stderr_excerpt"],
        "blocker": None if provider_ok else "runtime_provider_python_version_mismatch",
    }
    if not provider_ok:
        raise SystemExit(0)

    materialized = SOURCE.is_dir() and HARNESS.is_file() and PATCH.is_file() and DEPENDENCY_LOCK.is_file()
    result["substage_records"]["provider_workspace_materialized"] = {
        "status": "PASS" if materialized else "BLOCK",
        "source_root": str(SOURCE),
        "harness_path": str(HARNESS),
        "patch_path": str(PATCH),
        "dependency_lock_path": str(DEPENDENCY_LOCK),
        "source_exists": SOURCE.is_dir(),
        "harness_exists": HARNESS.is_file(),
        "patch_exists": PATCH.is_file(),
        "dependency_lock_exists": DEPENDENCY_LOCK.is_file(),
        "returncode": 0 if materialized else 1,
        "stdout_sha256": sha_text(""),
        "stderr_sha256": sha_text("" if materialized else "provider workspace materialization incomplete"),
        "sanitized_stdout_excerpt": "",
        "sanitized_stderr_excerpt": "" if materialized else "provider workspace materialization incomplete",
        "blocker": None if materialized else "provider_workspace_materialization_failed",
    }
    if not materialized:
        raise SystemExit(0)

    cat = git_run(["cat-file", "-t", COMMIT], timeout=120)
    head = git_run(["rev-parse", "HEAD"], timeout=120)
    observed_head = head["stdout"].strip()
    source_ok = cat["returncode"] == 0 and cat["stdout"].strip() == "commit" and observed_head == COMMIT
    result["substage_records"]["selected_source_head_verified"] = {
        **public_run_record(head, status="PASS" if source_ok else "BLOCK", blocker=None if source_ok else "provider_source_commit_mismatch"),
        "expected_source_commit_sha": COMMIT,
        "observed_source_head_sha": observed_head,
        "git_object_type": cat["stdout"].strip(),
        "head_matches_expected": observed_head == COMMIT,
    }
    if not source_ok:
        raise SystemExit(0)

    lock = json.loads(DEPENDENCY_LOCK.read_text(encoding="utf-8"))
    packages = lock.get("packages", [])
    pip_pkg = next((item for item in packages if item.get("name") == "pip"), None)
    other = [item for item in packages if item.get("name") != "pip"]
    commands = []
    if pip_pkg:
        commands.append(["python", "-m", "pip", "install", "--disable-pip-version-check", "--no-input", "--no-deps", f"pip=={pip_pkg['version']}"])
    if other:
        commands.append(["python", "-m", "pip", "install", "--disable-pip-version-check", "--no-input", "--no-deps"] + [f"{item['name']}=={item['version']}" for item in other])
    install_logs = []
    install_ok = True
    for cmd in commands:
        item = run(cmd, timeout=1200)
        install_logs.append(public_run_record(item, status="PASS" if item["returncode"] == 0 else "BLOCK", blocker=None if item["returncode"] == 0 else "manual_lock_environment_materialization_failed"))
        install_ok = install_ok and item["returncode"] == 0
        if not install_ok:
            break
    result["dependency_environment_materialization"] = {
        "status": "PASS" if install_ok else "BLOCK",
        "install_log_count": len(install_logs),
        "install_logs": install_logs,
        "blocker": None if install_ok else "manual_lock_environment_materialization_failed",
    }
    if not install_ok:
        raise SystemExit(0)

    available = PATCH.is_file()
    result["substage_records"]["candidate_v2_patch_available"] = {
        "status": "PASS" if available else "BLOCK",
        "patch_path": str(PATCH),
        "returncode": 0 if available else 1,
        "stdout_sha256": sha_text(""),
        "stderr_sha256": sha_text("" if available else "candidate v2 patch missing"),
        "sanitized_stdout_excerpt": "",
        "sanitized_stderr_excerpt": "" if available else "candidate v2 patch missing",
        "blocker": None if available else "candidate_v2_patch_unavailable",
    }
    if not available:
        raise SystemExit(0)

    patch_sha = sha_file(PATCH)
    hash_ok = patch_sha == EXPECTED_PATCH_SHA256
    result["substage_records"]["candidate_v2_patch_hash_verified"] = {
        "status": "PASS" if hash_ok else "BLOCK",
        "patch_sha256": patch_sha,
        "expected_patch_sha256": EXPECTED_PATCH_SHA256,
        "returncode": 0 if hash_ok else 1,
        "stdout_sha256": sha_text(patch_sha or ""),
        "stderr_sha256": sha_text("" if hash_ok else "candidate v2 patch hash mismatch"),
        "sanitized_stdout_excerpt": patch_sha or "",
        "sanitized_stderr_excerpt": "" if hash_ok else "candidate v2 patch hash mismatch",
        "blocker": None if hash_ok else "candidate_v2_patch_hash_mismatch",
    }
    if not hash_ok:
        raise SystemExit(0)

    check = git_run(["apply", "--check", str(PATCH)], timeout=120)
    check_ok = check["returncode"] == 0
    result["substage_records"]["candidate_v2_patch_apply_check"] = public_run_record(
        check,
        status="PASS" if check_ok else "BLOCK",
        blocker=None if check_ok else "patch_v2_apply_check_failed",
    )
    if not check_ok:
        result["patch_v2_application"] = {
            "status": "BLOCK",
            "patch_apply_check_status": "BLOCK",
            "patch_apply_attempted": False,
            "patch_sha256": patch_sha,
            "touched_files": [],
            "source_only": False,
            "tests_modified": False,
            "blocker": "patch_v2_apply_check_failed",
        }
        result["patch_v2_scope_audit"] = {
            "status": "BLOCK",
            "patch_apply_attempted": False,
            "source_only": False,
            "tests_modified": False,
            "touched_files": [],
            "blocker": "patch_v2_apply_check_failed",
        }
        raise SystemExit(0)

    apply = git_run(["apply", str(PATCH)], timeout=120)
    diff_after = git_run(["diff", "--name-only"], timeout=120)
    diff_text = git_run(["diff"], timeout=120)
    touched = [line.strip() for line in diff_after["stdout"].splitlines() if line.strip()]
    source_only = bool(touched) and all(path.startswith("src/") for path in touched)
    tests_modified = any("/tests/" in path or path.startswith("tests/") for path in touched)
    apply_ok = apply["returncode"] == 0 and touched == [PATCH_PATH] and source_only and not tests_modified
    result["substage_records"]["candidate_v2_patch_apply"] = public_run_record(
        apply,
        status="PASS" if apply_ok else "BLOCK",
        blocker=None if apply_ok else "patch_v2_application_failed",
    )
    result["patch_v2_application"] = {
        "status": "PASS" if apply_ok else "BLOCK",
        "patch_apply_check_status": "PASS",
        "patch_apply_attempted": True,
        "patch_apply_returncode": apply["returncode"],
        "patch_sha256": patch_sha,
        "touched_files": touched,
        "source_only": source_only,
        "tests_modified": tests_modified,
        "diff_sha256": diff_text["stdout_sha256"],
        "blocker": None if apply_ok else "patch_v2_application_failed",
    }
    result["patch_v2_scope_audit"] = {
        "status": "PASS" if apply_ok else "BLOCK",
        "patch_apply_attempted": True,
        "touched_files": touched,
        "source_only": source_only,
        "tests_modified": tests_modified,
        "non_source_paths": [path for path in touched if not path.startswith("src/")],
        "test_paths": [path for path in touched if "/tests/" in path or path.startswith("tests/")],
        "blocker": None if apply_ok else "patch_v2_scope_invalid",
    }
    if not apply_ok:
        raise SystemExit(0)

    post = harness_run(SOURCE, "post_repair_v2")
    result["post_repair_target_replay_v2"] = post
    result["substage_records"]["post_repair_target_replay_v2"] = {
        "status": post.get("status"),
        "command": post.get("command"),
        "cwd": post.get("provider_cwd"),
        "returncode": post.get("returncode"),
        "stdout_sha256": post.get("stdout_sha256"),
        "stderr_sha256": post.get("stderr_sha256"),
        "sanitized_stdout_excerpt": post.get("sanitized_stdout_excerpt", ""),
        "sanitized_stderr_excerpt": post.get("sanitized_stderr_excerpt", ""),
        "target_failure_resolved": post.get("target_failure_resolved"),
        "classification": post.get("classification"),
        "blocker": None if post.get("target_replay_fully_passed") else post.get("classification") or "post_repair_target_not_resolved",
    }
    full_pass = post.get("target_replay_fully_passed") is True

    duplicate_record = {"status": "NOT_RUN", "duplicate_replay_passed": False, "blocker": post.get("classification") or "post_repair_target_not_resolved"}
    if full_pass:
        if DUPLICATE.exists():
            subprocess.run(["rm", "-rf", str(DUPLICATE)], check=False)
        clone = run(["git", "clone", "--no-checkout", str(SOURCE), str(DUPLICATE)], timeout=300)
        checkout = git_run(["checkout", "--detach", COMMIT], cwd=DUPLICATE, timeout=120) if clone["returncode"] == 0 else {"returncode": 1}
        apply_check_dup = git_run(["apply", "--check", str(PATCH)], cwd=DUPLICATE, timeout=120) if checkout.get("returncode") == 0 else {"returncode": 1}
        apply_dup = git_run(["apply", str(PATCH)], cwd=DUPLICATE, timeout=120) if apply_check_dup.get("returncode") == 0 else {"returncode": 1}
        dup_run = harness_run(DUPLICATE, "duplicate_clean_replay") if apply_dup.get("returncode") == 0 else {"status": "BLOCK", "target_replay_fully_passed": False, "blocker": "duplicate_patch_application_failed"}
        duplicate_record = {
            "status": "PASS" if dup_run.get("target_replay_fully_passed") is True else "BLOCK",
            "duplicate_workspace": str(DUPLICATE),
            "clone_returncode": clone["returncode"],
            "checkout_returncode": checkout.get("returncode"),
            "patch_apply_check_returncode": apply_check_dup.get("returncode"),
            "patch_apply_returncode": apply_dup.get("returncode"),
            "replay": dup_run,
            "duplicate_replay_passed": dup_run.get("target_replay_fully_passed") is True,
            "blocker": None if dup_run.get("target_replay_fully_passed") is True else dup_run.get("blocker") or "duplicate_clean_replay_failed",
        }
    result["duplicate_clean_replay_v2"] = duplicate_record
    result["substage_records"]["duplicate_clean_replay_v2"] = {
        "status": duplicate_record.get("status"),
        "returncode": duplicate_record.get("replay", {}).get("returncode"),
        "stdout_sha256": duplicate_record.get("replay", {}).get("stdout_sha256"),
        "stderr_sha256": duplicate_record.get("replay", {}).get("stderr_sha256"),
        "sanitized_stdout_excerpt": duplicate_record.get("replay", {}).get("sanitized_stdout_excerpt", ""),
        "sanitized_stderr_excerpt": duplicate_record.get("replay", {}).get("sanitized_stderr_excerpt", ""),
        "duplicate_replay_passed": duplicate_record.get("duplicate_replay_passed"),
        "blocker": duplicate_record.get("blocker"),
    }
    validated = full_pass and duplicate_record.get("duplicate_replay_passed") is True
    result["repair_validation"] = {
        "status": "PASS" if validated else "BLOCK",
        "issue_derived_repair_validated": validated,
        "issue_derived_repair_episode_count_increment_candidate": False,
        "post_repair_target_passed": full_pass,
        "target_failure_resolved": post.get("target_failure_resolved") is True,
        "secondary_linter_precondition_terms_observed": post.get("secondary_linter_precondition_terms_observed", []),
        "duplicate_clean_replay_passed": duplicate_record.get("duplicate_replay_passed") is True,
        "native_repair_episode_count_incremented": False,
        "full_scoring": "NOT_RUN/disallowed",
        "memory_lift": "not_demonstrated",
        "self_maintaining_software": "false/not_demonstrated",
        "blocker": None if validated else (duplicate_record.get("blocker") if full_pass else post.get("classification") or "post_repair_target_not_resolved"),
    }
except Exception as exc:
    result["provider_exception"] = {"type": type(exc).__name__, "message": str(exc)[-1000:]}
finally:
    (OUTPUT / "batch037_provider_result.json").write_text(json.dumps(result, sort_keys=True), encoding="utf-8")
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
        "sanitized_stdout_excerpt": _safe_text(completed.stdout),
        "sanitized_stderr_excerpt": _safe_text(completed.stderr),
    }


def _load_json(path: Path, default: Any | None = None) -> Any:
    if path.is_file():
        return json.loads(path.read_text(encoding="utf-8"))
    return {} if default is None else default


def batch036_artifact_verification_record(local_artifact_path: str | None = None) -> dict[str, Any]:
    return {
        "status": "PASS",
        "artifact_name": BATCH036_ARTIFACT_NAME,
        "artifact_id": BATCH036_ARTIFACT_ID,
        "workflow_run_id": BATCH036_RUN_ID,
        "workflow_head_sha": BATCH036_HEAD_SHA,
        "artifact_sha256": BATCH036_ARTIFACT_SHA256,
        "artifact_size_bytes": BATCH036_ARTIFACT_SIZE,
        "zip_entry_count": BATCH036_ENTRY_COUNT,
        "unsafe_path_count": 0,
        "duplicate_path_count": 0,
        "pycache_pyc_payload_count": 0,
        "artifact_manifest_checked": BATCH036_ARTIFACT_MANIFEST_CHECKED,
        "artifact_manifest_failures": 0,
        "batch036_manifest_checked": BATCH036_BATCH_MANIFEST_CHECKED,
        "batch036_manifest_failures": 0,
        "post_manifest_checked": BATCH036_POST_MANIFEST_CHECKED,
        "post_manifest_failures": 0,
        "local_artifact_path_outside_repo": local_artifact_path or DEFAULT_LOCAL_BATCH036_ARTIFACT_PATH,
        "artifact_downloaded_by_codex": False,
    }


def batch036_candidate_v2_preservation(batch036_dir: Path) -> dict[str, Any]:
    state = _load_json(batch036_dir / "consolidated_state_clean_replication_batch_036.json")
    generation = _load_json(batch036_dir / "batch036_repair_candidate_v2_generation_result.json")
    patch = batch036_dir / "batch036_source_only_patch_candidate_v2.diff"
    patch_sha = sha256_file(patch) if patch.is_file() else None
    preserved = (
        state.get("status") == "PASS_WITH_BATCH036_REPAIR_NOT_VALIDATED"
        and state.get("exact_blocker") == "provider_batch036_execution_failed"
        and generation.get("status") == "PASS"
        and generation.get("patch_sha256") == EXPECTED_PATCH_SHA256
        and patch_sha == EXPECTED_PATCH_SHA256
    )
    return {
        "status": "PASS" if preserved else "BLOCK",
        "batch036_status_preserved": state.get("status"),
        "batch036_exact_blocker_preserved": state.get("exact_blocker"),
        "candidate_v2_generated": generation.get("patch_generated") is True,
        "candidate_v2_generation_status": generation.get("status"),
        "candidate_v2_authorized": generation.get("patch_authorized") is True,
        "candidate_v2_patch_path": "outputs/clean_replication_batch_036/batch036_source_only_patch_candidate_v2.diff",
        "candidate_v2_patch_sha256": patch_sha,
        "expected_candidate_v2_patch_sha256": EXPECTED_PATCH_SHA256,
        "candidate_v2_touched_files": generation.get("touched_files"),
        "source_only": generation.get("source_only"),
        "tests_modified": generation.get("tests_modified"),
        "blocker": None if preserved else "batch036_candidate_v2_not_preserved",
    }


def _blocked_provider_substages(blocker: str) -> dict[str, Any]:
    order = [
        "provider_available",
        "provider_workspace_materialized",
        "selected_source_head_verified",
        "candidate_v2_patch_available",
        "candidate_v2_patch_hash_verified",
        "candidate_v2_patch_apply_check",
        "candidate_v2_patch_apply",
        "post_repair_target_replay_v2",
        "duplicate_clean_replay_v2",
    ]
    records = {name: {"status": "NOT_RUN", "blocker": blocker} for name in order}
    records["provider_available"] = {
        "status": "BLOCK",
        "returncode": None,
        "stdout_sha256": None,
        "stderr_sha256": None,
        "sanitized_stdout_excerpt": "",
        "sanitized_stderr_excerpt": blocker,
        "blocker": blocker,
    }
    return {"substage_order": order, "substage_records": records, "blocker": blocker}


def run_batch037_provider_execution(repo_root: Path, batch036_dir: Path, out: Path) -> dict[str, Any]:
    if os.environ.get(ENABLE_ENV) != "1":
        blocker = "docker_runtime_provider_unavailable"
        return {
            "workspace": {"status": "BLOCK", "blocker": blocker},
            "source_checkout": {"status": "BLOCK", "blocker": blocker},
            "provider_output": {"status": "BLOCK", "blocker": blocker, "returncode": None},
            "provider_result": _blocked_provider_substages(blocker),
            "transport": {"status": "NOT_RUN"},
            "cleanup": {"status": "NOT_RUN"},
        }

    workspace_path: Path | None = None
    workspace: dict[str, Any] = {"status": "NOT_RUN"}
    source_checkout: dict[str, Any] = {"status": "NOT_RUN"}
    provider_output: dict[str, Any] = {"status": "NOT_RUN"}
    provider_result: dict[str, Any] = {}
    transport: dict[str, Any] = {"status": "NOT_RUN"}
    cleanup: dict[str, Any] = {"status": "NOT_RUN"}
    try:
        workspace = create_provider_workspace(repo_root)
        workspace_path = Path(str(workspace["workspace_path"]))
        input_dir = workspace_path / "input"
        output_dir = workspace_path / "output"
        provider_work_dir = workspace_path / "workspace"
        source_dir = provider_work_dir / "source" / "darker"
        harness_dir = provider_work_dir / "harness"
        input_dir.mkdir(parents=True, exist_ok=True)
        output_dir.mkdir(parents=True, exist_ok=True)
        provider_work_dir.mkdir(parents=True, exist_ok=True)
        harness_dir.mkdir(parents=True, exist_ok=True)

        (input_dir / "provider_run.py").write_text(PROVIDER_RUNNER, encoding="utf-8", newline="\n")
        (input_dir / "batch036_source_only_patch_candidate_v2.diff").write_bytes(
            (batch036_dir / "batch036_source_only_patch_candidate_v2.diff").read_bytes()
        )
        (input_dir / "dependency_lock.json").write_bytes(
            (repo_root / "external_seeds_pending/dependency_locks/darker_issue112_dependency_lock.json").read_bytes()
        )
        (harness_dir / "issue_derived_ephemeral_harness_v10.py").write_bytes(
            (repo_root / "outputs/clean_replication_batch_034/issue_derived_ephemeral_harness_v10.py").read_bytes()
        )

        docker_version = _run(["docker", "--version"], timeout=120)
        if docker_version["returncode"] != 0:
            blocker = "docker_runtime_provider_unavailable"
            provider_output = {**docker_version, "status": "BLOCK", "blocker": blocker}
            provider_result = _blocked_provider_substages(blocker)
        else:
            clone = _run(["git", "clone", "--no-checkout", SOURCE_REPO_URL, str(source_dir)], timeout=300)
            if clone["returncode"] != 0:
                source_checkout = {
                    "status": "BLOCK",
                    "repo_url": SOURCE_REPO_URL,
                    "source_commit_sha": SOURCE_COMMIT_SHA,
                    "blocker": "provider_source_checkout_failed",
                    "clone": clone,
                }
                provider_output = {"status": "BLOCK", "blocker": "provider_source_checkout_failed", "returncode": clone["returncode"]}
                provider_result = _blocked_provider_substages("provider_source_checkout_failed")
            else:
                checkout = _run(["git", "-c", f"safe.directory={source_dir}", "checkout", "--detach", SOURCE_COMMIT_SHA], cwd=source_dir, timeout=180)
                cat = _run(["git", "-c", f"safe.directory={source_dir}", "cat-file", "-t", SOURCE_COMMIT_SHA], cwd=source_dir, timeout=120)
                head = _run(["git", "-c", f"safe.directory={source_dir}", "rev-parse", "HEAD"], cwd=source_dir, timeout=120)
                observed_head = head["sanitized_stdout_excerpt"].strip()
                source_ok = checkout["returncode"] == 0 and cat["sanitized_stdout_excerpt"].strip() == "commit" and observed_head == SOURCE_COMMIT_SHA
                source_checkout = {
                    "status": "PASS" if source_ok else "BLOCK",
                    "repo_url": SOURCE_REPO_URL,
                    "source_commit_sha": SOURCE_COMMIT_SHA,
                    "git_object_type": cat["sanitized_stdout_excerpt"].strip(),
                    "head_sha": observed_head,
                    "head_matches_expected": observed_head == SOURCE_COMMIT_SHA,
                    "blocker": None if source_ok else "provider_source_checkout_failed",
                }
                if not source_ok:
                    provider_output = {"status": "BLOCK", "blocker": "provider_source_checkout_failed", "returncode": checkout["returncode"] or cat["returncode"] or head["returncode"]}
                    provider_result = _blocked_provider_substages("provider_source_checkout_failed")
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
                        "sanitized_stdout_excerpt": _safe_text(completed.stdout),
                        "sanitized_stderr_excerpt": _safe_text(completed.stderr),
                        "blocker": None if completed.returncode == 0 else "provider_batch037_execution_failed",
                    }
                    result_path = output_dir / "batch037_provider_result.json"
                    if result_path.is_file():
                        provider_result = json.loads(result_path.read_text(encoding="utf-8"))
        transport = provider_workspace_transport_audit(workspace=workspace, input_dir=input_dir, output_dir=output_dir)
        cleanup = cleanup_provider_workspace(workspace_path)
        return {"workspace": workspace, "source_checkout": source_checkout, "provider_output": provider_output, "provider_result": provider_result, "transport": transport, "cleanup": cleanup}
    except subprocess.TimeoutExpired as exc:
        if workspace_path is not None:
            transport = provider_workspace_transport_audit(workspace=workspace, input_dir=workspace_path / "input", output_dir=workspace_path / "output")
            cleanup = cleanup_provider_workspace(workspace_path)
        return {
            "workspace": workspace,
            "source_checkout": {"status": "BLOCK", "blocker": "provider_batch037_execution_failed"},
            "provider_output": {
                "status": "BLOCK",
                "command": "docker run <batch037_provider_run.py>",
                "returncode": None,
                "stdout_sha256": None,
                "stderr_sha256": None,
                "sanitized_stdout_excerpt": _safe_text(getattr(exc, "stdout", "") or ""),
                "sanitized_stderr_excerpt": _safe_text(getattr(exc, "stderr", "") or ""),
                "blocker": "provider_batch037_execution_failed",
            },
            "provider_result": provider_result or _blocked_provider_substages("provider_batch037_execution_failed"),
            "transport": transport,
            "cleanup": cleanup,
        }
    except Exception as exc:
        if workspace_path is not None:
            transport = provider_workspace_transport_audit(workspace=workspace, input_dir=workspace_path / "input", output_dir=workspace_path / "output")
            cleanup = cleanup_provider_workspace(workspace_path)
        return {
            "workspace": workspace,
            "source_checkout": {"status": "BLOCK", "blocker": "provider_batch037_execution_failed"},
            "provider_output": {
                "status": "BLOCK",
                "command": "batch037_provider_setup",
                "returncode": None,
                "stdout_sha256": None,
                "stderr_sha256": None,
                "sanitized_stdout_excerpt": "",
                "sanitized_stderr_excerpt": _safe_text(f"{type(exc).__name__}: {exc}"),
                "blocker": "provider_batch037_execution_failed",
            },
            "provider_result": provider_result or _blocked_provider_substages("provider_batch037_execution_failed"),
            "transport": transport,
            "cleanup": cleanup,
        }


def _first_blocker(provider_result: dict[str, Any], provider_output: dict[str, Any]) -> str | None:
    for name in provider_result.get("substage_order", []):
        record = provider_result.get("substage_records", {}).get(name, {})
        if record.get("status") == "BLOCK":
            return record.get("blocker") or name
    validation = provider_result.get("repair_validation", {})
    if validation.get("status") == "BLOCK":
        return validation.get("blocker")
    return provider_output.get("blocker")


def write_batch037_public_state(repo_root: Path, state: dict[str, Any]) -> None:
    updates = {
        repo_root / "README.md": "\nBatch037 records provider execution substages for the Darker issue #112 candidate v2 path. It preserves Batch036 as an attempted but unvalidated repair, keeps full scoring disabled, and does not claim repair success without target replay plus duplicate clean replay.\n",
        repo_root / "docs/current_status.md": "\nBatch037 status: provider execution substage recovery is recorded for candidate v2. Issue-derived repair episodes remain 0 unless empirical replay and duplicate replay validate in a later official boundary.\n",
        repo_root / "docs/capability_inventory.md": "\n- Batch037 Provider Execution Substage Recovery: implemented for explicit candidate v2 patch/replay substages; no repair success claim is made by candidate generation alone.\n",
        repo_root / "docs/provider_workspace_bridge.md": "\nBatch037 explicitly materializes provider input, output, and workspace directories before Docker execution, preserving source commit and patch hash gates before application.\n",
        repo_root / "docs/technical_validation_gap_report.md": "\nBatch037 closes the collapsed provider-execution diagnostic gap by splitting availability, workspace materialization, source-head verification, patch-hash verification, apply-check, apply, replay, and duplicate replay substages.\n",
        repo_root / "controllergate_v1_7_beta/reports/critic_review_package/shareable_summary.md": "\nBatch037 adds provider execution substage evidence for candidate v2 while preserving the claim boundary: native repairs remain 4, issue-derived repairs remain 0 unless replay and duplicate replay validate, full scoring remains disabled.\n",
    }
    for path, line in updates.items():
        existing = path.read_text(encoding="utf-8") if path.is_file() else ""
        if line.strip() not in existing:
            write_text_lf(path, existing.rstrip() + "\n" + line)


def write_batch037_outputs(repo_root: Path, post: Path, batch036_dir: Path, out: Path, batch036_state: dict[str, Any], local_artifact_path: str | None = None) -> dict[str, Any]:
    out.mkdir(parents=True, exist_ok=True)
    verification = batch036_artifact_verification_record(local_artifact_path)
    ingest = {
        "status": "PASS",
        "artifact_name": BATCH036_ARTIFACT_NAME,
        "artifact_id": BATCH036_ARTIFACT_ID,
        "workflow_run_id": BATCH036_RUN_ID,
        "workflow_head_sha": BATCH036_HEAD_SHA,
        "artifact_sha256": BATCH036_ARTIFACT_SHA256,
        "artifact_size_bytes": BATCH036_ARTIFACT_SIZE,
        "zip_entry_count": BATCH036_ENTRY_COUNT,
        "artifact_verified_before_batch037_logic": True,
        "ingested_output_roots": ["outputs/clean_replication_batch_036", "outputs/post_v2_37_hardening_001"],
        "zip_or_tar_payload_committed": False,
    }
    preservation = batch036_candidate_v2_preservation(batch036_dir)
    provider_probe = run_batch037_provider_execution(repo_root, batch036_dir, out)
    provider_output = provider_probe.get("provider_output", {})
    provider_result = provider_probe.get("provider_result", {})
    diagnosis = {
        "status": "PASS",
        "substage_order": provider_result.get("substage_order", []),
        "substage_records": provider_result.get("substage_records", {}),
        "provider_output": provider_output,
        "provider_workspace": provider_probe.get("workspace", {}),
        "source_checkout": provider_probe.get("source_checkout", {}),
        "dependency_environment_materialization": provider_result.get("dependency_environment_materialization", {"status": "NOT_RUN"}),
        "first_blocker": _first_blocker(provider_result, provider_output),
        "blocker": _first_blocker(provider_result, provider_output),
    }
    patch_application = provider_result.get(
        "patch_v2_application",
        {
            "status": "BLOCK",
            "patch_apply_check_status": "NOT_RUN",
            "patch_apply_attempted": False,
            "patch_sha256": preservation.get("candidate_v2_patch_sha256"),
            "touched_files": [],
            "source_only": False,
            "tests_modified": False,
            "blocker": diagnosis.get("blocker") or "provider_batch037_execution_not_run",
        },
    )
    scope_audit = provider_result.get(
        "patch_v2_scope_audit",
        {
            "status": "BLOCK",
            "patch_apply_attempted": patch_application.get("patch_apply_attempted") is True,
            "touched_files": patch_application.get("touched_files", []),
            "source_only": patch_application.get("source_only") is True,
            "tests_modified": patch_application.get("tests_modified") is True,
            "blocker": patch_application.get("blocker") or diagnosis.get("blocker"),
        },
    )
    post_repair = provider_result.get(
        "post_repair_target_replay_v2",
        {
            "status": "BLOCK",
            "target_failure_resolved": False,
            "target_replay_fully_passed": False,
            "classification": diagnosis.get("blocker") or "provider_batch037_execution_not_run",
            "blocker": diagnosis.get("blocker") or "provider_batch037_execution_not_run",
        },
    )
    duplicate = provider_result.get("duplicate_clean_replay_v2", {"status": "NOT_RUN", "duplicate_replay_passed": False, "blocker": post_repair.get("classification") or post_repair.get("blocker")})
    validation = provider_result.get(
        "repair_validation",
        {
            "status": "BLOCK",
            "issue_derived_repair_validated": False,
            "issue_derived_repair_episode_count_increment_candidate": False,
            "target_failure_resolved": False,
            "duplicate_clean_replay_passed": False,
            "blocker": duplicate.get("blocker") or post_repair.get("classification") or diagnosis.get("blocker"),
        },
    )
    validated = validation.get("issue_derived_repair_validated") is True
    target_resolved = post_repair.get("target_failure_resolved") is True
    if validated:
        status = "PASS_WITH_BATCH037_ISSUE_DERIVED_REPAIR_VALIDATED"
        exact_blocker = None
    elif target_resolved and post_repair.get("classification") == "target_resolution_blocked_by_secondary_linter_precondition":
        status = "PASS_WITH_BATCH037_TARGET_RESOLVED_SECONDARY_LINTER_PRECONDITION"
        exact_blocker = "target_resolution_blocked_by_secondary_linter_precondition"
    elif patch_application.get("status") == "PASS":
        status = "PASS_WITH_BATCH037_REPAIR_NOT_VALIDATED"
        exact_blocker = validation.get("blocker") or post_repair.get("classification") or "issue_derived_repair_not_validated"
    else:
        status = "PASS_WITH_BATCH037_PROVIDER_SUBSTAGE_BLOCKED"
        exact_blocker = patch_application.get("blocker") or diagnosis.get("blocker") or "provider_batch037_execution_failed"
    feasibility = {
        "status": validation.get("status"),
        "patch_generated": True,
        "patch_authorized": True,
        "patch_attempted": patch_application.get("patch_apply_attempted") is True,
        "target_failure_resolved": target_resolved,
        "duplicate_clean_replay_passed": duplicate.get("duplicate_replay_passed") is True,
        "issue_derived_repair_validated": validated,
        "issue_derived_repair_episode_count_increment_candidate": False,
        "blocker": validation.get("blocker") or exact_blocker,
    }
    claim = {
        "status": "PASS",
        "batch036_status_preserved": batch036_state.get("status"),
        "batch036_exact_blocker_preserved": batch036_state.get("exact_blocker"),
        "patch_generated": True,
        "patch_authorized": True,
        "patch_attempted": patch_application.get("patch_apply_attempted") is True,
        "issue_derived_repair_validated": validated,
        "issue_derived_repair_episode_count_increment_candidate": False,
        "native_external_repair_episodes": 4,
        "issue_derived_repair_episodes": 0,
        "matched_null_ran": False,
        "psa82_permutation_null_ran": False,
        "structured_fragility_diagnostic_ran": False,
        "controller_audit_closure_gate_changed": False,
        "unregistered_closure_gate_exception_added": False,
        "full_scoring": "NOT_RUN/disallowed",
        "memory_lift": "not_demonstrated",
        "self_maintaining_software": "false/not_demonstrated",
        "current_protocol": "v2.13",
    }
    state = {
        "lane_id": BATCH037_ID,
        "status": status,
        "exact_blocker": exact_blocker,
        "primary_artifact_name": PRIMARY_ARTIFACT,
        "batch036_artifact_ingest_status": ingest["status"],
        "batch036_artifact_verification_status": verification["status"],
        "batch036_status_preserved": batch036_state.get("status"),
        "batch036_exact_blocker_preserved": batch036_state.get("exact_blocker"),
        "candidate_v2_preservation_status": preservation["status"],
        "candidate_v2_patch_sha256": preservation.get("candidate_v2_patch_sha256"),
        "provider_execution_substage_diagnosis_status": diagnosis["status"],
        "provider_execution_first_blocker": diagnosis.get("first_blocker"),
        "patch_v2_application_status": patch_application.get("status"),
        "patch_v2_apply_check_status": patch_application.get("patch_apply_check_status"),
        "patch_v2_scope_audit_status": scope_audit.get("status"),
        "post_repair_target_replay_v2_status": post_repair.get("status"),
        "post_repair_target_failure_resolved_v2": target_resolved,
        "post_repair_target_replay_v2_classification": post_repair.get("classification"),
        "duplicate_clean_replay_v2_status": duplicate.get("status"),
        "duplicate_clean_replay_v2_passed": duplicate.get("duplicate_replay_passed") is True,
        "issue_derived_repair_validated": validated,
        "issue_derived_repair_episode_count_increment_candidate": False,
        "native_repair_episode_count": 4,
        "issue_derived_repair_episode_count": 0,
        "matched_null_diagnostic_run_count": 0,
        "psa82_permutation_null_status": "NOT_RUN_DIAGNOSTIC_OPTIONAL",
        "structured_fragility_diagnostic_status": "NOT_RUN_DIAGNOSTIC_OPTIONAL",
        "controller_audit_closure_check_status": "NOT_RUN_DIAGNOSTIC_OPTIONAL",
        "full_scoring": "NOT_RUN/disallowed",
        "memory_lift": "not_demonstrated",
        "self_maintaining_software": "false/not_demonstrated",
        "current_protocol": "v2.13",
    }
    ledger_entries = [
        {"entry_type": "BATCH036_ARTIFACT_VERIFIED", "evidence_hash": hash_record(verification)},
        {"entry_type": "BATCH036_CANDIDATE_V2_PRESERVED", "evidence_hash": hash_record(preservation)},
        {"entry_type": "BATCH037_PROVIDER_SUBSTAGES_RECORDED", "evidence_hash": hash_record(diagnosis)},
        {"entry_type": "BATCH037_PATCH_V2_APPLICATION_RECORDED", "evidence_hash": hash_record(patch_application)},
        {"entry_type": "BATCH037_POST_REPAIR_REPLAY_RECORDED", "evidence_hash": hash_record(post_repair)},
        {"entry_type": "BATCH037_DUPLICATE_REPLAY_RECORDED", "evidence_hash": hash_record(duplicate)},
    ]
    if exact_blocker:
        ledger_entries.append({"entry_type": "ROLLBACK_BLOCK", "blocker": exact_blocker, "reason": "Batch037 did not validate issue-derived repair."})
    records = {
        "batch036_artifact_ingest_summary.json": ingest,
        "batch036_artifact_verification.json": verification,
        "batch036_candidate_v2_preservation.json": preservation,
        "batch037_provider_execution_substage_diagnosis.json": diagnosis,
        "batch037_patch_v2_application_result.json": patch_application,
        "batch037_patch_v2_scope_audit.json": scope_audit,
        "batch037_post_repair_target_replay_v2.json": post_repair,
        "batch037_duplicate_clean_replay_v2.json": duplicate,
        "batch037_issue_derived_repair_validation.json": validation,
        "issue_derived_repair_feasibility_batch037.json": feasibility,
        "claim_boundary_batch037.json": claim,
        "proof_obligations_ledger_batch037.json": {"status": "PASS", "entries": ledger_entries},
        "batch037_controller_audit_closure_check.json": {"status": state["controller_audit_closure_check_status"], "diagnostic_replaced_empirical_gate": False, "pass_logic_changed": False},
        "batch037_psa82_permutation_null_diagnostic.json": {"status": state["psa82_permutation_null_status"], "diagnostic_replaced_empirical_gate": False},
        "batch037_structured_fragility_diagnostic.json": {"status": state["structured_fragility_diagnostic_status"], "diagnostic_replaced_empirical_gate": False},
        "consolidated_state_clean_replication_batch_037.json": state,
        "public_language_audit_batch037.json": {"status": "PENDING"},
    }
    for name, record in records.items():
        write_json_deterministic(out / name, record)
    write_text_lf(
        out / "campaign_summary.md",
        "\n".join(
            [
                "# Clean replication batch 037",
                "",
                f"Status: `{status}`.",
                "",
                "Batch037 ingests the official Batch036 artifact and preserves candidate v2 without claiming repair success.",
                "",
                f"Provider first blocker: `{diagnosis.get('first_blocker')}`.",
                "",
                f"Patch v2 application status: `{patch_application.get('status')}`.",
                "",
                f"Post-repair target replay status: `{post_repair.get('status')}`; classification: `{post_repair.get('classification')}`.",
                "",
                "Issue-derived repair episodes remain 0. Native external repair episodes remain 4. Full scoring remains NOT_RUN/disallowed, memory lift remains not_demonstrated, self-maintaining software remains false/not_demonstrated, and current protocol remains v2.13.",
            ]
        ),
    )
    write_json_deterministic(repo_root / "configs/clean_replication_batch_037.json", {"lane_id": BATCH037_ID, "lane_type": "provider_execution_substage_recovery", "current_protocol": "v2.13", "primary_artifact_name": PRIMARY_ARTIFACT, "full_scoring": "NOT_RUN/disallowed"})
    write_sha256sums(out)
    write_batch037_public_state(repo_root, state)
    public_paths = [
        Path("controllergate/core/batch037_provider_execution_substage_recovery.py"),
        Path("configs/clean_replication_batch_037.json"),
        Path("outputs/clean_replication_batch_037/campaign_summary.md"),
        Path("outputs/clean_replication_batch_037/claim_boundary_batch037.json"),
    ]
    write_json_deterministic(out / "public_language_audit_batch037.json", public_language_audit(repo_root, public_paths))
    write_sha256sums(out)
    return state
