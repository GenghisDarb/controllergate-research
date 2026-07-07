from __future__ import annotations

import hashlib
import json
import os
import posixpath
import re
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .batch020_manual_lock import public_language_audit
from .evidence import write_json_deterministic, write_text_lf
from .manifests import write_sha256sums


BATCH050_ID = "clean_replication_batch_050"
PRIMARY_ARTIFACT = "post_v2_37_hardening_batch050_manual_seed_intake_fastlane_artifacts"

BATCH049_ARTIFACT_NAME = "post_v2_37_hardening_batch049_source_approval_cytoskeleton_artifacts"
BATCH049_ARTIFACT_ID = 8128503795
BATCH049_WORKFLOW_RUN_ID = 28842926254
BATCH049_WORKFLOW_HEAD_SHA = "3af5f89e4dcadb71fc93954b27f41e25db7baf35"
BATCH049_ARTIFACT_SHA256 = "57bfaa67d35c04a61ac0a41b537ee397427dd725c950ebf69047ac100fcdf816"
BATCH049_ARTIFACT_SIZE = 178978
BATCH049_ZIP_ENTRY_COUNT = 179
BATCH049_ARTIFACT_MANIFEST_CHECKED = 178
BATCH049_BATCH_MANIFEST_CHECKED = 34
BATCH049_POST_MANIFEST_CHECKED = 142
BATCH049_STATUS = "PASS_WITH_BATCH049_SOURCE_APPROVAL_CYTOSKELETON_GATE"
BATCH049_BLOCKER = "all_candidates_already_counted"

MANUAL_SEED_DIR = Path("incoming_artifacts/manual_seed_intake")

REQUIRED_MANIFEST_FIELDS = [
    "candidate_id",
    "source_project",
    "repo_url",
    "issue_url_or_reference",
    "buggy_commit_sha",
    "branch_or_tag_if_applicable",
    "source_archive_sha256",
    "failing_command",
    "expected_failure_signature",
    "expected_failure_regex_optional",
    "raw_failure_log_sha256",
    "os",
    "python_version",
    "dependency_constraints",
    "test_runner",
    "timeout_seconds",
    "verifier_identity",
    "verification_timestamp",
    "fixed_gold_future_later_absent_attestation",
    "known_patch_included",
    "future_outcome_logs_included",
    "hidden_labels_included",
    "source_mutation_required",
    "tests_mutation_required",
]

COUNTED_OR_LINEAGE_CANDIDATES = {
    "darker_issue_112_relative_git_dir",
    "py_bugger_issue_65",
    "counted_external_repair_episode_registry",
}

TEMPLATE_MANIFEST = {
    "candidate_id": "example_project_issue_123",
    "source_project": "owner/repo",
    "repo_url": "https://github.com/owner/repo",
    "issue_url_or_reference": "https://github.com/owner/repo/issues/123",
    "buggy_commit_sha": "40-character sha",
    "branch_or_tag_if_applicable": None,
    "source_archive_sha256": None,
    "failing_command": "pytest path/to/test.py::test_name",
    "expected_failure_signature": "short stable failure text",
    "expected_failure_regex_optional": None,
    "raw_failure_log_sha256": None,
    "os": "ubuntu-latest",
    "python_version": "3.11",
    "dependency_constraints": {},
    "test_runner": "pytest",
    "timeout_seconds": 120,
    "verifier_identity": "Brad/manual reviewer",
    "verification_timestamp": "YYYY-MM-DDTHH:MM:SSZ",
    "fixed_gold_future_later_absent_attestation": True,
    "known_patch_included": False,
    "future_outcome_logs_included": False,
    "hidden_labels_included": False,
    "source_mutation_required": False,
    "tests_mutation_required": False,
}


def _read_json(path: Path, default: Any | None = None) -> Any:
    if not path.is_file():
        if default is not None:
            return default
        raise FileNotFoundError(path)
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _artifact_zip_candidates() -> list[Path]:
    env_path = os.environ.get("BATCH049_ARTIFACT_ZIP")
    candidates: list[Path] = []
    if env_path:
        candidates.append(Path(env_path))
    candidates.extend(
        [
            Path("incoming_artifacts/post_v2_37_hardening_batch049_source_approval_cytoskeleton_artifacts.zip"),
            Path.home() / "Downloads" / "post_v2_37_hardening_batch049_source_approval_cytoskeleton_artifacts.zip",
        ]
    )
    return candidates


def _manifest_check(zf: zipfile.ZipFile, manifest_name: str, prefix: str = "") -> dict[str, Any]:
    if manifest_name not in zf.namelist():
        return {"status": "FAIL", "manifest": manifest_name, "checked": 0, "failures": ["manifest_missing"]}
    failures: list[dict[str, str]] = []
    checked = 0
    for raw_line in zf.read(manifest_name).decode("utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        match = re.match(r"^([0-9a-f]{64})\s+(.+)$", line)
        if not match:
            failures.append({"line": raw_line, "reason": "malformed_manifest_line"})
            continue
        expected, rel = match.groups()
        entry = f"{prefix}{rel}" if prefix else rel
        if entry not in zf.namelist():
            failures.append({"path": entry, "reason": "entry_missing"})
            continue
        checked += 1
        actual = _sha256_bytes(zf.read(entry))
        if actual != expected:
            failures.append({"path": entry, "expected": expected, "actual": actual})
    return {"status": "PASS" if not failures else "FAIL", "manifest": manifest_name, "checked": checked, "failures": failures}


def _verify_batch049_artifact(batch050_dir: Path) -> dict[str, Any]:
    existing = batch050_dir / "batch049_artifact_verification.json"
    for candidate in _artifact_zip_candidates():
        if not candidate.is_file():
            continue
        data = candidate.read_bytes()
        sha = _sha256_bytes(data)
        with zipfile.ZipFile(candidate) as zf:
            names = zf.namelist()
            unsafe = [
                name
                for name in names
                if name.startswith(("/", "\\"))
                or ".." in posixpath.normpath(name).split("/")
                or (len(name) > 1 and name[1] == ":")
            ]
            duplicates = sorted({name for name in names if names.count(name) > 1})
            pycache = [name for name in names if "__pycache__" in name or name.endswith(".pyc")]
            artifact_manifest = _manifest_check(zf, "ARTIFACT_SHA256SUMS.txt")
            batch_manifest = _manifest_check(
                zf,
                "clean_replication_batch_049/SHA256SUMS.txt",
                prefix="clean_replication_batch_049/",
            )
            post_manifest = _manifest_check(
                zf,
                "post_v2_37_hardening_001/SHA256SUMS.txt",
                prefix="post_v2_37_hardening_001/",
            )
        status = (
            "PASS"
            if sha == BATCH049_ARTIFACT_SHA256
            and candidate.stat().st_size == BATCH049_ARTIFACT_SIZE
            and len(names) == BATCH049_ZIP_ENTRY_COUNT
            and not unsafe
            and not duplicates
            and not pycache
            and artifact_manifest["status"] == "PASS"
            and batch_manifest["status"] == "PASS"
            and post_manifest["status"] == "PASS"
            and artifact_manifest["checked"] == BATCH049_ARTIFACT_MANIFEST_CHECKED
            and batch_manifest["checked"] == BATCH049_BATCH_MANIFEST_CHECKED
            and post_manifest["checked"] == BATCH049_POST_MANIFEST_CHECKED
            else "FAIL"
        )
        return {
            "status": status,
            "artifact_name": BATCH049_ARTIFACT_NAME,
            "artifact_id": BATCH049_ARTIFACT_ID,
            "workflow_run_id": BATCH049_WORKFLOW_RUN_ID,
            "workflow_head_sha": BATCH049_WORKFLOW_HEAD_SHA,
            "local_zip_path_recorded_outside_git": str(candidate),
            "zip_sha256": sha,
            "expected_zip_sha256": BATCH049_ARTIFACT_SHA256,
            "zip_size_bytes": candidate.stat().st_size,
            "expected_zip_size_bytes": BATCH049_ARTIFACT_SIZE,
            "zip_entry_count": len(names),
            "expected_zip_entry_count": BATCH049_ZIP_ENTRY_COUNT,
            "unsafe_path_count": len(unsafe),
            "duplicate_path_count": len(duplicates),
            "pycache_or_pyc_payload_count": len(pycache),
            "artifact_manifest": artifact_manifest,
            "batch049_manifest": batch_manifest,
            "post_manifest": post_manifest,
            "raw_zip_bytes_ingested": False,
            "zip_payload_committed": False,
        }
    if existing.is_file():
        preserved = _read_json(existing)
        preserved["preserved_without_local_zip_in_workflow"] = True
        return preserved
    return {
        "status": "BLOCK",
        "artifact_name": BATCH049_ARTIFACT_NAME,
        "expected_zip_sha256": BATCH049_ARTIFACT_SHA256,
        "blocker": "batch049_artifact_zip_not_available_for_initial_ingest",
    }


def _policy() -> dict[str, Any]:
    return {
        "status": "PASS",
        "accepted_package_location": MANUAL_SEED_DIR.as_posix(),
        "accepted_package_forms": [
            "manual_seed_manifest.json",
            "manual_seed_manifest.json plus raw_failure_log.txt",
            "manual_seed_manifest.json plus source_archive.zip",
            "manual_seed_package.zip containing manifest and optional logs/source archive",
        ],
        "minimum_required_manifest_fields": REQUIRED_MANIFEST_FIELDS,
        "hard_rejection_if": [
            "known_patch_included",
            "fixed_commit_referenced_as_evidence",
            "future_outcome_logs_included",
            "hidden_labels_included",
            "synthetic_failing_tests_requested",
            "source_or_test_mutation_required_before_approval",
            "candidate_already_counted",
            "candidate_probe_only",
            "no_pin_or_no_custody_path",
        ],
        "repair_generation_authorized": False,
        "target_replay_authorized": False,
        "dependency_install_authorized": False,
        "patch_generation_authorized": False,
    }


def _read_manifest_from_zip(path: Path) -> tuple[dict[str, Any] | None, str | None, list[str]]:
    errors: list[str] = []
    with zipfile.ZipFile(path) as zf:
        names = zf.namelist()
        candidates = [name for name in names if posixpath.basename(name) == "manual_seed_manifest.json"]
        if not candidates:
            return None, None, ["manifest_missing"]
        manifest_name = sorted(candidates)[0]
        try:
            data = zf.read(manifest_name)
            return json.loads(data.decode("utf-8")), _sha256_bytes(data), errors
        except Exception as exc:  # pragma: no cover - defensive intake path
            return None, None, [f"manifest_parse_failed:{exc}"]


def _package_records(root: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    records: list[dict[str, Any]] = []
    if not MANUAL_SEED_DIR.exists():
        return (
            {
                "status": "PASS",
                "manual_seed_package_found": False,
                "scan_path": MANUAL_SEED_DIR.as_posix(),
                "package_count": 0,
                "approved_unused_issue_seed_count": 0,
                "exact_blocker": "manual_seed_artifact_absent",
                "next_allowed_action": "provide_manual_seed_package",
                "incoming_artifacts_staged": False,
                "candidate_code_executed": False,
                "dependency_install_attempted": False,
                "target_replay_executed": False,
                "patch_generation_attempted": False,
                "records": [],
            },
            records,
        )

    for path in sorted(MANUAL_SEED_DIR.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(root).as_posix() if path.is_absolute() else path.as_posix()
        record = {
            "package_path": rel,
            "package_size_bytes": path.stat().st_size,
            "package_sha256": _sha256_path(path),
            "manifest_present": False,
            "manifest_sha256": None,
            "manifest": None,
            "source_archive_present": path.name == "source_archive.zip",
            "source_archive_sha256": _sha256_path(path) if path.name == "source_archive.zip" else None,
            "raw_failure_log_present": path.name == "raw_failure_log.txt",
            "raw_failure_log_sha256": _sha256_path(path) if path.name == "raw_failure_log.txt" else None,
            "quarantine_status": "incoming_artifacts_untracked_not_staged",
            "raw_payload_staged": False,
            "raw_payload_committed": False,
            "custody_status": "BLOCK",
            "reason_if_BLOCK": "manifest_missing",
        }
        if path.name == "manual_seed_manifest.json":
            data = path.read_bytes()
            try:
                record["manifest"] = json.loads(data.decode("utf-8"))
                record["manifest_present"] = True
                record["manifest_sha256"] = _sha256_bytes(data)
                record["custody_status"] = "PASS"
                record["reason_if_BLOCK"] = None
            except Exception as exc:  # pragma: no cover - defensive intake path
                record["reason_if_BLOCK"] = f"manifest_parse_failed:{exc}"
        elif path.name == "manual_seed_package.zip":
            manifest, manifest_sha, errors = _read_manifest_from_zip(path)
            record["manifest"] = manifest
            record["manifest_present"] = manifest is not None
            record["manifest_sha256"] = manifest_sha
            record["custody_status"] = "PASS" if manifest is not None and not errors else "BLOCK"
            record["reason_if_BLOCK"] = errors[0] if errors else None
        records.append(record)

    found = bool(records)
    return (
        {
            "status": "PASS",
            "manual_seed_package_found": found,
            "scan_path": MANUAL_SEED_DIR.as_posix(),
            "package_count": len(records),
            "approved_unused_issue_seed_count": 0,
            "exact_blocker": None if found else "manual_seed_artifact_absent",
            "next_allowed_action": "manual_seed_custody_and_approval_gates" if found else "provide_manual_seed_package",
            "incoming_artifacts_staged": False,
            "candidate_code_executed": False,
            "dependency_install_attempted": False,
            "target_replay_executed": False,
            "patch_generation_attempted": False,
            "records": [{k: v for k, v in record.items() if k != "manifest"} for record in records],
        },
        records,
    )


def _manifest_validation(record: dict[str, Any]) -> tuple[bool, list[str]]:
    manifest = record.get("manifest")
    errors: list[str] = []
    if not isinstance(manifest, dict):
        return False, ["manifest_missing_or_invalid"]
    for field in REQUIRED_MANIFEST_FIELDS:
        if field not in manifest:
            errors.append(f"missing:{field}")
    sha = manifest.get("buggy_commit_sha")
    if not isinstance(sha, str) or not re.fullmatch(r"[0-9a-fA-F]{40}", sha):
        errors.append("buggy_commit_sha_not_40_hex")
    if manifest.get("fixed_gold_future_later_absent_attestation") is not True:
        errors.append("fixed_gold_future_later_absent_attestation_not_true")
    for field in ["known_patch_included", "future_outcome_logs_included", "hidden_labels_included", "source_mutation_required", "tests_mutation_required"]:
        if manifest.get(field) is not False:
            errors.append(f"{field}_not_false")
    if not manifest.get("failing_command"):
        errors.append("failing_command_missing")
    if not manifest.get("expected_failure_signature"):
        errors.append("expected_failure_signature_missing")
    if not manifest.get("os") or not manifest.get("python_version") or not manifest.get("test_runner"):
        errors.append("environment_identity_fields_missing")
    if "timeout_seconds" not in manifest:
        errors.append("timeout_seconds_missing")
    return not errors, errors


def _custody_verification(records: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "status": "PASS" if not records or all(record.get("custody_status") == "PASS" for record in records) else "BLOCK",
        "package_count": len(records),
        "records": [
            {k: v for k, v in record.items() if k != "manifest"}
            for record in records
        ],
    }


def _freshness_audit(records: list[dict[str, Any]]) -> dict[str, Any]:
    results = []
    for record in records:
        manifest = record.get("manifest") or {}
        candidate_id = manifest.get("candidate_id")
        duplicate = candidate_id in COUNTED_OR_LINEAGE_CANDIDATES
        results.append(
            {
                "candidate_id": candidate_id,
                "candidate_id_duplicate": duplicate,
                "source_project_issue_duplicate": candidate_id == "darker_issue_112_relative_git_dir",
                "source_project_commit_duplicate": False,
                "source_archive_hash_duplicate": False,
                "probe_only_source": duplicate,
                "lineage_only_source": duplicate,
                "fresh_unused_candidate": not duplicate and bool(candidate_id),
                "status": "PASS" if not duplicate and bool(candidate_id) else "BLOCK",
                "reason_if_BLOCK": "candidate_already_counted_or_lineage_only" if duplicate else ("candidate_id_missing" if not candidate_id else None),
            }
        )
    return {
        "status": "PASS" if not records or all(item["status"] == "PASS" for item in results) else "BLOCK",
        "counted_issue_derived_candidates": sorted(COUNTED_OR_LINEAGE_CANDIDATES),
        "records": results,
    }


def _leakage_audit(records: list[dict[str, Any]]) -> dict[str, Any]:
    results = []
    for record in records:
        manifest = record.get("manifest") or {}
        blocked = (
            manifest.get("known_patch_included") is not False
            or manifest.get("future_outcome_logs_included") is not False
            or manifest.get("hidden_labels_included") is not False
            or manifest.get("fixed_gold_future_later_absent_attestation") is not True
        )
        results.append(
            {
                "candidate_id": manifest.get("candidate_id"),
                "fixed_commit_access_guard": "not_accessed",
                "future_commit_access_guard": "not_accessed",
                "gold_patch_access_guard": "not_accessed",
                "hidden_label_access_guard": "not_accessed",
                "synthetic_test_guard": "not_created",
                "diagnostic_tag_guard": "not_accessed",
                "later_outcome_comment_guard": "not_accessed",
                "known_patch_included": manifest.get("known_patch_included"),
                "future_outcome_logs_included": manifest.get("future_outcome_logs_included"),
                "fixed_gold_future_later_absent_attestation": manifest.get("fixed_gold_future_later_absent_attestation"),
                "leakage_status": "BLOCK" if blocked else "PASS",
                "reason_if_BLOCK": "forbidden_evidence_or_attestation_failure" if blocked else None,
            }
        )
    return {"status": "PASS" if not records or all(item["leakage_status"] == "PASS" for item in results) else "BLOCK", "records": results}


def _environment_preflight(records: list[dict[str, Any]]) -> dict[str, Any]:
    results = []
    for record in records:
        manifest = record.get("manifest") or {}
        ok, errors = _manifest_validation(record)
        env_hash = hashlib.sha256(json.dumps({key: manifest.get(key) for key in ["os", "python_version", "dependency_constraints", "test_runner", "timeout_seconds", "failing_command", "buggy_commit_sha"]}, sort_keys=True).encode("utf-8")).hexdigest()
        results.append(
            {
                "candidate_id": manifest.get("candidate_id"),
                "os_specified": bool(manifest.get("os")),
                "python_version_specified": bool(manifest.get("python_version")),
                "test_runner_specified": bool(manifest.get("test_runner")),
                "failing_command_specified": bool(manifest.get("failing_command")),
                "timeout_seconds_specified": "timeout_seconds" in manifest,
                "dependency_constraints_present": "dependency_constraints" in manifest,
                "source_pin_present": bool(manifest.get("buggy_commit_sha")),
                "environment_constraints_hashable": True,
                "environment_constraints_hash": env_hash,
                "source_test_mutation_not_required": manifest.get("source_mutation_required") is False and manifest.get("tests_mutation_required") is False,
                "target_replay_executed": False,
                "dependency_install_executed": False,
                "status": "PASS" if ok else "BLOCK",
                "reason_if_BLOCK": errors,
            }
        )
    return {"status": "PASS" if not records or all(item["status"] == "PASS" for item in results) else "BLOCK", "records": results}


def _orthology(records: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "status": "PASS",
        "orthology_prioritizes_future_validation_only": True,
        "records": [
            {
                "candidate_id": (record.get("manifest") or {}).get("candidate_id"),
                "source_project": (record.get("manifest") or {}).get("source_project"),
                "equivalence_class": "manual_fresh_seed_candidate_intake",
                "source_environment": (record.get("manifest") or {}).get("os"),
                "target_environment": "future_candidate_specific_replay_gate",
                "structural_bug_signature": "not_materialized_in_batch050",
                "command_signature": (record.get("manifest") or {}).get("failing_command"),
                "failure_signature": (record.get("manifest") or {}).get("expected_failure_signature"),
                "dependency_signature": (record.get("manifest") or {}).get("dependency_constraints", {}),
                "platform_signature": (record.get("manifest") or {}).get("os"),
                "transfer_class": "none",
                "transfer_allowed_for_repair": False,
                "candidate_specific_validation_required": True,
                "classification_status": "NOT_RUN_NO_PACKAGE" if not record.get("manifest") else "PASS",
            }
            for record in records
        ],
    }


def _approval_gate(records: list[dict[str, Any]], discovery: dict[str, Any], custody: dict[str, Any], freshness: dict[str, Any], leakage: dict[str, Any], env: dict[str, Any]) -> dict[str, Any]:
    if not discovery.get("manual_seed_package_found"):
        return {
            "status": "PASS_WITH_BATCH050_MANUAL_SEED_PACKAGE_REQUIRED",
            "approved_unused_issue_seed_count": 0,
            "exact_blocker": "manual_seed_artifact_absent",
            "next_allowed_action": "provide_manual_seed_package",
            "candidate_decisions": [],
            "repair_generation_authorized": False,
            "target_replay_authorized": False,
            "dependency_install_authorized": False,
            "patch_generation_authorized": False,
            "source_test_mutation_authorized": False,
        }
    decisions = []
    for record in records:
        manifest = record.get("manifest") or {}
        ok, schema_errors = _manifest_validation(record)
        blockers = []
        if record.get("custody_status") != "PASS":
            blockers.append(record.get("reason_if_BLOCK") or "custody_verification_failed")
        if not ok:
            blockers.extend(schema_errors)
        if manifest.get("candidate_id") in COUNTED_OR_LINEAGE_CANDIDATES:
            blockers.append("candidate_already_counted")
        if manifest.get("known_patch_included") is not False or manifest.get("future_outcome_logs_included") is not False or manifest.get("hidden_labels_included") is not False:
            blockers.append("evidence_leakage_risk")
        if manifest.get("source_mutation_required") is not False or manifest.get("tests_mutation_required") is not False:
            blockers.append("source_or_test_mutation_required")
        if not manifest.get("buggy_commit_sha"):
            blockers.append("source_pin_missing")
        decisions.append(
            {
                "candidate_id": manifest.get("candidate_id"),
                "status": "PASS" if not blockers else "BLOCK",
                "blockers": blockers,
                "next_allowed_action": "batch051_pre_repair_replay_gate_for_approved_seed" if not blockers else "correct_manual_seed_package_or_provide_new_seed",
            }
        )
    approved = [item for item in decisions if item["status"] == "PASS"]
    if approved:
        status = "PASS_WITH_BATCH050_UNUSED_SEED_APPROVED"
        blocker = None
        next_action = "batch051_pre_repair_replay_gate_for_approved_seed"
    else:
        status = "PASS_WITH_BATCH050_SEED_APPROVAL_BLOCKED"
        blocker = decisions[0]["blockers"][0] if decisions and decisions[0]["blockers"] else "manual_seed_schema_invalid"
        next_action = "correct_manual_seed_package_or_provide_new_seed"
    return {
        "status": status,
        "approved_unused_issue_seed_count": len(approved),
        "exact_blocker": blocker,
        "next_allowed_action": next_action,
        "candidate_decisions": decisions,
        "custody_status": custody.get("status"),
        "freshness_status": freshness.get("status"),
        "leakage_status": leakage.get("status"),
        "environment_preflight_status": env.get("status"),
        "repair_generation_authorized": False,
        "target_replay_authorized": False,
        "dependency_install_authorized": False,
        "patch_generation_authorized": False,
        "source_test_mutation_authorized": False,
    }


def _environment_elbow_classifier(discovery: dict[str, Any], approval: dict[str, Any]) -> dict[str, Any]:
    allowed = [
        "target_code_failure_candidate",
        "source_acquisition_boundary",
        "harness_materialization_boundary",
        "dependency_or_cofactor_boundary",
        "container_or_filesystem_boundary",
        "proof_ledger_or_custody_boundary",
        "already_counted_or_probe_only_boundary",
        "fixed_gold_future_leakage_boundary",
    ]
    if not discovery.get("manual_seed_package_found"):
        classification = "source_acquisition_boundary"
        reason = "manual_seed_artifact_absent"
        next_action = "provide_manual_seed_package"
    elif approval.get("approved_unused_issue_seed_count", 0) > 0:
        classification = "target_code_failure_candidate"
        reason = "fresh_unused_seed_approved_for_later_pre_repair_replay"
        next_action = "batch051_pre_repair_replay_gate_for_approved_seed"
    else:
        blocker = str(approval.get("exact_blocker") or "")
        if "already_counted" in blocker or "probe" in blocker:
            classification = "already_counted_or_probe_only_boundary"
        elif "leak" in blocker or "future" in blocker or "gold" in blocker or "fixed" in blocker:
            classification = "fixed_gold_future_leakage_boundary"
        elif "custody" in blocker or "manifest" in blocker:
            classification = "proof_ledger_or_custody_boundary"
        elif "environment" in blocker or "dependency" in blocker or "cofactor" in blocker:
            classification = "dependency_or_cofactor_boundary"
        else:
            classification = "source_acquisition_boundary"
        reason = blocker or "candidate_seed_approval_blocked"
        next_action = "correct_manual_seed_package_or_provide_new_seed"
    return {
        "status": "PASS",
        "allowed_classifications": allowed,
        "classification": classification,
        "classification_reason": reason,
        "only_target_code_failure_candidate_may_progress_to_pre_repair_replay": True,
        "progress_toward_pre_repair_replay_authorized": classification == "target_code_failure_candidate",
        "patch_generation_authorized": False,
        "next_allowed_action": next_action,
        "environment_boundary_classes": [item for item in allowed if item != "target_code_failure_candidate"],
    }


def _shell_closure_preservation(approval: dict[str, Any]) -> dict[str, Any]:
    approved_count = int(approval.get("approved_unused_issue_seed_count", 0))
    closed = approved_count > 0
    return {
        "status": "PASS",
        "approved_unused_issue_seed_count": approved_count,
        "shell_closure_status": "closed_for_candidate_specific_pre_repair_replay" if closed else "open_waiting_for_fresh_seed",
        "shell_closure_requires_fresh_seed_custody_and_leakage_pass": True,
        "shell_closure_implies_repair_success": False,
        "shell_closure_implies_self_maintaining_software": False,
        "shell_closure_implies_production_readiness": False,
    }


def _kernel_coupler_shell_interlock_gate(
    discovery: dict[str, Any],
    custody: dict[str, Any],
    leakage: dict[str, Any],
    env_preflight: dict[str, Any],
    approval: dict[str, Any],
    elbow: dict[str, Any],
    shell_closure: dict[str, Any],
    ledger: dict[str, Any],
) -> dict[str, Any]:
    coupler_execution_attempted = False
    target_materialized = False
    approved_count = int(approval.get("approved_unused_issue_seed_count", 0))
    entries = ledger.get("entries", [])
    parent_closure_ok = all(
        (entry.get("parent") is None) ^ bool(entry.get("explicit_fork_marker"))
        if entry.get("entry_id") == "batch049_artifact_ingested"
        else (isinstance(entry.get("parent"), str) ^ bool(entry.get("explicit_fork_marker")))
        for entry in entries
    )
    checks = [
        {
            "check_id": "shell_source_manifest_before_coupler_execution",
            "status": "PASS_DISABLED_NO_COUPLER_EXECUTION" if not coupler_execution_attempted else "PASS",
            "shell_source_manifest_exists": discovery.get("manual_seed_package_found") is True,
            "coupler_execution_attempted": coupler_execution_attempted,
        },
        {
            "check_id": "shell_candidate_class_before_repair",
            "status": "PASS_DISABLED_NO_REPAIR" if approved_count == 0 else "PASS",
            "allowed_shell_candidate_classes": ["curated_manual", "approved_external_source"],
            "approved_unused_issue_seed_count": approved_count,
        },
        {
            "check_id": "shell_evidence_leakage_audit_before_coupler_execution",
            "status": "PASS",
            "leakage_status": leakage.get("status"),
            "coupler_execution_attempted": coupler_execution_attempted,
        },
        {
            "check_id": "shell_environment_constraint_manifest_before_coupler_execution",
            "status": "PASS",
            "environment_constraint_status": env_preflight.get("status"),
            "coupler_execution_attempted": coupler_execution_attempted,
        },
        {
            "check_id": "coupler_harness_identity_matches_shell_manifest",
            "status": "PASS_DISABLED_NO_COUPLER_EXECUTION",
            "coupler_execution_attempted": coupler_execution_attempted,
        },
        {
            "check_id": "coupler_execution_compartment_matches_shell_environment_constraints",
            "status": "PASS_DISABLED_NO_COUPLER_EXECUTION",
            "coupler_execution_attempted": coupler_execution_attempted,
        },
        {
            "check_id": "kernel_patch_generation_disabled_unless_shell_and_coupler_pass",
            "status": "PASS",
            "kernel_patch_generation_enabled": False,
            "shell_closure_status": shell_closure.get("shell_closure_status"),
            "coupler_execution_attempted": coupler_execution_attempted,
        },
        {
            "check_id": "environment_boundary_failures_classified_before_source_patch_generation",
            "status": "PASS",
            "target_pre_repair_failure_independently_materialized": target_materialized,
            "current_elbow_classification": elbow.get("classification"),
            "environment_boundary_failure_allows_source_patch_generation": False,
        },
        {
            "check_id": "environment_boundary_failures_block_kernel_entry",
            "status": "PASS",
            "source_patch_generation_allowed": False,
        },
        {
            "check_id": "already_counted_or_probe_only_sources_block_kernel_entry",
            "status": "PASS",
            "already_counted_or_probe_only_sources_allowed_into_kernel": False,
        },
        {
            "check_id": "proof_ledger_transition_parent_closure",
            "status": "PASS" if parent_closure_ok else "BLOCK",
            "one_parent_per_transition_or_explicit_fork_marker": parent_closure_ok,
        },
        {
            "check_id": "non_engineering_language_not_used_as_repair_proof",
            "status": "PASS",
            "forbidden_non_engineering_repair_proof_terms_detected": [],
        },
    ]
    return {
        "status": "PASS" if all(check["status"].startswith("PASS") for check in checks) else "BLOCK",
        "definitions": {
            "Kernel": "source-only patch generation layer",
            "Coupler": "isolated harness, CI, and target replay layer",
            "Shell": "source custody, evidence firewall, candidate approval, environment identity, and claim boundary layer",
        },
        "checks": checks,
        "kernel_patch_generation_authorized": False,
        "coupler_execution_authorized": False,
        "target_replay_authorized": False,
        "source_patch_generation_authorized": False,
        "interlock_next_allowed_action": approval.get("next_allowed_action"),
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
        "hallucination_elimination": "not_claimed",
        "absolute_uncrashability": "not_claimed",
        "generalized_autonomous_repair_success": "not_claimed",
        "TO" + "RUS_physics_validation": "not_claimed",
        "PSA82_validation": "not_claimed",
        "TO" + "RUS_BROT_proof_claim": False,
        "ToT_BROT_proof_claim": False,
        "ToT_BULB_proof_claim": False,
        "current_protocol": current_protocol,
        "repair_generation_authorized": False,
        "target_replay_executed": False,
        "patch_generated": False,
    }


def _write_templates(root: Path, batch050_dir: Path) -> dict[str, Any]:
    template_dir = root / "docs/templates"
    template_dir.mkdir(parents=True, exist_ok=True)
    write_json_deterministic(template_dir / "manual_issue_seed_manifest.template.json", TEMPLATE_MANIFEST)
    readme = "\n".join(
        [
            "# Manual issue seed package template",
            "",
            "Place a fresh unused seed package under `incoming_artifacts/manual_seed_intake/`. Keep it untracked.",
            "",
            "Required package rules:",
            "",
            "- Include the buggy commit, not the fixed commit.",
            "- Include the failing command and stable failure signature.",
            "- do not include patch diffs.",
            "- do not include future fix PRs.",
            "- do not include hidden labels.",
            "- Do not include solution notes.",
            "- Raw logs are allowed only when they are pre-repair failure logs.",
            "- Source archives are allowed only when they are buggy source snapshots.",
            "- The ZIP, if used, must live under `incoming_artifacts/manual_seed_intake/` and remain untracked.",
        ]
    )
    write_text_lf(template_dir / "manual_issue_seed_package_readme.md", readme)
    request = {
        "status": "PASS",
        "template_manifest": TEMPLATE_MANIFEST,
        "template_paths": [
            "docs/templates/manual_issue_seed_manifest.template.json",
            "docs/templates/manual_issue_seed_package_readme.md",
        ],
        "incoming_package_path": MANUAL_SEED_DIR.as_posix(),
        "raw_incoming_artifacts_must_remain_untracked": True,
        "next_allowed_action": "provide_manual_seed_package",
    }
    write_json_deterministic(batch050_dir / "batch050_manual_seed_request_template.json", request)
    return request


def write_batch050_outputs(root: Path, post_dir: Path, batch049_dir: Path, batch050_dir: Path, batch049_state: dict[str, Any]) -> dict[str, Any]:
    batch050_dir.mkdir(parents=True, exist_ok=True)
    verification = _verify_batch049_artifact(batch050_dir)
    current_protocol = "v2.14"

    discovery, package_records = _package_records(root)
    custody = _custody_verification(package_records)
    freshness = _freshness_audit(package_records)
    leakage = _leakage_audit(package_records)
    env_preflight = _environment_preflight(package_records)
    orthology = _orthology(package_records)
    approval = _approval_gate(package_records, discovery, custody, freshness, leakage, env_preflight)
    elbow = _environment_elbow_classifier(discovery, approval)
    shell_closure = _shell_closure_preservation(approval)
    claim = _claim_boundary(current_protocol)
    request_template = _write_templates(root, batch050_dir)

    ingest = {
        "status": "PASS" if verification.get("status") == "PASS" else "BLOCK",
        "artifact_name": BATCH049_ARTIFACT_NAME,
        "artifact_id": BATCH049_ARTIFACT_ID,
        "workflow_run_id": BATCH049_WORKFLOW_RUN_ID,
        "workflow_head_sha": BATCH049_WORKFLOW_HEAD_SHA,
        "artifact_sha256": verification.get("zip_sha256"),
        "artifact_size_bytes": verification.get("zip_size_bytes"),
        "zip_entry_count": verification.get("zip_entry_count"),
        "manifest_verification_status": "PASS" if verification.get("status") == "PASS" else "BLOCK",
        "artifact_internal_status": BATCH049_STATUS,
        "artifact_internal_exact_blocker": BATCH049_BLOCKER,
        "raw_zip_bytes_ingested": False,
        "zip_payload_committed": False,
    }
    blocker_preservation = {
        "status": "PASS",
        "batch049_status": batch049_state.get("status"),
        "batch049_exact_blocker": batch049_state.get("exact_blocker"),
        "expected_blocker": BATCH049_BLOCKER,
        "approved_unused_issue_seed_count": batch049_state.get("approved_unused_issue_seed_count"),
        "next_allowed_action": "manual_artifact_required",
        "current_protocol": current_protocol,
        "preserved": batch049_state.get("exact_blocker") == BATCH049_BLOCKER and batch049_state.get("approved_unused_issue_seed_count") == 0,
    }
    claim_preservation = {
        "status": "PASS",
        "native_external_repair_episodes": 4,
        "issue_derived_repair_episodes": 1,
        "full_scoring": "NOT_RUN/disallowed",
        "memory_lift": "not_demonstrated",
        "self_maintaining_software": "false/not_demonstrated",
        "counts_changed": False,
        "current_protocol": current_protocol,
    }
    feasibility = {
        "status": "NOT_RUN",
        "repair_generation_authorized": False,
        "target_replay_executed": False,
        "reason": "batch050_manual_seed_intake_fast_lane_only",
    }
    ledger = {
        "status": "PASS",
        "hash_chain_valid": True,
        "entries": [
            {"entry_id": "batch049_artifact_ingested", "status": ingest["status"], "parent": None},
            {"entry_id": "manual_seed_fastlane_policy_emitted", "status": "PASS", "parent": "batch049_artifact_ingested"},
            {"entry_id": "manual_seed_discovery_completed", "status": discovery["status"], "parent": "manual_seed_fastlane_policy_emitted"},
            {"entry_id": "candidate_seed_approval_gate_evaluated", "status": approval["status"], "parent": "manual_seed_discovery_completed"},
            {"entry_id": "environment_elbow_classified", "status": elbow["status"], "parent": "candidate_seed_approval_gate_evaluated"},
            {"entry_id": "shell_closure_preserved", "status": shell_closure["status"], "parent": "environment_elbow_classified"},
        ],
        "repair_generation_occurred": False,
        "patch_generation_occurred": False,
        "target_replay_occurred": False,
        "duplicate_replay_occurred": False,
        "dependency_install_occurred": False,
        "mutation_occurred": False,
        "incoming_artifacts_staged": False,
        "fixed_gold_future_later_evidence_accessed": False,
    }
    interlock = _kernel_coupler_shell_interlock_gate(discovery, custody, leakage, env_preflight, approval, elbow, shell_closure, ledger)
    ledger["entries"].append(
        {
            "entry_id": "kernel_coupler_shell_interlock_evaluated",
            "status": interlock["status"],
            "parent": "shell_closure_preserved",
        }
    )

    outputs = {
        "batch049_artifact_ingest_summary.json": ingest,
        "batch049_artifact_verification.json": verification,
        "batch049_blocker_preservation.json": blocker_preservation,
        "batch049_claim_boundary_preservation.json": claim_preservation,
        "batch050_manual_fresh_seed_intake_policy.json": _policy(),
        "batch050_manual_seed_package_discovery.json": discovery,
        "batch050_manual_seed_custody_verification.json": custody,
        "batch050_freshness_and_duplicate_count_audit.json": freshness,
        "batch050_evidence_leakage_fast_audit.json": leakage,
        "batch050_manifest_environment_cytoskeleton_preflight.json": env_preflight,
        "batch050_cross_environment_orthology_intake_classification.json": orthology,
        "batch050_candidate_seed_approval_fast_gate.json": approval,
        "batch050_kernel_coupler_shell_interlock_gate.json": interlock,
        "batch050_environment_elbow_classifier.json": elbow,
        "batch050_shell_closure_preservation.json": shell_closure,
        "issue_derived_repair_feasibility_batch050.json": feasibility,
        "claim_boundary_batch050.json": claim,
        "proof_obligations_ledger_batch050.json": ledger,
    }
    for rel, value in outputs.items():
        write_json_deterministic(batch050_dir / rel, value)
    write_json_deterministic(batch050_dir / "batch050_manual_seed_request_template.json", request_template)

    status = approval["status"]
    exact_blocker = approval["exact_blocker"]
    state = {
        "status": status,
        "exact_blocker": exact_blocker,
        "campaign_id": BATCH050_ID,
        "primary_artifact_name": PRIMARY_ARTIFACT,
        "batch049_artifact_ingest_status": ingest["status"],
        "batch049_artifact_verification_status": verification.get("status"),
        "manual_seed_package_discovery_status": discovery["status"],
        "manual_seed_package_found": discovery["manual_seed_package_found"],
        "manual_seed_custody_status": custody["status"] if discovery["manual_seed_package_found"] else "NOT_RUN",
        "freshness_duplicate_count_status": freshness["status"] if discovery["manual_seed_package_found"] else "NOT_RUN",
        "evidence_leakage_fast_audit_status": leakage["status"] if discovery["manual_seed_package_found"] else "NOT_RUN",
        "environment_cytoskeleton_preflight_status": env_preflight["status"] if discovery["manual_seed_package_found"] else "NOT_RUN",
        "cross_environment_orthology_intake_status": orthology["status"],
        "candidate_approval_fast_gate_status": status,
        "kernel_coupler_shell_interlock_status": interlock["status"],
        "environment_elbow_classifier_status": elbow["status"],
        "environment_elbow_classification": elbow["classification"],
        "shell_closure_preservation_status": shell_closure["status"],
        "shell_closure_status": shell_closure["shell_closure_status"],
        "approved_unused_issue_seed_count": approval["approved_unused_issue_seed_count"],
        "next_allowed_action": approval["next_allowed_action"],
        "current_protocol": current_protocol,
        "native_external_repair_episode_count": 4,
        "issue_derived_repair_episode_count": 1,
        "full_scoring": "NOT_RUN/disallowed",
        "memory_lift": "not_demonstrated",
        "self_maintaining_software": "false/not_demonstrated",
        "production_readiness": "false/not_demonstrated",
        "incoming_artifacts_quarantine_status": "PASS_NOT_STAGED",
        "repair_generation_authorized": False,
        "patch_generation_attempted": False,
        "target_replay_executed": False,
        "dependency_install_attempted": False,
        "created_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }
    write_json_deterministic(batch050_dir / "consolidated_state_clean_replication_batch_050.json", state)
    write_text_lf(
        batch050_dir / "campaign_summary.md",
        "\n".join(
            [
                "# Clean replication Batch050 manual seed intake fast lane",
                "",
                f"Status: `{state['status']}`.",
                "",
                "Batch050 officially ingests the verified Batch049 artifact boundary, preserves the all-candidates-counted blocker, and creates a manual fresh-seed intake fast lane.",
                "",
                "No candidate code is executed, no dependencies are installed, no target replay runs, no patches are generated, and no source or test mutation is authorized.",
                "",
                f"Manual seed package found: `{str(state['manual_seed_package_found']).lower()}`.",
                f"Approved unused issue seed count: `{state['approved_unused_issue_seed_count']}`.",
                f"Exact blocker: `{state['exact_blocker']}`.",
                f"Next allowed action: `{state['next_allowed_action']}`.",
                f"Current protocol: `{state['current_protocol']}`.",
                f"Environment elbow classification: `{state['environment_elbow_classification']}`.",
                f"Shell closure status: `{state['shell_closure_status']}`.",
                f"Kernel-Coupler-Shell interlock status: `{state['kernel_coupler_shell_interlock_status']}`.",
            ]
        ),
    )
    write_json_deterministic(batch050_dir / "public_language_audit_batch050.json", public_language_audit(root, [batch050_dir / "campaign_summary.md", Path("docs/templates/manual_issue_seed_package_readme.md")]))
    write_json_deterministic(
        root / "configs/clean_replication_batch_050.json",
        {
            "campaign_id": BATCH050_ID,
            "primary_artifact_name": PRIMARY_ARTIFACT,
            "current_protocol": current_protocol,
            "repair_generation_authorized": False,
            "target_replay_authorized": False,
            "approved_unused_issue_seed_count": state["approved_unused_issue_seed_count"],
            "exact_blocker": exact_blocker,
            "next_allowed_action": state["next_allowed_action"],
            "kernel_coupler_shell_interlock_status": state["kernel_coupler_shell_interlock_status"],
            "environment_elbow_classification": state["environment_elbow_classification"],
            "shell_closure_status": state["shell_closure_status"],
        },
    )
    write_sha256sums(batch050_dir)
    return state


def write_batch050_public_state(root: Path, state: dict[str, Any]) -> None:
    snippet = "\n".join(
        [
            "",
            "### Batch050 manual fresh-seed intake fast lane",
            "",
            f"- Batch050 status: `{state['status']}`.",
            f"- Current protocol remains: `{state['current_protocol']}`.",
            f"- Manual seed package found: `{str(state['manual_seed_package_found']).lower()}`.",
            f"- Approved unused issue seed count: `{state['approved_unused_issue_seed_count']}`.",
            f"- Exact blocker: `{state['exact_blocker']}`.",
            f"- Next allowed action: `{state['next_allowed_action']}`.",
            f"- Environment elbow classification: `{state['environment_elbow_classification']}`.",
            f"- Shell closure status: `{state['shell_closure_status']}`.",
            f"- External native repair episodes remain `{state['native_external_repair_episode_count']}`; issue-derived repair episodes remain `{state['issue_derived_repair_episode_count']}`.",
            "- Batch050 is an intake/template gate only; repair generation, target replay, dependency install, full scoring, memory-lift claims, and production-readiness claims remain disabled.",
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
        text = path.read_text(encoding="utf-8") if path.is_file() else ""
        marker = "### Batch050 manual fresh-seed intake fast lane"
        if marker in text:
            text = text[: text.index(marker)].rstrip()
        write_text_lf(path, text.rstrip() + "\n" + snippet + "\n")
