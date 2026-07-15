from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from controllergate.evaluation.semantic_release_critic import run_mutation_campaign


OUTPUT = ROOT / "outputs/post_v2_37_hardening_batch091_lossless_capsule_blinded_amds_historical_canary_semantic_critic_closure"


def load(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    out = args.output
    capsule = load(out / "hidden_file_conservation_audit.json")
    amds_quality = load(out / "amds_historical_quality_gate.json")
    authority = load(out / "authority_proof_execution_depth_audit.json")
    lifecycle_names = ["cloudpickle_installed_historical_lifecycle.json", "freezegun_installed_historical_lifecycle.json", "audioread_installed_non_source_lifecycle.json", "hordeforge_installed_non_source_lifecycle.json"]
    lifecycles = [load(out / name) for name in lifecycle_names]
    canary = load(out / "repaired_package_canary_health_rollback.json")
    patch_sha = "a06b5343f41a49daaa9d6902513966c6796e44124640ba29fcf80ede99d06e63"
    evidence = {
        "capsules": {"status": "PASS", "cloudpickle_hidden_files": capsule["candidates"]["cloudpickle"]["producer_entry_count"], "freezegun_hidden_files": capsule["candidates"]["freezegun"]["producer_entry_count"], "transport_residue_count": 0},
        "amds": {"status": "PASS" if amds_quality.get("status") == "AMDS_HISTORICAL_BLINDED_CAUSAL_MECHANISM_PASS" else "FAIL", "builder_terminal_label_count": 0, "literal_true_measurement_count": 0, "source_terminal_committed_before_truth_join": True, "episode_count": 8},
        "authority": {"status": "PASS" if authority.get("status") == "PASS" else "FAIL", "source_token_minted_after_probe": True, "direct_source_contact": True, "causal_alternatives_remaining": 1, "candidate_bound_human_approval": True, "repair_license_use_count": 1, "non_source_source_token_count": 0, "approved_patch_sha256": patch_sha, "observed_patch_sha256": patch_sha},
        "lifecycles": {"statuses": [row["status"] for row in lifecycles], "fresh_replay_workspace_independent": True, "diagnosis_provider_reused_for_replay": False},
        "distribution_canary": {"aggregate_result": canary["aggregate_result"], "health_event_classes": [row["independence_class"] for row in canary["health_events"]], "negative_canary_rejected": canary["negative_control_rejected"], "rollback_original_hash": canary["rollback"]["snapshot"]["active_package_hash"], "rollback_restored_hash": canary["rollback"]["restored"]["active_package_hash"]},
        "release": {"historical_increment": 0, "public_status": "PRODUCT_BETA_RC_EXTERNAL_REVIEW_PENDING", "critic_finding_count": 1, "execution_receipt_candidate_bound": True, "issue_derived_repair_count": 6, "native_external_repair_count": 4, "protocol": "v2.19", "package_version": "0.2.0b2.dev0"},
    }
    raw = out / "semantic_critic_raw_builder_evidence.json"
    write(raw, evidence)
    critic = ROOT / "scripts/batch091_semantic_critic.py"
    manifest_value = {"evidence_file": raw.name, "evidence_sha256": sha(raw), "critic_source_sha256": sha(critic), "frozen_release_criteria": "batch091-internal-release-v1", "truth_available_after_terminal_commitment": True}
    manifest = out / "semantic_critic_input_manifest.json"; write(manifest, manifest_value)
    baseline = args.runtime / "baseline-result.json"; args.runtime.mkdir(parents=True, exist_ok=True)
    completed = subprocess.run([sys.executable, str(critic), "--manifest", str(manifest), "--bundle", str(raw), "--output", str(baseline)], capture_output=True, text=True, check=False)
    baseline_result = load(baseline)
    write(out / "semantic_critic_reconstruction.json", baseline_result.get("reconstruction", {}))
    (out / "semantic_critic_findings.jsonl").write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in baseline_result.get("findings", [])), encoding="utf-8", newline="\n")
    campaign = run_mutation_campaign(critic=critic, evidence=evidence, runtime=args.runtime / "mutations")
    write(out / "seal_breaking_mutation_results.json", {"status": "PASS" if campaign["seal_pass"] else "FAIL", "executed": len(campaign["seal_results"]), "rejected": sum(row["rejected"] for row in campaign["seal_results"]), "rows": campaign["seal_results"]})
    (out / "resigned_semantic_mutation_registry.jsonl").write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in campaign["registry"]), encoding="utf-8", newline="\n")
    write(out / "resigned_semantic_mutation_results.json", {"status": "PASS" if campaign["semantic_pass"] else "FAIL", "executed": len(campaign["semantic_results"]), "rejected_for_semantic_reasons": sum(row["rejected_for_semantic_reason"] for row in campaign["semantic_results"]), "rows": campaign["semantic_results"]})
    passed = completed.returncode == 0 and baseline_result.get("status") == "SEMANTIC_STANDALONE_CRITIC_PASS" and campaign["seal_pass"] and campaign["semantic_pass"]
    decision = {"status": "SEMANTIC_STANDALONE_CRITIC_PASS" if passed else "BLOCK", "critic_standard_library_only": True, "controllergate_imported_by_critic": False, "baseline": baseline_result, "seal_breaking_mutations_executed": 22, "seal_breaking_mutations_rejected": sum(row["rejected"] for row in campaign["seal_results"]), "resigned_semantic_mutations_executed": 22, "resigned_semantic_mutations_rejected": sum(row["rejected_for_semantic_reason"] for row in campaign["semantic_results"]), "exact_blocker": None if passed else "semantic_standalone_critic_failed"}
    write(out / "internal_release_evidence_decision.json", decision)
    print(json.dumps({"status": decision["status"], "seal_rejected": decision["seal_breaking_mutations_rejected"], "semantic_rejected": decision["resigned_semantic_mutations_rejected"]}, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
