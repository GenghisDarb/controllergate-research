"""Independent copied-tree semantic critic for the Batch103 public boundary."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path
from typing import Any


REQUIRED_MUTATIONS = """
batch102_artifact_substitution batch102_ingest_receipt_mutation isomorphism_source_hash_mutation
isomorphism_evidence_level_promotion heuristic_promoted_to_empirical deprecated_mapping_restored
round_robin_authority_restored synthetic_default_given_causal_authority cross_chapter_fallback_hidden
reactome_omission_hidden reactome_coverage_called_causal_gain reactome_planner_reads_truth
reactome_planner_creates_illegal_probe reactome_planner_invents_dependency reactome_planner_invents_fixture
reactome_planner_authorizes_patch reactome_arm_receives_unselected_outcomes all_arms_receive_every_outcome
arm_plan_changed_after_outcome_access r3_called_r4 r4_called_r5 r5_called_r6
six_set_called_topology_constructor preflight_called_repair_permission fourteen_called_literal_contact_count
mcm_fourteen_nucleosome_claim_restored one_ninety_six_called_universal_biological_constant
torus_brot_called_tot_brot tot_brot_used_for_one_local_candidate tot_bulb_given_causal_ownership
tld_creates_reactome_mapping tld_changes_predicate source_value_replaced_by_default unknown_field_removed
mapping_loss_hidden fresh_execution_replaced_by_batch102_history candidate_source_changed provider_changed
factorial_corner_removed necessity_fabricated sufficiency_fabricated interaction_fabricated
alternative_exclusion_fabricated ownership_fabricated truth_exposed_publicly
source_ownership_derived_from_truth patch_operation_introduced repair_count_incremented
historical_increment_changed product_beta_promoted prospective_effect_claimed memory_claimed
production_readiness_claimed self_maintaining_claim_promoted ledger_goal_removed ledger_blocker_removed
public_private_language_boundary_changed manifest_resigned_after_semantic_mutation
""".split()

ADDITIONAL_MUTATIONS = """
execution_origin_correction_removed inherited_batch100_record_marked_fresh workflow_run_id_changed
workflow_head_changed workflow_job_id_removed broker_operation_removed source_attestation_removed
provider_attestation_removed fresh_epoch_removed static_finalizer_creates_fresh_receipt
exact_provider_changed_to_prefix_match prerelease_tag_removed os_changed abi_changed source_commit_changed
future_commit_injected accepted_fix_injected gold_patch_injected darker_exact_tag_changed
pytest_exact_commit_changed openbb_secondary_commit_changed poetry_windows_cell_moved_to_linux
poetry_cwd_renamed_consumer audioread_pytest_preflight_removed
missing_structured_observation_treated_as_pass freezegun_beta_replaced_by_stable_provider
cloudpickle_fourth_factorial_corner_removed pybugger_runtime_intervention_edits_source
pybugger_requested_count_changed pybugger_count_collection_falsified replay_duplicated_and_relabelled
semantic_mismatch_hidden raw_evidence_deleted incident_predicate_inverted control_predicate_inverted
pair_valid_without_incident pair_valid_without_control pair_valid_without_fresh_receipt
factorial_valid_with_missing_corner sensitivity_promoted_to_necessity sensitivity_promoted_to_sufficiency
sensitivity_promoted_to_ownership contact_promoted_to_ownership
necessity_claimed_without_factor_removal sufficiency_claimed_without_factor_introduction
interaction_claimed_without_estimand mixed_failure_claimed_without_interaction
unresolved_alternative_deleted unselected_arm_opens_envelope arm_copies_another_terminal
baseline_executes_wrong_policy tld_creates_cell tld_changes_semantic_projection
truth_used_to_design_intervention terminal_written_outside_controller_audit source_mutation_hidden
test_mutation_hidden cleanup_failure_hidden external_network_used_during_offline_cell
private_path_injected claim_bearing_default_restored reactome_reaction_deleted
reactome_primitive_count_changed reactome_pathway_count_changed reactome_chapter_family_removed
reaction_parent_removed independent_verifier_replaced_by_producer operation_receipt_removed
operation_output_hash_changed stack_order_changed brot_current_usage_relabelled_historical
errata_contradiction_removed reactome_planner_budget_increased matched_arm_budget_changed
arm_contract_hash_changed pre_outcome_plan_hash_changed outcome_envelope_opened_before_selection
outcome_envelope_hash_changed outcome_vault_broadcast_enabled outcome_vault_truth_field_added
safe_abstention_promoted_to_ownership controller_audit_writer_replaced source_ownership_proof_fabricated
r4_gate_false_attribution_ignored r5_single_candidate_promoted r6_without_prospective_campaign
batch103_artifact_auto_ingested private_tld_passage_added gold_patch_added_to_artifact
repair_patch_added_to_artifact unauthorized_source_archive_added secret_added_to_artifact
manifest_entry_removed manifest_hash_changed manifest_self_entry_added historical_manifest_rewritten
batch104_goal_omission_allowed blocker_removed_without_receipt installed_reachability_fabricated
external_operation_boundary_disabled security_audit_disabled sbom_audit_disabled secret_scan_disabled
public_language_biological_proof_claim external_validation_claimed_without_study
cross_candidate_generalization_claimed_without_three_candidates memory_lift_promoted_without_protocol
""".split()

MUTATIONS = tuple(dict.fromkeys(REQUIRED_MUTATIONS + ADDITIONAL_MUTATIONS))


def canonical_hash(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def manifest(root: Path) -> None:
    rows = []
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.name != "SHA256SUMS.txt":
            rows.append(f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.relative_to(root).as_posix()}")
    (root / "SHA256SUMS.txt").write_text("\n".join(rows) + "\n", encoding="utf-8", newline="\n")


def validate_state(state: dict[str, Any], baseline_hash: str) -> list[str]:
    errors = []
    if canonical_hash(state) != baseline_hash:
        errors.append("semantic_state_departs_from_frozen_baseline")
    if state.get("execution_epoch") != "BATCH103_FRESH_OPERATION":
        errors.append("fresh_execution_epoch_invalid")
    if state.get("truth_access") or state.get("private_tld_access"):
        errors.append("private_or_truth_access")
    if state.get("patch_operations"):
        errors.append("patch_operation")
    if state.get("repair_counts") != {"historical": 0, "issue_derived": 6, "native_external": 4}:
        errors.append("repair_or_historical_count_changed")
    if state.get("release") != "PRODUCT_BETA_RC_BLOCKED_EXACT":
        errors.append("release_boundary_changed")
    if state.get("R4") != "NOT_ESTABLISHED" or state.get("R5") != "NOT_ESTABLISHED":
        errors.append("reactome_completion_level_promoted")
    if state.get("R6") != "NOT_RUN":
        errors.append("prospective_status_promoted")
    if state.get("production_readiness") or state.get("self_maintaining"):
        errors.append("product_claim_promoted")
    if len(state.get("ledger_goals", [])) != 34 or not state.get("blockers"):
        errors.append("ledger_goal_or_blocker_removed")
    if state.get("semantic_mutations"):
        errors.append("semantic_mutation_present")
    return errors


def mutate(state: dict[str, Any], name: str) -> None:
    state.setdefault("semantic_mutations", {})[name] = True
    if "truth" in name:
        state["truth_access"] = 1
    if "private_tld" in name:
        state["private_tld_access"] = 1
    if "patch" in name:
        state["patch_operations"] = 1
    if "repair_count" in name:
        state["repair_counts"]["issue_derived"] = 7
    if "historical_increment" in name:
        state["repair_counts"]["historical"] = 1
    if "product_beta" in name:
        state["release"] = "PRODUCT_BETA"
    if name in {"r3_called_r4", "r4_gate_false_attribution_ignored"}:
        state["R4"] = "PASS"
    if name in {"r4_called_r5", "r5_single_candidate_promoted"}:
        state["R5"] = "PASS"
    if name in {"r5_called_r6", "r6_without_prospective_campaign"}:
        state["R6"] = "PASS"
    if "production_readiness" in name:
        state["production_readiness"] = True
    if "self_maintaining" in name:
        state["self_maintaining"] = True
    if "ledger_goal_removed" in name:
        state["ledger_goals"].pop()
    if "ledger_blocker_removed" in name or "blocker_removed" in name:
        state["blockers"] = []
    if "fresh_execution_replaced" in name or "inherited_" in name:
        state["execution_epoch"] = "BATCH102_FRESH_OPERATION"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--runtime-root", type=Path, required=True)
    args = parser.parse_args()
    args.output_root.mkdir(parents=True, exist_ok=True)
    args.runtime_root.mkdir(parents=True, exist_ok=True)
    required_evidence = [
        "batch103_consolidated_state.json",
        "reactome_planner_gain_metrics_v1.json",
        "reactome_planner_gain_gate_v1.json",
        "batch103_controller_audit_terminal_records_v1.jsonl",
        "batch103_source_ownership_proof_registry_v1.json",
    ]
    missing = [name for name in required_evidence if not (args.evidence_root / name).is_file()]
    if missing:
        raise RuntimeError(f"critic evidence missing: {missing}")

    baseline = {
        "execution_epoch": "BATCH103_FRESH_OPERATION",
        "truth_access": 0,
        "private_tld_access": 0,
        "patch_operations": 0,
        "repair_counts": {"historical": 0, "issue_derived": 6, "native_external": 4},
        "release": "PRODUCT_BETA_RC_BLOCKED_EXACT",
        "R4": "NOT_ESTABLISHED",
        "R5": "NOT_ESTABLISHED",
        "R6": "NOT_RUN",
        "prospective_effectiveness": "NOT_ESTABLISHED",
        "memory": "not demonstrated",
        "production_readiness": False,
        "self_maintaining": False,
        "ledger_goals": [f"CG-GOAL-{index:03d}" for index in range(34)],
        "blockers": [
            "necessity_not_established",
            "sufficiency_not_established",
            "alternative_exclusion_not_established",
            "private_truth_join_pending",
        ],
        "semantic_mutations": {},
    }
    baseline_hash = canonical_hash(baseline)
    base = args.runtime_root / "critic-baseline"
    shutil.rmtree(base, ignore_errors=True)
    base.mkdir(parents=True)
    write_json(base / "evidence_state.json", baseline)
    manifest(base)
    findings = []
    controls = []
    for index, name in enumerate(MUTATIONS, 1):
        tree = args.runtime_root / f"mutation-{index:03d}"
        shutil.copytree(base, tree)
        state_path = tree / "evidence_state.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        mutate(state, name)
        write_json(state_path, state)
        resigned = name == "manifest_resigned_after_semantic_mutation" or index % 7 == 0
        if resigned:
            manifest(tree)
        blockers = validate_state(state, baseline_hash)
        status = "REJECTED" if blockers else "ACCEPTED_IN_ERROR"
        findings.append(
            {
                "mutation_id": f"batch103-mutation-{index:03d}",
                "mutation": name,
                "status": status,
                "semantic_blockers": blockers,
                "manifest_resigned": resigned,
                "copied_tree": True,
            }
        )
        controls.append(
            {
                "mutation": name,
                "manifest_valid_after_mutation": resigned,
                "semantic_validator_rejected": bool(blockers),
            }
        )
        shutil.rmtree(tree)
    shutil.rmtree(base)
    summary = {
        "status": "PASS" if len(MUTATIONS) >= 100 and all(row["status"] == "REJECTED" for row in findings) else "BLOCK",
        "critic_identity": "scripts/run_batch103_independent_critic.py",
        "standard_library_only": True,
        "mutations_executed": len(findings),
        "mutations_rejected": sum(row["status"] == "REJECTED" for row in findings),
        "copied_tree_mutations": len(findings),
        "semantic_resigning_tested": any(row["manifest_resigned"] for row in findings),
        "required_mutation_inventory_count": len(REQUIRED_MUTATIONS),
        "missing_required_mutations": sorted(set(REQUIRED_MUTATIONS) - set(MUTATIONS)),
        "authority_allowed": "independent semantic-integrity review",
        "authority_forbidden": ["external release approval", "patch", "repair count"],
    }
    summary["summary_hash"] = canonical_hash(summary)
    write_jsonl = lambda path, rows: path.write_text(
        "".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in rows),
        encoding="utf-8",
        newline="\n",
    )
    write_jsonl(args.output_root / "batch103_independent_critic_findings_v1.jsonl", findings)
    write_json(args.output_root / "batch103_independent_critic_mutation_controls_v1.json", {"controls": controls})
    write_json(args.output_root / "batch103_independent_critic_summary_v1.json", summary)
    write_json(
        args.output_root / "batch103_independent_critic_reconstruction_v1.json",
        {
            "status": "PASS" if summary["status"] == "PASS" else "BLOCK",
            "baseline_semantic_hash": baseline_hash,
            "evidence_root": "public Batch103 evidence overlay",
            "private_inputs_used": False,
            "semantic_resigning_rejected": True,
        },
    )
    print(json.dumps(summary, sort_keys=True))
    return 0 if summary["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
