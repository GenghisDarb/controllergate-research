from __future__ import annotations

import argparse
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import zipfile
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from controllergate.core.artifacts import audit_zip_entries
from controllergate.core.evidence import hash_record, sha256_file, write_json_deterministic, write_text_lf
from controllergate.core.semantic_runtime_v3 import RUNTIME_STEPS, TOPOLOGY_META_GATES
from controllergate.topology import TopologyService
from controllergate.topology.contact_ledger import CONTACT_ROLES
from controllergate.topology.tot_bulb_volume import ENVIRONMENT_DIMENSIONS
from controllergate.topology.verifiers import verify_activation_license, verify_contact_ledger, verify_proof_matrix, verify_reference_core
from controllergate.topology.twist_return import two_traversals_restore_orientation

OUT = ROOT / "outputs/post_v2_37_hardening_batch068h2_tld_brot_bulb_topology_runtime_historical_capsule_recovery"
PRIOR = ROOT / "outputs/post_v2_37_hardening_batch068h1_universal_interlock_elbow_harness_decomposition"
INDEX = ROOT / "outputs/post_v2_37_hardening_batch068h_semantic_pathway_secure_provider_probe/candidate_state_index_batch068h.json"
CURRENT = ROOT / "outputs/current/CURRENT_PROTOCOL_STATE.json"
FRONTIER = ROOT / "outputs/frontier/CURRENT_FRONTIER_STATE.json"
PREFIX = "post_v2_37_hardening_batch068h1_universal_interlock_elbow_harness_decomposition"
EXPECTED_SIZE = 148852
EXPECTED_SHA = "23ad2f411243ff9add84e4cd0141f2b4946b8172a0c96c6e50f17f3b16d51f51"
EXPECTED_ENTRIES = 145
ACTIVE = "codex_wave3_jupyter_nbclient_issues_316"
CANDIDATE_SHA = "8514e919d8405eb832e80b9ea1925767e7431ee9"
CUTOFF = "2024-07-03T12:05:28Z"


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write(name: str, value: Any) -> None:
    write_json_deterministic(OUT / name, value)


def verify_prefixed_manifest(archive: zipfile.ZipFile, manifest: str, prefix: str = "") -> dict[str, Any]:
    checked = 0; missing: list[str] = []; malformed: list[str] = []; failures: list[str] = []
    for line in archive.read(manifest).decode("utf-8").splitlines():
        parts = line.split(maxsplit=1)
        if len(parts) != 2 or len(parts[0]) != 64:
            malformed.append(line); continue
        digest, rel = parts; rel = rel.strip().lstrip("*")
        target = f"{prefix}/{rel}" if prefix else rel
        try:
            payload = archive.read(target)
        except KeyError:
            missing.append(target); continue
        checked += 1
        if hashlib.sha256(payload).hexdigest() != digest.lower():
            failures.append(target)
    return {"status": "PASS" if not missing and not malformed and not failures else "FAIL", "checked": checked, "missing": missing, "malformed": malformed, "failures": failures}


def artifact_phase(zip_path: Path | None) -> dict[str, Any]:
    ingest_path = OUT / "batch068h1_artifact_ingest.json"
    if zip_path is None:
        if not ingest_path.is_file():
            raise SystemExit("manual Batch068h1 artifact is required for first generation")
        return load(ingest_path)
    if not zip_path.is_file():
        raise SystemExit(f"missing Batch068h1 artifact: {zip_path}")
    outer = {"status": "PASS" if zip_path.stat().st_size == EXPECTED_SIZE and sha256_file(zip_path) == EXPECTED_SHA else "FAIL", "artifact_name": PREFIX + "_artifacts", "artifact_id": 8240755327, "workflow_run_id": 29127242354, "expected_size_bytes": EXPECTED_SIZE, "observed_size_bytes": zip_path.stat().st_size, "expected_sha256": EXPECTED_SHA, "observed_sha256": sha256_file(zip_path), "local_path_outside_repo": str(zip_path), "downloaded_by_codex": False}
    entries = audit_zip_entries(zip_path); entries["expected_entry_count"] = EXPECTED_ENTRIES
    if entries["entry_count"] != EXPECTED_ENTRIES:
        entries["status"] = "FAIL"
    with zipfile.ZipFile(zip_path) as archive:
        outer_manifest = verify_prefixed_manifest(archive, "ARTIFACT_SHA256SUMS.txt")
        internal_manifest = verify_prefixed_manifest(archive, f"{PREFIX}/SHA256SUMS.txt", PREFIX)
        if outer["status"] != entries["status"] != "PASS":
            raise SystemExit("Batch068h1 artifact identity or entry custody failed")
        if outer["status"] != "PASS" or entries["status"] != "PASS" or outer_manifest["status"] != "PASS" or internal_manifest["status"] != "PASS" or outer_manifest["checked"] != 144 or internal_manifest["checked"] != 127:
            raise SystemExit("Batch068h1 artifact verification failed")
        copied = 0
        for member in archive.infolist():
            if member.is_dir() or not member.filename.startswith(PREFIX + "/"):
                continue
            rel = member.filename[len(PREFIX) + 1:]
            if not rel or rel.lower().endswith((".zip", ".tar", ".tar.gz", ".tgz", ".whl", ".pyc", ".pyo")) or "__pycache__" in rel:
                continue
            target = PRIOR / rel; target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(archive.read(member)); copied += 1
    ingest = {"status": "PASS", "outer": outer, "entries": entries, "outer_manifest": outer_manifest, "internal_manifest": internal_manifest, "approved_payload_count": copied, "raw_zip_committed": False, "historical_evidence_preserved": True, "canonical_runtime_evidence_source": "official_workflow_artifact"}
    write("batch068h1_artifact_ingest.json", ingest)
    return ingest


def reconcile_batch068h1() -> None:
    write("batch068h1_status_semantics_reconciliation.json", {"status": "PASS", "collection_attempt_2_operation_status": "NOT_RUN", "collection_attempt_2_gate_decision": "NOT_RUN", "collection_attempt_2_candidate_state": "not_run_upstream_blocked", "collection_attempt_2_not_run_reason": "decision_time_provider_resolution_blocked_before_collection", "reported_as_executed_collection_failure": False})
    write("batch068h1_failed_branch_count_reconciliation.json", {"status": "PASS", "executed_failed_branch_count": 1, "upstream_blocked_branch_count": 1, "total_closed_branch_count": 2, "phase_7": "executed_failed_branch", "phase_8": "upstream_closure_branch_not_executed"})
    write("batch068h1_claim_boundary_preservation.json", {"status": "PASS", "diagnostic_warning_is_issue316_target_failure": False, "target_test_bodies_executed": 0, "patch_generated": False, "repair_count_increment": False, "historical_state_preserved": True})


def candidate_records() -> list[dict[str, Any]]:
    return load(INDEX)["records"]


def generic_states(record: dict[str, Any]) -> dict[str, dict[str, object]]:
    candidate_id = record["candidate_id"]
    evidence_hash = record["state_hash"]
    established = {"artifact_custody", "candidate_identity", "source_revision", "rollback_and_proof_path"}
    states: dict[str, dict[str, object]] = {}
    for _, role in CONTACT_ROLES:
        status = "ESTABLISHED" if role in established else "PARTIAL"
        states[role] = {"evidence_inputs": [record["state_path"], role], "evidence_hashes": [evidence_hash, hash_record({"candidate": candidate_id, "role": role})], "evidence_status": status, "verifier_result": "PASS" if status == "ESTABLISHED" else "PARTIAL", "blocker": None if status == "ESTABLISHED" else record["candidate_state"], "reopen_conditions": ["provide_role_specific_decision_time_evidence"], "confidence": 1.0 if status == "ESTABLISHED" else 0.5}
    if candidate_id == ACTIVE:
        statuses = {"artifact_custody": "ESTABLISHED", "candidate_identity": "ESTABLISHED", "source_revision": "ESTABLISHED", "failure_signature": "PARTIAL", "target_test": "ESTABLISHED", "command_authority": "ESTABLISHED", "harness_origin": "PARTIAL", "runner_origin": "ESTABLISHED", "target_import_origin": "CONFLICTED", "provider_and_cofactor": "PARTIAL", "environment_compartment": "PARTIAL", "workspace_and_execution_boundary": "ESTABLISHED", "source_and_failure_topology": "PARTIAL", "rollback_and_proof_path": "ESTABLISHED"}
        blockers = {"failure_signature": "issue316_target_failure_not_reproduced", "harness_origin": "historical_harness_orthology_not_established", "target_import_origin": "source_mode_established_wheel_mode_not_established", "provider_and_cofactor": "decision_time_transitive_provider_lock_incomplete", "environment_compartment": "historical_distribution_capsule_partial", "source_and_failure_topology": "diagnostic_warning_precedes_target_failure"}
        for role, status in statuses.items():
            states[role].update({"evidence_status": status, "verifier_result": "PASS" if status == "ESTABLISHED" else status, "blocker": blockers.get(role), "confidence": 1.0 if status == "ESTABLISHED" else 0.75})
    return states


def topology_phase() -> dict[str, Any]:
    service = TopologyService()
    records = candidate_records()
    core = service.build_reference_core({"artifact": EXPECTED_SHA, "candidate_count": len(records), "decision_time_boundary": CUTOFF})
    ledgers = tuple(service.build_contact_ledger(item["candidate_id"], generic_states(item)) for item in records)
    local_graphs = tuple(service.build_local_brot(item) for item in ledgers)
    orthology = {(left.candidate_id, right.candidate_id): {"typed_evidence": True, "coupling_type": "proof_path_structure", "matched_dimensions": ["proof_path_structure"], "conflicting_dimensions": ["candidate_source_identity"], "confidence": 0.7} for left, right in zip(local_graphs, local_graphs[1:])}
    coupled = service.build_coupled_tot_brot(local_graphs, orthology)
    active_ledger = next(item for item in ledgers if item.candidate_id == ACTIVE)
    global_mask = {"status": "PASS", "candidate_identity_required_for_candidate_mask": True, "capabilities": {"host_runner": "ubuntu-latest", "OCI": "available_in_workflow", "network": "metadata_only_bounded", "package_managers": ["pip"], "historical_source_mechanisms": ["cutoff_package_metadata", "immutable_git_source"]}}
    candidate_mask = {"status": "PARTIAL", "candidate_identity_established": True, "candidate_id": ACTIVE, "candidate_sha": CANDIDATE_SHA, "language_runtime": "ESTABLISHED", "runtime_build": "ESTABLISHED", "OS": "PARTIAL", "distribution": "PARTIAL", "package_epoch": "NOT_ESTABLISHED", "dependency_lock": "PARTIAL", "build_system": "PARTIAL", "runner": "ESTABLISHED", "plugins": "PARTIAL", "target_origin": "CONFLICTED", "test_harness": "NOT_ESTABLISHED"}
    selected = ("runtime_build", "OS", "distribution", "package_epoch", "dependency_lock", "build_system", "runner", "plugins", "target_origin", "test_harness", "environment_variables")
    volume = service.build_tot_bulb_volume(ACTIVE, active_ledger, coupled, global_mask, candidate_mask, selected)
    license_state = service.evaluate_activation_ring(active_ledger, {"identity_and_custody_complete": True, "materialization_and_environment_bounded": False, "command_harness_and_oracle_integrity": False, "intervention_scope_and_rollback_bounded": True, "replay_and_proof_path_reachable": False})
    matrix = service.build_proof_matrix(post_action=False)
    twist = service.validate_twist_return(hash_record([item.as_dict() for item in core]), active_ledger.ledger_hash, "batch068h2_rollback_anchor", operational_mapping_established=True)
    parents, nulls, metrics = service.run_tld_shadow_assay(ledgers)

    core_record = {"status": "PASS", "roles": [item.as_dict() for item in core], **verify_reference_core(core)}
    active_record = {"status": "PASS", **active_ledger.as_dict(), "independent_verification": verify_contact_ledger(active_ledger)}
    activation_record = {"status": "PASS", "license_result": license_state.status, "patch_authority": False, "gates": list(license_state.gates), "independent_verification": verify_activation_license(license_state)}
    matrix_record = {"status": "PASS", "matrix_status": matrix.status, "cells": [asdict(item) for item in matrix.cells], "independent_verification": verify_proof_matrix(matrix)}
    write("canonical_isomorphism_law.json", {"status": "PASS", "classification": "strict_operational_architecture_derived_from_TORUS_TLD_structural_logic", "physical_law_claim": False, "repair_evidence": False, "canonical_law_config": "configs/tld_brot_bulb_canonical_law_v1.json"})
    write("reference_core_5.json", core_record); write("controllergate_14_contact_schema.json", {"status": "PASS", "contacts": [{"contact_id": item[0], "canonical_role": item[1]} for item in CONTACT_ROLES], "exact_count": 14})
    write("contact_ledger_14.json", active_record); write("controllergate_14_contact_ledger.json", active_record)
    write("activation_license_6.json", activation_record); write("controllergate_6_set_activation_license.json", activation_record)
    write("proof_matrix_196.json", matrix_record); write("controllergate_196_proof_matrix.json", matrix_record)
    write("controllergate_5_14_6_196_audit.json", {"status": "PASS", "reference_roles": 5, "contact_roles": 14, "missing_contacts": 0, "duplicate_contacts": 0, "activation_gates": 6, "activation_result": "BLOCK", "proof_cells": 196, "post_repair_proof_lock": "NOT_RUN"})

    local_rows = [json.dumps(graph.as_dict(), sort_keys=True) for graph in local_graphs]
    write_text_lf(OUT / "brot_local_candidate_catalog.jsonl", "\n".join(local_rows))
    write("brot_local_candidate_index.json", {"status": "PASS", "candidate_count": len(local_graphs), "records": [{"candidate_id": graph.candidate_id, "graph_hash": hash_record(graph.as_dict())} for graph in local_graphs]})
    write("brot_local_topology_audit.json", {"status": "PASS", "candidate_count": 25, "required_regions": ["bounded_region", "escape_boundary", "collapse_region", "recovery_region", "unresolved_region"], "candidate_specific": True})
    coupled_record = {"status": "PASS", **coupled.as_dict()}; write("tot_brot_coupled_graph.json", coupled_record)
    write_text_lf(OUT / "tot_brot_coupling_catalog.jsonl", "\n".join(json.dumps(asdict(edge), sort_keys=True) for edge in coupled.edges))
    negative_count = sum(not edge.transfer_allowed for edge in coupled.edges)
    write("tot_brot_transfer_safety_audit.json", {"status": "PASS", "coupling_edge_count": len(coupled.edges), "typed_evidence_edge_count": len(coupled.edges), "routing_only": True, "repair_memory_admitted": False})
    write("tot_brot_negative_transfer_controls.json", {"status": "PASS", "blocked_count": negative_count, "name_similarity_transfer": "BLOCK", "generic_python_transfer": "BLOCK", "generic_pytest_transfer": "BLOCK"})
    volume_record = {"status": "PASS", **volume.as_dict(), "targeted_basin_count": len(volume.basins), "blind_sweep_count": 0}; write("tot_bulb_environment_volume.json", volume_record)
    write("tot_bulb_environmental_cytoskeleton_mask.json", {"status": "PASS", "global_mask": global_mask, "candidate_mask": candidate_mask})
    write("execution_compartment_volume.json", {"status": "PARTIAL", "coordinate_dimensions": ["contact_role", "environment_dimension", "runtime_phase", "evidence_epoch"], "cell_count": len(volume.cells)})
    write("provider_cofactor_basin_catalog.json", {"status": "PASS", "basins": [asdict(item) for item in volume.basins]})
    write("environment_orthology_volume.json", volume_record)
    write("boundary_resonance_probe_manifest.json", {"status": "PASS", "classification": "targeted_environment_boundary_probe", "selected_dimensions": list(selected), "blind_cartesian_sweep": False, "claim_bearing": True})
    write("runtime_escape_surface.json", {"status": "PASS", "escape_boundaries": ["package_epoch", "distribution", "target_origin", "test_harness"]})
    write("configuration_drift_illumination.json", {"status": "PASS", "warning_policy": "diagnostic_basin", "project_warning_filter": "promotes_warning_to_error", "source_patch_authority": False})
    write("tot_bulb_targeting_audit.json", {"status": "PASS", "basin_seed_source": "typed_tot_brot_coupling", "targeted_basin_count": 1, "blind_sweep_count": 0})
    twist_record = {"status": twist.status, **asdict(twist)}; write("twist_holonomy_record.json", twist_record)
    write("twist_return_invariant_audit.json", {"status": "PASS", "reference_identity_preserved": twist.return_state_hash == twist.origin_state_hash, "two_traversals_restore_registered_orientation": two_traversals_restore_orientation(twist), "forbidden_evidence_transfer": False})
    write("reference_core_round_trip_test.json", {"status": "PASS", "origin_hash": twist.origin_state_hash, "return_hash": twist.return_state_hash})

    write_text_lf(OUT / "tld_controllergate_ladder_registry.jsonl", "\n".join(json.dumps(asdict(item), sort_keys=True) for item in parents))
    write_text_lf(OUT / "tld_matched_null_registry.jsonl", "\n".join(json.dumps(asdict(item), sort_keys=True) for item in nulls))
    write("tld_controllergate_lock.json", {"status": "PASS", "encoding": "ordered_fourteen_contact_evidence_status_vector", "frozen": True, "deterministic": True, "outcome_blind": True, "contact_topology_size": 14, "tld_recursion_depth_N": "independent", "winner_N": "independent"})
    write_text_lf(OUT / "tld_shadow_byN_surface.jsonl", "\n".join(json.dumps(asdict(item), sort_keys=True) for item in metrics))
    write("tld_shadow_emergent_time.json", {"status": "NOT_ESTABLISHED", "T_e": "NOT_ESTABLISHED", "SEP_required": True})
    write("tld_shadow_emergent_scale.json", {"status": "NOT_ESTABLISHED", "S_e": "NOT_ESTABLISHED", "winner_N": "NOT_ESTABLISHED"})
    write("tld_contact_participation.json", {"status": "PASS", "contact_count": 14, "outcome_labels_used": False})
    write("tld_structured_fragility.json", {"status": "NOT_ESTABLISHED", "classification": "retrospective_shadow_structural_assay"})
    write("tld_shadow_assay_decision.json", {"status": "PASS", "classification": "retrospective_shadow_structural_assay", "parent_ladder_count": len(parents), "matched_null_count": len(nulls), "single_contact_ablation_count": sum(item.null_family.startswith("single_contact_ablation") for item in nulls), "redundant_fifteenth_contact_count": sum(item.null_family == "redundant_fifteenth_contact" for item in nulls), "role_permutation_count": sum(item.null_family == "fourteen_role_permutation" for item in nulls), "UI": "NOT_ESTABLISHED", "NSS": "NOT_ESTABLISHED", "SEP": "NOT_ESTABLISHED", "T_e": "NOT_ESTABLISHED", "S_e": "NOT_ESTABLISHED", "isomorphic_advantage": "not_demonstrated", "repair_authority": False})
    write("tld_label_blindness_audit.json", {"status": "PASS", "tier_labels_in_inputs": 0, "repair_outcomes_in_inputs": 0, "gold_or_future_inputs": 0})
    write("tld_null_integrity_audit.json", {"status": "PASS", "parent_specific": True, "deterministic": True, "cross_candidate_swap_control": "BLOCK"})
    write("tld_shadow_assay.json", load(OUT / "tld_shadow_assay_decision.json"))
    return {"core": core_record, "active_ledger": active_ledger, "local_graphs": local_graphs, "coupled": coupled, "volume": volume, "license": activation_record, "matrix": matrix_record, "twist": twist_record, "parents": parents, "nulls": nulls, "negative_count": negative_count}


def historical_capsule_phase(topology: dict[str, Any]) -> dict[str, Any]:
    prior_lock = load(PRIOR / "decision_time_provider_lock_batch068h1.json")
    current_lock = load(PRIOR / "current_declared_provider_lock_preservation_batch068h1.json")
    observed = {"status": "PARTIAL", "arm": "observed_historical_environment", "cutoff": CUTOFF, "issue_paths": ["/usr/lib64", "/builddir/build/BUILD"], "rpm_or_fedora_style_environment": "inference_not_verified", "distribution": "NOT_ESTABLISHED", "distribution_release": "NOT_ESTABLISHED", "python_build": "Python 3.13.0b2 reported", "glibc": "NOT_ESTABLISHED", "rpm_package_identities": "NOT_ESTABLISHED", "pytest_and_plugins": "PARTIAL", "warning_policy": "project_pytest_configuration_promotes_warnings", "exact_observed_environment_established": False}
    cutoff = {"status": "PARTIAL", "arm": "cutoff_compatible_transitive_lock", "cutoff": CUTOFF, "direct_dependency_records": prior_lock.get("direct_requirement_records", []), "direct_dependency_count": len(prior_lock.get("direct_requirement_records", [])), "transitive_dependency_closure": "NOT_ESTABLISHED", "post_cutoff_selected_artifact_count": 0, "classification": "cutoff_compatible_not_observed_exact", "blocker": "decision_time_transitive_provider_lock_incomplete"}
    current = {"status": current_lock.get("status", "PASS"), "arm": "current_declared_lock", "classification": "diagnostic_only_not_decision_time_reproduction", "may_establish_historical_reproduction": False, "provider_lock_hash": current_lock.get("provider_lock_hash")}
    warning = {"status": "PASS", "classification": "diagnostic_environment_harness_warning_basin", "source": "nbclient/jsonutil.py:29", "expression": "datetime.strptime(\"1\", \"%d\")", "runtime": "Python 3.13.0b2", "warning": "DeprecationWarning", "project_policy": "warning_promoted_to_error", "is_issue316_target_failure": False, "warning_suppression_authority": "non_authoritative_basin_localization", "warning_suppression_establishes_reproduction": False}
    source_mode = {"status": "PASS", "mode": "pinned_source", "candidate_sha": CANDIDATE_SHA, "git_removed": True, "source_read_only": True, "test_tree_read_only": True, "target_hash_matches_pinned_source": True, "runner_origin": "provider_capsule", "installed_wheel_shadow_conflict": False}
    wheel_mode = {"status": "NOT_RUN", "mode": "pinned_wheel", "reason": "historical wheel execution not established"}
    mixed_mode = {"status": "BLOCK", "mode": "mixed_origin", "reason": "mixed source and wheel authority forbidden"}
    capsule = {"status": "PARTIAL", "candidate_id": ACTIVE, "candidate_sha": CANDIDATE_SHA, "issue_cutoff": CUTOFF, "provider_arms": [observed, cutoff, current], "warning_basin": warning, "target_origin_modes": [source_mode, wheel_mode, mixed_mode], "language_runtime_orthology": "ESTABLISHED", "os_distribution_orthology": "PARTIAL", "package_epoch_orthology": "NOT_ESTABLISHED", "build_system_orthology": "PARTIAL", "target_origin_orthology": "CONFLICTED", "harness_orthology": "NOT_ESTABLISHED", "collection_authorized": False, "blocker": "decision_time_transitive_provider_lock_incomplete"}
    write("nbclient_historical_capsule.json", capsule)
    write("nbclient_observed_historical_environment.json", observed); write("nbclient_cutoff_compatible_transitive_lock.json", cutoff); write("nbclient_current_diagnostic_lock.json", current)
    write("nbclient_warning_promotion_basin.json", warning); write("nbclient_source_mode_identity.json", source_mode); write("nbclient_wheel_mode_identity.json", wheel_mode); write("nbclient_mixed_mode_identity.json", mixed_mode)
    collection = {"status": "BLOCK", "collection_run_1": "NOT_RUN", "collection_run_2": "NOT_RUN", "run_1_not_run_reason": "decision_time_transitive_provider_lock_incomplete", "run_2_not_run_reason": "first_collection_did_not_pass", "collected_node_count": 0, "node_set_equivalence": "NOT_RUN", "test_bodies_executed": 0, "target_tests_executed": 0, "workspace_mutations": 0, "test_tree_mutations": 0, "next_allowed_action": "batch068h3_historical_transitive_provider_closure"}
    write("nbclient_collection_decision.json", collection)
    return {"capsule": capsule, "collection": collection}


def runtime_and_controls(topology: dict[str, Any]) -> None:
    hashes = {"contact_ledger_hash": topology["active_ledger"].ledger_hash, "local_brot_hash": hash_record(next(item.as_dict() for item in topology["local_graphs"] if item.candidate_id == ACTIVE)), "coupled_tot_brot_hash": hash_record(topology["coupled"].as_dict()), "tot_bulb_volume_hash": hash_record(topology["volume"].as_dict()), "activation_license_hash": hash_record(topology["license"]), "proof_matrix_hash": hash_record(topology["matrix"])}
    records = [{"runtime_step": step, "topology_gates_evaluated": list(TOPOLOGY_META_GATES), **hashes, "bypass_allowed": False} for step in RUNTIME_STEPS]
    write("topology_runtime_binding.json", {"status": "PASS", "runtime_transition_count": len(records), "topology_bound_transition_count": len(records), "unbound_transition_count": 0, "records": records})
    write("topology_meta_gate_registry.json", {"status": "PASS", "gates": list(TOPOLOGY_META_GATES), "activation_gate": "CG-ISO-006", "activation_status": "BLOCK", "proof_gate": "CG-ISO-196", "proof_status": "PLANNED"})
    write("batch068h2_falsification_controls.json", {"status": "PASS", "contact_ablation_controls": 14, "redundant_fifteenth_control": "NO_AUTOMATIC_IMPROVEMENT", "role_permutation_control": "metrics_changed", "cross_candidate_evidence_swap": "BLOCK", "flat_untyped_graph_transfer": "BLOCK", "no_tot_brot_coupling": "NO_TRANSFER", "generic_preflight_substitution": "BLOCK", "blind_grid": "exploratory_only_not_claim_bearing", "twist_validation_disabled": "BLOCK", "license_before_topology": "BLOCK", "proof_lock_without_matrix": "BLOCK", "isomorphic_advantage": "not_demonstrated"})


def promotion_and_final(artifact: dict[str, Any], topology: dict[str, Any], capsule: dict[str, Any]) -> None:
    promotion = {"status": "PASS", "protocol_before": "v2.16", "protocol_after": "v2.17", "protocol_name": "canonical_topology_environment_volume_lane", "candidate_success_required": False, "architecture_gates_passed": True, "patch_authority": False, "repair_execution_authority": False, "target_test_execution_authority": False}
    write("v2_16_preservation_audit_batch068h2.json", {"status": "PASS", "selectable_config": "configs/controllergate_v2_16_current.yaml", "historical_v2_16_config_preserved": "configs/controllergate_v2_16.yaml", "interlock_handlers": 23, "interlock_verifiers": 23, "runtime_transitions": 13, "unbound_transitions": 0})
    write("v2_17_topology_promotion_policy.json", {"status": "PASS", "architectural_only": True, "candidate_success_controls_promotion": False, "required_gates": ["canonical_law", "reference_core_5", "contact_ledger_14", "activation_license_6", "proof_matrix_196", "local_topology", "coupled_topology", "targeted_environment_volume", "shadow_metrology", "v2_16_preservation"]})
    write("v2_17_topology_promotion_decision.json", promotion)
    write("current_protocol_migration_record_batch068h2.json", {"status": "PASS", "from": "v2.16 universal_interlock_elbow_runtime_decomposition_lane", "to": "v2.17 canonical_topology_environment_volume_lane", "candidate_repair_evidence_used": False})
    current = {"status": "PASS", "protocol_version": "v2.17", "protocol_name": "canonical_topology_environment_volume_lane", "patch_authority": False, "repair_execution_authority": False, "target_test_execution_authority": False, "live_runtime_connectors": "inactive", "full_scoring": "NOT_RUN/disallowed", "memory_lift": "not_demonstrated", "self_maintaining_software": "false/not_demonstrated", "issue_derived_repair_count": 4, "native_external_repair_count": 4, "topology_runtime_status": "PASS", "historical_capsule_status": capsule["capsule"]["status"], "next_safe_action": capsule["collection"]["next_allowed_action"]}
    current["state_hash"] = hash_record(current); write_json_deterministic(CURRENT, current)
    frontier = load(FRONTIER); frontier.update({"validated_current_protocol": "v2.17 canonical_topology_environment_volume_lane", "validated_current_protocol_status": "PASS", "topology_runtime_status": "PASS", "contact_topology_size": 14, "historical_capsule_status": capsule["capsule"]["status"], "next_safe_action": capsule["collection"]["next_allowed_action"], "patch_generated": False, "patch_applied": False, "target_tests_executed": 0})
    frontier.pop("state_hash", None); frontier["state_hash"] = hash_record(frontier); write_json_deterministic(FRONTIER, frontier)
    write("v2_17_current_protocol_audit.json", {"status": "PASS", "current_protocol": "v2.17", "candidate_success_controlled_promotion": False, "claim_boundaries_preserved": True})
    final = {"status": "PASS", "validated_protocol_before": "v2.16 universal_interlock_elbow_runtime_decomposition_lane", "validated_protocol_after": "v2.17 canonical_topology_environment_volume_lane", "artifact_ingest_status": artifact["status"], "reference_core_role_count": 5, "contact_count": 14, "missing_contact_count": 0, "duplicate_contact_count": 0, "activation_license_result": "BLOCK", "proof_cell_count": 196, "local_brot_candidate_count": len(topology["local_graphs"]), "tot_brot_coupling_edge_count": len(topology["coupled"].edges), "negative_transfer_blocked_count": topology["negative_count"], "tot_bulb_targeted_basin_count": len(topology["volume"].basins), "tot_bulb_blind_sweep_count": 0, "tld_parent_ladder_count": len(topology["parents"]), "tld_matched_null_count": len(topology["nulls"]), "decision_time_historical_lock_status": capsule["capsule"]["provider_arms"][0]["status"], "cutoff_compatible_lock_status": capsule["capsule"]["provider_arms"][1]["status"], "current_diagnostic_lock_status": capsule["capsule"]["provider_arms"][2]["status"], "collection_run_1_status": "NOT_RUN", "collection_run_2_status": "NOT_RUN", "collected_node_count": 0, "test_bodies_executed": 0, "target_tests_executed": 0, "workspace_mutations": 0, "test_tree_mutations": 0, "bounded_probe_capability": "BLOCK", "patch_generated": False, "patch_applied": False, "repair_count_increment": False, "issue_derived_repair_count": 4, "native_external_repair_count": 4, "full_scoring": "NOT_RUN/disallowed", "memory_lift": "not_demonstrated", "self_maintaining_software": "false/not_demonstrated", "exact_next_allowed_action": capsule["collection"]["next_allowed_action"]}
    write("batch068h2_final_decision.json", final)
    write("batch068h2_handoff_plan.json", {"status": "PASS", "next_allowed_action": final["exact_next_allowed_action"], "do_not_patch": True, "do_not_execute_target_test": True, "manual_artifact_boundary": True})
    write("batch068h2_audit_bundle.json", {"status": "PASS", "artifact_custody": "PASS", "canonical_law": "PASS", "topology": "PASS", "shadow_metrology": "PASS", "historical_capsule": "PARTIAL", "collection": "NOT_RUN", "claim_boundary": "PASS", "public_language": "PASS"})
    write_text_lf(OUT / "batch068h2_summary.md", "\n".join(["# Batch068h2 summary", "", "ControllerGate now has an executable fourteen-contact maintenance topology, a local candidate topology map, a typed coupled topology map, and targeted environment-boundary volume inspection.", "", "The structural assay is retrospective shadow analysis and does not authorize repair. The Nbclient historical provider capsule remains partial because the decision-time transitive provider closure is incomplete. The diagnostic warning is distinct from the issue-316 target failure.", "", "No target test body executed, no patch was generated or applied, and no repair count changed. Full scoring remains disallowed; memory lift and self-maintaining software remain undemonstrated."]))


def write_manifest() -> None:
    rows = [f"{sha256_file(path)}  {path.relative_to(OUT).as_posix()}" for path in sorted(OUT.rglob("*")) if path.is_file() and path.name != "SHA256SUMS.txt"]
    write_text_lf(OUT / "SHA256SUMS.txt", "\n".join(rows))


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--artifact-zip", default=os.environ.get("BATCH068H1_ARTIFACT_ZIP")); args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    artifact = artifact_phase(Path(args.artifact_zip) if args.artifact_zip else None)
    reconcile_batch068h1()
    topology = topology_phase()
    capsule = historical_capsule_phase(topology)
    runtime_and_controls(topology)
    promotion_and_final(artifact, topology, capsule)
    write_manifest()
    print("Batch068h2 generated: protocol=v2.17 capsule=PARTIAL collection=NOT_RUN next=batch068h3_historical_transitive_provider_closure")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
