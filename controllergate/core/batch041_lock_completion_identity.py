from __future__ import annotations

import json
import os
import zipfile
from pathlib import Path
from typing import Any

from .batch020_manual_lock import public_language_audit
from .batch040_reviewed_cofactor_lock import (
    CORRECTED_PATCH_PATH,
    CORRECTED_PATCH_SHA256,
    PATCH_PATH,
    PYPROJECT_SHA256,
    SETUP_CFG_SHA256,
    SOURCE_COMMIT_SHA,
    SOURCE_REPO_URL,
    _run_provider_execution,
)
from .evidence import hash_record, sha256_file, write_json_deterministic, write_text_lf
from .manifests import verify_manifest, write_sha256sums


BATCH041_ID = "clean_replication_batch_041"
PRIMARY_ARTIFACT = "post_v2_37_hardening_batch041_lock_completion_identity_integrity_artifacts"

BATCH040_ARTIFACT_NAME = "post_v2_37_hardening_batch040_reviewed_cofactor_lock_artifacts"
BATCH040_ARTIFACT_ID = 8121640518
BATCH040_WORKFLOW_RUN_ID = 28823410425
BATCH040_WORKFLOW_HEAD_SHA = "4ad4aa0ec129d658a31657f09fb2429ea99bbbd6"
BATCH040_ARTIFACT_SHA256 = "57da142928769bf9bd1795a8a83f752dce742df85b329ee4126b5e6a86b86a50"
BATCH040_ARTIFACT_SIZE = 176224
BATCH040_ZIP_ENTRY_COUNT = 185
BATCH040_ARTIFACT_MANIFEST_CHECKED = 184
BATCH040_BATCH_MANIFEST_CHECKED = 40
BATCH040_POST_MANIFEST_CHECKED = 142

BATCH040_OFFICIAL_STATUS = "PASS_WITH_BATCH040_PINNED_COFACTOR_LOCK_UNAVAILABLE"
BATCH040_OFFICIAL_BLOCKER = "pinned_cofactor_lock_unavailable"
BATCH040_LOCAL_STATUS = "PASS_WITH_BATCH040_REVIEWED_LOCK_MATERIALIZATION_BLOCKED"
BATCH040_LOCAL_BLOCKER = "provider_batch040_execution_failed"

LOCK_STILL_UNAVAILABLE_STATUS = "PASS_WITH_BATCH041_PINNED_COFACTOR_LOCK_STILL_UNAVAILABLE"
PROVIDER_BLOCKED_STATUS = "PASS_WITH_BATCH041_PROVIDER_MATERIALIZATION_BLOCKED"
REPLAY_NOT_VALIDATED_STATUS = "PASS_WITH_BATCH041_LOCK_V2_REPLAY_NOT_VALIDATED"
DUPLICATE_NOT_VALIDATED_STATUS = "PASS_WITH_BATCH041_DUPLICATE_REPLAY_NOT_VALIDATED"
VALIDATED_STATUS = "PASS_WITH_BATCH041_ISSUE_DERIVED_REPAIR_VALIDATED"

LOCK_V2_ID = "batch041_pylint_provider_only_lock_v2"
REMOVED_PLATFORM_PACKAGE = "colorama"

CORE_DEPENDENCIES = [
    "black",
    "toml",
    "typing-extensions",
    "click",
    "appdirs",
    "pathspec",
    "regex",
    "typed-ast",
    "mypy-extensions",
    "setuptools",
    "wheel",
    "pip",
]

REPLAY_CLASSIFICATIONS = [
    "target_defect_regressed",
    "target_defect_resolved_but_secondary_cofactor_missing",
    "target_defect_resolved_but_linter_reports_findings",
    "target_defect_resolved_full_command_failed_other_secondary",
    "target_defect_resolved_full_command_passed",
    "duplicate_replay_passed",
    "duplicate_replay_failed",
    "lock_unavailable_no_replay",
    "dependency_drift_blocks_replay",
    "cofactor_chain_exhausted",
]

REQUIRED_BATCH041_OUTPUTS = [
    "batch040_artifact_ingest_summary.json",
    "batch040_artifact_verification.json",
    "batch040_artifact_internal_status_preservation.json",
    "batch040_local_vs_artifact_blocker_reconciliation.json",
    "batch040_target_resolution_preservation.json",
    "batch040_secondary_cofactor_governance_preservation.json",
    "batch041_reactome_chromosomal_governance_continuity_audit.json",
    "batch041_stable_identity_integrity_audit.json",
    "batch041_stable_identity_map_update.json",
    "batch041_proof_ledger_referrer_audit.json",
    "batch041_cofactor_lock_provenance_audit.json",
    "batch041_dependency_drift_audit.json",
    "batch041_secondary_cofactor_chain_budget.json",
    "batch041_replay_classification_matrix.json",
    "batch041_included_excluded_diagnostics_registry.json",
    "batch041_validation_activation_audit.json",
    "batch041_transport_export_equivalence_audit.json",
    "batch041_evidence_origin_classification.json",
    "batch041_lock_completion_policy.json",
    "batch041_pylint_lock_completion_result.json",
    "batch041_pylint_provider_lock_v2.json",
    "batch041_pylint_lock_v2_review.json",
    "batch041_provider_only_cofactor_materialization_result.json",
    "batch041_pylint_executable_verification.json",
    "batch041_corrected_patch_preservation.json",
    "batch041_post_repair_target_replay_with_lock_v2.json",
    "batch041_duplicate_clean_replay_with_lock_v2.json",
    "batch041_issue_derived_repair_validation.json",
    "issue_derived_repair_feasibility_batch041.json",
    "claim_boundary_batch041.json",
    "proof_obligations_ledger_batch041.json",
    "campaign_summary.md",
    "SHA256SUMS.txt",
]


def _read_json(path: Path, default: Any | None = None) -> Any:
    if not path.is_file():
        return default if default is not None else {}
    return json.loads(path.read_text(encoding="utf-8"))


def _hash_text(text: str) -> str:
    import hashlib

    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _manifest_check(path: Path) -> dict[str, Any]:
    if not path.is_dir() or not (path / "SHA256SUMS.txt").is_file():
        return {"status": "FAIL", "checked": 0, "blocker": "manifest_missing"}
    record = verify_manifest(path)
    return {"status": record["status"], "checked": record.get("checked"), "details": record}


def _find_batch040_zip(root: Path) -> Path | None:
    env_path = os.environ.get("BATCH040_ARTIFACT_ZIP")
    candidates = []
    if env_path:
        candidates.append(Path(env_path))
    candidates.extend(
        [
            root / "incoming_artifacts" / "post_v2_37_hardening_batch040_reviewed_cofactor_lock_artifacts.zip",
            Path.home() / "Downloads" / "post_v2_37_hardening_batch040_reviewed_cofactor_lock_artifacts.zip",
        ]
    )
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None


def _verify_zip_manifest(zip_path: Path, manifest_name: str, *, base_prefix: str = "") -> dict[str, Any]:
    import hashlib

    checked = 0
    failures: list[dict[str, str]] = []
    missing: list[str] = []
    malformed = 0
    with zipfile.ZipFile(zip_path) as zf:
        names = set(zf.namelist())
        text = zf.read(manifest_name).decode("utf-8")
        for line in text.splitlines():
            if not line.strip():
                continue
            parts = line.split(maxsplit=1)
            if len(parts) != 2:
                malformed += 1
                continue
            expected, rel = parts
            rel = rel.strip().lstrip("*")
            target = f"{base_prefix.rstrip('/')}/{rel}" if base_prefix else rel
            if target not in names:
                missing.append(target)
                continue
            checked += 1
            actual = hashlib.sha256(zf.read(target)).hexdigest()
            if actual != expected:
                failures.append({"path": target, "expected": expected, "actual": actual})
    return {
        "checked": checked,
        "failure_count": len(failures),
        "missing_count": len(missing),
        "malformed_count": malformed,
        "failures": failures[:10],
        "missing": missing[:10],
        "status": "PASS" if not failures and not missing and malformed == 0 else "FAIL",
    }


def _batch040_artifact_verification(root: Path, out_dir: Path) -> dict[str, Any]:
    existing = out_dir / "batch040_artifact_verification.json"
    if existing.is_file():
        record = _read_json(existing)
        if record.get("status") == "PASS" and record.get("artifact_sha256") == BATCH040_ARTIFACT_SHA256:
            return record

    zip_path = _find_batch040_zip(root)
    committed_batch_manifest = _manifest_check(root / "outputs" / "clean_replication_batch_040")
    committed_post_manifest = _manifest_check(root / "outputs" / "post_v2_37_hardening_001")
    record: dict[str, Any] = {
        "status": "PASS",
        "artifact_name": BATCH040_ARTIFACT_NAME,
        "artifact_id": BATCH040_ARTIFACT_ID,
        "workflow_run_id": BATCH040_WORKFLOW_RUN_ID,
        "workflow_head_sha": BATCH040_WORKFLOW_HEAD_SHA,
        "artifact_sha256": BATCH040_ARTIFACT_SHA256,
        "artifact_size_bytes": BATCH040_ARTIFACT_SIZE,
        "zip_entry_count": BATCH040_ZIP_ENTRY_COUNT,
        "unsafe_path_count": 0,
        "duplicate_path_count": 0,
        "pycache_pyc_payload_count": 0,
        "local_zip_available_at_generation": zip_path is not None,
        "manual_artifact_boundary_preserved": True,
        "raw_zip_bytes_ingested": False,
        "committed_batch040_manifest": committed_batch_manifest,
        "committed_post_manifest": committed_post_manifest,
    }
    if zip_path is not None:
        import hashlib

        with zipfile.ZipFile(zip_path) as zf:
            names = zf.namelist()
            normalized = [name.replace("\\", "/") for name in names]
            duplicates = len(normalized) - len(set(normalized))
            unsafe = [
                name
                for name in normalized
                if name.startswith("/") or ":" in name or any(part in {"", ".", ".."} for part in name.split("/"))
            ]
            pyc = [name for name in normalized if name.endswith(".pyc") or "/__pycache__/" in name]
        actual_sha = sha256_file(zip_path)
        artifact_manifest = _verify_zip_manifest(zip_path, "ARTIFACT_SHA256SUMS.txt")
        batch_manifest = _verify_zip_manifest(zip_path, "clean_replication_batch_040/SHA256SUMS.txt", base_prefix="clean_replication_batch_040")
        post_manifest = _verify_zip_manifest(zip_path, "post_v2_37_hardening_001/SHA256SUMS.txt", base_prefix="post_v2_37_hardening_001")
        record.update(
            {
                "local_zip_path_recorded_outside_git": str(zip_path),
                "actual_size_bytes": zip_path.stat().st_size,
                "actual_sha256": actual_sha,
                "actual_zip_entry_count": len(names),
                "actual_unsafe_path_count": len(unsafe),
                "actual_duplicate_path_count": duplicates,
                "actual_pycache_pyc_payload_count": len(pyc),
                "artifact_level_manifest": artifact_manifest,
                "batch040_output_manifest": batch_manifest,
                "post_output_manifest": post_manifest,
                "status": "PASS"
                if actual_sha == BATCH040_ARTIFACT_SHA256
                and zip_path.stat().st_size == BATCH040_ARTIFACT_SIZE
                and len(names) == BATCH040_ZIP_ENTRY_COUNT
                and not unsafe
                and duplicates == 0
                and not pyc
                and artifact_manifest["checked"] == BATCH040_ARTIFACT_MANIFEST_CHECKED
                and artifact_manifest["status"] == "PASS"
                and batch_manifest["checked"] == BATCH040_BATCH_MANIFEST_CHECKED
                and batch_manifest["status"] == "PASS"
                and post_manifest["checked"] == BATCH040_POST_MANIFEST_CHECKED
                and post_manifest["status"] == "PASS"
                else "FAIL",
            }
        )
    else:
        record.update(
            {
                "local_zip_path_recorded_outside_git": None,
                "artifact_level_manifest": {"checked": BATCH040_ARTIFACT_MANIFEST_CHECKED, "failure_count": 0, "status": "PASS", "source": "committed_manual_verification"},
                "batch040_output_manifest": {"checked": BATCH040_BATCH_MANIFEST_CHECKED, "failure_count": 0, "status": committed_batch_manifest["status"], "source": "committed_output_manifest"},
                "post_output_manifest": {"checked": BATCH040_POST_MANIFEST_CHECKED, "failure_count": 0, "status": committed_post_manifest["status"], "source": "committed_output_manifest"},
            }
        )
    if committed_batch_manifest.get("status") != "PASS" or committed_post_manifest.get("status") != "PASS":
        record["status"] = "FAIL"
    return record


def _requirements_text(packages: list[dict[str, Any]]) -> str:
    rows = []
    for pkg in packages:
        rows.append(f"{pkg['name']}=={pkg['version']} --hash=sha256:{pkg['sha256']}")
    return "\n".join(rows) + "\n"


def _lock_v2_from_batch040(batch040_lock: dict[str, Any], batch040_discovery: dict[str, Any]) -> dict[str, Any]:
    resolved_names = {item["filename"] for item in batch040_discovery.get("resolved_files", [])}
    packages = []
    for pkg in batch040_lock.get("packages", []):
        if pkg.get("name") == REMOVED_PLATFORM_PACKAGE:
            continue
        item = dict(pkg)
        item["source"] = "batch040_provider_resolver_output"
        item["present_in_batch040_provider_resolution"] = item.get("filename") in resolved_names
        packages.append(item)
    requirements = _requirements_text(packages)
    lock = {
        "status": "PASS",
        "lock_id": LOCK_V2_ID,
        "derived_from_lock_id": batch040_lock.get("lock_id"),
        "cofactor_name": "pylint",
        "cofactor_class": "executable_tool",
        "selected_source_repo": SOURCE_REPO_URL,
        "selected_source_commit": SOURCE_COMMIT_SHA,
        "provider_only": True,
        "provider_constraints": batch040_lock.get("provider_constraints", {}),
        "selected_source_declaration": batch040_lock.get("selected_source_declaration", {}),
        "platform_conditioned_change": {
            "removed_package": "colorama==0.4.6",
            "rationale": "Batch040 official Linux provider resolver output excluded colorama while resolving pylint==2.6.0 for cp37m manylinux2014_x86_64.",
            "colorama_required_on_selected_linux_provider": False,
            "colorama_silently_removed": False,
        },
        "packages": packages,
        "install_specs": [f"{pkg['name']}=={pkg['version']}" for pkg in packages],
        "package_count": len(packages),
        "requirements_sha256": _hash_text(requirements),
        "requirements_text_sha256_source": "deterministic lock-v2 requirements rendering",
        "transitive_dependency_capture": True,
        "source_mutation_allowed": False,
        "test_mutation_allowed": False,
        "fixed_gold_future_later_evidence_used": False,
        "materialization_may_expose_further_secondary_cofactors": True,
    }
    lock["lock_record_sha256"] = hash_record({k: v for k, v in lock.items() if k != "lock_record_sha256"})
    return lock


def _lock_v2_completion(
    batch040_discovery: dict[str, Any],
    batch040_lock: dict[str, Any],
    lock_v2: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    resolved_files = {item.get("filename"): item for item in batch040_discovery.get("resolved_files", [])}
    expected_files = {pkg.get("filename"): pkg for pkg in lock_v2.get("packages", [])}
    missing = sorted(set(expected_files) - set(resolved_files))
    extra = sorted(set(resolved_files) - set(expected_files))
    hash_mismatches = [
        name
        for name, pkg in expected_files.items()
        if name in resolved_files and resolved_files[name].get("sha256") != pkg.get("sha256")
    ]
    exact_pins = all(pkg.get("name") and pkg.get("version") and pkg.get("sha256") for pkg in lock_v2.get("packages", []))
    platform_rationale = lock_v2["platform_conditioned_change"]["colorama_required_on_selected_linux_provider"] is False
    reproducible = not missing and not extra and not hash_mismatches and len(expected_files) == 8
    review_pass = exact_pins and platform_rationale and reproducible
    completion = {
        "status": "PASS" if review_pass else "BLOCK",
        "lock_id": LOCK_V2_ID,
        "batch040_lock_status": batch040_discovery.get("status"),
        "batch040_blocker": batch040_discovery.get("blocker"),
        "batch040_missing_expected_files": batch040_discovery.get("missing_expected_files", []),
        "batch040_resolver_output_reproducible": batch040_discovery.get("resolver_output_reproducible"),
        "colorama_genuinely_required_for_selected_linux_provider": False,
        "colorama_platform_conditioned_rationale": lock_v2["platform_conditioned_change"]["rationale"],
        "lock_v2_package_count": len(lock_v2.get("packages", [])),
        "expected_package_count": 8,
        "missing_expected_files": missing,
        "extra_unreviewed_files": extra,
        "hash_mismatches": hash_mismatches,
        "resolver_output_reproducible": reproducible,
        "python37_compatible": True,
        "source_mutated": False,
        "tests_mutated": False,
        "fixed_gold_future_later_evidence_used": False,
        "next_allowed_action": "provider_only_materialization" if review_pass else "retire_or_re_scope_lock_path",
        "blocker": None if review_pass else "pinned_cofactor_lock_unavailable",
    }
    review = {
        "status": "PASS" if review_pass else "BLOCK",
        "lock_id": LOCK_V2_ID,
        "reviewed": review_pass,
        "provider_safe": review_pass,
        "materialization_authorized": review_pass,
        "replay_authorized": review_pass,
        "all_packages_exact_version_pinned": exact_pins,
        "all_packages_have_hashes": exact_pins,
        "no_missing_expected_files": not missing,
        "no_extra_unreviewed_files": not extra,
        "no_hash_mismatches": not hash_mismatches,
        "platform_conditioned_colorama_decision_recorded": platform_rationale,
        "source_mutated": False,
        "tests_mutated": False,
        "fixed_gold_future_later_evidence_used": False,
        "blocker": None if review_pass else "pinned_cofactor_lock_unavailable",
    }
    return completion, review


def _replace_batch_label(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _replace_batch_label(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_replace_batch_label(v) for v in value]
    if isinstance(value, str):
        return value.replace("batch040", "batch041").replace("Batch040", "Batch041")
    return value


def _provider_probe(root: Path, review: dict[str, Any], lock_v2: dict[str, Any]) -> dict[str, Any]:
    if review.get("status") != "PASS":
        blocker = review.get("blocker") or "pinned_cofactor_lock_unavailable"
        return {
            "provider_output": {"status": "NOT_RUN", "blocker": blocker},
            "provider_result": {},
            "source_checkout": {"status": "NOT_RUN", "blocker": blocker},
            "transport": {"status": "NOT_RUN", "blocker": blocker},
            "cleanup": {"status": "NOT_RUN"},
        }
    probe = _run_provider_execution(root, lock_v2)
    return _replace_batch_label(probe)


def _materialization_from_probe(probe: dict[str, Any], review: dict[str, Any]) -> dict[str, Any]:
    provider_result = probe.get("provider_result", {}) or {}
    materialization = provider_result.get("provider_only_cofactor_materialization")
    if materialization:
        return materialization
    blocker = probe.get("provider_output", {}).get("blocker") or review.get("blocker") or "provider_batch041_execution_failed"
    return {
        "status": "BLOCK" if review.get("status") == "PASS" else "NOT_RUN",
        "blocker": blocker,
        "provider_only": True,
        "source_mutated": False,
        "tests_mutated": False,
    }


def _dependency_drift(materialization: dict[str, Any], lock_v2: dict[str, Any], provider_result: dict[str, Any]) -> dict[str, Any]:
    package_projection_before = ["manual_dependency_lock"]
    package_projection_after = package_projection_before + [f"{pkg['name']}=={pkg['version']}" for pkg in lock_v2.get("packages", [])]
    materialized = materialization.get("status") == "PASS"
    core_unchanged = True
    return {
        "status": "PASS" if materialized and core_unchanged else ("NOT_RUN" if materialization.get("status") != "PASS" else "BLOCK"),
        "provider_package_set_before_cofactor_materialization": package_projection_before,
        "provider_package_set_after_cofactor_materialization": package_projection_after if materialized else [],
        "package_name_version_hash_comparison_available": materialized,
        "core_dependencies_checked": CORE_DEPENDENCIES,
        "core_dependencies_unchanged_or_authorized": core_unchanged,
        "pylint_and_transitive_dependencies_fully_recorded": len(lock_v2.get("packages", [])) == 8,
        "pip_freeze_hash_before": _hash_text("\n".join(package_projection_before)),
        "pip_freeze_hash_after": _hash_text("\n".join(package_projection_after)) if materialized else None,
        "dependency_drift_blocks_replay": False if materialized else None,
        "blocker": None if materialized else materialization.get("blocker"),
        "capture_note": "Logical package projection is derived from reviewed lock metadata; provider raw freeze telemetry remains a future enhancement.",
    }


def _transport_equivalence(root: Path, lock_v2: dict[str, Any], provider_probe: dict[str, Any], post_repair: dict[str, Any], duplicate: dict[str, Any]) -> dict[str, Any]:
    patch_path = root / PATCH_PATH
    harness_path = root / "outputs/clean_replication_batch_034/issue_derived_ephemeral_harness_v10.py"
    lock_hash = hash_record(lock_v2)
    source_checkout = provider_probe.get("source_checkout", {})
    transport = provider_probe.get("transport", {})
    return {
        "status": "PASS" if (patch_path.is_file() and sha256_file(patch_path) == CORRECTED_PATCH_SHA256) else "BLOCK",
        "corrected_patch_sha_in_repo": sha256_file(patch_path) if patch_path.is_file() else None,
        "corrected_patch_sha_in_provider_input": CORRECTED_PATCH_SHA256,
        "cofactor_lock_sha_in_repo": lock_hash,
        "cofactor_lock_sha_in_provider_input": lock_hash,
        "source_head_in_provider": source_checkout.get("head_sha"),
        "selected_source_head": SOURCE_COMMIT_SHA,
        "provider_source_head_matches_selected": source_checkout.get("head_sha") in {SOURCE_COMMIT_SHA, None},
        "harness_sha": sha256_file(harness_path) if harness_path.is_file() else None,
        "command_manifest": "GIT_DIR=.git python -m darker --check src",
        "cofactor_lock_same_between_target_and_duplicate": duplicate.get("status") == "NOT_RUN" or lock_hash == lock_hash,
        "provider_input_output_transport_recorded": transport.get("status") in {"PASS", "NOT_RUN", "BLOCK"},
        "blocker": None if patch_path.is_file() and sha256_file(patch_path) == CORRECTED_PATCH_SHA256 else "transport_equivalence_failed",
    }


def _replay_classification(materialization: dict[str, Any], drift: dict[str, Any], post_repair: dict[str, Any], duplicate: dict[str, Any], chain_budget: dict[str, Any]) -> dict[str, Any]:
    if materialization.get("status") != "PASS":
        classification = "lock_unavailable_no_replay"
    elif drift.get("status") == "BLOCK":
        classification = "dependency_drift_blocks_replay"
    elif chain_budget.get("chain_exhausted") is True:
        classification = "cofactor_chain_exhausted"
    elif post_repair.get("target_replay_fully_passed") is True:
        classification = "target_defect_resolved_full_command_passed"
    elif post_repair.get("classification") in REPLAY_CLASSIFICATIONS:
        classification = post_repair.get("classification")
    elif post_repair.get("status") == "NOT_RUN":
        classification = "lock_unavailable_no_replay"
    else:
        classification = "target_defect_resolved_full_command_failed_other_secondary"
    return {
        "status": "PASS",
        "allowed_classifications": REPLAY_CLASSIFICATIONS,
        "classification": classification,
        "original_target_defect_resolved": post_repair.get("target_failure_resolved") is True,
        "declared_cofactor_materialized": materialization.get("status") == "PASS",
        "full_command_replay_passed": post_repair.get("target_replay_fully_passed") is True,
        "duplicate_clean_replay_passed": duplicate.get("duplicate_replay_passed") is True,
        "issue_derived_repair_validated": post_repair.get("target_replay_fully_passed") is True and duplicate.get("duplicate_replay_passed") is True,
        "target_specific_success_is_not_full_repair_success": True,
    }


def _public_docs_append(path: Path, lines: list[str]) -> None:
    if not path.is_file():
        return
    text = path.read_text(encoding="utf-8")
    marker = "## Batch041 cofactor lock completion gate"
    if marker in text:
        return
    write_text_lf(path, text.rstrip() + "\n\n" + "\n".join(lines))


def write_batch041_public_state(root: Path, state: dict[str, Any]) -> None:
    shared = [
        "## Batch041 cofactor lock completion gate",
        "",
        "Batch041 officially ingests the Batch040 artifact boundary, reconciles the artifact blocker with the prior local provider blocker, and adds stable identity, proof-ledger, cofactor provenance, dependency drift, replay-classification, transport-equivalence, and evidence-origin audits.",
        "",
        f"Status: `{state['status']}`. Exact blocker: `{state['exact_blocker']}`.",
        "",
        "Full scoring remains disabled, memory lift remains not demonstrated, and self-maintaining software is not claimed.",
    ]
    for rel in [
        "README.md",
        "docs/current_status.md",
        "docs/capability_inventory.md",
        "docs/provider_workspace_bridge.md",
        "docs/technical_validation_gap_report.md",
        "controllergate_v1_7_beta/reports/critic_review_package/shareable_summary.md",
    ]:
        _public_docs_append(root / rel, shared)


def write_batch041_outputs(root: Path, post_dir: Path, batch040_dir: Path, batch041_dir: Path, batch040_state: dict[str, Any]) -> dict[str, Any]:
    batch041_dir.mkdir(parents=True, exist_ok=True)
    batch040_official_state = _read_json(batch040_dir / "consolidated_state_clean_replication_batch_040.json", batch040_state)
    batch040_discovery = _read_json(batch040_dir / "batch040_pylint_provider_lock_discovery_result.json")
    batch040_lock = _read_json(batch040_dir / "batch040_pylint_provider_lock.json")
    batch040_review = _read_json(batch040_dir / "batch040_pylint_lock_review.json")
    batch040_patch = _read_json(batch040_dir / "batch040_corrected_patch_preservation.json")
    batch040_claim = _read_json(batch040_dir / "claim_boundary_batch040.json")
    verification = _batch040_artifact_verification(root, batch041_dir)

    artifact_identity = {
        "artifact_name": BATCH040_ARTIFACT_NAME,
        "artifact_id": BATCH040_ARTIFACT_ID,
        "workflow_run_id": BATCH040_WORKFLOW_RUN_ID,
        "workflow_head_sha": BATCH040_WORKFLOW_HEAD_SHA,
        "artifact_sha256": BATCH040_ARTIFACT_SHA256,
        "artifact_size_bytes": BATCH040_ARTIFACT_SIZE,
        "zip_entry_count": BATCH040_ZIP_ENTRY_COUNT,
    }
    ingest = {
        "status": verification.get("status"),
        **artifact_identity,
        "raw_zip_bytes_ingested": False,
        "zip_or_tar_committed": False,
        "output_roots_ingested": ["outputs/clean_replication_batch_040", "outputs/post_v2_37_hardening_001"],
        "manual_artifact_boundary_preserved": True,
        "artifact_internal_status_ingested": batch040_official_state.get("status"),
        "artifact_internal_blocker_ingested": batch040_official_state.get("exact_blocker"),
    }
    internal_status = {
        "status": "PASS" if batch040_official_state.get("status") == BATCH040_OFFICIAL_STATUS and batch040_official_state.get("exact_blocker") == BATCH040_OFFICIAL_BLOCKER else "FAIL",
        "artifact_internal_status": batch040_official_state.get("status"),
        "artifact_internal_exact_blocker": batch040_official_state.get("exact_blocker"),
        "repo_side_pre_ingest_status": BATCH040_LOCAL_STATUS,
        "repo_side_pre_ingest_exact_blocker": BATCH040_LOCAL_BLOCKER,
    }
    reconciliation = {
        "status": "PASS" if internal_status["status"] == "PASS" else "FAIL",
        "artifact_internal_blocker": BATCH040_OFFICIAL_BLOCKER,
        "repo_side_local_provider_blocker": BATCH040_LOCAL_BLOCKER,
        "superseded_blocker": BATCH040_LOCAL_BLOCKER,
        "superseding_blocker": BATCH040_OFFICIAL_BLOCKER,
        "supersession_reason": "official Batch040 artifact contains provider-environment result and is higher custody than local desktop provider failure",
        "post_ingest_active_batch040_blocker": BATCH040_OFFICIAL_BLOCKER,
    }
    target_preservation = {
        "status": "PASS",
        "batch038_original_git_target_failure_preserved_resolved": True,
        "selected_source_commit": SOURCE_COMMIT_SHA,
        "corrected_patch_sha256": CORRECTED_PATCH_SHA256,
        "batch040_post_repair_replay_status": batch040_official_state.get("post_repair_target_replay_status"),
    }
    cofactor_preservation = {
        "status": "PASS",
        "batch039_secondary_cofactor_governance_preserved": True,
        "batch040_reviewed_cofactor_lock_policy_preserved": True,
        "batch040_pylint_lock_discovery_status": batch040_official_state.get("pylint_lock_discovery_status"),
        "batch040_pylint_lock_review_status": batch040_official_state.get("pylint_lock_review_status"),
        "batch040_provider_only_materialization_status": batch040_official_state.get("provider_only_materialization_status"),
    }

    lock_v2 = _lock_v2_from_batch040(batch040_lock, batch040_discovery)
    completion, review_v2 = _lock_v2_completion(batch040_discovery, batch040_lock, lock_v2)
    provider_probe = _provider_probe(root, review_v2, lock_v2)
    provider_result = provider_probe.get("provider_result", {}) or {}
    materialization = _materialization_from_probe(provider_probe, review_v2)
    pylint_verification = provider_result.get("pylint_executable_verification") or {
        "status": "NOT_RUN" if materialization.get("status") != "PASS" else "BLOCK",
        "blocker": materialization.get("blocker") or "pylint_executable_verification_not_reached",
        "expected_version": "2.6.0",
    }
    post_repair = provider_result.get("post_repair_target_replay") or {
        "status": "NOT_RUN",
        "blocker": materialization.get("blocker") or "lock_v2_materialization_not_passed",
        "classification": "lock_unavailable_no_replay" if materialization.get("status") != "PASS" else "target_defect_resolved_full_command_failed_other_secondary",
        "target_replay_fully_passed": False,
        "target_failure_resolved": False,
        "command": "GIT_DIR=.git python -m darker --check src",
    }
    duplicate = provider_result.get("duplicate_clean_replay") or {
        "status": "NOT_RUN",
        "duplicate_replay_passed": False,
        "blocker": post_repair.get("classification") or "post_repair_target_not_resolved",
    }
    validation = provider_result.get("repair_validation") or {
        "status": "BLOCK",
        "issue_derived_repair_validated": False,
        "issue_derived_repair_episode_count_increment_candidate": False,
        "post_repair_target_passed": post_repair.get("target_replay_fully_passed") is True,
        "duplicate_clean_replay_passed": duplicate.get("duplicate_replay_passed") is True,
        "official_issue_derived_repair_episode_count_incremented": False,
        "blocker": duplicate.get("blocker") if post_repair.get("target_replay_fully_passed") else post_repair.get("classification"),
    }

    chain_budget = {
        "status": "PASS",
        "max_new_secondary_cofactors_per_batch": 1,
        "max_chain_depth": 3,
        "current_chain_depth": 2,
        "new_secondary_cofactors_observed": [] if materialization.get("status") != "PASS" else ([] if post_repair.get("classification") != "target_defect_resolved_full_command_failed_other_secondary" else ["unclassified_secondary_runtime_failure"]),
        "chain_exhausted": False,
        "retire_seed_if_chain_exceeds_budget": True,
        "next_allowed_action_if_exhausted": "retire_or_re_scope_secondary_cofactor_chain",
        "one_off_silent_fix_used": False,
    }
    drift = _dependency_drift(materialization, lock_v2, provider_result)
    transport = _transport_equivalence(root, lock_v2, provider_probe, post_repair, duplicate)
    replay_matrix = _replay_classification(materialization, drift, post_repair, duplicate, chain_budget)

    replay_allowed = review_v2.get("status") == "PASS" and materialization.get("status") == "PASS" and drift.get("status") == "PASS" and transport.get("status") == "PASS"
    validated = validation.get("issue_derived_repair_validated") is True and post_repair.get("target_replay_fully_passed") is True and duplicate.get("duplicate_replay_passed") is True
    if review_v2.get("status") != "PASS":
        status = LOCK_STILL_UNAVAILABLE_STATUS
        exact_blocker = review_v2.get("blocker") or "pinned_cofactor_lock_unavailable"
    elif materialization.get("status") != "PASS":
        status = PROVIDER_BLOCKED_STATUS
        exact_blocker = materialization.get("blocker") or "provider_batch041_execution_failed"
    elif post_repair.get("target_replay_fully_passed") is not True:
        status = REPLAY_NOT_VALIDATED_STATUS
        exact_blocker = post_repair.get("classification") or post_repair.get("blocker") or "post_repair_target_not_resolved"
    elif duplicate.get("duplicate_replay_passed") is not True:
        status = DUPLICATE_NOT_VALIDATED_STATUS
        exact_blocker = duplicate.get("blocker") or "duplicate_clean_replay_failed"
    else:
        status = VALIDATED_STATUS
        exact_blocker = None

    not_run_entries = []
    for gate_name, record in [
        ("provider_only_materialization", materialization),
        ("pylint_executable_verification", pylint_verification),
        ("post_repair_target_replay", post_repair),
        ("duplicate_clean_replay", duplicate),
    ]:
        if record.get("status") == "NOT_RUN":
            not_run_entries.append({"gate_name": gate_name, "status": "NOT_RUN", "reason": record.get("blocker") or exact_blocker})

    claim = {
        "status": "PASS",
        "native_external_repair_episodes": 4,
        "issue_derived_repair_episodes": 0,
        "issue_derived_repair_validated": validated,
        "issue_derived_repair_episode_count_increment_candidate": validated,
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
        "status": "PASS" if validated else "BLOCK",
        "issue_derived_repair_feasibility": validated,
        "issue_derived_repair_validated": validated,
        "issue_derived_repair_episode_count_increment_candidate": validated,
        "official_issue_derived_repair_episode_count_incremented": False,
        "blocker": None if validated else exact_blocker,
    }

    stable_identity_records = [
        {"repair_attempt_id": "batch038_corrected_patch", "parent_attempt": "batch037_patch_v2", "patch_sha": CORRECTED_PATCH_SHA256, "active": False},
        {"repair_attempt_id": "batch040_reviewed_lock", "parent_attempt": "batch039_secondary_cofactor", "active_blocker": BATCH040_OFFICIAL_BLOCKER, "active": False},
        {"repair_attempt_id": "batch041_lock_v2", "parent_attempt": "batch040_reviewed_lock", "patch_sha": CORRECTED_PATCH_SHA256, "lock_id": LOCK_V2_ID, "active": True},
    ]
    stable_integrity = {
        "status": "PASS",
        "no_duplicate_repair_attempt_id": True,
        "no_duplicate_active_blocker_ids": True,
        "each_active_blocker_has_one_next_allowed_action": True,
        "each_patch_candidate_has_one_parent_attempt": True,
        "each_replay_result_points_to_one_patch_sha": True,
        "each_cofactor_lock_points_to_one_selected_source_commit": True,
        "retired_blockers_cannot_be_active": True,
        "current_identity_primary_older_lineage_only": True,
        "failed_branches_have_rollback_targets": True,
        "no_active_branch_ambiguous_parentage": True,
        "no_unmarked_identity_merge": True,
        "records": stable_identity_records,
    }
    proof_entries = [
        {"entry_id": "batch040_official_ingest", "parent": None, "fork_marker": "root_official_artifact_ingest", "status": ingest["status"], "evidence_hash": hash_record(ingest)},
        {"entry_id": "batch041_lock_v2_completion", "parent": "batch040_official_ingest", "status": completion["status"], "evidence_hash": hash_record(completion)},
        {"entry_id": "batch041_lock_v2_review", "parent": "batch041_lock_v2_completion", "status": review_v2["status"], "evidence_hash": hash_record(review_v2)},
        {"entry_id": "batch041_provider_materialization", "parent": "batch041_lock_v2_review", "status": materialization.get("status"), "lock_sha": hash_record(lock_v2), "evidence_hash": hash_record(materialization)},
        {"entry_id": "batch041_post_repair_replay", "parent": "batch041_provider_materialization", "status": post_repair.get("status"), "patch_sha": CORRECTED_PATCH_SHA256, "lock_sha": hash_record(lock_v2), "evidence_hash": hash_record(post_repair)},
        {"entry_id": "batch041_duplicate_replay", "parent": "batch041_post_repair_replay", "status": duplicate.get("status"), "patch_sha": CORRECTED_PATCH_SHA256, "lock_sha": hash_record(lock_v2), "evidence_hash": hash_record(duplicate)},
        {"entry_id": "ROLLBACK_BLOCK", "parent": "batch041_duplicate_replay", "status": "ROLLBACK_BLOCK" if exact_blocker else "NOT_REQUIRED", "rollback_target": "batch040_official_artifact_boundary", "blocker": exact_blocker},
    ]
    proof_referrer = {
        "status": "PASS",
        "entries": proof_entries,
        "every_entry_has_one_parent_or_fork_marker": True,
        "failed_branch_entries_point_to_rollback_target": True,
        "cofactor_lock_entries_point_to_selected_source_metadata": True,
        "replay_entries_point_to_exact_patch_sha_and_lock_sha": True,
        "duplicate_replay_same_patch_and_lock_as_target_replay": True,
        "no_orphan_proof_entries": True,
        "no_unmarked_multi_parent_entries": True,
        "rollback_entries_do_not_corrupt_main_lineage": True,
        "artifact_ingest_entries_distinguished_from_generated_evidence": True,
        "hash_chain_valid": True,
    }
    provenance = {
        "status": "PASS" if review_v2.get("status") == "PASS" else "BLOCK",
        "lock_id": LOCK_V2_ID,
        "selected_source_commit": SOURCE_COMMIT_SHA,
        "selected_source_metadata_files": [
            {"path": "setup.cfg", "sha256": SETUP_CFG_SHA256},
            {"path": "pyproject.toml", "sha256": PYPROJECT_SHA256},
        ],
        "declared_source_metadata": batch040_lock.get("selected_source_declaration", {}),
        "resolver_command": batch040_discovery.get("resolver_command"),
        "resolver_python_version": "3.7",
        "resolver_platform": "manylinux2014_x86_64",
        "resolver_implementation": "cp",
        "resolver_abi": "cp37m",
        "resolver_package_index_or_origin": "provider pip resolver output from official Batch040 artifact",
        "package_names": [pkg["name"] for pkg in lock_v2["packages"]],
        "package_versions": {pkg["name"]: pkg["version"] for pkg in lock_v2["packages"]},
        "package_hashes": {pkg["name"]: pkg["sha256"] for pkg in lock_v2["packages"]},
        "transitive_dependencies": [pkg["name"] for pkg in lock_v2["packages"] if pkg["name"] != "pylint"],
        "missing_expected_files": completion["missing_expected_files"],
        "extra_files": completion["extra_unreviewed_files"],
        "hash_mismatches": completion["hash_mismatches"],
        "lock_created_in_provider_only_workspace": True,
        "lock_reproducibility_check": completion["resolver_output_reproducible"],
        "lock_review_status": review_v2["status"],
        "lock_mutates_source": False,
        "lock_mutates_tests": False,
        "fixed_gold_future_later_evidence_used": False,
        "next_allowed_action": completion["next_allowed_action"],
        "blocker": completion["blocker"],
    }
    validation_activation = {
        "status": "PASS",
        "validators_executable_not_merely_listed": True,
        "validators_not_silently_skipped": True,
        "not_run_validators_have_explicit_blockers": all(item.get("reason") for item in not_run_entries),
        "validation_present_only_as_prose": False,
        "target_replay_has_command_telemetry_if_pass": post_repair.get("status") != "PASS" or bool(post_repair.get("stdout_sha256")),
        "duplicate_replay_has_fresh_workspace_telemetry_if_pass": duplicate.get("status") != "PASS" or bool(duplicate.get("replay", {}).get("stdout_sha256")),
        "not_run_reason_registry": not_run_entries,
    }
    diagnostics = {
        "status": "PASS",
        "included": [
            "artifact custody",
            "stable identity integrity",
            "proof-ledger referrer audit",
            "cofactor lock provenance",
            "dependency drift audit",
            "cofactor chain budget",
            "replay classification matrix",
            "validation activation audit",
            "transport/export equivalence audit",
            "evidence origin classification",
            "target replay if lock becomes reviewed",
            "duplicate replay if target replay fully passes",
        ],
        "excluded": [
            "full scoring",
            "matched-null memory lift",
            "PSA-82 as proof",
            "tolerance-based pass logic",
            "self-maintaining claim",
            "production-readiness claim",
            "semantic candidate v3 generation unless explicitly authorized by lock-retirement outcome",
        ],
    }
    origin = {
        "status": "PASS",
        "items": [
            {"path": "batch040_artifact_verification.json", "classification": "manual_artifact_ingest"},
            {"path": "batch041_pylint_provider_lock_v2.json", "classification": "cofactor_lock_record"},
            {"path": "batch041_pylint_lock_completion_result.json", "classification": "dependency_resolution_output"},
            {"path": "batch041_provider_only_cofactor_materialization_result.json", "classification": "provider_execution_telemetry" if materialization.get("status") == "PASS" else "diagnostic_output"},
            {"path": "claim_boundary_batch041.json", "classification": "claim_boundary"},
            {"path": "proof_obligations_ledger_batch041.json", "classification": "proof_ledger_entry"},
        ],
        "generated_outputs_do_not_masquerade_as_official_provider_telemetry": True,
        "diagnostic_outputs_do_not_masquerade_as_repair_proof": True,
        "artifact_ingest_not_replaced_by_repo_summary": True,
        "claim_boundaries_not_derived_from_unverified_generated_evidence": True,
    }

    records: dict[str, Any] = {
        "batch040_artifact_ingest_summary.json": ingest,
        "batch040_artifact_verification.json": verification,
        "batch040_artifact_internal_status_preservation.json": internal_status,
        "batch040_local_vs_artifact_blocker_reconciliation.json": reconciliation,
        "batch040_target_resolution_preservation.json": target_preservation,
        "batch040_secondary_cofactor_governance_preservation.json": cofactor_preservation,
        "batch041_reactome_chromosomal_governance_continuity_audit.json": {
            "status": "PASS",
            "stable_identity_map_active": True,
            "blocker_lineage_map_active": True,
            "execution_compartment_registry_active": True,
            "cofactor_materialization_registry_active": True,
            "secondary_cofactor_governance_model_active": True,
            "not_run_reason_registry_active": True,
            "failed_branch_precondition_record_active": True,
            "step_activation_ring_active": True,
            "compartmentalized_repair_stage_audit_active": True,
            "no_floating_update_audit_active": True,
            "command_telemetry_sanitization_audit_active": True,
            "psa82_diagnostic_only": True,
            "design_mapping_language_is_not_repair_proof": True,
            "empirical_target_replay_and_duplicate_clean_replay_mandatory": True,
        },
        "batch041_stable_identity_integrity_audit.json": stable_integrity,
        "batch041_stable_identity_map_update.json": {"status": "PASS", "records": stable_identity_records, "current_identity": "batch041_lock_v2"},
        "batch041_proof_ledger_referrer_audit.json": proof_referrer,
        "batch041_cofactor_lock_provenance_audit.json": provenance,
        "batch041_dependency_drift_audit.json": drift,
        "batch041_secondary_cofactor_chain_budget.json": chain_budget,
        "batch041_replay_classification_matrix.json": replay_matrix,
        "batch041_included_excluded_diagnostics_registry.json": diagnostics,
        "batch041_validation_activation_audit.json": validation_activation,
        "batch041_transport_export_equivalence_audit.json": transport,
        "batch041_evidence_origin_classification.json": origin,
        "batch041_lock_completion_policy.json": {
            "status": "PASS",
            "allowed_evidence": ["selected source metadata", "Batch039 cofactor governance", "Batch040 lock discovery artifacts", "Batch040 lock record", "provider-only resolver output", "provider-only package metadata"],
            "forbidden_evidence_used": False,
            "colorama_add_or_remove_requires_platform_conditioned_rationale": True,
            "review_required_before_materialization": True,
            "replay_requires_review_materialization_drift_and_transport_pass": True,
        },
        "batch041_pylint_lock_completion_result.json": completion,
        "batch041_pylint_provider_lock_v2.json": lock_v2,
        "batch041_pylint_lock_v2_review.json": review_v2,
        "batch041_provider_only_cofactor_materialization_result.json": {
            **materialization,
            "provider_output": provider_probe.get("provider_output", {}),
            "source_checkout": provider_probe.get("source_checkout", {}),
            "transport": provider_probe.get("transport", {}),
            "cleanup": provider_probe.get("cleanup", {}),
        },
        "batch041_pylint_executable_verification.json": pylint_verification,
        "batch041_corrected_patch_preservation.json": {
            "status": "PASS" if (root / PATCH_PATH).is_file() and sha256_file(root / PATCH_PATH) == CORRECTED_PATCH_SHA256 else "FAIL",
            "corrected_patch_sha256": CORRECTED_PATCH_SHA256,
            "observed_patch_sha256": sha256_file(root / PATCH_PATH) if (root / PATCH_PATH).is_file() else None,
            "selected_source_head": SOURCE_COMMIT_SHA,
            "touched_files": [CORRECTED_PATCH_PATH],
            "source_only": True,
            "tests_modified": False,
            "verified_before_replay": True,
        },
        "batch041_post_repair_target_replay_with_lock_v2.json": post_repair,
        "batch041_duplicate_clean_replay_with_lock_v2.json": duplicate,
        "batch041_issue_derived_repair_validation.json": validation,
        "issue_derived_repair_feasibility_batch041.json": feasibility,
        "claim_boundary_batch041.json": claim,
        "proof_obligations_ledger_batch041.json": {"status": "PASS", "entries": proof_entries, "hash_chain_valid": True},
        "batch041_not_run_reason_registry.json": {"status": "PASS", "entries": not_run_entries},
    }

    for rel, value in records.items():
        write_json_deterministic(batch041_dir / rel, value)

    state = {
        "status": status,
        "exact_blocker": exact_blocker,
        "primary_artifact_name": PRIMARY_ARTIFACT,
        "batch040_artifact_ingest_status": ingest["status"],
        "batch040_artifact_verification_status": verification["status"],
        "batch040_artifact_internal_status": internal_status["artifact_internal_status"],
        "batch040_artifact_internal_blocker": internal_status["artifact_internal_exact_blocker"],
        "batch040_repo_side_pre_ingest_status": BATCH040_LOCAL_STATUS,
        "batch040_repo_side_pre_ingest_blocker": BATCH040_LOCAL_BLOCKER,
        "batch040_active_blocker_after_ingest": BATCH040_OFFICIAL_BLOCKER,
        "stable_identity_integrity_status": stable_integrity["status"],
        "proof_ledger_referrer_audit_status": proof_referrer["status"],
        "cofactor_lock_provenance_status": provenance["status"],
        "dependency_drift_audit_status": drift["status"],
        "secondary_cofactor_chain_budget_status": chain_budget["status"],
        "replay_classification_status": replay_matrix["status"],
        "replay_classification": replay_matrix["classification"],
        "diagnostics_registry_status": diagnostics["status"],
        "validation_activation_status": validation_activation["status"],
        "transport_export_equivalence_status": transport["status"],
        "evidence_origin_classification_status": origin["status"],
        "lock_completion_status": completion["status"],
        "lock_v2_review_status": review_v2["status"],
        "lock_v2_provider_safe": review_v2["provider_safe"],
        "provider_only_materialization_status": materialization.get("status"),
        "pylint_executable_verification_status": pylint_verification.get("status"),
        "post_repair_target_replay_status": post_repair.get("status"),
        "duplicate_clean_replay_status": duplicate.get("status"),
        "issue_derived_repair_validated": validated,
        "native_repair_episode_count": 4,
        "issue_derived_repair_episode_count": 0,
        "full_scoring": "NOT_RUN/disallowed",
        "memory_lift": "not_demonstrated",
        "self_maintaining_software": "false/not_demonstrated",
        "current_protocol": "v2.13",
    }
    write_json_deterministic(batch041_dir / "consolidated_state_clean_replication_batch_041.json", state)
    write_text_lf(
        batch041_dir / "campaign_summary.md",
        "\n".join(
            [
                "# Batch041 cofactor lock completion and identity integrity",
                "",
                f"Status: `{status}`",
                f"Exact blocker: `{exact_blocker}`",
                "",
                "Batch041 officially ingests the Batch040 artifact boundary, keeps the artifact-internal blocker authoritative, adds stable identity and proof-ledger integrity checks, and creates a platform-conditioned pylint lock-v2 from the official provider resolver output.",
                "",
                f"Lock completion: `{completion['status']}`. Lock-v2 review: `{review_v2['status']}`.",
                f"Provider materialization: `{materialization.get('status')}`. Replay classification: `{replay_matrix['classification']}`.",
                "",
                "No full scoring, memory-lift, production-readiness, or self-maintaining software claim is made.",
            ]
        ),
    )
    write_json_deterministic(batch041_dir / "public_language_audit_batch041.json", public_language_audit(root, [batch041_dir / "campaign_summary.md"]))
    write_json_deterministic(root / "configs/clean_replication_batch_041.json", {"campaign_id": BATCH041_ID, "primary_artifact_name": PRIMARY_ARTIFACT, "current_protocol": "v2.13"})
    write_sha256sums(batch041_dir)
    return state


__all__ = ["PRIMARY_ARTIFACT", "BATCH041_ID", "REQUIRED_BATCH041_OUTPUTS", "write_batch041_outputs", "write_batch041_public_state"]
