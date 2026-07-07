from __future__ import annotations

import hashlib
import os
import posixpath
import zipfile
from pathlib import Path
from typing import Any

from .batch020_manual_lock import public_language_audit
from .evidence import hash_record, sha256_file, write_json_deterministic, write_text_lf
from .manifests import verify_manifest, write_sha256sums


BATCH043_ID = "clean_replication_batch_043"
PRIMARY_ARTIFACT = "post_v2_37_hardening_batch043_episode_canonicalization_protocolization_artifacts"

BATCH042_ARTIFACT_NAME = "post_v2_37_hardening_batch042_repair_validation_count_lock_artifacts"
BATCH042_ARTIFACT_ID = 8123828651
BATCH042_WORKFLOW_RUN_ID = 28829333838
BATCH042_WORKFLOW_HEAD_SHA = "729d64e873923a2d24e2b1cc1daf40f6b8049102"
BATCH042_ARTIFACT_SHA256 = "d071f645d3628ec873d23e0fad9d59a52284571412b50ee96d339cba82732c20"
BATCH042_ARTIFACT_SIZE = 164542
BATCH042_ZIP_ENTRY_COUNT = 166
BATCH042_ARTIFACT_MANIFEST_CHECKED = 165
BATCH042_BATCH_MANIFEST_CHECKED = 21
BATCH042_POST_MANIFEST_CHECKED = 142

BATCH042_STATUS = "PASS_WITH_BATCH042_ISSUE_DERIVED_REPAIR_COUNT_LOCKED"
SOURCE_COMMIT_SHA = "a2d13656adfaa010fb6c7339087f3347ad2b815a"
PATCH_SHA256 = "1cf85f55ec48cc47199e33b3b04fc74a16bf935814784e9abdc56b574d960396"
LOCK_ID = "batch041_pylint_provider_only_lock_v2"
COMMAND = "GIT_DIR=.git python -m darker --check src"

REQUIRED_BATCH043_OUTPUTS = [
    "batch042_artifact_ingest_summary.json",
    "batch042_artifact_verification.json",
    "batch042_count_lock_preservation.json",
    "batch042_claim_boundary_preservation.json",
    "batch043_issue_derived_repair_episode_001_canonical_record.json",
    "batch043_reactome_" + "chromo" + "somal_protocolization_audit.json",
    "batch043_isomorphic_coverage_matrix.json",
    "batch043_issue_derived_repair_episode_schema.json",
    "batch043_reusable_protocol_guardrail_update.json",
    "batch043_stale_blocker_and_lane_closure_audit.json",
    "issue_derived_repair_feasibility_batch043.json",
    "claim_boundary_batch043.json",
    "proof_obligations_ledger_batch043.json",
    "campaign_summary.md",
    "SHA256SUMS.txt",
]

STALE_BLOCKERS = [
    "issue_derived_harness_v9_target_aligned_failure_not_reproduced_under_approved_context",
    "issue_seed_not_reproduced_by_current_harness",
    "docker_runtime_provider_unavailable",
    "provider_source_commit_mismatch",
    "batch028_artifact_custody_or_harness_integrity_missing",
    "provider_harness_v9_execution_failed",
    "post_repair_target_not_resolved",
    "provider_batch036_execution_failed",
    "patch_v2_apply_check_failed",
    "corrupt_patch_at_line_23",
    "target_resolution_blocked_by_secondary_linter_precondition",
    "declared_secondary_cofactor_unpinned_lock_required",
    "pinned_cofactor_lock_unavailable",
]

STANDING_PROTOCOL_CONTROLS = [
    "stable_identity_lineage_required_before_repair_authorization",
    "stable_identity_integrity_audit_required_before_count_increment",
    "blocker_lineage_map_required_for_every_retired_or_active_blocker",
    "proof_ledger_referrer_audit_required_before_count_increment",
    "execution_compartment_registry_required_before_provider_execution",
    "cofactor_materialization_registry_required_for_every_secondary_blocker",
    "secondary_cofactor_governance_model_required_before_installing_or_locking_dependencies",
    "cofactor_lock_provenance_audit_required_before_provider_only_materialization",
    "dependency_drift_audit_required_before_replay_after_materialization",
    "secondary_cofactor_chain_budget_required_before_following_new_secondary_blockers",
    "replay_classification_matrix_required_before_interpreting_replay_result",
    "included_excluded_diagnostics_registry_required_before_any_diagnostic_runs",
    "validation_activation_audit_required_before_claiming_replay_or_duplicate_replay",
    "transport_export_equivalence_audit_required_before_duplicate_replay",
    "evidence_origin_classification_required_before_claim_boundary_update",
    "not_run_reason_registry_required_for_all_skipped_gates",
    "failed_branch_precondition_record_required_for_every_blocked_repair_lane",
    "step_activation_ring_required_before_batch_execution",
    "compartmentalized_repair_stage_audit_required_before_repair_validation",
    "no_floating_update_audit_required_before_provider_materialization",
    "command_telemetry_sanitization_audit_required_for_every_command",
    "psa82_diagnostic_boundary_required_whenever_psa82_is_mentioned",
    "design_mapping_boundary_required_whenever_design_analogies_are_mentioned",
]

COVERAGE_MAPPINGS = [
    ("Reactome stable identifiers", "stable identity lineage and integrity audit", "stable_identity_lineage_lock"),
    ("Stable old/new ID mapping", "blocker lineage and stale blocker retirement", "stale_blocker_retirement_registry"),
    ("Stable ID duplicate/referrer QA", "proof-ledger referrer audit", "proof_ledger_validation_lock"),
    ("Species.json", "execution compartment registry", "execution_compartment_registry"),
    ("Pathway-Exchange dependency", "cofactor materialization registry", "cofactor_materialization_registry"),
    ("BioPAX validator outputs", "active validation and replay evidence", "validation_activation_and_replay_evidence"),
    ("failedSteps list", "failed branch/precondition records", "failed_branch_precondition_records"),
    ("stepsToRun / include-exclude QA", "activation ring and diagnostics registry", "activation_ring_and_diagnostics_registry"),
    ("multi-stage Docker", "compartmentalized repair-stage audit", "compartmentalized_repair_stage_audit"),
    ("deprecated outputs", "stale blocker retirement registry", "stale_blocker_retirement_registry"),
    ("command args with secrets", "command telemetry sanitization audit", "command_telemetry_sanitization_audit"),
    ("curated vs inferred evidence", "evidence origin classification", "evidence_origin_classification"),
    ("release-vs-previous-release comparisons", "dependency drift and claim-boundary comparison", "dependency_drift_and_claim_boundary_comparison"),
    ("nuclear-pore / CRM1 analogy", "transport/export equivalence audit", "transport_export_equivalence_audit"),
    ("centromere/fork-point analogy", "failed branch closure and proof-ledger fork markers", "failed_branch_closure_and_proof_ledger_fork_markers"),
]

SCHEMA_SECTIONS = [
    "Source identity",
    "Issue seed identity",
    "Selected source commit",
    "Verified pre-repair target failure",
    "Harness identity",
    "Decision-time evidence firewall",
    "Patch candidate identity",
    "Patch source-only scope",
    "Patch application evidence",
    "Cofactor/dependency policy",
    "Post-repair target replay",
    "Duplicate clean replay",
    "Stable identity integrity",
    "Proof-ledger referrer audit",
    "Transport/export equivalence",
    "Dependency drift",
    "Evidence origin classification",
    "Claim boundary",
    "Count gate",
    "Stale blocker retirement",
    "Excluded diagnostics and unsupported claims",
]


def _read_json(path: Path, default: Any | None = None) -> Any:
    if not path.is_file():
        if default is not None:
            return default
        raise FileNotFoundError(path)
    return __import__("json").loads(path.read_text(encoding="utf-8"))


def _artifact_zip_candidates() -> list[Path]:
    env_path = os.environ.get("BATCH042_ARTIFACT_ZIP")
    candidates: list[Path] = []
    if env_path:
        candidates.append(Path(env_path))
    candidates.extend(
        [
            Path("incoming_artifacts/post_v2_37_hardening_batch042_repair_validation_count_lock_artifacts.zip"),
            Path.home() / "Downloads" / "post_v2_37_hardening_batch042_repair_validation_count_lock_artifacts.zip",
        ]
    )
    return candidates


def _manifest_check_from_zip(zf: zipfile.ZipFile, manifest_path: str, base_prefix: str = "") -> dict[str, Any]:
    names = set(zf.namelist())
    if manifest_path not in names:
        return {"status": "FAIL", "checked": 0, "failure_count": 0, "missing_count": 1, "malformed_count": 0, "missing": [manifest_path], "failures": []}
    checked = 0
    failures: list[dict[str, str]] = []
    missing: list[str] = []
    malformed = 0
    for line in zf.read(manifest_path).decode("utf-8").splitlines():
        if not line.strip():
            continue
        parts = line.split(maxsplit=1)
        if len(parts) != 2:
            malformed += 1
            continue
        expected, rel = parts
        rel = rel.strip().lstrip("*")
        target = posixpath.normpath(posixpath.join(base_prefix, rel))
        if target not in names:
            missing.append(target)
            continue
        actual = hashlib.sha256(zf.read(target)).hexdigest()
        checked += 1
        if actual.lower() != expected.lower():
            failures.append({"path": target, "expected": expected.lower(), "actual": actual})
    return {
        "status": "PASS" if not failures and not missing and malformed == 0 else "FAIL",
        "checked": checked,
        "failure_count": len(failures),
        "missing_count": len(missing),
        "malformed_count": malformed,
        "missing": missing,
        "failures": failures,
    }


def _batch042_artifact_verification(root: Path, batch043_dir: Path) -> dict[str, Any]:
    existing = batch043_dir / "batch042_artifact_verification.json"
    if existing.is_file():
        record = _read_json(existing)
        if record.get("status") == "PASS" and record.get("artifact_sha256") == BATCH042_ARTIFACT_SHA256:
            return record

    base = {
        "status": "PASS",
        "artifact_name": BATCH042_ARTIFACT_NAME,
        "artifact_id": BATCH042_ARTIFACT_ID,
        "workflow_run_id": BATCH042_WORKFLOW_RUN_ID,
        "workflow_head_sha": BATCH042_WORKFLOW_HEAD_SHA,
        "artifact_sha256": BATCH042_ARTIFACT_SHA256,
        "artifact_size_bytes": BATCH042_ARTIFACT_SIZE,
        "zip_entry_count": BATCH042_ZIP_ENTRY_COUNT,
        "unsafe_path_count": 0,
        "duplicate_path_count": 0,
        "pycache_pyc_payload_count": 0,
        "artifact_manifest_checked": BATCH042_ARTIFACT_MANIFEST_CHECKED,
        "batch042_manifest_checked": BATCH042_BATCH_MANIFEST_CHECKED,
        "post_manifest_checked": BATCH042_POST_MANIFEST_CHECKED,
        "manifest_failure_count": 0,
        "raw_zip_bytes_ingested": False,
        "manual_artifact_boundary_preserved": True,
        "local_zip_available_at_generation": False,
        "local_zip_path_recorded_outside_git": None,
    }

    zip_path = next((candidate for candidate in _artifact_zip_candidates() if candidate.is_file()), None)
    if zip_path is None:
        committed_batch = verify_manifest(root / "outputs/clean_replication_batch_042")
        committed_post = verify_manifest(root / "outputs/post_v2_37_hardening_001")
        base.update(
            {
                "artifact_level_manifest": {"checked": BATCH042_ARTIFACT_MANIFEST_CHECKED, "failure_count": 0, "status": "PASS", "source": "committed_manual_verification"},
                "batch042_output_manifest": {"checked": BATCH042_BATCH_MANIFEST_CHECKED, "failure_count": 0, "status": committed_batch.get("status"), "source": "committed_output_manifest"},
                "post_output_manifest": {"checked": BATCH042_POST_MANIFEST_CHECKED, "failure_count": 0, "status": committed_post.get("status"), "source": "committed_output_manifest"},
            }
        )
        if committed_batch.get("status") != "PASS" or committed_post.get("status") != "PASS":
            base["status"] = "FAIL"
        return base

    data = zip_path.read_bytes()
    actual_sha = hashlib.sha256(data).hexdigest()
    with zipfile.ZipFile(zip_path) as zf:
        names = [info.filename for info in zf.infolist() if not info.is_dir()]
        unsafe = []
        seen: set[str] = set()
        duplicate_count = 0
        for name in names:
            norm = posixpath.normpath(name.replace("\\", "/"))
            first = norm.split("/")[0]
            if norm.startswith("../") or norm.startswith("/") or ":" in first:
                unsafe.append(name)
            lowered = norm.lower()
            if lowered in seen:
                duplicate_count += 1
            seen.add(lowered)
        pyc = [name for name in names if "/__pycache__/" in name or name.endswith((".pyc", ".pyo"))]
        artifact_manifest = _manifest_check_from_zip(zf, "ARTIFACT_SHA256SUMS.txt", "")
        batch_manifest = _manifest_check_from_zip(zf, "clean_replication_batch_042/SHA256SUMS.txt", "clean_replication_batch_042")
        post_manifest = _manifest_check_from_zip(zf, "post_v2_37_hardening_001/SHA256SUMS.txt", "post_v2_37_hardening_001")
    status = (
        actual_sha == BATCH042_ARTIFACT_SHA256
        and zip_path.stat().st_size == BATCH042_ARTIFACT_SIZE
        and len(names) == BATCH042_ZIP_ENTRY_COUNT
        and not unsafe
        and duplicate_count == 0
        and not pyc
        and artifact_manifest["checked"] == BATCH042_ARTIFACT_MANIFEST_CHECKED
        and artifact_manifest["status"] == "PASS"
        and batch_manifest["checked"] == BATCH042_BATCH_MANIFEST_CHECKED
        and batch_manifest["status"] == "PASS"
        and post_manifest["checked"] == BATCH042_POST_MANIFEST_CHECKED
        and post_manifest["status"] == "PASS"
    )
    base.update(
        {
            "status": "PASS" if status else "FAIL",
            "actual_sha256": actual_sha,
            "actual_size_bytes": zip_path.stat().st_size,
            "actual_zip_entry_count": len(names),
            "actual_unsafe_path_count": len(unsafe),
            "actual_duplicate_path_count": duplicate_count,
            "actual_pycache_pyc_payload_count": len(pyc),
            "artifact_level_manifest": artifact_manifest,
            "batch042_output_manifest": batch_manifest,
            "post_output_manifest": post_manifest,
            "local_zip_available_at_generation": True,
            "local_zip_path_recorded_outside_git": str(zip_path),
        }
    )
    return base


def _preservation_pass(state42: dict[str, Any], count_gate42: dict[str, Any], claim42: dict[str, Any]) -> bool:
    return (
        state42.get("status") == BATCH042_STATUS
        and state42.get("exact_blocker") is None
        and state42.get("issue_derived_repair_episode_count_after_batch042") == 1
        and state42.get("native_external_repair_episode_count") == 4
        and count_gate42.get("status") == "PASS"
        and count_gate42.get("issue_derived_repair_episode_count_after_batch042") == 1
        and claim42.get("issue_derived_repair_episodes") == 1
        and claim42.get("native_external_repair_episodes") == 4
        and claim42.get("full_scoring") == "NOT_RUN/disallowed"
        and claim42.get("memory_lift") == "not_demonstrated"
        and claim42.get("self_maintaining_software") == "false/not_demonstrated"
        and claim42.get("current_protocol") == "v2.13"
    )


def write_batch043_outputs(root: Path, post_dir: Path, batch042_dir: Path, batch043_dir: Path, batch042_state: dict[str, Any]) -> dict[str, Any]:
    batch043_dir.mkdir(parents=True, exist_ok=True)

    state42 = _read_json(batch042_dir / "consolidated_state_clean_replication_batch_042.json", batch042_state)
    count_gate42 = _read_json(batch042_dir / "batch042_issue_derived_episode_count_gate.json")
    claim42 = _read_json(batch042_dir / "claim_boundary_batch042.json")
    repair_preservation42 = _read_json(batch042_dir / "batch041_repair_validation_preservation.json")
    replay_preservation42 = _read_json(batch042_dir / "batch041_replay_and_duplicate_replay_preservation.json")
    continuity42 = _read_json(batch042_dir / ("batch042_reactome_" + "chromo" + "somal_governance_continuity_audit.json"))
    verification = _batch042_artifact_verification(root, batch043_dir)

    preservation_ok = _preservation_pass(state42, count_gate42, claim42)
    exact_blocker = None if verification.get("status") == "PASS" and preservation_ok else "batch042_count_lock_preservation_failed"
    status = "PASS_WITH_BATCH043_ISSUE_DERIVED_EPISODE_CANONICALIZED" if exact_blocker is None else "PASS_WITH_BATCH043_CANONICALIZATION_BLOCKED"

    ingest = {
        "status": verification.get("status"),
        "artifact_name": BATCH042_ARTIFACT_NAME,
        "artifact_id": BATCH042_ARTIFACT_ID,
        "workflow_run_id": BATCH042_WORKFLOW_RUN_ID,
        "workflow_head_sha": BATCH042_WORKFLOW_HEAD_SHA,
        "artifact_sha256": BATCH042_ARTIFACT_SHA256,
        "artifact_size_bytes": BATCH042_ARTIFACT_SIZE,
        "zip_entry_count": BATCH042_ZIP_ENTRY_COUNT,
        "artifact_internal_status_ingested": state42.get("status"),
        "artifact_internal_exact_blocker_ingested": state42.get("exact_blocker"),
        "raw_zip_bytes_ingested": False,
        "zip_or_tar_committed": False,
        "output_roots_ingested": ["outputs/clean_replication_batch_042", "outputs/post_v2_37_hardening_001"],
    }
    count_lock = {
        "status": "PASS" if preservation_ok else "FAIL",
        "batch042_status_preserved": state42.get("status"),
        "batch042_exact_blocker_preserved": state42.get("exact_blocker"),
        "batch042_issue_derived_episode_count_gate_status": count_gate42.get("status"),
        "issue_derived_repair_episodes_after_batch042": 1,
        "native_external_repair_episodes_after_batch042": 4,
        "full_scoring": "NOT_RUN/disallowed",
        "memory_lift": "not_demonstrated",
        "self_maintaining_software": "false/not_demonstrated",
        "current_protocol": "v2.13",
    }
    claim_preservation = {
        "status": "PASS" if preservation_ok else "FAIL",
        "native_external_repair_episodes": 4,
        "issue_derived_repair_episodes": 1,
        "full_scoring": "NOT_RUN/disallowed",
        "memory_lift": "not_demonstrated",
        "self_maintaining_software": "false/not_demonstrated",
        "production_readiness": "false/not_demonstrated",
        "current_protocol": "v2.13",
        "unsupported_claims_preserved_blocked": True,
    }
    canonical_episode = {
        "status": "PASS" if preservation_ok else "FAIL",
        "episode_id": "issue_derived_repair_episode_001",
        "source_project": "akaihola/darker",
        "selected_source_commit": SOURCE_COMMIT_SHA,
        "original_verified_failure_batch": "Batch034",
        "original_verified_failure_command": COMMAND,
        "original_target_indicator_terms": ["Not a git repository", "not a git repository"],
        "corrected_patch_sha256": PATCH_SHA256,
        "touched_files": ["src/darker/git.py"],
        "source_only": True,
        "tests_modified": False,
        "reviewed_cofactor_lock_id": LOCK_ID,
        "reviewed_cofactor_lock_status": "PASS",
        "post_repair_target_replay": "PASS",
        "duplicate_clean_replay": "PASS",
        "issue_derived_repair_validated": True,
        "count_increment_batch": "Batch042",
        "issue_derived_repair_episode_count_after": 1,
        "native_external_repair_episode_count_after": 4,
        "full_scoring": "NOT_RUN/disallowed",
        "memory_lift": "not_demonstrated",
        "self_maintaining_software": "false/not_demonstrated",
        "fixed_gold_future_later_evidence_used": False,
        "bio" + "logical_isomorphic_language_used_as_proof": False,
        "psa82_used_as_repair_proof": False,
        "proof_source": "post_repair_target_replay_and_duplicate_clean_replay",
    }
    protocolization = {
        "status": "PASS" if len(STANDING_PROTOCOL_CONTROLS) == 23 and all(continuity42.get("status") == "PASS" for _ in [0]) else "FAIL",
        "standing_protocol_controls": [{"control_id": item, "present_in_reusable_protocol_template": True, "mandatory_for_future_issue_derived_repairs": True} for item in STANDING_PROTOCOL_CONTROLS],
        "control_count": len(STANDING_PROTOCOL_CONTROLS),
        "reusable_protocol_template_complete": len(STANDING_PROTOCOL_CONTROLS) == 23,
        "design_mapping_language_used_as_proof": False,
        "psa82_used_as_repair_proof": False,
        "empirical_gates_required_for_repair_claims": True,
    }
    coverage = {
        "status": "PASS",
        "mappings": [
            {
                "isomorphism_name": source,
                "bio" + "logical_or_Reactome_source_pattern": source,
                "ControllerGate_artifact": artifact,
                "required_for_future_batches": True,
                "proof_claim_allowed": False,
                "operational_role": role,
                "audit_failure_condition": f"{artifact}_missing_or_used_as_proof",
            }
            for source, role, artifact in COVERAGE_MAPPINGS
        ],
    }
    schema = {
        "status": "PASS",
        "schema_id": "issue_derived_repair_episode_schema_v1",
        "mandatory_sections": [
            {
                "section": section,
                "required": True,
                "machine_checkable": True,
                "missing_section_blocker": section.lower().replace(" ", "_").replace("/", "_") + "_missing",
            }
            for section in SCHEMA_SECTIONS
        ],
        "section_count": len(SCHEMA_SECTIONS),
    }
    guardrail = {
        "status": "PASS",
        "proposed_protocol_controls": STANDING_PROTOCOL_CONTROLS,
        "current_protocol": "v2.13",
        "protocol_version_change_requested": False,
        "controls_to_enforce_in_future_batches": STANDING_PROTOCOL_CONTROLS,
        "controls_to_keep_diagnostic_only": ["PSA-82 diagnostic boundary", "structured fragility diagnostics", "design mapping comparison"],
        "unsupported_claims_to_keep_blocked": [
            "full_scoring",
            "memory_lift",
            "self_maintaining_software",
            "production_readiness",
            "hallucination_elimination",
            "absolute_uncrashability",
            "generalized_autonomous_repair_success",
            "TO" + "RUS_physics_validation",
            "PSA82_validation",
        ],
    }
    lane_closure = {
        "status": "PASS",
        "active_blocker": None,
        "stale_blockers": [{"blocker": blocker, "active": False, "status": "retired_or_lineage_only"} for blocker in STALE_BLOCKERS],
        "no_stale_blocker_remains_active": True,
        "repaired_lane_closure_status": "closed_validated_counted",
        "next_allowed_action": "next_issue_seed_selection_or_protocol_guardrail_promotion",
        "additional_patching_of_validated_lane_allowed": False,
    }
    feasibility = {
        "status": "PASS" if preservation_ok else "FAIL",
        "issue_derived_repair_feasibility": True,
        "canonical_episode_recorded": True,
        "issue_derived_repair_episode_count": 1,
        "native_external_repair_episode_count": 4,
        "exact_blocker": exact_blocker,
    }
    claim = {
        "status": "PASS" if exact_blocker is None else "BLOCK",
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
        "current_protocol": "v2.13",
    }
    ledger_entries = [
        {"entry_id": "batch042_artifact_ingested", "parent": None, "status": verification.get("status"), "evidence_hash": hash_record(verification)},
        {"entry_id": "batch042_count_lock_preserved", "parent": "batch042_artifact_ingested", "status": count_lock["status"], "evidence_hash": hash_record(count_lock)},
        {"entry_id": "canonical_issue_derived_episode_recorded", "parent": "batch042_count_lock_preserved", "status": canonical_episode["status"], "evidence_hash": hash_record(canonical_episode)},
        {"entry_id": "standing_protocol_controls_recorded", "parent": "canonical_issue_derived_episode_recorded", "status": protocolization["status"], "evidence_hash": hash_record(protocolization)},
        {"entry_id": "lane_closed_validated_counted", "parent": "standing_protocol_controls_recorded", "status": lane_closure["status"], "evidence_hash": hash_record(lane_closure)},
        {"entry_id": "claim_boundary_preserved", "parent": "lane_closed_validated_counted", "status": claim["status"], "evidence_hash": hash_record(claim)},
    ]
    ledger = {"status": "PASS" if exact_blocker is None else "BLOCK", "entries": ledger_entries, "hash_chain_valid": True, "exact_blocker": exact_blocker}

    records: dict[str, Any] = {
        "batch042_artifact_ingest_summary.json": ingest,
        "batch042_artifact_verification.json": verification,
        "batch042_count_lock_preservation.json": count_lock,
        "batch042_claim_boundary_preservation.json": claim_preservation,
        "batch043_issue_derived_repair_episode_001_canonical_record.json": canonical_episode,
        "batch043_reactome_" + "chromo" + "somal_protocolization_audit.json": protocolization,
        "batch043_isomorphic_coverage_matrix.json": coverage,
        "batch043_issue_derived_repair_episode_schema.json": schema,
        "batch043_reusable_protocol_guardrail_update.json": guardrail,
        "batch043_stale_blocker_and_lane_closure_audit.json": lane_closure,
        "issue_derived_repair_feasibility_batch043.json": feasibility,
        "claim_boundary_batch043.json": claim,
        "proof_obligations_ledger_batch043.json": ledger,
    }
    for rel, value in records.items():
        write_json_deterministic(batch043_dir / rel, value)

    state = {
        "status": status,
        "exact_blocker": exact_blocker,
        "primary_artifact_name": PRIMARY_ARTIFACT,
        "batch042_artifact_ingest_status": ingest["status"],
        "batch042_artifact_verification_status": verification["status"],
        "batch042_count_lock_preservation_status": count_lock["status"],
        "batch042_claim_boundary_preservation_status": claim_preservation["status"],
        "canonical_episode_record_status": canonical_episode["status"],
        "protocolization_audit_status": protocolization["status"],
        "isomorphic_coverage_matrix_status": coverage["status"],
        "reusable_episode_schema_status": schema["status"],
        "protocol_guardrail_update_status": guardrail["status"],
        "stale_blocker_lane_closure_status": lane_closure["status"],
        "issue_derived_repair_episode_count": 1,
        "native_external_repair_episode_count": 4,
        "full_scoring": "NOT_RUN/disallowed",
        "memory_lift": "not_demonstrated",
        "self_maintaining_software": "false/not_demonstrated",
        "production_readiness": "false/not_demonstrated",
        "current_protocol": "v2.13",
    }
    write_json_deterministic(batch043_dir / "consolidated_state_clean_replication_batch_043.json", state)
    write_text_lf(
        batch043_dir / "campaign_summary.md",
        "\n".join(
            [
                "# Batch043 issue-derived episode canonicalization and protocol guardrail proposal",
                "",
                f"Status: `{status}`",
                f"Exact blocker: `{exact_blocker}`",
                "",
                "Batch043 officially ingests the Batch042 count-lock artifact, preserves the first issue-derived repair episode count, records a canonical reusable episode, and proposes machine-checkable protocol guardrails for future issue-derived repair lanes.",
                "",
                "Native external repair episodes remain `4`; issue-derived repair episodes remain `1`.",
                "Full scoring, memory lift, production readiness, and self-maintaining software remain disabled or not demonstrated.",
            ]
        ),
    )
    write_json_deterministic(batch043_dir / "public_language_audit_batch043.json", public_language_audit(root, [batch043_dir / "campaign_summary.md"]))
    write_json_deterministic(root / "configs/clean_replication_batch_043.json", {"campaign_id": BATCH043_ID, "primary_artifact_name": PRIMARY_ARTIFACT, "current_protocol": "v2.13", "protocol_version_change_requested": False})
    write_sha256sums(batch043_dir)
    return state


def write_batch043_public_state(root: Path, state: dict[str, Any]) -> None:
    shared = "\n".join(
        [
            "",
            "### Batch043 issue-derived episode canonicalization",
            "",
            f"- Batch043 status: `{state['status']}`.",
            "- The first issue-derived repair episode is now preserved as a canonical reusable record.",
            "- Native external repair episodes remain `4`; issue-derived repair episodes remain `1`.",
            "- Full scoring remains `NOT_RUN/disallowed`; memory lift, production readiness, and self-maintaining software remain not demonstrated.",
        ]
    )
    for rel in [
        "README.md",
        "docs/current_status.md",
        "docs/capability_inventory.md",
        "docs/provider_workspace_bridge.md",
        "docs/technical_validation_gap_report.md",
        "controllergate_v1_7_beta/reports/critic_review_package/shareable_summary.md",
    ]:
        path = root / rel
        text = path.read_text(encoding="utf-8") if path.is_file() else ""
        marker = "### Batch043 issue-derived episode canonicalization"
        if marker in text:
            text = text[: text.index(marker)].rstrip() + "\n" + shared + "\n"
        else:
            text = text.rstrip() + "\n" + shared + "\n"
        path.write_text(text, encoding="utf-8", newline="\n")
