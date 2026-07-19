from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_HEAD = "254febdab654a090c126d9b5232b92a8b7dea703"
OUTPUT = ROOT / "outputs" / "post_v2_37_hardening_batch098_causal_hypergraph_real_materialization_topology_probe_closure" / "batch098_pre_private_truth_semantic_closure_expected_failure.json"


def source_at(path: str) -> str:
    result = subprocess.run(
        ["git", "show", f"{EXPECTED_HEAD}:{path}"], cwd=ROOT, capture_output=True, text=True, check=True
    )
    return result.stdout


def line_for(source: str, needle: str) -> int:
    for number, line in enumerate(source.splitlines(), 1):
        if needle in line:
            return number
    return 1


def finding(finding_id: str, path: str, symbol: str, needle: str, risk: str, correction: str, test: str) -> dict[str, object]:
    source = source_at(path)
    line = line_for(source, needle)
    return {
        "finding_id": finding_id,
        "commit": EXPECTED_HEAD,
        "path": path,
        "symbol": symbol,
        "line_range": f"{line}-{line}",
        "detected": needle in source,
        "risk": risk,
        "required_correction": correction,
        "red_to_green_test": test,
    }


def main() -> int:
    specs = [
        ("B098-PTS-001", "scripts/finalize_batch098_hybrid_private_run.py", "main", 'truth.get("expected_by_candidate", {})', "Flat truth dictionaries are not candidate-bound evidence.", "Require a verified sealed CandidateTruthRecordV2 bundle.", "test_flat_truth_dictionary_rejected"),
        ("B098-PTS-002", "scripts/finalize_batch098_hybrid_private_run.py", "main", 'terminal["terminal"] == gold', "Generic strings can be scored as causal truth.", "Compare terminal_class with verified causal_class under scoreability rules.", "test_generic_terminal_string_not_scored"),
        ("B098-PTS-003", "scripts/finalize_batch098_hybrid_private_run.py", "main", "expected = truth.get", "Truth is not bound to repository, incident, commit, contract, fix, or regression evidence.", "Validate all CandidateTruthRecordV2 identity bindings.", "test_truth_record_identity_bindings"),
        ("B098-PTS-004", "scripts/finalize_batch098_hybrid_private_run.py", "main", "sealed_truth.read_text", "Truth construction is trusted without an independent verifier receipt.", "Verify deterministic bundle, producer/verifier independence, and rebuild identity.", "test_unverified_truth_bundle_rejected"),
        ("B098-PTS-005", "controllergate/amds/stage_runtime_v7.py", "execute_stage", 'result["terminal"] = "PROVISIONAL_CAUSAL_TERMINAL"', "ControllerAudit emits a generic causal terminal.", "Emit the causal terminal contract V2 fields and classes.", "test_controller_audit_terminal_contract_v2"),
        ("B098-PTS-006", "controllergate/amds/stage_runtime_v7.py", "execute_stage", 'result["terminal"] = "INSUFFICIENT_EVIDENCE"', "Terminal records omit a candidate-bound causal class.", "Bind class, cell, hypothesis, facts, observations, exclusions, and scope.", "test_causal_terminal_is_candidate_bound"),
        ("B098-PTS-007", "controllergate/amds/stage_runtime_v7.py", "execute_stage", 'next(iter(probe["predicted_neutral_partitions"]))', "Constraint updates select the first declared partition.", "Resolve partitions from verified structured observations only.", "test_first_partition_default_count_zero"),
        ("B098-PTS-008", "controllergate/evidence/probe_executor_v2.py", "execute_probe_contract", 'verification = {', "Semantic verification has no explicit observation-bound partition_key.", "Return partition_key, evidence, fact proposals, and unmatched reason.", "test_semantic_verifier_returns_partition_key"),
        ("B098-PTS-009", "controllergate/amds/stage_runtime_v7.py", "execute_stage", "for index, probe in enumerate(ordered):", "All probes execute before the first constraint update.", "Execute one selected probe per DPP round.", "test_probe_selection_update_interleaving"),
        ("B098-PTS-010", "controllergate/amds/stage_runtime_v7.py", "run_dpp14", "for index, stage in enumerate(STAGES):", "The planner cannot react to the first observation.", "Recompute the frontier and next probe after every verified observation.", "test_second_probe_depends_on_first_observation"),
        ("B098-PTS-011", "controllergate/amds/stage_runtime_v7.py", "run_dpp14", "return state, producer_rows, verifier_rows", "DPP-14 has one pass and no round registry.", "Iterate fourteen stages per round until terminal or explicit exhaustion.", "test_iterative_dpp14_rounds"),
        ("B098-PTS-012", "scripts/run_batch098_public_truth_blind.py", "component_probe", 'value["probe_kind"] = "boundary_dimension"', "Synthetic reachability probes stand in for architecture activation.", "Compile arm-specific frames with real component effects.", "test_synthetic_component_reachability_retired"),
        ("B098-PTS-013", "scripts/run_batch098_public_truth_blind.py", "component_probe", 'source_cell_or_edge_or_region', "Component execution does not change the board or planner.", "Prove cell, edge, constraint, and legal-inventory additions/removals.", "test_arm_components_change_compiled_frame"),
        ("B098-PTS-014", "scripts/run_batch098_public_truth_blind.py", "main", 'for arm_id in "ABCDEFGHIJ":', "All arms reuse one frame and probe inventory.", "Compile and hash each arm frame independently.", "test_arm_specific_frame_hashes"),
        ("B098-PTS-015", "scripts/run_batch098_public_truth_blind.py", "BASELINE_COMPONENTS", '"I": ("no_memory_active_planner",)', "Baseline I is only a component label.", "Implement a distinct no-memory active planner policy.", "test_baseline_i_policy_distinct"),
        ("B098-PTS-016", "scripts/run_batch098_public_truth_blind.py", "BASELINE_COMPONENTS", '"J": ("majority_baseline",)', "Baseline J still executes diagnostic probes.", "Implement a zero-probe registered constant/majority baseline.", "test_baseline_j_executes_zero_probes"),
        ("B098-PTS-017", "scripts/finalize_batch098_hybrid_private_run.py", "main", '"macro_accuracy"', "Scoring cannot produce per-class confusion matrices.", "Implement scoreability-aware per-arm confusion matrices.", "test_historical_confusion_matrices"),
        ("B098-PTS-018", "scripts/finalize_batch098_hybrid_private_run.py", "main", '"correct": terminal["terminal"] == gold', "Scoring conflates causal abstention, correct abstention, false attribution, and unresolved truth.", "Apply explicit causal and abstention scoring rules.", "test_scoring_case_taxonomy"),
        ("B098-PTS-019", "scripts/finalize_batch098_hybrid_private_run.py", "main", '"source_ownership_proof_count": 0', "Source-ownership proof count is hardcoded.", "Reconstruct decision-time source proofs only for eligible source terminals.", "test_source_ownership_reconstructed_not_fixed"),
        ("B098-PTS-020", "scripts/finalize_batch098_hybrid_private_run.py", "semantic_mutation_control", '"mutation": "truth_access_count_zero_to_one"', "Only one semantic mutation is exercised.", "Execute and reject at least thirty structured semantic mutations.", "test_complete_semantic_mutation_depth"),
        ("B098-PTS-021", "scripts/finalize_batch098_hybrid_private_run.py", "semantic_mutation_control", 'write_json(output / "complete_copied_raw_tree_mutation_result.json"', "The compact artifact lacks mutation coverage over truth, partitions, terminals, arms, scoring, and authority.", "Copy full relevant trees, re-sign them, and independently reject every mutation family.", "test_complete_raw_tree_mutation_coverage"),
    ]
    findings = [finding(*spec) for spec in specs]
    result = {
        "status": "BATCH098_PRE_PRIVATE_TRUTH_SEMANTIC_CLOSURE_FAIL_EXPECTED",
        "expected_starting_head": EXPECTED_HEAD,
        "observed_starting_head": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip(),
        "finding_count": len(findings),
        "all_findings_detected": all(row["detected"] for row in findings),
        "findings": findings,
        "producer": "scripts/audit_batch098_pre_private_truth_semantic_closure.py",
        "execution_depth": "Git-object inspection of the untouched parent commit",
        "semantic_scope": "expected-red private truth and semantic closure gaps",
        "authority_allowed": "implementation gate only",
        "authority_forbidden": ["scientific pass", "repair", "count", "release"],
    }
    canonical = json.dumps(result, sort_keys=True, separators=(",", ":")).encode()
    result["expected_red_seal_sha256"] = hashlib.sha256(canonical).hexdigest()
    OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(result["status"])
    print(f"finding_count={result['finding_count']}")
    print(f"all_findings_detected={str(result['all_findings_detected']).lower()}")
    return 0 if result["all_findings_detected"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
