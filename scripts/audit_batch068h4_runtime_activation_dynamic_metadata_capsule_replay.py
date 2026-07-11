from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
OUT = ROOT / "outputs/post_v2_37_hardening_batch068h4_runtime_activation_dynamic_metadata_capsule_replay"

from controllergate.core.frontier_state import verify_state_hash
from controllergate.runtime.execution_authorization import verify_authorization
from controllergate.runtime.execution_checkpoint import load_checkpoint
from controllergate.runtime.execution_plan import verify_plan


def load(name: str): return json.loads((OUT / name).read_text(encoding="utf-8"))


def main() -> int:
    errors: list[str] = []
    required = ["batch068h3_artifact_ingest.json", "batch068h3_status_semantics_correction.json", "runtime_execution_authorization_batch068h4.json", "runtime_execution_plan_batch068h4.json", "runtime_event_ledger_batch068h4.jsonl", "runtime_checkpoint_batch068h4.json", "runtime_dispatch_result_batch068h4.json", "canonical_cli_execution_audit_batch068h4.json", "nbclient_root_requirement_reconstruction.json", "historical_release_file_catalog.jsonl", "historical_artifact_acquisition_manifest.json", "historical_static_metadata_coverage.json", "dynamic_metadata_security_audit.json", "historical_dependency_graph_v2.json", "historical_complete_lock_v2.json", "historical_lock_verification_v2.json", "historical_environment_arm_registry.json", "collection_run1_result_batch068h4.json", "collection_run2_result_batch068h4.json", "prerepair_reproduction_decision_batch068h4.json", "nbclient_ast_extrusion_batch068h4.json", "controllergate_tld_dimensional_compatibility_audit.json", "product_execution_capability_matrix_batch068h4.json", "v2_18_preservation_audit_batch068h4.json", "v2_19_promotion_decision_batch068h4.json", "repository_burden_audit_batch068h4.json", "batch068h4_final_decision.json", "public_claim_boundary_audit_batch068h4.json", "SHA256SUMS.txt"]
    for name in required:
        if not (OUT / name).is_file(): errors.append(f"missing:{name}")
    if errors: print("Batch068h4 audit FAIL\n" + "\n".join(errors)); return 1
    ingest = load("batch068h3_artifact_ingest.json")
    if ingest.get("status") != "PASS" or ingest.get("observed_size_bytes") != 299282 or ingest.get("observed_sha256") != "81ad2ee4ae32a99fd7a43afd6dc117204c546666c37b56d7b4d3b000102c670b" or ingest.get("file_count") != 133: errors.append("batch068h3_identity_invalid")
    if ingest.get("outer_manifest", {}).get("checked") != 132 or ingest.get("outer_manifest", {}).get("status") != "PASS" or ingest.get("internal_manifest", {}).get("checked") != 103 or ingest.get("internal_manifest", {}).get("status") != "PASS": errors.append("batch068h3_manifests_invalid")
    semantics = load("batch068h3_status_semantics_correction.json")
    if semantics.get("selected_direct_root_artifact_count") != 15 or semantics.get("fully_transitively_resolved_package_count") != 0 or semantics.get("conflict_free_closure_established") is not False: errors.append("batch068h3_semantics_not_corrected")
    if verify_plan(load("runtime_execution_plan_batch068h4.json")).get("status") != "PASS": errors.append("runtime_plan_invalid")
    checkpoint = load_checkpoint(OUT / "runtime_checkpoint_batch068h4.json")
    if checkpoint.get("status") != "PASS": errors.append("checkpoint_invalid")
    cli = load("canonical_cli_execution_audit_batch068h4.json")
    if cli.get("status") != "PASS" or not all(cli.get(field) is True for field in ["authorization_required", "missing_authorization_blocks", "stale_authorization_blocks", "overbroad_authorization_blocks", "spent_authorization_blocks", "phase_skipping_blocks"]): errors.append("canonical_cli_guards_invalid")
    roots = load("nbclient_root_requirement_reconstruction.json")
    if roots.get("status") != "PASS" or not roots.get("records") or any(not all(item.get(key) is not None for key in ["source_file", "source_hash", "source_location", "raw_requirement", "normalized_requirement", "dependency_class"]) for item in roots.get("records", [])): errors.append("root_reconstruction_invalid")
    releases = [json.loads(line) for line in (OUT / "historical_release_file_catalog.jsonl").read_text(encoding="utf-8").splitlines() if line]
    if not releases or any(not item.get("artifact_file_url") or item.get("artifact_file_url") == item.get("project_metadata_url") for item in releases): errors.append("release_file_enumeration_or_urls_invalid")
    acquisitions = load("historical_artifact_acquisition_manifest.json")
    if acquisitions.get("status") == "PASS" and any(item.get("sha256") != item.get("expected_sha256") for item in acquisitions.get("records", [])): errors.append("artifact_hash_verification_failed")
    lock = load("historical_complete_lock_v2.json")
    if lock.get("status") == "PASS" and (lock.get("unresolved_metadata_nodes") or lock.get("unresolved_dependency_nodes") or lock.get("constraint_conflicts") or lock.get("post_cutoff_selected_artifact_count") != 0 or any(lock.get(key) != "PASS" for key in ["runtime_dependency_closure", "test_dependency_closure", "build_dependency_closure"])): errors.append("complete_lock_invariant_invalid")
    arms = load("historical_environment_arm_registry.json")
    if arms.get("status") != "PASS" or len(arms.get("arms", {})) != 3: errors.append("environment_arms_conflated")
    run1 = load("collection_run1_result_batch068h4.json"); run2 = load("collection_run2_result_batch068h4.json")
    if run2.get("status") == "PASS" and (run1.get("status") != "PASS" or not run1.get("node_ids") or run1.get("node_ids") != run2.get("node_ids")): errors.append("duplicate_collection_invalid")
    if run1.get("test_bodies_executed", 0) != 0 or run1.get("target_tests_executed", 0) != 0: errors.append("collection_executed_test_body")
    prerepair = load("prerepair_reproduction_decision_batch068h4.json")
    if prerepair.get("status") not in {"NOT_RUN"} and run2.get("status") != "PASS": errors.append("prerepair_before_duplicate_collection")
    tld = load("controllergate_tld_dimensional_compatibility_audit.json")
    if tld.get("current_fourteen_contact_single_snapshot_for_TLD_XI") != "INELIGIBLE_BY_CONSTRUCTION" or tld.get("metric_eligible") is not False or tld.get("product_blocker") is not False: errors.append("tld_dimension_boundary_invalid")
    final = load("batch068h4_final_decision.json")
    if final.get("patch_generated") or final.get("patch_applied") or final.get("repair_increment") or final.get("issue_derived_repair_count") != 4 or final.get("native_external_repair_count") != 4: errors.append("repair_boundary_changed")
    if final.get("full_scoring") != "NOT_RUN/disallowed" or final.get("memory_lift") != "not_demonstrated" or final.get("self_maintaining_software") != "false/not_demonstrated": errors.append("claim_boundary_changed")
    promotion = load("v2_19_promotion_decision_batch068h4.json")
    if promotion.get("status") == "PASS" and run2.get("status") != "PASS": errors.append("v2_19_promoted_without_duplicate_collection")
    manifest = OUT / "SHA256SUMS.txt"; covered = set()
    for line in manifest.read_text(encoding="utf-8").splitlines():
        digest, rel = line.split(maxsplit=1); rel = rel.strip().lstrip("*"); covered.add(rel); path = OUT / rel
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != digest: errors.append(f"manifest_mismatch:{rel}")
    if errors:
        print("Batch068h4 runtime activation/dynamic metadata/capsule replay audit FAIL"); print("\n".join(errors)); return 1
    print("Batch068h4 runtime activation/dynamic metadata/capsule replay audit PASS"); return 0


if __name__ == "__main__": raise SystemExit(main())
