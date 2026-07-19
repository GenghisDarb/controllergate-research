from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REQUIRED = [
    ROOT / "controllergate/evidence/private_truth_v2.py",
    ROOT / "controllergate/amds/semantic_closure_v8.py",
    ROOT / "controllergate/amds/historical_scoring_v8.py",
    ROOT / "scripts/build_batch098_private_sealed_truth.py",
    ROOT / "scripts/verify_batch098_private_sealed_truth.py",
    ROOT / "scripts/rebuild_batch098_private_sealed_truth.py",
    ROOT / "scripts/run_batch098_public_truth_blind_semantic_closure.py",
    ROOT / "scripts/batch098_semantic_mutations_v2.py",
    ROOT / "configs/batch098_opaque_probe_plan_registry_v2.jsonl",
]


def main() -> int:
    findings = []
    for path in REQUIRED:
        if not path.is_file() or path.stat().st_size == 0:
            findings.append(f"missing:{path.relative_to(ROOT).as_posix()}")
    executor = (ROOT / "controllergate/evidence/probe_executor_v2.py").read_text(encoding="utf-8")
    runtime = (ROOT / "controllergate/amds/semantic_closure_v8.py").read_text(encoding="utf-8")
    finalizer = (ROOT / "scripts/finalize_batch098_hybrid_private_run.py").read_text(encoding="utf-8")
    mutations = (ROOT / "scripts/batch098_semantic_mutations_v2.py").read_text(encoding="utf-8")
    checks = {
        "observation_bound_partition": "resolve_observed_partition" in executor and 'next(iter(' not in executor,
        "iterative_one_probe_round": "while remaining:" in runtime and "execute_probe_contract(selected" in runtime,
        "causal_terminal_v2": "terminal_class" in runtime and "PROVISIONAL_CAUSAL_TERMINAL" not in runtime,
        "arm_specific_frames": "compile_arm_frame" in runtime and "ARM_COMPONENTS" in runtime,
        "real_baseline_policies": "constant_insufficient_evidence_no_probes" in runtime and "no_memory_active_minimax" in runtime,
        "sealed_truth_required": 'parser.add_argument("--sealed-truth-bundle", required=True)' in finalizer,
        "flat_truth_rejected": "expected_by_candidate" not in finalizer,
        "causal_class_scoring": "classify_join" in finalizer and "terminal_class" in finalizer,
        "source_ownership_reconstructed": '"fixed_constant_used":False' in finalizer,
        "semantic_mutation_depth": len(MUTATION_NAMES.intersection(set(mutations.split('"')))) >= 30,
        "claim_boundary_preserved": "PRODUCT_BETA_RC_BLOCKED_EXACT" in finalizer,
    }
    findings.extend(f"check:{name}" for name, passed in checks.items() if not passed)
    plan_rows = [json.loads(line) for line in (ROOT / "configs/batch098_opaque_probe_plan_registry_v2.jsonl").read_text(encoding="utf-8").splitlines() if line]
    if len(plan_rows) != 16 or {row["arm_id"] for row in plan_rows} != {"E", "F"}:
        findings.append("corrected_opaque_plan_registry")
    result = {
        "status": "PASS" if not findings else "BLOCK",
        "result": "BATCH098_PRIVATE_TRUTH_SEMANTIC_CLOSURE_PASS" if not findings else "BATCH098_PRIVATE_TRUTH_SEMANTIC_CLOSURE_BLOCK",
        "checks": checks, "findings": findings,
        "ordinary_patch_authority": False, "protected_historical_actuation": False,
        "claim_boundary": "PRODUCT_BETA_RC_BLOCKED_EXACT",
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not findings else 1


MUTATION_NAMES = {
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
}


if __name__ == "__main__":
    raise SystemExit(main())
