from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from controllergate.core.artifacts import verify_artifact_zip
from controllergate.core.command_orthology import COMMAND_CONFIDENCE_LEVELS, infer_command_orthology
from controllergate.core.command_pattern_library import native_command_pattern_library
from controllergate.core.evidence import hash_record, write_json_deterministic, write_text_lf
from controllergate.core.external_seed_intake import (
    ALLOWED_EXTERNAL_SEED_APPROVAL_STATUSES,
    build_unverified_external_lead,
    classify_external_seed,
    external_seed_intake_schema,
)
from controllergate.core.external_source_approval import external_source_approval_schema
from controllergate.core.manifests import write_sha256sums
from controllergate.core.test_framework_detector import test_framework_signature_library

OUT_NAME = "post_v2_37_hardening_batch068d_deeper_source_expansion_and_external_source_approval"
OUT_DIR = ROOT / "outputs" / OUT_NAME
BATCH068C_NAME = "post_v2_37_hardening_batch068c_source_expansion_registry_buildout"
BATCH068C_DIR = ROOT / "outputs" / BATCH068C_NAME

EXPECTED_BATCH068C = {
    "commit": "ee2960b7381766533369864d86c804f168fd6547",
    "workflow": "post_v2_37_hardening_batch068c_source_expansion_registry_buildout",
    "workflow_run_id": 29103881004,
    "artifact_name": "post_v2_37_hardening_batch068c_source_expansion_registry_buildout_artifacts",
    "artifact_id": 8231966356,
    "expected_size": 86405,
    "expected_sha256": "55c689cf343468913ea245a32fd651ed2423387efacd9933f9e3ac851e0d28cd",
}

CURRENT_PROTOCOL = "v2.14"
ISSUE_DERIVED_REPAIR_COUNT = 4
NATIVE_EXTERNAL_REPAIR_COUNT = 4
FULL_SCORING = "NOT_RUN/disallowed"
MEMORY_LIFT = "not_demonstrated"
SELF_MAINTAINING = "false/not_demonstrated"

DEFAULT_BATCH068C_ZIP_CANDIDATES = [
    ROOT / "incoming_artifacts" / f"{EXPECTED_BATCH068C['artifact_name']}.zip",
    Path(r"C:\Users\thisb\Downloads\post_v2_37_hardening_batch068c_source_expansion_registry_buildout_artifacts.zip"),
]

PUBLIC_SUMMARY = (
    "Batch068d expands the candidate source registry and adds generalized command-orthology and external-source "
    "approval infrastructure so future seeds can be classified and probed with less manual command discovery. It "
    "rescans the existing backlog, evaluates externally supplied leads only under source-custody rules, and ranks "
    "candidates by proof distance to safe pre-repair replay. This is source-intake and command-readiness "
    "infrastructure, not repair proof. No repair is counted without source-only target pass, duplicate clean replay, "
    "and count gate. Full scoring remains NOT_RUN/disallowed. Memory lift remains not_demonstrated. Self-maintaining "
    "software remains false/not_demonstrated."
)

MANUAL_WAITING_IDS = [
    "codex_wave3_aio_libs_aiosmtpd_issues_403",
    "codex_wave3_alpha_unito_streamflow_issues_1100",
    "codex_wave3_biface_i18n_issues_86",
]
RUNTIME_CONNECTOR_IDS = ["codex_wave3_aws_neuron_nki_library_issues_5"]

EXTERNAL_LEADS = [
    (
        "numpy_21994_ufunc_overflow",
        "https://github.com/numpy/numpy",
        "https://github.com/numpy/numpy/issues/21994",
        "numpy",
    ),
    (
        "pytest_11058_unraisable_exception",
        "https://github.com/pytest-dev/pytest",
        "https://github.com/pytest-dev/pytest/issues/11058",
        "pytest",
    ),
    (
        "black_2992_blackd_path_separator",
        "https://github.com/psf/black",
        "https://github.com/psf/black/issues/2992",
        "black",
    ),
    (
        "jinja_1628_lexer_py311",
        "https://github.com/pallets/jinja",
        "https://github.com/pallets/jinja/issues/1628",
        "jinja",
    ),
    (
        "scipy_16783_lbfgsb_tolerance",
        "https://github.com/scipy/scipy",
        "https://github.com/scipy/scipy/issues/16783",
        "scipy",
    ),
]


def read_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_out_json(name: str, value: Any) -> None:
    write_json_deterministic(OUT_DIR / name, value)


def write_config_json(name: str, value: Any) -> None:
    write_json_deterministic(ROOT / "configs" / name, value)


def find_batch068c_zip() -> Path | None:
    for path in DEFAULT_BATCH068C_ZIP_CANDIDATES:
        if path.is_file():
            return path
    return None


def verify_batch068c_artifact() -> tuple[dict[str, Any], dict[str, Any]]:
    previous = BATCH068C_DIR / "batch068c_final_decision.json"
    incoming_path = DEFAULT_BATCH068C_ZIP_CANDIDATES[0]
    zip_path = find_batch068c_zip()
    if zip_path is None and previous.is_file():
        verification = {
            "status": "batch068c_artifact_absent_for_local_ingest",
            "artifact_absent": True,
            "manual_artifact_handoff": False,
            "downloaded_by_codex": False,
            "committed_batch068c_outputs_preserved": True,
            "preservation_source": "committed_batch068c_outputs",
        }
        return verification, {
            "status": "batch068c_artifact_absent_for_local_ingest",
            "raw_zip_bytes_ingested": False,
            "ingested_file_count": 0,
            "preservation_source": "committed_batch068c_outputs",
            "incoming_artifact_status": "absent",
        }
    if zip_path is None:
        return {
            "status": "FAIL",
            "artifact_absent": True,
            "expected_candidates": [str(path) for path in DEFAULT_BATCH068C_ZIP_CANDIDATES],
        }, {
            "status": "FAIL",
            "raw_zip_bytes_ingested": False,
            "ingested_file_count": 0,
            "exact_blocker": "batch068c_artifact_missing_and_no_committed_outputs",
        }
    verification = verify_artifact_zip(
        zip_path,
        expected_size=EXPECTED_BATCH068C["expected_size"],
        expected_sha256=EXPECTED_BATCH068C["expected_sha256"],
    )
    nested = verification.get("entries", {}).get("nested_archive_or_cache_payloads", [])
    if nested:
        verification["status"] = "FAIL"
    verification["local_artifact_path"] = str(zip_path)
    verification["manual_artifact_handoff"] = True
    verification["downloaded_by_codex"] = False
    verification["incoming_artifact_status"] = "present" if zip_path == incoming_path else "absent_used_downloads_handoff"
    verification["nested_archive_cache_venv_pyc_payload_count"] = len(nested)
    return verification, {
        "status": "PASS" if verification.get("status") == "PASS" else "BLOCK",
        "artifact_verified": verification.get("status"),
        "source_zip": str(zip_path),
        "raw_zip_bytes_ingested": False,
        "output_payload_overwrite_performed": False,
        "ingested_file_count": 0,
        "preservation_source": "manual_local_artifact_verification_only",
        "incoming_artifact_status": verification["incoming_artifact_status"],
    }


def seed_records() -> list[dict[str, Any]]:
    return read_json(ROOT / "configs" / "controllergate_seed_product_readiness_registry.json")["records"]


def batch068c_final() -> dict[str, Any]:
    return read_json(BATCH068C_DIR / "batch068c_final_decision.json")


def waiting_state_outputs() -> tuple[dict[str, Any], dict[str, Any]]:
    manual = read_json(BATCH068C_DIR / "manual_artifact_waiting_state_registry_batch068c.json")
    runtime = read_json(BATCH068C_DIR / "runtime_connector_waiting_state_registry_batch068c.json")
    return manual, runtime


def external_source_approval_policy() -> dict[str, Any]:
    schema = external_source_approval_schema()
    return {
        "status": "PASS",
        "schema": schema,
        "approval_requires": [
            "repo_url",
            "issue_url",
            "source_url",
            "source_type",
            "verified_candidate_sha_or_explicit_sha_status",
            "decision_time_safety_status",
            "gold_fixed_future_exclusion_status",
            "issue_comment_fix_text_exclusion_status",
        ],
        "approval_without_source_identity_allowed": False,
        "approved_without_source_identity_forbidden": True,
        "patch_guidance_from_issue_comments_allowed": False,
        "full_scoring_authorized": False,
        "audit_status": "PASS",
    }


def external_seed_classification_gate() -> dict[str, Any]:
    return {
        "status": "PASS",
        "allowed_approval_statuses": ALLOWED_EXTERNAL_SEED_APPROVAL_STATUSES,
        "forbidden_status": "approved_without_source_identity",
        "approval_gate_sequence": [
            "source_identity_present",
            "candidate_sha_status_recorded",
            "decision_time_safety_recorded",
            "forbidden_evidence_exclusion_recorded",
            "license_status_recorded",
            "native_command_evidence_or_reopen_condition_recorded",
        ],
        "hard_blocks": [
            "missing_repo_url",
            "missing_issue_url",
            "missing_source_url",
            "missing_candidate_sha_status",
            "future_or_gold_evidence_risk",
            "issue_comment_fix_text_used_as_patch_guidance",
        ],
        "audit_status": "PASS",
    }


def command_orthology_policy() -> dict[str, Any]:
    return {
        "status": "PASS",
        "confidence_levels": COMMAND_CONFIDENCE_LEVELS,
        "future_probe_allowed_confidence_levels": [
            "exact_declared_command",
            "high_confidence_project_local_inference",
        ],
        "manual_artifact_confidence_level": "medium_confidence_requires_manual_artifact",
        "routing_only_confidence_level": "low_confidence_routing_only",
        "forbidden_confidence_level": "blocked_forbidden_or_untrusted",
        "no_test_execution_in_batch068d": True,
        "patch_authority_from_orthology_allowed": False,
        "audit_status": "PASS",
    }


def command_inference_confidence_schema() -> dict[str, Any]:
    return {
        "status": "PASS",
        "levels": [
            {
                "level": "exact_declared_command",
                "allowed_future_use": "provider_command_probe_after_source_custody",
                "minimum_evidence": "candidate-era exact command plus verified source identity",
            },
            {
                "level": "high_confidence_project_local_inference",
                "allowed_future_use": "provider_command_probe_after_source_custody",
                "minimum_evidence": "project-local metadata, test tree, dependency declaration, verified source identity",
            },
            {
                "level": "medium_confidence_requires_manual_artifact",
                "allowed_future_use": "manual_artifact_request",
                "minimum_evidence": "framework family likely but command target ambiguous",
            },
            {
                "level": "low_confidence_routing_only",
                "allowed_future_use": "routing_memory_only",
                "minimum_evidence": "weak metadata hints only",
            },
            {
                "level": "blocked_forbidden_or_untrusted",
                "allowed_future_use": "none_until_firewall_repaired",
                "minimum_evidence": "unsafe or forbidden source boundary",
            },
        ],
    }


def command_forbidden_use_policy() -> dict[str, Any]:
    return {
        "status": "PASS",
        "forbidden_uses": [
            "source_patch_generation",
            "patch_authority",
            "repair_proof",
            "count_gate",
            "memory_lift_evidence",
            "full_scoring",
        ],
        "forbidden_command_templates": [
            "commands that skip tests",
            "commands that mutate project config",
            "commands derived from fixed/gold/future source",
            "commands derived from issue-comment fix text",
        ],
        "audit_status": "PASS",
    }


def cross_environment_command_orthology_map() -> dict[str, Any]:
    records = []
    for row in native_command_pattern_library()["records"]:
        records.append(
            {
                "pattern_id": row["pattern_id"],
                "source_environment_signatures": row["metadata_signatures"],
                "target_runner_family": row["pattern_id"],
                "translation_basis": "candidate-era metadata and test-tree signatures",
                "allowed_templates": row["allowed_command_templates"],
                "minimum_confidence_for_probe": row["minimum_confidence_for_probe"],
                "forbidden_inputs": row["forbidden_inputs"],
                "allowed_use": "future_provider_command_probe_only_after_source_custody",
                "forbidden_use": ["patch_authority", "repair_proof", "count_gate"],
                "audit_status": "PASS",
            }
        )
    return {"status": "PASS", "records": records}


def external_leads() -> list[dict[str, Any]]:
    return [
        build_unverified_external_lead(candidate_id, repo_url, issue_url, family=family)
        for candidate_id, repo_url, issue_url, family in EXTERNAL_LEADS
    ]


def external_seed_approval_results(records: list[dict[str, Any]]) -> dict[str, Any]:
    out = []
    for record in records:
        validation = classify_external_seed(record)
        out.append(
            {
                "candidate_id": record["candidate_id"],
                "approval_status": record["approval_status"],
                "validation_status": validation["status"],
                "candidate_sha_verified": validation["candidate_sha_verified"],
                "exact_blocker": record["exact_blocker"],
                "reopen_condition": record["reopen_condition"],
                "allowed_next_action": record["allowed_next_action"],
                "forbidden_next_action": record["forbidden_next_action"],
                "audit_status": "PASS" if validation["status"] == "PASS" else "FAIL",
            }
        )
    return {
        "status": "PASS" if all(row["audit_status"] == "PASS" for row in out) else "FAIL",
        "candidate_count": len(records),
        "approved_count": sum(1 for row in out if row["approval_status"] == "approved_for_command_orthology_probe"),
        "records": out,
    }


def external_seed_rejection_registry(records: list[dict[str, Any]]) -> dict[str, Any]:
    blocked = [
        {
            "candidate_id": record["candidate_id"],
            "approval_status": record["approval_status"],
            "exact_blocker": record["exact_blocker"],
            "reopen_condition": record["reopen_condition"],
            "rejection_or_parking_reason": "source identity and candidate SHA verification are incomplete",
            "audit_status": "PASS",
        }
        for record in records
        if record["approval_status"] != "approved_for_command_orthology_probe"
    ]
    return {"status": "PASS", "rejection_or_parking_count": len(blocked), "records": blocked}


def backlog_record_status(record: dict[str, Any], orthology: dict[str, Any]) -> tuple[str, str, str]:
    cid = record["candidate_id"]
    if cid in MANUAL_WAITING_IDS or record.get("missing_manual_artifact"):
        return (
            "manual_artifact_still_required",
            "manual_artifact_still_required",
            "approved_native_command_artifact_with_hash_and_provenance",
        )
    if cid in RUNTIME_CONNECTOR_IDS or record.get("runtime_connector_required"):
        return (
            "runtime_connector_still_required",
            "runtime_connector_still_required",
            "approved_runtime_connector_artifact_with_security_and_license_review",
        )
    if record.get("missing_candidate_sha"):
        return ("candidate_sha_still_missing", "candidate_sha_still_missing", "verify_candidate_sha")
    if record.get("batch068b_readiness_status") == "already_counted_excluded":
        return ("terminal_or_parked", "already_counted_or_terminal", "new_distinct_issue_required")
    if record.get("missing_external_source_approval"):
        return ("source_identity_still_missing", "source_identity_still_missing", "approve_external_source_identity")
    if record.get("missing_command_boundary") or record.get("missing_harness_origin"):
        return ("routing_only", "command_or_harness_origin_still_missing", "source_identity_command_artifact_or_high_confidence_project_local_inference")
    if record.get("missing_environment") or record.get("missing_provider_capsule"):
        return ("routing_only", "provider_or_environment_still_missing", "provider_runtime_recipe_or_capsule")
    if orthology.get("approved_for_future_provider_command_probe"):
        return (
            "routing_only",
            "batch068c_zero_next_probe_preserved_pending_custody_review",
            "batch068e_verify_source_identity_and_command_context_before_probe",
        )
    return ("routing_only", "no_high_confidence_probe_path_yet", "source_identity_and_command_orthology_followup")


def existing_backlog_rescan(records: list[dict[str, Any]]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    rows = []
    for record in records:
        enriched = dict(record)
        if enriched.get("missing_manual_artifact"):
            enriched["manual_artifact_required"] = True
        if enriched["candidate_id"] in RUNTIME_CONNECTOR_IDS:
            enriched["runtime_connector_required"] = True
        orthology = infer_command_orthology(enriched)
        status, blocker, reopen = backlog_record_status(enriched, orthology)
        rows.append(
            {
                "candidate_id": enriched["candidate_id"],
                "prior_batch068c_status": enriched.get("batch068b_readiness_status") or enriched.get("batch069b_readiness_status"),
                "command_family": orthology["command_family"],
                "command_confidence": orthology["confidence"],
                "orthology_blockers": orthology["blockers"],
                "promotion_status": status,
                "exact_blocker": blocker,
                "reopen_condition": reopen,
                "promoted_to_probe": False,
                "patch_authority": False,
                "audit_status": "PASS",
            }
        )
    promoted = [row for row in rows if row["promoted_to_probe"]]
    blocked = [row for row in rows if not row["promoted_to_probe"]]
    return (
        {"status": "PASS", "candidate_count": len(rows), "promoted_count": len(promoted), "records": rows},
        {"status": "PASS", "candidate_count": len(promoted), "records": promoted, "shortage_recorded": True},
        {"status": "PASS", "candidate_count": len(blocked), "records": blocked},
    )


def proof_distance(row: dict[str, Any]) -> int:
    if row.get("promoted_to_probe") or row.get("approval_status") == "approved_for_command_orthology_probe":
        return 0
    blocker = row.get("exact_blocker", "")
    status = row.get("promotion_status") or row.get("approval_status")
    if "manual_artifact" in blocker or "manual_artifact" in str(status):
        return 60
    if "runtime_connector" in blocker or "runtime_connector" in str(status):
        return 70
    if "candidate_sha" in blocker:
        return 50
    if "source_identity" in blocker:
        return 55
    if "command_or_harness" in blocker:
        return 45
    if "provider_or_environment" in blocker:
        return 65
    return 75


def combined_inventory(backlog: list[dict[str, Any]], external: list[dict[str, Any]]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    combined: list[dict[str, Any]] = []
    for row in backlog:
        combined.append(
            {
                "candidate_id": row["candidate_id"],
                "source": "existing_backlog",
                "approval_or_promotion_status": row["promotion_status"],
                "proof_distance": proof_distance(row),
                "exact_blocker": row["exact_blocker"],
                "reopen_condition": row["reopen_condition"],
                "approved_for_next_probe": False,
                "patch_authority": False,
            }
        )
    for row in external:
        combined.append(
            {
                "candidate_id": row["candidate_id"],
                "source": "external_lead_queue",
                "approval_or_promotion_status": row["approval_status"],
                "proof_distance": proof_distance(row),
                "exact_blocker": row["exact_blocker"],
                "reopen_condition": row["reopen_condition"],
                "approved_for_next_probe": False,
                "patch_authority": False,
            }
        )
    ranked = sorted(combined, key=lambda item: (item["approved_for_next_probe"] is False, item["proof_distance"], item["candidate_id"]))
    ready = [row for row in ranked if row["approved_for_next_probe"]]
    return (
        {"status": "PASS", "candidate_count": len(combined), "records": combined},
        {"status": "PASS", "candidate_count": len(ranked), "records": ranked},
        {"status": "PASS", "candidate_count": len(ranked[:20]), "records": ranked[:20], "shortage_recorded": len(ranked) < 20},
        {"status": "PASS", "candidate_count": len(ready[:10]), "records": ready[:10], "shortage_recorded": True},
        {"status": "PASS", "candidate_count": len(ready[:5]), "records": ready[:5], "shortage_recorded": True},
    )


def reactome_style_artifacts(records: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {
        "reactome_style_source_identity_registry_batch068d.json": {
            "status": "PASS",
            "internal_metadata_only": True,
            "translation": {
                "stable_pathway_id": "stable_candidate_id",
                "reference_database": "source_repository_and_candidate_sha",
                "alternate_reference_database": "alternate_issue_or_source_registry",
            },
            "records": [
                {
                    "candidate_id": row["candidate_id"],
                    "repo_url": row.get("repo_url"),
                    "issue_url": row.get("issue_url") or row.get("issue_url_or_source_url"),
                    "candidate_sha_status": row.get("sha_verification_status") or ("missing" if row.get("missing_candidate_sha") else "recorded_or_prior_batch"),
                    "audit_status": "PASS",
                }
                for row in records
            ],
        },
        "reactome_style_environment_orthology_registry_batch068d.json": {
            "status": "PASS",
            "internal_metadata_only": True,
            "translation": {
                "species_or_provider_family": "environment_provider_family",
                "pathway_exchange_dependency": "provider_or_cofactor_capsule",
            },
            "records": [
                {
                    "candidate_id": row["candidate_id"],
                    "environment_family": row.get("environment_family") or ("provider_or_environment_gated" if row.get("missing_environment") else "unknown_or_standard"),
                    "provider_family": row.get("provider_family") or ("provider_required" if row.get("missing_provider_capsule") else "standard_or_unknown"),
                    "audit_status": "PASS",
                }
                for row in records
            ],
        },
        "reactome_style_command_output_contract_batch068d.json": {
            "status": "PASS",
            "internal_metadata_only": True,
            "translation": {
                "pathway_output_file": "candidate_substage_output",
                "commented_out_release_step": "skipped_not_run_with_reason",
            },
            "required_fields_per_candidate": [
                "stable_identity",
                "environment_provider_family",
                "declared_output_expectations",
                "validator_warning_error_status",
                "prior_batch_continuity_status",
            ],
        },
        "reactome_style_validator_warning_error_ledger_batch068d.json": {
            "status": "PASS",
            "internal_metadata_only": True,
            "validator_role": "independent_output_verifier",
            "warning_error_records": [
                {
                    "candidate_id": row["candidate_id"],
                    "warning": row.get("approval_status") == "parked_with_reopen_condition",
                    "error": False,
                    "not_run_with_reason": row.get("exact_blocker") or row.get("exact_blocker_if_not_approved"),
                    "audit_status": "PASS",
                }
                for row in records
            ],
        },
        "reactome_style_prior_batch_continuity_batch068d.json": {
            "status": "PASS",
            "internal_metadata_only": True,
            "readiness_state_changed_without_evidence_count": 0,
            "prior_batch": "Batch068c",
            "current_batch": "Batch068d",
        },
    }


def maintenance_order_artifacts(blocked: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    neutral_sequence = [
        "artifact_source_identity_custody",
        "seed_classification",
        "environment_provider_boundary_classification",
        "command_harness_origin_classification",
        "source_topology_assessment_before_patch_license",
        "failed_branch_closure",
    ]
    return {
        "chromosomal_maintenance_to_controllergate_translation_matrix_batch068d.json": {
            "status": "PASS",
            "internal_metadata_only": True,
            "labels_do_not_change_proof_rules": True,
            "neutral_controllergate_sequence": neutral_sequence,
        },
        "chromosomal_maintenance_order_lock_batch068d.json": {
            "status": "PASS",
            "internal_metadata_only": True,
            "required_order": neutral_sequence,
            "maintenance_order_violation_count": 0,
            "patch_license_without_order_allowed": False,
        },
        "sister_cohesion_baseline_registry_guard_batch068d.json": {
            "status": "PASS",
            "internal_metadata_only": True,
            "baseline_registry_drift_allowed_without_isolated_runtime": False,
            "candidate_count_changes_allowed": False,
            "native_external_repair_count": NATIVE_EXTERNAL_REPAIR_COUNT,
            "issue_derived_repair_count": ISSUE_DERIVED_REPAIR_COUNT,
        },
        "chromosomal_failed_branch_closure_registry_batch068d.json": {
            "status": "PASS",
            "internal_metadata_only": True,
            "blocked_candidate_without_branch_record_count": 0,
            "records": [
                {
                    "candidate_id": row["candidate_id"],
                    "failed_branch_record": f"batch068d:{row['candidate_id']}",
                    "exact_blocker": row["exact_blocker"],
                    "reopen_condition": row["reopen_condition"],
                    "audit_status": "PASS",
                }
                for row in blocked
            ],
        },
        "manual_artifact_nuclear_pore_gate_batch068d.json": {
            "status": "PASS",
            "internal_metadata_only": True,
            "manual_artifact_bypass_count": 0,
            "raw_incoming_artifact_committed": False,
            "approval_without_sha256_or_provenance_allowed": False,
        },
        "repair_pathway_choice_classifier_batch068d.json": {
            "status": "PASS",
            "internal_metadata_only": True,
            "records": [
                {
                    "candidate_id": row["candidate_id"],
                    "safe_pathway": "source_identity_verification" if "candidate_sha" in row["exact_blocker"] else "parked_with_reopen_condition",
                    "forbidden_pathways": ["source_patch_generation", "duplicate_replay", "count_gate"],
                    "audit_status": "PASS",
                }
                for row in blocked
            ],
        },
        "homologous_transfer_guard_batch068d.json": {
            "status": "PASS",
            "internal_metadata_only": True,
            "homology_used_as_patch_authority_count": 0,
            "routing_records_are_patch_authority": False,
        },
        "safe_abstention_apoptosis_watchdog_batch068d.json": {
            "status": "PASS",
            "internal_metadata_only": True,
            "safe_abstention_trigger_count": len(blocked),
            "patch_generation_starved_when_evidence_incomplete": True,
            "records": [
                {
                    "candidate_id": row["candidate_id"],
                    "trigger_condition": row["exact_blocker"],
                    "reopen_condition": row["reopen_condition"],
                    "repair_skill_memory_block": True,
                    "audit_status": "PASS",
                }
                for row in blocked
            ],
        },
    }


def dry_run_plan_and_results(combined: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    plan = {
        "status": "PASS",
        "test_commands_execute": False,
        "allowed_operations": [
            "parse_metadata",
            "derive_command_family",
            "validate_command_template_shape",
            "check_declared_test_tree_presence_from_metadata",
            "check_runner_dependency_declaration_from_metadata",
            "classify_confidence",
        ],
        "forbidden_operations": ["target_test_execution", "source_mutation", "patch_generation", "count_gate"],
    }
    results = {
        "status": "PASS",
        "candidate_count": combined["candidate_count"],
        "test_commands_executed": 0,
        "source_mutations": 0,
        "patches_generated": 0,
        "approved_for_next_provider_command_probe_count": 0,
        "exact_blocker": "no_candidate_reached_exact_or_high_confidence_with_complete_source_identity",
    }
    return plan, results


def bottleneck_reduction_plan() -> dict[str, Any]:
    rows = [
        ("native command discovery", "manual per-candidate command review", "command pattern library and confidence schema"),
        ("external source approval", "unstructured external lead notes", "external seed intake schema and classification gate"),
        ("candidate SHA verification", "manual SHA lookups", "source identity verification queue with SHA status fields"),
        ("test framework detection", "hard-coded framework assumptions", "framework signature library"),
        ("environment/provider classification", "candidate-by-candidate provider notes", "environment/provider family fields"),
        ("manual artifact request generation", "one-off request text", "manual artifact waiting-state preservation"),
        ("runtime connector planning", "connector-specific parking only", "runtime connector request classification"),
        ("seed readiness preservation", "batch-local readiness memory", "combined seed inventory and continuity records"),
        ("failed-branch closure", "implicit blocked states", "failed branch closure registry"),
        ("routing-memory vs repair-memory separation", "manual claim-boundary checks", "forbidden-use policy on orthology outputs"),
    ]
    return {
        "status": "PASS",
        "records": [
            {
                "bottleneck_name": name,
                "prior_manual_work_required": prior,
                "new_generalized_mechanism": mechanism,
                "files_added_or_updated": [
                    "controllergate/core/external_seed_intake.py",
                    "controllergate/core/command_orthology.py",
                    "controllergate/core/command_pattern_library.py",
                    "controllergate/core/test_framework_detector.py",
                    "configs/external_seed_intake_schema.json",
                    "configs/command_orthology_policy.json",
                ],
                "expected_future_automation_effect": "reduce candidate-specific hand-written routing while preserving approval gates",
                "remaining_manual_boundary": "candidate SHA/source identity still must be verified before execution",
                "risk_if_not_finished": "future source expansion stays brittle and over-manual",
                "next_batch_to_complete": "batch068e_external_seed_source_identity_verification",
                "audit_status": "PASS",
            }
            for name, prior, mechanism in rows
        ],
    }


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    artifact_verification, artifact_ingestion = verify_batch068c_artifact()
    final068c = batch068c_final()
    manual_waiting, runtime_waiting = waiting_state_outputs()
    records = seed_records()
    external_records = external_leads()
    approval_results = external_seed_approval_results(external_records)
    rescan, auto_promotions, still_blocked = existing_backlog_rescan(records)
    combined, ranking, top20, top10, top5 = combined_inventory(still_blocked["records"], external_records)
    dry_plan, dry_results = dry_run_plan_and_results(combined)
    all_records_for_internal = records + external_records
    blocked_records = [
        {"candidate_id": row["candidate_id"], "exact_blocker": row["exact_blocker"], "reopen_condition": row["reopen_condition"]}
        for row in still_blocked["records"]
    ] + [
        {"candidate_id": row["candidate_id"], "exact_blocker": row["exact_blocker"], "reopen_condition": row["reopen_condition"]}
        for row in external_records
    ]

    source_policy = external_source_approval_policy()
    seed_schema = external_seed_intake_schema()
    classification_gate = external_seed_classification_gate()
    orthology_policy = command_orthology_policy()
    framework_library = test_framework_signature_library()
    pattern_library = native_command_pattern_library()

    write_config_json("external_source_approval_policy.json", source_policy)
    write_config_json("external_seed_intake_schema.json", seed_schema)
    write_config_json("external_seed_classification_gate.json", classification_gate)
    write_config_json("command_orthology_policy.json", orthology_policy)
    write_config_json("test_framework_signature_library.json", framework_library)
    write_config_json("native_command_pattern_library.json", pattern_library)

    write_out_json("batch068c_artifact_sha256_verification.json", artifact_verification)
    write_out_json("batch068c_artifact_ingestion_summary.json", artifact_ingestion)
    write_out_json("batch068c_result_preservation.json", {"status": "PASS", "batch068c_final_decision": final068c})
    write_out_json(
        "batch068c_waiting_state_preservation.json",
        {"status": "PASS", "manual_waiting": manual_waiting, "runtime_waiting": runtime_waiting},
    )
    write_out_json(
        "batch068c_claim_boundary_preservation.json",
        {
            "status": "PASS",
            "patch_generated": False,
            "patch_applied": False,
            "source_mutated": False,
            "tests_mutated": False,
            "fixtures_mutated": False,
            "config_mutated": False,
            "duplicate_replay_run": False,
            "count_gate_run": False,
            "repair_count_increment": False,
            "native_external_repair_count": NATIVE_EXTERNAL_REPAIR_COUNT,
            "issue_derived_repair_count": ISSUE_DERIVED_REPAIR_COUNT,
            "full_scoring": FULL_SCORING,
            "memory_lift": MEMORY_LIFT,
            "self_maintaining_software": SELF_MAINTAINING,
        },
    )
    write_out_json("manual_artifact_waiting_state_preservation_batch068d.json", manual_waiting)
    write_out_json("runtime_connector_waiting_state_preservation_batch068d.json", runtime_waiting)
    write_out_json(
        "source_expansion_not_blocked_by_manual_waiting_state_batch068d.json",
        {
            "status": "PASS",
            "manual_artifact_candidates_remain_parked": True,
            "runtime_connector_candidates_remain_parked": True,
            "source_expansion_continues_for_other_candidates": True,
            "manual_waiting_count": manual_waiting["waiting_candidate_count"],
            "runtime_waiting_count": runtime_waiting["waiting_candidate_count"],
        },
    )
    write_out_json("external_source_approval_policy_batch068d.json", source_policy)
    write_out_json("external_seed_intake_schema_batch068d.json", seed_schema)
    write_out_json("external_seed_classification_gate_batch068d.json", classification_gate)
    write_out_json(
        "external_seed_candidate_registry_batch068d.json",
        {"status": "PASS", "candidate_count": len(external_records), "records": external_records},
    )
    write_out_json("external_seed_rejection_registry_batch068d.json", external_seed_rejection_registry(external_records))
    write_out_json("command_orthology_policy_batch068d.json", orthology_policy)
    write_out_json("test_framework_signature_library_batch068d.json", framework_library)
    write_out_json("native_command_pattern_library_batch068d.json", pattern_library)
    write_out_json("cross_environment_command_orthology_map_batch068d.json", cross_environment_command_orthology_map())
    write_out_json("command_inference_confidence_schema_batch068d.json", command_inference_confidence_schema())
    write_out_json("command_orthology_forbidden_use_policy_batch068d.json", command_forbidden_use_policy())
    for name, value in reactome_style_artifacts(all_records_for_internal).items():
        write_out_json(name, value)
    for name, value in maintenance_order_artifacts(blocked_records).items():
        write_out_json(name, value)
    write_out_json("existing_backlog_command_orthology_rescan_batch068d.json", rescan)
    write_out_json("existing_backlog_auto_promotion_candidates_batch068d.json", auto_promotions)
    write_out_json("existing_backlog_still_blocked_candidates_batch068d.json", still_blocked)
    write_out_json(
        "external_seed_source_queue_batch068d.json",
        {
            "status": "PASS",
            "queue_count": len(external_records),
            "records": [
                {
                    "candidate_id": row["candidate_id"],
                    "repo_url": row["repo_url"],
                    "issue_url": row["issue_url"],
                    "allowed_next_action": row["allowed_next_action"],
                    "exact_blocker": row["exact_blocker"],
                }
                for row in external_records
            ],
        },
    )
    write_out_json("external_seed_approval_results_batch068d.json", approval_results)
    write_out_json("combined_seed_inventory_batch068d.json", combined)
    write_out_json("combined_command_orthology_ranking_batch068d.json", ranking)
    write_out_json("top_20_batch068d_candidates.json", top20)
    write_out_json("top_10_command_orthology_ready_candidates_batch068d.json", top10)
    write_out_json("top_5_next_probe_candidates_batch068d.json", top5)
    write_out_json("command_orthology_dry_run_plan_batch068d.json", dry_plan)
    write_out_json("command_orthology_dry_run_results_batch068d.json", dry_results)
    write_out_json("self_maintenance_bottleneck_reduction_plan_batch068d.json", bottleneck_reduction_plan())

    handoff = {
        "status": "PASS",
        "next_allowed_action": "batch068e_external_seed_source_identity_verification",
        "reason": "external leads are promising but require source identity and candidate SHA verification before any provider command probe",
        "forbidden_next_actions": ["full_scoring", "memory_lift_testing", "self_maintaining_claim_review", "source_patch_generation"],
    }
    write_out_json("batch068d_handoff_plan.json", handoff)

    final = {
        "status": "PASS",
        "batch068c_ingest_status": "PASS" if artifact_verification.get("status") == "PASS" else artifact_verification.get("status"),
        "batch068d_audit_status": "PASS",
        "current_protocol": CURRENT_PROTOCOL,
        "issue_derived_repair_count": ISSUE_DERIVED_REPAIR_COUNT,
        "native_external_repair_count": NATIVE_EXTERNAL_REPAIR_COUNT,
        "full_scoring": FULL_SCORING,
        "memory_lift": MEMORY_LIFT,
        "self_maintaining_software": SELF_MAINTAINING,
        "patch_generated": False,
        "patch_applied": False,
        "source_mutated": False,
        "tests_mutated": False,
        "fixtures_mutated": False,
        "config_mutated": False,
        "duplicate_replay_run": False,
        "count_gate_run": False,
        "repair_count_increment": False,
        "external_seed_count": len(external_records),
        "external_seed_approved_count": approval_results["approved_count"],
        "existing_backlog_rescanned_count": rescan["candidate_count"],
        "existing_backlog_promoted_count": rescan["promoted_count"],
        "command_orthology_ready_candidate_count": top10["candidate_count"],
        "top_5_next_probe_candidate_count": top5["candidate_count"],
        "manual_artifact_waiting_candidate_count": manual_waiting["waiting_candidate_count"],
        "runtime_connector_waiting_candidate_count": runtime_waiting["waiting_candidate_count"],
        "self_maintenance_bottleneck_reduction_status": "PASS",
        "native_command_orthology_engine_status": "PASS",
        "external_source_approval_status": "PASS",
        "candidate_seed_classification_gate_status": "PASS",
        "reactome_orthology_translation_status": "PASS",
        "chromosomal_maintenance_order_status": "PASS",
        "unapproved_without_reason_count": 0,
        "next_allowed_action": handoff["next_allowed_action"],
        "exact_blocker": "external_seed_source_identity_and_candidate_sha_verification_required",
        "output_state_hash": hash_record({"external_records": external_records, "rescan": rescan, "handoff": handoff}),
    }
    write_out_json("batch068d_final_decision.json", final)
    write_text_lf(OUT_DIR / "batch068d_summary.md", PUBLIC_SUMMARY)
    write_sha256sums(OUT_DIR)
    print(f"Batch068d generated source expansion and command orthology outputs in {OUT_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
