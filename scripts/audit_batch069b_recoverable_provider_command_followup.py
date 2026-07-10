from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from controllergate.core.ast_topology_extrusion import validate_ast_topology_record
from controllergate.core.cross_environment_orthology import validate_cross_environment_record
from controllergate.core.failed_branch_closure import validate_failed_branch_record
from controllergate.core.manifests import verify_manifest
from controllergate.core.public_summary import FORBIDDEN_PUBLIC_TERMS, audit_public_summary_text

OUT_NAME = "post_v2_37_hardening_batch069b_recoverable_provider_command_followup"
OUT_DIR = ROOT / "outputs" / OUT_NAME

ACTIVE = [
    "codex_wave3_aio_libs_aiosmtpd_issues_403",
    "codex_wave3_alpha_unito_streamflow_issues_1100",
    "codex_wave3_aws_neuron_nki_library_issues_5",
    "codex_wave3_biface_i18n_issues_86",
]

REQUIRED_TOP_FILES = [
    "batch069_artifact_ingestion_summary.json",
    "batch069_artifact_sha256_verification.json",
    "batch069_result_preservation.json",
    "batch069_candidate_probe_preservation.json",
    "batch069_seed_readiness_preservation.json",
    "batch069_claim_boundary_preservation.json",
    "batch069b_active_recoverable_candidate_set.json",
    "batch069b_audioread_terminal_preservation.json",
    "batch069b_probe_budget_policy.json",
    "universal_interlock_law_manifest_batch069b.json",
    "step_to_output_contract_registry_batch069b.json",
    "declared_expected_outputs_batch069b.json",
    "independent_output_verifier_batch069b.json",
    "not_run_with_reason_registry_batch069b.json",
    "stale_blocker_retirement_registry_batch069b.json",
    "recoverable_command_translation_policy_batch069b.json",
    "decision_time_command_source_priority_batch069b.json",
    "native_command_recovery_matrix_batch069b.json",
    "command_synthesis_vs_command_extraction_policy_batch069b.json",
    "cross_environment_orthology_map_batch069b.json",
    "environment_constraint_translation_matrix_batch069b.json",
    "orthology_before_container_initialization_audit_batch069b.json",
    "ast_topology_extrusion_map_batch069b.json",
    "two_winner_policy_batch069b.json",
    "winner_N_argmin_vs_elbow_audit_batch069b.json",
    "elbow_patch_authorization_gate_batch069b.json",
    "flatline_or_edge_pinned_abstention_batch069b.json",
    "failed_attempt_branch_record_schema_batch069b.json",
    "failed_attempt_branch_record_registry_batch069b.json",
    "branch_closed_without_count_increment_audit_batch069b.json",
    "rollback_target_registry_batch069b.json",
    "runtime_connector_gap_registry_batch069b.json",
    "future_connector_requirement_queue_batch069b.json",
    "provider_capsule_recipe_registry_batch069b.json",
    "manual_runner_requirement_registry_batch069b.json",
    "manual_artifact_request_queue_batch069b.json",
    "external_source_approval_queue_batch069b.json",
    "candidate_command_artifact_request_queue_batch069b.json",
    "reward_signal_memory_boundary_batch069b.json",
    "routing_memory_update_registry_batch069b.json",
    "repair_skill_memory_update_blocker_batch069b.json",
    "seed_product_readiness_registry_batch069b.json",
    "seed_reopen_condition_registry_batch069b.json",
    "batch069b_seed_readiness_delta.json",
    "connector_readiness_queue_batch069b.json",
    "batch070_or_068b_handoff_plan_batch069b.json",
    "batch069b_final_decision.json",
    "batch069b_summary.md",
    "SHA256SUMS.txt",
]

REQUIRED_CANDIDATE_FILES = [
    "candidate_identity_preservation.json",
    "command_source_inventory.json",
    "project_local_metadata_inventory.json",
    "ci_workflow_command_inventory.json",
    "tox_nox_hatch_poetry_pdm_uv_inventory.json",
    "test_tree_inventory.json",
    "runner_dependency_inventory.json",
    "candidate_command_recovery_decision.json",
    "candidate_command_manifest.json",
    "harness_origin_recheck.json",
    "workspace_purity_recheck.json",
    "provider_capsule_preservation.json",
    "pre_repair_replay_gate.json",
    "pre_repair_replay_result.json",
    "reward_signal.json",
    "failed_branch_record_if_blocked.json",
    "terminal_state.json",
    "next_action_recommendation.json",
]


def read_json(path: str | Path) -> Any:
    target = OUT_DIR / path if isinstance(path, str) else path
    return json.loads(target.read_text(encoding="utf-8"))


def expect(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def run_check(args: list[str], errors: list[str], label: str) -> None:
    proc = subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=False)
    expect(errors, proc.returncode == 0, f"{label} failed: {proc.stdout[-1200:]} {proc.stderr[-1200:]}")


def audit_public_summary(errors: list[str]) -> None:
    text = (OUT_DIR / "batch069b_summary.md").read_text(encoding="utf-8")
    expect(errors, audit_public_summary_text(text).get("status") == "PASS", "Batch069b summary failed neutral language audit")
    hits = [term for term in FORBIDDEN_PUBLIC_TERMS if term.lower() in text.lower()]
    expect(errors, not hits, f"Batch069b public summary contains forbidden public terms: {hits}")
    expect(errors, "not repair proof" in text, "public summary must state not repair proof")


def audit_candidate_records(errors: list[str]) -> None:
    matrix = read_json("native_command_recovery_matrix_batch069b.json")
    records = matrix.get("records", [])
    expect(errors, [record.get("candidate_id") for record in records] == ACTIVE, "Batch069b active candidate order changed")
    record_by_id = {record.get("candidate_id"): record for record in records}
    for cid in ACTIVE:
        cdir = OUT_DIR / "candidates" / cid
        expect(errors, cdir.is_dir(), f"missing candidate directory {cid}")
        for rel in REQUIRED_CANDIDATE_FILES:
            expect(errors, (cdir / rel).is_file(), f"missing candidate output {cid}/{rel}")
        record = record_by_id.get(cid)
        expect(errors, isinstance(record, dict), f"missing matrix record for {cid}")
        if not isinstance(record, dict):
            continue
        expect(errors, record.get("audit_status") == "PASS", f"{cid} audit status not PASS")
        expect(errors, record.get("pre_repair_replay_status") != "pre_repair_target_failure_materialized", f"{cid} unexpectedly materialized target failure")
        expect(errors, record.get("command_manifest_status") == "BLOCK", f"{cid} command manifest should remain blocked without exact native target command")
        manifest = read_json(cdir / "candidate_command_manifest.json")
        expect(errors, manifest.get("manual_guessed_command_used") is False, f"{cid} used manual guessed command")
        expect(errors, manifest.get("issue_comment_fix_text_used") is False, f"{cid} used issue-comment fix text")
        expect(errors, manifest.get("test_mutation_used") is False, f"{cid} used test mutation")
        harness = read_json(cdir / "harness_origin_recheck.json")
        expect(errors, harness.get("fixed_patch_gold_future_evidence_used") is False, f"{cid} used forbidden evidence")
        workspace = read_json(cdir / "workspace_purity_recheck.json")
        expect(errors, workspace.get("outside_live_repo") is True, f"{cid} workspace not outside live repo")
        expect(errors, workspace.get("source_mutation_allowed") is False, f"{cid} source mutation allowed")
        expect(errors, workspace.get("test_mutation_allowed") is False, f"{cid} test mutation allowed")
        branch = read_json(cdir / "failed_branch_record_if_blocked.json")
        expect(errors, validate_failed_branch_record(branch).get("status") == "PASS", f"{cid} failed branch closure invalid")
        reward = read_json(cdir / "reward_signal.json")
        expect(errors, reward.get("repair_skill_memory_update_allowed") is False, f"{cid} repair memory update allowed")
        expect(errors, reward.get("routing_memory_update_allowed") is True, f"{cid} routing memory not recorded")


def audit_interlocks(errors: list[str]) -> None:
    manifest = read_json("universal_interlock_law_manifest_batch069b.json")
    ids = {record.get("interlock_id") for record in manifest.get("records", [])}
    for required in [
        "artifact_custody",
        "provider_capsule",
        "command_translation",
        "cross_environment_orthology",
        "ast_topology",
        "failed_branch_closure",
        "step_to_output_contract",
        "duplicate_clean_replay",
        "count_gate",
    ]:
        expect(errors, required in ids, f"missing interlock {required}")
    step = read_json("step_to_output_contract_registry_batch069b.json")
    expect(errors, step.get("status") == "PASS", "step-to-output contract not PASS")
    verifier = read_json("independent_output_verifier_batch069b.json")
    expect(errors, verifier.get("silent_missing_output_count") == 0, "silent missing outputs detected")
    orthology = read_json("cross_environment_orthology_map_batch069b.json")
    for record in orthology.get("records", []):
        expect(errors, validate_cross_environment_record(record).get("status") == "PASS", f"orthology record invalid for {record.get('candidate_id')}")
    ast = read_json("ast_topology_extrusion_map_batch069b.json")
    for record in ast.get("records", []):
        expect(errors, validate_ast_topology_record(record).get("status") == "PASS", f"AST topology record invalid for {record.get('candidate_id')}")
    elbow = read_json("elbow_patch_authorization_gate_batch069b.json")
    expect(errors, elbow.get("patch_generation_allowed") is False, "elbow gate allowed Batch069b patch generation")
    failed = read_json("failed_attempt_branch_record_registry_batch069b.json")
    expect(errors, len(failed.get("records", [])) == 4, "expected one failed branch record per active candidate")
    closure = read_json("branch_closed_without_count_increment_audit_batch069b.json")
    expect(errors, closure.get("repair_count_increment") is False, "failed branch closure allowed count increment")


def audit_seed_product_readiness(errors: list[str]) -> None:
    registry = read_json("seed_product_readiness_registry_batch069b.json")
    records = registry.get("records", [])
    expect(errors, registry.get("status") == "PASS", "seed product-readiness status not PASS")
    expect(errors, registry.get("unapproved_without_reason_count") == 0, "seed readiness has unapproved_without_reason")
    expect(errors, len(records) >= 90, "Batch069b seed readiness lost Batch068 seed coverage")
    for item in records:
        expect(errors, item.get("batch069b_readiness_status") != "unapproved_without_reason", f"{item.get('candidate_id')} unapproved without reason")
        if item.get("batch069b_readiness_status") not in {"approved_for_current_probe"}:
            expect(errors, bool(item.get("exact_blocker")), f"{item.get('candidate_id')} missing exact blocker")
            expect(errors, bool(item.get("reopen_condition")), f"{item.get('candidate_id')} missing reopen condition")
    connectors = read_json("runtime_connector_gap_registry_batch069b.json")
    expect(errors, connectors.get("request_count") == 1, "expected one runtime connector requirement")
    manuals = read_json("manual_artifact_request_queue_batch069b.json")
    expect(errors, manuals.get("request_count") == 3, "expected three manual target-command artifact requests")


def audit_final(errors: list[str]) -> None:
    final = read_json("batch069b_final_decision.json")
    expect(errors, final.get("status") == "PASS", "final decision not PASS")
    expect(errors, final.get("batch069b_audit_status") == "PASS", "Batch069b audit status not PASS")
    expect(errors, final.get("current_protocol") == "v2.14", "current protocol changed")
    expect(errors, final.get("issue_derived_repair_count") == 4, "issue-derived repair count changed")
    expect(errors, final.get("native_external_repair_count") == 4, "native external repair count changed")
    for key in [
        "patch_generated",
        "patch_applied",
        "source_mutated",
        "tests_mutated",
        "fixtures_mutated",
        "config_mutated",
        "duplicate_replay_run",
        "count_gate_run",
        "repair_count_increment",
    ]:
        expect(errors, final.get(key) is False, f"{key} must remain false")
    expect(errors, final.get("active_candidate_count") == 4, "active candidate count must be 4")
    expect(errors, final.get("command_recovered_candidate_count") == 0, "exact native command recovery count must remain zero")
    expect(errors, final.get("pre_repair_replay_run_count") == 0, "pre-repair replay must not run without exact command")
    expect(errors, final.get("materialized_candidate_count") == 0, "materialized candidate count must be zero")
    expect(errors, final.get("manual_artifact_required_count") == 3, "manual artifact count mismatch")
    expect(errors, final.get("runtime_connector_required_count") == 1, "runtime connector count mismatch")
    expect(errors, final.get("failed_branch_record_count") == 4, "failed branch count mismatch")
    expect(errors, final.get("universal_interlock_law_status") == "PASS", "universal interlock law not PASS")
    expect(errors, final.get("step_to_output_contract_status") == "PASS", "step contract not PASS")
    expect(errors, final.get("seed_product_readiness_status") == "PASS", "seed product readiness not PASS")
    expect(errors, final.get("reward_memory_boundary_status") == "PASS", "reward memory boundary not PASS")
    expect(errors, final.get("unapproved_without_reason_count") == 0, "unapproved without reason count not zero")
    expect(errors, final.get("full_scoring") == "NOT_RUN/disallowed", "full scoring changed")
    expect(errors, final.get("memory_lift") == "not_demonstrated", "memory lift changed")
    expect(errors, final.get("self_maintaining_software") == "false/not_demonstrated", "self-maintaining claim changed")
    expect(errors, final.get("next_allowed_action") == "batch068b_manual_artifact_and_external_source_custody_intake", "unexpected next allowed action")


def main() -> int:
    errors: list[str] = []
    expect(errors, OUT_DIR.is_dir(), "missing Batch069b output directory")
    for rel in REQUIRED_TOP_FILES:
        expect(errors, (OUT_DIR / rel).is_file(), f"missing Batch069b output {rel}")
    for rel in [
        "scripts/generate_batch069b_recoverable_provider_command_followup.py",
        "scripts/audit_batch069b_recoverable_provider_command_followup.py",
        ".github/workflows/post_v2_37_hardening_batch069b_recoverable_provider_command_followup.yml",
        "configs/universal_interlock_law_manifest.json",
        "configs/step_to_output_contract_registry.json",
        "configs/recoverable_command_translation_policy.json",
        "configs/decision_time_command_source_priority.json",
        "configs/elbow_patch_authorization_policy.json",
        "configs/controllergate_seed_product_readiness_registry.json",
        "controllergate/core/recoverable_command_translation.py",
        "controllergate/core/cross_environment_orthology.py",
        "controllergate/core/ast_topology_extrusion.py",
        "controllergate/core/failed_branch_closure.py",
    ]:
        expect(errors, (ROOT / rel).is_file(), f"missing implementation file {rel}")
    if errors:
        print("FAIL:")
        for error in errors:
            print(f"- {error}")
        return 1
    manifest = verify_manifest(OUT_DIR)
    expect(errors, manifest.get("status") == "PASS", f"SHA256SUMS failed: {manifest}")
    artifact = read_json("batch069_artifact_sha256_verification.json")
    expect(errors, artifact.get("status") in {"PASS", "batch069_artifact_absent_for_local_ingest"}, f"unexpected artifact status {artifact.get('status')}")
    if artifact.get("status") == "PASS":
        outer = artifact.get("outer", {})
        entries = artifact.get("entries", {})
        expect(errors, outer.get("size_bytes") == 80954, "Batch069 artifact size mismatch")
        expect(errors, outer.get("sha256") == "7d5519b84bee18e5af15be66f4e040b7b9334e89330680ccd4fa9842a71c841c", "Batch069 artifact SHA mismatch")
        expect(errors, entries.get("unsafe_path_count") == 0, "Batch069 artifact unsafe paths")
        expect(errors, entries.get("duplicate_path_count") == 0, "Batch069 artifact duplicate paths")
        expect(errors, artifact.get("nested_archive_cache_venv_pyc_payload_count") == 0, "Batch069 artifact nested/cache payloads")
        for name, result in artifact.get("manifests", {}).items():
            expect(errors, result.get("status") == "PASS", f"Batch069 artifact manifest failed: {name}")
    audioread = read_json("batch069b_audioread_terminal_preservation.json")
    expect(errors, audioread.get("terminal_state") == "provider_backend_unavailable_still_terminal", "audioread terminal state not preserved")
    expect(errors, audioread.get("reopened") is False, "audioread was reopened")
    audit_candidate_records(errors)
    audit_interlocks(errors)
    audit_seed_product_readiness(errors)
    audit_final(errors)
    audit_public_summary(errors)

    run_check([sys.executable, "scripts/audit_batch069_multi_candidate_provider_command_probe.py"], errors, "Batch069 audit")
    run_check([sys.executable, "scripts/audit_batch068_multi_seed_harvest_for_5th_issue_repair.py"], errors, "Batch068 audit")
    run_check([sys.executable, "scripts/audit_batch063e_pytest_runner_target_split_evidence_intake.py"], errors, "Batch063e audit")
    run_check([sys.executable, "scripts/audit_batch063d_pytest_safe_tag_acquisition_hardening.py"], errors, "Batch063d audit")
    run_check([sys.executable, "scripts/audit_batch063c_pytest_command_boundary_followup.py"], errors, "Batch063c audit")
    run_check([sys.executable, "scripts/audit_batch067_universal_wrapper_hardening_implementation.py"], errors, "Batch067 audit")
    run_check([sys.executable, "scripts/controllergate_audit.py", "--protocol", "current"], errors, "current protocol audit")
    run_check([sys.executable, "scripts/controllergate_run.py", "--protocol", "current", "--dry-run"], errors, "current protocol dry-run")

    if errors:
        print("FAIL:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Batch069b recoverable provider-command follow-up audit PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
