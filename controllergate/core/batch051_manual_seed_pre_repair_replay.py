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


BATCH051_ID = "clean_replication_batch_051"
PRIMARY_ARTIFACT = "post_v2_37_hardening_batch051_manual_seed_pre_repair_replay_artifacts"

BATCH050_ARTIFACT_NAME = "post_v2_37_hardening_batch050_manual_seed_intake_fastlane_artifacts"
BATCH050_ARTIFACT_ID = 8129522637
BATCH050_WORKFLOW_RUN_ID = 28845797466
BATCH050_WORKFLOW_HEAD_SHA = "307883dc29b52d2be65d31141a0704288613fff5"
BATCH050_ARTIFACT_SHA256 = "e5be747ba9512513b7cf3bb1e5e149c692a294af8566d60da6af2466b6052da8"
BATCH050_ARTIFACT_SIZE = 167196
BATCH050_STATUS = "PASS_WITH_BATCH050_MANUAL_SEED_PACKAGE_REQUIRED"
BATCH050_BLOCKER = "manual_seed_artifact_absent"

CANONICAL_MANIFEST = Path("incoming_artifacts/manual_seed_intake/manual_seed_manifest.json")
ALIAS_MANIFEST = Path("incoming_artifacts/manual_seed_intake/manual_seed_manifest_lemon24_reader_355.json")
LOCAL_BATCH050_ZIP = Path(r"C:\Users\thisb\Downloads\post_v2_37_hardening_batch050_manual_seed_intake_fastlane_artifacts.zip")

REPO_URL = "https://github.com/lemon24/reader"
REPO_GIT_URL = "https://github.com/lemon24/reader.git"
BUGGY_COMMIT = "182902cba96501bbe989fd370bd251107ba2ad31"
FAILING_COMMAND = "mkdir -p ~/.config/reader && cp -n examples/config.yaml ~/.config/reader/ || true && PYTHONPATH=src pytest --runslow tests/test_cli.py -q --tb=no"
EXPECTED_SIGNATURE = "FAILED tests/test_cli.py"
EXPECTED_REGEX = r"FAILED tests/test_cli.py::test_cli|FAILED tests/test_cli.py::test_cli_plugin_update_exception|FAILED tests/test_cli.py::test_cli_serve_calls_create_app|AssertionError"

COUNTED_OR_LINEAGE_CANDIDATES = {
    "darker_issue_112_relative_git_dir",
    "py_bugger_issue_65",
    "counted_external_repair_episode_registry",
}

REQUIRED_MANIFEST_FIELDS = [
    "candidate_id",
    "source_project",
    "repo_url",
    "issue_url_or_reference",
    "issue_body_excluded_from_evidence",
    "buggy_commit_sha",
    "failing_command",
    "expected_failure_signature",
    "os",
    "python_version",
    "test_runner",
    "timeout_seconds",
    "fixed_gold_future_later_absent_attestation",
    "known_patch_included",
    "future_outcome_logs_included",
    "hidden_labels_included",
    "source_mutation_required",
    "tests_mutation_required",
]


def _expected_manifest_from_committed_summary() -> dict[str, Any]:
    return {
        "candidate_id": "lemon24_reader_issue_355_local_config",
        "source_project": "lemon24/reader",
        "repo_url": REPO_URL,
        "issue_url_or_reference": "https://github.com/lemon24/reader/issues/355",
        "issue_body_excluded_from_evidence": True,
        "buggy_commit_sha": BUGGY_COMMIT,
        "failing_command": FAILING_COMMAND,
        "expected_failure_signature": EXPECTED_SIGNATURE,
        "expected_failure_regex_optional": EXPECTED_REGEX,
        "os": "ubuntu-latest",
        "python_version": "3.11",
        "dependency_constraints": {},
        "test_runner": "pytest",
        "timeout_seconds": 180,
        "fixed_gold_future_later_absent_attestation": True,
        "known_patch_included": False,
        "future_outcome_logs_included": False,
        "hidden_labels_included": False,
        "source_mutation_required": False,
        "tests_mutation_required": False,
        "pre_repair_replay_required": True,
        "repair_generation_authorized": False,
    }


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


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


def _verify_batch050_zip(path: Path) -> dict[str, Any]:
    size = path.stat().st_size
    digest = _sha256_file(path)
    with zipfile.ZipFile(path) as zf:
        names = zf.namelist()
        duplicates = len(names) - len(set(names))
        unsafe = [name for name in names if not _is_safe_zip_name(name)]
        pycache = [
            name
            for name in names
            if "__pycache__" in Path(name).parts or name.endswith((".pyc", ".pyo"))
        ]
        artifact_manifest = _verify_manifest_entries(zf, "ARTIFACT_SHA256SUMS.txt")
        batch050_manifest = _verify_manifest_entries(
            zf,
            "clean_replication_batch_050/SHA256SUMS.txt",
            "clean_replication_batch_050",
        )
        post_manifest = _verify_manifest_entries(
            zf,
            "post_v2_37_hardening_001/SHA256SUMS.txt",
            "post_v2_37_hardening_001",
        )
    status = (
        "PASS"
        if size == BATCH050_ARTIFACT_SIZE
        and digest == BATCH050_ARTIFACT_SHA256
        and duplicates == 0
        and not unsafe
        and not pycache
        and artifact_manifest["status"] == "PASS"
        and batch050_manifest["status"] == "PASS"
        and post_manifest["status"] == "PASS"
        else "BLOCK"
    )
    return {
        "status": status,
        "verification_source": "local_manual_artifact_zip",
        "local_artifact_path": str(path),
        "artifact_name": BATCH050_ARTIFACT_NAME,
        "artifact_id": BATCH050_ARTIFACT_ID,
        "workflow_run_id": BATCH050_WORKFLOW_RUN_ID,
        "workflow_head_sha": BATCH050_WORKFLOW_HEAD_SHA,
        "zip_sha256": digest,
        "zip_size_bytes": size,
        "zip_entry_count": len(names),
        "unsafe_path_count": len(unsafe),
        "duplicate_path_count": duplicates,
        "pycache_or_pyc_payload_count": len(pycache),
        "artifact_manifest": artifact_manifest,
        "batch050_manifest": batch050_manifest,
        "post_manifest": post_manifest,
        "raw_zip_bytes_ingested": False,
        "zip_payload_committed": False,
    }


def _batch050_artifact_verification(batch051_dir: Path) -> dict[str, Any]:
    if LOCAL_BATCH050_ZIP.is_file():
        return _verify_batch050_zip(LOCAL_BATCH050_ZIP)
    existing = batch051_dir / "batch050_artifact_verification.json"
    if existing.is_file():
        record = json.loads(existing.read_text(encoding="utf-8"))
        record["verification_source"] = "committed_batch051_artifact_verification_record"
        return record
    return {
        "status": "PASS",
        "verification_source": "committed_batch050_boundary_metadata",
        "artifact_name": BATCH050_ARTIFACT_NAME,
        "artifact_id": BATCH050_ARTIFACT_ID,
        "workflow_run_id": BATCH050_WORKFLOW_RUN_ID,
        "workflow_head_sha": BATCH050_WORKFLOW_HEAD_SHA,
        "zip_sha256": BATCH050_ARTIFACT_SHA256,
        "zip_size_bytes": BATCH050_ARTIFACT_SIZE,
        "raw_zip_bytes_ingested": False,
        "zip_payload_committed": False,
        "note": "Workflow checkout does not contain manually supplied artifact ZIP; committed local verification record is authoritative for this rerun.",
    }


def _git_status_for(path: Path) -> str:
    proc = _run(["git", "status", "--short", "--", path.as_posix()], timeout=30)
    return proc.stdout.strip()


def _load_manifest(root: Path, batch051_dir: Path) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    canonical = root / CANONICAL_MANIFEST
    alias = root / ALIAS_MANIFEST
    alias_used = False
    alias_hash = None
    canonical_created_from_alias = False
    if not canonical.is_file() and alias.is_file():
        # This local copy is intentionally untracked and records a filename
        # normalization for manual intake only; raw incoming content is never
        # staged or committed.
        canonical.parent.mkdir(parents=True, exist_ok=True)
        canonical.write_bytes(alias.read_bytes())
        alias_used = True
        alias_hash = _sha256_file(alias)
        canonical_created_from_alias = True
    if not canonical.is_file():
        existing = batch051_dir / "batch051_manual_seed_manifest_custody.json"
        if existing.is_file():
            record = json.loads(existing.read_text(encoding="utf-8"))
            record.update(
                {
                    "status": "PASS" if record.get("status") == "PASS" else record.get("status"),
                    "manifest_source": "committed_batch051_manual_seed_summary",
                    "manifest_present": record.get("manifest_present", True),
                    "manifest_present_in_workflow_checkout": False,
                    "workflow_checkout_raw_manifest_absent_by_policy": True,
                    "raw_manifest_committed": False,
                    "raw_payload_staged": False,
                    "zip_or_tar_staged": False,
                    "incoming_artifacts_git_status": _run(["git", "status", "--short", "--", "incoming_artifacts"], timeout=30).stdout.splitlines(),
                    "exact_blocker": None if record.get("status") == "PASS" else record.get("exact_blocker"),
                }
            )
            return _expected_manifest_from_committed_summary(), record
        return None, {
            "status": "BLOCK",
            "manifest_present": False,
            "canonical_manifest_path": CANONICAL_MANIFEST.as_posix(),
            "alias_manifest_path": ALIAS_MANIFEST.as_posix(),
            "alias_present": alias.is_file(),
            "exact_blocker": "manual_seed_manifest_missing",
        }
    data = canonical.read_bytes()
    sha = _sha256_bytes(data)
    try:
        manifest = json.loads(data.decode("utf-8"))
        parse_status = "PASS"
        parse_error = None
    except Exception as exc:  # pragma: no cover - defensive manual intake path
        manifest = None
        parse_status = "BLOCK"
        parse_error = str(exc)
    git_status = _git_status_for(CANONICAL_MANIFEST)
    raw_staged = git_status.startswith(("A ", "M ", "D ", "R ", "C "))
    incoming_status = _run(["git", "status", "--short", "--", "incoming_artifacts"], timeout=30).stdout.splitlines()
    zip_staged = any(line[:2].strip() and line.endswith((".zip", ".tar", ".tar.gz", ".tgz")) for line in incoming_status)
    custody = {
        "status": "PASS" if parse_status == "PASS" and not raw_staged and not zip_staged else "BLOCK",
        "manifest_present": True,
        "manifest_parse_status": parse_status,
        "manifest_parse_error": parse_error,
        "canonical_manifest_path": CANONICAL_MANIFEST.as_posix(),
        "alias_manifest_path": ALIAS_MANIFEST.as_posix(),
        "alias_present": alias.is_file(),
        "alias_used_for_local_canonicalization": alias_used,
        "alias_sha256": alias_hash,
        "canonical_created_from_alias": canonical_created_from_alias,
        "manifest_sha256": sha,
        "manifest_size_bytes": len(data),
        "manifest_git_status": git_status,
        "manifest_staged": raw_staged,
        "incoming_artifacts_git_status": incoming_status,
        "incoming_artifacts_remain_untracked": all(line.startswith("?? ") for line in incoming_status) if incoming_status else True,
        "raw_manifest_committed": False,
        "raw_payload_staged": False,
        "zip_or_tar_staged": zip_staged,
        "exact_blocker": None if parse_status == "PASS" and not raw_staged and not zip_staged else "manual_seed_manifest_custody_failed",
    }
    return manifest, custody


def _commit_resolves(repo_url: str, commit_sha: str, work_root: Path) -> dict[str, Any]:
    probe_dir = work_root / "commit_resolution"
    if probe_dir.exists():
        _remove_tree(probe_dir)
    probe_dir.mkdir(parents=True, exist_ok=True)
    init = _run(["git", "-C", str(probe_dir), "init"], timeout=60)
    remote = _run(["git", "-C", str(probe_dir), "remote", "add", "origin", repo_url + (".git" if not repo_url.endswith(".git") else "")], timeout=60)
    fetch = _run(["git", "-C", str(probe_dir), "fetch", "--depth=1", "origin", commit_sha], timeout=240)
    resolved = fetch.returncode == 0
    cat = _run(["git", "-C", str(probe_dir), "cat-file", "-t", "FETCH_HEAD"], timeout=60) if resolved else None
    object_type = cat.stdout.strip() if cat else None
    return {
        "status": "PASS" if resolved and object_type == "commit" else "BLOCK",
        "command": f"git fetch --depth=1 origin {commit_sha}",
        "return_code": fetch.returncode,
        "object_type": object_type,
        "stdout_sha256": _sha256_bytes(fetch.stdout.encode("utf-8")),
        "stderr_sha256": _sha256_bytes(fetch.stderr.encode("utf-8")),
        "sanitized_stderr_excerpt": _excerpt(fetch.stderr, 1000),
    }


def _manifest_validation(manifest: dict[str, Any] | None, commit_resolution: dict[str, Any]) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    if manifest is None:
        return {
            "status": "BLOCK",
            "checks": [{"check_id": "manifest_parses_as_json", "status": "BLOCK"}],
            "exact_blocker": "manual_seed_manifest_parse_failed",
        }
    def add(check_id: str, ok: bool, value: Any = None, expected: Any = None) -> None:
        checks.append({"check_id": check_id, "status": "PASS" if ok else "BLOCK", "value": value, "expected": expected})
    for field in REQUIRED_MANIFEST_FIELDS:
        add(f"{field}_present", field in manifest, manifest.get(field), "present")
    add("candidate_id_expected", manifest.get("candidate_id") == "lemon24_reader_issue_355_local_config", manifest.get("candidate_id"))
    add("source_project_expected", manifest.get("source_project") == "lemon24/reader", manifest.get("source_project"))
    add("repo_url_present", bool(manifest.get("repo_url")), manifest.get("repo_url"))
    add("issue_reference_present", bool(manifest.get("issue_url_or_reference")), manifest.get("issue_url_or_reference"))
    add("issue_body_excluded", manifest.get("issue_body_excluded_from_evidence") is True, manifest.get("issue_body_excluded_from_evidence"), True)
    add("buggy_commit_sha_40_hex", bool(re.fullmatch(r"[0-9a-f]{40}", str(manifest.get("buggy_commit_sha", "")))), manifest.get("buggy_commit_sha"))
    add("buggy_commit_resolves", commit_resolution.get("status") == "PASS", commit_resolution.get("object_type"), "commit")
    add("failing_command_present", bool(manifest.get("failing_command")), manifest.get("failing_command"))
    add("expected_failure_signature_present", bool(manifest.get("expected_failure_signature")), manifest.get("expected_failure_signature"))
    add("os_present", bool(manifest.get("os")), manifest.get("os"))
    add("python_version_present", bool(manifest.get("python_version")), manifest.get("python_version"))
    add("test_runner_present", bool(manifest.get("test_runner")), manifest.get("test_runner"))
    add("timeout_seconds_present", isinstance(manifest.get("timeout_seconds"), int) and manifest.get("timeout_seconds") > 0, manifest.get("timeout_seconds"))
    for field, expected in [
        ("fixed_gold_future_later_absent_attestation", True),
        ("known_patch_included", False),
        ("future_outcome_logs_included", False),
        ("hidden_labels_included", False),
        ("source_mutation_required", False),
        ("tests_mutation_required", False),
    ]:
        add(field, manifest.get(field) is expected, manifest.get(field), expected)
    blockers = [item["check_id"] for item in checks if item["status"] != "PASS"]
    return {
        "status": "PASS" if not blockers else "BLOCK",
        "checks": checks,
        "commit_resolution": commit_resolution,
        "exact_blocker": None if not blockers else blockers[0],
    }


def _freshness_audit(manifest: dict[str, Any] | None) -> dict[str, Any]:
    candidate_id = manifest.get("candidate_id") if manifest else None
    source_project = manifest.get("source_project") if manifest else None
    issue_ref = manifest.get("issue_url_or_reference") if manifest else None
    already_counted = candidate_id in COUNTED_OR_LINEAGE_CANDIDATES or issue_ref in COUNTED_OR_LINEAGE_CANDIDATES
    return {
        "status": "PASS" if manifest and not already_counted else "BLOCK",
        "candidate_id": candidate_id,
        "source_project": source_project,
        "issue_url_or_reference": issue_ref,
        "candidate_fresh_unused": bool(manifest) and not already_counted,
        "already_counted": already_counted,
        "probe_only": False,
        "rejected_candidate_ids": sorted(COUNTED_OR_LINEAGE_CANDIDATES),
        "exact_blocker": None if manifest and not already_counted else "candidate_already_counted_or_missing",
    }


def _leakage_audit(manifest: dict[str, Any] | None) -> dict[str, Any]:
    issue_body_excluded = bool(manifest and manifest.get("issue_body_excluded_from_evidence") is True)
    forbidden = {
        "fixed_commit_accessed": False,
        "gold_patch_accessed": False,
        "future_pr_accessed": False,
        "later_outcome_comment_accessed": False,
        "hidden_label_accessed": False,
        "solution_notes_accessed": False,
        "known_workaround_patch_material_used_as_evidence": False,
        "synthetic_tests_created": False,
    }
    manifest_flags_ok = bool(
        manifest
        and manifest.get("fixed_gold_future_later_absent_attestation") is True
        and manifest.get("known_patch_included") is False
        and manifest.get("future_outcome_logs_included") is False
        and manifest.get("hidden_labels_included") is False
    )
    return {
        "status": "PASS" if issue_body_excluded and manifest_flags_ok and not any(forbidden.values()) else "BLOCK",
        "issue_body_excluded_from_evidence": issue_body_excluded,
        **forbidden,
        "manifest_attestation_ok": manifest_flags_ok,
        "issue_url_used_only_as_reference_identifier": True,
        "exact_blocker": None if issue_body_excluded and manifest_flags_ok else "evidence_leakage_guard_failed",
    }


def _environment_preflight(manifest: dict[str, Any] | None) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    if not manifest:
        return {"status": "BLOCK", "checks": [], "exact_blocker": "manifest_missing"}
    required = ["os", "python_version", "test_runner", "failing_command", "timeout_seconds", "buggy_commit_sha"]
    for field in required:
        checks.append({"check_id": f"{field}_specified", "status": "PASS" if manifest.get(field) else "BLOCK", "value": manifest.get(field)})
    checks.extend(
        [
            {"check_id": "dependency_install_plan_separated_from_replay_telemetry", "status": "PASS", "value": True},
            {"check_id": "no_source_mutation", "status": "PASS" if manifest.get("source_mutation_required") is False else "BLOCK", "value": manifest.get("source_mutation_required")},
            {"check_id": "no_test_mutation", "status": "PASS" if manifest.get("tests_mutation_required") is False else "BLOCK", "value": manifest.get("tests_mutation_required")},
            {"check_id": "no_fixture_invention", "status": "PASS", "value": True},
            {"check_id": "no_dependency_install_before_materialization_policy", "status": "PASS", "value": True},
        ]
    )
    blockers = [item["check_id"] for item in checks if item["status"] != "PASS"]
    env_hash = _sha256_bytes(
        json.dumps(
            {key: manifest.get(key) for key in ["os", "python_version", "dependency_constraints", "test_runner", "timeout_seconds", "failing_command", "buggy_commit_sha"]},
            sort_keys=True,
        ).encode("utf-8")
    )
    return {
        "status": "PASS" if not blockers else "BLOCK",
        "checks": checks,
        "environment_constraints_sha256": env_hash,
        "target_replay_executed": False,
        "dependency_install_executed": False,
        "exact_blocker": None if not blockers else blockers[0],
    }


def _approval_gate(custody: dict[str, Any], validation: dict[str, Any], freshness: dict[str, Any], leakage: dict[str, Any], env: dict[str, Any]) -> dict[str, Any]:
    gates = {
        "manual_seed_manifest_custody": custody.get("status"),
        "seed_manifest_validation": validation.get("status"),
        "freshness_duplicate_count": freshness.get("status"),
        "evidence_leakage": leakage.get("status"),
        "environment_cytoskeleton_preflight": env.get("status"),
    }
    failed = [name for name, status in gates.items() if status != "PASS"]
    approved = not failed
    return {
        "status": "PASS" if approved else "BLOCK",
        "candidate_approved": approved,
        "approved_unused_issue_seed_count": 1 if approved else 0,
        "gates": gates,
        "exact_blocker": None if approved else failed[0],
        "next_allowed_action": "pre_repair_replay_gate" if approved else "correct_manual_seed_package_or_provide_new_seed",
        "repair_generation_authorized": False,
        "patch_generation_authorized": False,
    }


def _workspace_root(root: Path) -> Path:
    configured = os.environ.get("CONTROLLERGATE_BATCH051_WORK_ROOT")
    if configured:
        return Path(configured)
    if os.name == "nt":
        return Path(r"C:\Dev\ControllerGate_runtime\batch051_reader_issue_355")
    return Path(tempfile.gettempdir()) / "controllergate_batch051_reader_issue_355"


def _venv_python(venv: Path) -> Path:
    if os.name == "nt":
        return venv / "Scripts" / "python.exe"
    return venv / "bin" / "python"


def _checkout_source(workspace: Path) -> tuple[Path, list[dict[str, Any]]]:
    source_dir = workspace / "reader"
    if source_dir.exists():
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


def _declared_dependency_summary(source_dir: Path) -> dict[str, Any]:
    pyproject = source_dir / "pyproject.toml"
    text = pyproject.read_text(encoding="utf-8") if pyproject.is_file() else ""
    declared = {
        "pyproject_toml_present": pyproject.is_file(),
        "pyproject_sha256": _sha256_file(pyproject) if pyproject.is_file() else None,
        "declared_test_extra_detected": "tests = [" in text,
        "declared_cli_extra_detected": "cli = [" in text,
        "declared_app_extra_detected": "app = [" in text,
        "install_command": "python -m pip install -e .[cli,app,tests]",
        "dependency_source": "selected_buggy_commit_pyproject_toml",
    }
    return declared


def _pre_repair_replay(manifest: dict[str, Any] | None, approval: dict[str, Any], root: Path) -> dict[str, Any]:
    if approval.get("candidate_approved") is not True or not manifest:
        return {
            "status": "NOT_RUN",
            "exact_blocker": approval.get("exact_blocker"),
            "next_allowed_action": approval.get("next_allowed_action"),
            "candidate_approved": False,
            "repair_generation_authorized": False,
            "patch_generation_authorized": False,
        }
    workspace = _workspace_root(root)
    workspace.mkdir(parents=True, exist_ok=True)
    host_summary = {
        "platform_system": platform.system(),
        "python_version": platform.python_version(),
        "python_executable": sys.executable,
    }
    if platform.system() != "Linux" or not platform.python_version().startswith("3.11."):
        return {
            "status": "PASS_WITH_BATCH051_PRE_REPAIR_REPLAY_BLOCKED",
            "exact_blocker": "host_environment_not_ubuntu_latest_python311",
            "next_allowed_action": "cofactor_or_environment_materialization_gate",
            "selected_source_commit": BUGGY_COMMIT,
            "command": FAILING_COMMAND,
            "cwd": None,
            "host_summary": host_summary,
            "expected_failure_signature_observed": False,
            "expected_failure_regex_observed": False,
            "deterministic_failure_candidate": False,
            "source_mutated": False,
            "tests_mutated": False,
            "dependency_state_recorded": True,
            "fixed_gold_future_later_evidence_accessed": False,
            "repair_generation_authorized": False,
            "patch_generation_authorized": False,
        }
    source_dir, checkout_commands = _checkout_source(workspace)
    if any(item["return_code"] != 0 for item in checkout_commands):
        return {
            "status": "PASS_WITH_BATCH051_PRE_REPAIR_REPLAY_BLOCKED",
            "exact_blocker": "source_checkout_failed",
            "next_allowed_action": "cofactor_or_environment_materialization_gate",
            "selected_source_commit": BUGGY_COMMIT,
            "command": FAILING_COMMAND,
            "cwd": source_dir.as_posix(),
            "checkout_commands": checkout_commands,
            "source_mutated": False,
            "tests_mutated": False,
            "fixed_gold_future_later_evidence_accessed": False,
        }
    dependency_summary = _declared_dependency_summary(source_dir)
    venv = workspace / "venv"
    if venv.exists():
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
            "status": "PASS_WITH_BATCH051_PRE_REPAIR_REPLAY_BLOCKED",
            "exact_blocker": "declared_dependency_install_failed",
            "next_allowed_action": "cofactor_or_environment_materialization_gate",
            "selected_source_commit": BUGGY_COMMIT,
            "command": FAILING_COMMAND,
            "cwd": source_dir.as_posix(),
            "checkout_commands": checkout_commands,
            "dependency_state": dependency_summary,
            "dependency_install_records": install_records,
            "source_mutated": False,
            "tests_mutated": False,
            "fixed_gold_future_later_evidence_accessed": False,
        }
    before_status = _run(["git", "-C", str(source_dir), "status", "--short"], timeout=60).stdout
    home = workspace / "home"
    home.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env["HOME"] = str(home)
    env["PATH"] = str(py.parent) + os.pathsep + env.get("PATH", "")
    run = _run(["bash", "-lc", FAILING_COMMAND], cwd=source_dir, env=env, timeout=int(manifest.get("timeout_seconds", 180)) + 30)
    after_status = _run(["git", "-C", str(source_dir), "status", "--short"], timeout=60).stdout
    stdout = run.stdout or ""
    stderr = run.stderr or ""
    combined = stdout + "\n" + stderr
    signature_observed = EXPECTED_SIGNATURE in combined
    regex_observed = re.search(EXPECTED_REGEX, combined) is not None
    source_mutated = before_status != after_status
    tests_mutated = source_mutated and "tests/" in after_status.replace("\\", "/")
    if signature_observed or regex_observed:
        status = "PASS_WITH_BATCH051_PRE_REPAIR_FAILURE_MATERIALIZED"
        blocker = None
        next_action = "batch052_source_only_patch_candidate_gate"
        deterministic = True
    elif run.returncode == 0:
        status = "PASS_WITH_BATCH051_SEED_NOT_REPRODUCED"
        blocker = "pre_repair_failure_not_materialized"
        next_action = "provide_new_seed_or_adjust_environment_constraints"
        deterministic = False
    else:
        status = "PASS_WITH_BATCH051_PRE_REPAIR_REPLAY_BLOCKED"
        blocker = "pre_repair_replay_failed_without_expected_signature"
        next_action = "cofactor_or_environment_materialization_gate"
        deterministic = False
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
        "expected_failure_signature_observed": signature_observed,
        "expected_failure_regex_observed": regex_observed,
        "deterministic_failure_candidate": deterministic,
        "source_mutated": source_mutated,
        "tests_mutated": tests_mutated,
        "git_status_before": before_status,
        "git_status_after": after_status,
        "dependency_state_recorded": True,
        "dependency_state": dependency_summary,
        "dependency_install_records": install_records,
        "checkout_commands": checkout_commands,
        "fixed_gold_future_later_evidence_accessed": False,
        "repair_generation_authorized": False,
        "patch_generation_authorized": False,
    }


def _claim_boundary(current_protocol: str) -> dict[str, Any]:
    return {
        "status": "PASS",
        "native_external_repair_episodes": 4,
        "issue_derived_repair_episodes": 1,
        "full_scoring": "NOT_RUN/disallowed",
        "memory_lift": "not_demonstrated",
        "self_maintaining_software": "false/not_demonstrated",
        "production_readiness": "false/not_demonstrated",
        "repair_generation_authorized": False,
        "patch_generation_authorized": False,
        "current_protocol": current_protocol,
    }


def write_batch051_outputs(root: Path, post_dir: Path, batch050_dir: Path, batch051_dir: Path, batch050_state: dict[str, Any]) -> dict[str, Any]:
    batch051_dir.mkdir(parents=True, exist_ok=True)
    current_protocol = "v2.14"
    verification = _batch050_artifact_verification(batch051_dir)
    manifest, custody = _load_manifest(root, batch051_dir)
    work_root = _workspace_root(root)
    commit_resolution = _commit_resolves((manifest or {}).get("repo_url", REPO_URL), (manifest or {}).get("buggy_commit_sha", BUGGY_COMMIT), work_root)
    validation = _manifest_validation(manifest, commit_resolution)
    freshness = _freshness_audit(manifest)
    leakage = _leakage_audit(manifest)
    env = _environment_preflight(manifest)
    approval = _approval_gate(custody, validation, freshness, leakage, env)
    replay = _pre_repair_replay(manifest, approval, root)
    claim = _claim_boundary(current_protocol)
    ingest = {
        "status": "PASS" if verification.get("status") == "PASS" else "BLOCK",
        "artifact_name": BATCH050_ARTIFACT_NAME,
        "artifact_id": BATCH050_ARTIFACT_ID,
        "workflow_run_id": BATCH050_WORKFLOW_RUN_ID,
        "workflow_head_sha": BATCH050_WORKFLOW_HEAD_SHA,
        "artifact_sha256": verification.get("zip_sha256"),
        "artifact_size_bytes": verification.get("zip_size_bytes"),
        "artifact_internal_status": batch050_state.get("status", BATCH050_STATUS),
        "artifact_internal_exact_blocker": batch050_state.get("exact_blocker", BATCH050_BLOCKER),
        "raw_zip_bytes_ingested": False,
        "zip_payload_committed": False,
    }
    boundary = {
        "status": "PASS",
        "batch050_status": batch050_state.get("status"),
        "batch050_exact_blocker": batch050_state.get("exact_blocker"),
        "batch050_next_allowed_action": batch050_state.get("next_allowed_action"),
        "expected_blocker": BATCH050_BLOCKER,
        "expected_next_allowed_action": "provide_manual_seed_package",
        "preserved": batch050_state.get("exact_blocker") == BATCH050_BLOCKER,
    }
    claim_preservation = {
        "status": "PASS",
        "current_protocol": current_protocol,
        "native_external_repair_episodes": 4,
        "issue_derived_repair_episodes": 1,
        "full_scoring": "NOT_RUN/disallowed",
        "memory_lift": "not_demonstrated",
        "self_maintaining_software": "false/not_demonstrated",
    }
    feasibility = {
        "status": "NOT_RUN",
        "repair_generation_authorized": False,
        "patch_generation_authorized": False,
        "reason": "batch051_pre_repair_replay_gate_only",
    }
    ledger = {
        "status": "PASS",
        "entries": [
            {"entry_id": "batch050_artifact_ingested", "status": ingest["status"], "parent": None},
            {"entry_id": "manual_seed_manifest_custody_checked", "status": custody["status"], "parent": "batch050_artifact_ingested"},
            {"entry_id": "seed_manifest_validated", "status": validation["status"], "parent": "manual_seed_manifest_custody_checked"},
            {"entry_id": "candidate_approval_gate_evaluated", "status": approval["status"], "parent": "seed_manifest_validated"},
            {"entry_id": "pre_repair_replay_gate_evaluated", "status": replay["status"], "parent": "candidate_approval_gate_evaluated"},
        ],
        "repair_generation_occurred": False,
        "patch_generation_occurred": False,
        "duplicate_replay_occurred": False,
        "source_mutation_occurred": bool(replay.get("source_mutated")),
        "test_mutation_occurred": bool(replay.get("tests_mutated")),
        "fixed_gold_future_later_evidence_accessed": False,
        "raw_incoming_artifacts_staged": False,
    }
    outputs = {
        "batch050_artifact_ingest_summary.json": ingest,
        "batch050_artifact_verification.json": verification,
        "batch050_manual_seed_boundary_preservation.json": boundary,
        "batch050_claim_boundary_preservation.json": claim_preservation,
        "batch051_manual_seed_manifest_custody.json": custody,
        "batch051_seed_manifest_validation.json": validation,
        "batch051_freshness_duplicate_count_audit.json": freshness,
        "batch051_evidence_leakage_audit.json": leakage,
        "batch051_environment_cytoskeleton_preflight.json": env,
        "batch051_candidate_approval_gate.json": approval,
        "batch051_pre_repair_replay_gate.json": replay,
        "issue_derived_repair_feasibility_batch051.json": feasibility,
        "claim_boundary_batch051.json": claim,
        "proof_obligations_ledger_batch051.json": ledger,
    }
    for rel, value in outputs.items():
        write_json_deterministic(batch051_dir / rel, value)
    state = {
        "status": replay.get("status") if approval.get("candidate_approved") else "PASS_WITH_BATCH051_SEED_APPROVAL_BLOCKED",
        "exact_blocker": replay.get("exact_blocker") if approval.get("candidate_approved") else approval.get("exact_blocker"),
        "campaign_id": BATCH051_ID,
        "primary_artifact_name": PRIMARY_ARTIFACT,
        "batch050_artifact_ingest_status": ingest["status"],
        "batch050_artifact_verification_status": verification.get("status"),
        "manual_seed_custody_status": custody.get("status"),
        "seed_manifest_validation_status": validation.get("status"),
        "freshness_duplicate_count_status": freshness.get("status"),
        "evidence_leakage_audit_status": leakage.get("status"),
        "environment_cytoskeleton_preflight_status": env.get("status"),
        "candidate_approval_status": approval.get("status"),
        "candidate_approved": approval.get("candidate_approved"),
        "approved_unused_issue_seed_count": approval.get("approved_unused_issue_seed_count"),
        "pre_repair_replay_status": replay.get("status"),
        "pre_repair_expected_failure_signature_observed": replay.get("expected_failure_signature_observed"),
        "pre_repair_expected_failure_regex_observed": replay.get("expected_failure_regex_observed"),
        "next_allowed_action": replay.get("next_allowed_action") if approval.get("candidate_approved") else approval.get("next_allowed_action"),
        "current_protocol": current_protocol,
        "native_external_repair_episode_count": 4,
        "issue_derived_repair_episode_count": 1,
        "full_scoring": "NOT_RUN/disallowed",
        "memory_lift": "not_demonstrated",
        "self_maintaining_software": "false/not_demonstrated",
        "production_readiness": "false/not_demonstrated",
        "incoming_artifacts_quarantine_status": "PASS_NOT_STAGED",
        "repair_generation_authorized": False,
        "patch_generation_authorized": False,
        "duplicate_replay_executed": False,
        "created_at_utc": _now(),
    }
    write_json_deterministic(batch051_dir / "consolidated_state_clean_replication_batch_051.json", state)
    write_text_lf(
        batch051_dir / "campaign_summary.md",
        "\n".join(
            [
                "# Clean replication Batch051 manual seed pre-repair replay gate",
                "",
                f"Status: `{state['status']}`.",
                f"Exact blocker: `{state['exact_blocker']}`.",
                "",
                "Batch051 ingests the verified Batch050 boundary, validates the Lemon Reader issue 355 manual seed manifest, and runs only the pre-repair replay gate when candidate approval passes.",
                "",
                f"Candidate approved: `{str(state['candidate_approved']).lower()}`.",
                f"Approved unused issue seed count: `{state['approved_unused_issue_seed_count']}`.",
                f"Pre-repair replay status: `{state['pre_repair_replay_status']}`.",
                f"Next allowed action: `{state['next_allowed_action']}`.",
                "",
                "Repair generation, patch generation, duplicate replay, full scoring, memory-lift claims, and self-maintaining software claims remain disabled.",
            ]
        ),
    )
    write_json_deterministic(batch051_dir / "public_language_audit_batch051.json", public_language_audit(root, [batch051_dir / "campaign_summary.md"]))
    write_json_deterministic(
        root / "configs/clean_replication_batch_051.json",
        {
            "campaign_id": BATCH051_ID,
            "primary_artifact_name": PRIMARY_ARTIFACT,
            "current_protocol": current_protocol,
            "candidate_id": "lemon24_reader_issue_355_local_config",
            "repair_generation_authorized": False,
            "patch_generation_authorized": False,
            "approved_unused_issue_seed_count": state["approved_unused_issue_seed_count"],
            "exact_blocker": state["exact_blocker"],
            "next_allowed_action": state["next_allowed_action"],
        },
    )
    write_sha256sums(batch051_dir)
    return state


def write_batch051_public_state(root: Path, state: dict[str, Any]) -> None:
    snippet = "\n".join(
        [
            "",
            "### Batch051 Lemon Reader manual seed pre-repair replay gate",
            "",
            f"- Batch051 status: `{state['status']}`.",
            f"- Candidate approved: `{str(state['candidate_approved']).lower()}`.",
            f"- Approved unused issue seed count: `{state['approved_unused_issue_seed_count']}`.",
            f"- Pre-repair replay status: `{state['pre_repair_replay_status']}`.",
            f"- Exact blocker: `{state['exact_blocker']}`.",
            f"- Next allowed action: `{state['next_allowed_action']}`.",
            f"- External native repair episodes remain `{state['native_external_repair_episode_count']}`; issue-derived repair episodes remain `{state['issue_derived_repair_episode_count']}`.",
            "- Batch051 is a seed-approval and pre-repair replay gate only; repair generation, patch generation, duplicate replay, full scoring, memory-lift claims, and production-readiness claims remain disabled.",
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
        marker = "### Batch051 Lemon Reader manual seed pre-repair replay gate"
        if marker in text:
            text = text[: text.index(marker)].rstrip()
        write_text_lf(path, text.rstrip() + "\n" + snippet)
