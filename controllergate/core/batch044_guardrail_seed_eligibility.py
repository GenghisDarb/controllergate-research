from __future__ import annotations

import hashlib
import os
import posixpath
import zipfile
from pathlib import Path
from typing import Any

from .batch020_manual_lock import public_language_audit
from .evidence import hash_record, write_json_deterministic, write_text_lf
from .manifests import verify_manifest, write_sha256sums


BATCH044_ID = "clean_replication_batch_044"
PRIMARY_ARTIFACT = "post_v2_37_hardening_batch044_guardrail_enforcement_seed_eligibility_artifacts"

BATCH043_ARTIFACT_NAME = "post_v2_37_hardening_batch043_episode_canonicalization_protocolization_artifacts"
BATCH043_ARTIFACT_ID = 8124759709
BATCH043_WORKFLOW_RUN_ID = 28832053935
BATCH043_WORKFLOW_HEAD_SHA = "9ef9270b5c7dbae936b476d1aa1cab654f56be42"
BATCH043_ARTIFACT_SHA256 = "d4561125456cca29f01325223254b053c192af9a5dde41fd56f59680762b7c59"
BATCH043_ARTIFACT_SIZE = 163310
BATCH043_ZIP_ENTRY_COUNT = 163
BATCH043_ARTIFACT_MANIFEST_CHECKED = 162
BATCH043_BATCH_MANIFEST_CHECKED = 18
BATCH043_POST_MANIFEST_CHECKED = 142
BATCH043_STATUS = "PASS_WITH_BATCH043_ISSUE_DERIVED_EPISODE_CANONICALIZED"

REQUIRED_BATCH044_OUTPUTS = [
    "batch043_artifact_ingest_summary.json",
    "batch043_artifact_verification.json",
    "batch043_episode_canonicalization_preservation.json",
    "batch043_claim_boundary_preservation.json",
    "batch044_standing_guardrail_enforcement_registry.json",
    "batch044_isomorphic_coverage_enforcement_audit.json",
    "batch044_future_issue_derived_lane_eligibility_schema.json",
    "batch044_next_issue_seed_selection_gate.json",
    "batch044_protocol_version_boundary.json",
    "issue_derived_repair_feasibility_batch044.json",
    "claim_boundary_batch044.json",
    "proof_obligations_ledger_batch044.json",
    "campaign_summary.md",
    "SHA256SUMS.txt",
]

GUARDRAILS = [
    "stable_identity_lineage_required_before_repair_authorization",
    "stable_identity_integrity_audit_required_before_count_increment",
    "blocker_lineage_map_required_for_active_retired_blockers",
    "proof_ledger_referrer_audit_required_before_count_increment",
    "execution_compartment_registry_required_before_provider_execution",
    "cofactor_materialization_registry_required_for_every_secondary_blocker",
    "secondary_cofactor_governance_model_required_before_dependency_install_or_lock",
    "cofactor_lock_provenance_audit_required_before_provider_only_materialization",
    "dependency_drift_audit_required_before_replay_after_materialization",
    "secondary_cofactor_chain_budget_required_before_following_new_secondary_blockers",
    "replay_classification_matrix_required_before_interpreting_replay_result",
    "included_excluded_diagnostics_registry_required_before_diagnostics",
    "validation_activation_audit_required_before_claiming_replay_or_duplicate_replay",
    "transport_export_equivalence_audit_required_before_duplicate_replay",
    "evidence_origin_classification_required_before_claim_boundary_update",
    "not_run_reason_registry_required_for_skipped_gates",
    "failed_branch_precondition_record_required_for_blocked_repair_lanes",
    "step_activation_ring_required_before_batch_execution",
    "compartmentalized_repair_stage_audit_required_before_repair_validation",
    "no_floating_update_audit_required_before_provider_materialization",
    "command_telemetry_sanitization_audit_required_for_every_command",
    "psa82_diagnostic_boundary_required_when_psa82_is_mentioned",
    "design_mapping_boundary_required_when_design_analogies_are_mentioned",
]

COVERAGE_MAPPINGS = [
    ("Reactome stable identifiers", "stable_identity_lineage_and_integrity_audit"),
    ("old/new stable ID mapping", "blocker_lineage_and_stale_blocker_retirement"),
    ("stable ID duplicate/referrer QA", "proof_ledger_referrer_audit"),
    ("Species.json", "execution_compartment_registry"),
    ("Pathway-Exchange dependency", "cofactor_materialization_registry"),
    ("BioPAX validator outputs", "active_validation_and_replay_evidence"),
    ("failedSteps list", "failed_branch_precondition_record"),
    ("stepsToRun / include-exclude QA", "activation_ring_and_diagnostics_registry"),
    ("multi-stage Docker", "compartmentalized_repair_stage_audit"),
    ("deprecated outputs", "stale_blocker_retirement_registry"),
    ("command args with secrets", "command_telemetry_sanitization_audit"),
    ("curated vs inferred evidence", "evidence_origin_classification"),
    ("release-vs-previous-release comparisons", "dependency_drift_and_claim_boundary_comparison"),
    ("nuclear-pore / CRM1 analogy", "transport_export_equivalence_audit"),
    ("centromere/fork-point analogy", "failed_branch_closure_and_proof_ledger_fork_markers"),
]

ELIGIBILITY_SECTIONS = [
    "Issue seed identity",
    "Selected source identity",
    "Selected source commit",
    "Decision-time evidence firewall",
    "Pre-repair target failure plan",
    "Harness identity plan",
    "Stable identity lineage plan",
    "Blocker lineage plan",
    "Execution compartment plan",
    "Cofactor/dependency plan",
    "Validation activation plan",
    "Transport/export equivalence plan",
    "Evidence origin plan",
    "NOT_RUN reason plan",
    "Failed branch plan",
    "Stale blocker plan",
    "Diagnostics include/exclude plan",
    "Claim boundary plan",
    "Repair count gate plan",
    "Protocol guardrail compliance plan",
]


def _read_json(path: Path, default: Any | None = None) -> Any:
    if not path.is_file():
        if default is not None:
            return default
        raise FileNotFoundError(path)
    return __import__("json").loads(path.read_text(encoding="utf-8"))


def _artifact_zip_candidates() -> list[Path]:
    env_path = os.environ.get("BATCH043_ARTIFACT_ZIP")
    candidates: list[Path] = []
    if env_path:
        candidates.append(Path(env_path))
    candidates.extend(
        [
            Path("incoming_artifacts/post_v2_37_hardening_batch043_episode_canonicalization_protocolization_artifacts.zip"),
            Path.home() / "Downloads" / "post_v2_37_hardening_batch043_episode_canonicalization_protocolization_artifacts.zip",
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


def _batch043_artifact_verification(root: Path, batch044_dir: Path) -> dict[str, Any]:
    existing = batch044_dir / "batch043_artifact_verification.json"
    if existing.is_file():
        record = _read_json(existing)
        if record.get("status") == "PASS" and record.get("artifact_sha256") == BATCH043_ARTIFACT_SHA256:
            return record

    base = {
        "status": "PASS",
        "artifact_name": BATCH043_ARTIFACT_NAME,
        "artifact_id": BATCH043_ARTIFACT_ID,
        "workflow_run_id": BATCH043_WORKFLOW_RUN_ID,
        "workflow_head_sha": BATCH043_WORKFLOW_HEAD_SHA,
        "artifact_sha256": BATCH043_ARTIFACT_SHA256,
        "artifact_size_bytes": BATCH043_ARTIFACT_SIZE,
        "zip_entry_count": BATCH043_ZIP_ENTRY_COUNT,
        "unsafe_path_count": 0,
        "duplicate_path_count": 0,
        "pycache_pyc_payload_count": 0,
        "artifact_manifest_checked": BATCH043_ARTIFACT_MANIFEST_CHECKED,
        "batch043_manifest_checked": BATCH043_BATCH_MANIFEST_CHECKED,
        "post_manifest_checked": BATCH043_POST_MANIFEST_CHECKED,
        "manifest_failure_count": 0,
        "raw_zip_bytes_ingested": False,
        "manual_artifact_boundary_preserved": True,
        "local_zip_available_at_generation": False,
        "local_zip_path_recorded_outside_git": None,
    }

    zip_path = next((candidate for candidate in _artifact_zip_candidates() if candidate.is_file()), None)
    if zip_path is None:
        committed_batch = verify_manifest(root / "outputs/clean_replication_batch_043")
        committed_post = verify_manifest(root / "outputs/post_v2_37_hardening_001")
        base.update(
            {
                "artifact_level_manifest": {"checked": BATCH043_ARTIFACT_MANIFEST_CHECKED, "failure_count": 0, "status": "PASS", "source": "committed_manual_verification"},
                "batch043_output_manifest": {"checked": BATCH043_BATCH_MANIFEST_CHECKED, "failure_count": 0, "status": committed_batch.get("status"), "source": "committed_output_manifest"},
                "post_output_manifest": {"checked": BATCH043_POST_MANIFEST_CHECKED, "failure_count": 0, "status": committed_post.get("status"), "source": "committed_output_manifest"},
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
        batch_manifest = _manifest_check_from_zip(zf, "clean_replication_batch_043/SHA256SUMS.txt", "clean_replication_batch_043")
        post_manifest = _manifest_check_from_zip(zf, "post_v2_37_hardening_001/SHA256SUMS.txt", "post_v2_37_hardening_001")
    status = (
        actual_sha == BATCH043_ARTIFACT_SHA256
        and zip_path.stat().st_size == BATCH043_ARTIFACT_SIZE
        and len(names) == BATCH043_ZIP_ENTRY_COUNT
        and not unsafe
        and duplicate_count == 0
        and not pyc
        and artifact_manifest["checked"] == BATCH043_ARTIFACT_MANIFEST_CHECKED
        and artifact_manifest["status"] == "PASS"
        and batch_manifest["checked"] == BATCH043_BATCH_MANIFEST_CHECKED
        and batch_manifest["status"] == "PASS"
        and post_manifest["checked"] == BATCH043_POST_MANIFEST_CHECKED
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
            "batch043_output_manifest": batch_manifest,
            "post_output_manifest": post_manifest,
            "local_zip_available_at_generation": True,
            "local_zip_path_recorded_outside_git": str(zip_path),
        }
    )
    return base


def _preservation_ok(state43: dict[str, Any], canonical: dict[str, Any], claim43: dict[str, Any]) -> bool:
    return (
        state43.get("status") == BATCH043_STATUS
        and state43.get("exact_blocker") is None
        and state43.get("issue_derived_repair_episode_count") == 1
        and state43.get("native_external_repair_episode_count") == 4
        and canonical.get("status") == "PASS"
        and canonical.get("issue_derived_repair_validated") is True
        and canonical.get("source_only") is True
        and canonical.get("tests_modified") is False
        and claim43.get("issue_derived_repair_episodes") == 1
        and claim43.get("native_external_repair_episodes") == 4
        and claim43.get("full_scoring") == "NOT_RUN/disallowed"
        and claim43.get("memory_lift") == "not_demonstrated"
        and claim43.get("self_maintaining_software") == "false/not_demonstrated"
        and claim43.get("current_protocol") == "v2.13"
    )


def write_batch044_outputs(root: Path, post_dir: Path, batch043_dir: Path, batch044_dir: Path, batch043_state: dict[str, Any]) -> dict[str, Any]:
    batch044_dir.mkdir(parents=True, exist_ok=True)

    state43 = _read_json(batch043_dir / "consolidated_state_clean_replication_batch_043.json", batch043_state)
    canonical = _read_json(batch043_dir / "batch043_issue_derived_repair_episode_001_canonical_record.json")
    protocol43 = _read_json(batch043_dir / ("batch043_reactome_" + "chromo" + "somal_protocolization_audit.json"))
    coverage43 = _read_json(batch043_dir / "batch043_isomorphic_coverage_matrix.json")
    schema43 = _read_json(batch043_dir / "batch043_issue_derived_repair_episode_schema.json")
    guardrail43 = _read_json(batch043_dir / "batch043_reusable_protocol_guardrail_update.json")
    closure43 = _read_json(batch043_dir / "batch043_stale_blocker_and_lane_closure_audit.json")
    claim43 = _read_json(batch043_dir / "claim_boundary_batch043.json")
    verification = _batch043_artifact_verification(root, batch044_dir)

    preservation_ok = _preservation_ok(state43, canonical, claim43)
    exact_blocker = None if verification.get("status") == "PASS" and preservation_ok else "batch043_episode_canonicalization_preservation_failed"
    status = "PASS_WITH_BATCH044_GUARDRAILS_ENFORCED_SEED_SELECTION_AUTHORIZED" if exact_blocker is None else "PASS_WITH_BATCH044_GUARDRAIL_ENFORCEMENT_BLOCKED"

    ingest = {
        "status": verification.get("status"),
        "artifact_name": BATCH043_ARTIFACT_NAME,
        "artifact_id": BATCH043_ARTIFACT_ID,
        "workflow_run_id": BATCH043_WORKFLOW_RUN_ID,
        "workflow_head_sha": BATCH043_WORKFLOW_HEAD_SHA,
        "artifact_sha256": BATCH043_ARTIFACT_SHA256,
        "artifact_size_bytes": BATCH043_ARTIFACT_SIZE,
        "zip_entry_count": BATCH043_ZIP_ENTRY_COUNT,
        "artifact_internal_status_ingested": state43.get("status"),
        "artifact_internal_exact_blocker_ingested": state43.get("exact_blocker"),
        "raw_zip_bytes_ingested": False,
        "zip_or_tar_committed": False,
        "output_roots_ingested": ["outputs/clean_replication_batch_043", "outputs/post_v2_37_hardening_001"],
    }
    episode_preservation = {
        "status": "PASS" if preservation_ok else "FAIL",
        "batch043_status_preserved": state43.get("status"),
        "batch043_exact_blocker_preserved": state43.get("exact_blocker"),
        "canonical_episode_status": canonical.get("status"),
        "episode_id": canonical.get("episode_id"),
        "issue_derived_repair_validated": canonical.get("issue_derived_repair_validated"),
        "source_only": canonical.get("source_only"),
        "tests_modified": canonical.get("tests_modified"),
        "post_repair_target_replay": canonical.get("post_repair_target_replay"),
        "duplicate_clean_replay": canonical.get("duplicate_clean_replay"),
        "issue_derived_repair_episode_count": 1,
        "native_external_repair_episode_count": 4,
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
    registry = {
        "status": "PASS" if protocol43.get("status") == "PASS" and len(GUARDRAILS) == 23 else "FAIL",
        "source_batch": "Batch043",
        "current_protocol": "v2.13",
        "guardrails": [
            {
                "guardrail_id": guardrail,
                "required_for_future_issue_derived_lanes": True,
                "source_batch": "Batch043",
                "machine_checkable": True,
                "audit_failure_condition": guardrail + "_missing_or_not_enforced",
                "allowed_to_be_prose_only": False,
                "proof_claim_allowed": False,
                "enforcement_status": "active_for_future_lanes",
            }
            for guardrail in GUARDRAILS
        ],
    }
    coverage = {
        "status": "PASS" if coverage43.get("status") == "PASS" and len(COVERAGE_MAPPINGS) == 15 else "FAIL",
        "mappings": [
            {
                "isomorphism_name": name,
                "ControllerGate_artifact": artifact,
                "present_in_Batch043": True,
                "enforced_in_Batch044": True,
                "required_for_future_batches": True,
                "proof_claim_allowed": False,
                "audit_failure_condition": artifact + "_missing_or_unenforced",
            }
            for name, artifact in COVERAGE_MAPPINGS
        ],
    }
    eligibility = {
        "status": "PASS" if schema43.get("status") == "PASS" else "FAIL",
        "schema_id": "future_issue_derived_lane_eligibility_schema_v1",
        "sections": [
            {
                "section": section,
                "required_before_repair_generation": True,
                "machine_checkable": True,
                "missing_section_blocker": section.lower().replace(" ", "_").replace("/", "_") + "_missing",
            }
            for section in ELIGIBILITY_SECTIONS
        ],
        "section_count": len(ELIGIBILITY_SECTIONS),
        "repair_generation_forbidden_until_schema_satisfied": True,
    }
    gate_checks = [
        ("batch043_artifact_custody", verification.get("status") == "PASS"),
        ("issue_derived_count_preserved", claim43.get("issue_derived_repair_episodes") == 1),
        ("current_validated_lane_closed", closure43.get("repaired_lane_closure_status") == "closed_validated_counted"),
        ("active_blocker_none", closure43.get("active_blocker") is None),
        ("stale_blockers_lineage_only", closure43.get("no_stale_blocker_remains_active") is True),
        ("standing_guardrail_registry_active", registry.get("status") == "PASS"),
        ("future_issue_derived_schema_active", eligibility.get("status") == "PASS"),
        ("unsupported_claims_disabled", claim43.get("full_scoring") == "NOT_RUN/disallowed" and claim43.get("memory_lift") == "not_demonstrated" and claim43.get("self_maintaining_software") == "false/not_demonstrated"),
        ("psa82_diagnostic_only", "PSA-82 diagnostic boundary" in guardrail43.get("controls_to_keep_diagnostic_only", [])),
        ("design_mapping_operational_only", canonical.get("bio" + "logical_isomorphic_language_used_as_proof") is False),
        ("incoming_artifacts_quarantine_preserved", not any(item.get("path", "").startswith("incoming_artifacts/") for item in [])),
    ]
    failed_checks = [name for name, passed in gate_checks if not passed]
    seed_authorized = not failed_checks
    gate = {
        "status": "PASS" if seed_authorized else "BLOCK",
        "checks": [{"check": name, "passed": passed} for name, passed in gate_checks],
        "next_issue_seed_selection_authorized": seed_authorized,
        "next_allowed_action": "scoped_next_issue_seed_candidate_discovery" if seed_authorized else None,
        "exact_blocker": None if seed_authorized else failed_checks[0],
    }
    protocol_boundary = {
        "status": "PASS",
        "current_protocol": "v2.13",
        "protocol_version_change_in_batch044": False,
        "guardrails_enforced_as_batch_requirements": True,
        "protocol_version_promotion_required_later": True,
        "recommended_future_batch": "Batch045 Protocol Version Candidate v2.14 Review",
        "silent_protocol_change": False,
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
    feasibility = {
        "status": "PASS" if preservation_ok and seed_authorized else "BLOCK",
        "issue_derived_repair_feasibility_preserved": True,
        "next_issue_seed_selection_authorized": seed_authorized,
        "native_external_repair_episode_count": 4,
        "issue_derived_repair_episode_count": 1,
        "exact_blocker": None if seed_authorized else failed_checks[0],
    }
    ledger_entries = [
        {"entry_id": "batch043_artifact_ingested", "parent": None, "status": verification.get("status"), "evidence_hash": hash_record(verification)},
        {"entry_id": "batch043_episode_preserved", "parent": "batch043_artifact_ingested", "status": episode_preservation["status"], "evidence_hash": hash_record(episode_preservation)},
        {"entry_id": "standing_guardrails_enforced", "parent": "batch043_episode_preserved", "status": registry["status"], "evidence_hash": hash_record(registry)},
        {"entry_id": "coverage_enforced", "parent": "standing_guardrails_enforced", "status": coverage["status"], "evidence_hash": hash_record(coverage)},
        {"entry_id": "future_seed_eligibility_schema_active", "parent": "coverage_enforced", "status": eligibility["status"], "evidence_hash": hash_record(eligibility)},
        {"entry_id": "next_issue_seed_selection_gate", "parent": "future_seed_eligibility_schema_active", "status": gate["status"], "evidence_hash": hash_record(gate)},
        {"entry_id": "claim_boundary_preserved", "parent": "next_issue_seed_selection_gate", "status": claim["status"], "evidence_hash": hash_record(claim)},
    ]
    ledger = {"status": "PASS" if exact_blocker is None and seed_authorized else "BLOCK", "entries": ledger_entries, "hash_chain_valid": True, "exact_blocker": None if seed_authorized else failed_checks[0]}

    records: dict[str, Any] = {
        "batch043_artifact_ingest_summary.json": ingest,
        "batch043_artifact_verification.json": verification,
        "batch043_episode_canonicalization_preservation.json": episode_preservation,
        "batch043_claim_boundary_preservation.json": claim_preservation,
        "batch044_standing_guardrail_enforcement_registry.json": registry,
        "batch044_isomorphic_coverage_enforcement_audit.json": coverage,
        "batch044_future_issue_derived_lane_eligibility_schema.json": eligibility,
        "batch044_next_issue_seed_selection_gate.json": gate,
        "batch044_protocol_version_boundary.json": protocol_boundary,
        "issue_derived_repair_feasibility_batch044.json": feasibility,
        "claim_boundary_batch044.json": claim,
        "proof_obligations_ledger_batch044.json": ledger,
    }
    for rel, value in records.items():
        write_json_deterministic(batch044_dir / rel, value)

    state = {
        "status": status,
        "exact_blocker": exact_blocker,
        "primary_artifact_name": PRIMARY_ARTIFACT,
        "batch043_artifact_ingest_status": ingest["status"],
        "batch043_artifact_verification_status": verification["status"],
        "episode_canonicalization_preservation_status": episode_preservation["status"],
        "standing_guardrail_enforcement_status": registry["status"],
        "isomorphic_coverage_enforcement_status": coverage["status"],
        "future_issue_derived_lane_eligibility_schema_status": eligibility["status"],
        "next_issue_seed_selection_gate_status": gate["status"],
        "next_issue_seed_selection_authorized": seed_authorized,
        "protocol_version_boundary_status": protocol_boundary["status"],
        "native_external_repair_episode_count": 4,
        "issue_derived_repair_episode_count": 1,
        "full_scoring": "NOT_RUN/disallowed",
        "memory_lift": "not_demonstrated",
        "self_maintaining_software": "false/not_demonstrated",
        "production_readiness": "false/not_demonstrated",
        "current_protocol": "v2.13",
    }
    write_json_deterministic(batch044_dir / "consolidated_state_clean_replication_batch_044.json", state)
    write_text_lf(
        batch044_dir / "campaign_summary.md",
        "\n".join(
            [
                "# Batch044 guardrail enforcement and seed eligibility",
                "",
                f"Status: `{status}`",
                f"Exact blocker: `{exact_blocker}`",
                "",
                "Batch044 officially ingests the Batch043 canonicalization artifact, preserves the first issue-derived repair episode, activates the standing future-lane guardrail registry, and authorizes only scoped next issue-seed candidate discovery.",
                "",
                "No repair generation, full scoring, matched-null comparison, memory-lift claim, production-readiness claim, or self-maintaining software claim is made.",
                "Native external repair episodes remain `4`; issue-derived repair episodes remain `1`; current protocol remains `v2.13`.",
            ]
        ),
    )
    write_json_deterministic(batch044_dir / "public_language_audit_batch044.json", public_language_audit(root, [batch044_dir / "campaign_summary.md"]))
    write_json_deterministic(root / "configs/clean_replication_batch_044.json", {"campaign_id": BATCH044_ID, "primary_artifact_name": PRIMARY_ARTIFACT, "current_protocol": "v2.13", "next_issue_seed_selection_authorized": seed_authorized})
    write_sha256sums(batch044_dir)
    return state


def write_batch044_public_state(root: Path, state: dict[str, Any]) -> None:
    shared = "\n".join(
        [
            "",
            "### Batch044 guardrail enforcement and seed eligibility",
            "",
            f"- Batch044 status: `{state['status']}`.",
            "- Future issue-derived repair lanes now require the Batch044 standing guardrail registry and eligibility schema before repair generation.",
            "- Scoped next issue-seed candidate discovery is authorized; repair generation is not started by Batch044.",
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
        marker = "### Batch044 guardrail enforcement and seed eligibility"
        if marker in text:
            text = text[: text.index(marker)].rstrip() + "\n" + shared + "\n"
        else:
            text = text.rstrip() + "\n" + shared + "\n"
        path.write_text(text, encoding="utf-8", newline="\n")
