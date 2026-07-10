from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from controllergate.core.manifests import verify_manifest
from controllergate.core.public_summary import audit_public_summary_text

OUT_NAME = "post_v2_37_hardening_batch068f_candidate_sha_resolution_intake"
OUT_DIR = ROOT / "outputs" / OUT_NAME

EXTERNAL_LEADS = {
    "numpy_21994_ufunc_overflow",
    "pytest_11058_unraisable_exception",
    "black_2992_blackd_path_separator",
    "jinja_1628_lexer_py311",
    "scipy_16783_lbfgsb_tolerance",
}

REQUIRED_OUTPUTS = [
    "batch068e_artifact_ingestion_summary.json",
    "batch068e_artifact_sha256_verification.json",
    "batch068e_result_preservation.json",
    "batch068e_candidate_sha_request_preservation.json",
    "candidate_sha_resolution_engine_policy_batch068f.json",
    "candidate_sha_resolution_confidence_schema_batch068f.json",
    "decision_time_candidate_epoch_policy_batch068f.json",
    "acceptable_candidate_sha_source_policy_batch068f.json",
    "release_tag_resolution_policy_batch068f.json",
    "external_seed_candidate_sha_resolution_results_batch068f.json",
    "external_seed_tier_update_registry_batch068f.json",
    "external_seed_sha_unresolved_registry_batch068f.json",
    "external_seed_verified_sha_registry_batch068f.json",
    "existing_backlog_candidate_sha_resolution_budget_batch068f.json",
    "existing_backlog_candidate_sha_resolution_results_batch068f.json",
    "existing_backlog_verified_sha_registry_batch068f.json",
    "existing_backlog_unresolved_sha_registry_batch068f.json",
    "tier2_metadata_command_orthology_dry_run_batch068f.json",
    "tier2_command_orthology_readiness_registry_batch068f.json",
    "tier3_candidate_promotion_registry_batch068f.json",
    "controllergate_universalization_gap_ledger_batch068f.json",
    "batch_local_to_core_promotion_registry_batch068f.json",
    "wrapper_capability_maturity_matrix_batch068f.json",
    "underdeveloped_mechanism_backlog_batch068f.json",
    "self_maintenance_autonomy_gap_analysis_batch068f.json",
    "self_maintenance_bottleneck_reduction_plan_batch068f.json",
    "agnostic_provenance_lock_scaffold_batch068f.json",
    "live_telemetry_translation_scaffold_batch068f.json",
    "shadow_materialization_sandbox_scaffold_batch068f.json",
    "runtime_substrate_connector_registry_scaffold_batch068f.json",
    "live_rollback_hotswap_policy_scaffold_batch068f.json",
    "agi_runtime_wrapper_activation_watchdog_batch068f.json",
    "runtime_wrapper_activation_watchdog_status_batch068f.json",
    "reactome_style_source_identity_registry_batch068f.json",
    "reactome_style_environment_orthology_registry_batch068f.json",
    "reactome_style_prior_batch_continuity_batch068f.json",
    "chromosomal_maintenance_order_lock_batch068f.json",
    "sister_cohesion_baseline_registry_guard_batch068f.json",
    "chromosomal_failed_branch_closure_registry_batch068f.json",
    "homologous_transfer_guard_batch068f.json",
    "safe_abstention_apoptosis_watchdog_batch068f.json",
    "controllergate_full_redundancy_inventory_batch068f.json",
    "controllergate_version_mechanism_genealogy_batch068f.json",
    "controllergate_batch_to_capability_matrix_batch068f.json",
    "controllergate_mechanism_family_deduplication_map_batch068f.json",
    "controllergate_state_name_drift_audit_batch068f.json",
    "controllergate_batch_output_redundancy_audit_batch068f.json",
    "controllergate_config_schema_canonicalization_plan_batch068f.json",
    "controllergate_audit_workflow_redundancy_audit_batch068f.json",
    "controllergate_public_claim_boundary_drift_audit_batch068f.json",
    "controllergate_redundancy_decision_ledger_batch068f.json",
    "batch068f_handoff_plan.json",
    "batch068f_final_decision.json",
    "batch068f_summary.md",
    "SHA256SUMS.txt",
]

REQUIRED_IMPLEMENTATION_FILES = [
    "controllergate/core/candidate_sha_resolver.py",
    "controllergate/core/issue_epoch_snapshot.py",
    "controllergate/core/tag_release_resolver.py",
    "controllergate/core/commit_object_verifier.py",
    "controllergate/core/sha_resolution_confidence.py",
    "controllergate/core/universalization_audit.py",
    "controllergate/core/agnostic_provenance_lock.py",
    "controllergate/core/live_telemetry_translation.py",
    "controllergate/core/shadow_materialization.py",
    "controllergate/core/runtime_substrate_connector.py",
    "controllergate/core/live_rollback_hotswap.py",
    "controllergate/core/runtime_wrapper_activation_watchdog.py",
    "configs/candidate_sha_resolution_engine_policy.json",
    "configs/candidate_sha_resolution_confidence_schema.json",
    "configs/decision_time_candidate_epoch_policy.json",
    "configs/acceptable_candidate_sha_source_policy.json",
    "configs/agnostic_provenance_lock_scaffold.json",
    "configs/live_telemetry_translation_scaffold.json",
    "configs/shadow_materialization_sandbox_scaffold.json",
    "configs/runtime_substrate_connector_registry_scaffold.json",
    "configs/live_rollback_hotswap_policy_scaffold.json",
    "configs/agi_runtime_wrapper_activation_watchdog.json",
    "scripts/generate_batch068f_candidate_sha_resolution_intake.py",
    "scripts/audit_batch068f_candidate_sha_resolution_intake.py",
    ".github/workflows/post_v2_37_hardening_batch068f_candidate_sha_resolution_intake.yml",
]

FORBIDDEN_ACTIVE_STATES = {
    "active_executed",
    "live_patch_enabled",
    "device_hook_enabled",
    "memory_dump_collected",
    "hot_swap_enabled",
}


def forbidden_active_value_hits(value: Any) -> list[str]:
    hits: list[str] = []
    if isinstance(value, str):
        if value in FORBIDDEN_ACTIVE_STATES:
            hits.append(value)
    elif isinstance(value, dict):
        for child in value.values():
            hits.extend(forbidden_active_value_hits(child))
    elif isinstance(value, list):
        for child in value:
            hits.extend(forbidden_active_value_hits(child))
    return hits


def read_json(name: str | Path) -> Any:
    path = OUT_DIR / name if isinstance(name, str) else name
    return json.loads(path.read_text(encoding="utf-8"))


def expect(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def run_check(args: list[str], errors: list[str], label: str) -> None:
    proc = subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=False)
    expect(errors, proc.returncode == 0, f"{label} failed: {proc.stdout[-1200:]} {proc.stderr[-1200:]}")


def audit_artifact(errors: list[str]) -> None:
    artifact = read_json("batch068e_artifact_sha256_verification.json")
    expect(
        errors,
        artifact.get("status") in {"PASS", "batch068e_artifact_absent_preserved_committed_outputs"},
        f"unexpected Batch068e artifact status {artifact.get('status')}",
    )
    if artifact.get("status") == "PASS":
        expect(errors, artifact.get("outer", {}).get("size_bytes") == 59330, "Batch068e artifact size mismatch")
        expect(
            errors,
            artifact.get("outer", {}).get("sha256") == "fcc2a122d79110fd6a29d0b8292547a983f6eaaa0f68cd121ad4c1c111dad656",
            "Batch068e artifact SHA mismatch",
        )
        expect(errors, artifact.get("nested_archive_cache_venv_pyc_payload_count") == 0, "nested archive/cache payloads detected")
        for name, result in artifact.get("manifests", {}).items():
            expect(errors, result.get("status") == "PASS", f"Batch068e manifest failed {name}")


def audit_external_sha_resolution(errors: list[str]) -> None:
    results = read_json("external_seed_candidate_sha_resolution_results_batch068f.json")
    verified = read_json("external_seed_verified_sha_registry_batch068f.json")
    unresolved = read_json("external_seed_sha_unresolved_registry_batch068f.json")
    expect(errors, results.get("status") == "PASS", "external resolution results not PASS")
    expect(errors, results.get("candidate_count") == 5, "external candidate count must be five")
    seen = {row.get("candidate_id") for row in results.get("records", [])}
    expect(errors, seen == EXTERNAL_LEADS, f"external lead set mismatch {seen}")
    expect(errors, verified.get("verified_count") + unresolved.get("unresolved_count") == 5, "verified+unresolved count mismatch")
    for result in results.get("records", []):
        cid = result["candidate_id"]
        decision = result["decision"]
        expect(errors, len(result.get("attempts", [])) >= 1, f"{cid} missing resolution attempts")
        expect(errors, decision.get("approved_for_test_execution") is False, f"{cid} test execution approved")
        expect(errors, decision.get("approved_for_patch_generation") is False, f"{cid} patch generation approved")
        expect(errors, decision.get("confidence") in {
            "exact_reproduction_commit",
            "strong_versioned_release_commit",
            "decision_time_epoch_snapshot_commit",
            "unresolved_sha_required",
            "weak_sha_hint_requires_manual_review",
            "rejected_forbidden_source",
        }, f"{cid} invalid confidence")
        record = result["verified_commit_object_record"]
        expect(errors, record.get("checkout_performed") is False, f"{cid} checkout performed")
        expect(errors, record.get("raw_clone_committed") is False, f"{cid} raw clone committed")
        for rel in [
            f"external_seed_sha_resolution/{cid}/candidate_sha_resolution_attempts.json",
            f"external_seed_sha_resolution/{cid}/candidate_sha_resolution_decision.json",
            f"external_seed_sha_resolution/{cid}/verified_commit_object_record.json",
            f"external_seed_sha_resolution/{cid}/decision_time_epoch_boundary.json",
            f"external_seed_sha_resolution/{cid}/source_identity_tier_update.json",
            f"external_seed_sha_resolution/{cid}/terminal_state.json",
        ]:
            expect(errors, (OUT_DIR / rel).is_file(), f"{cid} missing {rel}")


def audit_backlog_and_tier2(errors: list[str]) -> None:
    budget = read_json("existing_backlog_candidate_sha_resolution_budget_batch068f.json")
    backlog = read_json("existing_backlog_candidate_sha_resolution_results_batch068f.json")
    tier2 = read_json("tier2_metadata_command_orthology_dry_run_batch068f.json")
    readiness = read_json("tier2_command_orthology_readiness_registry_batch068f.json")
    tier3 = read_json("tier3_candidate_promotion_registry_batch068f.json")
    expect(errors, budget.get("status") == "PASS", "backlog budget not PASS")
    expect(errors, budget.get("attempted_count") == 20, "expected top-20 backlog attempts")
    expect(errors, backlog.get("attempted_count") == 20, "backlog attempted count mismatch")
    expect(errors, tier2.get("status") == "PASS", "tier2 dry-run not PASS")
    expect(errors, tier2.get("metadata_only") is True, "tier2 dry-run must be metadata-only")
    expect(errors, tier2.get("tests_executed") == 0, "tier2 dry-run executed tests")
    expect(errors, tier2.get("patch_generated") is False, "tier2 dry-run generated patch")
    expect(errors, readiness.get("ready_for_tier3_count") == 0, "Tier 3 readiness should remain zero")
    expect(errors, tier3.get("tier3_candidate_count") == 0, "Tier 3 promotion must remain zero")


def audit_runtime_scaffolds(errors: list[str]) -> None:
    for rel in [
        "agnostic_provenance_lock_scaffold_batch068f.json",
        "live_telemetry_translation_scaffold_batch068f.json",
        "shadow_materialization_sandbox_scaffold_batch068f.json",
        "runtime_substrate_connector_registry_scaffold_batch068f.json",
        "live_rollback_hotswap_policy_scaffold_batch068f.json",
    ]:
        value = read_json(rel)
        expect(errors, value.get("status") == "scaffolded_with_config_and_audit", f"{rel} wrong scaffold status")
        expect(errors, value.get("activation_state") == "not_run_precondition_blocked", f"{rel} active unexpectedly")
        hits = forbidden_active_value_hits(value)
        expect(errors, not hits, f"{rel} contains active states {hits}")
        expect(errors, value.get("patch_authority") is False, f"{rel} patch authority enabled")
    watchdog = read_json("runtime_wrapper_activation_watchdog_status_batch068f.json")
    expect(errors, watchdog.get("issue_derived_repair_count") == 4, "watchdog issue count changed")
    expect(errors, watchdog.get("activation_threshold_issue_derived_repairs") == 20, "watchdog threshold changed")
    expect(errors, watchdog.get("activation_state") == "activation_threshold_not_met", "watchdog activation state wrong")
    expect(errors, watchdog.get("runtime_wrapper_activation_allowed") is False, "runtime wrapper activation allowed")
    expect(errors, watchdog.get("live_device_repair_enabled") is False, "live device repair enabled")


def audit_universalization_and_redundancy(errors: list[str]) -> None:
    universal = read_json("controllergate_universalization_gap_ledger_batch068f.json")
    redundancy = read_json("controllergate_redundancy_decision_ledger_batch068f.json")
    state_drift = read_json("controllergate_state_name_drift_audit_batch068f.json")
    claim = read_json("controllergate_public_claim_boundary_drift_audit_batch068f.json")
    inventory = read_json("controllergate_full_redundancy_inventory_batch068f.json")
    expect(errors, universal.get("status") == "PASS", "universalization gap ledger not PASS")
    expect(errors, universal.get("tracked_file_count", 0) > 0, "universalization ledger empty")
    expect(errors, inventory.get("safe_to_delete_now_count") == 0, "safe-to-delete count must be zero")
    expect(errors, redundancy.get("harmful_redundancy_count") == 0, "harmful redundancy must be zero in this classification-only batch")
    expect(errors, redundancy.get("safe_to_delete_now_count") == 0, "redundancy safe-to-delete count must be zero")
    expect(errors, redundancy.get("future_consolidation_batch_recommended") is True, "future consolidation not recommended")
    expect(errors, state_drift.get("state_name_conflict_count") == 0, "state name conflict count must be zero")
    expect(errors, claim.get("public_claim_boundary_violation_count") == 0, "public claim boundary violation")


def audit_interlocks_and_final(errors: list[str]) -> None:
    for rel in [
        "reactome_style_source_identity_registry_batch068f.json",
        "reactome_style_environment_orthology_registry_batch068f.json",
        "reactome_style_prior_batch_continuity_batch068f.json",
        "chromosomal_maintenance_order_lock_batch068f.json",
        "sister_cohesion_baseline_registry_guard_batch068f.json",
        "chromosomal_failed_branch_closure_registry_batch068f.json",
        "homologous_transfer_guard_batch068f.json",
        "safe_abstention_apoptosis_watchdog_batch068f.json",
    ]:
        value = read_json(rel)
        expect(errors, value.get("status") == "PASS", f"{rel} not PASS")
        expect(errors, value.get("internal_metadata_only") is True, f"{rel} not metadata-only")
    expect(errors, read_json("chromosomal_maintenance_order_lock_batch068f.json").get("maintenance_order_violation_count") == 0, "order lock violation")
    expect(errors, read_json("homologous_transfer_guard_batch068f.json").get("homology_used_as_patch_authority_count") == 0, "transfer guard used as patch authority")
    final = read_json("batch068f_final_decision.json")
    expect(errors, final.get("status") == "PASS", "final status not PASS")
    expect(errors, final.get("current_protocol") == "v2.14", "current protocol changed")
    expect(errors, final.get("external_seed_count") == 5, "external seed count mismatch")
    expect(errors, final.get("external_seed_sha_resolution_attempt_count") == 5, "external SHA attempt count mismatch")
    expect(errors, final.get("external_seed_tier3_count") == 0, "external Tier 3 must remain zero")
    expect(errors, final.get("target_tests_executed") == 0, "target tests executed")
    for key in ["patch_generated", "patch_applied", "source_mutated", "tests_mutated", "duplicate_replay_run", "count_gate_run", "repair_count_increment"]:
        expect(errors, final.get(key) is False, f"{key} must remain false")
    expect(errors, final.get("native_external_repair_count") == 4, "native count changed")
    expect(errors, final.get("issue_derived_repair_count") == 4, "issue-derived count changed")
    expect(errors, final.get("full_scoring") == "NOT_RUN/disallowed", "full scoring changed")
    expect(errors, final.get("memory_lift") == "not_demonstrated", "memory lift changed")
    expect(errors, final.get("self_maintaining_software") == "false/not_demonstrated", "self-maintaining changed")
    expect(errors, final.get("runtime_wrapper_activation_allowed") is False, "runtime wrapper activation allowed")
    expect(errors, final.get("state_name_conflict_count") == 0, "state conflict count changed")
    expect(errors, final.get("public_claim_boundary_violation_count") == 0, "public claim violation count changed")
    expect(errors, final.get("safe_to_delete_now_count") == 0, "safe-to-delete count changed")


def audit_public_summary(errors: list[str]) -> None:
    text = (OUT_DIR / "batch068f_summary.md").read_text(encoding="utf-8")
    expect(errors, audit_public_summary_text(text).get("status") == "PASS", "public summary language audit failed")
    lowered = text.lower()
    for forbidden in ["reactome", "chromosomal", "biological", "torus", "tld", "tot-brot", "tot-bulb", "apoptosis"]:
        expect(errors, forbidden not in lowered, f"public summary contains {forbidden}")
    expect(errors, "not repair proof" in lowered, "public summary must state not repair proof")


def main() -> int:
    errors: list[str] = []
    expect(errors, OUT_DIR.is_dir(), "missing Batch068f output directory")
    for rel in REQUIRED_OUTPUTS:
        expect(errors, (OUT_DIR / rel).is_file(), f"missing output {rel}")
    for rel in REQUIRED_IMPLEMENTATION_FILES:
        expect(errors, (ROOT / rel).is_file(), f"missing implementation/config {rel}")
    if not errors:
        manifest = verify_manifest(OUT_DIR)
        expect(errors, manifest.get("status") == "PASS", f"SHA256SUMS failed: {manifest}")
    if not errors:
        audit_artifact(errors)
        audit_external_sha_resolution(errors)
        audit_backlog_and_tier2(errors)
        audit_runtime_scaffolds(errors)
        audit_universalization_and_redundancy(errors)
        audit_interlocks_and_final(errors)
        audit_public_summary(errors)
        run_check([sys.executable, "scripts/controllergate_audit.py", "--protocol", "current"], errors, "current protocol audit")
        run_check([sys.executable, "scripts/controllergate_run.py", "--protocol", "current", "--dry-run"], errors, "current protocol dry-run")
    if errors:
        print("FAIL:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Batch068f candidate SHA resolution intake audit PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
