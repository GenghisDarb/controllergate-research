from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "outputs/post_v2_37_hardening_batch092_reactome_complete_pathway_ir_external_review_correction"
STARTING_HEAD = "1c13c97b1d251e79065eb64a425b9666ed410d51"
RESULT = "BATCH092_PRE_FIX_EXTERNAL_REVIEW_FAIL_EXPECTED"


def _finding(
    finding_id: str,
    path: str,
    symbol: str,
    line_range: str,
    raw_evidence: str,
    risk: str,
    correction: str,
    test: str,
) -> dict[str, Any]:
    return {
        "finding_id": finding_id,
        "commit": STARTING_HEAD,
        "path": path,
        "symbol": symbol,
        "line_range": line_range,
        "raw_evidence": raw_evidence,
        "risk": risk,
        "required_correction": correction,
        "red_to_green_test": test,
    }


FINDINGS = [
    _finding("B091-ER-01", "configs/batch091_amds_measurement_contracts.json", "candidates[*].measurement", "4-64", "candidate rows carry class-associated observed_* keys", "terminal class is encoded in the measurement contract", "replace class-associated keys with role-specific neutral records", "test_batch092_rejects_class_associated_observation_keys"),
    _finding("B091-ER-02", "scripts/batch091_sanitize_amds_inputs.py", "main", "46-75", "expanded_receipts = (receipts * 2)[:4] and signal is printed", "duplicated old receipts become answer-bearing probes", "materialize candidate-specific probes from independent role receipts", "test_batch092_sanitizer_has_no_duplicate_receipts_or_answer_key"),
    _finding("B091-ER-03", "controllergate/amds/dpp14/blind_runtime.py", "_update", "49-62", "signals maps observed_* keys directly to terminal families", "probe output directly selects the terminal", "derive semantic facts through registered verifiers and causal-board constraints", "test_batch092_terminal_not_selected_by_observation_key"),
    _finding("B091-ER-04", "configs/batch091_amds_measurement_contracts.json", "cloudpickle/freezegun receipts", "20-32", "post_repair_results and duplicate_postpatch_full_target_result are decision inputs", "future outcome evidence contaminates diagnosis", "exclude post-repair, validation, fixed, gold, and future records", "test_batch092_rejects_post_repair_and_future_receipts"),
    _finding("B091-ER-05", "scripts/batch091_sanitize_amds_inputs.py", "episode role assignment", "76-87", "two receipt objects are reused for five semantic roles", "role identity is asserted rather than measured", "require one independently verified receipt per role or an equivalence proof", "test_batch092_role_receipt_reuse_requires_equivalence_proof"),
    _finding("B091-ER-06", "scripts/run_batch091_blinded_amds.py", "execute eligibility", "68-76", "eligibility checks 64-character hashes and literal booleans", "syntactic receipt shape is treated as semantic provenance", "verify receipt producer, role, source, timing, and custody", "test_batch092_role_receipt_semantic_validation"),
    _finding("B091-ER-07", "controllergate/amds/dpp14/blind_runtime.py", "run_blind_episode", "71-74", "frame_hash excludes the probes key", "probe definitions can change without changing the decision frame", "bind probe contracts and plans into the frozen frame hash", "test_batch092_probe_contract_is_frame_bound"),
    _finding("B091-ER-08", "scripts/run_batch091_blinded_amds.py", "execute", "83-96", "blind runtime owns the terminal while canonical DPP-14 output is ignored", "the canonical causal-board path is bypassed", "make causal_board and probe_planner own terminal production", "test_batch092_canonical_causal_board_owns_terminal"),
    _finding("B091-ER-09", "scripts/run_batch091_blinded_amds.py", "execute canonical compatibility trace", "87-95", "canonical probes execute print('receipt_probe_executed=true')", "synthetic compatibility traces do not measure the candidate", "execute candidate-specific registered probes and consume their terminal", "test_batch092_canonical_trace_uses_candidate_probes"),
    _finding("B091-ER-10", "controllergate/amds/dpp14/blind_runtime.py", "run_blind_episode contradiction branch", "96-99", "set-intersection updates cannot add a family outside the prior frontier", "contradiction and backtracking are unreachable", "route conflicting verified facts through truth maintenance and branch ledger", "test_batch092_contradiction_and_backtrack_are_reachable"),
    _finding("B091-ER-11", "scripts/run_batch091_blinded_amds.py", "join baseline construction", "148-154", "the observed macro score is copied into fixed, random, no-memory, and historical rows", "baselines are labels rather than executions", "execute each preregistered baseline under equal budget", "test_batch092_baselines_have_distinct_execution_receipts"),
    _finding("B091-ER-12", "controllergate/amds/dpp14/blind_runtime.py", "critic_join", "121-125", "every non-source truth row is included in safe-abstention accuracy", "positive ownership classes are mis-scored as abstentions", "scope abstention accuracy only to preregistered abstention truth cases", "test_batch092_safe_abstention_denominator"),
    _finding("B091-ER-13", "controllergate/amds/dpp14/blind_runtime.py", "run_blind_episode result", "108-113", "wrong_patch_authorizations and label_leakage_count are literal zero", "safety metrics are asserted instead of reconstructed", "reconstruct authorization from token ledgers and leakage from complete inputs/code/logs", "test_batch092_reconstructs_wrong_authorization_and_leakage"),
    _finding("B091-ER-14", "scripts/run_batch091_stage_proofs.py", "registry/main proof loops", "59-182", "requirements are looped into named producer/verifier rows using a small receipt pool", "generated rows impersonate executed mechanisms", "execute a registered stage producer and independent verifier for each proof", "test_batch092_generic_proof_loop_has_zero_authority"),
    _finding("B091-ER-15", "scripts/run_batch091_stage_proofs.py", "source and license proof production", "115-182", "producer and verifier identities are constructed strings", "identity names do not prove processes executed independently", "bind separate execution receipts and code hashes", "test_batch092_named_producer_and_verifier_executed"),
    _finding("B091-ER-16", "controllergate/proof/authorization_tokens.py", "produce_stage_proof", "40-89", "status PASS follows field validation", "the helper can manufacture semantic authority", "make the proof service persist only externally produced verified receipts", "test_batch092_proof_helper_cannot_manufacture_pass"),
    _finding("B091-ER-17", "scripts/run_batch091_stage_proofs.py", "approval construction", "138-156", "human_authority Brad record is synthesized in repository code", "human authorization origin is not external", "consume an exact prompt-bound, actor/run/candidate/patch/path/nonce/expiry receipt", "test_batch092_prompt_bound_human_authorization"),
    _finding("B091-ER-18", "controllergate/product/historical_lifecycle.py", "historical lifecycle authority", "328-423", "lifecycles consume Batch091 terminal and generated proof chains", "downstream success inherits unsupported authority", "re-run only after corrected canonical AMDS and executed proof chains", "test_batch092_lifecycles_require_corrected_authority"),
    _finding("B091-ER-19", "controllergate/product/historical_lifecycle.py", "non-source lifecycle probes", "214-265", "non-source classification consumes pre-arranged terminal evidence", "non-source terminal depth is not independently reconstructed", "execute project-level reproducers and canonical AMDS without answer keys", "test_batch092_non_source_project_level_execution"),
    _finding("B091-ER-20", "controllergate/deployment/package_canary.py", "run_repaired_distribution_canary", "149-167", "active_state and switched_state are Python dictionaries", "no real active package-slot transition or rollback occurred", "use real isolated slots and atomic active-pointer replacement", "test_batch092_real_slot_switch_and_exact_rollback"),
    _finding("B091-ER-21", "controllergate/product/historical_lifecycle.py", "subprocess helpers", "101-423", "product-reachable lifecycle operations are not uniformly brokered", "external-operation custody is incomplete", "route build/install/replay/canary/rollback through the canonical broker", "test_batch092_all_product_operations_are_brokered"),
    _finding("B091-ER-22", "scripts/run_batch091_semantic_critic.py", "builder evidence construction", "43-57", "critic receives a compact builder-computed summary", "critic does not reconstruct conclusions from raw evidence", "supply raw ledgers, manifests, SQLite export, truth, and criteria", "test_batch092_critic_reconstructs_from_raw_evidence"),
    _finding("B091-ER-23", "controllergate/evaluation/semantic_release_critic.py", "MUTATIONS/run_mutation_campaign", "12-82", "re-signed mutations alter summary fields", "semantic mutation coverage does not exercise raw evidence dependencies", "mutate raw bundles and consistently regenerate every affected manifest", "test_batch092_resigned_raw_semantic_mutations"),
    _finding("B091-ER-24", "ARTIFACT_SHA256SUMS.txt", "outer artifact manifest", "self entry", "manifest lists its own path with the empty-file SHA-256", "the outer manifest cannot truthfully verify itself", "exclude every manifest from its own hash list and reconcile the historical defect", "test_batch092_outer_manifest_has_no_self_entry"),
]


def _git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    observed = _git("rev-parse", "HEAD")
    payload: dict[str, Any] = {
        "status": RESULT,
        "producer": "scripts/audit_batch092_pre_fix_external_review.py",
        "execution_depth": "static_source_and_official_artifact_external_review_at_batch092_start",
        "semantic_scope": "Batch091 external-review authority only",
        "authority_allowed": "expected-red correction plan",
        "authority_forbidden": ["repair", "release", "production_promotion", "count_increment"],
        "starting_head": STARTING_HEAD,
        "observed_head": observed,
        "finding_count": len(FINDINGS),
        "findings": FINDINGS,
        "required_result": RESULT,
    }
    seal_basis = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    payload["expected_red_seal_sha256"] = hashlib.sha256(seal_basis).hexdigest()
    args.output.mkdir(parents=True, exist_ok=True)
    target = args.output / "batch092_pre_fix_external_review_expected_failure.json"
    target.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(RESULT)
    return 0 if observed == STARTING_HEAD and len(FINDINGS) == 24 else 1


if __name__ == "__main__":
    raise SystemExit(main())
