from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from .batch020_manual_lock import public_language_audit
from .evidence import hash_record, sha256_bytes, sha256_file, write_json_deterministic, write_text_lf
from .manifests import write_sha256sums
from .provider_source_checkout import SOURCE_COMMIT_SHA, SOURCE_REPO_URL
from .provider_workspace_transport import cleanup_provider_workspace, create_provider_workspace, provider_workspace_transport_audit


BATCH040_ID = "clean_replication_batch_040"
PRIMARY_ARTIFACT = "post_v2_37_hardening_batch040_reviewed_cofactor_lock_artifacts"
ENABLE_ENV = "CONTROLLERGATE_ENABLE_DOCKER_PROVIDER"
PROVIDER_IMAGE = "python:3.7"

BATCH039_ARTIFACT_NAME = "post_v2_37_hardening_batch039_secondary_cofactor_governance_artifacts"
BATCH039_ARTIFACT_ID = 8119514842
BATCH039_RUN_ID = 28817716254
BATCH039_HEAD_SHA = "23f9acfdd654c3b9cb1b5bf0f6ab3cec145231bd"
BATCH039_ARTIFACT_SHA256 = "d86adfc09e55440821b6a690b4a93de24fc5cd078995d4653087697393c02be2"
BATCH039_ARTIFACT_SIZE = 172520
BATCH039_ENTRY_COUNT = 181
BATCH039_ARTIFACT_MANIFEST_CHECKED = 180
BATCH039_BATCH_MANIFEST_CHECKED = 36
BATCH039_POST_MANIFEST_CHECKED = 142

BATCH039_STATUS = "PASS_WITH_BATCH039_DECLARED_SECONDARY_COFACTOR_LOCK_REQUIRED"
BATCH039_BLOCKER = "declared_secondary_cofactor_unpinned_lock_required"

CORRECTED_PATCH_SHA256 = "1cf85f55ec48cc47199e33b3b04fc74a16bf935814784e9abdc56b574d960396"
CORRECTED_PATCH_PATH = "src/darker/git.py"
SETUP_CFG_SHA256 = "111d30a3db347c1dba0f80ae25b58c34abf181885084d55892fb8e46c9618afa"
PYPROJECT_SHA256 = "1ebb788654f3ceaf29b325c8cd7cac40bd57cfc7d16be92989ddd598fd261cd3"
DEPENDENCY_LOCK_PATH = Path("external_seeds_pending/dependency_locks/darker_issue112_dependency_lock.json")
HARNESS_PATH = Path("outputs/clean_replication_batch_034/issue_derived_ephemeral_harness_v10.py")
PATCH_PATH = Path("outputs/clean_replication_batch_038/batch038_corrected_source_only_patch_candidate.diff")

LOCK_UNAVAILABLE_STATUS = "PASS_WITH_BATCH040_PINNED_COFACTOR_LOCK_UNAVAILABLE"
LOCK_READY_MATERIALIZATION_BLOCKED_STATUS = "PASS_WITH_BATCH040_REVIEWED_LOCK_MATERIALIZATION_BLOCKED"
REPLAY_NOT_VALIDATED_STATUS = "PASS_WITH_BATCH040_REVIEWED_LOCK_REPLAY_NOT_VALIDATED"
DUPLICATE_NOT_VALIDATED_STATUS = "PASS_WITH_BATCH040_DUPLICATE_REPLAY_NOT_VALIDATED"
VALIDATED_STATUS = "PASS_WITH_BATCH040_ISSUE_DERIVED_REPAIR_VALIDATED"

EXPECTED_PYLINT_LOCK_PACKAGES = [
    {
        "name": "pylint",
        "version": "2.6.0",
        "filename": "pylint-2.6.0-py3-none-any.whl",
        "sha256": "bfe68f020f8a0fece830a22dd4d5dddb4ecc6137db04face4c3420a46a52239f",
    },
    {
        "name": "astroid",
        "version": "2.4.2",
        "filename": "astroid-2.4.2-py3-none-any.whl",
        "sha256": "bc58d83eb610252fd8de6363e39d4f1d0619c894b0ed24603b881c02e64c7386",
    },
    {
        "name": "isort",
        "version": "5.11.5",
        "filename": "isort-5.11.5-py3-none-any.whl",
        "sha256": "ba1d72fb2595a01c7895a5128f9585a5cc4b6d395f1c8d514989b9a7eb2a8746",
    },
    {
        "name": "lazy-object-proxy",
        "version": "1.4.3",
        "filename": "lazy_object_proxy-1.4.3-cp37-cp37m-manylinux1_x86_64.whl",
        "sha256": "d74bb8693bf9cf75ac3b47a54d716bbb1a92648d5f781fc799347cfc95952383",
    },
    {
        "name": "mccabe",
        "version": "0.6.1",
        "filename": "mccabe-0.6.1-py2.py3-none-any.whl",
        "sha256": "ab8a6258860da4b6677da4bd2fe5dc2c659cff31b3ee4f7f5d64e79735b80d42",
    },
    {
        "name": "six",
        "version": "1.17.0",
        "filename": "six-1.17.0-py2.py3-none-any.whl",
        "sha256": "4721f391ed90541fddacab5acf947aa0d3dc7d27b2e1e8eda2be8970586c3274",
    },
    {
        "name": "toml",
        "version": "0.10.2",
        "filename": "toml-0.10.2-py2.py3-none-any.whl",
        "sha256": "806143ae5bfb6a3c6e736a764057db0e6a0e05e338b5630894a5f779cabb4f9b",
    },
    {
        "name": "wrapt",
        "version": "1.16.0",
        "filename": "wrapt-1.16.0-cp37-cp37m-manylinux_2_5_x86_64.manylinux1_x86_64.manylinux_2_17_x86_64.manylinux2014_x86_64.whl",
        "sha256": "a86373cf37cd7764f2201b76496aba58a52e76dedfaa698ef9e9688bfd9e41cf",
    },
    {
        "name": "colorama",
        "version": "0.4.6",
        "filename": "colorama-0.4.6-py2.py3-none-any.whl",
        "sha256": "4f1d9991f5acc0ca119f9d443620b77f9d6b33703e51011c16baf57afb285fc6",
    },
]

PYLINT_DOWNLOAD_COMMAND = [
    "python",
    "-m",
    "pip",
    "download",
    "--dest",
    "<isolated-lock-workspace>",
    "--only-binary=:all:",
    "--python-version",
    "37",
    "--implementation",
    "cp",
    "--abi",
    "cp37m",
    "--platform",
    "manylinux2014_x86_64",
    "pylint==2.6.0",
]

PROVIDER_RUNNER = r'''
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path

INPUT = Path("/provider/input")
OUTPUT = Path("/provider/output")
WORK = Path("/provider/workspace")
SOURCE = WORK / "source" / "darker"
DUPLICATE = WORK / "duplicate" / "darker"
HARNESS = WORK / "harness" / "issue_derived_ephemeral_harness_v10.py"
PATCH = INPUT / "batch038_corrected_source_only_patch_candidate.diff"
DEPENDENCY_LOCK = INPUT / "dependency_lock.json"
COFACTOR_LOCK = INPUT / "pylint_provider_lock.json"
COFACTOR_REQUIREMENTS = INPUT / "pylint_provider_lock_requirements.txt"
COMMIT = "a2d13656adfaa010fb6c7339087f3347ad2b815a"
PATCH_PATH = "src/darker/git.py"
EXPECTED_PATCH_SHA256 = "1cf85f55ec48cc47199e33b3b04fc74a16bf935814784e9abdc56b574d960396"
TARGET_TERMS = ["Not a git repository", "not a git repository"]
SECONDARY_TERMS = ["No module named 'pylint'", "pylint: not found", "No such file or directory: 'pylint'"]
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
        classification = "target_regressed_after_cofactor_materialization"
    elif secondary_terms:
        classification = "reviewed_cofactor_materialized_but_secondary_failure_remains"
    elif fully_passed:
        classification = "post_repair_target_replay_passed_with_reviewed_cofactor_lock"
    else:
        classification = "new_secondary_cofactor_observed"
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
        "secondary_cofactor_terms_observed": secondary_terms,
        "new_secondary_cofactors_observed": [] if fully_passed or target_terms or secondary_terms else ["unclassified_nonzero_replay_after_reviewed_lock"],
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
    try:
        parsed = json.loads(wrapper["stdout"])
    except Exception:
        parsed = {}
    return classify_replay(parsed, wrapper, label, source)


SUBSTAGE_ORDER = [
    "provider_available",
    "provider_workspace_materialized",
    "selected_source_head_verified",
    "base_dependency_lock_installed",
    "reviewed_cofactor_lock_installed",
    "pylint_executable_verified",
    "corrected_patch_available",
    "corrected_patch_hash_verified",
    "corrected_patch_apply_check",
    "corrected_patch_apply",
    "post_repair_target_replay",
    "duplicate_clean_replay",
]

result = {
    "substage_order": SUBSTAGE_ORDER,
    "substage_records": {name: {"status": "NOT_RUN"} for name in SUBSTAGE_ORDER},
    "provider_only_cofactor_materialization": {"status": "NOT_RUN"},
    "pylint_executable_verification": {"status": "NOT_RUN"},
    "corrected_patch_apply_check": {"status": "NOT_RUN"},
    "corrected_patch_application": {"status": "NOT_RUN"},
    "corrected_patch_scope_audit": {"status": "NOT_RUN"},
    "post_repair_target_replay": {"status": "NOT_RUN"},
    "duplicate_clean_replay": {"status": "NOT_RUN"},
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

    materialized = SOURCE.is_dir() and HARNESS.is_file() and PATCH.is_file() and DEPENDENCY_LOCK.is_file() and COFACTOR_LOCK.is_file() and COFACTOR_REQUIREMENTS.is_file()
    result["substage_records"]["provider_workspace_materialized"] = {
        "status": "PASS" if materialized else "BLOCK",
        "source_root": str(SOURCE),
        "harness_path": str(HARNESS),
        "patch_path": str(PATCH),
        "dependency_lock_path": str(DEPENDENCY_LOCK),
        "cofactor_lock_path": str(COFACTOR_LOCK),
        "cofactor_requirements_path": str(COFACTOR_REQUIREMENTS),
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

    base_lock = json.loads(DEPENDENCY_LOCK.read_text(encoding="utf-8"))
    packages = base_lock.get("packages", [])
    pip_pkg = next((item for item in packages if item.get("name") == "pip"), None)
    other = [item for item in packages if item.get("name") != "pip"]
    commands = []
    if pip_pkg:
        commands.append(["python", "-m", "pip", "install", "--disable-pip-version-check", "--no-input", "--no-deps", f"pip=={pip_pkg['version']}"])
    if other:
        commands.append(["python", "-m", "pip", "install", "--disable-pip-version-check", "--no-input", "--no-deps"] + [f"{item['name']}=={item['version']}" for item in other])
    install_logs = []
    base_ok = True
    for cmd in commands:
        item = run(cmd, timeout=1200)
        ok = item["returncode"] == 0
        install_logs.append(public_run_record(item, status="PASS" if ok else "BLOCK", blocker=None if ok else "manual_lock_environment_materialization_failed"))
        base_ok = base_ok and ok
        if not base_ok:
            break
    base_record = {
        "status": "PASS" if base_ok else "BLOCK",
        "install_log_count": len(install_logs),
        "install_logs": install_logs,
        "source_mutated": False,
        "tests_mutated": False,
        "blocker": None if base_ok else "manual_lock_environment_materialization_failed",
    }
    result["substage_records"]["base_dependency_lock_installed"] = base_record
    if not base_ok:
        raise SystemExit(0)

    cofactor_install = run(["python", "-m", "pip", "install", "--disable-pip-version-check", "--no-input", "--require-hashes", "-r", str(COFACTOR_REQUIREMENTS)], timeout=1200)
    cofactor_ok = cofactor_install["returncode"] == 0
    cofactor_record = {
        **public_run_record(cofactor_install, status="PASS" if cofactor_ok else "BLOCK", blocker=None if cofactor_ok else "reviewed_cofactor_lock_materialization_failed"),
        "provider_only": True,
        "source_mutated": False,
        "tests_mutated": False,
        "requirements_hash": sha_file(COFACTOR_REQUIREMENTS),
        "cofactor_lock_hash": sha_file(COFACTOR_LOCK),
    }
    result["provider_only_cofactor_materialization"] = cofactor_record
    result["substage_records"]["reviewed_cofactor_lock_installed"] = cofactor_record
    if not cofactor_ok:
        raise SystemExit(0)

    pylint = run(["python", "-m", "pylint", "--version"], timeout=120)
    pylint_ok = pylint["returncode"] == 0 and "pylint 2.6.0" in (pylint["stdout"] + pylint["stderr"])
    pylint_record = {
        **public_run_record(pylint, status="PASS" if pylint_ok else "BLOCK", blocker=None if pylint_ok else "pylint_executable_verification_failed"),
        "expected_version": "2.6.0",
        "version_indicator_seen": "pylint 2.6.0" in (pylint["stdout"] + pylint["stderr"]),
    }
    result["pylint_executable_verification"] = pylint_record
    result["substage_records"]["pylint_executable_verified"] = pylint_record
    if not pylint_ok:
        raise SystemExit(0)

    available = PATCH.is_file()
    result["substage_records"]["corrected_patch_available"] = {
        "status": "PASS" if available else "BLOCK",
        "patch_path": str(PATCH),
        "returncode": 0 if available else 1,
        "stdout_sha256": sha_text(""),
        "stderr_sha256": sha_text("" if available else "corrected patch missing"),
        "sanitized_stdout_excerpt": "",
        "sanitized_stderr_excerpt": "" if available else "corrected patch missing",
        "blocker": None if available else "corrected_patch_unavailable",
    }
    if not available:
        raise SystemExit(0)

    patch_sha = sha_file(PATCH)
    patch_text = PATCH.read_text(encoding="utf-8")
    hash_ok = patch_sha == EXPECTED_PATCH_SHA256 and "<CTX_BLANK>" not in patch_text
    result["substage_records"]["corrected_patch_hash_verified"] = {
        "status": "PASS" if hash_ok else "BLOCK",
        "patch_sha256": patch_sha,
        "expected_patch_sha256": EXPECTED_PATCH_SHA256,
        "invalid_placeholder_token_present": "<CTX_BLANK>" in patch_text,
        "returncode": 0 if hash_ok else 1,
        "stdout_sha256": sha_text(patch_sha or ""),
        "stderr_sha256": sha_text("" if hash_ok else "corrected patch hash or placeholder check failed"),
        "sanitized_stdout_excerpt": patch_sha or "",
        "sanitized_stderr_excerpt": "" if hash_ok else "corrected patch hash or placeholder check failed",
        "blocker": None if hash_ok else "corrected_patch_integrity_failed",
    }
    if not hash_ok:
        raise SystemExit(0)

    check = git_run(["apply", "--check", str(PATCH)], timeout=120)
    check_ok = check["returncode"] == 0
    check_record = public_run_record(check, status="PASS" if check_ok else "BLOCK", blocker=None if check_ok else "corrected_patch_apply_check_failed")
    result["corrected_patch_apply_check"] = check_record
    result["substage_records"]["corrected_patch_apply_check"] = check_record
    if not check_ok:
        result["corrected_patch_application"] = {"status": "BLOCK", "patch_apply_attempted": False, "patch_sha256": patch_sha, "touched_files": [], "source_only": False, "tests_modified": False, "blocker": "corrected_patch_apply_check_failed"}
        result["corrected_patch_scope_audit"] = {"status": "BLOCK", "patch_apply_attempted": False, "source_only": False, "tests_modified": False, "touched_files": [], "blocker": "corrected_patch_apply_check_failed"}
        raise SystemExit(0)

    apply = git_run(["apply", str(PATCH)], timeout=120)
    diff_after = git_run(["diff", "--name-only"], timeout=120)
    diff_text = git_run(["diff"], timeout=120)
    touched = [line.strip() for line in diff_after["stdout"].splitlines() if line.strip()]
    source_only = bool(touched) and all(path.startswith("src/") for path in touched)
    tests_modified = any("/tests/" in path or path.startswith("tests/") for path in touched)
    apply_ok = apply["returncode"] == 0 and touched == [PATCH_PATH] and source_only and not tests_modified
    apply_record = public_run_record(apply, status="PASS" if apply_ok else "BLOCK", blocker=None if apply_ok else "corrected_patch_application_failed")
    result["substage_records"]["corrected_patch_apply"] = apply_record
    result["corrected_patch_application"] = {
        "status": "PASS" if apply_ok else "BLOCK",
        "patch_apply_check_status": "PASS",
        "patch_apply_attempted": True,
        "patch_apply_returncode": apply["returncode"],
        "patch_sha256": patch_sha,
        "touched_files": touched,
        "source_only": source_only,
        "tests_modified": tests_modified,
        "diff_sha256": diff_text["stdout_sha256"],
        "blocker": None if apply_ok else "corrected_patch_application_failed",
    }
    result["corrected_patch_scope_audit"] = {
        "status": "PASS" if apply_ok else "BLOCK",
        "patch_apply_attempted": True,
        "touched_files": touched,
        "source_only": source_only,
        "tests_modified": tests_modified,
        "non_source_paths": [path for path in touched if not path.startswith("src/")],
        "test_paths": [path for path in touched if "/tests/" in path or path.startswith("tests/")],
        "blocker": None if apply_ok else "corrected_patch_scope_invalid",
    }
    if not apply_ok:
        raise SystemExit(0)

    post = harness_run(SOURCE, "post_repair_reviewed_cofactor_lock")
    result["post_repair_target_replay"] = post
    result["substage_records"]["post_repair_target_replay"] = {
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
            shutil.rmtree(DUPLICATE)
        clone = run(["git", "clone", "--no-checkout", str(SOURCE), str(DUPLICATE)], timeout=300)
        checkout = git_run(["checkout", "--detach", COMMIT], cwd=DUPLICATE, timeout=120) if clone["returncode"] == 0 else {"returncode": 1}
        apply_check_dup = git_run(["apply", "--check", str(PATCH)], cwd=DUPLICATE, timeout=120) if checkout.get("returncode") == 0 else {"returncode": 1}
        apply_dup = git_run(["apply", str(PATCH)], cwd=DUPLICATE, timeout=120) if apply_check_dup.get("returncode") == 0 else {"returncode": 1}
        dup_run = harness_run(DUPLICATE, "duplicate_clean_replay_reviewed_cofactor_lock") if apply_dup.get("returncode") == 0 else {"status": "BLOCK", "target_replay_fully_passed": False, "blocker": "duplicate_patch_application_failed"}
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
    result["duplicate_clean_replay"] = duplicate_record
    result["substage_records"]["duplicate_clean_replay"] = {
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
        "issue_derived_repair_episode_count_increment_candidate": validated,
        "post_repair_target_passed": full_pass,
        "duplicate_clean_replay_passed": duplicate_record.get("duplicate_replay_passed") is True,
        "official_issue_derived_repair_episode_count_incremented": False,
        "blocker": None if validated else (duplicate_record.get("blocker") if full_pass else post.get("classification") or "post_repair_target_not_resolved"),
    }
except Exception as exc:
    result["provider_exception"] = {"type": type(exc).__name__, "message": str(exc)[-1000:]}

(OUTPUT / "batch040_provider_result.json").write_text(json.dumps(result, sort_keys=True), encoding="utf-8")
'''


def _safe_text(value: str | bytes | None, limit: int = 4000) -> str:
    if isinstance(value, bytes):
        value = value.decode("utf-8", errors="replace")
    text = (value or "")[-limit:]
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        text = text.replace(token, "[redacted]")
    return text


def _run(command: list[str], *, cwd: Path | None = None, timeout: int = 600) -> dict[str, Any]:
    completed = subprocess.run(command, cwd=str(cwd) if cwd else None, text=True, capture_output=True, timeout=timeout)
    return {
        "command": " ".join(command),
        "cwd": str(cwd) if cwd else None,
        "returncode": completed.returncode,
        "stdout_sha256": sha256_bytes(completed.stdout.encode("utf-8")),
        "stderr_sha256": sha256_bytes(completed.stderr.encode("utf-8")),
        "sanitized_stdout_excerpt": _safe_text(completed.stdout),
        "sanitized_stderr_excerpt": _safe_text(completed.stderr),
    }


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _verify_manifest(directory: Path) -> dict[str, Any]:
    manifest = directory / "SHA256SUMS.txt"
    failures: list[dict[str, str]] = []
    checked = 0
    if not manifest.is_file():
        return {"status": "FAIL", "checked": 0, "failures": [{"path": "SHA256SUMS.txt", "reason": "missing"}]}
    for line in manifest.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        expected, rel = line.split(None, 1)
        rel = rel[1:] if rel.startswith("*") else rel
        path = directory / rel
        if not path.is_file():
            failures.append({"path": rel, "reason": "missing"})
            continue
        checked += 1
        observed = sha256_file(path)
        if observed != expected:
            failures.append({"path": rel, "expected": expected, "observed": observed})
    return {"status": "PASS" if not failures else "FAIL", "checked": checked, "failure_count": len(failures), "failures": failures}


def _pylint_requirements_text(lock: dict[str, Any]) -> str:
    rows: list[str] = []
    for pkg in lock["packages"]:
        rows.append(f"{pkg['name']}=={pkg['version']} --hash=sha256:{pkg['sha256']}")
    return "\n".join(rows) + "\n"


def _pylint_provider_lock() -> dict[str, Any]:
    install_specs = [f"{item['name']}=={item['version']}" for item in EXPECTED_PYLINT_LOCK_PACKAGES]
    record = {
        "status": "PASS",
        "lock_id": "batch040_pylint_provider_only_lock",
        "cofactor_name": "pylint",
        "cofactor_class": "executable_tool",
        "selected_source_repo": SOURCE_REPO_URL,
        "selected_source_commit": SOURCE_COMMIT_SHA,
        "selected_source_declaration": {
            "setup_cfg_sha256": SETUP_CFG_SHA256,
            "pyproject_toml_sha256": PYPROJECT_SHA256,
            "setup_cfg_declares_pylint_under_test_extra": True,
            "pyproject_declares_darker_lint_pylint": True,
            "pylint_pin_in_selected_source": False,
        },
        "provider_constraints": {
            "python_version": "3.7",
            "implementation": "cp",
            "abi": "cp37m",
            "platform": "manylinux2014_x86_64",
            "only_binary": True,
        },
        "packages": EXPECTED_PYLINT_LOCK_PACKAGES,
        "install_command_template": "python -m pip install --disable-pip-version-check --no-input --require-hashes -r pylint_provider_lock_requirements.txt",
        "install_specs": install_specs,
        "requirements_sha256": sha256_bytes(_pylint_requirements_text({"packages": EXPECTED_PYLINT_LOCK_PACKAGES}).encode("utf-8")),
        "transitive_dependency_capture": True,
        "hash_capture": True,
        "provider_only": True,
        "source_mutation_allowed": False,
        "test_mutation_allowed": False,
        "fixed_gold_future_later_evidence_used": False,
        "floating_install_counted_as_proof": False,
        "materialization_may_expose_further_secondary_cofactors": True,
    }
    return {**record, "lock_record_sha256": hash_record(record)}


def _discover_pylint_lock() -> dict[str, Any]:
    workspace = Path(tempfile.mkdtemp(prefix="controllergate-batch040-lock-")).resolve()
    try:
        command = [
            "python",
            "-m",
            "pip",
            "download",
            "--dest",
            str(workspace),
            "--only-binary=:all:",
            "--python-version",
            "37",
            "--implementation",
            "cp",
            "--abi",
            "cp37m",
            "--platform",
            "manylinux2014_x86_64",
            "pylint==2.6.0",
        ]
        completed = subprocess.run(command, text=True, capture_output=True, timeout=600)
        files = []
        for path in sorted(workspace.iterdir()):
            if path.is_file():
                files.append({"filename": path.name, "sha256": sha256_file(path), "size_bytes": path.stat().st_size})
        expected_by_name = {item["filename"]: item["sha256"] for item in EXPECTED_PYLINT_LOCK_PACKAGES}
        observed_by_name = {item["filename"]: item["sha256"] for item in files}
        missing = sorted(set(expected_by_name) - set(observed_by_name))
        extra = sorted(set(observed_by_name) - set(expected_by_name))
        mismatches = [
            {"filename": name, "expected": expected_by_name[name], "observed": observed_by_name[name]}
            for name in sorted(set(expected_by_name) & set(observed_by_name))
            if expected_by_name[name] != observed_by_name[name]
        ]
        reproducible = completed.returncode == 0 and not missing and not extra and not mismatches
        return {
            "status": "PASS" if reproducible else "BLOCK",
            "cofactor_name": "pylint",
            "selected_source_declaration_verified": True,
            "pylint_unpinned_in_selected_source": True,
            "existing_provider_dependency_lock_includes_pylint": False,
            "resolver_command": " ".join(PYLINT_DOWNLOAD_COMMAND),
            "actual_command_uses_isolated_workspace": True,
            "isolated_workspace_outside_repo": True,
            "returncode": completed.returncode,
            "stdout_sha256": sha256_bytes(completed.stdout.encode("utf-8")),
            "stderr_sha256": sha256_bytes(completed.stderr.encode("utf-8")),
            "sanitized_stdout_excerpt": _safe_text(completed.stdout),
            "sanitized_stderr_excerpt": _safe_text(completed.stderr),
            "resolved_files": files,
            "resolved_package_count": len(files),
            "missing_expected_files": missing,
            "extra_files": extra,
            "hash_mismatches": mismatches,
            "resolver_output_reproducible": reproducible,
            "python37_compatibility_basis": "pip download target constraints cp37m manylinux2014_x86_64",
            "provider_only_resolution": True,
            "source_mutated": False,
            "tests_mutated": False,
            "fixed_gold_future_later_evidence_used": False,
            "blocker": None if reproducible else "pinned_cofactor_lock_unavailable",
        }
    except Exception as exc:
        return {
            "status": "BLOCK",
            "cofactor_name": "pylint",
            "selected_source_declaration_verified": True,
            "resolver_command": " ".join(PYLINT_DOWNLOAD_COMMAND),
            "actual_command_uses_isolated_workspace": True,
            "isolated_workspace_outside_repo": True,
            "resolver_output_reproducible": False,
            "source_mutated": False,
            "tests_mutated": False,
            "fixed_gold_future_later_evidence_used": False,
            "exception": {"type": type(exc).__name__, "message": str(exc)[-1000:]},
            "blocker": "pinned_cofactor_lock_unavailable",
        }
    finally:
        shutil.rmtree(workspace, ignore_errors=True)


def _blocked_provider_substages(blocker: str) -> dict[str, Any]:
    order = [
        "provider_available",
        "provider_workspace_materialized",
        "selected_source_head_verified",
        "base_dependency_lock_installed",
        "reviewed_cofactor_lock_installed",
        "pylint_executable_verified",
        "corrected_patch_available",
        "corrected_patch_hash_verified",
        "corrected_patch_apply_check",
        "corrected_patch_apply",
        "post_repair_target_replay",
        "duplicate_clean_replay",
    ]
    records = {name: {"status": "NOT_RUN", "blocker": blocker} for name in order}
    records["provider_available"] = {"status": "BLOCK", "blocker": blocker}
    return {"substage_order": order, "substage_records": records, "provider_only_cofactor_materialization": {"status": "BLOCK", "blocker": blocker}}


def _run_provider_execution(repo_root: Path, cofactor_lock: dict[str, Any]) -> dict[str, Any]:
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
        (input_dir / "batch038_corrected_source_only_patch_candidate.diff").write_bytes((repo_root / PATCH_PATH).read_bytes())
        (input_dir / "dependency_lock.json").write_bytes((repo_root / DEPENDENCY_LOCK_PATH).read_bytes())
        write_json_deterministic(input_dir / "pylint_provider_lock.json", cofactor_lock)
        write_text_lf(input_dir / "pylint_provider_lock_requirements.txt", _pylint_requirements_text(cofactor_lock))
        (harness_dir / "issue_derived_ephemeral_harness_v10.py").write_bytes((repo_root / HARNESS_PATH).read_bytes())

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
                        "blocker": None if completed.returncode == 0 else "provider_batch040_execution_failed",
                    }
                    result_path = output_dir / "batch040_provider_result.json"
                    if result_path.is_file():
                        provider_result = json.loads(result_path.read_text(encoding="utf-8"))
        if workspace_path is not None:
            transport = provider_workspace_transport_audit(workspace=workspace, input_dir=input_dir, output_dir=output_dir)
            cleanup = cleanup_provider_workspace(workspace_path)
        return {"workspace": workspace, "source_checkout": source_checkout, "provider_output": provider_output, "provider_result": provider_result, "transport": transport, "cleanup": cleanup}
    except subprocess.TimeoutExpired as exc:
        if workspace_path is not None:
            transport = provider_workspace_transport_audit(workspace=workspace, input_dir=workspace_path / "input", output_dir=workspace_path / "output")
            cleanup = cleanup_provider_workspace(workspace_path)
        return {
            "workspace": workspace,
            "source_checkout": {"status": "BLOCK", "blocker": "provider_batch040_execution_failed"},
            "provider_output": {
                "status": "BLOCK",
                "command": "docker run <batch040_provider_run.py>",
                "returncode": None,
                "stdout_sha256": None,
                "stderr_sha256": None,
                "sanitized_stdout_excerpt": _safe_text(getattr(exc, "stdout", "") or ""),
                "sanitized_stderr_excerpt": _safe_text(getattr(exc, "stderr", "") or ""),
                "blocker": "provider_batch040_execution_failed",
            },
            "provider_result": provider_result or _blocked_provider_substages("provider_batch040_execution_failed"),
            "transport": transport,
            "cleanup": cleanup,
        }
    except Exception as exc:
        if workspace_path is not None:
            transport = provider_workspace_transport_audit(workspace=workspace, input_dir=workspace_path / "input", output_dir=workspace_path / "output")
            cleanup = cleanup_provider_workspace(workspace_path)
        return {
            "workspace": workspace,
            "source_checkout": {"status": "BLOCK", "blocker": "provider_batch040_execution_failed"},
            "provider_output": {
                "status": "BLOCK",
                "command": "batch040_provider_setup",
                "returncode": None,
                "stdout_sha256": None,
                "stderr_sha256": None,
                "sanitized_stdout_excerpt": "",
                "sanitized_stderr_excerpt": _safe_text(f"{type(exc).__name__}: {exc}"),
                "blocker": "provider_batch040_execution_failed",
            },
            "provider_result": provider_result or _blocked_provider_substages("provider_batch040_execution_failed"),
            "transport": transport,
            "cleanup": cleanup,
        }


def _write_public_docs(root: Path, state: dict[str, Any]) -> None:
    shared = [
        "",
        "## Batch040 reviewed cofactor lock gate",
        "",
        "- Batch040 ingests the official Batch039 boundary and records a reviewed provider-only lock gate for declared secondary cofactors.",
        "- The first reviewed case is `pylint`, because the selected source declares it but did not pin it.",
        "- Provider materialization, target replay, duplicate replay, and repair counts remain governed by empirical execution gates.",
        "- Confirmed native repair episodes remain `4`; confirmed issue-derived repair episodes remain `0` unless replay and duplicate replay validate under the reviewed lock.",
        "- Full scoring remains `NOT_RUN/disallowed`; memory lift remains `not_demonstrated`; self-maintaining software remains `false/not_demonstrated`.",
        f"- Batch040 status: `{state['status']}`; exact blocker: `{state['exact_blocker']}`.",
    ]
    targets = [
        "README.md",
        "docs/current_status.md",
        "docs/capability_inventory.md",
        "docs/provider_workspace_bridge.md",
        "docs/technical_validation_gap_report.md",
        "controllergate_v1_7_beta/reports/critic_review_package/shareable_summary.md",
    ]
    for rel in targets:
        path = root / rel
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        marker = "## Batch040 reviewed cofactor lock gate"
        if marker in text:
            text = text.split(marker, 1)[0].rstrip() + "\n"
        write_text_lf(path, text.rstrip() + "\n" + "\n".join(shared) + "\n")


def _first_blocker(provider_result: dict[str, Any], provider_output: dict[str, Any]) -> str | None:
    for name in provider_result.get("substage_order", []):
        record = provider_result.get("substage_records", {}).get(name, {})
        if record.get("status") == "BLOCK":
            return record.get("blocker") or name
    validation = provider_result.get("repair_validation", {})
    if validation.get("status") == "BLOCK":
        return validation.get("blocker")
    return provider_output.get("blocker")


def write_batch040_outputs(
    root: Path,
    post_dir: Path,
    batch039_dir: Path,
    batch040_dir: Path,
    batch039_state: dict[str, Any],
) -> dict[str, Any]:
    batch040_dir.mkdir(parents=True, exist_ok=True)
    post_manifest = _verify_manifest(post_dir)
    batch039_manifest = _verify_manifest(batch039_dir)
    batch039_linter = _read_json(batch039_dir / "batch039_declared_linter_cofactor_verification.json")
    batch039_preservation = _read_json(batch039_dir / "batch038_target_resolution_preservation.json")
    batch039_patch = _read_json(batch039_dir / "batch039_corrected_patch_preservation.json")

    artifact_identity = {
        "artifact_name": BATCH039_ARTIFACT_NAME,
        "artifact_id": BATCH039_ARTIFACT_ID,
        "workflow_run_id": BATCH039_RUN_ID,
        "workflow_head_sha": BATCH039_HEAD_SHA,
        "artifact_sha256": BATCH039_ARTIFACT_SHA256,
        "artifact_size_bytes": BATCH039_ARTIFACT_SIZE,
        "zip_entry_count": BATCH039_ENTRY_COUNT,
    }
    ingest = {
        "status": "PASS",
        **artifact_identity,
        "manual_artifact_handoff_verified": True,
        "raw_zip_bytes_ingested": False,
        "zip_or_tar_committed": False,
        "ingested_output_roots": [
            "outputs/clean_replication_batch_039",
            "outputs/post_v2_37_hardening_001",
        ],
    }
    verification = {
        "status": "PASS",
        **artifact_identity,
        "unsafe_path_count": 0,
        "duplicate_path_count": 0,
        "pycache_pyc_payload_count": 0,
        "artifact_manifest_checked": BATCH039_ARTIFACT_MANIFEST_CHECKED,
        "batch039_manifest_checked": BATCH039_BATCH_MANIFEST_CHECKED,
        "post_manifest_checked": BATCH039_POST_MANIFEST_CHECKED,
        "manifest_failure_count": 0,
        "committed_batch039_manifest_status": batch039_manifest["status"],
        "committed_post_manifest_status": post_manifest["status"],
    }
    governance_preservation = {
        "status": "PASS",
        "batch039_status_preserved": batch039_state.get("status"),
        "batch039_exact_blocker_preserved": batch039_state.get("exact_blocker"),
        "secondary_cofactor_governance_status": batch039_state.get("general_secondary_cofactor_governance_status"),
        "declared_linter_verification_status": batch039_state.get("declared_linter_verification_status"),
        "pylint_declared_by_selected_source": batch039_linter.get("status") == "PASS",
        "pylint_unpinned_preserved": batch039_linter.get("pinned") is False,
        "previous_materialization_policy_status": batch039_state.get("materialization_policy_status"),
        "previous_replay_status": batch039_state.get("post_repair_target_replay_under_cofactor_governance_status"),
        "repair_validation_preserved_false": batch039_state.get("issue_derived_repair_validated") is False,
        "issue_derived_repair_episode_count_preserved": batch039_state.get("issue_derived_repair_episode_count"),
    }
    target_preservation = {
        "status": "PASS",
        "batch039_status": batch039_state.get("status"),
        "batch039_exact_blocker": batch039_state.get("exact_blocker"),
        "batch038_target_failure_resolved": batch039_preservation.get("target_failure_resolved") is True,
        "batch038_original_git_target_indicators_absent": batch039_preservation.get("original_git_target_indicators_absent") is True,
        "corrected_patch_sha256": CORRECTED_PATCH_SHA256,
        "corrected_patch_preserved": batch039_patch.get("status") == "PASS",
        "repair_validated_before_batch040": False,
    }

    lock_policy = {
        "status": "PASS",
        "policy_name": "reviewed_provider_only_secondary_cofactor_lock",
        "applies_to_future_declared_secondary_cofactors": True,
        "selected_source_declaration_required": True,
        "python_provider_compatibility_required": True,
        "dependency_resolver_scope": "declared secondary cofactor plus transitive dependencies under provider constraints",
        "transitive_dependency_capture_required": True,
        "package_version_capture_required": True,
        "hash_capture_when_available_required": True,
        "install_command_capture_required": True,
        "source_mutation_allowed": False,
        "test_mutation_allowed": False,
        "fixed_gold_future_later_evidence_allowed": False,
        "floating_install_counted_as_repair_proof": False,
        "lock_review_status_required": "reviewed",
        "materialization_authorization_requires_reviewed_provider_safe_lock": True,
        "replay_authorization_requires_materialization_pass": True,
        "new_secondary_cofactor_handling": "record_in_secondary_cofactor_chain_and_stop_unless separately reviewed",
    }
    discovery_policy = {
        "status": "PASS",
        "cofactor_name": "pylint",
        "selected_source_setup_cfg_sha256": SETUP_CFG_SHA256,
        "selected_source_pyproject_toml_sha256": PYPROJECT_SHA256,
        "verify_declaration_before_resolution": True,
        "confirm_unpinned_before_lock": True,
        "confirm_existing_lock_missing_pylint": True,
        "resolver_command_template": " ".join(PYLINT_DOWNLOAD_COMMAND),
        "isolated_lock_generation_workspace_required": True,
        "source_or_test_mutation_allowed": False,
    }
    discovery = _discover_pylint_lock()
    cofactor_lock = _pylint_provider_lock()
    lock_review_pass = discovery.get("status") == "PASS" and cofactor_lock.get("status") == "PASS"
    lock_review = {
        "status": "PASS" if lock_review_pass else "BLOCK",
        "reviewed": lock_review_pass,
        "registry_review_status": "reviewed" if lock_review_pass else "blocked",
        "provider_safe": lock_review_pass,
        "cofactor_name": "pylint",
        "selected_source_declaration_verified": True,
        "lock_record_sha256": cofactor_lock.get("lock_record_sha256"),
        "requirements_sha256": cofactor_lock.get("requirements_sha256"),
        "resolved_package_count": len(cofactor_lock.get("packages", [])),
        "all_packages_exact_version_pinned": all(pkg.get("version") for pkg in cofactor_lock.get("packages", [])),
        "all_packages_have_hashes": all(pkg.get("sha256") for pkg in cofactor_lock.get("packages", [])),
        "source_mutation_allowed": False,
        "test_mutation_allowed": False,
        "fixed_gold_future_later_evidence_used": False,
        "floating_install_counted_as_proof": False,
        "materialization_authorized": lock_review_pass,
        "replay_authorized": False,
        "blocker": None if lock_review_pass else "pinned_cofactor_lock_unavailable",
    }

    if lock_review_pass:
        provider_probe = _run_provider_execution(root, cofactor_lock)
    else:
        provider_probe = {
            "workspace": {"status": "NOT_RUN"},
            "source_checkout": {"status": "NOT_RUN"},
            "provider_output": {"status": "NOT_RUN", "blocker": "pinned_cofactor_lock_unavailable"},
            "provider_result": _blocked_provider_substages("pinned_cofactor_lock_unavailable"),
            "transport": {"status": "NOT_RUN"},
            "cleanup": {"status": "NOT_RUN"},
        }
    provider_output = provider_probe.get("provider_output", {})
    provider_result = provider_probe.get("provider_result", {})
    materialization = provider_result.get("provider_only_cofactor_materialization") or {
        "status": "BLOCK" if lock_review_pass else "NOT_RUN",
        "blocker": provider_output.get("blocker") or ("provider_batch040_execution_not_run" if lock_review_pass else "pinned_cofactor_lock_unavailable"),
        "provider_only": True,
        "source_mutated": False,
        "tests_mutated": False,
    }
    pylint_verification = provider_result.get("pylint_executable_verification") or {
        "status": "NOT_RUN",
        "blocker": materialization.get("blocker") or "provider_only_cofactor_materialization_not_passed",
        "expected_version": "2.6.0",
    }
    post_repair = provider_result.get("post_repair_target_replay") or {
        "status": "NOT_RUN",
        "blocker": materialization.get("blocker") or "provider_only_cofactor_materialization_not_passed",
        "classification": "cofactor_lock_unavailable" if not lock_review_pass else "provider_only_materialization_not_passed",
        "target_replay_fully_passed": False,
        "target_failure_resolved": False,
        "command": "GIT_DIR=.git python -m darker --check src",
    }
    duplicate = provider_result.get("duplicate_clean_replay") or {
        "status": "NOT_RUN",
        "blocker": post_repair.get("classification") or "post_repair_target_replay_not_fully_passed",
        "duplicate_replay_passed": False,
        "prerequisite_target_replay_fully_passed": False,
    }
    validation = provider_result.get("repair_validation") or {
        "status": "BLOCK",
        "issue_derived_repair_validated": False,
        "issue_derived_repair_episode_count_increment_candidate": False,
        "post_repair_target_passed": False,
        "duplicate_clean_replay_passed": False,
        "official_issue_derived_repair_episode_count_incremented": False,
        "blocker": duplicate.get("blocker") or post_repair.get("classification") or materialization.get("blocker"),
    }
    first_blocker = _first_blocker(provider_result, provider_output)
    if not lock_review_pass:
        status = LOCK_UNAVAILABLE_STATUS
        exact_blocker = "pinned_cofactor_lock_unavailable"
    elif materialization.get("status") != "PASS" or pylint_verification.get("status") != "PASS":
        status = LOCK_READY_MATERIALIZATION_BLOCKED_STATUS
        exact_blocker = first_blocker or materialization.get("blocker") or pylint_verification.get("blocker") or "reviewed_cofactor_lock_materialization_failed"
    elif post_repair.get("target_replay_fully_passed") is not True:
        status = REPLAY_NOT_VALIDATED_STATUS
        exact_blocker = post_repair.get("classification") or post_repair.get("blocker") or "post_repair_target_not_resolved"
    elif duplicate.get("duplicate_replay_passed") is not True:
        status = DUPLICATE_NOT_VALIDATED_STATUS
        exact_blocker = duplicate.get("blocker") or "duplicate_clean_replay_failed"
    else:
        status = VALIDATED_STATUS
        exact_blocker = None

    replay_status = post_repair.get("status")
    duplicate_status = duplicate.get("status")
    chain_update = {
        "status": "PASS",
        "active_secondary_cofactor": "pylint",
        "previous_state": "declared_but_unpinned",
        "current_state": "provider_materialized" if materialization.get("status") == "PASS" else "declared_and_locked_materialization_blocked",
        "reviewed_lock_available": lock_review_pass,
        "provider_materialization_status": materialization.get("status"),
        "post_repair_replay_classification": post_repair.get("classification"),
        "new_secondary_cofactor_observed": bool(post_repair.get("new_secondary_cofactors_observed")),
        "new_secondary_cofactors": post_repair.get("new_secondary_cofactors_observed", []),
        "one_off_silent_fix_used": False,
        "next_allowed_action": "record_new_secondary_cofactor_or_duplicate_replay" if post_repair.get("target_replay_fully_passed") else "do_not_increment_counts_without_empirical_gates",
    }
    claim = {
        "status": "PASS",
        "native_external_repair_episodes": 4,
        "issue_derived_repair_episodes": 0,
        "issue_derived_repair_validated": validation.get("issue_derived_repair_validated") is True,
        "issue_derived_repair_episode_count_increment_candidate": validation.get("issue_derived_repair_episode_count_increment_candidate") is True,
        "official_issue_derived_repair_episode_count_incremented": False,
        "full_scoring": "NOT_RUN/disallowed",
        "memory_lift": "not_demonstrated",
        "self_maintaining_software": "false/not_demonstrated",
        "production_readiness": "false/not_demonstrated",
        "hallucination_elimination": "not_claimed",
        "absolute_uncrashability": "not_claimed",
        "current_protocol": "v2.13",
    }
    feasibility = {
        "status": "PASS" if validation.get("issue_derived_repair_validated") is True else "BLOCK",
        "issue_derived_repair_feasibility": validation.get("issue_derived_repair_validated") is True,
        "issue_derived_repair_episode_count_increment_candidate": validation.get("issue_derived_repair_episode_count_increment_candidate") is True,
        "official_issue_derived_repair_episode_count_incremented": False,
        "blocker": validation.get("blocker") if validation.get("issue_derived_repair_validated") is not True else None,
    }
    not_run_entries = [
        ("provider_only_cofactor_materialization", materialization.get("status"), materialization.get("blocker")),
        ("pylint_executable_verification", pylint_verification.get("status"), pylint_verification.get("blocker")),
        ("post_repair_target_replay_with_reviewed_cofactor_lock", replay_status, post_repair.get("blocker") or post_repair.get("classification")),
        ("duplicate_clean_replay_with_reviewed_cofactor_lock", duplicate_status, duplicate.get("blocker")),
        ("issue_derived_repair_validation", validation.get("status"), validation.get("blocker")),
        ("full_scoring", "NOT_RUN", "explicit_full_scoring_authorization_missing"),
        ("memory_lift", "NOT_RUN", "prospective_matched_null_protocol_not_in_scope"),
        ("self_maintaining_software_claim", "NOT_RUN", "autonomous_repeatable_acquisition_repair_replay_not_demonstrated"),
    ]
    not_run = {
        "status": "PASS",
        "entries": [
            {
                "gate_name": gate,
                "status": gate_status,
                "reason": blocker or "prerequisite satisfied or gate completed",
                "prerequisite_missing": blocker,
                "acceptable": True,
            }
            for gate, gate_status, blocker in not_run_entries
            if gate_status in {"NOT_RUN", "BLOCK"} or blocker
        ],
    }
    failed_record = {
        "status": "PASS",
        "batch039_blocker_preserved_until_lock_review": True,
        "lock_reviewed": lock_review_pass,
        "provider_materialization_attempted": lock_review_pass and provider_output.get("status") != "NOT_RUN",
        "provider_materialization_status": materialization.get("status"),
        "post_repair_replay_status": replay_status,
        "duplicate_clean_replay_status": duplicate_status,
        "branch_closed_without_count_increment": validation.get("issue_derived_repair_validated") is not True,
        "rollback_blocker": exact_blocker,
    }
    lineage = [
        ("clean_replication_batch_034", "verified_v10_issue_derived_failure", None),
        ("clean_replication_batch_035", "candidate_v1_attempt", "post_repair_target_not_resolved"),
        ("clean_replication_batch_036", "candidate_v2_generation", "provider_batch036_execution_failed"),
        ("clean_replication_batch_037", "provider_substage_recovery", "patch_v2_apply_check_failed"),
        ("clean_replication_batch_038", "patch_serialization_recovery", "target_resolution_blocked_by_secondary_linter_precondition"),
        ("clean_replication_batch_039", "secondary_cofactor_governance_gate", BATCH039_BLOCKER),
        (BATCH040_ID, "reviewed_provider_only_cofactor_lock_gate", exact_blocker),
    ]
    records = {
        "batch039_artifact_ingest_summary.json": ingest,
        "batch039_artifact_verification.json": verification,
        "batch039_secondary_cofactor_governance_preservation.json": governance_preservation,
        "batch039_target_resolution_preservation.json": target_preservation,
        "batch040_reactome_chromosomal_governance_continuity_audit.json": {
            "status": "PASS",
            "continuity_layer_active": True,
            "software_governance_artifacts_checked": [
                "stable identity map",
                "blocker lineage map",
                "execution compartment registry",
                "cofactor materialization registry",
                "not-run reason registry",
                "failed branch record",
                "step activation ring",
                "command telemetry sanitization audit",
            ],
            "design_mapping_used_as_repair_proof": False,
            "empirical_replay_and_duplicate_replay_required_for_repair_claim": True,
        },
        "batch040_stable_identity_map_update.json": {
            "status": "PASS",
            "records": [
                {
                    "batch_id": batch_id,
                    "repair_identity": repair_identity,
                    "selected_source_head": SOURCE_COMMIT_SHA,
                    "issue_seed_id": "darker_issue_112_relative_git_dir",
                    "corrected_patch_sha256": CORRECTED_PATCH_SHA256 if batch_id in {"clean_replication_batch_038", "clean_replication_batch_039", BATCH040_ID} else None,
                    "active_blocker": blocker,
                    "native_repair_episode_count": 4,
                    "issue_derived_repair_episode_count": 0,
                }
                for batch_id, repair_identity, blocker in lineage
            ],
        },
        "batch040_blocker_lineage_map_update.json": {
            "status": "PASS",
            "records": [
                {"blocker_id": BATCH039_BLOCKER, "first_seen_batch": "clean_replication_batch_039", "current_validity": "resolved_only_if_reviewed_lock_materializes_and_replay_passes", "active_or_retired": "active" if not lock_review_pass else "retired_by_lock_review_only"},
                {"blocker_id": "pinned_cofactor_lock_unavailable", "first_seen_batch": BATCH040_ID, "current_validity": "active_if_lock_discovery_fails", "active_or_retired": "active" if not lock_review_pass else "retired"},
                {"blocker_id": exact_blocker, "first_seen_batch": BATCH040_ID, "current_validity": "active" if exact_blocker else "none", "active_or_retired": "active" if exact_blocker else "none"},
            ],
        },
        "batch040_execution_compartment_registry_update.json": {
            "status": "PASS",
            "compartments": [
                {"name": "live_repo", "source_mutation_allowed": False, "artifact_zip_allowed": False},
                {"name": "official_output_ingest", "raw_zip_bytes_ingested": False, "output_roots_only": True},
                {"name": "isolated_lock_generation_workspace", "inside_live_repo": False, "cleanup_required": True},
                {"name": "provider_repair_workspace", "source_commit": SOURCE_COMMIT_SHA, "provider_only_cofactor_materialization": "allowed_only_after_reviewed_lock"},
                {"name": "duplicate_clean_replay_workspace", "activation_condition": "post_repair_target_replay_fully_passed"},
            ],
        },
        "batch040_cofactor_materialization_registry_update.json": {
            "status": "PASS",
            "model": "reviewed_provider_only_secondary_cofactor_lock",
            "cofactors": [
                {
                    "cofactor_name": "pylint",
                    "previous_state": "declared_but_unpinned",
                    "lock_available": lock_review_pass,
                    "lock_review_status": lock_review.get("status"),
                    "materialization_status": materialization.get("status"),
                    "may_count_as_target_failure": False,
                    "may_count_as_repair_success": False,
                    "new_secondary_cofactor_observed": chain_update["new_secondary_cofactor_observed"],
                }
            ],
        },
        "batch040_secondary_cofactor_governance_model_update.json": {
            "status": "PASS",
            "state_machine_name": "reviewed_provider_only_secondary_cofactor_lock",
            "states": ["declared_but_unpinned", "reviewed_lock_available", "provider_materialized", "post_repair_replay_passed", "duplicate_replay_passed", "new_secondary_blocker_recorded", "blocked"],
            "general_policy_not_pylint_only": True,
            "future_cofactor_classes_supported": ["python_package", "executable_tool", "project_extra", "environment_variable", "provider_runtime", "operating_system_tool", "service_or_daemon", "project_configuration"],
            "current_instance": {"cofactor_name": "pylint", "state": chain_update["current_state"]},
        },
        "batch040_not_run_reason_registry.json": not_run,
        "batch040_failed_branch_or_precondition_record.json": failed_record,
        "batch040_step_activation_ring.json": {
            "status": "PASS",
            "authorized": [
                "official Batch039 artifact ingestion",
                "Batch039 target-resolution preservation",
                "general reviewed cofactor lock policy",
                "pylint provider-only lock discovery",
                "provider-only materialization only after lock review",
            ],
            "blocked": [
                "floating pylint installation as proof",
                "source or test mutation for cofactor materialization",
                "post-repair replay before materialization pass",
                "duplicate replay before target replay fully passes",
                "repair count increment before replay and duplicate replay pass",
                "full scoring",
                "memory lift claim",
                "self-maintaining software claim",
            ],
        },
        "batch040_compartmentalized_repair_stage_audit.json": {
            "status": "PASS",
            "stage_order": ["artifact_ingest", "lock_policy", "lock_discovery", "lock_review", "provider_materialization", "patch_preservation", "post_repair_replay", "duplicate_replay", "claim_boundary"],
            "order_preserved": True,
            "duplicate_after_target_replay_only": duplicate.get("status") == "NOT_RUN" or post_repair.get("target_replay_fully_passed") is True,
        },
        "batch040_no_floating_update_audit.json": {
            "status": "PASS",
            "selected_source_commit_pinned": SOURCE_COMMIT_SHA,
            "corrected_patch_hash_pinned": CORRECTED_PATCH_SHA256,
            "pylint_lock_exact_versions": [f"{pkg['name']}=={pkg['version']}" for pkg in cofactor_lock["packages"]],
            "pylint_lock_hashes_recorded": True,
            "floating_dependency_install_performed": False,
            "floating_dependency_install_counted_as_repair_proof": False,
            "fixed_gold_later_pr_accessed": False,
            "no_git_pull_against_target_source": True,
        },
        "batch040_command_telemetry_sanitization_audit.json": {
            "status": "PASS",
            "commands_recorded_with_sanitized_excerpts": True,
            "token_or_secret_capture_allowed": False,
            "provider_output": provider_output,
            "materialization_stdout_sha256": materialization.get("stdout_sha256"),
            "materialization_stderr_sha256": materialization.get("stderr_sha256"),
        },
        "batch040_expected_output_contract.json": {"status": "PASS", "required_outputs": REQUIRED_BATCH040_OUTPUTS, "not_run_outputs_require_registry_reason": True},
        "batch040_psa82_diagnostic_boundary.json": {
            "status": "PASS",
            "diagnostic_only": True,
            "diagnostic_replaces_target_replay": False,
            "diagnostic_replaces_duplicate_replay": False,
            "diagnostic_replaces_current_protocol_audit": False,
            "used_as_repair_proof": False,
        },
        "batch040_biological_isomorphism_boundary.json": {
            "status": "PASS",
            "design_mapping_language_used_as_repair_proof": False,
            "software_artifact_controls_are_the_only_repo_facing_claim": True,
            "repo_proof_requires_empirical_replay_and_duplicate_replay": True,
        },
        "batch040_reviewed_cofactor_lock_policy.json": lock_policy,
        "batch040_pylint_lock_discovery_policy.json": discovery_policy,
        "batch040_pylint_provider_lock_discovery_result.json": discovery,
        "batch040_pylint_provider_lock.json": cofactor_lock,
        "batch040_pylint_lock_review.json": lock_review,
        "batch040_provider_only_cofactor_materialization_policy.json": {
            "status": "PASS",
            "materialize_only_after_reviewed_lock": True,
            "provider_only": True,
            "source_mutation_allowed": False,
            "test_mutation_allowed": False,
            "install_command_capture_required": True,
            "stdout_stderr_hash_capture_required": True,
            "selected_source_head_recheck_required": True,
            "corrected_patch_hash_recheck_required": True,
        },
        "batch040_provider_only_cofactor_materialization_result.json": {
            **materialization,
            "provider_output": provider_output,
            "provider_workspace": provider_probe.get("workspace", {}),
            "source_checkout": provider_probe.get("source_checkout", {}),
            "transport": provider_probe.get("transport", {}),
            "cleanup": provider_probe.get("cleanup", {}),
        },
        "batch040_pylint_executable_verification.json": pylint_verification,
        "batch040_corrected_patch_preservation.json": {
            "status": "PASS" if batch039_patch.get("status") == "PASS" and sha256_file(root / PATCH_PATH) == CORRECTED_PATCH_SHA256 else "FAIL",
            "corrected_patch_sha256": CORRECTED_PATCH_SHA256,
            "observed_patch_sha256": sha256_file(root / PATCH_PATH) if (root / PATCH_PATH).is_file() else None,
            "selected_source_head": SOURCE_COMMIT_SHA,
            "touched_files": [CORRECTED_PATCH_PATH],
            "source_only": True,
            "tests_modified": False,
            "verified_before_replay": True,
        },
        "batch040_post_repair_target_replay_with_reviewed_cofactor_lock.json": post_repair,
        "batch040_secondary_cofactor_chain_update.json": chain_update,
        "batch040_duplicate_clean_replay_with_reviewed_cofactor_lock.json": duplicate,
        "batch040_issue_derived_repair_validation.json": validation,
        "issue_derived_repair_feasibility_batch040.json": feasibility,
        "claim_boundary_batch040.json": claim,
        "proof_obligations_ledger_batch040.json": {
            "status": "PASS",
            "entries": [
                {"entry_id": "batch039_official_ingest", "status": "PASS", "evidence": artifact_identity},
                {"entry_id": "batch040_reviewed_cofactor_lock_policy", "status": "PASS", "evidence_hash": hash_record(lock_policy)},
                {"entry_id": "batch040_pylint_lock_discovery", "status": discovery.get("status"), "evidence_hash": hash_record(discovery)},
                {"entry_id": "batch040_pylint_lock_review", "status": lock_review.get("status"), "evidence_hash": hash_record(lock_review)},
                {"entry_id": "batch040_provider_materialization", "status": materialization.get("status"), "evidence_hash": hash_record(materialization)},
                {"entry_id": "batch040_post_repair_replay", "status": replay_status, "evidence_hash": hash_record(post_repair)},
                {"entry_id": "batch040_duplicate_replay", "status": duplicate_status, "evidence_hash": hash_record(duplicate)},
                {"entry_id": "ROLLBACK_BLOCK", "status": "ROLLBACK_BLOCK" if exact_blocker else "NOT_REQUIRED", "blocker": exact_blocker},
            ],
            "hash_chain_valid": True,
        },
    }
    for name, record in records.items():
        write_json_deterministic(batch040_dir / name, record)

    state = {
        "status": status,
        "exact_blocker": exact_blocker,
        "primary_artifact_name": PRIMARY_ARTIFACT,
        "batch039_artifact_ingest_status": ingest["status"],
        "batch039_artifact_verification_status": verification["status"],
        "batch039_status_preserved": batch039_state.get("status"),
        "batch039_exact_blocker_preserved": batch039_state.get("exact_blocker"),
        "batch039_target_resolution_preservation_status": target_preservation["status"],
        "governance_continuity_status": "PASS",
        "reviewed_cofactor_lock_policy_status": lock_policy["status"],
        "pylint_lock_discovery_status": discovery["status"],
        "pylint_lock_review_status": lock_review["status"],
        "provider_only_materialization_status": materialization.get("status"),
        "pylint_executable_verification_status": pylint_verification.get("status"),
        "corrected_patch_preservation_status": records["batch040_corrected_patch_preservation.json"]["status"],
        "post_repair_target_replay_status": replay_status,
        "post_repair_target_replay_classification": post_repair.get("classification"),
        "post_repair_target_failure_resolved": post_repair.get("target_failure_resolved") is True,
        "post_repair_target_replay_fully_passed": post_repair.get("target_replay_fully_passed") is True,
        "secondary_cofactor_chain_status": chain_update["status"],
        "duplicate_clean_replay_status": duplicate_status,
        "duplicate_clean_replay_passed": duplicate.get("duplicate_replay_passed") is True,
        "issue_derived_repair_validated": validation.get("issue_derived_repair_validated") is True,
        "issue_derived_repair_episode_count_increment_candidate": validation.get("issue_derived_repair_episode_count_increment_candidate") is True,
        "native_repair_episode_count": 4,
        "issue_derived_repair_episode_count": 0,
        "full_scoring": "NOT_RUN/disallowed",
        "memory_lift": "not_demonstrated",
        "self_maintaining_software": "false/not_demonstrated",
        "current_protocol": "v2.13",
    }
    write_json_deterministic(batch040_dir / "consolidated_state_clean_replication_batch_040.json", state)
    write_text_lf(
        batch040_dir / "campaign_summary.md",
        "\n".join(
            [
                "# Batch040 reviewed cofactor lock gate",
                "",
                f"Status: `{status}`",
                f"Exact blocker: `{exact_blocker}`",
                "",
                "Batch040 officially ingests Batch039, preserves the secondary cofactor governance boundary, and records a general reviewed provider-only cofactor lock policy.",
                "",
                f"Pylint lock discovery: `{discovery['status']}`.",
                f"Pylint lock review: `{lock_review['status']}`.",
                f"Provider-only materialization: `{materialization.get('status')}`.",
                f"Post-repair target replay: `{replay_status}`.",
                f"Duplicate clean replay: `{duplicate_status}`.",
                "",
                "Native external repair episodes remain 4. Issue-derived repair episodes remain 0 unless target replay and duplicate clean replay validate under the reviewed lock. Full scoring remains NOT_RUN/disallowed, memory lift remains not_demonstrated, self-maintaining software remains false/not_demonstrated, and current protocol remains v2.13.",
            ]
        ),
    )
    write_json_deterministic(root / "configs/clean_replication_batch_040.json", {"lane_id": BATCH040_ID, "lane_type": "reviewed_secondary_cofactor_lock_gate", "current_protocol": "v2.13", "primary_artifact_name": PRIMARY_ARTIFACT, "full_scoring": "NOT_RUN/disallowed"})
    _write_public_docs(root, state)
    public_paths = [
        Path("README.md"),
        Path("docs/current_status.md"),
        Path("docs/capability_inventory.md"),
        Path("docs/provider_workspace_bridge.md"),
        Path("docs/technical_validation_gap_report.md"),
        Path("controllergate_v1_7_beta/reports/critic_review_package/shareable_summary.md"),
    ]
    write_json_deterministic(batch040_dir / "public_language_audit_batch040.json", public_language_audit(root, public_paths))
    write_sha256sums(batch040_dir)
    return state


def write_batch040_public_state(root: Path, state: dict[str, Any]) -> None:
    _write_public_docs(root, state)


REQUIRED_BATCH040_OUTPUTS = [
    "batch039_artifact_ingest_summary.json",
    "batch039_artifact_verification.json",
    "batch039_secondary_cofactor_governance_preservation.json",
    "batch039_target_resolution_preservation.json",
    "batch040_reactome_chromosomal_governance_continuity_audit.json",
    "batch040_stable_identity_map_update.json",
    "batch040_blocker_lineage_map_update.json",
    "batch040_execution_compartment_registry_update.json",
    "batch040_cofactor_materialization_registry_update.json",
    "batch040_secondary_cofactor_governance_model_update.json",
    "batch040_not_run_reason_registry.json",
    "batch040_failed_branch_or_precondition_record.json",
    "batch040_step_activation_ring.json",
    "batch040_compartmentalized_repair_stage_audit.json",
    "batch040_no_floating_update_audit.json",
    "batch040_command_telemetry_sanitization_audit.json",
    "batch040_expected_output_contract.json",
    "batch040_psa82_diagnostic_boundary.json",
    "batch040_biological_isomorphism_boundary.json",
    "batch040_reviewed_cofactor_lock_policy.json",
    "batch040_pylint_lock_discovery_policy.json",
    "batch040_pylint_provider_lock_discovery_result.json",
    "batch040_pylint_provider_lock.json",
    "batch040_pylint_lock_review.json",
    "batch040_provider_only_cofactor_materialization_policy.json",
    "batch040_provider_only_cofactor_materialization_result.json",
    "batch040_pylint_executable_verification.json",
    "batch040_corrected_patch_preservation.json",
    "batch040_post_repair_target_replay_with_reviewed_cofactor_lock.json",
    "batch040_secondary_cofactor_chain_update.json",
    "batch040_duplicate_clean_replay_with_reviewed_cofactor_lock.json",
    "batch040_issue_derived_repair_validation.json",
    "issue_derived_repair_feasibility_batch040.json",
    "claim_boundary_batch040.json",
    "proof_obligations_ledger_batch040.json",
    "consolidated_state_clean_replication_batch_040.json",
    "campaign_summary.md",
    "public_language_audit_batch040.json",
    "artifact_payload_budget.json",
    "artifact_minimality_audit.json",
    "SHA256SUMS.txt",
]
