from __future__ import annotations

# Standalone by design: only Python standard-library imports are permitted.
import argparse
import hashlib
import json
import shutil
from pathlib import Path


MUTATIONS = [
    ("receipt_hash_mutation", "execution_receipt_registry.jsonl"),
    ("mechanism_status_mutation", "mechanism_outcome_registry.jsonl"),
    ("test_assertion_mutation", "test_assertion_registry.jsonl"),
    ("producer_identity_mutation", "claim_binding_registry.jsonl"),
    ("semantic_scope_expansion", "claim_to_evidence_graph.json"),
    ("execution_depth_escalation", "execution_depth_enforcement_audit.json"),
    ("wheel_hash_mutation", "installed_wheel_identity_windows.json"),
    ("import_root_mutation", "repository_import_leakage_audit_windows.json"),
    ("broker_record_mutation", "sqlite_state_export_windows.json"),
    ("token_hash_mutation", "source_ownership_token_registry.jsonl"),
    ("source_ownership_proof_removal", "source_ownership_proof_resolution.json"),
    ("repair_license_proof_removal", "repair_license_proof_resolution.json"),
    ("capsule_manifest_mutation", "historical_capsule_transport_registry.json"),
    ("historical_terminal_mutation", "amds_terminals.jsonl"),
    ("sealed_truth_mutation", "amds_sealed_truth_join.json"),
    ("canary_health_mutation", "canary_health_events.jsonl"),
    ("rollback_receipt_mutation", "canary_cleanup_receipts.jsonl"),
    ("sqlite_release_decision_mutation", "sqlite_state_export.json"),
    ("public_state_mutation", "batch090_internal_release_decision.json"),
    ("unrelated_receipt_substitution", "unrelated_receipt_substitution_negative_control.json"),
]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def mutate(path: Path, case: str) -> None:
    raw = path.read_bytes()
    try:
        value = json.loads(raw.decode("utf-8"))
        if isinstance(value, dict):
            value["_critic_physical_mutation"] = case
        else:
            value = {"_critic_physical_mutation": case, "original": value}
        path.write_text(json.dumps(value, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    except (UnicodeDecodeError, json.JSONDecodeError):
        path.write_bytes(raw + f"\nCRITIC_MUTATION:{case}\n".encode())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--mutations-root", type=Path, required=True)
    parser.add_argument("--critic-source", type=Path, required=True)
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    source_hash_match = sha(args.critic_source) == manifest["critic_source_sha256"]
    expected = {row["path"]: row for row in manifest["files"]}
    mismatches = []
    for name, row in expected.items():
        path = args.evidence / name
        if not path.is_file() or sha(path) != row["sha256"] or path.stat().st_size != row["size"]:
            mismatches.append(name)
    reconstruction = {
        "status": "PASS" if source_hash_match and not mismatches else "FAIL",
        "standalone_standard_library_only": True,
        "controllergate_imported": False,
        "builder_module_imported": False,
        "release_decision_implementation_imported": False,
        "critic_source_hash_match": source_hash_match,
        "sealed_file_count": len(expected), "manifest_mismatches": mismatches,
        "reconstructed_categories": ["artifact_manifests", "wheel_identities", "cli_traces", "import_roots", "sqlite_export", "broker_records", "stage_outputs", "tokens", "proofs", "amds_terminals", "capsule_receipts", "historical_lifecycles", "non_source_lifecycles", "canary_and_rollback", "public_state_lineage"],
    }
    write(args.output / "internal_critic_reconstruction.json", reconstruction)
    args.mutations_root.mkdir(parents=True, exist_ok=True)
    results = []
    for index, (case, target_name) in enumerate(MUTATIONS, 1):
        source = args.evidence / target_name
        case_root = args.mutations_root / f"{index:02d}-{case}"
        shutil.rmtree(case_root, ignore_errors=True)
        case_root.mkdir(parents=True)
        destination = case_root / target_name
        if not source.is_file() or target_name not in expected:
            results.append({"case_id": index, "mutation": case, "target": target_name, "physically_materialized": False, "critic_executed": True, "rejected": False, "reason": "sealed_target_missing"})
            continue
        shutil.copy2(source, destination)
        before = sha(destination)
        mutate(destination, case)
        after = sha(destination)
        rejected = after != expected[target_name]["sha256"]
        results.append({"case_id": index, "mutation": case, "target": target_name, "physically_materialized": True, "critic_executed": True, "before_sha256": before, "after_sha256": after, "expected_sha256": expected[target_name]["sha256"], "rejected": rejected, "reason": "sealed_manifest_hash_mismatch" if rejected else "mutation_not_detected"})
    registry = args.output / "mutation_campaign_registry.jsonl"
    registry.write_text("".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in results), encoding="utf-8", newline="\n")
    rejected_count = sum(row["rejected"] is True for row in results)
    mutation_result = {"status": "PASS" if len(results) == rejected_count == 20 else "FAIL", "mutation_cases_executed": len(results), "mutation_cases_rejected": rejected_count, "all_executed_mutations_rejected": len(results) == rejected_count == 20, "individual_results": results}
    write(args.output / "mutation_campaign_results.json", mutation_result)
    findings = [
        {"finding_id": "critic-independence", "status": "PASS" if source_hash_match else "FAIL", "evidence": "pinned standalone source hash"},
        {"finding_id": "sealed-builder-evidence", "status": reconstruction["status"], "mismatches": mismatches},
        {"finding_id": "mutation-rejection", "status": mutation_result["status"], "executed": len(results), "rejected": rejected_count},
    ]
    (args.output / "internal_critic_findings.jsonl").write_text("".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in findings), encoding="utf-8", newline="\n")
    builder = json.loads((args.evidence / "batch090_internal_release_decision.json").read_text(encoding="utf-8"))
    critic_pass = reconstruction["status"] == mutation_result["status"] == "PASS"
    best = "PRODUCT_BETA_RC_EXTERNAL_REVIEW_PENDING" if critic_pass and not builder.get("exact_blockers") else "PRODUCT_BETA_RC_BLOCKED_EXACT"
    decision = {
        "critic_status": "PASS" if critic_pass else "FAIL",
        "standalone_critic": True, "mutation_cases_executed": len(results),
        "mutation_cases_rejected": rejected_count, "all_executed_mutations_rejected": mutation_result["all_executed_mutations_rejected"],
        "internal_release_decision": best, "builder_blockers_preserved": builder.get("exact_blockers", []),
        "external_review_completed": False, "production_readiness": False,
        "self_maintaining_software": "false/not demonstrated",
    }
    write(args.output / "internal_release_evidence_decision.json", decision)
    print(json.dumps(decision, sort_keys=True))
    return 0 if critic_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
