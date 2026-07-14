from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NAME = "post_v2_37_hardening_batch088_causal_amds_historical_capsule_product_beta_closure"
REQUIRED = {
    "batch087_artifact_ingest.json", "batch087_artifact_sha256_verification.json",
    "batch087_artifact_manifest_verification.json", "batch087_raw_evidence_preservation.json",
    "batch087_amds_depth_reconciliation.json", "batch087_tld_depth_reconciliation.json",
    "batch087_release_blocker_reconciliation.json", "batch088_pre_fix_expected_failure.json",
    "amds_minesweeper_source_audit.json", "amds_semantic_leakage_audit.json",
    "amds_active_inference_audit.json", "amds_frame_binding_audit.json",
    "amds_contradiction_backtrack_audit.json", "amds_historical_frame.json",
    "amds_decision_frame_registry.json", "amds_probe_contract_registry.jsonl",
    "amds_probe_planning_registry.jsonl", "amds_broker_execution_registry.jsonl",
    "amds_semantic_observation_registry.jsonl", "amds_constraint_event_registry.jsonl",
    "amds_branch_lineage.jsonl", "amds_terminal_registry.jsonl", "amds_sealed_truth_join.json",
    "amds_baseline_results.json", "amds_quality_gate.json", "historical_transport_artifact_registry.json",
    "cloudpickle_source_capsule_verification.json", "cloudpickle_provider_capsule_verification.json",
    "freezegun_source_capsule_verification.json", "freezegun_provider_capsule_verification.json",
    "cloudpickle_canonical_historical_lifecycle.json", "freezegun_canonical_historical_lifecycle.json",
    "historical_non_source_frozen_frame.json", "aifc_non_source_lifecycle.json",
    "imp_non_source_lifecycle.json", "historical_non_source_lifecycle_results.json",
    "repaired_distribution_build.json", "canary_slot_materialization.json", "canary_target_execution.json",
    "canary_distinct_consumer_execution.json", "canary_health_event_registry.jsonl",
    "canary_negative_control.json", "canary_deployment_proof.json", "canary_package_switch.json",
    "canary_exact_rollback.json", "repaired_package_canary_health_rollback.json",
    "proof_bound_interlock_audit.json", "causal_elbow_execution_derivation.json",
    "controller_orientation_return_map.json", "batch087_tld_synthetic_fixture_reconciliation.json",
    "tld_requirements_evidence_ledger.jsonl", "tld_three_projection_execution.json",
    "tld_projection_ablation.json", "tld_curvature_elbow_audit.json", "tld_baseline_parity_audit.json",
    "tld_null_effective_sample_audit.json", "public_state_generation_audit.json",
    "release_version_lineage.json", "batch088_independent_critic.json",
    "batch088_product_beta_rc_decision.json", "batch088_claim_boundary.json",
    "batch088_consolidated_state.json", "batch088_audit_summary.json", "campaign_summary.md",
    "PORTABLE_ARTIFACT_SHA256SUMS.txt", "SHA256SUMS.txt",
}


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def verify_manifest(output: Path, name: str) -> list[str]:
    failures = []
    for line in (output / name).read_text(encoding="utf-8").splitlines():
        expected, relative = line.split("  ", 1)
        path = output / relative
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            failures.append(relative)
    return failures


def audit(output: Path, *, verify_manifests: bool) -> tuple[bool, dict]:
    missing = sorted(name for name in REQUIRED if not (output / name).is_file())
    errors = []
    if missing:
        errors.append("required_outputs_missing")
    ingest = read(output / "batch087_artifact_ingest.json")
    artifact = read(output / "batch087_artifact_manifest_verification.json")
    pre = read(output / "batch088_pre_fix_expected_failure.json")
    frames = read(output / "amds_decision_frame_registry.json")["frames"]
    leakage = read(output / "amds_semantic_leakage_audit.json")
    active = read(output / "amds_active_inference_audit.json")
    adversarial = read(output / "amds_contradiction_backtrack_audit.json")
    quality = read(output / "amds_quality_gate.json")
    claims = read(output / "batch088_claim_boundary.json")
    release = read(output / "batch088_product_beta_rc_decision.json")
    critic = read(output / "batch088_independent_critic.json")
    if ingest.get("status") != "PASS" or artifact.get("status") != "PASS": errors.append("batch087_ingest_invalid")
    if pre.get("status") != "BATCH088_PRE_FIX_AUDIT_FAIL_EXPECTED" or int(pre.get("detected_defect_count", 0)) < 17: errors.append("expected_red_critic_invalid")
    if len(frames) != 8 or len({row["frame_hash"] for row in frames}) != 8: errors.append("candidate_specific_frames_invalid")
    if leakage.get("label_leakage_count") != 0: errors.append("semantic_leakage")
    if active.get("status") != "PASS": errors.append("active_inference_audit_failed")
    if adversarial.get("status") != "PASS" or adversarial.get("contradictions", 0) < 2: errors.append("contradiction_suite_failed")
    if quality.get("prospective_effectiveness") != "NOT_ESTABLISHED": errors.append("prospective_overclaim")
    if claims != {
        "amds_prospective_effectiveness": "NOT_ESTABLISHED", "automatic_merge": "inactive",
        "full_scoring": "NOT_RUN/disallowed", "historical_replay_count_increment": 0,
        "issue_derived_repair_count": 6, "memory_status": "shadow_only_not_used",
        "native_external_repair_count": 4, "production_readiness": False,
        "prospective_memory_lift": "not demonstrated", "public_write_connectors": "inactive",
        "self_maintaining_software": "false/not demonstrated",
    }: errors.append("claim_boundary_changed")
    if release.get("status") != "PRODUCT_BETA_RC_BLOCKED_EXACT" or release.get("package_version") != "0.2.0b2.dev0": errors.append("release_decision_invalid")
    if critic.get("status") != "PASS_BLOCK_DECISION": errors.append("independent_critic_invalid")
    manifest_failures = [] if missing or not verify_manifests else sorted(set(verify_manifest(output, "SHA256SUMS.txt") + verify_manifest(output, "PORTABLE_ARTIFACT_SHA256SUMS.txt")))
    if manifest_failures: errors.append("manifest_hash_failure")
    result = {
        "errors": errors,
        "manifest_failures": manifest_failures,
        "missing": missing,
        "scientific_result": release.get("status"),
        "status": "PASS" if not errors else "FAIL",
    }
    return not errors, result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "outputs" / NAME)
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    ok, result = audit(args.output, verify_manifests=args.verify_only)
    if not args.verify_only:
        (args.output / "batch088_audit_summary.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(result, sort_keys=True))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
