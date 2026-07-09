from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from controllergate.core.manifests import verify_manifest
from controllergate.core.public_summary import FORBIDDEN_PUBLIC_TERMS, audit_public_summary_text
from controllergate.core.step_contracts import validate_step_contract

OUT_NAME = "post_v2_37_hardening_batch067_universal_wrapper_hardening_implementation"
OUT_DIR = ROOT / "outputs" / OUT_NAME

REQUIRED_CORE_FILES = [
    "controllergate/core/artifacts.py",
    "controllergate/core/step_contracts.py",
    "controllergate/core/workspace_purity.py",
    "controllergate/core/command_translation.py",
    "controllergate/core/harness_origin.py",
    "controllergate/core/version_origin.py",
    "controllergate/core/runner_target.py",
    "controllergate/core/terminal_states.py",
    "controllergate/core/abstention.py",
    "controllergate/core/source_topology.py",
    "controllergate/core/proof_ledger.py",
    "controllergate/core/public_summary.py",
    "controllergate/core/environment_orthology.py",
    "controllergate/core/candidate_seed_classes.py",
    "controllergate/core/failure_translation.py",
    "controllergate/core/cross_family_homology.py",
    "controllergate/core/source_approval.py",
]

REQUIRED_CONFIGS = [
    "configs/controllergate_step_contract_schema.json",
    "configs/controllergate_default_candidate_step_contract.json",
    "configs/controllergate_deprecated_or_unbounded_step_registry.json",
    "configs/workspace_purity_policy.json",
    "configs/candidate_isolated_runtime_policy.json",
    "configs/cross_environment_orthology_schema.json",
    "configs/candidate_seed_classification_schema.json",
    "configs/failure_translation_rule_schema.json",
    "configs/environment_constraint_map_schema.json",
    "configs/controllergate_self_maintenance_runtime_wrapper_backlog.json",
    "configs/controllergate_permanent_fix_queue.json",
]

REQUIRED_OUTPUTS = [
    "batch063b_artifact_ingestion_summary.json",
    "batch063b_artifact_sha256_verification.json",
    "batch063b_result_preservation.json",
    "batch063b_boundary_preservation.json",
    "batch067_batch063b_input_contract.json",
    "reactome_style_step_contract_model_batch067.json",
    "provider_capsule_step_contract_schema_batch067.json",
    "candidate_execution_step_registry_batch067.json",
    "step_to_output_contract_registry_batch067.json",
    "deprecated_or_unbounded_step_exclusion_registry_batch067.json",
    "provider_output_verifier_contract_batch067.json",
    "reactome_to_controllergate_mapping_matrix_batch067.json",
    "workspace_purity_policy_batch067.json",
    "candidate_isolated_runtime_policy_batch067.json",
    "stale_artifact_resistance_policy_batch067.json",
    "candidate_workspace_purity_schema_batch067.json",
    "candidate_isolated_venv_schema_batch067.json",
    "global_environment_drift_prevention_policy_batch067.json",
    "command_translation_layer_policy_batch067.json",
    "candidate_command_manifest_schema_batch067.json",
    "pytest_command_translation_case_study_batch067.json",
    "command_boundary_terminal_state_registry_batch067.json",
    "command_manifest_origin_audit_batch067.json",
    "non_circular_harness_origin_policy_batch067.json",
    "harness_origin_bootstrap_schema_batch067.json",
    "harness_origin_root_of_trust_registry_batch067.json",
    "harness_origin_self_reference_blocker_policy_batch067.json",
    "harness_origin_pre_post_integrity_policy_batch067.json",
    "version_origin_policy_batch067.json",
    "safe_git_tag_acquisition_policy_batch067.json",
    "runner_target_import_origin_policy_batch067.json",
    "pytest_version_origin_case_study_preservation_batch067.json",
    "pytest_runner_target_collision_case_study_preservation_batch067.json",
    "confidence_abstention_policy_batch067.json",
    "safe_abstention_watchdog_schema_batch067.json",
    "confidence_abstention_audit_batch067.json",
    "unrecoverable_branch_explanation_policy_batch067.json",
    "loop_prevention_policy_batch067.json",
    "universal_bug_terminal_state_registry_batch067.json",
    "bug_terminal_state_contract_batch067.json",
    "candidate_reopen_condition_registry_batch067.json",
    "unrecoverable_under_current_policy_registry_batch067.json",
    "ast_topology_extrusion_policy_batch067.json",
    "ast_topology_extrusion_schema_batch067.json",
    "source_syntax_resilience_policy_batch067.json",
    "patch_gate_ast_integrity_requirement_batch067.json",
    "pytest_readonly_ast_topology_probe_preservation_batch067.json",
    "baseline_registry_snapshot_policy_batch067.json",
    "proof_ledger_forkpoint_policy_batch067.json",
    "failed_attempt_branch_record_schema_batch067.json",
    "rollback_marker_policy_batch067.json",
    "ghost_state_prevention_policy_batch067.json",
    "public_summary_guard_policy_batch067.json",
    "public_forbidden_language_audit_batch067.json",
    "public_safe_summary_batch067.md",
    "cross_environment_orthology_map_batch067.json",
    "candidate_seed_classification_gate_batch067.json",
    "orthology_transfer_registry_batch067.json",
    "failure_translation_rule_registry_batch067.json",
    "environment_constraint_map_batch067.json",
    "environment_specific_failure_signature_registry_batch067.json",
    "source_family_equivalence_registry_batch067.json",
    "provider_family_equivalence_registry_batch067.json",
    "runner_command_equivalence_registry_batch067.json",
    "orthology_transfer_safety_policy_batch067.json",
    "candidate_seed_classification_audit_batch067.json",
    "candidate_seed_promotion_policy_batch067.json",
    "probe_source_to_candidate_seed_boundary_batch067.json",
    "manual_artifact_custody_seed_intake_policy_batch067.json",
    "external_source_approval_registry_batch067.json",
    "reactome_biological_logic_to_controllergate_translation_matrix_batch067.json",
    "failure_signature_schema_batch067.json",
    "failure_signature_registry_batch067.json",
    "environment_specific_failure_classifier_batch067.json",
    "failure_surface_separation_audit_batch067.json",
    "cross_family_homology_ledger_batch067.json",
    "cross_family_homology_policy_batch067.json",
    "cross_family_homology_routing_memory_only_audit_batch067.json",
    "cross_family_homology_public_boundary_batch067.json",
    "manual_artifact_intake_log_schema_batch067.json",
    "source_discovery_provenance_schema_batch067.json",
    "source_approval_gate_policy_batch067.json",
    "probe_to_candidate_promotion_policy_batch067.json",
    "isomorphism_errata_lock_batch067.json",
    "brot_totbrot_totbulb_translation_policy_batch067.json",
    "single_system_vs_coupled_system_boundary_batch067.json",
    "environment_locator_before_patch_gate_policy_batch067.json",
    "batch067_final_decision.json",
    "batch067_core_module_upgrade_summary.json",
    "batch067_summary.md",
    "SHA256SUMS.txt",
]

REQUIRED_TESTS = [
    "tests/core/test_batch067_artifact_custody.py",
    "tests/core/test_batch067_wrapper_core.py",
    "tests/core/test_batch067_translation_layer.py",
    "tests/core/test_batch067_public_summary_guard.py",
]


def read_json(rel: str) -> dict[str, object]:
    return json.loads((OUT_DIR / rel).read_text(encoding="utf-8"))


def expect(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def run_check(args: list[str], errors: list[str], label: str) -> None:
    proc = subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=False)
    expect(errors, proc.returncode == 0, f"{label} failed: {proc.stdout[-1000:]} {proc.stderr[-1000:]}")


def audit_public_docs(errors: list[str]) -> None:
    for rel in [
        "README.md",
        "docs/current_status.md",
        "controllergate_v1_7_beta/reports/critic_review_package/shareable_summary.md",
        "docs/controllergate_self_maintenance_runtime_wrapper_roadmap.md",
        "docs/controllergate_public_readiness_plan.md",
    ]:
        path = ROOT / rel
        expect(errors, path.is_file(), f"missing public doc {rel}")
        text = path.read_text(encoding="utf-8")
        expect(errors, "Batch067 adds reusable wrapper and failure-translation infrastructure" in text, f"missing Batch067 public-safe wording in {rel}")
        hits = [term for term in FORBIDDEN_PUBLIC_TERMS + ["Reactome"] if term.lower() in text.lower()]
        expect(errors, not hits, f"public doc {rel} contains forbidden internal terms: {hits}")
        expect(errors, audit_public_summary_text(text).get("status") == "PASS", f"public summary guard failed for {rel}")


def audit_git_tracked_payload(errors: list[str]) -> None:
    proc = subprocess.run(["git", "ls-files"], cwd=ROOT, text=True, capture_output=True, check=False)
    expect(errors, proc.returncode == 0, "git ls-files failed")
    forbidden = [
        line for line in proc.stdout.splitlines()
        if (
            line.startswith(f"outputs/{OUT_NAME}/")
            or line.startswith("incoming_artifacts/")
            or line.startswith("artifact_payload/")
            or line.startswith("ControllerGate_runtime/")
        )
        and (
            line.lower().endswith((".zip", ".tar", ".tgz", ".7z", ".pyc", ".pyo", ".whl"))
            or "/__pycache__/" in line
            or "/.pytest_cache/" in line
            or line.startswith("incoming_artifacts/")
            or "ControllerGate_runtime" in line
        )
    ]
    expect(errors, not forbidden, f"forbidden tracked payloads: {forbidden[:10]}")


def main() -> int:
    errors: list[str] = []
    expect(errors, OUT_DIR.is_dir(), f"missing output directory {OUT_DIR}")
    for rel in REQUIRED_CORE_FILES + REQUIRED_CONFIGS + REQUIRED_TESTS:
        expect(errors, (ROOT / rel).is_file(), f"missing required repo file {rel}")
    for rel in REQUIRED_OUTPUTS:
        expect(errors, (OUT_DIR / rel).is_file(), f"missing required Batch067 output {rel}")
    if errors:
        print("FAIL:")
        for error in errors:
            print(f"- {error}")
        return 1

    manifest = verify_manifest(OUT_DIR)
    expect(errors, manifest.get("status") == "PASS", f"Batch067 SHA256SUMS failed: {manifest}")
    default_contract = json.loads((ROOT / "configs/controllergate_default_candidate_step_contract.json").read_text(encoding="utf-8"))
    expect(errors, validate_step_contract(default_contract).status == "PASS", "default step contract failed validation")

    artifact = read_json("batch063b_artifact_sha256_verification.json")
    ingest = read_json("batch063b_artifact_ingestion_summary.json")
    if artifact.get("status") == "batch063b_artifact_absent_for_local_ingest":
        expect(errors, ingest.get("status") == "batch063b_artifact_absent_for_local_ingest", "artifact absence not recorded consistently")
    else:
        expect(errors, artifact.get("status") == "PASS", "Batch063b artifact verification did not pass")
        expect(errors, artifact.get("outer", {}).get("size_bytes") == 125405, "Batch063b artifact size mismatch")
        expect(errors, artifact.get("outer", {}).get("sha256") == "9977b50fbe054f362dbcdf62b2aa2b4f5225ac0b5cb1305a64a2d727a6a4f26a", "Batch063b artifact SHA mismatch")
        expect(errors, artifact.get("entries", {}).get("unsafe_path_count") == 0, "Batch063b artifact unsafe paths detected")
        expect(errors, artifact.get("entries", {}).get("duplicate_path_count") == 0, "Batch063b artifact duplicate paths detected")
        manifests = artifact.get("manifests", {})
        expect(errors, manifests.get("ARTIFACT_SHA256SUMS.txt", {}).get("status") == "PASS", "artifact-level manifest failed")
        expect(errors, manifests.get("SHA256SUMS.txt", {}).get("status") == "PASS", "internal SHA256SUMS failed")
        expect(errors, ingest.get("raw_zip_bytes_ingested") is False, "raw ZIP bytes ingested")

    preservation = read_json("batch063b_result_preservation.json")
    boundary = read_json("batch063b_boundary_preservation.json")
    final = read_json("batch067_final_decision.json")
    expect(errors, preservation.get("issue_derived_repair_count") == 4, "Batch063b issue-derived count not preserved")
    expect(errors, preservation.get("native_external_repair_count") == 4, "Batch063b native count not preserved")
    expect(errors, preservation.get("pytest_version_origin_classification") == "pytest_version_origin_missing_tags", "Pytest version-origin boundary changed")
    expect(errors, preservation.get("pytest_runner_target_import_origin_classification") == "runner_target_collision_unresolved_self_runner", "Pytest runner-target boundary changed")
    expect(errors, preservation.get("pytest_command_boundary_classification") == "pytest_command_boundary_blocked_version_origin", "Pytest command-boundary changed")
    expect(errors, preservation.get("pytest_prerepair_replay_classification") == "blocked_target_command_invalid", "Pytest pre-repair replay boundary changed")
    expect(errors, preservation.get("pytest_future_patch_license_state") == "pytest_patch_license_closed_command_boundary_blocked", "Pytest patch-license boundary changed")
    for key in ["patch_generated", "patch_applied", "source_mutated", "tests_mutated", "fixtures_mutated", "duplicate_replay_run", "count_gate_run", "repair_count_increment"]:
        expect(errors, boundary.get(key) is False, f"Batch067 boundary expected {key}=false")
        expect(errors, final.get(key) is False, f"Batch067 final expected {key}=false")
    expect(errors, final.get("issue_derived_repair_count") == 4, "issue-derived repair count changed")
    expect(errors, final.get("native_external_repair_count") == 4, "native external repair count changed")
    expect(errors, final.get("full_scoring") == "NOT_RUN/disallowed", "full scoring changed")
    expect(errors, final.get("memory_lift") == "not_demonstrated", "memory lift changed")
    expect(errors, final.get("self_maintaining_software") == "false/not_demonstrated", "self-maintaining claim changed")
    expect(errors, final.get("next_allowed_action") == "batch063c_pytest_command_boundary_followup", "unexpected next allowed action")
    expect(errors, final.get("wrapper_hardening_complete_enough_for_batch063c") is True, "wrapper hardening not marked complete enough for Batch063c")

    orthology = read_json("cross_environment_orthology_map_batch067.json")
    seed_gate = read_json("candidate_seed_classification_gate_batch067.json")
    homology = read_json("cross_family_homology_ledger_batch067.json")
    source_approval = read_json("external_source_approval_registry_batch067.json")
    translation_matrix = read_json("reactome_biological_logic_to_controllergate_translation_matrix_batch067.json")
    public_boundary = read_json("cross_family_homology_public_boundary_batch067.json")
    expect(errors, orthology.get("status") == "PASS" and orthology.get("records"), "orthology map missing records")
    expect(errors, seed_gate.get("orthology_transfer_requires_promotion") is True, "orthology-transfer seed promotion not enforced")
    expect(errors, seed_gate.get("probe_only_environmental_sources_blocked") is True, "probe-only sources not blocked")
    expect(errors, homology.get("routing_memory_only") is True, "cross-family homology not routing-only")
    for record in homology.get("records", []):
        expect(errors, record.get("patch_authority_allowed") is False, "homology record authorizes patch generation")
        expect(errors, record.get("repair_proof_allowed") is False, "homology record authorizes repair proof")
        expect(errors, record.get("count_gate_evidence_allowed") is False, "homology record authorizes count gate")
    expect(errors, source_approval.get("approved_unused_candidate_count") == 0, "source approval registry unexpectedly approved candidates")
    expect(errors, translation_matrix.get("internal_design_metadata_only") is True and translation_matrix.get("public_claim_allowed") is False, "translation matrix boundary invalid")
    expect(errors, public_boundary.get("public_claim_allowed") is False, "homology public boundary allows public claim")

    audit_public_docs(errors)
    audit_git_tracked_payload(errors)
    run_check([sys.executable, "scripts/controllergate_audit.py", "--protocol", "current"], errors, "current protocol audit")
    run_check([sys.executable, "scripts/controllergate_run.py", "--protocol", "current", "--dry-run"], errors, "current protocol dry-run")

    if errors:
        print("FAIL:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Batch067 universal wrapper hardening implementation audit PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
