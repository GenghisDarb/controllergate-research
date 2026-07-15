"""Standard-library-only semantic release evidence critic for Batch091."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rule(condition: bool, rule_id: str, blocker: str, reopen: str, findings: list[dict[str, str]]) -> None:
    if not condition:
        findings.append({"rule": rule_id, "exact_blocker": blocker, "expected_reopen_condition": reopen})


def inspect(manifest_path: Path, bundle_path: Path) -> tuple[int, dict[str, object]]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    custody_findings = []
    if manifest.get("evidence_sha256") != sha(bundle_path):
        custody_findings.append("sealed_evidence_hash_mismatch")
    if manifest.get("critic_source_sha256") != sha(Path(__file__)):
        custody_findings.append("pinned_critic_source_hash_mismatch")
    if custody_findings:
        return 2, {"status": "BLOCK", "custody_status": "FAIL", "semantic_status": "NOT_EVALUATED", "findings": custody_findings}
    state = json.loads(bundle_path.read_text(encoding="utf-8"))
    c = state["capsules"]; a = state["amds"]; p = state["authority"]
    l = state["lifecycles"]; d = state["distribution_canary"]; r = state["release"]
    findings: list[dict[str, str]] = []
    rule(c["cloudpickle_hidden_files"] == 58, "CAPSULE_CLOUDPICKLE_HIDDEN_CONSERVATION", "cloudpickle_source_capsule_conservation_failed", "restore all 58 manifest-declared hidden files", findings)
    rule(c["freezegun_hidden_files"] == 39, "CAPSULE_FREEZEGUN_HIDDEN_CONSERVATION", "freezegun_source_capsule_conservation_failed", "restore all 39 manifest-declared hidden files", findings)
    rule(c["transport_residue_count"] == 0, "CAPSULE_RUNTIME_RESIDUE_PROHIBITED", "short_lived_artifact_runtime_residue", "remove runtime and environment paths", findings)
    rule(a["builder_terminal_label_count"] == 0, "AMDS_BUILDER_TRUTH_BLIND", "amds_builder_terminal_label_leakage", "remove terminal labels from builder inputs", findings)
    rule(a["literal_true_measurement_count"] == 0, "AMDS_MEASUREMENTS_EXECUTED", "amds_measurement_receipts_missing", "supply executed measurement receipts", findings)
    rule(p["source_token_minted_after_probe"], "SOURCE_TOKEN_REQUIRES_EXECUTED_PROBE", "source_ownership_without_executed_probe", "execute and seal candidate-bound probe", findings)
    rule(p["direct_source_contact"], "SOURCE_OWNERSHIP_REQUIRES_DIRECT_CONTACT", "inferred_support_is_not_source_ownership", "supply direct AST, call, or data-flow contact", findings)
    rule(p["causal_alternatives_remaining"] == 1, "CAUSAL_ELBOW_CATEGORICAL", "causal_elbow_not_closed", "reduce current alternatives to one", findings)
    rule(p["candidate_bound_human_approval"], "LICENSE_REQUIRES_CANDIDATE_BOUND_APPROVAL", "generic_human_approval_authority", "provide candidate, run, patch, path, nonce, and expiry binding", findings)
    rule(p["repair_license_use_count"] == 1, "REPAIR_LICENSE_SINGLE_USE", "spent_repair_license_reused", "mint a fresh single-use license", findings)
    rule(a["source_terminal_committed_before_truth_join"], "SOURCE_TERMINAL_PRECEDES_TRUTH_JOIN", "source_terminal_changed_before_truth_join", "restore sealed source terminal commitment", findings)
    rule(p["non_source_source_token_count"] == 0, "NON_SOURCE_HAS_NO_SOURCE_AUTHORITY", "non_source_source_ownership_token_minted", "remove source authority from non-source episode", findings)
    rule(l["fresh_replay_workspace_independent"], "FRESH_REPLAY_WORKSPACE_INDEPENDENT", "fresh_replay_workspace_reused", "use a fresh capsule activation", findings)
    rule(not l["diagnosis_provider_reused_for_replay"], "REPLAY_PROVIDER_INDEPENDENT", "diagnosis_provider_reused_for_replay", "activate an equivalent second provider", findings)
    rule(p["observed_patch_sha256"] == p["approved_patch_sha256"], "PATCH_BYTES_MATCH_APPROVAL", "approved_patch_identity_mismatch", "restore approved patch bytes", findings)
    rule(len(set(d["health_event_classes"])) == 3, "CANARY_THREE_DISTINCT_HEALTH_EVENTS", "canary_health_event_not_independent", "execute three distinct health classes", findings)
    rule(d["negative_canary_rejected"], "NEGATIVE_CANARY_MUST_REJECT", "negative_canary_passed", "restore original buggy-distribution rejection", findings)
    rule(d["rollback_original_hash"] == d["rollback_restored_hash"], "ROLLBACK_EXACT_PACKAGE_IDENTITY", "rollback_restored_wrong_package_hash", "restore original active package hash", findings)
    rule(r["historical_increment"] == 0, "HISTORICAL_NON_COUNTING_BOUNDARY", "historical_repair_count_changed", "restore zero historical increment", findings)
    rule(r["public_status"] == "PRODUCT_BETA_RC_EXTERNAL_REVIEW_PENDING", "PUBLIC_EXTERNAL_REVIEW_BOUNDARY", "public_state_overclaim", "restore external-review-pending status", findings)
    rule(r["critic_finding_count"] >= 1, "CRITIC_FINDING_CONSERVATION", "critic_finding_removed", "restore the external-review finding", findings)
    rule(r["execution_receipt_candidate_bound"], "EXECUTION_RECEIPT_CONTEXT_BOUND", "unrelated_execution_receipt_substituted", "restore candidate/run/stage-bound receipt", findings)
    rule(c["status"] == "PASS" and a["status"] == "PASS" and p["status"] == "PASS", "CORE_RECONSTRUCTION_PASS", "core_semantic_reconstruction_failed", "restore core evidence invariants", findings)
    rule(all(value == "PASS" for value in l["statuses"]), "FOUR_HISTORICAL_LIFECYCLES_PASS", "historical_lifecycle_closure_failed", "complete four installed lifecycles", findings)
    rule(d["aggregate_result"] == "DEPLOYED_CANARY_HEALTH_ROLLBACK_PASS", "CANARY_AGGREGATE_PASS", "deployed_canary_health_rollback", "complete distribution, health, switch, rollback, and cleanup", findings)
    reconstruction = {
        "capsule_conservation": c["status"], "amds_custody_and_quality": a["status"],
        "authority_chains": p["status"], "historical_lifecycles": l["statuses"],
        "repaired_distribution_and_canary": d["aggregate_result"], "historical_increment": r["historical_increment"],
        "public_status": r["public_status"], "semantic_rule_count": 25,
    }
    result = {"status": "SEMANTIC_STANDALONE_CRITIC_PASS" if not findings else "BLOCK", "custody_status": "PASS",
              "semantic_status": "PASS" if not findings else "FAIL", "reconstruction": reconstruction, "findings": findings}
    return (0 if not findings else 3), result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    code, result = inspect(args.manifest, args.bundle)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"status": result["status"], "custody_status": result["custody_status"], "semantic_status": result["semantic_status"]}, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
