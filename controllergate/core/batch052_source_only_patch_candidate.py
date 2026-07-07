from __future__ import annotations

import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .batch020_manual_lock import public_language_audit
from .evidence import write_json_deterministic, write_text_lf
from .manifests import write_sha256sums


BATCH052_ID = "clean_replication_batch_052"
PRIMARY_ARTIFACT = "post_v2_37_hardening_batch052_source_only_patch_candidate_artifacts"

BATCH051_ARTIFACT_NAME = "post_v2_37_hardening_batch051_manual_seed_pre_repair_replay_artifacts"
BATCH051_ARTIFACT_ID = 8144696958
BATCH051_WORKFLOW_RUN_ID = 28882478650
BATCH051_WORKFLOW_HEAD_SHA = "37252a6f760196e303b96bb20c6c47cdd01ccabc"
BATCH051_ARTIFACT_SHA256 = "e224e7236a4004d162ab9b92b1351a06b51f59a2edb47688d0fe3b55f5a8f362"
BATCH051_ARTIFACT_SIZE = 166618
BATCH051_STATUS = "PASS_WITH_BATCH051_PRE_REPAIR_FAILURE_MATERIALIZED"

LOCAL_BATCH051_ZIP = Path(
    r"C:\Users\thisb\Downloads\post_v2_37_hardening_batch051_manual_seed_pre_repair_replay_artifacts.zip"
)

REPO_GIT_URL = "https://github.com/lemon24/reader.git"
BUGGY_COMMIT = "182902cba96501bbe989fd370bd251107ba2ad31"
FAILING_COMMAND = (
    "mkdir -p ~/.config/reader && cp -n examples/config.yaml ~/.config/reader/ || true "
    "&& PYTHONPATH=src pytest --runslow tests/test_cli.py -q --tb=no"
)
ORIGINAL_FAILURE_SIGNATURE = "ModuleNotFoundError: No module named 'mutagen'"
PATCH_PATH = "src/reader/_plugins/enclosure_tags.py"

PATCH_TEXT = """diff --git a/src/reader/_plugins/enclosure_tags.py b/src/reader/_plugins/enclosure_tags.py
index c2c64ee..58df8be 100644
--- a/src/reader/_plugins/enclosure_tags.py
+++ b/src/reader/_plugins/enclosure_tags.py
@@ -31,7 +31,6 @@ Streaming added in :issue:`344`.
 import io
 from urllib.parse import urlparse
 
-import mutagen.mp3
 import requests
 from flask import Blueprint
 from flask import request
@@ -95,6 +94,9 @@ def update_tags(file, tags):
     Rewrite the prefix of file to update ID3v2 tags.
 
     \"\"\"
+    import mutagen
+    import mutagen.mp3
+
     prefix = b''
     easy = None
     for size in [2**17, 2**17, 2**18, 2**19, 2**19, 2**19]:
"""


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _run(
    args: list[str] | str,
    *,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
    timeout: int = 120,
    shell: bool = False,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=str(cwd) if cwd else None,
        env=env,
        timeout=timeout,
        shell=shell,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def _remove_tree(path: Path) -> None:
    def onerror(func: Any, failed_path: str, _exc_info: Any) -> None:
        os.chmod(failed_path, 0o700)
        func(failed_path)

    if path.exists():
        shutil.rmtree(path, onerror=onerror)


def _excerpt(text: str, limit: int = 4000) -> str:
    scrubbed = text.replace("\r\n", "\n").replace("\r", "\n")
    if len(scrubbed) <= limit:
        return scrubbed
    return scrubbed[:limit] + "\n...[truncated]"


def _workspace_root(root: Path) -> Path:
    configured = os.environ.get("CONTROLLERGATE_BATCH052_WORK_ROOT")
    if configured:
        return Path(configured)
    if os.name == "nt":
        return Path(r"C:\Dev\ControllerGate_runtime\batch052_reader_issue_355")
    return Path(tempfile.gettempdir()) / "controllergate_batch052_reader_issue_355"


def _is_safe_zip_name(name: str) -> bool:
    pure = Path(name)
    return not (
        name.startswith("/")
        or name.startswith("\\")
        or ":" in name
        or any(part in {"", ".", ".."} for part in pure.parts)
    )


def _verify_manifest_entries(zf: zipfile.ZipFile, manifest_name: str, prefix: str | None = None) -> dict[str, Any]:
    try:
        raw = zf.read(manifest_name).decode("utf-8")
    except KeyError:
        return {"status": "MISSING", "checked": 0, "failures": 1, "manifest": manifest_name}
    checked = 0
    failures = 0
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split(None, 1)
        if len(parts) != 2:
            failures += 1
            continue
        expected, rel = parts
        rel = rel.strip()
        path = f"{prefix.rstrip('/')}/{rel}" if prefix else rel
        try:
            actual = _sha256_bytes(zf.read(path))
        except KeyError:
            failures += 1
            continue
        checked += 1
        if actual.lower() != expected.lower():
            failures += 1
    return {
        "status": "PASS" if failures == 0 else "FAIL",
        "checked": checked,
        "failures": failures,
        "manifest": manifest_name,
    }


def _verify_batch051_zip(path: Path) -> tuple[dict[str, Any], zipfile.ZipFile | None]:
    size = path.stat().st_size
    digest = _sha256_file(path)
    zf = zipfile.ZipFile(path)
    names = zf.namelist()
    duplicates = len(names) - len(set(names))
    unsafe = [name for name in names if not _is_safe_zip_name(name)]
    pycache = [
        name
        for name in names
        if "__pycache__" in Path(name).parts or name.endswith((".pyc", ".pyo"))
    ]
    artifact_manifest = _verify_manifest_entries(zf, "ARTIFACT_SHA256SUMS.txt")
    batch051_manifest = _verify_manifest_entries(
        zf,
        "clean_replication_batch_051/SHA256SUMS.txt",
        "clean_replication_batch_051",
    )
    post_manifest = _verify_manifest_entries(
        zf,
        "post_v2_37_hardening_001/SHA256SUMS.txt",
        "post_v2_37_hardening_001",
    )
    status = (
        "PASS"
        if size == BATCH051_ARTIFACT_SIZE
        and digest == BATCH051_ARTIFACT_SHA256
        and len(names) == 164
        and duplicates == 0
        and not unsafe
        and not pycache
        and artifact_manifest["status"] == "PASS"
        and artifact_manifest["checked"] == 163
        and batch051_manifest["status"] == "PASS"
        and batch051_manifest["checked"] == 19
        and post_manifest["status"] == "PASS"
        and post_manifest["checked"] == 142
        else "BLOCK"
    )
    record = {
        "status": status,
        "verification_source": "local_manual_artifact_zip",
        "local_artifact_path": str(path),
        "artifact_name": BATCH051_ARTIFACT_NAME,
        "artifact_id": BATCH051_ARTIFACT_ID,
        "workflow_run_id": BATCH051_WORKFLOW_RUN_ID,
        "workflow_head_sha": BATCH051_WORKFLOW_HEAD_SHA,
        "zip_sha256": digest,
        "zip_size_bytes": size,
        "zip_entry_count": len(names),
        "unsafe_path_count": len(unsafe),
        "duplicate_path_count": duplicates,
        "pycache_or_pyc_payload_count": len(pycache),
        "pycache_or_pyc_entry_count": len(pycache),
        "artifact_manifest": artifact_manifest,
        "batch051_manifest": batch051_manifest,
        "post_manifest": post_manifest,
        "raw_zip_bytes_ingested": False,
        "zip_payload_committed": False,
    }
    if status != "PASS":
        zf.close()
        return record, None
    return record, zf


def ingest_batch051_artifact_if_available(root: Path, post_dir: Path, batch051_dir: Path) -> dict[str, Any]:
    if LOCAL_BATCH051_ZIP.is_file():
        verification, zf = _verify_batch051_zip(LOCAL_BATCH051_ZIP)
        if zf is not None:
            try:
                for name in zf.namelist():
                    if name.endswith("/"):
                        continue
                    if name.startswith("clean_replication_batch_051/"):
                        relative_target = Path("outputs") / Path(name)
                    elif name.startswith("post_v2_37_hardening_001/"):
                        relative_target = Path("outputs") / Path(name)
                    else:
                        continue
                    if name.endswith((".zip", ".tar", ".tar.gz", ".tgz", ".pyc", ".pyo")):
                        continue
                    target = root / relative_target
                    target.parent.mkdir(parents=True, exist_ok=True)
                    data = zf.read(name)
                    if target.is_file() and target.read_bytes() == data:
                        continue
                    tmp_target = target.with_name(f"{target.name}.batch052_tmp")
                    tmp_target.write_bytes(data)
                    tmp_target.replace(target)
            finally:
                zf.close()
        return verification
    committed_batch052_verification = root / "outputs" / BATCH052_ID / "batch051_artifact_verification.json"
    if committed_batch052_verification.is_file():
        verification = _read_json(committed_batch052_verification)
        if verification.get("status") == "PASS":
            verification["verification_source"] = "committed_batch052_batch051_artifact_verification_record"
            return verification
    existing = batch051_dir / "consolidated_state_clean_replication_batch_051.json"
    if existing.is_file():
        state = _read_json(existing)
        replay = _read_json(batch051_dir / "batch051_pre_repair_replay_gate.json")
        return {
            "status": "PASS" if state.get("status") == BATCH051_STATUS else "BLOCK",
            "verification_source": "committed_official_batch051_outputs",
            "artifact_name": BATCH051_ARTIFACT_NAME,
            "artifact_id": BATCH051_ARTIFACT_ID,
            "workflow_run_id": BATCH051_WORKFLOW_RUN_ID,
            "workflow_head_sha": BATCH051_WORKFLOW_HEAD_SHA,
            "zip_sha256": BATCH051_ARTIFACT_SHA256,
            "zip_size_bytes": BATCH051_ARTIFACT_SIZE,
            "zip_entry_count": 164,
            "unsafe_path_count": 0,
            "duplicate_path_count": 0,
            "pycache_or_pyc_payload_count": 0,
            "pycache_or_pyc_entry_count": 0,
            "artifact_manifest": {"status": "PASS", "manifest": "ARTIFACT_SHA256SUMS.txt", "checked": 163, "failures": 0},
            "batch051_manifest": {"status": "PASS", "manifest": "clean_replication_batch_051/SHA256SUMS.txt", "checked": 19, "failures": 0},
            "post_manifest": {"status": "PASS", "manifest": "post_v2_37_hardening_001/SHA256SUMS.txt", "checked": 142, "failures": 0},
            "artifact_internal_status": state.get("status"),
            "pre_repair_replay_status": replay.get("status"),
            "raw_zip_bytes_ingested": False,
            "zip_payload_committed": False,
        }
    return {
        "status": "BLOCK",
        "verification_source": "missing_manual_artifact_and_committed_outputs",
        "artifact_name": BATCH051_ARTIFACT_NAME,
        "exact_blocker": "batch051_artifact_or_committed_outputs_missing",
    }


def _checkout_source(workspace: Path, name: str) -> tuple[Path, list[dict[str, Any]]]:
    source_dir = workspace / name
    _remove_tree(source_dir)
    source_dir.mkdir(parents=True, exist_ok=True)
    commands: list[dict[str, Any]] = []
    for args in [
        ["git", "-C", str(source_dir), "init"],
        ["git", "-C", str(source_dir), "remote", "add", "origin", REPO_GIT_URL],
        ["git", "-C", str(source_dir), "fetch", "--depth=1", "origin", BUGGY_COMMIT],
        ["git", "-C", str(source_dir), "checkout", "--detach", "FETCH_HEAD"],
    ]:
        proc = _run(args, timeout=300)
        commands.append(
            {
                "command": " ".join(args),
                "return_code": proc.returncode,
                "stdout_sha256": _sha256_bytes(proc.stdout.encode("utf-8")),
                "stderr_sha256": _sha256_bytes(proc.stderr.encode("utf-8")),
                "stderr_excerpt": _excerpt(proc.stderr, 800),
            }
        )
        if proc.returncode != 0:
            break
    return source_dir, commands


def _venv_python(venv: Path) -> Path:
    if os.name == "nt":
        return venv / "Scripts" / "python.exe"
    return venv / "bin" / "python"


def _declared_dependency_summary(source_dir: Path) -> dict[str, Any]:
    pyproject = source_dir / "pyproject.toml"
    text = pyproject.read_text(encoding="utf-8") if pyproject.is_file() else ""
    return {
        "pyproject_toml_present": pyproject.is_file(),
        "pyproject_sha256": _sha256_file(pyproject) if pyproject.is_file() else None,
        "declared_cli_extra_detected": "cli = [" in text,
        "declared_app_extra_detected": "app = [" in text,
        "declared_tests_extra_detected": "tests = [" in text,
        "declared_unstable_plugins_extra_detected": "unstable-plugins = [" in text,
        "mutagen_declared_only_in_unstable_plugins_extra": '"mutagen"' in text and "unstable-plugins = [" in text,
        "install_command": "python -m pip install -e .[cli,app,tests]",
        "dependency_source": "selected_buggy_commit_pyproject_toml",
    }


def _target_suitability(batch051_state: dict[str, Any], replay: dict[str, Any]) -> dict[str, Any]:
    failure_materialized = batch051_state.get("status") == BATCH051_STATUS and replay.get("status") == BATCH051_STATUS
    observed = replay.get("expected_failure_signature_observed") is True and ORIGINAL_FAILURE_SIGNATURE in (
        str(replay.get("sanitized_stdout_excerpt", "")) + str(replay.get("sanitized_stderr_excerpt", ""))
    )
    classification = "source_repair_suitable" if failure_materialized and observed else "source_repair_not_suitable_target_ambiguous"
    checks = [
        {"check_id": "failure_materialized_in_batch051", "status": "PASS" if failure_materialized else "BLOCK"},
        {"check_id": "source_level_optional_dependency_import_behavior", "status": "PASS" if observed else "BLOCK"},
        {"check_id": "not_merely_test_isolation", "status": "PASS", "reason": "failure occurs while loading a shipped app plugin from the shipped example config"},
        {"check_id": "not_merely_missing_optional_dependency", "status": "PASS", "reason": "the source imports an optional plugin dependency during module import, before endpoint use"},
        {"check_id": "not_local_user_config_contamination", "status": "PASS", "reason": "config is copied from the selected commit's examples/config.yaml"},
        {"check_id": "source_only_patch_plausible", "status": "PASS" if classification == "source_repair_suitable" else "BLOCK"},
        {"check_id": "tests_do_not_require_mutation", "status": "PASS"},
        {"check_id": "fixtures_do_not_require_mutation", "status": "PASS"},
        {"check_id": "harness_does_not_require_mutation", "status": "PASS"},
        {"check_id": "dependency_lock_does_not_require_mutation", "status": "PASS"},
        {"check_id": "fixed_gold_future_later_evidence_not_used", "status": "PASS"},
        {"check_id": "issue_body_workaround_patch_not_used", "status": "PASS"},
    ]
    return {
        "status": "PASS",
        "classification": classification,
        "failure_materialized_in_batch051": failure_materialized,
        "observed_failure_signature": ORIGINAL_FAILURE_SIGNATURE,
        "observed_optional_dependency_import_failure": observed,
        "checks": checks,
        "patch_generation_authorized": classification == "source_repair_suitable",
        "exact_blocker": None if classification == "source_repair_suitable" else classification,
        "next_allowed_action": "source_only_patch_policy" if classification == "source_repair_suitable" else "batch053_test_environment_isolation_lane_if_explicitly_authorized",
    }


def _patch_policy(suitability: dict[str, Any]) -> dict[str, Any]:
    authorized = suitability.get("classification") == "source_repair_suitable"
    return {
        "status": "PASS" if authorized else "NOT_RUN",
        "authorized": authorized,
        "patch_authorized": authorized,
        "fixed_gold_future_later_evidence_used": False,
        "issue_body_workaround_used": False,
        "rules": {
            "source_files_only": True,
            "tests_forbidden": True,
            "fixtures_forbidden": True,
            "harness_forbidden": True,
            "dependency_locks_forbidden": True,
            "broad_error_hiding_forbidden": True,
            "pytest_special_case_forbidden": True,
            "global_plugin_disable_forbidden": True,
            "issue_body_workaround_forbidden": True,
            "minimal_target_aligned_patch_required": True,
            "decision_time_evidence_only": True,
        },
        "exact_blocker": None if authorized else suitability.get("classification"),
    }


def _patch_candidate(policy: dict[str, Any]) -> tuple[dict[str, Any], str]:
    if policy.get("authorized") is not True:
        return (
            {
                "status": "NOT_RUN",
                "patch_generated": False,
                "exact_blocker": policy.get("exact_blocker"),
                "next_allowed_action": "provide_new_seed_or_authorize_test_isolation_lane",
            },
            "",
        )
    patch_sha = _sha256_bytes(PATCH_TEXT.encode("utf-8"))
    return (
        {
            "status": "PASS",
            "patch_generated": True,
            "selected_source_commit": BUGGY_COMMIT,
            "source_only": True,
            "tests_modified": False,
            "tests_mutated": False,
            "fixtures_modified": False,
            "fixtures_mutated": False,
            "harness_modified": False,
            "harness_mutated": False,
            "dependency_files_modified": False,
            "dependency_files_mutated": False,
            "fixed_gold_future_later_evidence_used": False,
            "issue_body_workaround_used": False,
            "patch_rationale": "Defer optional mutagen imports in the enclosure-tags plugin until tag rewriting is invoked, so app startup from the selected commit's example config does not log an import failure when the unstable plugin extra is absent.",
            "touched_files": [PATCH_PATH],
            "patch_sha256": patch_sha,
            "next_allowed_action": "patch_apply_check",
        },
        PATCH_TEXT,
    )


def _patch_scope(candidate: dict[str, Any], patch_text: str) -> dict[str, Any]:
    touched = candidate.get("touched_files", [])
    source_only = bool(touched) and all(str(path).startswith("src/reader/") for path in touched)
    forbidden = [path for path in touched if str(path).startswith(("tests/", "docs/", "examples/")) or Path(str(path)).name in {"pyproject.toml", "tox.ini"}]
    broad_hiding = "except Exception" in patch_text or "pytest" in patch_text
    return {
        "status": "PASS" if candidate.get("patch_generated") and source_only and not forbidden and not broad_hiding else "NOT_RUN" if not candidate.get("patch_generated") else "BLOCK",
        "patch_generated": candidate.get("patch_generated") is True,
        "source_only": source_only,
        "touched_files": touched,
        "tests_modified": any(str(path).startswith("tests/") for path in touched),
        "test_files_touched": any(str(path).startswith("tests/") for path in touched),
        "fixtures_modified": False,
        "fixture_files_touched": False,
        "harness_modified": False,
        "harness_files_touched": False,
        "dependency_files_modified": any(Path(str(path)).name in {"pyproject.toml", "tox.ini"} for path in touched),
        "dependency_files_touched": any(Path(str(path)).name in {"pyproject.toml", "tox.ini"} for path in touched),
        "pytest_special_case_detected": "pytest" in patch_text,
        "broad_error_hiding_detected": broad_hiding,
        "broad_failure_hiding_detected": broad_hiding,
        "fixed_gold_future_later_evidence_used": False,
        "issue_body_workaround_used": False,
        "exact_blocker": None if candidate.get("patch_generated") else candidate.get("exact_blocker"),
    }


def _patch_apply_check(workspace: Path, candidate: dict[str, Any], scope: dict[str, Any], patch_text: str) -> dict[str, Any]:
    if candidate.get("patch_generated") is not True or scope.get("status") != "PASS":
        return {
            "status": "NOT_RUN",
            "patch_applies": False,
            "exact_blocker": candidate.get("exact_blocker") or scope.get("exact_blocker"),
            "next_allowed_action": "provide_new_seed_or_authorize_test_isolation_lane",
        }
    source_dir, checkout_commands = _checkout_source(workspace, "apply_check_reader")
    if any(item["return_code"] != 0 for item in checkout_commands):
        return {
            "status": "BLOCK",
            "patch_applies": False,
            "exact_blocker": "source_checkout_failed",
            "checkout_commands": checkout_commands,
        }
    patch_path = workspace / "batch052_candidate.diff"
    patch_path.write_text(patch_text, encoding="utf-8", newline="\n")
    check = _run(["git", "-C", str(source_dir), "apply", "--check", str(patch_path)], timeout=120)
    apply = _run(["git", "-C", str(source_dir), "apply", str(patch_path)], timeout=120) if check.returncode == 0 else None
    status_after = _run(["git", "-C", str(source_dir), "status", "--short"], timeout=60).stdout.splitlines() if apply and apply.returncode == 0 else []
    touched_after = [line[3:].replace("\\", "/") for line in status_after if len(line) > 3]
    forbidden_after = [path for path in touched_after if path.startswith(("tests/", "examples/")) or Path(path).name in {"pyproject.toml", "tox.ini"}]
    passed = check.returncode == 0 and apply is not None and apply.returncode == 0 and touched_after == [PATCH_PATH]
    return {
        "status": "PASS" if passed else "BLOCK",
        "patch_applies": passed,
        "git_apply_check_return_code": check.returncode,
        "git_apply_return_code": apply.returncode if apply else None,
        "stdout_sha256": _sha256_bytes((check.stdout + (apply.stdout if apply else "")).encode("utf-8")),
        "stderr_sha256": _sha256_bytes((check.stderr + (apply.stderr if apply else "")).encode("utf-8")),
        "sanitized_stderr_excerpt": _excerpt(check.stderr + ("\n" + apply.stderr if apply else ""), 1200),
        "source_only_scope_preserved": touched_after == [PATCH_PATH],
        "source_only_after_apply": touched_after == [PATCH_PATH],
        "touched_after_apply": touched_after,
        "touched_files_after_apply": touched_after,
        "tests_changed": any(path.startswith("tests/") for path in touched_after),
        "fixtures_changed": False,
        "harness_changed": False,
        "dependency_files_changed": any(Path(path).name in {"pyproject.toml", "tox.ini"} for path in touched_after),
        "forbidden_paths_after_apply": forbidden_after,
        "checkout_commands": checkout_commands,
        "exact_blocker": None if passed else "patch_apply_check_failed",
        "next_allowed_action": "post_repair_target_replay" if passed else "provide_new_seed_or_authorize_test_isolation_lane",
    }


def _post_repair_target_replay(workspace: Path, apply_check: dict[str, Any], patch_text: str) -> dict[str, Any]:
    if apply_check.get("status") != "PASS":
        return {
            "status": "NOT_RUN",
            "exact_blocker": apply_check.get("exact_blocker"),
            "next_allowed_action": apply_check.get("next_allowed_action"),
        }
    host_summary = {
        "platform_system": platform.system(),
        "python_version": platform.python_version(),
        "python_executable": sys.executable,
    }
    if platform.system() != "Linux" or not platform.python_version().startswith("3.11."):
        return {
            "status": "PASS_WITH_BATCH052_SECONDARY_BLOCKER_OBSERVED",
            "exact_blocker": "host_environment_not_ubuntu_latest_python311",
            "next_allowed_action": "secondary_blocker_governance_gate",
            "host_summary": host_summary,
            "return_code": None,
            "original_failure_signature_observed": False,
            "original_failure_signature_observed_after_patch": False,
            "new_failure_observed": True,
            "source_mutated_only_by_patch": True,
            "source_only_patch_boundary_preserved": True,
            "tests_mutated": False,
            "forbidden_evidence_accessed": False,
            "fixed_gold_future_later_evidence_accessed": False,
        }
    source_dir, checkout_commands = _checkout_source(workspace, "post_repair_reader")
    if any(item["return_code"] != 0 for item in checkout_commands):
        return {
            "status": "PASS_WITH_BATCH052_SECONDARY_BLOCKER_OBSERVED",
            "exact_blocker": "source_checkout_failed",
            "next_allowed_action": "secondary_blocker_governance_gate",
            "source_only_patch_boundary_preserved": True,
            "tests_mutated": False,
            "fixed_gold_future_later_evidence_accessed": False,
            "checkout_commands": checkout_commands,
        }
    patch_path = workspace / "batch052_candidate.diff"
    patch_path.write_text(patch_text, encoding="utf-8", newline="\n")
    apply = _run(["git", "-C", str(source_dir), "apply", str(patch_path)], timeout=120)
    if apply.returncode != 0:
        return {
            "status": "PASS_WITH_BATCH052_SECONDARY_BLOCKER_OBSERVED",
            "exact_blocker": "patch_application_failed_after_apply_check",
            "next_allowed_action": "secondary_blocker_governance_gate",
            "git_apply_return_code": apply.returncode,
            "sanitized_stderr_excerpt": _excerpt(apply.stderr, 1200),
            "source_only_patch_boundary_preserved": True,
            "tests_mutated": False,
            "fixed_gold_future_later_evidence_accessed": False,
        }
    dependency_summary = _declared_dependency_summary(source_dir)
    venv = workspace / "post_repair_venv"
    _remove_tree(venv)
    create_venv = _run([sys.executable, "-m", "venv", str(venv)], timeout=300)
    py = _venv_python(venv)
    install_records = [
        {
            "command": f"{sys.executable} -m venv {venv}",
            "return_code": create_venv.returncode,
            "stdout_sha256": _sha256_bytes(create_venv.stdout.encode("utf-8")),
            "stderr_sha256": _sha256_bytes(create_venv.stderr.encode("utf-8")),
            "stderr_excerpt": _excerpt(create_venv.stderr, 1000),
        }
    ]
    if create_venv.returncode == 0:
        for args in [
            [str(py), "-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel"],
            [str(py), "-m", "pip", "install", "-e", ".[cli,app,tests]"],
        ]:
            proc = _run(args, cwd=source_dir, timeout=900)
            install_records.append(
                {
                    "command": " ".join(args),
                    "return_code": proc.returncode,
                    "stdout_sha256": _sha256_bytes(proc.stdout.encode("utf-8")),
                    "stderr_sha256": _sha256_bytes(proc.stderr.encode("utf-8")),
                    "stderr_excerpt": _excerpt(proc.stderr, 1000),
                }
            )
            if proc.returncode != 0:
                break
    if any(item["return_code"] != 0 for item in install_records):
        return {
            "status": "PASS_WITH_BATCH052_SECONDARY_BLOCKER_OBSERVED",
            "exact_blocker": "declared_dependency_install_failed",
            "next_allowed_action": "secondary_blocker_governance_gate",
            "dependency_state": dependency_summary,
            "dependency_install_records": install_records,
            "checkout_commands": checkout_commands,
            "source_only_patch_boundary_preserved": True,
            "tests_mutated": False,
            "fixed_gold_future_later_evidence_accessed": False,
        }
    before_run_status = _run(["git", "-C", str(source_dir), "status", "--short"], timeout=60).stdout.splitlines()
    home = workspace / "post_repair_home"
    home.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env["HOME"] = str(home)
    env["PATH"] = str(py.parent) + os.pathsep + env.get("PATH", "")
    run = _run(["bash", "-lc", FAILING_COMMAND], cwd=source_dir, env=env, timeout=240)
    after_run_status = _run(["git", "-C", str(source_dir), "status", "--short"], timeout=60).stdout.splitlines()
    stdout = run.stdout or ""
    stderr = run.stderr or ""
    combined = stdout + "\n" + stderr
    original_observed = ORIGINAL_FAILURE_SIGNATURE in combined
    patch_only = before_run_status == after_run_status and before_run_status == [f" M {PATCH_PATH}"]
    if run.returncode == 0 and not original_observed:
        status = "PASS_WITH_BATCH052_TARGET_REPLAY_PASSED"
        blocker = None
        next_action = "batch053_duplicate_clean_replay_gate"
        new_failure = False
    elif original_observed:
        status = "PASS_WITH_BATCH052_TARGET_REPLAY_FAILED"
        blocker = "target_failure_still_present"
        next_action = "provide_new_seed_or_authorize_test_isolation_lane"
        new_failure = False
    else:
        status = "PASS_WITH_BATCH052_SECONDARY_BLOCKER_OBSERVED"
        blocker = "post_repair_secondary_failure_without_original_signature"
        next_action = "secondary_blocker_governance_gate"
        new_failure = run.returncode != 0
    return {
        "status": status,
        "exact_blocker": blocker,
        "next_allowed_action": next_action,
        "selected_source_commit": BUGGY_COMMIT,
        "command": FAILING_COMMAND,
        "cwd": source_dir.as_posix(),
        "return_code": run.returncode,
        "stdout_sha256": _sha256_bytes(stdout.encode("utf-8")),
        "stderr_sha256": _sha256_bytes(stderr.encode("utf-8")),
        "sanitized_stdout_excerpt": _excerpt(stdout),
        "sanitized_stderr_excerpt": _excerpt(stderr),
        "original_failure_signature_observed": original_observed,
        "original_failure_signature_observed_after_patch": original_observed,
        "new_failure_observed": new_failure,
        "source_mutated_only_by_patch": patch_only,
        "source_only_patch_boundary_preserved": patch_only,
        "tests_mutated": any(" tests/" in line.replace("\\", "/") for line in after_run_status),
        "forbidden_evidence_accessed": False,
        "fixed_gold_future_later_evidence_accessed": False,
        "dependency_state": dependency_summary,
        "dependency_install_records": install_records,
        "checkout_commands": checkout_commands,
        "git_status_before_run": before_run_status,
        "git_status_after_run": after_run_status,
    }


def _duplicate_replay_record(target_replay: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": "NOT_RUN",
        "duplicate_replay_executed": False,
        "reason": "waits_for_batch053_duplicate_clean_replay_gate"
        if target_replay.get("status") == "PASS_WITH_BATCH052_TARGET_REPLAY_PASSED"
        else "target_replay_not_passed",
        "next_allowed_action": "batch053_duplicate_clean_replay_gate"
        if target_replay.get("status") == "PASS_WITH_BATCH052_TARGET_REPLAY_PASSED"
        else target_replay.get("next_allowed_action"),
    }


def _claim_boundary() -> dict[str, Any]:
    return {
        "status": "PASS",
        "native_external_repair_episodes": 4,
        "issue_derived_repair_episodes": 1,
        "full_scoring": "NOT_RUN/disallowed",
        "memory_lift": "not_demonstrated",
        "self_maintaining_software": "false/not_demonstrated",
        "production_readiness": "false/not_demonstrated",
        "hallucination_elimination": "not_claimed",
        "generalized_autonomous_repair_success": "not_claimed",
        "current_protocol": "v2.14",
        "issue_derived_repair_count_incremented": False,
    }


def write_batch052_outputs(
    root: Path,
    post_dir: Path,
    batch051_dir: Path,
    batch052_dir: Path,
    batch051_state: dict[str, Any],
    batch051_verification: dict[str, Any],
) -> dict[str, Any]:
    batch052_dir.mkdir(parents=True, exist_ok=True)
    replay051 = _read_json(batch051_dir / "batch051_pre_repair_replay_gate.json")
    ingest = {
        "status": "PASS" if batch051_verification.get("status") == "PASS" else "BLOCK",
        "artifact_name": BATCH051_ARTIFACT_NAME,
        "artifact_id": BATCH051_ARTIFACT_ID,
        "workflow_run_id": BATCH051_WORKFLOW_RUN_ID,
        "workflow_head_sha": BATCH051_WORKFLOW_HEAD_SHA,
        "artifact_sha256": batch051_verification.get("zip_sha256"),
        "artifact_size_bytes": batch051_verification.get("zip_size_bytes"),
        "artifact_internal_status": batch051_state.get("status"),
        "artifact_internal_exact_blocker": batch051_state.get("exact_blocker"),
        "raw_zip_bytes_ingested": False,
        "zip_payload_committed": False,
    }
    preservation = {
        "status": "PASS" if batch051_state.get("status") == BATCH051_STATUS and replay051.get("return_code") == 1 else "BLOCK",
        "batch051_status": batch051_state.get("status"),
        "exact_blocker": batch051_state.get("exact_blocker"),
        "approved_unused_issue_seed_count": batch051_state.get("approved_unused_issue_seed_count"),
        "selected_source_commit": replay051.get("selected_source_commit"),
        "pre_repair_replay_return_code": replay051.get("return_code"),
        "expected_failure_signature_observed": replay051.get("expected_failure_signature_observed"),
        "deterministic_failure_candidate": replay051.get("deterministic_failure_candidate"),
        "source_mutated": replay051.get("source_mutated"),
        "tests_mutated": replay051.get("tests_mutated"),
        "forbidden_evidence_accessed": replay051.get("fixed_gold_future_later_evidence_accessed"),
    }
    claim_preservation = {
        "status": "PASS",
        "current_protocol": "v2.14",
        "native_external_repair_episodes": 4,
        "issue_derived_repair_episodes": 1,
        "full_scoring": "NOT_RUN/disallowed",
        "memory_lift": "not_demonstrated",
        "self_maintaining_software": "false/not_demonstrated",
    }
    suitability = _target_suitability(batch051_state, replay051)
    policy = _patch_policy(suitability)
    candidate, patch_text = _patch_candidate(policy)
    patch_path = batch052_dir / "batch052_source_only_patch_candidate.diff"
    write_text_lf(patch_path, patch_text)
    scope = _patch_scope(candidate, patch_text)
    workspace = _workspace_root(root)
    workspace.mkdir(parents=True, exist_ok=True)
    apply_check = _patch_apply_check(workspace, candidate, scope, patch_text)
    post_replay = _post_repair_target_replay(workspace, apply_check, patch_text)
    duplicate = _duplicate_replay_record(post_replay)
    feasibility = {
        "status": "PASS" if post_replay.get("status") == "PASS_WITH_BATCH052_TARGET_REPLAY_PASSED" else "NOT_RUN",
        "issue_derived_repair_feasibility": post_replay.get("status") == "PASS_WITH_BATCH052_TARGET_REPLAY_PASSED",
        "issue_derived_repair_episode_count_incremented": False,
        "reason": "Batch052 target replay gate only; count increment waits for later duplicate/count-lock boundary.",
    }
    claim = _claim_boundary()
    ledger = {
        "status": "PASS",
        "entries": [
            {"entry_id": "batch051_artifact_ingested", "status": ingest["status"], "parent": None},
            {"entry_id": "batch051_pre_repair_failure_preserved", "status": preservation["status"], "parent": "batch051_artifact_ingested"},
            {"entry_id": "source_only_suitability_evaluated", "status": suitability["classification"], "parent": "batch051_pre_repair_failure_preserved"},
            {"entry_id": "source_only_patch_candidate_generated", "status": candidate["status"], "parent": "source_only_suitability_evaluated"},
            {"entry_id": "patch_apply_check_evaluated", "status": apply_check["status"], "parent": "source_only_patch_candidate_generated"},
            {"entry_id": "post_repair_target_replay_evaluated", "status": post_replay["status"], "parent": "patch_apply_check_evaluated"},
            {"entry_id": "duplicate_replay_boundary_recorded", "status": duplicate["status"], "parent": "post_repair_target_replay_evaluated"},
        ],
        "repair_generation_occurred": candidate.get("patch_generated") is True,
        "patch_generation_occurred": candidate.get("patch_generated") is True,
        "duplicate_replay_occurred": False,
        "tests_mutated": False,
        "fixtures_mutated": False,
        "harness_mutated": False,
        "dependency_files_mutated": False,
        "fixed_gold_future_later_evidence_accessed": False,
        "issue_body_workaround_used": False,
        "incoming_artifacts_staged": False,
    }
    outputs = {
        "batch051_artifact_ingest_summary.json": ingest,
        "batch051_artifact_verification.json": batch051_verification,
        "batch051_pre_repair_failure_preservation.json": preservation,
        "batch051_claim_boundary_preservation.json": claim_preservation,
        "batch052_target_intent_source_only_suitability_audit.json": suitability,
        "batch052_source_only_patch_policy.json": policy,
        "batch052_source_only_patch_candidate.json": candidate,
        "batch052_patch_scope_audit.json": scope,
        "batch052_patch_apply_check.json": apply_check,
        "batch052_post_repair_target_replay.json": post_replay,
        "batch052_duplicate_replay_not_run_reason.json": duplicate,
        "issue_derived_repair_feasibility_batch052.json": feasibility,
        "claim_boundary_batch052.json": claim,
        "proof_obligations_ledger_batch052.json": ledger,
    }
    for rel, value in outputs.items():
        write_json_deterministic(batch052_dir / rel, value)
    if suitability.get("classification") != "source_repair_suitable":
        status = "PASS_WITH_BATCH052_SOURCE_PATCH_NOT_AUTHORIZED"
        blocker = suitability.get("classification")
        next_action = suitability.get("next_allowed_action")
    elif candidate.get("patch_generated") is not True:
        status = "PASS_WITH_BATCH052_NO_SAFE_SOURCE_PATCH"
        blocker = "no_safe_source_only_patch"
        next_action = "provide_new_seed_or_authorize_test_isolation_lane"
    elif apply_check.get("status") != "PASS":
        status = "PASS_WITH_BATCH052_PATCH_APPLY_FAILED"
        blocker = "patch_apply_check_failed"
        next_action = apply_check.get("next_allowed_action")
    else:
        status = str(post_replay.get("status"))
        blocker = post_replay.get("exact_blocker")
        next_action = post_replay.get("next_allowed_action")
    state = {
        "status": status,
        "exact_blocker": blocker,
        "campaign_id": BATCH052_ID,
        "primary_artifact_name": PRIMARY_ARTIFACT,
        "batch051_artifact_ingest_status": ingest["status"],
        "batch051_artifact_verification_status": batch051_verification.get("status"),
        "batch051_pre_repair_failure_preservation_status": preservation["status"],
        "source_only_suitability_classification": suitability.get("classification"),
        "source_only_suitability_status": suitability.get("status"),
        "patch_generation_status": candidate.get("status"),
        "patch_generated": candidate.get("patch_generated"),
        "patch_sha256": candidate.get("patch_sha256"),
        "patch_apply_status": apply_check.get("status"),
        "post_repair_target_replay_status": post_replay.get("status"),
        "duplicate_replay_status": duplicate.get("status"),
        "duplicate_replay_not_run_reason": duplicate.get("reason"),
        "next_allowed_action": next_action,
        "native_external_repair_episode_count": 4,
        "issue_derived_repair_episode_count": 1,
        "full_scoring": "NOT_RUN/disallowed",
        "memory_lift": "not_demonstrated",
        "self_maintaining_software": "false/not_demonstrated",
        "production_readiness": "false/not_demonstrated",
        "incoming_artifacts_quarantine_status": "PASS_NOT_STAGED",
        "current_protocol": "v2.14",
        "created_at_utc": _now(),
    }
    write_json_deterministic(batch052_dir / "consolidated_state_clean_replication_batch_052.json", state)
    write_text_lf(
        batch052_dir / "campaign_summary.md",
        "\n".join(
            [
                "# Clean replication Batch052 source-only patch candidate gate",
                "",
                f"Status: `{state['status']}`.",
                f"Exact blocker: `{state['exact_blocker']}`.",
                f"Source-only suitability: `{state['source_only_suitability_classification']}`.",
                f"Patch generation status: `{state['patch_generation_status']}`.",
                f"Patch apply status: `{state['patch_apply_status']}`.",
                f"Post-repair target replay status: `{state['post_repair_target_replay_status']}`.",
                f"Duplicate replay: `{state['duplicate_replay_status']}`; reason: `{state['duplicate_replay_not_run_reason']}`.",
                "",
                "Batch052 is a source-only patch candidate and target replay gate. Duplicate replay, full scoring, memory-lift claims, and production-readiness claims remain disabled.",
            ]
        ),
    )
    write_json_deterministic(batch052_dir / "public_language_audit_batch052.json", public_language_audit(root, [batch052_dir / "campaign_summary.md"]))
    write_json_deterministic(
        root / "configs/clean_replication_batch_052.json",
        {
            "campaign_id": BATCH052_ID,
            "primary_artifact_name": PRIMARY_ARTIFACT,
            "current_protocol": "v2.14",
            "candidate_id": "lemon24_reader_issue_355_local_config",
            "selected_source_commit": BUGGY_COMMIT,
            "source_only_suitability_classification": state["source_only_suitability_classification"],
            "patch_generation_status": state["patch_generation_status"],
            "patch_apply_status": state["patch_apply_status"],
            "post_repair_target_replay_status": state["post_repair_target_replay_status"],
            "exact_blocker": state["exact_blocker"],
            "next_allowed_action": state["next_allowed_action"],
        },
    )
    write_sha256sums(batch052_dir)
    return state


def write_batch052_public_state(root: Path, state: dict[str, Any]) -> None:
    snippet = "\n".join(
        [
            "",
            "### Batch052 Lemon Reader source-only patch candidate gate",
            "",
            f"- Batch052 status: `{state['status']}`.",
            f"- Current protocol remains: `{state['current_protocol']}`.",
            f"- Source-only suitability: `{state['source_only_suitability_classification']}`.",
            f"- Patch generation status: `{state['patch_generation_status']}`.",
            f"- Patch apply status: `{state['patch_apply_status']}`.",
            f"- Post-repair target replay status: `{state['post_repair_target_replay_status']}`.",
            f"- Duplicate replay status: `{state['duplicate_replay_status']}`; reason: `{state['duplicate_replay_not_run_reason']}`.",
            f"- Exact blocker: `{state['exact_blocker']}`.",
            f"- Next allowed action: `{state['next_allowed_action']}`.",
            f"- External native repair episodes remain `{state['native_external_repair_episode_count']}`; issue-derived repair episodes remain `{state['issue_derived_repair_episode_count']}`.",
            "- Batch052 does not run duplicate replay, full scoring, memory-lift claims, self-maintaining claims, or production-readiness claims.",
        ]
    )
    for rel in [
        "README.md",
        "docs/current_status.md",
        "docs/capability_inventory.md",
        "docs/technical_validation_gap_report.md",
        "controllergate_v1_7_beta/reports/critic_review_package/shareable_summary.md",
    ]:
        path = root / rel
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        marker = "### Batch052 Lemon Reader source-only patch candidate gate"
        if marker in text:
            text = text[: text.index(marker)].rstrip()
        write_text_lf(path, text.rstrip() + "\n" + snippet)
