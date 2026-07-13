from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from controllergate.core.evidence import sha256_file
from controllergate.execution.execution_claim_verifier import verify_execution_claims
from controllergate.governance.builder_critic_gate import builder_critic_agreement
from controllergate.runtime.runtime_root_policy import LOCAL_ROOT, validate_runtime_root


BATCH = "post_v2_37_hardening_batch081_execution_constitution_provider_incident_pilot"
B80 = "post_v2_37_hardening_batch080_executed_preflight_provider_memory_wave1d"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def manifest_ok(directory: Path) -> bool:
    manifest = directory / "SHA256SUMS.txt"
    if not manifest.is_file(): return False
    for line in manifest.read_text(encoding="utf-8").splitlines():
        expected, rel = line.split(maxsplit=1)
        target = directory / rel.strip().lstrip("*")
        if not target.is_file() or sha256_file(target) != expected: return False
    return True


def main() -> int:
    root = Path.cwd(); out = root / "outputs" / BATCH; b80 = root / "outputs" / B80
    required = [
        "batch080_artifact_ingest.json", "batch080_state_preservation.json", "batch080_claim_boundary_preservation.json",
        "batch080_count6_preservation.json", "batch080_public_surface_preservation.json", "batch080_pluggy_contamination_reconciliation.json",
        "batch080_corrected_execution_frame.json", "batch080_collection_depth_reconciliation.json", "batch080_target_identity_reconciliation.json",
        "batch080_hordeforge_provider_regression.json", "batch080_provider_depth_reconciliation.json", "batch081_engineering_constitution_proof.json",
        "batch081_execution_authenticity_contract.json", "batch081_execution_authenticity_audit.json", "batch081_runtime_root_attestation.json",
        "batch081_contamination_v2_regression.json", "batch081_collection_contract_v2_regression.json", "batch081_target_resolver_v3_regression.json",
        "batch081_provider_builder_v3_status.json", "batch081_hordeforge_provider_closure.json", "batch081_incident_preflight.json",
        "batch081_execution_frame.json", "batch081_final_decisions.json", "batch081_builder_critic_agreement.json", "campaign_summary.md", "SHA256SUMS.txt",
    ]
    failures = [f"missing:{name}" for name in required if not (out / name).is_file()]
    if failures:
        print("Batch081 audit: FAIL", failures); return 1
    ingest = load(out / "batch080_artifact_ingest.json")
    if ingest.get("status") != "PASS" or ingest.get("artifact_manifest", {}).get("checked") != 435: failures.append("batch080_outer_manifest")
    expected_counts = [41, 16, 106, 32, 47, 61, 58, 45]
    observed_counts = [record.get("checked") for record in ingest.get("output_manifests", {}).values()]
    if observed_counts != expected_counts: failures.append(f"batch080_internal_counts:{observed_counts}")
    if not manifest_ok(b80): failures.append("batch080_raw_manifest_drift")
    if not manifest_ok(out): failures.append("batch081_manifest")
    if load(out / "batch080_corrected_execution_frame.json").get("clean_eligible_batch080_frame_count") != 0: failures.append("corrected_frame_not_zero")
    pluggy = load(out / "batch080_pluggy_contamination_reconciliation.json")
    if pluggy.get("classification") != "HARD_REJECT_SOLUTION_CONTAMINATION": failures.append("pluggy_not_hard_rejected")
    collection = load(out / "batch080_collection_depth_reconciliation.json")
    if collection.get("corrected_node_collection_pass") is not False or collection.get("correction", {}).get("return_code") != 3: failures.append("collection_false_pass_not_corrected")
    target = load(out / "batch080_target_identity_reconciliation.json")
    if target.get("target_mapping") != "SYMBOL_NAME_COLLISION" or target.get("correct_lane") != "ISSUE_DERIVED_REPRODUCER_LANE": failures.append("target_collision_not_corrected")
    provider = load(out / "batch080_provider_depth_reconciliation.json")
    if provider.get("recovered_with_zero_verified_artifacts") is not False: failures.append("provider_false_recovery")
    constitution = load(root / "configs/controllergate_engineering_constitution_v1.json")
    if constitution.get("law_count") != 40: failures.append("constitution_law_count")
    rows = [json.loads(line) for line in (out / "batch081_execution_ledger.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    authenticity = verify_execution_claims(rows, claimed_executed_stages=1)
    if authenticity["status"] != "PASS": failures.append("execution_authenticity")
    if validate_runtime_root(LOCAL_ROOT, repo_root=root)["status"] != "PASS": failures.append("c_runtime_root")
    if validate_runtime_root(r"E:\ControllerGate_Runtime", repo_root=root)["status"] != "BLOCK": failures.append("e_runtime_not_rejected")
    incident = load(out / "batch081_incident_preflight.json")
    if incident.get("clean_eligible_candidate_count") != 0 or incident.get("adaptive_replenishment") is not False: failures.append("incident_frame")
    decisions = load(out / "batch081_final_decisions.json")
    locked = {"ISSUE_DERIVED_REPAIR_COUNT": 6, "AMDS_PROSPECTIVE_EFFECTIVENESS": "NOT_ESTABLISHED", "ROUTING_MEMORY_PROSPECTIVE_LIFT": "not demonstrated", "SELF_MAINTAINING_SOFTWARE": "false/not demonstrated", "LIVE_CONNECTORS": "inactive"}
    if any(decisions.get(key) != value for key, value in locked.items()): failures.append("claim_boundary")
    agreement = load(out / "batch081_builder_critic_agreement.json")
    if builder_critic_agreement(agreement["builder"], agreement["critic"])["status"] != "PASS": failures.append("builder_critic")
    status = "PASS" if not failures else "FAIL"
    print("Batch081 audit:", status, failures)
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
