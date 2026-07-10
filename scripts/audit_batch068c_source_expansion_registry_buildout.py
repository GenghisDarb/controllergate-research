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
from controllergate.core.source_expansion_ranking import ALLOWED_SOURCE_EXPANSION_APPROVAL_STATUSES

OUT_NAME = "post_v2_37_hardening_batch068c_source_expansion_registry_buildout"
OUT_DIR = ROOT / "outputs" / OUT_NAME

REQUIRED_FILES = [
    "batch068b_artifact_ingestion_summary.json",
    "batch068b_artifact_sha256_verification.json",
    "batch068b_result_preservation.json",
    "batch068b_manual_artifact_waiting_state_preservation.json",
    "batch068b_manual_artifact_request_preservation.json",
    "batch068b_runtime_connector_request_preservation.json",
    "batch068b_claim_boundary_preservation.json",
    "manual_artifact_waiting_state_registry_batch068c.json",
    "runtime_connector_waiting_state_registry_batch068c.json",
    "do_not_fabricate_manual_command_artifacts_policy_batch068c.json",
    "batch068c_source_expansion_scope.json",
    "batch068c_existing_seed_backlog_scan.json",
    "batch068c_unapproved_seed_reconsideration_matrix.json",
    "batch068c_new_source_expansion_policy.json",
    "native_command_readiness_score_schema_batch068c.json",
    "source_expansion_candidate_inventory_batch068c.json",
    "native_command_ready_candidate_ranking_batch068c.json",
    "top_20_source_expansion_candidates_batch068c.json",
    "top_10_native_command_ready_candidates_batch068c.json",
    "top_5_next_probe_candidates_batch068c.json",
    "source_expansion_approval_status_registry_batch068c.json",
    "manual_artifact_backlog_preservation_batch068c.json",
    "runtime_connector_backlog_preservation_batch068c.json",
    "external_source_approval_backlog_preservation_batch068c.json",
    "universal_interlock_law_manifest_batch068c.json",
    "step_to_output_contract_registry_batch068c.json",
    "failed_attempt_branch_record_registry_batch068c.json",
    "cross_environment_orthology_map_batch068c.json",
    "ast_topology_extrusion_map_batch068c.json",
    "elbow_patch_authorization_gate_batch068c.json",
    "reward_signal_memory_boundary_batch068c.json",
    "batch068c_handoff_plan.json",
    "reactome_style_stable_candidate_identity_map_batch068c.json",
    "reactome_species_to_environment_orthology_matrix_batch068c.json",
    "reactome_pathway_to_candidate_output_contract_batch068c.json",
    "reactome_style_validator_warning_error_ledger_batch068c.json",
    "reactome_style_prior_batch_continuity_check_batch068c.json",
    "reactome_curated_vs_inferred_candidate_boundary_batch068c.json",
    "multi_view_candidate_projection_matrix_batch068c.json",
    "reactome_to_controllergate_translation_matrix_batch068c.json",
    "chromosomal_maintenance_to_controllergate_translation_matrix_batch068c.json",
    "chromosomal_maintenance_order_lock_batch068c.json",
    "sister_cohesion_baseline_registry_guard_batch068c.json",
    "chromosomal_failed_branch_closure_registry_batch068c.json",
    "manual_artifact_nuclear_pore_gate_batch068c.json",
    "repair_pathway_choice_classifier_batch068c.json",
    "homologous_transfer_guard_batch068c.json",
    "safe_abstention_apoptosis_watchdog_batch068c.json",
    "batch068c_final_decision.json",
    "batch068c_summary.md",
    "SHA256SUMS.txt",
]


def read_json(name: str) -> Any:
    return json.loads((OUT_DIR / name).read_text(encoding="utf-8"))


def expect(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def run_check(args: list[str], errors: list[str], label: str) -> None:
    proc = subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=False)
    expect(errors, proc.returncode == 0, f"{label} failed: {proc.stdout[-1200:]} {proc.stderr[-1200:]}")


def audit_candidate_inventory(errors: list[str]) -> None:
    inventory = read_json("source_expansion_candidate_inventory_batch068c.json")
    approval = read_json("source_expansion_approval_status_registry_batch068c.json")
    expect(errors, inventory.get("status") == "PASS", "candidate inventory not PASS")
    expect(errors, approval.get("status") == "PASS", "approval registry not PASS")
    records = approval.get("records", [])
    expect(errors, len(records) == inventory.get("candidate_count"), "approval registry count mismatch")
    for row in records:
        status = row.get("approval_status")
        expect(errors, status in ALLOWED_SOURCE_EXPANSION_APPROVAL_STATUSES, f"{row.get('candidate_id')} invalid status {status}")
        expect(errors, status != "unapproved_without_reason", f"{row.get('candidate_id')} unapproved without reason")
        if status != "approved_for_batch069c_provider_command_probe":
            expect(errors, bool(row.get("exact_blocker_if_not_approved")), f"{row.get('candidate_id')} missing exact blocker")
            expect(errors, bool(row.get("reopen_condition")), f"{row.get('candidate_id')} missing reopen condition")
    top20 = read_json("top_20_source_expansion_candidates_batch068c.json")
    top10 = read_json("top_10_native_command_ready_candidates_batch068c.json")
    top5 = read_json("top_5_next_probe_candidates_batch068c.json")
    expect(errors, top20.get("candidate_count", 0) >= 1 or top20.get("shortage_recorded") is True, "top20 missing without shortage")
    expect(errors, top10.get("candidate_count", 0) >= 1 or top10.get("shortage_recorded") is True, "top10 missing without shortage")
    expect(errors, top5.get("candidate_count", 0) >= 1 or top5.get("shortage_recorded") is True, "top5 missing without shortage")


def audit_backlogs_and_interlocks(errors: list[str]) -> None:
    manual = read_json("manual_artifact_waiting_state_registry_batch068c.json")
    runtime = read_json("runtime_connector_waiting_state_registry_batch068c.json")
    expect(errors, manual.get("waiting_candidate_count") == 3, "manual waiting count changed")
    expect(errors, runtime.get("waiting_candidate_count") == 1, "runtime waiting count changed")
    policy = read_json("do_not_fabricate_manual_command_artifacts_policy_batch068c.json")
    expect(errors, policy.get("workflow_hints_are_not_approved_command_artifacts") is True, "workflow hints allowed as command artifacts")
    for rel in [
        "universal_interlock_law_manifest_batch068c.json",
        "step_to_output_contract_registry_batch068c.json",
        "failed_attempt_branch_record_registry_batch068c.json",
        "cross_environment_orthology_map_batch068c.json",
        "ast_topology_extrusion_map_batch068c.json",
        "reward_signal_memory_boundary_batch068c.json",
    ]:
        value = read_json(rel)
        expect(errors, value.get("status") == "PASS", f"{rel} not PASS")
        expect(errors, value.get("batch068c_audit_status") == "PASS", f"{rel} not marked preserved")
    elbow = read_json("elbow_patch_authorization_gate_batch068c.json")
    expect(errors, elbow.get("patch_generation_allowed") is False, "elbow gate allowed patch generation")


def audit_mapping_addenda(errors: list[str]) -> None:
    stable = read_json("reactome_style_stable_candidate_identity_map_batch068c.json")
    env = read_json("reactome_species_to_environment_orthology_matrix_batch068c.json")
    contracts = read_json("reactome_pathway_to_candidate_output_contract_batch068c.json")
    validator = read_json("reactome_style_validator_warning_error_ledger_batch068c.json")
    continuity = read_json("reactome_style_prior_batch_continuity_check_batch068c.json")
    curated = read_json("reactome_curated_vs_inferred_candidate_boundary_batch068c.json")
    multi = read_json("multi_view_candidate_projection_matrix_batch068c.json")
    translation = read_json("reactome_to_controllergate_translation_matrix_batch068c.json")
    for name, value in [
        ("stable", stable),
        ("env", env),
        ("contracts", contracts),
        ("validator", validator),
        ("continuity", continuity),
        ("curated", curated),
        ("multi", multi),
        ("translation", translation),
    ]:
        expect(errors, value.get("status") == "PASS", f"mapping addendum {name} not PASS")
    expect(errors, stable.get("candidate_alias_duplicate_count") == 0, "duplicate candidate alias count nonzero")
    expect(errors, continuity.get("readiness_state_changed_without_evidence_count") == 0, "readiness changed without evidence")
    for row in curated.get("records", []):
        if row.get("boundary_classification") in {"orthology_inferred_routing_only", "diagnostic_only", "manual_artifact_pending", "runtime_connector_pending"}:
            expect(errors, row.get("patch_authority") is False, f"{row.get('candidate_id')} got patch authority")
    expect(errors, len(multi.get("records", [])) >= 1, "top candidates lack multi-view projection")

    chrom = read_json("chromosomal_maintenance_to_controllergate_translation_matrix_batch068c.json")
    order = read_json("chromosomal_maintenance_order_lock_batch068c.json")
    baseline = read_json("sister_cohesion_baseline_registry_guard_batch068c.json")
    closure = read_json("chromosomal_failed_branch_closure_registry_batch068c.json")
    gate = read_json("manual_artifact_nuclear_pore_gate_batch068c.json")
    pathway = read_json("repair_pathway_choice_classifier_batch068c.json")
    transfer = read_json("homologous_transfer_guard_batch068c.json")
    abstention = read_json("safe_abstention_apoptosis_watchdog_batch068c.json")
    for name, value in [
        ("chromosomal_translation", chrom),
        ("order", order),
        ("baseline", baseline),
        ("closure", closure),
        ("gate", gate),
        ("pathway", pathway),
        ("transfer", transfer),
        ("abstention", abstention),
    ]:
        expect(errors, value.get("status") == "PASS", f"maintenance addendum {name} not PASS")
    expect(errors, order.get("maintenance_order_violation_count") == 0, "maintenance order violation")
    expect(errors, closure.get("blocked_candidate_without_branch_record_count") == 0, "blocked candidate missing closure")
    expect(errors, gate.get("manual_artifact_bypass_count") == 0, "manual artifact bypass")
    expect(errors, transfer.get("homology_used_as_patch_authority_count") == 0, "homology used as patch authority")


def audit_final(errors: list[str]) -> None:
    final = read_json("batch068c_final_decision.json")
    expect(errors, final.get("status") == "PASS", "final status not PASS")
    expect(errors, final.get("batch068c_audit_status") == "PASS", "audit status not PASS")
    expect(errors, final.get("current_protocol") == "v2.14", "current protocol changed")
    expect(errors, final.get("issue_derived_repair_count") == 4, "issue-derived count changed")
    expect(errors, final.get("native_external_repair_count") == 4, "native external count changed")
    for key in ["patch_generated", "patch_applied", "source_mutated", "tests_mutated", "fixtures_mutated", "config_mutated", "duplicate_replay_run", "count_gate_run", "repair_count_increment"]:
        expect(errors, final.get(key) is False, f"{key} must remain false")
    for key in [
        "unapproved_without_reason_count",
        "readiness_state_changed_without_evidence_count",
        "orthology_used_as_patch_authority_count",
        "manual_pending_promoted_count",
        "runtime_pending_promoted_count",
        "blocked_candidate_without_branch_record_count",
        "manual_artifact_bypass_count",
        "homology_used_as_patch_authority_count",
        "maintenance_order_violation_count",
    ]:
        expect(errors, final.get(key) == 0, f"{key} must be 0")
    expect(errors, final.get("full_scoring") == "NOT_RUN/disallowed", "full scoring changed")
    expect(errors, final.get("memory_lift") == "not_demonstrated", "memory lift changed")
    expect(errors, final.get("self_maintaining_software") == "false/not_demonstrated", "self-maintaining changed")


def audit_public_summary(errors: list[str]) -> None:
    text = (OUT_DIR / "batch068c_summary.md").read_text(encoding="utf-8")
    expect(errors, audit_public_summary_text(text).get("status") == "PASS", "neutral public language audit failed")
    forbidden = [
        "reactome",
        "chromosomal",
        "biological",
        "sister chromatid",
        "cohesin",
        "centromere",
        "apoptosis",
        "repair fork",
        "mcm",
        "nuclear pore",
        "torus",
        "tld",
        "tot-brot",
        "tot-bulb",
    ]
    hits = [term for term in forbidden if term in text.lower()]
    expect(errors, not hits, f"public summary contains internal terms: {hits}")
    expect(errors, "not repair proof" in text, "public summary must state not repair proof")


def main() -> int:
    errors: list[str] = []
    expect(errors, OUT_DIR.is_dir(), "missing Batch068c output directory")
    for rel in REQUIRED_FILES:
        expect(errors, (OUT_DIR / rel).is_file(), f"missing output {rel}")
    for rel in [
        "controllergate/core/source_expansion_ranking.py",
        "scripts/generate_batch068c_source_expansion_registry_buildout.py",
        "scripts/audit_batch068c_source_expansion_registry_buildout.py",
        ".github/workflows/post_v2_37_hardening_batch068c_source_expansion_registry_buildout.yml",
    ]:
        expect(errors, (ROOT / rel).is_file(), f"missing implementation {rel}")
    if errors:
        print("FAIL:")
        for error in errors:
            print(f"- {error}")
        return 1
    manifest = verify_manifest(OUT_DIR)
    expect(errors, manifest.get("status") == "PASS", f"SHA256SUMS failed: {manifest}")
    artifact = read_json("batch068b_artifact_sha256_verification.json")
    expect(errors, artifact.get("status") in {"PASS", "batch068b_artifact_absent_for_local_ingest"}, "unexpected Batch068b artifact status")
    if artifact.get("status") == "PASS":
        expect(errors, artifact.get("outer", {}).get("size_bytes") == 49136, "Batch068b artifact size mismatch")
        expect(errors, artifact.get("outer", {}).get("sha256") == "8efb7b5e79de431075bd25f0eda4cf5eac43eb5c29486e8052fa63aaaa8c51a8", "Batch068b artifact SHA mismatch")
        for name, result in artifact.get("manifests", {}).items():
            expect(errors, result.get("status") == "PASS", f"Batch068b manifest failed {name}")
    audit_candidate_inventory(errors)
    audit_backlogs_and_interlocks(errors)
    audit_mapping_addenda(errors)
    audit_final(errors)
    audit_public_summary(errors)
    run_check([sys.executable, "scripts/controllergate_audit.py", "--protocol", "current"], errors, "current protocol audit")
    run_check([sys.executable, "scripts/controllergate_run.py", "--protocol", "current", "--dry-run"], errors, "current protocol dry-run")
    if errors:
        print("FAIL:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Batch068c source expansion registry buildout audit PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
