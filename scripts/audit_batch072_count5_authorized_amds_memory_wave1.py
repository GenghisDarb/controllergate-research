from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from controllergate.core.batch072_count5_amds_wave1 import BATCH, EXPECTED_SHA256, PATCH_SHA256

OUT = ROOT / "outputs" / BATCH


def load(name: str) -> dict:
    return json.loads((OUT / name).read_text(encoding="utf-8"))


def audit_manifest() -> bool:
    for line in (OUT / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
        digest, relative = line.split(maxsplit=1)
        path = OUT / relative.strip().lstrip("*")
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            return False
    return True


def main() -> int:
    errors: list[str] = []
    required = {
        "batch071_artifact_ingest.json", "batch071_state_preservation.json",
        "batch071_claim_boundary_preservation.json", "batch071_patch_identity_preservation.json",
        "connexion_count5_provider_arm_registry.json", "connexion_count5_pre_repair_challenge.json",
        "connexion_count5_patch_challenge.json", "connexion_count5_metamorphic_invariants.json",
        "connexion_count5_duplicate_replay.json", "connexion_count5_hardening_decision.json",
        "v2_19_authorization_completion_batch072.json", "v2_19_deterministic_provider_completion_batch072.json",
        "v2_19_lifecycle_implementation_batch072.json", "candidate_specific_logic_audit_batch072.json",
        "generic_patch_planner_boundary_batch072.json", "ownership_classifier_generalization_audit_batch072.json",
        "amds_fourteen_contact_resolution_batch072.json", "amds_planner_freeze_batch072.json",
        "routing_memory_snapshot_batch072.json", "batch072_seed_intake_policy.json",
        "batch072_weak_lead_registry.jsonl", "batch072_contamination_decisions.jsonl",
        "batch072_commit_resolution_registry.jsonl", "batch072_fresh_candidate_cohort.json",
        "batch072_cohort_freeze_hash.json", "batch072_wave1_preregistration.json",
        "batch072_diagnostic_arm_execution.json", "batch072_arm_sealing_and_ground_truth.json",
        "batch072_wave1_metrics.json", "batch072_authoritative_repair_decisions.json",
        "batch072_completion_decisions.json", "batch073_cold_start_handoff.json",
        "batch073_exact_next_actions.json", "batch073_validation_progress_matrix.json",
        "batch073_candidate_freeze_preservation.json", "batch072_claim_boundary.json",
        "batch072_final_decision.json", "batch072_summary.md", "SHA256SUMS.txt",
    }
    missing = sorted(name for name in required if not (OUT / name).is_file())
    if missing: errors.append(f"missing:{','.join(missing)}")
    if missing:
        print("Batch072 audit: FAIL")
        return 1
    ingest = load("batch071_artifact_ingest.json")
    if ingest.get("status") != "PASS" or ingest.get("observed_sha256") != EXPECTED_SHA256 or ingest.get("file_count") != 160:
        errors.append("batch071_artifact_identity")
    if ingest.get("outer_manifest", {}).get("checked") != 159:
        errors.append("outer_manifest")
    expected_manifests = {"h8": 70, "h9": 24, "batch070": 28, "batch071": 25}
    if any(ingest.get("internal_manifests", {}).get(key, {}).get("checked") != count for key, count in expected_manifests.items()):
        errors.append("internal_manifests")
    if ingest.get("connexion_patch_sha256") != PATCH_SHA256 or load("batch071_patch_identity_preservation.json").get("sha256") != PATCH_SHA256:
        errors.append("connexion_patch_identity")
    claim = load("batch072_claim_boundary.json")
    if claim.get("historical_count_under_H71_criteria") != 5 or claim.get("native_external_repair_count") != 4:
        errors.append("historical_counts")
    if claim.get("hardened_count_status") != "QUARANTINED_PENDING_REVALIDATION":
        errors.append("hardened_count_status")
    arms = load("connexion_count5_provider_arm_registry.json").get("provider_arms", [])
    if len(arms) != 3 or not all(item.get("nonconflated") for item in arms):
        errors.append("provider_arms_conflated")
    if load("connexion_count5_metamorphic_invariants.json").get("status") != "PASS":
        errors.append("metamorphic_invariants")
    authorization = load("v2_19_authorization_completion_batch072.json")
    if authorization.get("status") != "PASS" or authorization.get("manifest_is_authorization") is not False:
        errors.append("candidate_dispatch_authorization")
    provider = load("v2_19_deterministic_provider_completion_batch072.json")
    if not provider.get("hash_locked_wheelhouse") or not provider.get("editable_install_absent"):
        errors.append("provider_determinism")
    logic = load("candidate_specific_logic_audit_batch072.json")
    if logic.get("status") != "PASS" or not all(logic.get(key) for key in ("exact_hipo_exception_rule_absent", "test_sort_routes_assertion_rule_absent", "prewritten_sort_routes_patch_absent")):
        errors.append("candidate_specific_production_logic")
    contacts = load("amds_fourteen_contact_resolution_batch072.json")
    if contacts.get("contact_count") != 14 or contacts.get("earlier_phase_completion_not_sufficient") is not True:
        errors.append("fourteen_contact_resolution")
    prereg = load("batch072_wave1_preregistration.json")
    cohort = load("batch072_fresh_candidate_cohort.json")
    freeze = load("batch072_cohort_freeze_hash.json")
    if not cohort.get("frozen_before_outcomes") or prereg.get("cohort_hash") != freeze.get("cohort_hash"):
        errors.append("cohort_freeze")
    if load("batch072_diagnostic_arm_execution.json").get("patches_generated") != 0:
        errors.append("diagnostic_arm_patch")
    metrics = load("batch072_wave1_metrics.json")
    if metrics.get("TLD_NSS_imported") or metrics.get("unverified_elbow_gate_used"):
        errors.append("unverified_metric_gate")
    decisions = load("batch072_completion_decisions.json")
    if decisions.get("AMDS_PROSPECTIVE_EFFECTIVENESS") != "NOT_ESTABLISHED" or decisions.get("MEMORY_LIFT") != "not_demonstrated" or decisions.get("SELF_MAINTAINING_SOFTWARE") != "false/not_demonstrated":
        errors.append("claim_boundary")
    if len([path for path in OUT.iterdir() if path.is_file()]) > 45:
        errors.append("evidence_compaction")
    if not audit_manifest():
        errors.append("sha256_manifest")
    print("Batch072 audit:", "PASS" if not errors else "FAIL")
    if errors:
        print("errors:", ", ".join(errors))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
