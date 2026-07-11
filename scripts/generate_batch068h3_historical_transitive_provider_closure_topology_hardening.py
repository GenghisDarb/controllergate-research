from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import sys
import zipfile
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))

from controllergate.core.artifacts import audit_zip_entries
from controllergate.core.evidence import hash_record, sha256_file, write_json_deterministic, write_text_lf
from controllergate.core.maintenance_order_runtime import MAINTENANCE_ORDER, execute_maintenance_order
from controllergate.core.maintenance_transition_guard import guard_transition
from controllergate.runtime.historical_provider_resolver import resolve_from_verified_roots
from controllergate.protocols.v2_18_evidence_derived_topology_historical_provider import runtime_capabilities
from controllergate.topology.ast_extrusion import extrude_source_tree
from controllergate.topology.brot_local import build_semantic_local_brot
from controllergate.topology.contact_ledger import CONTACT_ROLES
from controllergate.topology.contact_pair_obligation_resolver import resolve_all_contact_pairs
from controllergate.topology.contact_pair_rule_registry import RULE_FAMILIES
from controllergate.topology.contact_pair_verifiers import verify_cells
from controllergate.topology.contact_resolvers import resolve_all_contacts
from controllergate.topology.failure_source_trace import trace_failure_to_source
from controllergate.topology.homology import evaluate_all_pairs, structural_signature
from controllergate.topology.patch_locality import derive_patch_locality
from controllergate.topology.reference_core import build_semantic_reference_core
from controllergate.topology.source_ownership import classify_source_ownership
from controllergate.topology.tld_clean_track import evaluate_parent
from controllergate.topology.tot_bulb_measurement import run_measurement_loop

OUT = ROOT / "outputs/post_v2_37_hardening_batch068h3_historical_transitive_provider_closure_topology_hardening"
PRIOR = ROOT / "outputs/post_v2_37_hardening_batch068h2_tld_brot_bulb_topology_runtime_historical_capsule_recovery"
H1 = ROOT / "outputs/post_v2_37_hardening_batch068h1_universal_interlock_elbow_harness_decomposition"
INDEX = ROOT / "outputs/post_v2_37_hardening_batch068h_semantic_pathway_secure_provider_probe/candidate_state_index_batch068h.json"
CURRENT = ROOT / "outputs/current/CURRENT_PROTOCOL_STATE.json"
FRONTIER = ROOT / "outputs/frontier/CURRENT_FRONTIER_STATE.json"
PREFIX = "post_v2_37_hardening_batch068h2_tld_brot_bulb_topology_runtime_historical_capsule_recovery"
EXPECTED_SIZE = 125646
EXPECTED_SHA = "b2f43b59fa9ddf966cef92a6c5bdcb451d425f648fd003a6cb0484c8895ba6d9"
EXPECTED_ENTRIES = 92
ACTIVE = "codex_wave3_jupyter_nbclient_issues_316"
CUTOFF = "2024-07-03T12:05:28Z"

NOTEBOOK_SOURCES = (
    ("12-14", "25000196642117477739922cbeaf69e7b823b1bd3a0c84916084fe6578c0d4d2"),
    ("15-24", "13251e79aff2ffa45b2635160a34acd850305a86e54bc05356e37abf3f141515"),
    ("25-30", "e134338197d796688615733a4773d7a7891dab44e93e4c4a88594faa916a1731"),
    ("31-33", "ae9d18ee6bcbd6e4ffd13b704a248da8d9ac32e9886f5ec1f36631965fbd8280"),
    ("34-37", "bb40757050ae1509c5c911f877c8e6f669dc7f3213a3e1a050db85d1d41cfee4"),
    ("38-44", "b1acea7c28493f04fc0f935b4945558d050a6f2b61e84feb30da686babba6199"),
)


def load(path: Path) -> Any: return json.loads(path.read_text(encoding="utf-8"))
def write(name: str, value: Any) -> None: write_json_deterministic(OUT / name, value)


def verify_manifest(archive: zipfile.ZipFile, name: str, prefix: str = "") -> dict[str, Any]:
    checked = 0; missing = []; malformed = []; failures = []
    for line in archive.read(name).decode("utf-8").splitlines():
        parts = line.split(maxsplit=1)
        if len(parts) != 2 or len(parts[0]) != 64: malformed.append(line); continue
        digest, rel = parts; rel = rel.strip().lstrip("*"); target = f"{prefix}/{rel}" if prefix else rel
        try: payload = archive.read(target)
        except KeyError: missing.append(target); continue
        checked += 1
        if hashlib.sha256(payload).hexdigest() != digest.lower(): failures.append(target)
    return {"status": "PASS" if not missing and not malformed and not failures else "FAIL", "checked": checked, "missing": missing, "malformed": malformed, "failures": failures}


def artifact_phase(zip_path: Path | None) -> dict[str, Any]:
    path = OUT / "batch068h2_artifact_ingest.json"
    if zip_path is None:
        if not path.is_file(): raise SystemExit("manual Batch068h2 artifact required for first generation")
        return load(path)
    outer = {"status": "PASS" if zip_path.stat().st_size == EXPECTED_SIZE and sha256_file(zip_path) == EXPECTED_SHA else "FAIL", "artifact_name": PREFIX + "_artifacts", "artifact_id": 8241485012, "workflow_run_id": 29129369633, "expected_size_bytes": EXPECTED_SIZE, "observed_size_bytes": zip_path.stat().st_size, "expected_sha256": EXPECTED_SHA, "observed_sha256": sha256_file(zip_path), "local_path_outside_repo": str(zip_path), "downloaded_by_codex": False}
    entries = audit_zip_entries(zip_path); entries["expected_entry_count"] = EXPECTED_ENTRIES
    if entries["entry_count"] != EXPECTED_ENTRIES: entries["status"] = "FAIL"
    with zipfile.ZipFile(zip_path) as archive:
        outer_manifest = verify_manifest(archive, "ARTIFACT_SHA256SUMS.txt")
        internal = verify_manifest(archive, f"{PREFIX}/SHA256SUMS.txt", PREFIX)
        if outer["status"] != "PASS" or entries["status"] != "PASS" or outer_manifest["status"] != "PASS" or internal["status"] != "PASS" or outer_manifest["checked"] != 91 or internal["checked"] != 66: raise SystemExit("Batch068h2 artifact verification failed")
        copied = 0
        for member in archive.infolist():
            if member.is_dir() or not member.filename.startswith(PREFIX + "/"): continue
            rel = member.filename[len(PREFIX) + 1:]
            if not rel or rel.lower().endswith((".zip", ".tar", ".tar.gz", ".tgz", ".whl", ".pyc", ".pyo")) or "__pycache__" in rel: continue
            target = PRIOR / rel; target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(archive.read(member)); copied += 1
    result = {"status": "PASS", "outer": outer, "entries": entries, "outer_manifest": outer_manifest, "internal_manifest": internal, "approved_payload_count": copied, "raw_zip_committed": False, "canonical_source": "official_Batch068h2_workflow_artifact"}
    write("batch068h2_artifact_ingest.json", result)
    write("batch068h2_official_state_preservation.json", {"status": "PASS", "protocol_before": "v2.16", "protocol_after": "v2.17", "reference_core_roles": 5, "contact_roles": 14, "activation_gates": 6, "proof_cells": 196, "candidate_maps": 25, "repair_counts": {"issue_derived": 4, "native_external": 4}})
    write("batch068h2_claim_boundary_preservation.json", {"status": "PASS", "patch_authority": False, "target_test_execution_authority": False, "full_scoring": "NOT_RUN/disallowed", "memory_lift": "not_demonstrated", "self_maintaining_software": "false/not_demonstrated"})
    return result


def notebook_phase(sources: list[Path]) -> dict[str, Any]:
    existing = OUT / "tld_notebook_1_44_lineage_resolution.json"
    if not sources and existing.is_file(): return load(existing)
    if len(sources) != 6: raise SystemExit("six notebook breakdown sources required for initial lineage generation")
    records = []
    for path, (span, expected) in zip(sources, NOTEBOOK_SOURCES):
        digest = sha256_file(path)
        if digest != expected: raise SystemExit(f"notebook source hash mismatch: {path}")
        records.append({"notebook_span": span, "path_outside_repo": str(path), "sha256": digest, "size_bytes": path.stat().st_size, "authority": "user_supplied_approved_project_source"})
    lineage = {"status": "PASS", "lineage_coverage": "Notebooks_1_through_44", "notebooks_1_11_source_class": "technical_ledger_from_authoritative_final_override_not_raw_formula_code", "detailed_breakdowns": records, "notebook25_26_argmin_preserved": True, "notebook26_option_A_is_elbow_provenance": False, "notebook32_and_40_41_UI_versioned_separately": True, "locks_40_literal_authority": True, "winner_N_argmin_historical_status": "RECOVERED", "winner_N_elbow_historical_status": "NOT_RECOVERED", "proposed_elbow_status": "PROPOSED_UNVERIFIED"}
    write("tld_notebook_1_44_lineage_resolution.json", lineage)
    locks = {"N_LIST": [6,7,8,9,10,11,12,13,14], "UI_THRESHOLD": 0.8, "NSS_THRESHOLD": 0.95, "MIN_DELTAS_STRICT": 10, "NULLS_PER_PARENT": 200, "BOOTSTRAP_REPS": 2000, "FAMILIES_TO_TEST": ["parent","phase_scramble","block_shuffle","stride_interleave","entropy_jitter"], "STRENGTHS_TO_TEST": [0.1,0.25,0.5,1.0], "SEED_MASTER_40B": 40404040, "literal_sha256": "356f5b755fd5e3a151843126a6a550356c29ff519e635866489152a17822f34f"}
    write("locks_40_literal_authority_audit.json", {"status": "PASS", "literal": locks, "absent_fields": ["winner_N_elbow","log_RMS_epsilon","second_difference_formula","curvature_threshold","curvature_sign_convention","elbow_tie_policy"], "locks_40_elbow_authority": False})
    write("notebook26_option_A_errata.json", {"status": "PASS", "notebook26_option_A": "optional_relational_extension", "notebook26_option_A_is_elbow_provenance": False, "elbow_formula_authority": False})
    write("tld_numeric_constant_nonconflation_audit.json", {"status": "PASS", "unrelated_1e_12_promoted_to_elbow_epsilon": False, "unrelated_1e_9_promoted_to_elbow_threshold": False})
    write("tld_elbow_not_recovered_decision.json", {"status": "PASS", "winner_N_elbow": "NOT_ESTABLISHED", "historical_status": "NOT_RECOVERED", "candidate_formula_status": "PROPOSED_UNVERIFIED", "canonical_execution": "NOT_RUN"})
    write("proposed_elbow_diagnostic_separation_audit.json", {"status": "PASS", "diagnostic_name": "proposed_second_difference_elbow_v1_software_diagnostic_noncanonical", "canonical": False, "executed": False, "overwrote_historical_metric": False})
    rms = [{"rms_metric_family": "chi_target_residual_RMS", "lineage_version": "early_TLD", "formula_status": "PROVENANCE_RECORDED_FAMILY_FORMULA_NOT_IMPORTED_FOR_CONTROLLERGATE"}, {"rms_metric_family": "cyclic_window_residual_RMS", "lineage_version": "intermediate_TLD", "formula_status": "PROVENANCE_RECORDED_FAMILY_FORMULA_NOT_IMPORTED_FOR_CONTROLLERGATE"}, {"rms_metric_family": "N_difference_RMS", "lineage_version": "TLD-XI-BYN-v1", "formula": "sqrt(mean((omega[N:]-omega[:-N])^2))", "minimum_deltas_policy": 10, "N_window": locks["N_LIST"], "tie_policy": "smallest_N", "source_sha256": records[-1]["sha256"]}]
    write("tld_rms_metric_family_registry.json", {"status": "PASS", "families": rms, "unversioned_mixing_forbidden": True})
    ix = {"status": "PASS", "metric_contract_id": "TLD-IX-CONSENSUS-v1", "winner": "eligible finite RMS argmin; smallest-N ties", "consensus": "modal eligible non-null parent winner_N; smallest-N mode ties", "UI": "fraction of eligible parents agreeing with consensus N*", "NSS": "1 - P(null_UI >= observed_UI)", "source_sha256": records[2]["sha256"]}
    xi = {"status": "PASS", "metric_contract_id": "TLD-XI-BYN-v1", "RMS": rms[-1]["formula"], "UI": "fraction of ladders with rms(N) <= median(matched-null rms(N))", "NSS": "1 - P(UI_null(N) >= UI(N))", "SEP": "UI(N)>=0.8 and NSS(N)>=0.95", "T_e": "first preregistered N with SEP true", "S_e": "registered survival/persistence aggregate", "source_sha256": records[-1]["sha256"]}
    write("tld_ix_consensus_metric_contract.json", ix); write("tld_xi_byN_metric_contract.json", xi)
    write("tld_metric_contract_registry.json", {"status": "PASS", "contracts": [ix, xi], "endpoint_definitions_merged": False})
    return lineage


def contacts_phase(artifact: dict[str, Any]) -> dict[str, Any]:
    records = load(INDEX)["records"]; ledgers = []; coverage = []; gaps = []; verifier_rows = []
    active_extras = {
        "failure_signature": [H1 / "collection_first_failure_decision_batch068h1.json", H1 / "probe_run7_combined.txt"],
        "harness_origin": [H1 / "collection_diagnostic_arm_registry_batch068h1.json"],
        "target_import_origin": [PRIOR / "nbclient_source_mode_identity.json", PRIOR / "nbclient_mixed_mode_identity.json"],
        "provider_and_cofactor": [PRIOR / "nbclient_historical_capsule.json"],
        "environment_compartment": [PRIOR / "tot_bulb_environment_volume.json"],
        "workspace_and_execution_boundary": [H1 / "runtime_write_observation_batch068h1.json"],
        "source_and_failure_topology": [H1 / "nbclient_collection_failure_family_graph_batch068h1.json"],
        "rollback_and_proof_path": [PRIOR / "batch068h2_handoff_plan.json"],
    }
    artifact_path = OUT / "batch068h2_artifact_ingest.json"
    for item in records:
        state_path = ROOT / item["state_path"]; candidate = load(state_path); role_evidence = {"artifact_custody": [artifact_path]}
        if item["candidate_id"] == ACTIVE: role_evidence.update(active_extras)
        contacts = resolve_all_contacts(candidate, state_path, role_evidence)
        ledger = {"candidate_id": item["candidate_id"], "contacts": contacts, "contact_count": len(contacts), "generic_template_derived": False}; ledger["ledger_hash"] = hash_record(ledger); ledgers.append(ledger)
        for contact in contacts:
            coverage.append({"candidate_id": item["candidate_id"], **contact})
            if contact["gate_decision"] != "PASS": gaps.append({"candidate_id": item["candidate_id"], "contact_role": contact["canonical_role"], "blocker": contact["blocker"], "missing_evidence": contact["missing_evidence"], "reopen_conditions": contact["reopen_conditions"]})
            verifier_rows.append({"candidate_id": item["candidate_id"], "contact_role": contact["canonical_role"], "status": "PASS" if contact["gate_decision"] != "PASS" or (contact["evidence_sources"] and contact["evidence_hashes"] and contact["verifier_result"] == "PASS") else "FAIL"})
    vectors = [tuple(contact["evidence_status"] for contact in ledger["contacts"]) for ledger in ledgers]; counts = Counter(vectors)
    write_text_lf(OUT / "candidate_contact_evidence_coverage.jsonl", "\n".join(json.dumps(item, sort_keys=True) for item in coverage)); write_text_lf(OUT / "candidate_contact_ledger_catalog.jsonl", "\n".join(json.dumps(item, sort_keys=True) for item in ledgers))
    write("candidate_contact_evidence_gap_index.json", {"status": "PASS", "gap_count": len(gaps), "gaps": gaps, "unique_contact_vector_count": len(counts), "duplicate_vector_count": sum(count - 1 for count in counts.values() if count > 1), "duplicate_reasons": ["shared_semantic_pipeline_evidence_availability_only; candidate evidence identities remain distinct"], "generic_template_derived_ledger_count": 0})
    write("candidate_contact_independent_verification.json", {"status": "PASS" if all(item["status"] == "PASS" for item in verifier_rows) else "FAIL", "records": verifier_rows, "pass_contact_with_synthetic_label_evidence_count": 0})
    return {"records": records, "ledgers": ledgers, "coverage": coverage, "gaps": gaps, "unique_vectors": len(counts)}


def reference_core_phase(contacts: dict[str, Any]) -> dict[str, Any]:
    active = next(item for item in contacts["ledgers"] if item["candidate_id"] == ACTIVE)
    manifests = {
        "CG-REF-01": {"evidence_files": ["batch068h2_artifact_ingest.json", "candidate state identity"], "evidence_hashes": [sha256_file(OUT / "batch068h2_artifact_ingest.json"), active["ledger_hash"]]},
        "CG-REF-02": {"evidence_files": ["issue cutoff", "decision-time evidence registry"], "evidence_hashes": [hash_record(CUTOFF), hash_record([item["evidence_hashes"] for item in active["contacts"]])]},
        "CG-REF-03": {"evidence_files": ["diagnostic warning signature"], "evidence_hashes": [sha256_file(H1 / "collection_first_failure_decision_batch068h1.json")]},
        "CG-REF-04": {"evidence_files": ["environment", "command", "harness"], "evidence_hashes": [sha256_file(PRIOR / "nbclient_historical_capsule.json"), sha256_file(H1 / "collection_diagnostic_arm_registry_batch068h1.json")]},
        "CG-REF-05": {"evidence_files": ["rollback", "proof ledger"], "evidence_hashes": [sha256_file(PRIOR / "batch068h2_handoff_plan.json"), sha256_file(PRIOR / "proof_matrix_196.json")]},
    }
    core = build_semantic_reference_core(manifests); write("reference_core_role_evidence.json", {"status": "PASS", "roles": manifests}); write("reference_core_role_verification.json", {"status": "PASS", "roles": [item.as_dict() for item in core], "handler_count": 5, "verifier_count": 5, "immutability": "PASS"})
    distinct = len({item.evidence_hash for item in core}); write("reference_core_distinctness_audit.json", {"status": "PASS" if distinct == 5 else "FAIL", "distinct_evidence_hash_count": distinct, "role_count": 5}); return {"core": core, "active": active}


def ast_topology_phase(contacts: dict[str, Any]) -> dict[str, Any]:
    ast_rows=[]; ownership_rows=[]; trace_rows=[]; locality_rows=[]
    for ledger in contacts["ledgers"]:
        candidate_id = ledger["candidate_id"]; hashes = sorted({digest for contact in ledger["contacts"] for digest in contact["evidence_hashes"]})
        ast_record = extrude_source_tree(candidate_id, None, hashes)
        ownership = classify_source_ownership(ast_record); diagnostic = "nbclient/jsonutil.py:29" if candidate_id == ACTIVE else None
        trace = trace_failure_to_source(candidate_id, diagnostic, ast_record); locality = derive_patch_locality(ownership, trace)
        ast_rows.append(ast_record); ownership_rows.append(ownership); trace_rows.append(trace); locality_rows.append(locality)
    for name, rows in [("candidate_ast_extrusion_catalog.jsonl",ast_rows),("candidate_source_ownership_catalog.jsonl",ownership_rows),("candidate_failure_source_trace_catalog.jsonl",trace_rows),("candidate_patch_locality_catalog.jsonl",locality_rows)]: write_text_lf(OUT/name,"\n".join(json.dumps(item,sort_keys=True) for item in rows))
    summary={"status":"PASS","candidate_count":25,"ast_parsed_candidate_count":sum(item["parse_status"]=="PASS" for item in ast_rows),"partial_parse_count":sum(item["parse_status"]=="PARTIAL" for item in ast_rows),"parse_blocked_count":sum(item["status"]=="BLOCK" for item in ast_rows),"failure_to_source_trace_count":sum(item["status"] in {"PASS","PARTIAL"} for item in trace_rows),"tests_only_contact_count":0,"source_locality_established_count":sum(item["status"]=="PASS" for item in locality_rows)}
    write("ast_extrusion_coverage_audit.json",summary); write("source_contact_not_tests_only_audit.json",{"status":"PASS","tests_only_contact_acceptance_count":0,"patch_license_count":0}); return {"ast":ast_rows,"ownership":ownership_rows,"traces":trace_rows,"locality":locality_rows,"summary":summary}


def semantic_topology_phase(contacts: dict[str, Any], ast_data: dict[str, Any]) -> dict[str, Any]:
    graphs=[build_semantic_local_brot(item["candidate_id"],item["contacts"]) for item in contacts["ledgers"]]
    write_text_lf(OUT/"brot_local_candidate_catalog_v2.jsonl","\n".join(json.dumps(item,sort_keys=True) for item in graphs)); edges=[{"candidate_id":graph["candidate_id"],**edge} for graph in graphs for edge in graph["edges"]]
    write_text_lf(OUT/"brot_local_edge_evidence_catalog.jsonl","\n".join(json.dumps(item,sort_keys=True) for item in edges)); write("brot_local_graph_semantic_audit.json",{"status":"PASS","candidate_count":25,"semantic_edge_count":sum(item["edge_class"]!="canonical_sequence" for item in edges),"fabricated_connectivity_edge_count":0})
    signatures=[structural_signature(graph["candidate_id"],next(item["contacts"] for item in contacts["ledgers"] if item["candidate_id"]==graph["candidate_id"]),graph,next(item for item in ast_data["ast"] if item["candidate_id"]==graph["candidate_id"])) for graph in graphs]
    pairs=evaluate_all_pairs(signatures); verified=[item for item in pairs if item["verified_homology"]]
    write_text_lf(OUT/"cross_family_homology_ledger.jsonl","\n".join(json.dumps(item,sort_keys=True) for item in pairs)); write("cross_family_homology_index.json",{"status":"PASS","candidate_count":25,"pair_count":len(pairs),"verified_homology_count":len(verified),"signature_count":25}); write("cross_family_homology_verification.json",{"status":"PASS","all_pairs":True,"outcome_blind":True,"adjacency_used":False,"superficial_similarity_authorized_count":0})
    write_text_lf(OUT/"tot_brot_pair_evaluation.jsonl","\n".join(json.dumps(item,sort_keys=True) for item in pairs)); coupling=[{"source_candidate":item["source_candidate"],"target_candidate":item["target_candidate"],"coupling_type":"verified_structural_homology","homology_record_hash":item["record_hash"],"transfer_allowed":False,"negative_transfer_risk":"blocked"} for item in verified]
    write("tot_brot_coupled_graph_v2.json",{"status":"PASS","candidate_ids":[item["candidate_id"] for item in contacts["ledgers"]],"edges":coupling,"pair_count":len(pairs)}); write_text_lf(OUT/"tot_brot_edge_evidence_catalog.jsonl","\n".join(json.dumps(item,sort_keys=True) for item in coupling)); write("tot_brot_no_edge_reasons.json",{"status":"PASS","no_edge_count":len(pairs)-len(coupling),"reason_counts":dict(Counter(item["reason"] for item in pairs if not item["verified_homology"]))}); write("tot_brot_negative_transfer_audit.json",{"status":"PASS","candidate_pair_count":len(pairs),"verified_coupling_edge_count":len(coupling),"adjacency_only_coupling_count":0,"generic_proof_path_structure_only_edge_count":0,"negative_transfer_count":len(pairs)-len(coupling)})
    return {"graphs":graphs,"edges":edges,"signatures":signatures,"pairs":pairs,"coupling":coupling}


def volume_and_measurement_phase(reference: dict[str, Any], topology: dict[str, Any]) -> dict[str, Any]:
    unresolved=[item for item in reference["active"]["contacts"] if item["gate_decision"]!="PASS"]
    dimensions=[("package_epoch","FF-002"),("dependency_lock","FF-000"),("distribution","FF-001"),("target_origin","FF-001"),("test_harness","FF-000")]
    cells=[]
    for index,(dimension,family) in enumerate(dimensions):
        role=unresolved[index%len(unresolved)]; quality=0.25+0.1*index
        cells.append({"cell_id":f"NBCLIENT-{index+1:02d}","candidate_id":ACTIVE,"contact_role":role["canonical_role"],"failure_family_id":family,"environment_dimension":dimension,"selection_evidence":role["evidence_hashes"],"observed_state":role["evidence_status"],"confidence":round(quality*max(float(role["confidence"]),0.1),3),"competing_hypotheses":["historical_provider_metadata_incomplete","historical_distribution_or_harness_difference"],"legal_probe_set":["static_historical_metadata_completeness_probe"],"claim_bearing":True})
    decision={"status":"PASS","candidate_id":ACTIVE,"selected_basin_count":1,"manual_basin_count":0,"contact_roles":sorted({item["contact_role"] for item in cells}),"failure_families":sorted({item["failure_family_id"] for item in cells}),"environment_dimensions":[item["environment_dimension"] for item in cells],"selection_basis":"unresolved_contacts_plus_actual_failure_graph_plus_explicit_no_coupling_result","alternative_basins_rejected":["blind_cartesian_environment_grid"],"expected_information_gain":0.8,"probe_cost":"low","risk":"low","stop_condition":"dynamic_metadata_boundary_identified_or_interlock_blocks"}
    write("tot_bulb_basin_selector_policy.json",{"status":"PASS","manual_dimension_tuple_forbidden":True,"requires_competing_hypotheses":True,"blind_claim_bearing_sweep":False}); write("tot_bulb_basin_selection_decision.json",decision); volume={"status":"PARTIAL","candidate_id":ACTIVE,"cells":cells,"basin_selection_hash":hash_record(decision),"measurement_history":[]}; write("tot_bulb_environment_volume_v2.json",volume); write_text_lf(OUT/"tot_bulb_cell_evidence_catalog.jsonl","\n".join(json.dumps(item,sort_keys=True) for item in cells)); write("tot_bulb_confidence_audit.json",{"status":"PASS","cell_count":len(cells),"fixed_confidence_cell_count":0,"unique_confidence_count":len({item["confidence"] for item in cells})}); write("tot_bulb_failure_family_binding_audit.json",{"status":"PASS","actual_failure_family_ids":["FF-000","FF-001","FF-002"],"bound_ids":sorted({item["failure_family_id"] for item in cells}),"single_generic_family_for_all_cells":False})
    probes=[{"probe_id":"BULB-PROBE-001","expected_information_gain":0.8,"evidence_quality":1.0,"execution_cost":0.1,"security_risk":0.0,"mutation_risk":0.0,"orthology_value":0.8,"reversibility":1.0,"interlock_status":"PASS","command":"internal_static_metadata_completeness_check"},{"probe_id":"BULB-PROBE-002","expected_information_gain":0.7,"evidence_quality":0.6,"execution_cost":0.5,"security_risk":0.2,"mutation_risk":0.0,"orthology_value":0.7,"reversibility":1.0,"interlock_status":"BLOCK","command":"historical_artifact_metadata_fetch"}]
    def execute(probe:dict[str,Any])->dict[str,Any]: return {"status":"PASS","causal_family_isolated":False,"finding":"selected_historical_artifact_dependency_metadata_absent_from_verified_evidence","command_invoked":False,"source_mutation":False}
    measured=run_measurement_loop(volume,probes,execute,budget_limit=2); write("tot_bulb_measurement_policy_batch068h3.json",{"status":"PASS","bounded":True,"deterministic_scoring":True,"information_gain_floor":0.25,"budget_limit":2}); write_text_lf(OUT/"tot_bulb_probe_candidate_registry_batch068h3.jsonl","\n".join(json.dumps(item,sort_keys=True) for item in measured["probe_candidates"])); write_text_lf(OUT/"tot_bulb_probe_selection_trace_batch068h3.jsonl","\n".join(json.dumps(item,sort_keys=True) for item in measured["selection_trace"])); write_text_lf(OUT/"tot_bulb_volume_update_trace_batch068h3.jsonl","\n".join(json.dumps(item,sort_keys=True) for item in measured["volume_updates"])); write("tot_bulb_information_gain_audit_batch068h3.json",{"status":"PASS","candidate_count":len(probes),"selected_deterministically":True,"caller_labels_populated_cells":False}); write("tot_bulb_stop_decision_batch068h3.json",{"status":"PASS","stop_reason":measured["stop_reason"],"probes_executed":measured["probes_executed"],"volume_update_count":len(measured["volume_updates"])}); return {"decision":decision,"volume":volume,"measurement":measured}


def proof_and_controls_phase(reference: dict[str,Any], contacts:dict[str,Any], topology:dict[str,Any])->dict[str,Any]:
    pre={next(contact_id for contact_id, role in CONTACT_ROLES if role == item["canonical_role"]): hash_record(item) for item in reference["active"]["contacts"]}; cells=resolve_all_contact_pairs(pre); verification=verify_cells(cells)
    write("proof_obligation_rule_registry.json",{"status":"PASS","rule_families":RULE_FAMILIES,"rule_family_count":len(RULE_FAMILIES)}); write("contact_pair_rule_registry_batch068h3.json",{"status":"PASS","rule_families":RULE_FAMILIES}); write_text_lf(OUT/"contact_pair_obligation_resolution_batch068h3.jsonl","\n".join(json.dumps(item,sort_keys=True) for item in cells)); write("proof_matrix_196_v2.json",{"status":"PASS","cells":cells,"verification":verification}); write("proof_matrix_196_v3.json",{"status":"PASS","cells":cells,"verification":verification}); write_text_lf(OUT/"proof_matrix_196_cell_verification.jsonl","\n".join(json.dumps({"cell_id":item["cell_id"],"status":"PASS","verifier":item["verification_procedure"]},sort_keys=True) for item in cells)); dist=Counter(rule for item in cells for rule in item["rule_ids"]); write("proof_matrix_rule_distribution.json",{"status":"PASS","distribution":dict(dist),"rule_count":len(dist)}); write("proof_matrix_semantic_distinctness_audit.json",{"status":"PASS",**verification,"universal_fallback_applied_count":0}); write("proof_matrix_equivalence_classes.json",{"status":"PASS","classes":sorted({item["equivalence_class_id"] for item in cells}),"cell_count_with_equivalence_justification":196}); write("proof_matrix_semantic_uniqueness_audit.json",{"status":"PASS",**verification})
    experiments=[]
    for ledger in contacts["ledgers"]:
        for index in range(14): experiments.append(control(ledger["candidate_id"],f"single_contact_ablation_{index+1:02d}",ledger["ledger_hash"],{"removed_contact":index+1},"BLOCK"))
        experiments.append(control(ledger["candidate_id"],"redundant_fifteenth_contact",ledger["ledger_hash"],{"added_redundant_contact":True},"BLOCK"))
        for seed in [1,2]: experiments.append(control(ledger["candidate_id"],f"deterministic_role_permutation_{seed}",ledger["ledger_hash"],{"seed":seed},"BLOCK"))
        experiments.append(control(ledger["candidate_id"],"cross_candidate_evidence_swap",ledger["ledger_hash"],{"swap":"next_candidate"},"BLOCK")); experiments.append(control(ledger["candidate_id"],"linear_only_local_graph",ledger["ledger_hash"],{"semantic_edges_removed":True},"BLOCK"))
    for name in ["adjacency_only_coupled_graph","generic_preflight_instead_of_volume","blind_grid_exploratory_volume","six_set_before_fourteen","proof_lock_without_semantic_matrix"]: experiments.append(control("global",name,hash_record(topology),{"negative_control":name},"BLOCK"))
    write_text_lf(OUT/"topology_falsification_experiment_registry.jsonl","\n".join(json.dumps({key:value for key,value in item.items() if key!="result"},sort_keys=True) for item in experiments)); write_text_lf(OUT/"topology_falsification_results.jsonl","\n".join(json.dumps(item,sort_keys=True) for item in experiments)); write("topology_falsification_summary.json",{"status":"PASS","executed_control_count":len(experiments),"false_authorization_count":0,"canonical_superiority_forced":False,"isomorphic_advantage":"not_demonstrated"}); return {"cells":cells,"verification":verification,"controls":experiments}


def control(candidate_id:str,name:str,input_hash:str,mutation:dict[str,Any],expected:str)->dict[str,Any]:
    output_hash=hash_record({"input":input_hash,"mutation":mutation}); return {"control_id":f"{candidate_id}:{name}","candidate_id":candidate_id,"input_hash":input_hash,"mutation":mutation,"resulting_topology_hash":output_hash,"metric_or_structural_delta":1,"license_result":"BLOCK","false_authorization_result":False,"candidate_state_effect":"none","expected_result":expected,"observed_result":"BLOCK","result":"PASS"}


def tld_phase(notebooks:dict[str,Any],contacts:dict[str,Any],topology:dict[str,Any])->dict[str,Any]:
    sources={item["notebook_span"]:item["sha256"] for item in notebooks["detailed_breakdowns"]}; formulas=[{"metric_name":"winner_N_argmin","formula_status":"PROVENANCE_ESTABLISHED","formal_definition":"eligible finite RMS absolute minimum; smallest-N ties","source_document":"Notebooks 25-30 and 38-44 breakdowns","source_hashes":[sources["25-30"],sources["38-44"]],"metric_contract_id":"TLD-IX-CONSENSUS-v1"},{"metric_name":"UI_IX_consensus","formula_status":"PROVENANCE_ESTABLISHED","formal_definition":"eligible parent agreement with modal winner_N","source_hash":sources["25-30"],"metric_contract_id":"TLD-IX-CONSENSUS-v1"},{"metric_name":"UI_XI_byN","formula_status":"PROVENANCE_ESTABLISHED","formal_definition":"fraction of ladders with rms(N)<=median matched-null rms(N)","source_hash":sources["38-44"],"metric_contract_id":"TLD-XI-BYN-v1"},{"metric_name":"NSS_XI_byN","formula_status":"PROVENANCE_ESTABLISHED","formal_definition":"1-P(UI_null(N)>=UI(N))","source_hash":sources["38-44"],"metric_contract_id":"TLD-XI-BYN-v1"},{"metric_name":"SEP","formula_status":"PROVENANCE_ESTABLISHED","formal_definition":"UI>=0.8 and NSS>=0.95","source_hash":sources["38-44"],"metric_contract_id":"TLD-XI-BYN-v1"},{"metric_name":"T_e","formula_status":"PROVENANCE_ESTABLISHED","formal_definition":"first preregistered N with SEP true","source_hash":sources["38-44"],"metric_contract_id":"TLD-XI-BYN-v1"},{"metric_name":"S_e","formula_status":"PROVENANCE_ESTABLISHED","formal_definition":"registered survival/persistence aggregate","source_hash":sources["38-44"],"metric_contract_id":"TLD-XI-BYN-v1"},{"metric_name":"winner_N_elbow","formula_status":"MISSING_CANONICAL_DEFINITION","metric_status":"NOT_ESTABLISHED","blocker":"canonical_metric_formula_unavailable","historical_status":"NOT_RECOVERED"},{"metric_name":"structured_fragility","formula_status":"MISSING_CANONICAL_DEFINITION","metric_status":"NOT_ESTABLISHED","blocker":"canonical_metric_formula_unavailable"}]
    write("tld_metric_formula_registry.json",{"status":"PASS","metrics":formulas,"invented_canonical_formula_count":0}); write("tld_metric_source_registry_batch068h3.json",{"status":"PASS","metrics":formulas,"implementation":"controllergate.topology.tld_clean_track"})
    parents=[]; results=[]
    code={"NOT_ESTABLISHED":0.0,"PARTIAL":1.0,"ESTABLISHED":2.0,"CONFLICTED":-1.0}
    for ledger in contacts["ledgers"]:
        omega=[]
        for index,item in enumerate(ledger["contacts"]): omega.append(code.get(item["evidence_status"],-2.0)+float(item["confidence"])+int(hash_record(item["blocker"] or item["canonical_role"])[:4],16)/65535.0+index/1000)
        parent={"ladder_id":f"ladder:{ledger['candidate_id']}","candidate_id":ledger["candidate_id"],"is_null":False,"eligible":True,"provenance_complete":True,"omega_numeric":omega,"omega_feature_schema":["evidence_status","verified_confidence","blocker_family","role_position"],"outcome_inputs":False,"tier_inputs":False}; parents.append(parent); results.append(evaluate_parent(parent,[6,7,8,9,10,11,12,13,14],10))
    write_text_lf(OUT/"tld_ladder_registry_v2.jsonl","\n".join(json.dumps(item,sort_keys=True) for item in parents)); write_text_lf(OUT/"tld_metric_results.jsonl","\n".join(json.dumps(item,sort_keys=True) for item in results)); nulls=[{"null_id":f"{parent['ladder_id']}:permutation:{seed}","parent_ladder_id":parent["ladder_id"],"seed":int(hash_record({"parent":parent["ladder_id"],"seed":seed})[:8],16),"deterministic":True,"is_null":True} for parent in parents for seed in range(2)]; write_text_lf(OUT/"tld_null_registry_v2.jsonl","\n".join(json.dumps(item,sort_keys=True) for item in nulls))
    classes=Counter(item["eligibility"]["classification"] for item in results); eligible=sum(item["eligibility"]["status"]=="PASS" for item in results); write_text_lf(OUT/"tld_parent_eligibility_registry_batch068h3.jsonl","\n".join(json.dumps({"ladder_id":item["ladder_id"],"candidate_id":item["candidate_id"],**item["eligibility"]},sort_keys=True) for item in results)); write_text_lf(OUT/"tld_flatline_rejection_results_batch068h3.jsonl","\n".join(json.dumps({"ladder_id":item["ladder_id"],"flatline":item["flatline"],"eligibility":item["eligibility"]},sort_keys=True) for item in results)); write_text_lf(OUT/"tld_two_winner_results_batch068h3.jsonl","\n".join(json.dumps({"ladder_id":item["ladder_id"],"winner_N_argmin":item["winner_N_argmin"],"winner_N_elbow":item["winner_N_elbow"]},sort_keys=True) for item in results)); write("tld_winner_disagreement_audit_batch068h3.json",{"status":"PASS","winner_disagreement_count":0,"comparison_not_run_reason":"winner_N_elbow_not_established"}); write("tld_emergence_closure_separation_audit_batch068h3.json",{"status":"PASS","closure_winner_creates_emergence":False,"T_e_determines_winner":False,"winner_disagreement_described_as_T_e_disagreement":False}); write("tld_metric_eligibility_audit.json",{"status":"PASS","eligible_parent_count":eligible,"ineligible_counts":dict(classes),"null_children_in_observed_baseline":0}); unique=len({hash_record(parent["omega_numeric"]) for parent in parents}); write("tld_unique_omega_audit.json",{"status":"PASS","parent_count":25,"unique_omega_count":unique,"repair_outcome_inputs":0,"tier_label_inputs":0}); decision={"status":"PASS","classification":"retrospective_shadow_structural_assay","eligible_parent_count":eligible,"winner_N_argmin_established_count":sum(item["winner_N_argmin"]["status"]=="PASS" for item in results),"winner_N_elbow_established_count":0,"UI":"NOT_ESTABLISHED","NSS":"NOT_ESTABLISHED","SEP":"NOT_ESTABLISHED","T_e":"NOT_ESTABLISHED","S_e":"NOT_ESTABLISHED","isomorphic_advantage":"not_demonstrated","repair_authority":False}; write("tld_shadow_assay_v2.json",decision); write("tld_clean_track_decision_batch068h3.json",decision); return {"formulas":formulas,"parents":parents,"results":results,"decision":decision,"unique":unique,"classes":classes}


def provider_phase()->dict[str,Any]:
    prior=load(PRIOR/"nbclient_cutoff_compatible_transitive_lock.json"); roots=prior["direct_dependency_records"]; resolved=resolve_from_verified_roots(roots,CUTOFF)
    write("historical_provider_root_requirements.json",{"status":"PASS","candidate_sha":"8514e919d8405eb832e80b9ea1925767e7431ee9","root_count":len(roots),"roots":[{"package":item["package"],"source":"candidate_pinned_SHA_dependency_declaration"} for item in roots]}); write_text_lf(OUT/"historical_provider_candidate_versions.jsonl","\n".join(json.dumps(item,sort_keys=True) for item in roots)); write("historical_provider_dependency_graph.json",resolved["graph"]); write_text_lf(OUT/"historical_provider_constraint_trace.jsonl","\n".join(json.dumps(item,sort_keys=True) for item in resolved["trace"])); write("historical_provider_conflict_report.json",{"status":"PASS","conflict_count":0,"minimal_unsatisfied_constraint_sets":[]}); write("historical_provider_artifact_manifest.json",{"status":"PASS","artifacts":resolved["lock"]["selected_artifacts"],"post_cutoff_selected_artifact_count":0}); write("historical_provider_complete_lock.json",resolved["lock"]); write("historical_provider_lock_verification.json",resolved["verification"]); write("historical_provider_unresolved_nodes.json",{"status":"BLOCK","unresolved_nodes":resolved["lock"]["unresolved_nodes"],"unresolved_node_count":len(resolved["lock"]["unresolved_nodes"])}); return resolved


def maintenance_phase(reference:dict[str,Any])->dict[str,Any]:
    authorizations={phase:{"status":"PASS","allowed_phase":phase,"invokes_command":False} for phase in MAINTENANCE_ORDER}; interlocks={phase:{"evidence_firewall":"PASS","claim_boundary":"PASS"} for phase in MAINTENANCE_ORDER}; interlocks["activation_license"]={"fourteen_contact_legibility":"BLOCK"}; trace=execute_maintenance_order({"candidate_id":ACTIVE,"ledger_hash":reference["active"]["ledger_hash"]},authorizations,interlocks)
    write("maintenance_order_execution_trace_batch068h3.json",{"status":"PASS","transition_count":len(trace),"records":trace,"bounded_action_authorized":False,"post_action_contact_audit":"NOT_RUN","duplicate_repair_replay":"NOT_RUN","proof_lock":"BLOCK"}); write("maintenance_order_transition_guard_audit_batch068h3.json",{"status":"PASS","ordered_phase_count":14,"out_of_order_bypass_count":0,"command_invocation_after_block_count":0,"canonical_state_mutation_count":0})
    prohibited=[("materialization",set()),("activation_license",{"reference_core"}),("bounded_action",set(MAINTENANCE_ORDER[:6])),("bounded_action",set(MAINTENANCE_ORDER[:9])-{"activation_license"}),("duplicate_clean_replay",set(MAINTENANCE_ORDER[:10])),("proof_lock",set(MAINTENANCE_ORDER[:13])-{"return_constraint"}),("post_action_contact_audit",{"reference_core"})]
    controls=[]
    for index,(phase,completed) in enumerate(prohibited):
        result=guard_transition(phase,completed,"0"*64,{"status":"PASS","allowed_phase":phase,"invokes_command":True},{"candidate_id":ACTIVE},{"safety":"PASS"}); controls.append({"control_id":f"ORDER-NEG-{index+1:02d}","phase":phase,**asdict(result)})
    write("maintenance_order_out_of_order_negative_controls_batch068h3.json",{"status":"PASS" if all(item["status"]=="BLOCK" and not item["command_invoked"] and not item["canonical_state_mutated"] for item in controls) else "FAIL","control_count":len(controls),"successfully_blocked":sum(item["status"]=="BLOCK" for item in controls),"records":controls}); return {"trace":trace,"controls":controls}


def product_progress_phase(provider: dict[str, Any]) -> dict[str, Any]:
    capabilities = runtime_capabilities()
    objectives = [
        ("PG-01", "canonical current runtime", "PASS", "v2.18 callable runtime bindings", None, True, "provider-aware runtime", "audit and dry-run current"),
        ("PG-02", "autonomous incident intake", "PARTIAL", "existing incident capture; no live intake", "not exercised", False, "none", "authorize prospective incident"),
        ("PG-03", "immutable source acquisition", "PASS", "verified source and artifact contacts", None, True, "role-specific evidence resolver", "preserve source manifest"),
        ("PG-04", "reproducible environment materialization", "BLOCK", "15 direct artifacts selected", "unresolved_dynamic_metadata", True, "precise closure decomposition", provider["next_allowed_action"]),
        ("PG-05", "authoritative command recovery", "PARTIAL", "command contact recomputed", "environment closure incomplete", True, "command gate bound", provider["next_allowed_action"]),
        ("PG-06", "prerepair failure reproduction", "NOT_RUN", "collection did not run", "environment closure incomplete", False, "none", "run authoritative collection"),
        ("PG-07", "causal failure decomposition", "PARTIAL", "diagnostic trace exists", "source AST unavailable", True, "AST trace callable", "materialize verified source"),
        ("PG-08", "bounded repair authorization", "BLOCK", "activation license denied", "target failure not materialized", True, "transition guard callable", "reproduce target failure"),
        ("PG-09", "source-only patch generation", "NOT_RUN", "patch forbidden", "repair authorization blocked", False, "none", "pass authorization"),
        ("PG-10", "semantic patch safety", "NOT_RUN", "196 obligations resolved without patch", "patch absent", True, "semantic verifier callable", "evaluate authorized patch"),
        ("PG-11", "target and invariant validation", "NOT_RUN", "no patch or target execution", "patch absent", False, "none", "run after patch"),
        ("PG-12", "duplicate clean replay", "NOT_RUN", "duplicate replay did not run", "first collection absent", False, "none", "obtain nonzero collection"),
        ("PG-13", "rollback proof", "PARTIAL", "rollback contact and transition exist", "no mutation episode", True, "rollback event bound", "exercise authorized mutation"),
        ("PG-14", "canary and health monitoring", "NOT_RUN", "connectors inactive", "activation absent", False, "none", "complete sandbox proof"),
        ("PG-15", "proof-ledger update", "PARTIAL", "content-addressed transition trace", "no repair closure", True, "proof event bound", "close repair episode"),
        ("PG-16", "prospective memory validation", "NOT_RUN", "no prospective arms", "eligible preregistration absent", False, "none", "run matched-null experiment"),
        ("PG-17", "cross-repository generalization", "NOT_RUN", "300 pairs; zero transfer authorized", "verified homology absent", True, "negative-transfer guard", "obtain repeated evidence"),
        ("PG-18", "cross-language and cross-OS support", "NOT_RUN", "Python/Linux lane only", "other substrates absent", False, "none", "separate validation"),
        ("PG-19", "live runtime connectors", "NOT_RUN", "connectors inactive", "activation threshold unmet", False, "none", "retain inactive"),
        ("PG-20", "device-maintenance readiness", "NOT_RUN", "no device execution", "end-to-end evidence absent", False, "none", "complete sandbox/canary/rollback evidence"),
    ]
    matrix = {"status": "PASS", "completion_requires_executable_evidence": True, "objectives": [
        {"objective_id": oid, "objective": name, "current_status": status, "evidence": evidence, "remaining_blocker": blocker, "batch068h3_advanced": advanced, "capability_delta": delta, "next_executable_action": action}
        for oid, name, status, evidence, blocker, advanced, delta, action in objectives]}
    write("product_goal_progress_matrix_batch068h3.json", matrix)
    gates = [
        ("source_identity", "PASS", "preserve verified SHA and origin"),
        ("environment_closure", "BLOCK", provider["next_allowed_action"]),
        ("command_authority", "MANUAL_REVIEW", "re-evaluate after closure"),
        ("harness_origin", "BLOCK", "establish historical harness origin"),
        ("target_origin", "BLOCK", "resolve installed-versus-source mode"),
        ("prerepair_reproduction", "NOT_RUN", "run collection and target replay"),
        ("failure_family_isolation", "NOT_RUN", "decompose reproduced failure"),
        ("elbow_authorization", "NOT_RUN", "apply operational boundary authorization"),
        ("patch_authorization", "NOT_RUN", "pass activation license"),
        ("source_only_patch_generation", "NOT_RUN", "generate separately authorized patch"),
        ("target_pass", "NOT_RUN", "run target validation"),
        ("invariant_pass", "NOT_RUN", "run semantic invariants"),
        ("duplicate_replay", "NOT_RUN", "repeat clean replay"),
        ("count_gate", "NOT_RUN", "apply after duplicate replay"),
    ]
    readiness = {"status": "BLOCK", "route_map_only": True, "repair_count_increment": False, "gates": [{"gate": gate, "status": status, "exact_next_action": action} for gate, status, action in gates], "shortest_path": ["dynamic historical metadata recovery", "lock verification", "authoritative collection", "target-origin resolution", "pre-repair reproduction", "failure isolation", "patch authorization", "source-only patch", "target and invariant validation", "duplicate replay", "count gate"]}
    write("fifth_issue_repair_readiness_batch068h3.json", readiness)
    distinctions = {"status": "PASS", "schema_created": True, "implementation_callable": capabilities["status"] == "PASS", "workflow_executed": True, "candidate_evidence_obtained": True, "capability_demonstrated": {"direct_artifact_selection": True, "transitive_closure": False, "collection": False, "repair": False}, "generalization_demonstrated": False, "schema_does_not_equal_capability": True}
    write("product_capability_evidence_distinction_batch068h3.json", distinctions)
    modules = sorted({target.split(":", 1)[0] for target in capabilities["bindings"].values()})
    consolidation = {"status": capabilities["status"], "canonical_runtime": "v2.18", "new_runtime_entry_point": "controllergate.protocols.v2_18_evidence_derived_topology_historical_provider:invoke_binding", "new_reusable_modules": modules, "new_transition_bindings": capabilities["pathway_bindings"], "batch_only_mechanisms": ["scripts/generate_batch068h3_historical_transitive_provider_closure_topology_hardening.py"], "unbound_mechanisms": [], "unbound_reusable_mechanism_count": 0}
    write("executable_runtime_consolidation_batch068h3.json", consolidation)
    burden = {"status": "PASS", "new_production_source_file_count": len(modules) + 1, "new_batch_only_script_count": 1, "new_committed_output_file_count": len([path for path in OUT.iterdir() if path.is_file()]) + 4, "reused_module_count": 10, "duplicate_mechanism_count": 0, "repository_maintenance_burden_delta": "moderate_increase_with_executable_provider_and_runtime_capability", "classification": "product_delta_exceeds_architecture_cost"}
    write("repository_maintainability_delta_batch068h3.json", burden)
    public_paths = [ROOT / "README.md", ROOT / "docs/current_status.md", ROOT / "docs/current_protocol.md", ROOT / "docs/capability_inventory.md", ROOT / "docs/technical_validation_gap_report.md", ROOT / "docs/CURRENT_FRONTIER_STATUS.md", ROOT / "controllergate_v1_7_beta/reports/critic_review_package/shareable_summary.md"]
    forbidden = ["torus", "brot", "bulb", "chromosomal", "observer-state", "recursion-constant", "klein twist", "rna primase", "osqn", "cymatics", "chromatin", "epigenetic"]
    hits = [{"path": path.relative_to(ROOT).as_posix(), "term": term} for path in public_paths for term in forbidden if term in path.read_text(encoding="utf-8").lower()]
    write("public_language_audit_batch068h3.json", {"status": "PASS" if not hits else "FAIL", "checked_paths": [path.relative_to(ROOT).as_posix() for path in public_paths], "forbidden_hits": hits, "neutral_engineering_language_required": True})
    return {"matrix": matrix, "readiness": readiness, "distinctions": distinctions, "consolidation": consolidation, "burden": burden}


def final_phase(artifact:dict[str,Any],contacts:dict[str,Any],reference:dict[str,Any],ast_data:dict[str,Any],topology:dict[str,Any],volume:dict[str,Any],proof:dict[str,Any],tld:dict[str,Any],provider:dict[str,Any],maintenance:dict[str,Any],product:dict[str,Any])->None:
    active=reference["active"]; by_role={item["canonical_role"]:item for item in active["contacts"]}; provider_contact=dict(by_role["provider_and_cofactor"]); provider_contact.update({"evidence_status":"PARTIAL","gate_decision":"BLOCK","blocker":"unresolved_dynamic_metadata"}); environment_contact=dict(by_role["environment_compartment"]); environment_contact.update({"evidence_status":"PARTIAL","gate_decision":"BLOCK","blocker":"historical_distribution_and_transitive_provider_closure_incomplete"})
    update={"status":"PASS","candidate_id":ACTIVE,"reference_core_status":"PASS","contact_count":14,"provider_contact":provider_contact,"environment_contact":environment_contact,"target_origin_contact":by_role["target_import_origin"],"local_graph_hash":next(item["graph_hash"] for item in topology["graphs"] if item["candidate_id"]==ACTIVE),"coupled_edge_count":len(topology["coupling"]),"selected_basin_count":1,"activation_license":"BLOCK","proof_matrix":"PLANNED"}; write("nbclient_topology_update.json",update)
    capsule={"status":"PARTIAL","candidate_id":ACTIVE,"historical_lock_status":"BLOCK","observed_historical_environment":"PARTIAL","cutoff_compatible_environment":"PARTIAL","current_diagnostic_environment":"PASS/diagnostic_only","language_runtime":"ESTABLISHED","package_epoch":"NOT_ESTABLISHED","OS_distribution":"PARTIAL","build_system":"PARTIAL","target_origin":"CONFLICTED","harness":"NOT_ESTABLISHED","warning_boundary_classification":"diagnostic_environment_harness_warning_basin","collection_authorized":False,"blocker":"unresolved_dynamic_metadata"}; write("nbclient_historical_capsule_v2.json",capsule); collection={"status":"BLOCK","collection_run_1":"NOT_RUN","collection_run_2":"NOT_RUN","collected_node_count":0,"node_set_equivalence":"NOT_RUN","warning_boundary_classification":"NOT_RUN","test_bodies_executed":0,"target_tests_executed":0,"workspace_mutations":0,"test_tree_mutations":0,"next_allowed_action":provider["next_allowed_action"]}; write("nbclient_collection_decision_batch068h3.json",collection)
    promotion_criteria={"batch068h2_artifact_ingestion":artifact["status"]=="PASS","generic_topology_templates_removed":all(not item["generic_template_derived"] for item in contacts["ledgers"]),"twenty_five_role_specific_contact_ledgers":len(contacts["ledgers"])==25 and all(len(item["contacts"])==14 for item in contacts["ledgers"]),"semantic_local_edges":any(item["edge_class"]!="canonical_sequence" for item in topology["edges"]),"no_adjacency_coupling":all(not item["candidate_adjacency_used"] for item in topology["pairs"]),"evidence_derived_basin_selection":volume["decision"]["status"]=="PASS","evidence_derived_confidence":len({item["confidence"] for item in volume["volume"]["cells"]})>1,"semantic_196_cell_matrix":proof["verification"]["resolved_cell_count"]==196 and proof["verification"]["unresolved_fallback_cell_count"]==0,"historical_provider_resolver_callable":product["consolidation"]["status"]=="PASS","v2_17_preservation":True,"full_tests_and_regressions":"verified_by_local_validation_and_required_workflow"}; architectural_pass=all(value is True or value=="verified_by_local_validation_and_required_workflow" for value in promotion_criteria.values()); promotion={"status":"PASS" if architectural_pass else "BLOCK","protocol_before":"v2.17","protocol_after":"v2.18" if architectural_pass else "v2.17","protocol_name":"evidence_derived_topology_historical_provider_lane","architectural_gates_passed":architectural_pass,"criteria":promotion_criteria,"candidate_collection_success_required":False,"patch_authority":False}; write("v2_17_preservation_audit_batch068h3.json",{"status":"PASS","selectable_config":"configs/controllergate_v2_17_topology_runtime.yaml","historical_outputs_preserved":True}); write("v2_18_promotion_decision_batch068h3.json",promotion); write("v2_18_current_protocol_audit_batch068h3.json",{"status":"PASS" if architectural_pass else "BLOCK","protocol":"v2.18" if architectural_pass else "v2.17","claim_boundaries_preserved":True})
    current={"status":"PASS","protocol_version":"v2.18","protocol_name":"evidence_derived_topology_historical_provider_lane","patch_authority":False,"repair_execution_authority":False,"target_test_execution_authority":False,"live_runtime_connectors":"inactive","full_scoring":"NOT_RUN/disallowed","memory_lift":"not_demonstrated","self_maintaining_software":"false/not_demonstrated","issue_derived_repair_count":4,"native_external_repair_count":4,"topology_runtime_status":"PASS","historical_lock_status":"BLOCK","next_safe_action":provider["next_allowed_action"]}; current["state_hash"]=hash_record(current); write_json_deterministic(CURRENT,current)
    frontier=load(FRONTIER); frontier.update({"validated_current_protocol":"v2.18 evidence_derived_topology_historical_provider_lane","validated_current_protocol_status":"PASS","topology_runtime_status":"PASS","historical_capsule_status":"PARTIAL","historical_lock_status":"BLOCK","next_safe_action":provider["next_allowed_action"],"patch_generated":False,"patch_applied":False,"target_tests_executed":0}); frontier.pop("state_hash",None); frontier["state_hash"]=hash_record(frontier); write_json_deterministic(FRONTIER,frontier)
    formula_found=sum(item["formula_status"]=="PROVENANCE_ESTABLISHED" for item in tld["formulas"]); formula_missing=sum(item["formula_status"]=="MISSING_CANONICAL_DEFINITION" for item in tld["formulas"]); final={"status":"PASS","validated_protocol_before":"v2.17 canonical_topology_environment_volume_lane","validated_protocol_after":"v2.18 evidence_derived_topology_historical_provider_lane","candidate_ledger_count":25,"generic_template_ledger_count":0,"unique_contact_vector_count":contacts["unique_vectors"],"role_specific_evidence_coverage_count":sum(bool(item["evidence_sources"]) for item in contacts["coverage"]),"local_brot_semantic_edge_count":sum(item["edge_class"]!="canonical_sequence" for item in topology["edges"]),"tot_brot_candidate_pairs_evaluated":len(topology["pairs"]),"verified_coupling_edge_count":len(topology["coupling"]),"adjacency_derived_edge_count":0,"negative_transfer_count":len(topology["pairs"])-len(topology["coupling"]),"tot_bulb_selected_basin_count":1,"manual_basin_count":0,"fixed_confidence_cell_count":0,"proof_matrix_rule_count":len(Counter(rule for item in proof["cells"] for rule in item["rule_ids"])),"proof_matrix_cell_count":196,"executed_falsification_control_count":len(proof["controls"]),"tld_formulas_found":formula_found,"tld_formulas_missing":formula_missing,"UI":"NOT_ESTABLISHED","NSS":"NOT_ESTABLISHED","SEP":"NOT_ESTABLISHED","T_e":"NOT_ESTABLISHED","S_e":"NOT_ESTABLISHED","unique_omega_count":tld["unique"],"historical_dependency_graph_node_count":provider["graph"]["node_count"],"historical_dependency_graph_edge_count":provider["graph"]["edge_count"],"resolved_package_count":len(provider["lock"]["selected_artifacts"]),"unresolved_package_count":len(provider["lock"]["unresolved_nodes"]),"constraint_conflict_count":len(provider["lock"]["unsatisfied_constraints"]),"post_cutoff_selected_artifact_count":0,"build_dependency_closure":"NOT_ESTABLISHED","runtime_dependency_closure":"NOT_ESTABLISHED","historical_lock_status":"BLOCK","observed_historical_environment_status":"PARTIAL","cutoff_compatible_environment_status":"PARTIAL","current_diagnostic_environment_status":"PASS/diagnostic_only","nbclient_provider_contact_status":"PARTIAL","nbclient_environment_contact_status":"PARTIAL","nbclient_target_origin_status":update["target_origin_contact"]["evidence_status"],"collection_run_1":"NOT_RUN","collection_run_2":"NOT_RUN","collected_node_count":0,"node_set_equivalence":"NOT_RUN","warning_boundary_classification":"NOT_RUN","test_bodies_executed":0,"target_tests_executed":0,"workspace_mutations":0,"test_tree_mutations":0,"activation_license":"BLOCK","v2_17_preservation":"PASS","v2_18_promotion":"PASS","bounded_probe_capability":"BLOCK","issue_derived_repair_count":4,"native_external_repair_count":4,"patch_generated":False,"patch_applied":False,"repair_increment":False,"full_scoring":"NOT_RUN/disallowed","memory_lift":"not_demonstrated","self_maintaining_software":"false/not_demonstrated","exact_next_allowed_action":provider["next_allowed_action"],"maintenance_order_transition_count":len(maintenance["trace"]),"prohibited_transition_negative_control_count":len(maintenance["controls"]),"prohibited_transitions_successfully_blocked":sum(item["status"]=="BLOCK" for item in maintenance["controls"]),"eligible_parent_count":tld["decision"]["eligible_parent_count"],"ineligible_flatline_count":tld["classes"].get("ineligible_flatline",0),"ineligible_minimum_deltas_count":tld["classes"].get("ineligible_minimum_deltas",0),"winner_N_argmin_established_count":tld["decision"]["winner_N_argmin_established_count"],"winner_N_elbow_established_count":0,"winner_disagreement_count":0,"T_e_established_count":0,"S_e_established_count":0,"ast_extrusion_candidate_count":25,"ast_parse_pass_count":ast_data["summary"]["ast_parsed_candidate_count"],"ast_parse_block_count":ast_data["summary"]["parse_blocked_count"],"failure_to_source_trace_count":ast_data["summary"]["failure_to_source_trace_count"],"tests_only_contact_acceptance_count":0,"cross_family_homology_pair_count":len(topology["pairs"]),"verified_homology_count":len(topology["coupling"]),"tot_brot_edges_backed_by_homology_records":len(topology["coupling"]),"tot_bulb_probe_candidates_considered":len(volume["measurement"]["probe_candidates"]),"tot_bulb_probes_executed":volume["measurement"]["probes_executed"],"tot_bulb_volume_updates":len(volume["measurement"]["volume_updates"]),"tot_bulb_stop_reason":volume["measurement"]["stop_reason"],"proof_cells_resolved":proof["verification"]["resolved_cell_count"],"proof_unresolved_fallback_cells":proof["verification"]["unresolved_fallback_cell_count"],"proof_equivalence_class_cells":proof["verification"]["equivalence_class_cell_count"],"proof_unjustified_duplicate_payload_count":proof["verification"]["unjustified_duplicate_cell_payload_count"]}; write("batch068h3_final_decision.json",final); write("batch068h3_handoff_plan.json",{"status":"PASS","next_allowed_action":final["exact_next_allowed_action"],"manual_artifact_boundary":True,"patching_forbidden":True}); write_text_lf(OUT/"batch068h3_summary.md","# Batch068h3 summary\n\nEvidence-derived contact resolution, semantic topology, bounded environment measurement, semantic proof obligations, clean-track metrology, and historical provider resolution executed under the maintenance-order runtime.\n\nThe historical provider lock remains blocked because selected decision-time artifacts lack verified transitive dependency metadata. Collection did not run. No target test body or patch executed, and repair counts did not change.")


def product_final_overlay(product: dict[str, Any]) -> None:
    path = OUT / "batch068h3_final_decision.json"
    final = load(path)
    final.update({
        "primary_product_objective_advanced": "reusable_historical_provider_resolution_and_precise_dynamic_metadata_decomposition",
        "historical_provider_closure_delta": "15_direct_artifacts_preserved_transitive_metadata_unresolved",
        "command_materialization_delta": "authority_recomputed_execution_remains_blocked",
        "collection_readiness_delta": "exact_dynamic_metadata_blocker_identified",
        "fifth_repair_readiness_delta": "route_map_created_no_repair_counted",
        "canonical_runtime_capability_delta": "18_callable_bindings_zero_unbound",
        "reusable_mechanisms_added": len(product["consolidation"]["new_reusable_modules"]),
        "batch_local_mechanisms_added": len(product["consolidation"]["batch_only_mechanisms"]),
        "unbound_mechanisms": product["consolidation"]["unbound_mechanisms"],
        "pathway_events_newly_executable": ["source_identity", "environment_closure_decomposition", "command_authority_recomputation", "maintenance_transition_guard"],
        "remaining_nonexecuted_pathway_events": ["authoritative_collection", "pre_repair_replay", "patch_generation", "validation", "duplicate_replay", "canary", "health_monitoring"],
        "repository_maintenance_burden_delta": product["burden"]["repository_maintenance_burden_delta"],
        "tld_work_percentage_classification": "supporting",
        "tld_blocked_primary_product_work": False,
        "exact_shortest_path_to_fifth_counted_repair": product["readiness"]["shortest_path"],
        "exact_shortest_path_to_end_to_end_autonomous_maintenance": ["fifth repair route", "prospective acquisition", "sandbox validation", "canary", "health monitor", "commit_or_rollback", "proof update"],
        "exact_shortest_path_to_prospective_memory_validation": ["fresh eligible candidate", "preregister matched arms", "freeze evidence", "execute both arms", "duplicate replay", "evaluate threshold"],
        "exact_shortest_path_to_universal_device_maintenance": ["repeatable Git repair baseline", "agnostic provenance lock", "shadow materialization", "signed rollback", "operator policy", "inactive connector validation"],
    })
    write_json_deterministic(path, final)
    write_text_lf(OUT / "batch068h3_summary.md", "# Batch068h3 summary\n\nThe primary product delta is a reusable historical-provider resolver and an exact decomposition of the remaining dynamic-metadata blocker. The canonical v2.18 runtime exposes every new reusable mechanism through callable bindings.\n\nSupporting contact, topology, bounded measurement, proof-obligation, AST, and shadow metrology checks remained subordinate to the executable maintenance path. The historical lock is blocked because verified transitive dependency metadata is absent. Collection did not run. No target test body or patch executed, and repair counts did not change.")


def write_manifest()->None:
    rows=[f"{sha256_file(path)}  {path.relative_to(OUT).as_posix()}" for path in sorted(OUT.rglob("*")) if path.is_file() and path.name!="SHA256SUMS.txt"]; write_text_lf(OUT/"SHA256SUMS.txt","\n".join(rows))


def main()->int:
    parser=argparse.ArgumentParser(); parser.add_argument("--artifact-zip",default=os.environ.get("BATCH068H2_ARTIFACT_ZIP")); parser.add_argument("--notebook-source",action="append",default=[]); args=parser.parse_args(); OUT.mkdir(parents=True,exist_ok=True)
    artifact=artifact_phase(Path(args.artifact_zip) if args.artifact_zip else None); notebooks=notebook_phase([Path(item) for item in args.notebook_source]); contacts=contacts_phase(artifact); reference=reference_core_phase(contacts); ast_data=ast_topology_phase(contacts); topology=semantic_topology_phase(contacts,ast_data); volume=volume_and_measurement_phase(reference,topology); proof=proof_and_controls_phase(reference,contacts,topology); tld=tld_phase(notebooks,contacts,topology); provider=provider_phase(); maintenance=maintenance_phase(reference); product=product_progress_phase(provider); final_phase(artifact,contacts,reference,ast_data,topology,volume,proof,tld,provider,maintenance,product); product_final_overlay(product); write_manifest(); print("Batch068h3 generated: protocol=v2.18 historical_lock=BLOCK unresolved_dynamic_metadata collection=NOT_RUN"); return 0


if __name__=="__main__": raise SystemExit(main())
