from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from controllergate.core.batch076_amds_causal_memory_calibration import (
    BATCH,
    EXPECTED_SHA,
    EXPECTED_SIZE,
    OFFICIAL_PROVIDER_HASHES,
)
from controllergate.amds.observation_contract_v2 import validate_observation

OUT = ROOT / "outputs" / BATCH


def load(name: str) -> dict:
    return json.loads((OUT / name).read_text(encoding="utf-8"))


def expect(errors: list[str], condition: bool, label: str) -> None:
    if not condition:
        errors.append(label)


def manifest_valid() -> tuple[bool, int]:
    manifest = OUT / "SHA256SUMS.txt"
    if not manifest.is_file():
        return False, 0
    checked = 0
    for line in manifest.read_text(encoding="utf-8").splitlines():
        digest, relative = line.split(maxsplit=1)
        target = OUT / relative.strip().lstrip("*")
        if not target.is_file() or hashlib.sha256(target.read_bytes()).hexdigest() != digest:
            return False, checked
        checked += 1
    return checked > 0, checked


def jsonl(name: str) -> list[dict]:
    return [json.loads(line) for line in (OUT / name).read_text(encoding="utf-8").splitlines() if line]


def main() -> int:
    errors: list[str] = []
    required = {
        "batch075_artifact_ingest.json", "batch075_state_preservation.json",
        "batch075_claim_boundary_preservation.json", "batch075_arm_evidence_preservation.json",
        "batch075_provider_hash_reconciliation.json", "batch075_failure_contract_reconciliation.json",
        "batch075_corrected_admission_depth.json", "batch075_amds_evidence_depth_reconciliation.json",
        "hordeforge_timeout_diagnostic_registry.jsonl", "hordeforge_thread_and_process_stack_evidence.json",
        "hordeforge_direct_invocation_comparison.json", "hordeforge_corrected_admission_decision.json",
        "amds_probe_registry_fidelity_batch076.json", "amds_repeated_probe_prevention_audit.json",
        "batch076_probe_authorization_audit.json", "batch076_probe_event_chain_audit.json",
        "routing_memory_corpus_v1.jsonl", "routing_memory_corpus_manifest.json",
        "routing_memory_proof_binding_audit.json", "routing_memory_feature_schema_v1.json",
        "batch076_real_memory_snapshot.json", "batch076_shuffled_memory_snapshot.json",
        "batch076_candidate_memory_matches.jsonl", "batch076_memory_influence_trace.jsonl",
        "batch076_causal_probe_catalog.json", "batch076_arm_execution_summary.json",
        "batch076_blinded_ground_truth_v2.json", "batch076_causal_memory_metrics.json",
        "batch076_authoritative_repair_decision.json", "batch076_completion_decisions.json",
        "batch076_final_decision.json", "batch076_summary.md", "SHA256SUMS.txt",
    }
    missing = sorted(name for name in required if not (OUT / name).is_file())
    if missing:
        errors.append("missing:" + ",".join(missing))
    valid_manifest, manifest_count = manifest_valid()
    expect(errors, valid_manifest and manifest_count >= 30, "manifest")

    ingest = load("batch075_artifact_ingest.json")
    expect(errors, ingest.get("status") == "PASS", "batch075_ingest")
    expect(errors, ingest.get("observed_size_bytes") == EXPECTED_SIZE, "artifact_size")
    expect(errors, ingest.get("observed_sha256") == EXPECTED_SHA, "artifact_sha")
    expect(errors, ingest.get("file_count") == 177, "artifact_file_count")
    expect(errors, ingest.get("outer_manifest", {}).get("checked") == 176, "outer_manifest")
    expect(errors, [ingest.get("internal_manifests", {}).get(name, {}).get("checked") for name in (
        "post_v2_37_hardening_batch073_count5_revalidation_frozen_wave1",
        "post_v2_37_hardening_batch074_sterile_high_yield_amds_memory_wave1",
        "post_v2_37_hardening_batch075_provider_harness_amds_memory_wave1a",
    )] == [41, 16, 106], "internal_manifests")
    entry = ingest.get("entry_audit", {})
    expect(errors, all(entry.get(key) == 0 for key in (
        "unsafe_path_count", "duplicate_path_count", "pycache_payload_count",
        "pyc_payload_count", "nested_archive_or_cache_payload_count",
    )), "path_custody")

    state = load("batch075_state_preservation.json")
    claims = load("batch075_claim_boundary_preservation.json")
    expect(errors, state.get("status") == "PASS", "batch075_state")
    expect(errors, claims.get("issue_derived_repair_count") == 5, "issue_count_preserved")
    expect(errors, claims.get("native_external_repair_count") == 4, "native_count_preserved")
    expect(errors, claims.get("memory_lift") == "not_demonstrated", "memory_claim")

    hashes = load("batch075_provider_hash_reconciliation.json")
    records = {row["candidate_id"]: row for row in hashes.get("records", [])}
    for candidate, official in OFFICIAL_PROVIDER_HASHES.items():
        row = records.get(candidate, {})
        expect(errors, row.get("official_provider_lock_hash") == official, f"official_hash:{candidate}")
        expect(errors, row.get("local_promoted") is False, f"local_not_promoted:{candidate}")
    expect(errors, hashes.get("scientific_authority") == "official_workflow", "provider_authority")

    historical = load("batch075_amds_evidence_depth_reconciliation.json")
    expect(errors, historical.get("preserved_raw_probe_records") == 24, "historical_raw")
    expect(errors, historical.get("accepted_observations_under_v2") == 14, "historical_accepted")
    expect(errors, historical.get("rejected_null_observations") == 10, "historical_null_rejected")
    expect(errors, historical.get("informative_posterior_updates_under_v3") == 0, "historical_informative")
    expect(errors, historical.get("empty_reported_posterior_maps") == 24, "historical_empty_posteriors")

    horde = load("hordeforge_corrected_admission_decision.json")
    expect(errors, horde.get("corrected_admission") == "QUARANTINED_RESOURCE_TIMEOUT", "horde_quarantine")
    expect(errors, horde.get("candidate_failure_reproduced") is False, "horde_not_candidate_failure")
    expect(errors, horde.get("repair_authority") is False, "horde_no_repair")
    timeout_rows = jsonl("hordeforge_timeout_diagnostic_registry.jsonl")
    expect(errors, bool(timeout_rows), "timeout_registry")
    stack = load("hordeforge_thread_and_process_stack_evidence.json")
    expect(errors, stack.get("all_network_none") is True, "timeout_network_none")

    arms = load("batch076_arm_execution_summary.json")
    arm_rows = arms.get("records", [])
    observations = [obs for arm in arm_rows for obs in arm.get("observations", [])]
    expect(errors, arms.get("arm_count") == 6 and arms.get("candidate_count") == 1, "arm_design")
    expect(errors, len(observations) == 48, "accepted_observation_count")
    expect(errors, all(validate_observation(obs)["status"] == "PASS" for obs in observations), "observation_contract")
    expect(errors, all(len(arm.get("posterior_updates", [])) == len(arm.get("observations", [])) for arm in arm_rows), "posterior_coverage")
    expect(errors, all(bool(arm.get("posterior")) for arm in arm_rows), "nonempty_posteriors")
    expect(errors, all(len(set(arm.get("executed_probe_sequence", []))) == len(arm.get("executed_probe_sequence", [])) for arm in arm_rows), "no_probe_repeats")
    expect(errors, all(arm.get("patch_authority") is False for arm in arm_rows), "arms_no_patch")

    auth = load("batch076_probe_authorization_audit.json")
    events = load("batch076_probe_event_chain_audit.json")
    expect(errors, auth.get("status") == "PASS" and auth.get("accepted_probe_count") == auth.get("spent_nonce_count") == 48, "authorization_nonce_bijection")
    expect(errors, auth.get("reused_nonces") == 0, "nonce_reuse")
    expect(errors, events.get("status") == "PASS" and events.get("accepted_probe_count") == events.get("probe_event_count") == 48, "event_bijection")

    memory = jsonl("routing_memory_corpus_v1.jsonl")
    memory_manifest = load("routing_memory_corpus_manifest.json")
    expect(errors, len(memory) == memory_manifest.get("record_count") == 9, "memory_count")
    expect(errors, memory_manifest.get("issue_derived_records") == 5 and memory_manifest.get("native_records") == 4, "memory_classes")
    expect(errors, memory_manifest.get("forbidden_fields_present") is False, "memory_firewall")
    expect(errors, load("routing_memory_proof_binding_audit.json").get("status") == "PASS", "memory_proof_binding")
    expect(errors, all(row.get("proof_evidence_path") and row.get("proof_evidence_sha256") for row in memory), "memory_proof_fields")

    ground = load("batch076_blinded_ground_truth_v2.json")
    expect(errors, ground.get("arms_sealed_before_adjudication") is True, "ground_truth_blind")
    expect(errors, ground.get("strategy_labels_available") is False and ground.get("memory_labels_available") is False, "ground_truth_labels")
    metrics = load("batch076_causal_memory_metrics.json")
    expect(errors, metrics.get("AMDS_PROSPECTIVE_EFFECTIVENESS") == "NOT_ESTABLISHED", "amds_effectiveness")
    expect(errors, metrics.get("memory_lift") == "not_demonstrated", "memory_lift")
    expect(errors, metrics.get("wrong_patch_authorization_rate") == 0.0, "wrong_patch_rate")

    repair = load("batch076_authoritative_repair_decision.json")
    final = load("batch076_final_decision.json")
    expect(errors, repair.get("status") == "NOT_RUN_NO_SAFE_GENERIC_PATCH_PLAN" and repair.get("attempts") == 0, "repair_not_run")
    expect(errors, final.get("status") == "PASS", "final")
    expect(errors, final.get("validated_protocol") == "v2.19", "protocol")
    expect(errors, final.get("issue_derived_repair_count") == 5 and final.get("native_external_repair_count") == 4, "counts")
    expect(errors, final.get("full_scoring") == "NOT_RUN/disallowed", "full_scoring")
    expect(errors, final.get("self_maintaining_software") == "false/not_demonstrated", "self_maintaining")
    expect(errors, final.get("live_connectors") == "inactive", "live_connectors")

    if errors:
        print("Batch076 AMDS causal memory calibration audit: FAIL")
        print("errors:", ", ".join(errors))
        return 1
    print(f"Batch076 AMDS causal memory calibration audit: PASS ({manifest_count} manifest entries)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
