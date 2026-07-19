from __future__ import annotations

import argparse
import copy
import hashlib
import json
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import Any, Callable


MUTATIONS = [
    "causal_truth_class", "abstention_expectation", "scoreability", "candidate_truth_record_swap",
    "truth_timestamp_before_terminal", "truth_builder_reads_observed_terminal", "accepted_fix_identity_removal",
    "frozen_source_commit_binding", "independent_truth_verifier_removal", "observed_partition_key",
    "first_partition_forcing", "unmatched_partition_promoted_to_fact", "generic_causal_terminal_substitution",
    "terminal_cell_removal", "alternative_exclusion_removal", "false_legal_probe_exhaustion",
    "arm_relabel_without_frame_change", "synthetic_component_probe_counted_as_ablation", "baseline_i_relabel",
    "baseline_j_diagnostic_execution", "opaque_plan_post_execution_mutation", "source_ownership_from_sealed_truth",
    "wrong_causal_class_scored_correct", "causal_case_abstention_scored_correct",
    "abstention_required_causal_claim_scored_correct", "copied_macro_accuracy", "unresolved_truth_included_scoreable",
    "repair_count_increment", "product_beta_promotion", "public_claim_boundary_mutation",
]


def lines(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def put_lines(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in rows), encoding="utf-8", newline="\n")


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def put(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()


def resign(root: Path) -> dict[str, Any]:
    rows = []
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.name != "SHA256SUMS.txt":
            rows.append({"path": path.relative_to(root).as_posix(), "size": path.stat().st_size, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    put_lines(root / "SHA256SUMS.txt", rows)
    failures = [row["path"] for row in rows if hashlib.sha256((root / row["path"]).read_bytes()).hexdigest() != row["sha256"]]
    return {"status": "PASS" if not failures else "BLOCK", "entries": len(rows), "failures": failures}


def semantic_critic(root: Path, frozen: dict[str, Any]) -> list[str]:
    findings: list[str] = []
    truth = lines(root / "candidate_truth_records_v2.jsonl")
    truth_by = {row["candidate_id"]: row for row in truth}
    if {row["candidate_id"]: digest(row) for row in truth} != frozen["truth_record_hashes"]:
        findings.append("truth_record_semantics_changed_after_freeze")
    for row in truth:
        if row["scoreability"] == "SCOREABLE_CAUSAL" and (row["causal_class"] in {"UNRESOLVED_TRUTH", "ABSTENTION_REQUIRED"} or not row["alternative_exclusions"] or not row["direct_causal_contact"]):
            findings.append("invalid_scoreable_causal_truth")
        if row["scoreability"] == "SCOREABLE_ABSTENTION" and (row["causal_class"] != "ABSTENTION_REQUIRED" or not row["abstention_expected"]):
            findings.append("invalid_scoreable_abstention_truth")
        if row["scoreability"] == "SCOREABLE_CAUSAL" and not row.get("accepted_fix_identity"):
            findings.append("accepted_fix_identity_missing")
        if not row.get("independent_verifier") or row.get("producer") == row.get("independent_verifier"):
            findings.append("independent_truth_verifier_missing")
        if not row.get("truth_created_after_terminal"):
            findings.append("truth_timestamp_precedes_terminal")
    blindness = load(root / "private_truth_builder_outcome_blindness_audit.json")
    if any(blindness.get(key, 0) for key in ("observed_terminal_value_access_count", "arm_result_access_count", "probe_outcome_access_count", "score_access_count")):
        findings.append("truth_builder_outcome_access")
    observations = lines(root / "public_neutral_observations_v2.jsonl")
    for row in observations:
        expected = f"{row['probe_kind']}_observed" if row.get("partition_evidence", {}).get("kind_matches") else f"{row['probe_kind']}_not_observed"
        if row.get("partition_key") and row["partition_key"] != expected:
            findings.append("partition_not_bound_to_observation")
        if row.get("partition_key") is None and row.get("positive_fact_proposals"):
            findings.append("unmatched_partition_promoted")
        if row.get("partition_evidence", {}).get("resolution_reason") == "first declared partition":
            findings.append("first_partition_forcing")
    terminals = lines(root / "controller_audit_terminal_records_v2.jsonl")
    allowed = {"SOURCE_OWNED_BEHAVIOR_DEFECT","PROVIDER_OWNED","ENVIRONMENT_PLATFORM_OWNED","RUNNER_OWNED","HARNESS_FIXTURE_OWNED","SERVICE_TRANSPORT_OWNED","TEST_EXPECTATION_FRAGILITY","MIXED_FAILURE","INSUFFICIENT_EVIDENCE"}
    for row in terminals:
        if row["terminal_class"] not in allowed:
            findings.append("generic_or_invalid_terminal")
        if not row.get("terminal_cell_id"):
            findings.append("terminal_cell_missing")
        if row["terminal_class"] != "INSUFFICIENT_EVIDENCE" and not row.get("alternative_exclusion_ids"):
            findings.append("causal_terminal_missing_alternative_exclusion")
        exhaustion = row["legal_probe_exhaustion_receipt"]
        if exhaustion["status"] == "PASS" and exhaustion["executed"] + exhaustion["remaining"] != exhaustion["registered"]:
            findings.append("false_legal_probe_exhaustion")
    frames = lines(root / "arm_specific_frame_registry_v2.jsonl")
    expected_components = frozen["arm_components"]
    for row in frames:
        if sorted(row["component_registry"]) != sorted(expected_components.get(row["arm_id"], [])):
            findings.append("arm_relabel_or_component_inventory_invalid")
        if row.get("synthetic_component_probe_count", 0):
            findings.append("synthetic_component_probe_used")
    baselines = lines(root / "baseline_policy_registry_v2.jsonl")
    by_baseline = {row["baseline_id"]: row for row in baselines}
    if by_baseline["I"]["policy"] != "no_memory_active_minimax" or not by_baseline["I"]["adaptive"]:
        findings.append("baseline_i_not_distinct")
    if by_baseline["J"]["executes_probes"]:
        findings.append("baseline_j_executes_diagnostics")
    plans = lines(root / "batch098_opaque_probe_plan_registry_v2.jsonl")
    for row in plans:
        actual = row.pop("plan_hash")
        expected = digest(row)
        row["plan_hash"] = actual
        if actual != expected:
            findings.append("opaque_plan_mutated_after_freeze")
    source_proofs = lines(root / "decision_time_source_ownership_proofs_v2.jsonl")
    if any(row.get("sealed_truth_access_count", 0) for row in source_proofs):
        findings.append("source_ownership_derived_from_truth")
    joins = lines(root / "private_truth_join_v2.jsonl")
    for row in joins:
        truth_row = truth_by[row["candidate_id"]]
        terminal = row["observed_terminal_class"]
        if truth_row["scoreability"] == "NOT_SCOREABLE" and row["correct"] is not None:
            findings.append("unresolved_truth_scored")
        if truth_row["scoreability"] == "SCOREABLE_CAUSAL":
            expected_correct = terminal == truth_row["causal_class"]
            if row["correct"] != expected_correct:
                findings.append("causal_case_scoring_incorrect")
        if truth_row["scoreability"] == "SCOREABLE_ABSTENTION":
            expected_correct = terminal == "INSUFFICIENT_EVIDENCE"
            if row["correct"] != expected_correct:
                findings.append("abstention_case_scoring_incorrect")
    scores = lines(root / "arm_historical_scores_v2.jsonl")
    if scores != frozen["arm_scores"]:
        findings.append("aggregate_score_not_reconstructed")
    claim = load(root / "batch098_private_truth_semantic_closure_claim_boundary.json")
    if claim.get("ordinary_patches") != 0 or claim.get("historical_increment") != 0 or claim.get("issue_derived_repairs") != 6:
        findings.append("repair_or_count_boundary_mutated")
    if claim.get("release_decision") != "PRODUCT_BETA_RC_BLOCKED_EXACT" or claim.get("production_readiness") is not False:
        findings.append("product_beta_or_public_boundary_promoted")
    return sorted(set(findings))


def apply_mutation(name: str, root: Path) -> None:
    truth_path = root / "candidate_truth_records_v2.jsonl"
    truth = lines(truth_path)
    observations_path = root / "public_neutral_observations_v2.jsonl"
    observations = lines(observations_path)
    terminals_path = root / "controller_audit_terminal_records_v2.jsonl"
    terminals = lines(terminals_path)
    frames_path = root / "arm_specific_frame_registry_v2.jsonl"
    frames = lines(frames_path)
    baselines_path = root / "baseline_policy_registry_v2.jsonl"
    baselines = lines(baselines_path)
    joins_path = root / "private_truth_join_v2.jsonl"
    joins = lines(joins_path)
    scores_path = root / "arm_historical_scores_v2.jsonl"
    scores = lines(scores_path)
    claim_path = root / "batch098_private_truth_semantic_closure_claim_boundary.json"
    claim = load(claim_path)
    if name == "causal_truth_class": truth[0]["causal_class"] = "RUNNER_OWNED"
    elif name == "abstention_expectation": truth[0]["abstention_expected"] = True
    elif name == "scoreability": truth[0]["scoreability"] = "SCOREABLE_ABSTENTION"
    elif name == "candidate_truth_record_swap": truth[0]["candidate_id"], truth[1]["candidate_id"] = truth[1]["candidate_id"], truth[0]["candidate_id"]
    elif name == "truth_timestamp_before_terminal": truth[0]["truth_created_after_terminal"] = False
    elif name == "truth_builder_reads_observed_terminal":
        blind = load(root / "private_truth_builder_outcome_blindness_audit.json"); blind["observed_terminal_value_access_count"] = 1; put(root / "private_truth_builder_outcome_blindness_audit.json", blind)
    elif name == "accepted_fix_identity_removal": truth[0]["accepted_fix_identity"] = None
    elif name == "frozen_source_commit_binding": truth[0]["frozen_buggy_commit"] = "0" * 40
    elif name == "independent_truth_verifier_removal": truth[0]["independent_verifier"] = ""
    elif name == "observed_partition_key": observations[0]["partition_key"] = f"{observations[0]['probe_kind']}_not_observed"
    elif name == "first_partition_forcing": observations[0]["partition_evidence"]["resolution_reason"] = "first declared partition"
    elif name == "unmatched_partition_promoted_to_fact": observations[0]["partition_key"] = None; observations[0]["positive_fact_proposals"] = ["invalid-fact"]
    elif name == "generic_causal_terminal_substitution": terminals[0]["terminal_class"] = "PROVISIONAL_CAUSAL_TERMINAL"
    elif name == "terminal_cell_removal": terminals[0]["terminal_cell_id"] = None
    elif name == "alternative_exclusion_removal": truth[0]["alternative_exclusions"] = []
    elif name == "false_legal_probe_exhaustion": terminals[0]["legal_probe_exhaustion_receipt"]["executed"] += 1
    elif name == "arm_relabel_without_frame_change": frames[0]["arm_id"] = "F"
    elif name == "synthetic_component_probe_counted_as_ablation": frames[0]["synthetic_component_probe_count"] = 1
    elif name == "baseline_i_relabel": next(row for row in baselines if row["baseline_id"] == "I")["policy"] = "fixed_registered_order"
    elif name == "baseline_j_diagnostic_execution": next(row for row in baselines if row["baseline_id"] == "J")["executes_probes"] = True
    elif name == "opaque_plan_post_execution_mutation":
        plan_path = root / "batch098_opaque_probe_plan_registry_v2.jsonl"; plans = lines(plan_path); plans[0]["ordered_opaque_probe_ids"].reverse(); put_lines(plan_path, plans)
    elif name == "source_ownership_from_sealed_truth":
        proof_path = root / "decision_time_source_ownership_proofs_v2.jsonl"; proofs = lines(proof_path); proofs.append({"candidate_id":truth[0]["candidate_id"],"arm_id":"A","sealed_truth_access_count":1}); put_lines(proof_path, proofs)
    elif name == "wrong_causal_class_scored_correct": joins[0]["observed_terminal_class"] = "RUNNER_OWNED"; joins[0]["correct"] = True
    elif name == "causal_case_abstention_scored_correct": joins[0]["observed_terminal_class"] = "INSUFFICIENT_EVIDENCE"; joins[0]["correct"] = True
    elif name == "abstention_required_causal_claim_scored_correct": truth[0]["scoreability"]="SCOREABLE_ABSTENTION"; truth[0]["causal_class"]="ABSTENTION_REQUIRED"; truth[0]["abstention_expected"]=True; joins[0]["observed_terminal_class"]="RUNNER_OWNED"; joins[0]["correct"]=True
    elif name == "copied_macro_accuracy": scores[0]["macro_accuracy"] = 1.0
    elif name == "unresolved_truth_included_scoreable": next(row for row in truth if row["causal_class"] == "UNRESOLVED_TRUTH")["scoreability"] = "SCOREABLE_CAUSAL"
    elif name == "repair_count_increment": claim["historical_increment"] = 1
    elif name == "product_beta_promotion": claim["release_decision"] = "PRODUCT_BETA_RC_PASS"
    elif name == "public_claim_boundary_mutation": claim["production_readiness"] = True
    put_lines(truth_path, truth); put_lines(observations_path, observations); put_lines(terminals_path, terminals)
    put_lines(frames_path, frames); put_lines(baselines_path, baselines); put_lines(joins_path, joins); put_lines(scores_path, scores); put(claim_path, claim)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--corrected-artifact", required=True)
    parser.add_argument("--sealed-truth-bundle", required=True)
    parser.add_argument("--opaque-plan-registry", required=True)
    parser.add_argument("--scoring-output", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    corrected = Path(args.corrected_artifact)
    scoring = Path(args.scoring_output)
    output = Path(args.output); output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="batch098-semantic-mutation-base-") as temporary:
        base = Path(temporary) / "base"; base.mkdir()
        for name in ("public_neutral_observations_v2.jsonl","controller_audit_terminal_records_v2.jsonl","arm_specific_frame_registry_v2.jsonl","baseline_policy_registry_v2.jsonl","decision_time_source_ownership_proofs_v2.jsonl"):
            shutil.copy2(corrected / name, base / name)
        for name in ("private_truth_join_v2.jsonl","arm_historical_scores_v2.jsonl","batch098_private_truth_semantic_closure_claim_boundary.json"):
            shutil.copy2(scoring / name, base / name)
        shutil.copy2(args.opaque_plan_registry, base / "batch098_opaque_probe_plan_registry_v2.jsonl")
        with zipfile.ZipFile(args.sealed_truth_bundle) as archive:
            for name in ("candidate_truth_records_v2.jsonl","private_truth_builder_outcome_blindness_audit.json"):
                (base / name).write_bytes(archive.read(name))
        truth = lines(base / "candidate_truth_records_v2.jsonl")
        frozen = {
            "truth_record_hashes": {row["candidate_id"]: digest(row) for row in truth},
            "arm_components": {"A":["canonical_amds"],"B":["canonical_amds","tot_bulb"],"C":["canonical_amds","local_brot"],"D":["canonical_amds","tot_bulb","local_brot","executed_tot_brot_projection"],"E":["canonical_amds","tot_bulb","local_brot","executed_tot_brot_projection","opaque_tld_ordering"],"F":["canonical_amds","tot_bulb","local_brot","executed_tot_brot_projection","opaque_tld_ordering","observer_state","provisional_state","modalities"],"G":[],"H":[],"I":[],"J":[]},
            "arm_scores": lines(base / "arm_historical_scores_v2.jsonl"),
        }
        if semantic_critic(base, frozen):
            raise SystemExit("unmutated critic input does not pass")
        results = []
        findings = []
        for index, mutation in enumerate(MUTATIONS, 1):
            tree = Path(temporary) / f"mutation-{index:02d}"
            shutil.copytree(base, tree)
            apply_mutation(mutation, tree)
            manifest = resign(tree)
            violations = semantic_critic(tree, frozen)
            rejected = bool(violations)
            row = {
                "mutation_id": f"B098-SEM-{index:02d}", "mutation": mutation,
                "complete_copied_raw_evidence_tree": True, "affected_seals_recomputed": True,
                "manifest_status_after_resign": manifest["status"], "semantic_rejected": rejected,
                "critic_findings": violations, "status": "PASS" if manifest["status"] == "PASS" and rejected else "BLOCK",
            }
            results.append(row)
            findings.extend({"mutation_id":row["mutation_id"],"finding":finding,"severity":"BLOCK"} for finding in violations)
    put_lines(output / "resigned_raw_semantic_mutation_registry_v2.jsonl", results)
    put_lines(output / "standalone_semantic_critic_findings_v2.jsonl", findings)
    summary = {
        "status":"PASS" if len(results) >= 30 and all(row["status"] == "PASS" for row in results) else "BLOCK",
        "complete_copied_raw_evidence_tree_mutation":True,"semantic_mutations_executed":len(results),
        "semantic_mutations_rejected":sum(row["semantic_rejected"] for row in results),
        "manifest_resign_pass_count":sum(row["manifest_status_after_resign"] == "PASS" for row in results),
        "independent_critic":"scripts.batch098_semantic_mutations_v2.semantic_critic",
        "authority_allowed":"historical evidence mutation-resistance audit only",
        "authority_forbidden":["repair","repair count","release"]
    }
    put(output / "resigned_raw_semantic_mutation_results_v2.json", summary)
    put(output / "complete_copied_raw_evidence_tree_mutation_v2.json", summary)
    put(output / "standalone_semantic_critic_reconstruction_v2.json", {"status":"PASS","unmutated_tree_findings":0,"mutation_finding_count":len(findings),"raw_inputs_reconstructed":True})
    return 0 if summary["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
