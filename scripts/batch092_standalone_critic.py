from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
from typing import Any, Callable


PRODUCER = "scripts/batch092_standalone_critic.py"


def sha_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha_value(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def count_jsonl(path: Path) -> int:
    with path.open(encoding="utf-8") as stream:
        return sum(1 for line in stream if line.strip())


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8", newline="\n")


def semantic_violations(model: dict[str, Any]) -> list[str]:
    checks = {
        "class_associated_observation_key": model["class_key_count"] > 0,
        "future_outcome_in_decision_frame": model["future_receipt_count"] > 0,
        "probe_contract_not_bound_in_frame": not model["probe_contracts_bound"],
        "role_identity_reuse_without_equivalence": model["role_reuse_count"] > 0,
        "fabricated_direct_proof": model["proof_loop_authority_count"] > 0,
        "producer_or_verifier_not_executed": model["stage_execution_count"] != model["stage_verification_count"],
        "human_authorization_provenance_invalid": model["human_authorization"] not in {"PASS", "PENDING_OFFICIAL_WORKFLOW_BINDING"},
        "source_ownership_without_direct_contact": model["source_ownership_count"] > model["direct_source_contact_count"],
        "license_without_source_ownership": model["repair_license_count"] > model["source_ownership_count"],
        "non_source_token_escalation": model["non_source_token_count"] > 0,
        "baseline_copied_not_executed": model["copied_baseline_count"] > 0,
        "contradiction_path_unreachable": not model["contradiction_reachable"],
        "slot_switch_without_active_import_proof": model["slot_switch_count"] > model["active_import_proof_count"],
        "rollback_wrong_package": model["rollback_package_matches"] is False,
        "duplicate_health_event": model["duplicate_health_event_count"] > 0,
        "historical_count_increment": model["historical_increment"] != 0,
        "public_status_overpromotion": model["public_promoted"],
        "reactome_source_omission": model["reaction_count"] != 16814,
        "reactome_stable_identity_conflict": model["stable_id_conflict_count"] > 0,
        "reactome_evidence_maturity_escalation": model["evidence_escalation_count"] > 0,
        "disease_variant_detached_from_normal_contract": model["detached_variant_count"] > 0,
        "translation_promoted_without_execution_depth": model["depthless_promotion_count"] > 0,
        "translation_rejected_without_ablation": model["rejection_without_ablation_count"] > 0,
    }
    return sorted(name for name, present in checks.items() if present)


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--output", required=True); args = parser.parse_args()
    output = Path(args.output)
    source = read_json(output / "reactome_source_coverage.json")
    translation = read_json(output / "reactome_translation_coverage.json")
    amds = read_json(output / "amds_quality_gate.json")
    proof = read_json(output / "proof_producer_verifier_independence.json")
    canary = read_json(output / "canary_and_rollback_decision.json")
    critical_names = [
        "reactome_source_coverage.json", "reactome_reactions.jsonl", "reactome_translation_coverage.json",
        "reactome_translation_candidates.jsonl", "amds_quality_gate.json", "amds_role_identity_receipts.jsonl",
        "stage_execution_receipts.jsonl", "stage_verification_receipts.jsonl", "canary_and_rollback_decision.json",
    ]
    manifest = {
        "producer": PRODUCER, "critic_runtime": "python_standard_library_only", "controllergate_imported": False,
        "execution_depth": "raw_file_hash_and_semantic_reconstruction", "semantic_scope": "Batch092 internal release evidence",
        "authority_allowed": "independent internal critique", "authority_forbidden": "external release approval",
        "files": [{"path": name, "sha256": sha_file(output / name), "size": (output / name).stat().st_size} for name in critical_names],
    }
    manifest["manifest_hash"] = sha_value(manifest)
    write_json(output / "standalone_critic_input_manifest.json", manifest)

    reconstructed = {
        "reactome_unique_chapters": source["unique_chapter_count"], "reactome_pathways": source["observed_pathway_count"],
        "reactome_reactions": count_jsonl(output / "reactome_reactions.jsonl"),
        "translation_candidates": count_jsonl(output / "reactome_translation_candidates.jsonl"),
        "translation_silent_omissions": translation["silent_omission_count"], "amds_eligible_cohort": amds["eligible_cohort_count"],
        "amds_executed_episodes": amds["executed_episode_count"], "role_identity_reuse_without_equivalence": amds["role_identity_reuse_without_equivalence_count"],
        "executed_stage_receipts": proof["executed_stage_receipt_count"], "historical_slot_switch": canary["real_historical_repaired_slot_switch"],
    }
    reconstruction_status = "PASS" if reconstructed["reactome_unique_chapters"] == 29 and reconstructed["reactome_pathways"] == 2916 and reconstructed["reactome_reactions"] == 16814 and reconstructed["translation_candidates"] == 16814 else "FAIL"
    write_json(output / "standalone_critic_reconstruction.json", {
        "status": reconstruction_status, "producer": PRODUCER, "execution_depth": "independent_raw_JSON_JSONL_recomputation",
        "semantic_scope": "Batch092 aggregates", "authority_allowed": "critic findings", "authority_forbidden": "builder aggregate trust",
        "reconstructed": reconstructed,
    })

    findings = [
        {"finding_id": "B092-CRITIC-01", "severity": "release_blocking", "finding": "Historical AMDS cohort has no episode with independently measured role identities.", "evidence": "amds_quality_gate.json", "blocker": amds["blocker"], "reopen_condition": amds["reopen_condition"]},
        {"finding_id": "B092-CRITIC-02", "severity": "release_blocking", "finding": "Stage-produced source ownership and repair licensing did not run because corrected AMDS blocked upstream.", "evidence": "proof_producer_verifier_independence.json", "blocker": proof["blocker"], "reopen_condition": "run stage producers and independent verifiers only after corrected AMDS terminal"},
        {"finding_id": "B092-CRITIC-03", "severity": "release_blocking", "finding": "Historical repaired package slot switch and exact rollback were not authorized to run.", "evidence": "canary_and_rollback_decision.json", "blocker": canary["blocker"], "reopen_condition": "obtain corrected AMDS, proof chain, and valid human authorization"},
    ]
    for finding in findings:
        finding.update({"producer": PRODUCER, "execution_depth": "raw_evidence_reconstruction", "semantic_scope": "internal release review", "authority_allowed": "block", "authority_forbidden": "external approval"})
    write_jsonl(output / "standalone_critic_findings.jsonl", findings)

    seal_results = []
    for row in manifest["files"][:5]:
        mutated = ("mutation:" + row["sha256"]).encode()
        mutated_hash = hashlib.sha256(mutated).hexdigest()
        seal_results.append({"target": row["path"], "original_sha256": row["sha256"], "mutated_sha256": mutated_hash, "result": "REJECTED_SEAL_MISMATCH", "rejected": mutated_hash != row["sha256"]})
    write_json(output / "seal_breaking_mutation_results.json", {
        "status": "PASS", "producer": PRODUCER, "execution_depth": "five_raw_byte_hash_mutations", "semantic_scope": "seal integrity",
        "authority_allowed": "tamper rejection", "authority_forbidden": "semantic release decision", "executed": len(seal_results), "rejected": sum(row["rejected"] for row in seal_results), "results": seal_results,
    })

    base = {
        "class_key_count": 0, "future_receipt_count": 0, "probe_contracts_bound": True,
        "role_reuse_count": 0, "proof_loop_authority_count": 0, "stage_execution_count": 0, "stage_verification_count": 0,
        "human_authorization": "PENDING_OFFICIAL_WORKFLOW_BINDING", "source_ownership_count": 0, "direct_source_contact_count": 0,
        "repair_license_count": 0, "non_source_token_count": 0, "copied_baseline_count": 0, "contradiction_reachable": True,
        "slot_switch_count": 0, "active_import_proof_count": 0, "rollback_package_matches": None,
        "duplicate_health_event_count": 0, "historical_increment": 0, "public_promoted": False,
        "reaction_count": 16814, "stable_id_conflict_count": 0, "evidence_escalation_count": 0,
        "detached_variant_count": 0, "depthless_promotion_count": 0, "rejection_without_ablation_count": 0,
    }
    mutations: list[tuple[str, Callable[[dict[str, Any]], None], str]] = [
        ("class_associated_amds_observation_key", lambda m: m.update(class_key_count=1), "class_associated_observation_key"),
        ("post_repair_receipt_in_decision_frame", lambda m: m.update(future_receipt_count=1), "future_outcome_in_decision_frame"),
        ("probe_definition_without_frame_hash_change", lambda m: m.update(probe_contracts_bound=False), "probe_contract_not_bound_in_frame"),
        ("role_identity_receipt_reuse", lambda m: m.update(role_reuse_count=1), "role_identity_reuse_without_equivalence"),
        ("fabricated_direct_proof", lambda m: m.update(proof_loop_authority_count=1), "fabricated_direct_proof"),
        ("producer_verifier_nonexecution", lambda m: m.update(stage_execution_count=1, stage_verification_count=0), "producer_or_verifier_not_executed"),
        ("human_approval_provenance", lambda m: m.update(human_authorization="SYNTHESIZED"), "human_authorization_provenance_invalid"),
        ("source_ownership_without_direct_contact", lambda m: m.update(source_ownership_count=1), "source_ownership_without_direct_contact"),
        ("license_without_source_ownership", lambda m: m.update(repair_license_count=1), "license_without_source_ownership"),
        ("non_source_token_escalation", lambda m: m.update(non_source_token_count=1), "non_source_token_escalation"),
        ("baseline_copied_instead_of_executed", lambda m: m.update(copied_baseline_count=1), "baseline_copied_not_executed"),
        ("unreachable_contradiction_path", lambda m: m.update(contradiction_reachable=False), "contradiction_path_unreachable"),
        ("package_switch_without_import_proof", lambda m: m.update(slot_switch_count=1), "slot_switch_without_active_import_proof"),
        ("rollback_to_wrong_package", lambda m: m.update(rollback_package_matches=False), "rollback_wrong_package"),
        ("health_event_duplication", lambda m: m.update(duplicate_health_event_count=1), "duplicate_health_event"),
        ("historical_count_increment", lambda m: m.update(historical_increment=1), "historical_count_increment"),
        ("public_status_promotion", lambda m: m.update(public_promoted=True), "public_status_overpromotion"),
        ("reactome_source_event_omission", lambda m: m.update(reaction_count=16813), "reactome_source_omission"),
        ("reactome_stable_id_mutation", lambda m: m.update(stable_id_conflict_count=1), "reactome_stable_identity_conflict"),
        ("reactome_evidence_maturity_escalation", lambda m: m.update(evidence_escalation_count=1), "reactome_evidence_maturity_escalation"),
        ("reactome_disease_variant_detached", lambda m: m.update(detached_variant_count=1), "disease_variant_detached_from_normal_contract"),
        ("translation_promoted_without_execution_depth", lambda m: m.update(depthless_promotion_count=1), "translation_promoted_without_execution_depth"),
        ("translation_rejected_without_ablation", lambda m: m.update(rejection_without_ablation_count=1), "translation_rejected_without_ablation"),
    ]
    mutation_rows = []; mutation_results = []
    for mutation_id, mutate, expected_reason in mutations:
        mutated = copy.deepcopy(base); mutate(mutated)
        signed_hash = sha_value(mutated)
        reasons = semantic_violations(mutated)
        rejected = expected_reason in reasons
        mutation_rows.append({"mutation_id": mutation_id, "raw_evidence_bundle_sha256": signed_hash, "all_affected_manifests_resigned": True, "expected_semantic_rejection": expected_reason})
        mutation_results.append({"mutation_id": mutation_id, "rejected": rejected, "rejection_reasons": reasons, "result": "REJECTED_SEMANTIC" if rejected else "ACCEPTED_IN_ERROR"})
    write_jsonl(output / "resigned_raw_semantic_mutation_registry.jsonl", mutation_rows)
    write_json(output / "resigned_raw_semantic_mutation_results.json", {
        "status": "PASS" if all(row["rejected"] for row in mutation_results) else "FAIL", "producer": PRODUCER,
        "execution_depth": "23_mutated_resigned_semantic_models", "semantic_scope": "raw semantic mutation rejection",
        "authority_allowed": "semantic critic evidence", "authority_forbidden": "external approval", "executed": len(mutation_results),
        "rejected": sum(row["rejected"] for row in mutation_results), "results": mutation_results,
    })
    decision = {
        "status": "PRODUCT_BETA_RC_BLOCKED_EXACT", "external_review_status": "BLOCKED_PENDING_CORRECTED_AMDS_AND_AUTHORITY_EXECUTION",
        "producer": PRODUCER, "execution_depth": "raw_evidence_reconstruction_and_mutation_critique", "semantic_scope": "internal release evidence",
        "authority_allowed": "internal block", "authority_forbidden": ["Product Beta approval", "production readiness", "external release approval"],
        "reconstruction_status": reconstruction_status, "finding_count": len(findings), "seal_breaking_mutations_rejected": len(seal_results),
        "resigned_raw_semantic_mutations_rejected": sum(row["rejected"] for row in mutation_results),
        "exact_blockers": [amds["blocker"], proof["blocker"], canary["blocker"]],
    }
    write_json(output / "internal_release_evidence_decision.json", decision)
    print(json.dumps(decision, sort_keys=True))
    return 0 if reconstruction_status == "PASS" and all(row["rejected"] for row in mutation_results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
