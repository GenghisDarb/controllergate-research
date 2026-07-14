from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


REQUIRED = [
    "batch083_raw_evidence_preservation.json", "batch083_amds_depth_reconciliation.json", "batch083_canary_depth_reconciliation.json",
    "batch083_product_alpha_depth_reconciliation.json", "batch083_maturity_model_reconciliation.json",
    "batch084_batch083_artifact_ingest_preservation.json", "batch084_batch083_provider_artifact_verification.jsonl",
    "batch084_batch083_provider_artifact_verification_summary.json", "batch084_cumulative_maturity_before.json",
    "batch084_cumulative_maturity_after.json", "batch084_current_batch_evidence_delta.json", "batch084_production_readiness_maturity.json",
    "batch084_cumulative_maturity_recalibration.json", "batch084_historical_amds_v2.json", "batch084_amds_probe_execution_registry.jsonl",
    "batch084_amds_arm_seals.jsonl", "batch084_amds_metrics.json", "batch084_routing_memory_retrieval_registry.jsonl",
    "batch084_routing_memory_summary.json", "batch084_null_wrapper_contract.json", "batch084_null_wrapper_execution_registry.jsonl",
    "batch084_control_taxonomy.json", "batch084_null_baseline_nonconflation.json", "batch084_randomization_null_registry.jsonl",
    "batch084_null_separation_shadow.json", "batch084_cross_family_homology_ledger.json", "batch084_cross_family_retrieval_registry.jsonl",
    "batch084_cloudpickle_real_canary.json", "batch084_freezegun_real_canary.json", "batch084_real_canary_identity_audit.json",
    "batch084_real_canary_comparison.json", "batch084_historical_product_beta_replay.json", "batch084_controlled_write_connector_sandbox.json",
    "batch084_openbb_network_none_contract.json", "batch084_openbb_network_canaries.json", "batch084_openbb_container_execution.json",
    "batch084_poetry_differential_preregistration.json", "batch084_poetry_loo_matrix.jsonl", "batch084_poetry_stage_one_seal.json",
    "batch084_poetry_loto_matrix.jsonl", "batch084_poetry_differential_result.json", "batch084_provider_precondition_registry.jsonl",
    "batch084_provider_precondition_audit.json", "batch084_failed_attempt_branch_registry.jsonl", "batch084_branch_lineage_audit.json",
    "batch084_normal_incident_pathways.jsonl", "batch084_output_divergence_registry.jsonl", "batch084_divergence_locality_audit.json",
    "batch084_prospective_cohort_freeze.json", "batch084_prospective_diagnostic_arms.json", "batch084_conditional_repair_results.json",
    "batch084_duplicate_replay_rollback_proof_count_canary.json", "batch084_independent_critic.json", "batch084_final_claim_boundary.json",
    "batch084_final_state.json", "campaign_summary.md", "SHA256SUMS.txt",
]


def read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--out", required=True); args = parser.parse_args(); out = Path(args.out)
    errors = [f"missing:{name}" for name in REQUIRED if not (out / name).is_file()]
    contract = read(ROOT / "configs/batch084_prompt_contract.json")
    if contract.get("prompt_id") != "CG-BATCH084-REAL-AMDS-CANARY-PRODUCT-BETA-2026-07-14-V1" or contract.get("prompt_sentinel") != "BEGIN_BATCH084_REAL_OPERATIONAL_DEPTH": errors.append("prompt_identity")
    if errors:
        print(json.dumps({"status": "FAIL", "errors": errors}, sort_keys=True)); return 1
    if read(out / "batch083_raw_evidence_preservation.json").get("status") != "PASS": errors.append("batch083_raw_evidence_changed")
    amds_correction = read(out / "batch083_amds_depth_reconciliation.json")
    if amds_correction.get("REAL_MULTI_PROBE_AMDS_REPLAY") != "NOT_ESTABLISHED" or amds_correction.get("BATCH083_AMDS_MATURITY") != "LEVEL_2_CONTROLLED_FIXTURE_VALIDATED": errors.append("batch083_amds_overclaim_not_corrected")
    canary_correction = read(out / "batch083_canary_depth_reconciliation.json")
    if canary_correction.get("HISTORICAL_REPAIRED_SOFTWARE_CANARY") != "NOT_ESTABLISHED": errors.append("batch083_canary_overclaim_not_corrected")
    artifact_summary = read(out / "batch084_batch083_provider_artifact_verification_summary.json")
    if artifact_summary.get("status") != "PASS" or artifact_summary.get("artifact_count") != 3: errors.append("provider_artifact_identity")
    historical = read(out / "batch084_historical_amds_v2.json"); episodes = historical.get("episodes", [])
    if len(episodes) < 8 or len({row["repository_family"] for row in episodes}) < 6 or len({row["terminal_truth"] for row in episodes}) < 4: errors.append("historical_frame_depth")
    probes = jsonl(out / "batch084_amds_probe_execution_registry.jsonl")
    grouped: dict[tuple[str, str], list[dict]] = {}
    for row in probes: grouped.setdefault((row["episode_id"], row["strategy"]), []).append(row)
    for key, rows in grouped.items():
        if len(rows) < 6 or len({row["source_path"] for row in rows}) < 6: errors.append(f"distinct_probe_evidence:{key}")
        if any(row.get("selection_method") not in {"deterministic_constraint_elimination", "calibrated_information_gain"} for row in rows): errors.append(f"probe_selection_method:{key}")
        if any(row.get("likelihood_status") == "LIKELIHOOD_NOT_CALIBRATED" and any(row.get(field) is not None for field in ("predicted_information_gain", "entropy_before", "entropy_after")) for row in rows): errors.append(f"fabricated_entropy:{key}")
    if any(row.get("truth_visible") for row in probes): errors.append("truth_visible_before_arm_seal")
    seals = jsonl(out / "batch084_amds_arm_seals.jsonl")
    if any(row.get("truth_visible") for row in seals): errors.append("arm_not_blinded")
    taxonomy = read(out / "batch084_control_taxonomy.json")["conditions"]
    expected_controls = {"REAL_MEMORY_AMDS", "NO_MEMORY_AMDS", "SHUFFLED_MEMORY_AMDS", "STATELESS_NULL_WRAPPER", "RANDOMIZATION_NULL", "FIXED_ORDER_BASELINE"}
    if set(taxonomy) != expected_controls: errors.append("control_taxonomy_conflated")
    nonconflation = read(out / "batch084_null_baseline_nonconflation.json")
    if nonconflation.get("stateless_null_is_white_noise") is not False or nonconflation.get("stateless_pooled_with_randomization_null") is not False: errors.append("null_baseline_conflation")
    nulls = jsonl(out / "batch084_randomization_null_registry.jsonl")
    if any(count < 19 for count in Counter(row["episode_id"] for row in nulls).values()): errors.append("randomization_null_power")
    shadow = read(out / "batch084_null_separation_shadow.json")
    if shadow.get("production_threshold") != "NOT_ESTABLISHED_FOR_CONTROLLERGATE_PRODUCTION": errors.append("nss_overclaim")
    homology = read(out / "batch084_cross_family_homology_ledger.json")
    forbidden = {"candidate_id", "terminal_class", "patch_text", "source_snippet", "repair_result", "count_result", "future_revision", "gold_fix"}
    if any(forbidden & set(row.get("features", {})) for row in homology.get("records", [])): errors.append("homology_leakage")
    identities = read(out / "batch084_real_canary_identity_audit.json").get("records", [])
    expected_patches = {"cloudpickle_507_py313_typevar_distutils": "a06b5343f41a49daaa9d6902513966c6796e44124640ba29fcf80ede99d06e63", "freezegun_547_py313_datetimes_assertion": "8daf31c4d59ead1832aa3bdc6260bae3c92a1052f140c9f0442a550c4ebf3247"}
    if any(row.get("observed_patch_sha256") != expected_patches.get(row.get("candidate_id")) for row in identities) or len(identities) != 2: errors.append("historical_canary_patch_identity")
    for name in ("cloudpickle", "freezegun"):
        canary = read(out / f"batch084_{name}_real_canary.json")
        if canary.get("status") == "HISTORICAL_REPAIRED_SOFTWARE_CANARY_PASS" and any(value != "PASS" for value in canary.get("execution_steps", {}).values()): errors.append(f"false_real_canary_pass:{name}")
        if canary.get("repair_count_changed") is not False: errors.append(f"historical_count_inflation:{name}")
    product = read(out / "batch084_historical_product_beta_replay.json")
    if not product.get("canonical_cli_used") or product.get("historical_count_increment") != 0: errors.append("product_beta_boundary")
    connector = read(out / "batch084_controlled_write_connector_sandbox.json")
    if connector.get("status") != "CONTROLLED_WRITE_CONNECTOR_FIXTURE_PASS" or connector.get("public_remote_mutation") is not False or connector.get("live_write_connector_active") is not False: errors.append("controlled_write_connector")
    openbb_contract = read(out / "batch084_openbb_network_none_contract.json"); openbb = read(out / "batch084_openbb_container_execution.json")
    if openbb_contract.get("preferred_strategy") != "docker_network_none_same_container" or openbb_contract.get("server_and_client_same_container") is not True: errors.append("openbb_contract")
    if openbb.get("status") == "CANDIDATE_FAILURE_REPRODUCED" and (not openbb.get("duplicate_failure_reproduced") or any(not row.get("contract_pass") for row in openbb.get("replays", []))): errors.append("openbb_false_reproduction")
    loo = jsonl(out / "batch084_poetry_loo_matrix.jsonl"); loto = jsonl(out / "batch084_poetry_loto_matrix.jsonl")
    if len(loo) != 26 or any(row.get("changed_factor_count") != 1 for row in loo): errors.append("poetry_loo_contract")
    if any(row.get("changed_factor_count") != 2 or not row.get("stage_one_seal_verified_before_execution") for row in loto): errors.append("poetry_loto_contract")
    provider_rows = jsonl(out / "batch084_provider_precondition_registry.jsonl")
    if any(row.get("requirement_class") == "required" and row.get("lock_status") in {"DECLARED_UNPINNED", "DECLARED_PINNED_MISSING"} and row.get("failure_classification") != "declared_secondary_cofactor_unpinned_lock_required" for row in provider_rows): errors.append("provider_precondition_unblocked")
    divergence = jsonl(out / "batch084_output_divergence_registry.jsonl")
    if any(row.get("patch_authorized") and row.get("terminal_divergence_class") not in {"SOURCE_OWNED_OUTPUT_DIVERGENCE", "MIXED_DIVERGENCE"} for row in divergence): errors.append("non_source_patch_authorization")
    repair = read(out / "batch084_conditional_repair_results.json")
    if repair.get("repair_attempt_count", 0) > 2: errors.append("repair_attempt_limit")
    final = read(out / "batch084_final_claim_boundary.json")
    if final.get("current_protocol") != "v2.19" or final.get("full_scoring") != "NOT_RUN/disallowed" or final.get("prospective_memory_lift") != "not demonstrated" or final.get("self_maintaining_software") != "false/not demonstrated" or final.get("live_write_connectors") != "inactive": errors.append("claim_boundary")
    sums = {line.split(maxsplit=1)[1].lstrip(" *"): line.split(maxsplit=1)[0] for line in (out / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines() if line.strip()}
    if any(name not in sums for name in REQUIRED if name != "SHA256SUMS.txt"): errors.append("manifest_coverage")
    for rel, digest in sums.items():
        path = out / rel
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != digest: errors.append(f"manifest:{rel}")
    result = {"status": "PASS" if not errors else "FAIL", "errors": errors, "required_file_count": len(REQUIRED), "historical_episode_count": len(episodes), "probe_execution_count": len(probes)}
    print(json.dumps(result, sort_keys=True)); return 0 if not errors else 1


if __name__ == "__main__": raise SystemExit(main())
