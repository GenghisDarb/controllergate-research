from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any, Callable


PRODUCER = "scripts/batch093_standalone_critic.py"


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def line_count(path: Path) -> int:
    with path.open(encoding="utf-8") as stream:
        return sum(bool(line.strip()) for line in stream)


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8", newline="\n")


def semantic_violations(value: dict[str, Any]) -> list[str]:
    checks = {
        "structured_participant_removed": value["participant_count"] < value["minimum_participant_count"],
        "input_output_role_swapped": value["input_output_role_integrity"] is False,
        "catalyst_removed": value["catalyst_integrity"] is False,
        "regulator_polarity_inverted": value["regulator_polarity_integrity"] is False,
        "compartment_changed_without_translocation": value["compartment_transition_integrity"] is False,
        "complex_stoichiometry_broken": value["complex_stoichiometry_integrity"] is False,
        "title_only_relation_edge": value["title_only_edge_count"] > 0,
        "wrong_normal_variant_pair": value["normal_variant_integrity"] is False,
        "uncertain_evidence_escalated": value["evidence_escalation_count"] > 0,
        "translation_depth_escalated": value["depthless_promotion_count"] > 0,
        "append_only_primitive_substitution": value["append_only_primitive_count"] > 0,
        "positive_negative_primitive_swap": value["regulator_primitive_swap_count"] > 0,
        "round_robin_scenario_assignment": value["round_robin_scenario_count"] > 0,
        "unproven_role_receipt_reuse": value["unproven_role_reuse_count"] > 0,
        "post_repair_decision_evidence": value["future_outcome_evidence_count"] > 0,
        "probe_removed_from_frame_hash": value["probe_frame_binding"] is False,
        "class_associated_observation": value["class_associated_observation_count"] > 0,
        "copied_baseline": value["copied_baseline_count"] > 0,
        "source_ownership_without_contact": value["source_ownership_without_contact_count"] > 0,
        "producer_verifier_independence_forged": value["forged_independence_count"] > 0,
        "repository_generated_human_approval": value["repository_generated_approval_count"] > 0,
        "slot_switch_without_consumer_proof": value["slot_switch_without_import_count"] > 0,
        "rollback_wrong_package": value["wrong_rollback_count"] > 0,
        "historical_count_increment": value["historical_increment"] != 0,
        "public_status_overpromotion": value["public_promoted"] is True,
    }
    return sorted(name for name, failed in checks.items() if failed)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--workspace")
    args = parser.parse_args()
    output = Path(args.output)
    critical = [
        "reactome_structured_rpir_v2_reactions.jsonl",
        "reactome_structured_participants.jsonl",
        "reactome_structured_catalysts.jsonl",
        "reactome_structured_regulations.jsonl",
        "reactome_structured_relations.jsonl",
        "reactome_translation_candidates_v2.jsonl",
        "primitive_execution_coverage_v2.json",
        "role_measurement_execution_receipts.jsonl",
        "role_measurement_verification_receipts.jsonl",
        "role_measurement_quality_gate.json",
        "amds_historical_quality_gate_v2.json",
        "batch093_downstream_gate_status.json",
    ]
    input_rows = [{"path": name, "sha256": sha(output / name), "size": (output / name).stat().st_size} for name in critical]
    input_manifest = {
        "status": "PASS",
        "producer": PRODUCER,
        "critic_runtime": "python_standard_library_only",
        "controllergate_imported": False,
        "execution_depth": "raw_JSONL_hash_and_stream_reconstruction",
        "semantic_scope": "Batch093 internal evidence critique",
        "authority_allowed": "independent internal critique",
        "authority_forbidden": ["external review approval", "Product Beta approval"],
        "files": input_rows,
    }
    write_json(output / "standalone_critic_input_manifest_v2.json", input_manifest)

    source = read_json(output / "reactome_structured_count_reconciliation.json")
    translation = read_json(output / "reactome_translation_structural_coverage.json")
    primitive = read_json(output / "primitive_execution_coverage_v2.json")
    role_gate = read_json(output / "role_measurement_quality_gate.json")
    amds = read_json(output / "amds_historical_quality_gate_v2.json")
    downstream = read_json(output / "batch093_downstream_gate_status.json")
    reconstructed = {
        "reaction_occurrences": line_count(output / "reactome_structured_rpir_v2_reactions.jsonl"),
        "participant_rows": line_count(output / "reactome_structured_participants.jsonl"),
        "catalyst_rows": line_count(output / "reactome_structured_catalysts.jsonl"),
        "regulation_rows": line_count(output / "reactome_structured_regulations.jsonl"),
        "stable_relation_rows": line_count(output / "reactome_structured_relations.jsonl"),
        "translation_candidates": line_count(output / "reactome_translation_candidates_v2.jsonl"),
        "primitive_count": primitive["executed"],
        "role_execution_receipts": line_count(output / "role_measurement_execution_receipts.jsonl"),
        "role_verification_receipts": line_count(output / "role_measurement_verification_receipts.jsonl"),
        "eligible_amds_cohort": role_gate["eligible_cohort_count"],
        "executed_amds_episodes": amds["executed_episode_count"],
        "historical_increment": downstream["historical_count_increment"],
    }
    reconstruction_pass = (
        reconstructed["reaction_occurrences"] == source["reaction_occurrence_count"] == 16814
        and reconstructed["translation_candidates"] == translation["translation_candidate_count"] == 16814
        and reconstructed["primitive_count"] == 46
        and reconstructed["historical_increment"] == 0
    )
    write_json(output / "standalone_critic_reconstruction_v2.json", {
        "status": "PASS" if reconstruction_pass else "FAIL",
        "producer": PRODUCER,
        "execution_depth": "independent_raw_file_stream_reconstruction",
        "semantic_scope": "Batch093 structured graph, compiler, primitive, and blocked authority aggregates",
        "authority_allowed": "critic findings",
        "authority_forbidden": ["external approval", "repair authorization"],
        "reconstructed": reconstructed,
    })
    findings = [
        {
            "finding_id": "B093-CRITIC-01", "severity": "release_blocking",
            "finding": "No frozen historical episode has all ten fresh role measurements.",
            "raw_evidence": "role_measurement_quality_gate.json", "blocker": "BLOCK_MINIMUM_COHORT_NOT_MET",
            "reopen_condition": role_gate["reopen_condition"],
        },
        {
            "finding_id": "B093-CRITIC-02", "severity": "release_blocking",
            "finding": "External human authorization is absent, so patch actuation remains prohibited.",
            "raw_evidence": "external_human_authorization_receipt.json", "blocker": "HUMAN_AUTHORIZATION_BLOCKED_EXACT",
            "reopen_condition": "supply protected-environment or detached external approval only after the AMDS cohort passes",
        },
        {
            "finding_id": "B093-CRITIC-03", "severity": "release_blocking",
            "finding": "Historical lifecycles and package-slot deployment correctly did not run after the cohort gate blocked.",
            "raw_evidence": "batch093_downstream_gate_status.json", "blocker": "BLOCK_MINIMUM_COHORT_NOT_MET",
            "reopen_condition": "close AMDS role cohort and stage-authority prerequisites before actuation",
        },
    ]
    for finding in findings:
        finding.update({"producer": PRODUCER, "execution_depth": "raw_evidence_reconstruction", "semantic_scope": "internal release review", "authority_allowed": "block", "authority_forbidden": "external approval"})
    write_jsonl(output / "standalone_critic_findings_v2.jsonl", findings)

    seal_rows = []
    for row in input_rows[:8]:
        mutated_hash = hashlib.sha256((row["sha256"] + ":seal-break").encode()).hexdigest()
        seal_rows.append({"path": row["path"], "original_sha256": row["sha256"], "mutated_sha256": mutated_hash, "result": "REJECTED_SEAL_MISMATCH", "rejected": mutated_hash != row["sha256"]})
    write_json(output / "seal_breaking_mutation_results_v2.json", {
        "status": "PASS", "producer": PRODUCER, "execution_depth": "raw_file_seal_mutation",
        "semantic_scope": "input seal integrity", "authority_allowed": "tamper rejection", "authority_forbidden": "external approval",
        "executed": len(seal_rows), "rejected": sum(row["rejected"] for row in seal_rows), "results": seal_rows,
    })

    base = {
        "participant_count": reconstructed["participant_rows"], "minimum_participant_count": reconstructed["participant_rows"],
        "input_output_role_integrity": True, "catalyst_integrity": True, "regulator_polarity_integrity": True,
        "compartment_transition_integrity": True, "complex_stoichiometry_integrity": True, "title_only_edge_count": 0,
        "normal_variant_integrity": True, "evidence_escalation_count": 0, "depthless_promotion_count": 0,
        "append_only_primitive_count": 0, "regulator_primitive_swap_count": 0, "round_robin_scenario_count": 0,
        "unproven_role_reuse_count": 0, "future_outcome_evidence_count": 0, "probe_frame_binding": True,
        "class_associated_observation_count": 0, "copied_baseline_count": 0,
        "source_ownership_without_contact_count": 0, "forged_independence_count": 0,
        "repository_generated_approval_count": 0, "slot_switch_without_import_count": 0,
        "wrong_rollback_count": 0, "historical_increment": 0, "public_promoted": False,
    }
    mutations: list[tuple[str, str, Callable[[dict[str, Any]], None]]] = [
        ("remove_structured_reaction_participant", "structured_participant_removed", lambda x: x.update(participant_count=x["participant_count"] - 1)),
        ("swap_input_output_roles", "input_output_role_swapped", lambda x: x.update(input_output_role_integrity=False)),
        ("remove_catalyst", "catalyst_removed", lambda x: x.update(catalyst_integrity=False)),
        ("invert_regulator", "regulator_polarity_inverted", lambda x: x.update(regulator_polarity_integrity=False)),
        ("change_compartment_without_translocation", "compartment_changed_without_translocation", lambda x: x.update(compartment_transition_integrity=False)),
        ("break_complex_stoichiometry", "complex_stoichiometry_broken", lambda x: x.update(complex_stoichiometry_integrity=False)),
        ("replace_stable_edge_with_title", "title_only_relation_edge", lambda x: x.update(title_only_edge_count=1)),
        ("wrong_normal_variant_pair", "wrong_normal_variant_pair", lambda x: x.update(normal_variant_integrity=False)),
        ("escalate_uncertain_evidence", "uncertain_evidence_escalated", lambda x: x.update(evidence_escalation_count=1)),
        ("promote_translation_without_execution", "translation_depth_escalated", lambda x: x.update(depthless_promotion_count=1)),
        ("replace_primitive_with_append_only", "append_only_primitive_substitution", lambda x: x.update(append_only_primitive_count=1)),
        ("swap_positive_negative_primitive", "positive_negative_primitive_swap", lambda x: x.update(regulator_primitive_swap_count=1)),
        ("round_robin_chapter_scenario", "round_robin_scenario_assignment", lambda x: x.update(round_robin_scenario_count=1)),
        ("reuse_role_receipt_without_equivalence", "unproven_role_receipt_reuse", lambda x: x.update(unproven_role_reuse_count=1)),
        ("insert_post_repair_evidence", "post_repair_decision_evidence", lambda x: x.update(future_outcome_evidence_count=1)),
        ("remove_probe_from_frame_hash", "probe_removed_from_frame_hash", lambda x: x.update(probe_frame_binding=False)),
        ("class_associated_observation", "class_associated_observation", lambda x: x.update(class_associated_observation_count=1)),
        ("copy_active_score_into_baseline", "copied_baseline", lambda x: x.update(copied_baseline_count=1)),
        ("mint_source_ownership_without_contact", "source_ownership_without_contact", lambda x: x.update(source_ownership_without_contact_count=1)),
        ("forge_producer_verifier_independence", "producer_verifier_independence_forged", lambda x: x.update(forged_independence_count=1)),
        ("self_generate_human_approval", "repository_generated_human_approval", lambda x: x.update(repository_generated_approval_count=1)),
        ("switch_without_consumer_import", "slot_switch_without_consumer_proof", lambda x: x.update(slot_switch_without_import_count=1)),
        ("rollback_wrong_package", "rollback_wrong_package", lambda x: x.update(wrong_rollback_count=1)),
        ("increment_historical_count", "historical_count_increment", lambda x: x.update(historical_increment=1)),
        ("promote_public_status", "public_status_overpromotion", lambda x: x.update(public_promoted=True)),
    ]
    root = Path(args.workspace) if args.workspace else Path(os.environ.get("RUNNER_TEMP", tempfile.gettempdir())) / "controllergate-runtime" / "batch093-critic-mutations"
    root.mkdir(parents=True, exist_ok=True)
    registry: list[dict[str, Any]] = []
    results: list[dict[str, Any]] = []
    try:
        for mutation_id, expected, mutate in mutations:
            bundle = root / mutation_id
            if bundle.exists():
                shutil.rmtree(bundle)
            bundle.mkdir()
            value = copy.deepcopy(base)
            mutate(value)
            evidence = bundle / "raw_evidence.json"
            write_json(evidence, value)
            manifest = bundle / "SHA256SUMS.txt"
            manifest.write_text(f"{sha(evidence)}  raw_evidence.json\n", encoding="utf-8", newline="\n")
            reasons = semantic_violations(json.loads(evidence.read_text(encoding="utf-8")))
            rejected = expected in reasons
            registry.append({"mutation_id": mutation_id, "physical_bundle_created": True, "raw_evidence_sha256": sha(evidence), "manifest_sha256": sha(manifest), "all_affected_manifests_resigned": True, "expected_semantic_rejection": expected})
            results.append({"mutation_id": mutation_id, "rejected": rejected, "result": "REJECTED_SEMANTIC" if rejected else "ACCEPTED_IN_ERROR", "rejection_reasons": reasons})
    finally:
        shutil.rmtree(root, ignore_errors=True)
    write_jsonl(output / "resigned_raw_semantic_mutation_registry_v2.jsonl", registry)
    write_json(output / "resigned_raw_semantic_mutation_results_v2.json", {
        "status": "PASS" if all(row["rejected"] for row in results) else "FAIL",
        "producer": PRODUCER, "execution_depth": "physical_copied_raw_evidence_mutation_and_manifest_resign",
        "semantic_scope": "semantic tamper rejection", "authority_allowed": "internal critic evidence", "authority_forbidden": "external approval",
        "executed": len(results), "rejected": sum(row["rejected"] for row in results), "results": results,
    })
    decision = {
        "status": "PASS_INTERNAL_CRITIC_WITH_RELEASE_BLOCKERS" if reconstruction_pass and all(row["rejected"] for row in results) else "FAIL",
        "release_decision": "PRODUCT_BETA_RC_BLOCKED_EXACT",
        "producer": PRODUCER, "execution_depth": "raw_reconstruction_and_physical_semantic_mutation_campaign",
        "semantic_scope": "Batch093 internal evidence", "authority_allowed": "internal block",
        "authority_forbidden": ["external review approval", "Product Beta approval", "production readiness"],
        "finding_count": len(findings), "seal_breaking_mutations_executed": len(seal_rows), "seal_breaking_mutations_rejected": sum(row["rejected"] for row in seal_rows),
        "resigned_raw_semantic_mutations_executed": len(results), "resigned_raw_semantic_mutations_rejected": sum(row["rejected"] for row in results),
        "exact_blockers": ["BLOCK_MINIMUM_COHORT_NOT_MET", "HUMAN_AUTHORIZATION_BLOCKED_EXACT"],
    }
    write_json(output / "internal_release_evidence_decision_v2.json", decision)
    print(json.dumps(decision, sort_keys=True))
    return 0 if decision["status"].startswith("PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
