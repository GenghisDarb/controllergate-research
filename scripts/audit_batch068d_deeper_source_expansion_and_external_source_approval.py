from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from controllergate.core.external_seed_intake import ALLOWED_EXTERNAL_SEED_APPROVAL_STATUSES
from controllergate.core.manifests import verify_manifest
from controllergate.core.public_summary import audit_public_summary_text

OUT_NAME = "post_v2_37_hardening_batch068d_deeper_source_expansion_and_external_source_approval"
OUT_DIR = ROOT / "outputs" / OUT_NAME

REQUIRED_FILES = [
    "batch068c_artifact_ingestion_summary.json",
    "batch068c_artifact_sha256_verification.json",
    "batch068c_result_preservation.json",
    "batch068c_waiting_state_preservation.json",
    "batch068c_claim_boundary_preservation.json",
    "manual_artifact_waiting_state_preservation_batch068d.json",
    "runtime_connector_waiting_state_preservation_batch068d.json",
    "source_expansion_not_blocked_by_manual_waiting_state_batch068d.json",
    "external_source_approval_policy_batch068d.json",
    "external_seed_intake_schema_batch068d.json",
    "external_seed_classification_gate_batch068d.json",
    "external_seed_candidate_registry_batch068d.json",
    "external_seed_rejection_registry_batch068d.json",
    "command_orthology_policy_batch068d.json",
    "test_framework_signature_library_batch068d.json",
    "native_command_pattern_library_batch068d.json",
    "cross_environment_command_orthology_map_batch068d.json",
    "command_inference_confidence_schema_batch068d.json",
    "command_orthology_forbidden_use_policy_batch068d.json",
    "reactome_style_source_identity_registry_batch068d.json",
    "reactome_style_environment_orthology_registry_batch068d.json",
    "reactome_style_command_output_contract_batch068d.json",
    "reactome_style_validator_warning_error_ledger_batch068d.json",
    "reactome_style_prior_batch_continuity_batch068d.json",
    "chromosomal_maintenance_to_controllergate_translation_matrix_batch068d.json",
    "chromosomal_maintenance_order_lock_batch068d.json",
    "sister_cohesion_baseline_registry_guard_batch068d.json",
    "chromosomal_failed_branch_closure_registry_batch068d.json",
    "manual_artifact_nuclear_pore_gate_batch068d.json",
    "repair_pathway_choice_classifier_batch068d.json",
    "homologous_transfer_guard_batch068d.json",
    "safe_abstention_apoptosis_watchdog_batch068d.json",
    "existing_backlog_command_orthology_rescan_batch068d.json",
    "existing_backlog_auto_promotion_candidates_batch068d.json",
    "existing_backlog_still_blocked_candidates_batch068d.json",
    "external_seed_source_queue_batch068d.json",
    "external_seed_approval_results_batch068d.json",
    "combined_seed_inventory_batch068d.json",
    "combined_command_orthology_ranking_batch068d.json",
    "top_20_batch068d_candidates.json",
    "top_10_command_orthology_ready_candidates_batch068d.json",
    "top_5_next_probe_candidates_batch068d.json",
    "command_orthology_dry_run_plan_batch068d.json",
    "command_orthology_dry_run_results_batch068d.json",
    "self_maintenance_bottleneck_reduction_plan_batch068d.json",
    "batch068d_handoff_plan.json",
    "batch068d_final_decision.json",
    "batch068d_summary.md",
    "SHA256SUMS.txt",
]

REQUIRED_IMPLEMENTATION_FILES = [
    "controllergate/core/external_source_approval.py",
    "controllergate/core/external_seed_intake.py",
    "controllergate/core/command_orthology.py",
    "controllergate/core/command_pattern_library.py",
    "controllergate/core/test_framework_detector.py",
    "configs/external_source_approval_policy.json",
    "configs/external_seed_intake_schema.json",
    "configs/external_seed_classification_gate.json",
    "configs/command_orthology_policy.json",
    "configs/test_framework_signature_library.json",
    "configs/native_command_pattern_library.json",
    "scripts/generate_batch068d_deeper_source_expansion_and_external_source_approval.py",
    "scripts/audit_batch068d_deeper_source_expansion_and_external_source_approval.py",
    ".github/workflows/post_v2_37_hardening_batch068d_deeper_source_expansion_and_external_source_approval.yml",
]


def read_json(name: str) -> Any:
    return json.loads((OUT_DIR / name).read_text(encoding="utf-8"))


def expect(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def run_check(args: list[str], errors: list[str], label: str) -> None:
    proc = subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=False)
    expect(errors, proc.returncode == 0, f"{label} failed: {proc.stdout[-1200:]} {proc.stderr[-1200:]}")


def audit_external_seed_intake(errors: list[str]) -> None:
    schema = read_json("external_seed_intake_schema_batch068d.json")
    registry = read_json("external_seed_candidate_registry_batch068d.json")
    results = read_json("external_seed_approval_results_batch068d.json")
    rejection = read_json("external_seed_rejection_registry_batch068d.json")
    expect(errors, schema.get("status") == "PASS", "external seed schema not PASS")
    expect(errors, "approved_without_source_identity" == schema.get("forbidden_status"), "forbidden status not declared")
    expect(errors, registry.get("status") == "PASS", "external seed registry not PASS")
    expect(errors, registry.get("candidate_count") == 5, "expected five external leads")
    expect(errors, results.get("approved_count") == 0, "external leads were approved before source identity verification")
    expect(errors, rejection.get("rejection_or_parking_count") == registry.get("candidate_count"), "not all external leads parked/rejected")
    for row in registry.get("records", []):
        cid = row.get("candidate_id")
        expect(errors, row.get("approval_status") in ALLOWED_EXTERNAL_SEED_APPROVAL_STATUSES, f"{cid} invalid approval status")
        expect(errors, row.get("approval_status") != "approved_without_source_identity", f"{cid} forbidden approval status")
        if row.get("approval_status") == "approved_for_command_orthology_probe":
            validation = row.get("validation", {})
            expect(errors, validation.get("candidate_sha_verified") is True, f"{cid} approved without verified SHA")
        else:
            expect(errors, bool(row.get("exact_blocker")), f"{cid} missing exact blocker")
            expect(errors, bool(row.get("reopen_condition")), f"{cid} missing reopen condition")


def audit_command_orthology(errors: list[str]) -> None:
    policy = read_json("command_orthology_policy_batch068d.json")
    patterns = read_json("native_command_pattern_library_batch068d.json")
    signatures = read_json("test_framework_signature_library_batch068d.json")
    cross = read_json("cross_environment_command_orthology_map_batch068d.json")
    dry = read_json("command_orthology_dry_run_results_batch068d.json")
    expect(errors, policy.get("status") == "PASS", "command orthology policy not PASS")
    expect(errors, policy.get("no_test_execution_in_batch068d") is True, "test execution was allowed")
    expect(errors, patterns.get("status") == "PASS", "native command pattern library not PASS")
    expect(errors, signatures.get("status") == "PASS", "test framework signature library not PASS")
    expect(errors, cross.get("status") == "PASS", "cross environment command map not PASS")
    expect(errors, len(patterns.get("records", [])) >= 16, "native pattern library too small")
    for row in patterns.get("records", []):
        for field in [
            "pattern_id",
            "source_files",
            "metadata_signatures",
            "test_tree_signatures",
            "runner_dependency_signatures",
            "allowed_command_templates",
            "forbidden_command_templates",
            "confidence_rules",
            "decision_time_safe_inputs",
            "forbidden_inputs",
            "harness_origin_requirements",
            "runner_target_requirements",
            "provider_capsule_requirements",
            "minimum_confidence_for_probe",
            "audit_status",
        ]:
            expect(errors, field in row, f"pattern {row.get('pattern_id')} missing {field}")
    expect(errors, dry.get("test_commands_executed") == 0, "Batch068d executed target tests")
    expect(errors, dry.get("patches_generated") == 0, "Batch068d generated patch")
    expect(errors, dry.get("approved_for_next_provider_command_probe_count") == 0, "dry run approved probe unexpectedly")


def audit_backlog_rescan(errors: list[str]) -> None:
    rescan = read_json("existing_backlog_command_orthology_rescan_batch068d.json")
    promotions = read_json("existing_backlog_auto_promotion_candidates_batch068d.json")
    blocked = read_json("existing_backlog_still_blocked_candidates_batch068d.json")
    manual = read_json("manual_artifact_waiting_state_preservation_batch068d.json")
    runtime = read_json("runtime_connector_waiting_state_preservation_batch068d.json")
    expect(errors, rescan.get("candidate_count") == 94, "existing backlog count changed")
    expect(errors, rescan.get("promoted_count") == 0, "existing backlog was promoted unexpectedly")
    expect(errors, promotions.get("candidate_count") == 0, "auto promotion list must be empty")
    expect(errors, blocked.get("candidate_count") == 94, "blocked backlog count changed")
    expect(errors, manual.get("waiting_candidate_count") == 3, "manual waiting count changed")
    expect(errors, runtime.get("waiting_candidate_count") == 1, "runtime waiting count changed")
    for row in rescan.get("records", []):
        expect(errors, row.get("promoted_to_probe") is False, f"{row.get('candidate_id')} promoted unexpectedly")
        expect(errors, row.get("patch_authority") is False, f"{row.get('candidate_id')} got patch authority")
        if row.get("promotion_status") == "manual_artifact_still_required":
            expect(errors, row.get("candidate_id") in [r["candidate_id"] for r in manual.get("records", [])] or row.get("exact_blocker") == "manual_artifact_still_required", f"{row.get('candidate_id')} manual artifact mismatch")
        if row.get("promotion_status") == "runtime_connector_still_required":
            expect(errors, row.get("candidate_id") in [r["candidate_id"] for r in runtime.get("records", [])], f"{row.get('candidate_id')} runtime connector mismatch")


def audit_internal_metadata_and_final(errors: list[str]) -> None:
    for rel in [
        "reactome_style_source_identity_registry_batch068d.json",
        "reactome_style_environment_orthology_registry_batch068d.json",
        "reactome_style_command_output_contract_batch068d.json",
        "reactome_style_validator_warning_error_ledger_batch068d.json",
        "reactome_style_prior_batch_continuity_batch068d.json",
        "chromosomal_maintenance_to_controllergate_translation_matrix_batch068d.json",
        "chromosomal_maintenance_order_lock_batch068d.json",
        "sister_cohesion_baseline_registry_guard_batch068d.json",
        "chromosomal_failed_branch_closure_registry_batch068d.json",
        "manual_artifact_nuclear_pore_gate_batch068d.json",
        "repair_pathway_choice_classifier_batch068d.json",
        "homologous_transfer_guard_batch068d.json",
        "safe_abstention_apoptosis_watchdog_batch068d.json",
    ]:
        value = read_json(rel)
        expect(errors, value.get("status") == "PASS", f"{rel} not PASS")
        expect(errors, value.get("internal_metadata_only") is True or rel.startswith("sister_"), f"{rel} not marked internal metadata only")
    expect(errors, read_json("chromosomal_maintenance_order_lock_batch068d.json").get("maintenance_order_violation_count") == 0, "maintenance order violation")
    expect(errors, read_json("manual_artifact_nuclear_pore_gate_batch068d.json").get("manual_artifact_bypass_count") == 0, "manual artifact bypass")
    expect(errors, read_json("homologous_transfer_guard_batch068d.json").get("homology_used_as_patch_authority_count") == 0, "routing used as patch authority")

    final = read_json("batch068d_final_decision.json")
    expect(errors, final.get("status") == "PASS", "final status not PASS")
    expect(errors, final.get("batch068d_audit_status") == "PASS", "audit status not PASS")
    expect(errors, final.get("current_protocol") == "v2.14", "current protocol changed")
    expect(errors, final.get("issue_derived_repair_count") == 4, "issue-derived repair count changed")
    expect(errors, final.get("native_external_repair_count") == 4, "native repair count changed")
    expect(errors, final.get("external_seed_count") == 5, "external seed count mismatch")
    expect(errors, final.get("external_seed_approved_count") == 0, "external seed approved count must be zero")
    expect(errors, final.get("existing_backlog_rescanned_count") == 94, "backlog rescan count mismatch")
    expect(errors, final.get("existing_backlog_promoted_count") == 0, "backlog promoted count must be zero")
    expect(errors, final.get("command_orthology_ready_candidate_count") == 0, "command orthology ready count must be zero")
    expect(errors, final.get("top_5_next_probe_candidate_count") == 0, "top 5 next probe count must be zero")
    expect(errors, final.get("manual_artifact_waiting_candidate_count") == 3, "manual waiting final count changed")
    expect(errors, final.get("runtime_connector_waiting_candidate_count") == 1, "runtime waiting final count changed")
    expect(errors, final.get("unapproved_without_reason_count") == 0, "unapproved without reason count nonzero")
    expect(errors, final.get("next_allowed_action") == "batch068e_external_seed_source_identity_verification", "unexpected next action")
    expect(errors, final.get("exact_blocker") == "external_seed_source_identity_and_candidate_sha_verification_required", "unexpected blocker")
    for key in ["patch_generated", "patch_applied", "source_mutated", "tests_mutated", "fixtures_mutated", "config_mutated", "duplicate_replay_run", "count_gate_run", "repair_count_increment"]:
        expect(errors, final.get(key) is False, f"{key} must remain false")
    expect(errors, final.get("full_scoring") == "NOT_RUN/disallowed", "full scoring changed")
    expect(errors, final.get("memory_lift") == "not_demonstrated", "memory lift changed")
    expect(errors, final.get("self_maintaining_software") == "false/not_demonstrated", "self-maintaining changed")


def audit_public_summary(errors: list[str]) -> None:
    text = (OUT_DIR / "batch068d_summary.md").read_text(encoding="utf-8")
    expect(errors, audit_public_summary_text(text).get("status") == "PASS", "neutral public language audit failed")
    forbidden = [
        "reactome",
        "chromosomal",
        "biological",
        "torus",
        "tld",
        "tot-brot",
        "tot-bulb",
        "apoptosis",
        "cytoskeleton",
        "orthology bridge",
    ]
    hits = [term for term in forbidden if term in text.lower()]
    expect(errors, not hits, f"public summary contains internal terms: {hits}")
    expect(errors, "not repair proof" in text, "public summary must state not repair proof")


def main() -> int:
    errors: list[str] = []
    expect(errors, OUT_DIR.is_dir(), "missing Batch068d output directory")
    for rel in REQUIRED_FILES:
        expect(errors, (OUT_DIR / rel).is_file(), f"missing output {rel}")
    for rel in REQUIRED_IMPLEMENTATION_FILES:
        expect(errors, (ROOT / rel).is_file(), f"missing implementation {rel}")
    if errors:
        print("FAIL:")
        for error in errors:
            print(f"- {error}")
        return 1
    manifest = verify_manifest(OUT_DIR)
    expect(errors, manifest.get("status") == "PASS", f"SHA256SUMS failed: {manifest}")
    artifact = read_json("batch068c_artifact_sha256_verification.json")
    expect(errors, artifact.get("status") in {"PASS", "batch068c_artifact_absent_for_local_ingest"}, "unexpected Batch068c artifact status")
    if artifact.get("status") == "PASS":
        expect(errors, artifact.get("outer", {}).get("size_bytes") == 86405, "Batch068c artifact size mismatch")
        expect(errors, artifact.get("outer", {}).get("sha256") == "55c689cf343468913ea245a32fd651ed2423387efacd9933f9e3ac851e0d28cd", "Batch068c artifact SHA mismatch")
        for name, result in artifact.get("manifests", {}).items():
            expect(errors, result.get("status") == "PASS", f"Batch068c manifest failed {name}")
    audit_external_seed_intake(errors)
    audit_command_orthology(errors)
    audit_backlog_rescan(errors)
    audit_internal_metadata_and_final(errors)
    audit_public_summary(errors)
    run_check([sys.executable, "scripts/controllergate_audit.py", "--protocol", "current"], errors, "current protocol audit")
    run_check([sys.executable, "scripts/controllergate_run.py", "--protocol", "current", "--dry-run"], errors, "current protocol dry-run")
    if errors:
        print("FAIL:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Batch068d deeper source expansion and external source approval audit PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
