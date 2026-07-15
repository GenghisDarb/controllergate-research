from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/post_v2_37_hardening_batch091_lossless_capsule_blinded_amds_historical_canary_semantic_critic_closure"


def load(name: str) -> dict:
    return json.loads((OUT / name).read_text(encoding="utf-8"))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    required = {
        "batch090_artifact_ingest.json", "batch090_claim_reconciliation.json", "hidden_file_conservation_audit.json",
        "amds_historical_quality_gate.json", "authority_proof_execution_depth_audit.json",
        "cloudpickle_installed_historical_lifecycle.json", "freezegun_installed_historical_lifecycle.json",
        "audioread_installed_non_source_lifecycle.json", "hordeforge_installed_non_source_lifecycle.json",
        "repaired_distribution_build.json", "repaired_package_canary_health_rollback.json",
        "semantic_critic_input_manifest.json", "internal_release_evidence_decision.json",
        "seal_breaking_mutation_results.json", "resigned_semantic_mutation_results.json",
        "batch091_internal_release_decision.json", "batch091_consolidated_state.json", "batch091_claim_boundary.json",
        "public_state_generation_audit.json", "public_state_sync_audit.json", "SHA256SUMS.txt",
    }
    failures = [f"missing:{name}" for name in sorted(required) if not (OUT / name).is_file()]
    if failures:
        print(json.dumps({"status": "FAIL", "failures": failures}, sort_keys=True)); return 1
    manifest_rows = [line.split("  ", 1) for line in (OUT / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines() if line]
    for expected, name in manifest_rows:
        path = OUT / name
        if not path.is_file() or sha(path) != expected:
            failures.append(f"manifest:{name}")
    hidden = load("hidden_file_conservation_audit.json")
    if hidden["candidates"]["cloudpickle"].get("producer_entry_count") != 58 or hidden["candidates"]["cloudpickle"].get("consumer_entry_count") != 58:
        failures.append("cloudpickle_hidden_file_conservation")
    if hidden["candidates"]["freezegun"].get("producer_entry_count") != 39 or hidden["candidates"]["freezegun"].get("consumer_entry_count") != 39:
        failures.append("freezegun_hidden_file_conservation")
    amds = load("amds_historical_quality_gate.json")
    if amds.get("status") != "AMDS_HISTORICAL_BLINDED_CAUSAL_MECHANISM_PASS" or amds.get("eligible_episode_count") != 8:
        failures.append("amds_historical_blinded_causal_mechanism")
    for name in ("cloudpickle_installed_historical_lifecycle.json", "freezegun_installed_historical_lifecycle.json", "audioread_installed_non_source_lifecycle.json", "hordeforge_installed_non_source_lifecycle.json"):
        if load(name).get("status") != "PASS": failures.append(name)
    if load("repaired_package_canary_health_rollback.json").get("aggregate_result") != "DEPLOYED_CANARY_HEALTH_ROLLBACK_PASS":
        failures.append("deployed_canary_health_rollback")
    critic = load("internal_release_evidence_decision.json")
    if critic.get("status") != "SEMANTIC_STANDALONE_CRITIC_PASS" or critic.get("seal_breaking_mutations_rejected") != 22 or critic.get("resigned_semantic_mutations_rejected") != 22:
        failures.append("semantic_standalone_critic")
    state = load("batch091_consolidated_state.json")
    expected = {"status": "PRODUCT_BETA_RC_EXTERNAL_REVIEW_PENDING", "exact_blocker": "external_independent_release_review_pending", "protocol": "v2.19", "package_version": "0.2.0b2.dev0", "issue_derived_repair_count": 6, "native_external_repair_count": 4, "historical_increment": 0, "full_scoring": "NOT_RUN/disallowed", "production_readiness": False}
    for key, value in expected.items():
        if state.get(key) != value: failures.append(f"claim:{key}")
    if state.get("public_writes") != "inactive" or state.get("automatic_merge") != "inactive" or state.get("self_maintaining_software") != "false/not_demonstrated":
        failures.append("claim_boundary")
    forbidden_suffixes = {".zip", ".tar", ".gz", ".pyc", ".pyo"}
    if any(path.suffix.casefold() in forbidden_suffixes or "__pycache__" in path.parts for path in OUT.rglob("*")):
        failures.append("nonportable_output_payload")
    print(json.dumps({"status": "PASS" if not failures else "FAIL", "audit": "Batch091", "failures": failures, "manifest_entries": len(manifest_rows)}, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
