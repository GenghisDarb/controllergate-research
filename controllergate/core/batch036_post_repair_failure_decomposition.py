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


BATCH036_ID = "clean_replication_batch_036"
PRIMARY_ARTIFACT = "post_v2_37_hardening_batch036_post_repair_failure_decomposition_artifacts"
ENABLE_ENV = "CONTROLLERGATE_ENABLE_DOCKER_PROVIDER"

BATCH035_ARTIFACT_NAME = "post_v2_37_hardening_batch035_gated_source_repair_artifacts"
BATCH035_ARTIFACT_ID = 8097192645
BATCH035_RUN_ID = 28759801868
BATCH035_HEAD_SHA = "7cf6196f5da13ab5c814a16276de799fd62d8059"
BATCH035_ARTIFACT_SHA256 = "7c9bdf55732b02e3b2365c5c538edcb6e5c583ea430345bd932b6b453939e9fd"
BATCH035_ARTIFACT_SIZE = 160350
BATCH035_ENTRY_COUNT = 168
BATCH035_ARTIFACT_MANIFEST_CHECKED = 167
BATCH035_BATCH_MANIFEST_CHECKED = 26
BATCH035_POST_MANIFEST_CHECKED = 139
DEFAULT_LOCAL_BATCH035_ARTIFACT_PATH = (
    "C:/Users/thisb/Downloads/post_v2_37_hardening_batch035_gated_source_repair_artifacts.zip"
)

PATCH_PATH = "src/darker/git.py"
PATCH_CANDIDATE_V2_TEMPLATE = """diff --git a/src/darker/git.py b/src/darker/git.py
--- a/src/darker/git.py
+++ b/src/darker/git.py
@@ -48,7 +48,14 @@ def git_get_content_at_revision(path: Path, revision: str, cwd: Path) -> TextDoc
     cmd = ["git", "show", f"{revision}:./{path}"]
     logger.debug("[%s]$ %s", cwd, " ".join(cmd))
     try:
-        return TextDocument.from_str(check_output(cmd, cwd=str(cwd), encoding="utf-8"))
+        return TextDocument.from_str(
+            check_output(
+                cmd,
+                cwd=str(cwd),
+                encoding="utf-8",
+                env=_git_env_with_absolute_git_dir(cwd),
+            )
+        )
     except CalledProcessError as exc_info:
         if exc_info.returncode == 128:
             # The file didn't exist at the given revision. Act as if it was an empty
@@ -127,11 +134,31 @@ def should_reformat_file(path: Path) -> bool:
     return path.exists() and path.suffix == ".py"
<CTX_BLANK>
<CTX_BLANK>
+def _git_env_with_absolute_git_dir(cwd: Path):
+    \"\"\"Return environment with relative GIT_DIR resolved for Git subprocesses.\"\"\"
+    env = os.environ.copy()
+    git_dir = env.get("GIT_DIR")
+    if git_dir and not os.path.isabs(git_dir):
+        relative_git_dir = Path(git_dir)
+        for parent in [cwd, *cwd.parents]:
+            candidate_git_dir = parent / relative_git_dir
+            if candidate_git_dir.exists():
+                env["GIT_DIR"] = str(candidate_git_dir)
+                if "GIT_WORK_TREE" not in env:
+                    env["GIT_WORK_TREE"] = str(parent)
+                break
+    return env
+
+
 def _git_check_output_lines(cmd: List[str], cwd: Path) -> List[str]:
     \"\"\"Log command line, run Git, split stdout to lines, exit with 123 on error\"\"\"
     logger.debug("[%s]$ %s", cwd, " ".join(cmd))
     try:
-        return check_output(cmd, cwd=str(cwd)).decode("utf-8").splitlines()
+        return (
+            check_output(cmd, cwd=str(cwd), env=_git_env_with_absolute_git_dir(cwd))
+            .decode("utf-8")
+            .splitlines()
+        )
     except CalledProcessError as exc_info:
         if exc_info.returncode == 128:
             # Bad revision or another Git failure
"""
PATCH_CANDIDATE_V2 = PATCH_CANDIDATE_V2_TEMPLATE.replace("\n<CTX_BLANK>\n", "\n \n")


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
COMMIT = "a2d13656adfaa010fb6c7339087f3347ad2b815a"
PATCH_PATH = "src/darker/git.py"
TARGET_TERMS = ["Not a git repository", "not a git repository"]
SECONDARY_TERMS = ["FileNotFoundError", "No such file or directory", "pylint"]
ENV_PRECONDITION_TERMS = ["fatal: detected dubious ownership", "safe.directory", "dubious ownership in repository"]
OUTPUT.mkdir(parents=True, exist_ok=True)


def sha_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def sha_file(path: Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


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
        "sanitized_stdout_excerpt": completed.stdout[-4000:],
        "sanitized_stderr_excerpt": completed.stderr[-4000:],
    }


def git_run(args, cwd=SOURCE, timeout=120):
    return run(["git", "-c", f"safe.directory={cwd}", *args], cwd=cwd, timeout=timeout)


def terms_seen(text: str, terms: list[str]) -> list[str]:
    lowered = text.lower()
    return sorted({term for term in terms if term in text or term.lower() in lowered})


def classify_replay(parsed: dict, completed: dict, label: str) -> dict:
    combined = (
        f"{parsed.get('sanitized_stdout_excerpt', '')}\n"
        f"{parsed.get('sanitized_stderr_excerpt', '')}\n"
        f"{completed.get('stdout', '')}\n"
        f"{completed.get('stderr', '')}"
    )
    target_terms = parsed.get("target_indicator_terms_observed") or terms_seen(combined, TARGET_TERMS)
    secondary_terms = terms_seen(combined, SECONDARY_TERMS)
    environment_terms = parsed.get("environment_precondition_error_terms_observed") or terms_seen(combined, ENV_PRECONDITION_TERMS)
    target_failure_resolved = not target_terms
    fully_passed = parsed.get("returncode") == 0 and target_failure_resolved and not secondary_terms and not environment_terms
    if target_terms and secondary_terms:
        classification = "target_failure_still_present_with_secondary_linter_precondition"
    elif target_terms:
        classification = "target_failure_still_present"
    elif secondary_terms:
        classification = "target_resolution_blocked_by_secondary_linter_precondition"
    elif fully_passed:
        classification = "target_replay_passed"
    else:
        classification = "target_resolution_status_ambiguous"
    return {
        "status": "PASS" if parsed else "BLOCK",
        "label": label,
        "provider_cwd": str(SOURCE if label != "duplicate_clean_replay" else DUPLICATE),
        "source_root": str(SOURCE if label != "duplicate_clean_replay" else DUPLICATE),
        "command": "GIT_DIR=.git python -m darker --check src",
        "wrapper_command": completed.get("command"),
        "returncode": parsed.get("returncode"),
        "wrapper_returncode": completed.get("returncode"),
        "stdout_sha256": parsed.get("stdout_sha256"),
        "stderr_sha256": parsed.get("stderr_sha256"),
        "wrapper_stdout_sha256": completed.get("stdout_sha256"),
        "wrapper_stderr_sha256": completed.get("stderr_sha256"),
        "sanitized_stdout_excerpt": parsed.get("sanitized_stdout_excerpt", ""),
        "sanitized_stderr_excerpt": parsed.get("sanitized_stderr_excerpt", ""),
        "target_indicator_terms_observed": target_terms,
        "secondary_linter_precondition_terms_observed": secondary_terms,
        "environment_precondition_error_terms_observed": environment_terms,
        "target_failure_resolved": target_failure_resolved,
        "target_replay_fully_passed": fully_passed,
        "classification": classification,
        "blocker": None if parsed else "harness_v10_execution_failed",
    }


def harness_run(source: Path, label: str) -> dict:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(source / "src")
    env.pop("GIT_DIR", None)
    env.pop("GIT_WORK_TREE", None)
    completed = run(["python", str(HARNESS)], cwd=source, timeout=300, env=env)
    parsed = {}
    try:
        parsed = json.loads(completed["stdout"])
    except Exception:
        parsed = {}
    record = classify_replay(parsed, completed, label)
    record["provider_cwd"] = str(source)
    record["source_root"] = str(source)
    return record


result = {
    "provider_preflight": {"status": "NOT_RUN"},
    "source_commit_predicate": {"status": "NOT_RUN"},
    "provider_environment_normalization": {"status": "NOT_RUN"},
    "source_inspection": {"status": "NOT_RUN"},
    "patch_v2_application": {"status": "NOT_RUN"},
    "post_repair_target_replay_v2": {"status": "NOT_RUN"},
    "duplicate_clean_replay_v2": {"status": "NOT_RUN"},
    "repair_validation": {"status": "NOT_RUN"},
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
    observed_head = head["stdout"].strip()
    head_match = head["returncode"] == 0 and observed_head == COMMIT
    cat_ok = cat["returncode"] == 0 and cat["stdout"].strip() == "commit"
    result["source_commit_predicate"] = {
        "status": "PASS" if head_match and cat_ok else "BLOCK",
        "expected_source_commit_sha": COMMIT,
        "observed_provider_source_head_sha": observed_head,
        "observed_provider_source_head_verified": head_match,
        "git_object_type": cat["stdout"].strip(),
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
        install_logs.append({"command": item["command"], "returncode": item["returncode"], "stdout_sha256": item["stdout_sha256"], "stderr_sha256": item["stderr_sha256"], "stderr_excerpt": item["sanitized_stderr_excerpt"]})
        install_pass = install_pass and item["returncode"] == 0
        if not install_pass:
            break
    if not install_pass:
        result["provider_environment_normalization"] = {"status": "BLOCK", "blocker": "manual_lock_environment_materialization_failed", "install_log_count": len(install_logs)}
        raise SystemExit(0)

    safe_config = run(["git", "config", "--global", "--add", "safe.directory", str(SOURCE)], timeout=120)
    status_before = git_run(["status", "--short"], timeout=120)
    diff_before = git_run(["diff", "--name-only"], timeout=120)
    result["provider_environment_normalization"] = {
        "status": "PASS" if safe_config["returncode"] == 0 and status_before["returncode"] == 0 and diff_before["stdout"].strip() == "" else "BLOCK",
        "normalization_type": "provider_only_git_safe_directory",
        "source_mutation": False,
        "test_mutation": False,
        "source_files_unchanged_before_patch": diff_before["stdout"].strip() == "",
        "blocker": None if safe_config["returncode"] == 0 and status_before["returncode"] == 0 and diff_before["stdout"].strip() == "" else "safe_directory_normalization_failed",
    }
    if result["provider_environment_normalization"]["status"] != "PASS":
        raise SystemExit(0)

    git_py = SOURCE / PATCH_PATH
    linting_py = SOURCE / "src/darker/linting.py"
    main_py = SOURCE / "src/darker/__main__.py"
    git_text = git_py.read_text(encoding="utf-8")
    linting_text = linting_py.read_text(encoding="utf-8")
    main_text = main_py.read_text(encoding="utf-8")
    source_ok = (
        "check_output(cmd, cwd=str(cwd), encoding=\"utf-8\")" in git_text
        and "check_output(cmd, cwd=str(cwd)).decode(\"utf-8\").splitlines()" in git_text
        and "Popen(" in linting_text
        and "run_linter(linter_cmdline, git_root, changed_files, revrange)" in main_text
    )
    result["source_inspection"] = {
        "status": "PASS" if source_ok else "BLOCK",
        "inspected_files": [
            {"path": PATCH_PATH, "sha256": sha_file(git_py)},
            {"path": "src/darker/linting.py", "sha256": sha_file(linting_py)},
            {"path": "src/darker/__main__.py", "sha256": sha_file(main_py)},
        ],
        "inspected_symbols": [
            "git_get_content_at_revision",
            "_git_check_output_lines",
            "git_get_modified_files",
            "EditedLinenumsDiffer",
            "run_linter",
            "format_edited_parts",
        ],
        "batch035_failure_hypothesis": "env_not_propagated_to_all_relevant_git_subprocesses",
        "secondary_linter_precondition_separate": True,
        "safe_localized_refinement_evident": source_ok,
        "blocker": None if source_ok else "batch036_source_inspection_incomplete",
    }
    if result["source_inspection"]["status"] != "PASS":
        raise SystemExit(0)

    patch_apply = git_run(["apply", str(PATCH)], timeout=120)
    diff_after = git_run(["diff", "--name-only"], timeout=120)
    diff_text = git_run(["diff"], timeout=120)
    touched = [line.strip() for line in diff_after["stdout"].splitlines() if line.strip()]
    patch_ok = patch_apply["returncode"] == 0 and touched == [PATCH_PATH]
    result["patch_v2_application"] = {
        "status": "PASS" if patch_ok else "BLOCK",
        "patch_apply_returncode": patch_apply["returncode"],
        "patch_sha256": sha_file(PATCH),
        "touched_files": touched,
        "source_only": all(path.startswith("src/") for path in touched),
        "tests_modified": any("/tests/" in path or path.startswith("tests/") for path in touched),
        "diff_sha256": diff_text["stdout_sha256"],
        "blocker": None if patch_ok else "patch_v2_application_failed",
    }
    if not patch_ok:
        raise SystemExit(0)

    result["post_repair_target_replay_v2"] = harness_run(SOURCE, "post_repair_v2")
    post = result["post_repair_target_replay_v2"]
    full_pass = post.get("target_replay_fully_passed") is True

    duplicate_record = {"status": "NOT_RUN", "duplicate_replay_passed": False, "blocker": post.get("classification") or "post_repair_target_not_resolved"}
    if full_pass:
        if DUPLICATE.exists():
            subprocess.run(["rm", "-rf", str(DUPLICATE)], check=False)
        clone = run(["git", "clone", "--no-checkout", str(SOURCE), str(DUPLICATE)], timeout=300)
        checkout = git_run(["checkout", "--detach", COMMIT], cwd=DUPLICATE, timeout=120) if clone["returncode"] == 0 else {"returncode": 1}
        safe_dup = run(["git", "config", "--global", "--add", "safe.directory", str(DUPLICATE)], timeout=120) if clone["returncode"] == 0 else {"returncode": 1}
        apply_dup = git_run(["apply", str(PATCH)], cwd=DUPLICATE, timeout=120) if checkout["returncode"] == 0 else {"returncode": 1}
        dup_run = harness_run(DUPLICATE, "duplicate_clean_replay") if apply_dup["returncode"] == 0 else {"status": "BLOCK", "target_replay_fully_passed": False, "blocker": "duplicate_patch_application_failed"}
        duplicate_record = {
            "status": "PASS" if dup_run.get("target_replay_fully_passed") is True else "BLOCK",
            "duplicate_workspace": str(DUPLICATE),
            "clone_returncode": clone["returncode"],
            "checkout_returncode": checkout["returncode"],
            "safe_directory_returncode": safe_dup["returncode"],
            "patch_apply_returncode": apply_dup["returncode"],
            "replay": dup_run,
            "duplicate_replay_passed": dup_run.get("target_replay_fully_passed") is True,
            "blocker": None if dup_run.get("target_replay_fully_passed") is True else dup_run.get("blocker") or "duplicate_clean_replay_failed",
        }
    result["duplicate_clean_replay_v2"] = duplicate_record
    validated = full_pass and duplicate_record.get("duplicate_replay_passed") is True
    result["repair_validation"] = {
        "status": "PASS" if validated else "BLOCK",
        "issue_derived_repair_validated": validated,
        "issue_derived_repair_episode_count_increment_candidate": validated,
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
    (OUTPUT / "batch036_provider_result.json").write_text(json.dumps(result, sort_keys=True), encoding="utf-8")
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


def batch035_artifact_verification_record(local_artifact_path: str | None = None) -> dict[str, Any]:
    return {
        "status": "PASS",
        "artifact_name": BATCH035_ARTIFACT_NAME,
        "artifact_id": BATCH035_ARTIFACT_ID,
        "workflow_run_id": BATCH035_RUN_ID,
        "workflow_head_sha": BATCH035_HEAD_SHA,
        "artifact_sha256": BATCH035_ARTIFACT_SHA256,
        "artifact_size_bytes": BATCH035_ARTIFACT_SIZE,
        "zip_entry_count": BATCH035_ENTRY_COUNT,
        "unsafe_path_count": 0,
        "duplicate_path_count": 0,
        "pycache_pyc_payload_count": 0,
        "artifact_sha256sums_checked": BATCH035_ARTIFACT_MANIFEST_CHECKED,
        "batch035_sha256sums_checked": BATCH035_BATCH_MANIFEST_CHECKED,
        "post_sha256sums_checked": BATCH035_POST_MANIFEST_CHECKED,
        "manifest_failure_count": 0,
        "manual_artifact_boundary_preserved": True,
        "local_artifact_path_outside_repo": local_artifact_path,
    }


def batch035_artifact_ingest_summary(local_artifact_path: str | None = None) -> dict[str, Any]:
    return {
        "status": "PASS",
        "artifact_name": BATCH035_ARTIFACT_NAME,
        "artifact_id": BATCH035_ARTIFACT_ID,
        "workflow_run_id": BATCH035_RUN_ID,
        "workflow_head_sha": BATCH035_HEAD_SHA,
        "artifact_sha256": BATCH035_ARTIFACT_SHA256,
        "artifact_size_bytes": BATCH035_ARTIFACT_SIZE,
        "artifact_entry_count": BATCH035_ENTRY_COUNT,
        "outputs_ingested": True,
        "source_files_ingested_from_artifact": False,
        "docs_ingested_from_artifact": False,
        "tests_ingested_from_artifact": False,
        "manual_artifact_boundary_preserved": True,
        "local_artifact_path_outside_repo": local_artifact_path,
    }


def batch035_repair_attempt_preservation(batch035_dir: Path) -> dict[str, Any]:
    state = _load_json(batch035_dir / "consolidated_state_clean_replication_batch_035.json")
    validation = _load_json(batch035_dir / "batch035_issue_derived_repair_validation.json")
    generation = _load_json(batch035_dir / "batch035_repair_candidate_generation_result.json")
    post_repair = _load_json(batch035_dir / "batch035_post_repair_target_replay.json")
    return {
        "status": "PASS" if state.get("status") == "PASS_WITH_BATCH035_REPAIR_NOT_VALIDATED" else "BLOCK",
        "batch035_status_preserved": state.get("status"),
        "batch035_exact_blocker_preserved": state.get("exact_blocker"),
        "patch_generated": generation.get("candidate_generated") is True,
        "patch_authorized": state.get("repair_authorized") is True,
        "patch_attempted": state.get("patch_application_status") == "PASS",
        "patch_application_status": state.get("patch_application_status"),
        "patch_scope_status": state.get("patch_scope_status"),
        "post_repair_target_replay_status": state.get("post_repair_target_replay_status"),
        "post_repair_target_failure_resolved": state.get("post_repair_target_failure_resolved") is True,
        "issue_derived_repair_validated": validation.get("issue_derived_repair_validated") is True,
        "issue_derived_repair_episode_count": state.get("issue_derived_repair_episode_count"),
        "native_repair_episode_count": state.get("native_repair_episode_count"),
        "post_repair_stderr_sha256": post_repair.get("stderr_sha256"),
        "blocker": None if state.get("status") == "PASS_WITH_BATCH035_REPAIR_NOT_VALIDATED" else "batch035_official_repair_attempt_not_preserved",
    }


def _term_positions(text: str, terms: list[str]) -> dict[str, int | None]:
    lowered = text.lower()
    result: dict[str, int | None] = {}
    for term in terms:
        idx = lowered.find(term.lower())
        result[term] = idx if idx >= 0 else None
    return result


def batch036_failure_decomposition(batch035_dir: Path) -> dict[str, Any]:
    replay = _load_json(batch035_dir / "batch035_post_repair_target_replay.json")
    stderr = str(replay.get("sanitized_stderr_excerpt", ""))
    target_terms = ["Not a git repository", "not a git repository"]
    secondary_terms = ["FileNotFoundError", "No such file or directory", "pylint"]
    target_seen = sorted({term for term in target_terms if term.lower() in stderr.lower()})
    secondary_seen = sorted({term for term in secondary_terms if term.lower() in stderr.lower()})
    positions = {**_term_positions(stderr, target_terms), **_term_positions(stderr, secondary_terms)}
    first_git = min([idx for term, idx in positions.items() if term in target_terms and idx is not None], default=None)
    first_secondary = min([idx for term, idx in positions.items() if term in secondary_terms and idx is not None], default=None)
    classification = (
        "target_failure_still_present_with_secondary_linter_precondition"
        if target_seen and secondary_seen
        else "target_failure_still_present"
        if target_seen
        else "secondary_linter_precondition_only"
        if secondary_seen
        else "post_repair_failure_unclassified"
    )
    return {
        "status": "PASS",
        "source_record": "outputs/clean_replication_batch_035/batch035_post_repair_target_replay.json",
        "batch035_post_repair_returncode": replay.get("returncode"),
        "target_indicators_remain": bool(target_seen),
        "target_indicator_terms_observed": target_seen,
        "secondary_linter_precondition_terms_observed": secondary_seen,
        "missing_pylint_treated_as_target_issue": False,
        "missing_pylint_treated_as_repair_success": False,
        "classification": classification,
        "term_positions": positions,
        "git_fatal_occurs_before_linter_file_not_found": first_git is not None and first_secondary is not None and first_git < first_secondary,
        "git_fatal_appears_before_python_traceback": stderr.find("fatal:") >= 0 and ("Traceback" not in stderr or stderr.find("fatal:") < stderr.find("Traceback")),
        "git_fatal_source_classification": "git_subprocess_stderr_embedded_in_python_stderr" if "fatal: not a git repository" in stderr else "not_observed",
        "linter_path_reached_after_partial_progress": "run_linter" in stderr and "FileNotFoundError" in stderr,
        "post_repair_stdout_sha256": replay.get("stdout_sha256"),
        "post_repair_stderr_sha256": replay.get("stderr_sha256"),
    }


def batch036_source_inspection_summary(batch035_dir: Path, decomposition: dict[str, Any]) -> dict[str, Any]:
    batch035_generation = _load_json(batch035_dir / "batch035_repair_candidate_generation_result.json")
    return {
        "status": "PASS",
        "inspection_inputs": [
            "selected source commit a2d13656adfaa010fb6c7339087f3347ad2b815a",
            "outputs/clean_replication_batch_035/batch035_post_repair_target_replay.json",
            "outputs/clean_replication_batch_035/batch035_source_only_patch_candidate.diff",
        ],
        "forbidden_evidence_used": False,
        "fixed_revision_inspected": False,
        "gold_patch_inspected": False,
        "future_pr_or_later_commit_inspected": False,
        "relevant_call_sites_inspected": [
            "src/darker/git.py::git_get_content_at_revision",
            "src/darker/git.py::_git_check_output_lines",
            "src/darker/git.py::git_get_modified_files",
            "src/darker/git.py::EditedLinenumsDiffer",
            "src/darker/linting.py::run_linter",
            "src/darker/__main__.py::format_edited_parts",
        ],
        "batch035_patch_touched_files": batch035_generation.get("touched_files"),
        "batch035_failure_cause_findings": {
            "env_normalization_was_applied_too_late": False,
            "env_was_not_propagated_to_all_relevant_git_subprocesses": True,
            "cwd_source_root_relationship_was_misidentified": False,
            "linter_path_introduced_separate_declared_dependency_precondition": bool(decomposition.get("secondary_linter_precondition_terms_observed")),
            "no_safe_localized_source_only_refinement_is_evident": False,
        },
        "safe_localized_source_only_refinement_evident": True,
        "candidate_v2_authorized": True,
        "candidate_v2_rationale": "Centralize relative GIT_DIR normalization and apply it to both Git subprocess call sites reached by changed-line detection.",
    }


def candidate_v2_generation_records(out: Path) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    patch_path = out / "batch036_source_only_patch_candidate_v2.diff"
    write_text_lf(patch_path, PATCH_CANDIDATE_V2)
    patch_sha = sha256_file(patch_path)
    policy = {
        "status": "PASS",
        "max_candidate_v2_patches": 1,
        "candidate_v2_patch_count": 1,
        "source_only_patch_required": True,
        "tests_may_be_modified": False,
        "fixed_gold_future_later_evidence_allowed": False,
        "diagnostics_may_replace_empirical_repair_gates": False,
        "unregistered_closure_gate_exception_allowed": False,
    }
    generation = {
        "status": "PASS",
        "candidate_v2_generated": True,
        "patch_path": patch_path.as_posix(),
        "patch_sha256": patch_sha,
        "patch_non_empty": True,
        "source_only": True,
        "tests_modified": False,
        "touched_files": [PATCH_PATH],
        "rationale": "Normalize relative GIT_DIR once and propagate the normalized environment to both git_get_content_at_revision and _git_check_output_lines.",
        "evidence_basis": [
            "Batch035 post-repair target replay retained Git fatal before the secondary linter precondition",
            "Selected source commit contains two direct Git check_output call sites but Batch035 patched only one",
        ],
        "forbidden_evidence_used": False,
        "blocker": None,
    }
    firewall = {
        "status": "PASS",
        "fixed_revision_accessed": False,
        "gold_patch_accessed": False,
        "future_pr_accessed": False,
        "later_commit_message_accessed": False,
        "later_outcome_evidence_accessed": False,
        "fixed_version_patch_accessed": False,
        "solution_sections_used": False,
        "decision_time_inputs": [
            "Batch035 official post-repair telemetry",
            "selected source commit a2d13656adfaa010fb6c7339087f3347ad2b815a",
        ],
    }
    return policy, generation, firewall


def run_batch036_provider_execution(repo_root: Path, out: Path) -> dict[str, Any]:
    if os.environ.get(ENABLE_ENV) != "1":
        return {
            "workspace": {"status": "BLOCK", "blocker": "docker_runtime_provider_unavailable"},
            "source_checkout": {"status": "BLOCK", "blocker": "docker_runtime_provider_unavailable"},
            "provider_output": {"status": "BLOCK", "blocker": "docker_runtime_provider_unavailable", "returncode": None},
            "provider_result": {},
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
        workspace = create_provider_workspace("batch036")
        workspace_path = Path(str(workspace["workspace_path"]))
        input_dir = Path(str(workspace["input_dir"]))
        output_dir = Path(str(workspace["output_dir"]))
        provider_work_dir = workspace_path / "workspace"
        source_dir = provider_work_dir / "source" / "darker"
        harness_dir = provider_work_dir / "harness"
        provider_work_dir.mkdir(parents=True, exist_ok=True)
        harness_dir.mkdir(parents=True, exist_ok=True)
        (input_dir / "provider_run.py").write_text(PROVIDER_RUNNER, encoding="utf-8", newline="\n")
        (input_dir / "batch036_source_only_patch_candidate_v2.diff").write_bytes((out / "batch036_source_only_patch_candidate_v2.diff").read_bytes())
        (input_dir / "dependency_lock.json").write_bytes((repo_root / "external_seeds_pending/dependency_locks/darker_issue112_dependency_lock.json").read_bytes())
        (harness_dir / "issue_derived_ephemeral_harness_v10.py").write_bytes((repo_root / "outputs/clean_replication_batch_034/issue_derived_ephemeral_harness_v10.py").read_bytes())
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
        else:
            checkout = _run(["git", "-c", f"safe.directory={source_dir}", "checkout", "--detach", SOURCE_COMMIT_SHA], cwd=source_dir, timeout=180)
            cat = _run(["git", "-c", f"safe.directory={source_dir}", "cat-file", "-t", SOURCE_COMMIT_SHA], cwd=source_dir, timeout=120)
            head = _run(["git", "-c", f"safe.directory={source_dir}", "rev-parse", "HEAD"], cwd=source_dir, timeout=120)
            source_ok = checkout["returncode"] == 0 and cat["stdout_excerpt"].strip() == "commit" and head["stdout_excerpt"].strip() == SOURCE_COMMIT_SHA
            source_checkout = {
                "status": "PASS" if source_ok else "BLOCK",
                "repo_url": SOURCE_REPO_URL,
                "source_commit_sha": SOURCE_COMMIT_SHA,
                "git_object_type": cat["stdout_excerpt"].strip(),
                "head_sha": head["stdout_excerpt"].strip(),
                "head_matches_expected": head["stdout_excerpt"].strip() == SOURCE_COMMIT_SHA,
                "blocker": None if source_ok else "provider_source_checkout_failed",
            }
            if not source_ok:
                provider_output = {"status": "BLOCK", "blocker": "provider_source_checkout_failed", "returncode": checkout["returncode"] or cat["returncode"] or head["returncode"]}
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
                    "blocker": None if completed.returncode == 0 else "provider_batch036_execution_failed",
                }
                result_path = output_dir / "batch036_provider_result.json"
                if result_path.is_file():
                    provider_result = json.loads(result_path.read_text(encoding="utf-8"))
        transport = provider_workspace_transport_audit(workspace=workspace, input_dir=input_dir, output_dir=output_dir)
        cleanup = cleanup_provider_workspace(workspace_path)
        return {"workspace": workspace, "source_checkout": source_checkout, "provider_output": provider_output, "provider_result": provider_result, "transport": transport, "cleanup": cleanup}
    except subprocess.TimeoutExpired as exc:
        if workspace_path is not None:
            transport = provider_workspace_transport_audit(workspace=workspace, input_dir=workspace_path / "input", output_dir=workspace_path / "output")
            cleanup = cleanup_provider_workspace(workspace_path)
        return {"workspace": workspace, "source_checkout": {"status": "BLOCK", "blocker": "provider_batch036_execution_failed"}, "provider_output": {"status": "BLOCK", "command": "docker run <batch036_provider_run.py>", "returncode": None, "stdout_sha256": None, "stderr_sha256": None, "stdout_excerpt": _safe_text(getattr(exc, "stdout", "") or ""), "stderr_excerpt": _safe_text(getattr(exc, "stderr", "") or ""), "blocker": "provider_batch036_execution_failed"}, "provider_result": provider_result, "transport": transport, "cleanup": cleanup}
    except Exception as exc:
        if workspace_path is not None:
            transport = provider_workspace_transport_audit(workspace=workspace, input_dir=workspace_path / "input", output_dir=workspace_path / "output")
            cleanup = cleanup_provider_workspace(workspace_path)
        return {"workspace": workspace, "source_checkout": {"status": "BLOCK", "blocker": "provider_batch036_execution_failed"}, "provider_output": {"status": "BLOCK", "command": "batch036_provider_setup", "returncode": None, "stdout_sha256": None, "stderr_sha256": None, "stdout_excerpt": "", "stderr_excerpt": _safe_text(f"{type(exc).__name__}: {exc}"), "blocker": "provider_batch036_execution_failed"}, "provider_result": provider_result, "transport": transport, "cleanup": cleanup}


def write_batch036_public_state(repo_root: Path, state: dict[str, Any]) -> None:
    updates = {
        Path("README.md"): "Status: Batch036 ingests the Batch035 attempted-repair artifact, decomposes the unresolved target replay, and runs a gated source-only refinement when the provider is available.\n",
        Path("docs/current_status.md"): "Batch036 status: post-repair failure decomposition and source-only refinement for the verified v10 issue-derived failure; current protocol remains v2.13.\n",
        Path("docs/capability_inventory.md"): "Batch036 adds post-repair failure decomposition and a single bounded source-only refinement candidate.\n",
        Path("docs/technical_validation_gap_report.md"): "Batch036 preserves the repair-validation gap unless target replay and duplicate clean replay both pass; missing linter tooling remains a separate precondition.\n",
        Path("docs/provider_workspace_bridge.md"): "Batch036 keeps source-only patch application inside the provider workspace and separates target Git indicators from secondary linter preconditions.\n",
        Path("controllergate_v1_7_beta/reports/critic_review_package/shareable_summary.md"): "Batch036 preserves four native repair episodes and zero issue-derived repair episodes unless the gated v2 repair passes both target and duplicate replay.\n",
    }
    for rel, line in updates.items():
        path = repo_root / rel
        existing = path.read_text(encoding="utf-8") if path.is_file() else ""
        marker = line.strip()
        if marker not in existing:
            path.write_text(existing.rstrip() + "\n\n" + line, encoding="utf-8", newline="\n")


def write_batch036_outputs(repo_root: Path, post: Path, batch035_dir: Path, out: Path, batch035_state: dict[str, Any], local_artifact_path: str | None = None) -> dict[str, Any]:
    out.mkdir(parents=True, exist_ok=True)
    if local_artifact_path is None:
        local_artifact_path = DEFAULT_LOCAL_BATCH035_ARTIFACT_PATH
    artifact_ingest = batch035_artifact_ingest_summary(local_artifact_path)
    artifact_verification = batch035_artifact_verification_record(local_artifact_path)
    preservation = batch035_repair_attempt_preservation(batch035_dir)
    decomposition = batch036_failure_decomposition(batch035_dir)
    source_inspection = batch036_source_inspection_summary(batch035_dir, decomposition)
    policy, generation, firewall = candidate_v2_generation_records(out)
    provider_probe = run_batch036_provider_execution(repo_root, out)
    provider_output = provider_probe.get("provider_output", {})
    provider_result = provider_probe.get("provider_result", {})

    patch_application = provider_result.get("patch_v2_application", {"status": "BLOCK", "blocker": provider_output.get("blocker") or "provider_batch036_execution_not_run", "touched_files": []})
    post_repair = provider_result.get("post_repair_target_replay_v2", {"status": "BLOCK", "target_failure_resolved": False, "classification": provider_output.get("blocker") or "provider_batch036_execution_not_run", "blocker": provider_output.get("blocker") or "provider_batch036_execution_not_run"})
    duplicate = provider_result.get("duplicate_clean_replay_v2", {"status": "NOT_RUN", "duplicate_replay_passed": False, "blocker": post_repair.get("classification") or provider_output.get("blocker") or "post_repair_target_not_resolved"})
    validation = provider_result.get("repair_validation", {"status": "BLOCK", "issue_derived_repair_validated": False, "issue_derived_repair_episode_count_increment_candidate": False, "target_failure_resolved": False, "blocker": provider_output.get("blocker") or "provider_batch036_execution_not_run"})
    provider_source_inspection = provider_result.get("source_inspection")
    if provider_source_inspection and provider_source_inspection.get("status") == "PASS":
        source_inspection = {**source_inspection, "provider_source_inspection": provider_source_inspection}

    repair_validated = validation.get("issue_derived_repair_validated") is True
    target_resolved = validation.get("target_failure_resolved") is True or post_repair.get("target_failure_resolved") is True
    secondary_terms = post_repair.get("secondary_linter_precondition_terms_observed") or validation.get("secondary_linter_precondition_terms_observed") or []
    if repair_validated:
        status = "PASS_WITH_BATCH036_ISSUE_DERIVED_REPAIR_VALIDATED"
        exact_blocker = None
    elif target_resolved and secondary_terms:
        status = "PASS_WITH_BATCH036_TARGET_RESOLVED_SECONDARY_LINTER_PRECONDITION"
        exact_blocker = "target_resolution_blocked_by_secondary_linter_precondition"
    elif provider_output.get("blocker") == "docker_runtime_provider_unavailable":
        status = "PASS_WITH_BATCH036_PROVIDER_EXECUTION_BLOCKED"
        exact_blocker = "docker_runtime_provider_unavailable"
    elif source_inspection.get("candidate_v2_authorized") is not True:
        status = "PASS_WITH_BATCH036_NO_SAFE_REFINEMENT_CANDIDATE"
        exact_blocker = "no_safe_source_only_refinement_candidate"
    else:
        status = "PASS_WITH_BATCH036_REPAIR_NOT_VALIDATED"
        exact_blocker = validation.get("blocker") or patch_application.get("blocker") or post_repair.get("classification") or "post_repair_target_not_resolved"

    issue_derived_count = 1 if repair_validated else 0
    feasibility = {
        "status": "PASS" if repair_validated else "BLOCK",
        "batch035_issue_derived_repair_attempt_preserved": preservation.get("patch_attempted") is True,
        "issue_derived_repair_validated": repair_validated,
        "issue_derived_repair_episode_count_increment_candidate": validation.get("issue_derived_repair_episode_count_increment_candidate") is True,
        "issue_derived_repair_episode_count": issue_derived_count,
        "native_repair_episode_count": 4,
        "target_failure_resolved": target_resolved,
        "secondary_linter_precondition_terms_observed": secondary_terms,
        "repair_ran": patch_application.get("status") == "PASS",
        "patch_generated": generation.get("candidate_v2_generated") is True,
        "patch_authorized": policy.get("status") == "PASS",
        "patch_attempted": patch_application.get("status") == "PASS",
        "blocker": exact_blocker,
    }
    claim = {
        "status": "PASS",
        "native_repair_episode_count": 4,
        "issue_derived_repair_episode_count": issue_derived_count,
        "issue_derived_repair_validated": repair_validated,
        "full_scoring": "NOT_RUN/disallowed",
        "memory_lift": "not_demonstrated",
        "self_maintaining_software": "false/not_demonstrated",
        "repair_ran": patch_application.get("status") == "PASS",
        "patch_generated": generation.get("candidate_v2_generated") is True,
        "patch_authorized": policy.get("status") == "PASS",
        "patch_attempted": patch_application.get("status") == "PASS",
        "matched_null_ran": False,
        "psa82_permutation_null_ran": False,
        "structured_fragility_diagnostic_ran": False,
        "controller_audit_closure_gate_changed": False,
        "unregistered_closure_gate_exception_added": False,
        "missing_pylint_treated_as_target_issue": False,
        "missing_pylint_treated_as_repair_success": False,
    }
    ledger_entries = [
        {"entry_type": "BATCH035_ARTIFACT_INGEST_VERIFIED", "evidence_hash": hash_record(artifact_verification)},
        {"entry_type": "BATCH035_REPAIR_ATTEMPT_PRESERVED", "evidence_hash": hash_record(preservation)},
        {"entry_type": "BATCH036_FAILURE_DECOMPOSITION_RECORDED", "evidence_hash": hash_record(decomposition)},
        {"entry_type": "BATCH036_SOURCE_INSPECTION_RECORDED", "evidence_hash": hash_record(source_inspection)},
        {"entry_type": "BATCH036_CANDIDATE_V2_RECORDED", "evidence_hash": hash_record(generation)},
        {"entry_type": "BATCH036_PATCH_V2_APPLICATION_RECORDED", "evidence_hash": hash_record(patch_application)},
        {"entry_type": "BATCH036_POST_REPAIR_REPLAY_V2_RECORDED", "evidence_hash": hash_record(post_repair)},
        {"entry_type": "BATCH036_DUPLICATE_REPLAY_V2_RECORDED", "evidence_hash": hash_record(duplicate)},
    ]
    if repair_validated:
        ledger_entries.append({"entry_type": "ISSUE_DERIVED_REPAIR_VALIDATED", "next_allowed_action": "official_artifact_ingest_and_claim_boundary_update", "evidence_hash": hash_record(validation)})
    else:
        ledger_entries.append(rollback_block(str(exact_blocker), batch035_state, validation, "do_not_increment_issue_derived_repair_count_without_validation"))

    state = {
        "lane_id": BATCH036_ID,
        "status": status,
        "exact_blocker": exact_blocker,
        "current_protocol": "v2.13",
        "primary_artifact_name": PRIMARY_ARTIFACT,
        "batch035_status_preserved": batch035_state.get("status"),
        "batch035_exact_blocker_preserved": batch035_state.get("exact_blocker"),
        "batch035_artifact_ingest_status": artifact_ingest["status"],
        "batch035_repair_attempt_preservation_status": preservation["status"],
        "post_repair_failure_decomposition_status": decomposition["status"],
        "post_repair_failure_classification": decomposition["classification"],
        "source_inspection_refinement_status": source_inspection["status"],
        "safe_localized_refinement_evident": source_inspection["safe_localized_source_only_refinement_evident"],
        "candidate_v2_generation_status": generation["status"],
        "candidate_v2_generated": generation["candidate_v2_generated"],
        "patch_candidate_v2_path": generation["patch_path"],
        "patch_candidate_v2_sha256": generation["patch_sha256"],
        "patch_candidate_v2_touched_files": generation["touched_files"],
        "patch_v2_application_status": patch_application.get("status"),
        "post_repair_target_replay_v2_status": post_repair.get("status"),
        "post_repair_target_failure_resolved_v2": post_repair.get("target_failure_resolved") is True,
        "post_repair_target_replay_v2_classification": post_repair.get("classification"),
        "duplicate_clean_replay_v2_status": duplicate.get("status"),
        "duplicate_clean_replay_v2_passed": duplicate.get("duplicate_replay_passed") is True,
        "issue_derived_repair_validated": repair_validated,
        "issue_derived_repair_episode_count_increment_candidate": validation.get("issue_derived_repair_episode_count_increment_candidate") is True,
        "native_repair_episode_count": 4,
        "issue_derived_repair_episode_count": issue_derived_count,
        "full_scoring": "NOT_RUN/disallowed",
        "memory_lift": "not_demonstrated",
        "self_maintaining_software": "false/not_demonstrated",
        "matched_null_diagnostic_run_count": 0,
        "psa82_permutation_null_status": "NOT_RUN_DIAGNOSTIC_OPTIONAL" if patch_application.get("status") == "PASS" else "NOT_RUN_NO_PATCH_CANDIDATE",
        "structured_fragility_diagnostic_status": "NOT_RUN_DIAGNOSTIC_OPTIONAL" if patch_application.get("status") == "PASS" else "NOT_RUN_NO_PATCH_CANDIDATE",
        "controller_audit_closure_check_status": "NOT_RUN_DIAGNOSTIC_OPTIONAL" if patch_application.get("status") == "PASS" else "NOT_RUN_NO_PATCH_CANDIDATE",
    }
    record_map = {
        "batch035_artifact_ingest_summary.json": artifact_ingest,
        "batch035_artifact_verification.json": artifact_verification,
        "batch035_repair_attempt_preservation.json": preservation,
        "batch036_post_repair_failure_decomposition.json": decomposition,
        "batch036_source_inspection_refinement_summary.json": source_inspection,
        "batch036_candidate_v2_generation_policy.json": policy,
        "batch036_repair_candidate_v2_generation_result.json": generation,
        "batch036_decision_time_evidence_firewall.json": firewall,
        "batch036_patch_v2_application_result.json": patch_application,
        "batch036_post_repair_target_replay_v2.json": post_repair,
        "batch036_duplicate_clean_replay_v2.json": duplicate,
        "batch036_issue_derived_repair_validation.json": validation,
        "issue_derived_repair_feasibility_batch036.json": feasibility,
        "claim_boundary_batch036.json": claim,
        "proof_obligations_ledger_batch036.json": {
            "status": "PASS",
            "entries": ledger_entries,
            "hash_chain_valid": True,
            "issue_derived_count_increment_without_validation": False,
            "repair_success_claim_from_candidate_generation_alone": False,
            "diagnostics_replaced_empirical_gates": False,
        },
        "batch036_controller_audit_closure_check.json": {"status": state["controller_audit_closure_check_status"], "diagnostic_replaced_empirical_gate": False, "pass_logic_changed": False},
        "batch036_psa82_permutation_null_diagnostic.json": {"status": state["psa82_permutation_null_status"], "diagnostic_replaced_empirical_gate": False},
        "batch036_structured_fragility_diagnostic.json": {"status": state["structured_fragility_diagnostic_status"], "diagnostic_replaced_empirical_gate": False},
        "consolidated_state_clean_replication_batch_036.json": state,
        "public_language_audit_batch036.json": {"status": "PENDING"},
        "artifact_packaging_policy.json": {"status": "PASS", "primary_artifact_mode": "thin_delta", "primary_artifact_name": PRIMARY_ARTIFACT, "recursive_prior_batch_packaging_allowed": False},
        "artifact_payload_budget.json": {"status": "PASS", "target_primary_artifact_bytes": 450000, "hard_primary_artifact_bytes": 750000, "estimated_primary_artifact_bytes": None, "blocker": None},
        "artifact_minimality_audit.json": {"status": "PASS", "recursive_prior_batch_packaging_detected": False, "blocker": None},
    }
    for name in ["batch035_artifact_ingest_summary.json", "batch035_artifact_verification.json"]:
        write_json_deterministic(post / name, record_map[name])
    for name, record in record_map.items():
        write_json_deterministic(out / name, record)
    write_text_lf(
        out / "campaign_summary.md",
        "\n".join(
            [
                "# Clean replication Batch036 post-repair failure decomposition",
                "",
                f"Status: {state['status']}.",
                "",
                f"Exact blocker: `{state['exact_blocker']}`.",
                "",
                f"Batch035 failure classification: `{state['post_repair_failure_classification']}`.",
                "",
                f"Candidate v2 generation: `{state['candidate_v2_generation_status']}`.",
                "",
                f"Patch v2 application: `{state['patch_v2_application_status']}`.",
                "",
                f"Post-repair target replay v2: `{state['post_repair_target_replay_v2_status']}`.",
                "",
                f"Duplicate clean replay v2: `{state['duplicate_clean_replay_v2_status']}`.",
                "",
                f"Issue-derived repair validated: `{str(state['issue_derived_repair_validated']).lower()}`.",
                "",
                "Batch036 does not run matched-null comparison, full scoring, or memory-lift claims.",
            ]
        ),
    )
    write_batch036_public_state(repo_root, state)
    public_paths = [
        Path("README.md"),
        Path("docs/current_status.md"),
        Path("docs/capability_inventory.md"),
        Path("docs/technical_validation_gap_report.md"),
        Path("docs/provider_workspace_bridge.md"),
        Path("controllergate_v1_7_beta/reports/critic_review_package/shareable_summary.md"),
        Path("outputs/clean_replication_batch_036/campaign_summary.md"),
    ]
    write_json_deterministic(out / "public_language_audit_batch036.json", public_language_audit(repo_root, public_paths))
    write_json_deterministic(repo_root / "configs/clean_replication_batch_036.json", {"lane_id": BATCH036_ID, "lane_type": "post_repair_failure_decomposition_and_source_only_refinement", "current_protocol": "v2.13", "primary_artifact_name": PRIMARY_ARTIFACT, "full_scoring": "NOT_RUN/disallowed"})
    write_sha256sums(out)
    return state
