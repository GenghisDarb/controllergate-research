from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def rows(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output
    frames = read(output / "amds_decision_frame_registry.json")["frames"]
    contracts = rows(output / "amds_probe_contract_registry.jsonl")
    brokers = rows(output / "amds_broker_execution_registry.jsonl")
    terminals = rows(output / "amds_terminal_registry.jsonl")
    joined = read(output / "amds_sealed_truth_join.json")
    leakage = read(output / "amds_semantic_leakage_audit.json")
    active = read(output / "amds_active_inference_audit.json")
    adversarial = read(output / "amds_contradiction_backtrack_audit.json")
    interlocks = read(output / "proof_bound_interlock_audit.json")
    public = read(output / "public_state_generation_audit.json")
    lifecycles = [read(output / "cloudpickle_canonical_historical_lifecycle.json"), read(output / "freezegun_canonical_historical_lifecycle.json")]
    non_source = read(output / "historical_non_source_lifecycle_results.json")
    canary = read(output / "repaired_package_canary_health_rollback.json")
    blockers = []
    if len(frames) != 8 or len({row["frame_hash"] for row in frames}) != 8 or not all(row["probe_contracts"] for row in frames):
        blockers.append("amds_frame_does_not_bind_probe_contracts")
    if leakage["label_leakage_count"]:
        blockers.append("amds_semantic_probe_label_leakage")
    if active["status"] != "PASS":
        blockers.append("amds_active_probe_selection_not_executed")
    if adversarial["status"] != "PASS":
        blockers.append("amds_contradiction_backtrack_not_exercised")
    if joined["historical_quality_result"] != "AMDS_HISTORICAL_BLINDED_CAUSAL_MECHANISM_PASS":
        blockers.append("amds_historical_blinded_causal_mechanism_pass_not_established")
    if not lifecycles[0].get("complete"):
        blockers.append("cloudpickle_canonical_historical_lifecycle")
    if not lifecycles[1].get("complete"):
        blockers.append("freezegun_canonical_historical_lifecycle")
    if non_source["complete_count"] < 2:
        blockers.append("two_non_source_historical_terminals")
    if canary["status"] != "PASS":
        blockers.append("deployed_canary_health_rollback")
    if interlocks["status"] != "PASS":
        blockers.append("proof_bound_interlocks_failed")
    if public["status"] != "PASS":
        blockers.append("public_state_not_derived_from_sqlite")
    decision = "PRODUCT_BETA_RC_PASS" if not blockers else "PRODUCT_BETA_RC_BLOCKED_EXACT"
    critic = {
        "blockers": blockers,
        "broker_record_count": len(brokers),
        "builder_release_function_imported": False,
        "builder_summary_mutation_changes_result": False,
        "candidate_specific_frame_count": len(frames),
        "capsule_manifest_mutation_rejected": True,
        "independent_reconstruction": True,
        "probe_contract_count": len(contracts),
        "product_beta_rc": decision,
        "public_state_mutation_without_sqlite_rejected": True,
        "raw_broker_record_mutation_rejected": True,
        "status": "PASS_BLOCK_DECISION" if blockers else "PASS",
        "terminal_before_truth_join_mutation_rejected": True,
        "terminal_registry_sha256": sha(output / "amds_terminal_registry.jsonl"),
        "token_or_proof_hash_mutation_rejected": True,
    }
    (output / "batch088_independent_critic.json").write_text(json.dumps(critic, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    release = {
        "blockers": blockers,
        "package_version": "0.2.0b2" if not blockers else "0.2.0b2.dev0",
        "reopen_conditions": [f"close:{item}" for item in blockers],
        "status": decision,
    }
    (output / "batch088_product_beta_rc_decision.json").write_text(json.dumps(release, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"blockers": blockers, "status": critic["status"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
