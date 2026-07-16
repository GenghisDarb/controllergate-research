from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


OUTPUT_NAME = "post_v2_37_hardening_batch094_value_bound_rpir_fresh_amds_cohort_historical_closure"
MANIFESTS = ("ARTIFACT_SHA256SUMS.txt", "PORTABLE_ARTIFACT_SHA256SUMS.txt", "SHA256SUMS.txt")


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_json(root: Path, name: str) -> dict[str, Any]:
    return json.loads((root / name).read_text(encoding="utf-8"))


def rows(root: Path, name: str) -> list[dict[str, Any]]:
    return [json.loads(line) for line in (root / name).read_text(encoding="utf-8").splitlines() if line]


def line_count(path: Path) -> int:
    with path.open(encoding="utf-8") as stream:
        return sum(bool(line.strip()) for line in stream)


def require(condition: bool, message: str, failures: list[str]) -> None:
    if not condition:
        failures.append(message)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default=f"outputs/{OUTPUT_NAME}")
    parser.add_argument("--require-cross-platform", action="store_true")
    args = parser.parse_args()
    output = Path(args.output)
    failures: list[str] = []
    required = [
        "batch093_artifact_ingest.json", "batch093_artifact_manifest_verification.json",
        "batch094_pre_fix_value_bound_rpir_and_fresh_cohort_expected_failure.json",
        "reactome_release97_member_use_audit.json", "rpir_v2_1_schema.json", "rpir_v2_1_graph_completeness_decision.json",
        "rpir_v2_1_roundtrip_audit.json", "rpir_v2_1_anchor_audit.json", "reactome_translation_authority_firewall_v3.json",
        "reactome_translation_distinctness_v2.json", "primitive_behavioral_coverage.json", "primitive_confusion_pair_results.jsonl",
        "primitive_composed_scenario_ablations.jsonl", "reactome_chapter_scenario_registry_v3.jsonl",
        "historical_episode_acquisition_contracts.jsonl", "historical_source_capsules.jsonl", "historical_test_tree_capsules.jsonl",
        "historical_provider_capsules.jsonl", "historical_target_reproducer_capsules.jsonl", "historical_command_contracts.jsonl",
        "historical_runner_harness_identities.jsonl", "historical_incident_snapshots.jsonl",
        "historical_proof_release_parent_snapshots.jsonl", "historical_materialization_results.jsonl",
        "historical_acquisition_broker_operations.jsonl", "historical_frozen_cohort_v2.json", "historical_no_substitution_audit.json",
        "role_future_outcome_provenance_scan_v2.json", "role_identity_claim_graph_v2.json", "role_identity_reuse_audit_v2.json",
        "role_measurement_quality_gate_v2.json", "amds_historical_quality_gate_v3.json", "external_human_authorization_gate.json",
        "batch094_downstream_gate_status.json", "standalone_critic_input_manifest_v3.json", "standalone_critic_reconstruction_v3.json",
        "standalone_critic_findings_v3.jsonl", "seal_breaking_mutation_results_v3.json",
        "resigned_actual_evidence_mutation_registry.jsonl", "resigned_actual_evidence_mutation_results.json",
        "internal_release_evidence_decision_v3.json", "public_state_generation_audit.json", "public_state_sync_audit.json",
        "release_version_lineage.json", "batch094_internal_release_decision.json", "batch094_external_review_package_index.json",
        "batch094_claim_boundary.json", "batch094_consolidated_state.json", "campaign_summary.md", *MANIFESTS,
    ]
    missing = [name for name in required if not (output / name).is_file()]
    require(not missing, f"required outputs missing: {missing}", failures)
    if missing:
        print(json.dumps({"status": "FAIL", "failures": failures}, sort_keys=True))
        return 1

    ingest = read_json(output, "batch093_artifact_ingest.json")
    manifest = read_json(output, "batch093_artifact_manifest_verification.json")
    red = read_json(output, "batch094_pre_fix_value_bound_rpir_and_fresh_cohort_expected_failure.json")
    members = read_json(output, "reactome_release97_member_use_audit.json")
    graph = read_json(output, "rpir_v2_1_graph_completeness_decision.json")
    roundtrip = read_json(output, "rpir_v2_1_roundtrip_audit.json")
    anchors = read_json(output, "rpir_v2_1_anchor_audit.json")
    firewall = read_json(output, "reactome_translation_authority_firewall_v3.json")
    distinct = read_json(output, "reactome_translation_distinctness_v2.json")
    primitive = read_json(output, "primitive_behavioral_coverage.json")
    cohort = read_json(output, "historical_frozen_cohort_v2.json")
    no_substitution = read_json(output, "historical_no_substitution_audit.json")
    future = read_json(output, "role_future_outcome_provenance_scan_v2.json")
    role_claim = read_json(output, "role_identity_claim_graph_v2.json")
    role_reuse = read_json(output, "role_identity_reuse_audit_v2.json")
    role = read_json(output, "role_measurement_quality_gate_v2.json")
    amds = read_json(output, "amds_historical_quality_gate_v3.json")
    approval = read_json(output, "external_human_authorization_gate.json")
    downstream = read_json(output, "batch094_downstream_gate_status.json")
    cross = read_json(output, "installed_cross_platform_equivalence_v3.json")
    critic_reconstruction = read_json(output, "standalone_critic_reconstruction_v3.json")
    seal = read_json(output, "seal_breaking_mutation_results_v3.json")
    resigned = read_json(output, "resigned_actual_evidence_mutation_results.json")
    critic = read_json(output, "internal_release_evidence_decision_v3.json")
    sync = read_json(output, "public_state_sync_audit.json")
    decision = read_json(output, "batch094_internal_release_decision.json")
    claim = read_json(output, "batch094_claim_boundary.json")

    require(ingest["status"] == "PASS" and ingest["artifact"]["artifact_id"] == 8363847950, "Batch093 artifact ingest failed", failures)
    require(ingest["artifact"]["sha256"] == "0f77d8e46ae72bf70adc0f585e56a4467ccb548d66f179ab8a699537173f15c6" and ingest["artifact"]["size"] == 11261479, "Batch093 artifact byte identity mismatch", failures)
    require(manifest["status"] == "PASS" and all(row["status"] == "PASS" and row["self_entries"] == 0 for row in manifest["manifests"]), "Batch093 manifests failed", failures)
    require(red["status"] == "BATCH094_PRE_FIX_AUDIT_FAIL_EXPECTED" and red["finding_count"] == 11 and red["audit_hash"] == "6851f77437f6ba3f65c9b289558dca1cfcb1007be139f1bfde6949a3b5926eda", "sealed expected-red audit mismatch", failures)
    require(members["status"] == "PASS" and members["member_count"] == members["consumed_member_count"] == 7 and members["unused_member_count"] == 0, "exact source-member use audit failed", failures)
    require(graph["rpir_version"] == "controllergate-rpir-v2.1" and graph["pathway_occurrences"] == 2916 and graph["reaction_occurrences"] == 16814, "RPIR v2.1 occurrence coverage failed", failures)
    require(graph["silent_omission_count"] == 0 and graph["unknown_field_state_count"] == 0 and graph["complex_cycle_count"] == 0, "RPIR graph completeness failed", failures)
    require(graph["entity_set_member_count"] == 22690 and graph["candidate_member_count"] == 8391 and graph["demonstrated_member_count"] == 2832, "source member graph counts changed", failures)
    require(graph["complex_component_count"] == 170063 and graph["recursive_complex_count"] == 26060, "complex closure counts changed", failures)
    require(graph["stable_preceding_edge_count"] == graph["stable_following_edge_count"] == 15234, "stable edge reciprocity failed", failures)
    require(graph["normal_variant_pair_count"] == graph["inverse_variant_edge_count"] == 720 and graph["computed_first_divergence_count"] == 674, "normal/variant graph failed", failures)
    require(graph["stoichiometry_source_value_count"] == 0 and "numeric_stoichiometry_not_exposed_by_consumed_release_tables" in graph["exact_format_blockers"], "numeric stoichiometry boundary was hidden", failures)
    require(roundtrip["status"] == "PASS" and anchors["status"] == "PASS", "RPIR roundtrip or anchor audit failed", failures)
    require(line_count(output / "rpir_v2_1_reactions.jsonl") == 16814 and line_count(output / "rpir_v2_1_pathways.jsonl") == 2916, "RPIR row counts mismatch", failures)
    require(firewall["status"] == "PASS" and firewall["candidate_count"] == firewall["value_bound_count"] == 16814, "value-bound translation coverage failed", failures)
    require(firewall["repair_authority_count"] == firewall["production_promotion_count"] == firewall["keyword_count_hash_only_authority_count"] == 0, "translation authority firewall failed", failures)
    require(distinct["exact_string_count"] == 14846 and distinct["semantic_equivalence_cluster_count"] == 1143 and distinct["distinct_primitive_composition_count"] == 588, "translation distinctness changed", failures)
    require(primitive["status"] == "PASS" and primitive["primitive_count"] == primitive["behaviorally_demonstrated_count"] == primitive["ablation_count"] == 46, "primitive behavioral coverage failed", failures)
    require(primitive["confusion_pair_count"] == primitive["confusion_pair_pass_count"] == 16 and primitive["effect_key_only_authority_count"] == 0, "primitive confusion controls failed", failures)
    require(line_count(output / "reactome_chapter_scenario_registry_v3.jsonl") == 29, "chapter scenario registry must contain 29 source-bound scenarios", failures)

    materialized = rows(output, "historical_materialization_results.jsonl")
    expected_order = ["darker_issue_112_relative_git_dir", "py_bugger_issue_65", "cloudpickle_507_py313_typevar_distutils", "freezegun_547_py313_datetimes_assertion", "audioread_144_py313_aifc_removed", "pytest_13480_wdefault_unraisable_threadexception", "incident_openbb_7585_modular_openapi_reproducer", "incident_poetry_10974_init_duplicate_name"]
    require(cohort["candidate_order"] == expected_order and len(materialized) == 8, "frozen cohort order changed", failures)
    require(cohort["status"] == "BLOCK" and cohort["blocker"] == "BLOCK_MINIMUM_COHORT_NOT_MET" and cohort["materialized_candidate_count"] == 6, "minimum-cohort block not preserved", failures)
    require(sum(row["status"] == "PASS" for row in materialized) == 6 and sum(row["status"] != "PASS" for row in materialized) == 2, "actual materialization results mismatch", failures)
    require(no_substitution["status"] == "PASS" and no_substitution["replacement_count"] == 0, "candidate substitution occurred", failures)
    require(cohort["patch_operation_count"] == cohort["historical_count_increment"] == 0, "cohort patch/count mutation occurred", failures)
    require(line_count(output / "historical_acquisition_broker_operations.jsonl") == cohort["broker_operation_count"] and cohort["broker_operation_count"] > 0, "broker operation ledger mismatch", failures)
    for name in ("historical_source_capsules.jsonl", "historical_test_tree_capsules.jsonl", "historical_provider_capsules.jsonl", "historical_target_reproducer_capsules.jsonl", "historical_command_contracts.jsonl", "historical_runner_harness_identities.jsonl", "historical_incident_snapshots.jsonl", "historical_proof_release_parent_snapshots.jsonl"):
        require(line_count(output / name) == 8, f"fresh role capsule count mismatch: {name}", failures)
    require(future["admitted_future_or_outcome_evidence_count"] == 0, "future/outcome evidence was admitted", failures)
    require(role_claim["verified_role_edges"] == 0 and role_reuse["executed_role_receipt_count"] == 0, "role authority was fabricated after upstream block", failures)
    require(role["status"] == "BLOCK" and role["required_role_count"] == 80 and role["executed_role_receipt_count"] == 0, "role quality gate violated", failures)
    require(amds["status"] == "BLOCK" and amds["executed_episode_count"] == amds["probe_count"] == 0 and amds["actual_baselines"] == "NOT_RUN", "AMDS executed or was fabricated after cohort block", failures)
    require(approval["status"] == "HUMAN_AUTHORIZATION_BLOCKED_EXACT" and approval["repository_generated_approval"] is False and approval["run_historical_actuation"] is False, "human authorization boundary failed", failures)
    require(downstream["role_measurements"] == downstream["amds"] == downstream["stage_authority"] == "NOT_RUN", "downstream authority ran after block", failures)
    require(downstream["historical_lifecycles"] == downstream["non_source_lifecycles"] == downstream["deployment"] == "NOT_RUN", "lifecycle or deployment ran after block", failures)
    require(downstream["patch_operation_count"] == downstream["historical_count_increment"] == 0, "downstream patch/count mutation occurred", failures)

    windows = rows(output, "reactome_chapter_scenario_results_windows_v3.jsonl") if (output / "reactome_chapter_scenario_results_windows_v3.jsonl").is_file() else []
    linux = rows(output, "reactome_chapter_scenario_results_linux_v3.jsonl") if (output / "reactome_chapter_scenario_results_linux_v3.jsonl").is_file() else []
    require(len(windows) == 29 and all(row["status"] == "PASS" for row in windows), "Windows installed scenarios failed", failures)
    if args.require_cross_platform:
        require(len(linux) == 29 and all(row["status"] == "PASS" for row in linux), "Linux installed scenarios failed", failures)
        require(cross["status"] == "PASS" and set(cross["available_platforms"]) == {"linux", "windows"}, "official cross-platform equivalence failed", failures)
    else:
        require(cross["status"] in {"PASS", "BLOCK_MISSING_PLATFORM_EVIDENCE"}, "cross-platform boundary invalid", failures)

    require(critic_reconstruction["status"] == "PASS", "standalone raw reconstruction failed", failures)
    require(line_count(output / "standalone_critic_findings_v3.jsonl") > 0, "critic findings ledger is empty despite blockers", failures)
    require(seal["status"] == "PASS" and seal["executed"] == seal["rejected"] >= 2, "seal-breaking mutation rejection failed", failures)
    require(resigned["status"] == "PASS" and resigned["executed"] == resigned["rejected"] >= 12, "re-signed actual evidence mutation rejection failed", failures)
    require(critic["status"] == "PASS_INTERNAL_CRITIC_WITH_RELEASE_BLOCKERS" and critic["finding_count"] > 0, "standalone critic hid blockers", failures)
    require(sync["status"] == "PASS", "public status is not synchronized", failures)
    require(decision["status"] == claim["status"] == "PRODUCT_BETA_RC_BLOCKED_EXACT", "release boundary overclaimed", failures)
    require(claim["protocol"] == "v2.19" and claim["package_version"] == "0.2.0b2.dev0", "protocol or package version changed", failures)
    require(claim["issue_derived_repair_count"] == 6 and claim["native_external_repair_count"] == 4 and claim["historical_increment"] == 0, "repair counts changed", failures)
    require(claim["full_scoring"] == "NOT_RUN/disallowed" and claim["public_writes"] == claim["automatic_merge"] == "inactive", "disabled authorities changed", failures)
    require(claim["production_readiness"] is False and claim["self_maintaining_software"] == "false/not demonstrated", "production or self-maintenance overclaim", failures)

    for manifest_name in MANIFESTS:
        names: list[str] = []
        for line in (output / manifest_name).read_text(encoding="utf-8").splitlines():
            if not line:
                continue
            expected, name = line.split("  ", 1)
            names.append(name)
            require((output / name).is_file() and sha(output / name) == expected, f"manifest mismatch: {manifest_name}:{name}", failures)
        require(manifest_name not in names, f"invalid self-entry: {manifest_name}", failures)
    forbidden_suffixes = {".zip", ".pdf", ".whl", ".pyc", ".pyo", ".tar", ".tgz", ".sqlite", ".sqlite3", ".owl"}
    require(not [path for path in output.rglob("*") if path.is_file() and path.suffix.lower() in forbidden_suffixes], "raw/runtime payload found in output", failures)
    require(not [path for path in output.rglob("*") if path.is_dir() and path.name in {".git", "__pycache__", "site-packages"}], "runtime directory found in output", failures)

    result = {
        "status": "PASS" if not failures else "FAIL", "producer": "scripts/audit_batch094_value_bound_rpir_fresh_amds_cohort_historical_closure.py",
        "execution_depth": "complete Batch094 custody, RPIR, compiler, installed, cohort, critic, manifest, and claim audit",
        "semantic_scope": "Batch094 internal evidence", "authority_allowed": "internal audit", "authority_forbidden": "external release approval",
        "require_cross_platform": args.require_cross_platform, "failure_count": len(failures), "failures": failures,
    }
    print(json.dumps(result, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
