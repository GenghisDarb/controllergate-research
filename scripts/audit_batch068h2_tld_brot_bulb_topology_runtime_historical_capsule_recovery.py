from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from controllergate.core.evidence import sha256_file
from controllergate.topology.contact_ledger import CONTACT_ROLES

OUT = ROOT / "outputs/post_v2_37_hardening_batch068h2_tld_brot_bulb_topology_runtime_historical_capsule_recovery"


def load(name: str) -> dict[str, object]:
    return json.loads((OUT / name).read_text(encoding="utf-8"))


def expect(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def main() -> int:
    errors: list[str] = []
    required = [
        "batch068h1_artifact_ingest.json", "batch068h1_status_semantics_reconciliation.json", "batch068h1_failed_branch_count_reconciliation.json", "batch068h1_claim_boundary_preservation.json",
        "canonical_isomorphism_law.json", "reference_core_5.json", "contact_ledger_14.json", "activation_license_6.json", "proof_matrix_196.json",
        "brot_local_candidate_catalog.jsonl", "tot_brot_coupled_graph.json", "tot_bulb_environment_volume.json", "tld_shadow_assay.json",
        "nbclient_historical_capsule.json", "nbclient_collection_decision.json", "batch068h2_final_decision.json", "batch068h2_handoff_plan.json", "batch068h2_summary.md", "SHA256SUMS.txt",
    ]
    for name in required:
        expect((OUT / name).is_file(), f"missing:{name}", errors)
    if errors:
        print("Batch068h2 audit FAIL\n" + "\n".join(errors)); return 1

    manifest = {}
    for line in (OUT / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
        digest, rel = line.split(maxsplit=1); rel = rel.strip().lstrip("*"); manifest[rel] = digest
        expect((OUT / rel).is_file() and sha256_file(OUT / rel) == digest, f"manifest_failure:{rel}", errors)
    actual = {path.relative_to(OUT).as_posix() for path in OUT.rglob("*") if path.is_file() and path.name != "SHA256SUMS.txt"}
    expect(set(manifest) == actual, "manifest_coverage_mismatch", errors)

    artifact = load("batch068h1_artifact_ingest.json")
    expect(artifact.get("status") == "PASS", "batch068h1_ingest", errors)
    expect(artifact["outer"]["observed_size_bytes"] == 148852 and artifact["outer"]["observed_sha256"] == "23ad2f411243ff9add84e4cd0141f2b4946b8172a0c96c6e50f17f3b16d51f51", "batch068h1_outer_identity", errors)
    expect(artifact["entries"]["entry_count"] == 145 and artifact["entries"]["unsafe_path_count"] == artifact["entries"]["duplicate_path_count"] == artifact["entries"]["nested_archive_or_cache_payload_count"] == artifact["entries"]["pyc_payload_count"] == 0, "batch068h1_entry_custody", errors)
    expect(artifact["outer_manifest"]["checked"] == 144 and artifact["internal_manifest"]["checked"] == 127, "batch068h1_manifests", errors)
    expect(artifact["raw_zip_committed"] is False, "raw_zip_committed", errors)

    semantics = load("batch068h1_status_semantics_reconciliation.json"); counts = load("batch068h1_failed_branch_count_reconciliation.json")
    expect(semantics["collection_attempt_2_operation_status"] == semantics["collection_attempt_2_gate_decision"] == "NOT_RUN" and semantics["collection_attempt_2_candidate_state"] == "not_run_upstream_blocked" and semantics["reported_as_executed_collection_failure"] is False, "upstream_blocked_semantics", errors)
    expect(counts["executed_failed_branch_count"] == 1 and counts["upstream_blocked_branch_count"] == 1 and counts["total_closed_branch_count"] == 2, "failed_branch_counts", errors)

    canonical = load("canonical_isomorphism_law.json")
    law = load("../dummy") if False else json.loads((ROOT / "configs/tld_brot_bulb_canonical_law_v1.json").read_text(encoding="utf-8"))
    expect(canonical["status"] == law["status"] == "PASS" and canonical["physical_law_claim"] is False, "canonical_law", errors)
    expect("two-dimensional" in law["definitions"]["ToT-BROT"] and "three/four-dimensional" in law["definitions"]["ToT-BULB"], "brot_bulb_definitions", errors)
    expect(law["symbols"]["omega"].endswith("only") and len({law["symbols"][key] for key in ["T_e", "S_e", "winner_N", "contact_topology_size", "tld_recursion_depth_N"]}) == 5, "symbol_conflation", errors)
    contract = json.loads((ROOT / "configs/tld_brot_bulb_artifact_contract_v1.json").read_text(encoding="utf-8"))
    expect(set(contract["physics_lane"]["required_only_for_genuine_physics_computation"]).isdisjoint(actual), "fabricated_physics_artifacts", errors)

    core = load("reference_core_5.json"); ledger = load("contact_ledger_14.json"); activation = load("activation_license_6.json"); matrix = load("proof_matrix_196.json")
    expect(core["role_count"] == len(core["roles"]) == 5, "reference_core_count", errors)
    contacts = ledger["contacts"]; ids = [item["contact_id"] for item in contacts]
    expect(len(contacts) == len(set(ids)) == 14 and set(ids) == {item[0] for item in CONTACT_ROLES}, "contact_ledger_exactness", errors)
    expect(all(item["gate_decision"] != "PASS" or (item["evidence_inputs"] and item["evidence_hashes"] and item["verifier_result"] == "PASS") for item in contacts), "empty_contact_pass", errors)
    expect(len(activation["gates"]) == 6 and all(item["conjunctive"] for item in activation["gates"]) and activation["license_result"] == "BLOCK" and activation["patch_authority"] is False, "activation_ring", errors)
    cells = matrix["cells"]
    expect(len(cells) == len({(item["source_contact"], item["destination_contact"]) for item in cells}) == 196 and matrix["matrix_status"] == "PLANNED", "proof_matrix", errors)

    local_rows = [json.loads(line) for line in (OUT / "brot_local_candidate_catalog.jsonl").read_text(encoding="utf-8").splitlines()]
    expect(len(local_rows) == 25 and len({item["candidate_id"] for item in local_rows}) == 25, "local_brot_count", errors)
    coupled = load("tot_brot_coupled_graph.json"); safety = load("tot_brot_transfer_safety_audit.json"); negative = load("tot_brot_negative_transfer_controls.json")
    expect(safety["typed_evidence_edge_count"] == len(coupled["edges"]) and safety["repair_memory_admitted"] is False, "coupled_topology_evidence", errors)
    expect(negative["status"] == "PASS" and negative["name_similarity_transfer"] == negative["generic_python_transfer"] == negative["generic_pytest_transfer"] == "BLOCK", "negative_transfer", errors)
    volume = load("tot_bulb_environment_volume.json"); targeting = load("tot_bulb_targeting_audit.json")
    expect(volume["targeted_basin_count"] >= 1 and volume["blind_sweep_count"] == 0 and targeting["basin_seed_source"] == "typed_tot_brot_coupling", "targeted_volume", errors)
    expect(volume["global_mask"] != volume["candidate_mask"] and volume["candidate_mask"]["candidate_identity_established"] is True, "mask_separation", errors)
    expect(load("twist_return_invariant_audit.json")["status"] == "PASS" and load("reference_core_round_trip_test.json")["status"] == "PASS", "twist_return", errors)

    assay = load("tld_shadow_assay.json")
    expect(assay["parent_ladder_count"] == 25 and assay["matched_null_count"] == 525 and assay["single_contact_ablation_count"] == 350 and assay["redundant_fifteenth_contact_count"] == 25 and assay["role_permutation_count"] == 25, "tld_registry_counts", errors)
    expect(assay["UI"] == assay["NSS"] == assay["SEP"] == assay["T_e"] == assay["S_e"] == "NOT_ESTABLISHED" and assay["repair_authority"] is False, "tld_claim_boundary", errors)
    expect(load("tld_label_blindness_audit.json")["status"] == load("tld_null_integrity_audit.json")["status"] == "PASS", "tld_integrity", errors)

    runtime = load("topology_runtime_binding.json")
    expect(runtime["runtime_transition_count"] == runtime["topology_bound_transition_count"] == 13 and runtime["unbound_transition_count"] == 0, "runtime_topology_binding", errors)
    expect(all(len(item["topology_gates_evaluated"]) == 9 and all(item[key] for key in ["contact_ledger_hash", "local_brot_hash", "coupled_tot_brot_hash", "tot_bulb_volume_hash", "activation_license_hash", "proof_matrix_hash"]) for item in runtime["records"]), "runtime_topology_hashes", errors)
    core_text = "\n".join(path.read_text(encoding="utf-8") for path in (ROOT / "controllergate/topology").glob("*.py"))
    expect("codex_wave3_jupyter" not in core_text and "nbclient" not in core_text.lower() and "8514e919" not in core_text, "candidate_specific_core_hardcoding", errors)

    capsule = load("nbclient_historical_capsule.json"); collection = load("nbclient_collection_decision.json")
    arms = {item["arm"]: item for item in capsule["provider_arms"]}
    expect(set(arms) == {"observed_historical_environment", "cutoff_compatible_transitive_lock", "current_declared_lock"}, "provider_arm_separation", errors)
    expect(arms["cutoff_compatible_transitive_lock"]["post_cutoff_selected_artifact_count"] == 0 and arms["cutoff_compatible_transitive_lock"]["classification"] == "cutoff_compatible_not_observed_exact", "cutoff_lock", errors)
    expect(arms["current_declared_lock"]["classification"] == "diagnostic_only_not_decision_time_reproduction", "current_lock_authority", errors)
    expect(capsule["warning_basin"]["is_issue316_target_failure"] is False and capsule["warning_basin"]["warning_suppression_establishes_reproduction"] is False, "warning_basin", errors)
    modes = {item["mode"]: item["status"] for item in capsule["target_origin_modes"]}
    expect(modes == {"pinned_source": "PASS", "pinned_wheel": "NOT_RUN", "mixed_origin": "BLOCK"}, "target_origin_modes", errors)
    expect(collection["collection_run_1"] == collection["collection_run_2"] == "NOT_RUN" and collection["collected_node_count"] == collection["test_bodies_executed"] == collection["target_tests_executed"] == collection["workspace_mutations"] == collection["test_tree_mutations"] == 0, "collection_execution_boundary", errors)

    final = load("batch068h2_final_decision.json")
    expect(final["validated_protocol_before"].startswith("v2.16") and final["validated_protocol_after"].startswith("v2.17"), "protocol_promotion", errors)
    expect(load("v2_16_preservation_audit_batch068h2.json")["status"] == load("v2_17_topology_promotion_decision.json")["status"] == "PASS", "protocol_preservation_promotion", errors)
    expect(final["patch_generated"] is final["patch_applied"] is final["repair_count_increment"] is False and final["issue_derived_repair_count"] == final["native_external_repair_count"] == 4, "repair_count_boundary", errors)
    expect(final["full_scoring"] == "NOT_RUN/disallowed" and final["memory_lift"] == "not_demonstrated" and final["self_maintaining_software"] == "false/not_demonstrated", "claim_boundary", errors)
    expect(final["exact_next_allowed_action"] == "batch068h3_historical_transitive_provider_closure", "next_action", errors)

    public_paths = [ROOT / "README.md", ROOT / "docs/current_status.md", ROOT / "docs/capability_inventory.md", ROOT / "docs/technical_validation_gap_report.md", ROOT / "docs/CURRENT_FRONTIER_STATUS.md"]
    forbidden = ["TORUS-BROT", "ToT-BROT", "ToT-BULB", "chromosomal", "Klein Bottle", "Möbius"]
    for path in public_paths:
        text = path.read_text(encoding="utf-8")
        expect(not any(term.lower() in text.lower() for term in forbidden), f"public_internal_language:{path.name}", errors)

    if errors:
        print("Batch068h2 canonical topology runtime historical capsule recovery audit FAIL"); print("\n".join(errors)); return 1
    print("Batch068h2 canonical topology runtime historical capsule recovery audit PASS")
    print("protocol=v2.17 capsule=PARTIAL collection=NOT_RUN repair_authority=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
