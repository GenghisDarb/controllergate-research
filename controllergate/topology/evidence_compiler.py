from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Iterable, Mapping

from controllergate.state.integrity import canonical_hash


BOUNDARY_DIMENSIONS = (
    "runtime", "abi", "operating_system", "architecture", "source_revision",
    "source_tree", "provider_graph", "dependency_lock", "build_backend",
    "runner", "harness", "command", "working_directory", "environment",
    "filesystem", "permissions", "writable_paths", "network_policy",
    "service_state", "resource_limits", "system_libraries", "cleanup_state",
)


@dataclass(frozen=True)
class ObserverStateContractV2:
    observer_id: str
    role: str
    candidate_id: str
    task_goal: str
    claim_scope: str
    risk_posture: str
    allowed_operation_classes: tuple[str, ...]
    forbidden_operation_classes: tuple[str, ...]
    truth_access: bool
    patch_access: bool
    future_evidence_access: bool
    memory_mode: str
    human_authorization_state: str
    parent_observer_state_hash: str | None
    creation_time: str
    expiry_condition: str

    def validate(self) -> None:
        if self.role not in {"external reviewer", "human approver"} and self.truth_access:
            raise ValueError("truth access is not allowed for this observer")
        if self.patch_access:
            raise ValueError("ordinary evidence-only observer cannot access patches")
        if self.future_evidence_access:
            raise ValueError("future evidence access is forbidden")

    @property
    def contract_hash(self) -> str:
        self.validate()
        return canonical_hash(asdict(self))


def compile_boundary_volume(candidate: Mapping[str, Any], role_receipts: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    role_receipts = tuple(role_receipts)
    provider = candidate.get("observed_provider", {})
    recipe = candidate.get("provider_recipe", {})
    source = candidate.get("source_capsule", {})
    process = candidate.get("process", {})
    cleanup = candidate.get("cleanup", {})
    values = {
        "runtime": provider.get("python", {}).get("version"), "abi": provider.get("abi_tags"),
        "operating_system": provider.get("python", {}).get("system"), "architecture": provider.get("python", {}).get("machine"),
        "source_revision": source.get("observed_commit"), "source_tree": source.get("source_tree_hash"),
        "provider_graph": provider.get("package_graph_hash"), "dependency_lock": recipe.get("dependency_lock_identity"),
        "build_backend": recipe.get("install_command"), "runner": recipe.get("project_target_command", [None])[0],
        "harness": recipe.get("semantic_outcome_contract_id"), "command": recipe.get("project_target_command"),
        "working_directory": recipe.get("working_directory_policy"), "environment": recipe.get("environment_allowlist"),
        "filesystem": provider.get("platform_tags"), "permissions": "measured_process_boundary",
        "writable_paths": "runtime_root_only", "network_policy": recipe.get("network_acquisition_policy"),
        "service_state": candidate.get("service_lifecycle") or "NOT_APPLICABLE", "resource_limits": process.get("resource_state", "UNRESOLVED"),
        "system_libraries": provider.get("python", {}).get("soabi"), "cleanup_state": cleanup.get("status"),
    }
    receipt_hashes = sorted({str(r.get("measurement_hash")) for r in role_receipts if r.get("measurement_hash")})
    cells=[]
    for dimension in BOUNDARY_DIMENSIONS:
        value=values.get(dimension); state="VERIFIED" if value not in (None,"",[],{}) else "UNRESOLVED"
        cells.append({"dimension":dimension,"observed":value,"state":state,"raw_measurement_receipts":receipt_hashes,"independent_verification_receipts":sorted(str(r.get("verifier_execution_receipt")) for r in role_receipts if r.get("verifier_execution_receipt")),"allowed_alignment_actions":["materialize_source_declared_requirement","repeat_neutral_probe"],"forbidden_alignment_actions":["source_mutation","test_mutation","outcome_driven_retry","future_evidence"],"reopen_condition":None if state=="VERIFIED" else f"execute_{dimension}_measurement"})
    record={"candidate_id":candidate["candidate_id"],"cells":cells,"outcome_dependent_alignment_count":0,"frozen_before_target":True,"authority_allowed":"environment alignment only","authority_forbidden":["terminal","repair","count"]}
    return {**record,"volume_hash":canonical_hash(record)}


def compile_local_graph(candidate: Mapping[str, Any], producer_receipts: Iterable[Mapping[str, Any]], verifier_receipts: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    producers=tuple(producer_receipts); verifiers=tuple(verifier_receipts); topology=candidate.get("source_topology", {})
    nodes=list(topology.get("nodes", [])); edges=[]
    for edge in topology.get("edges", []):
        edges.append({**edge,"producer_receipt":topology.get("tracked_manifest_operation"),"verifier_receipt":topology.get("graph_hash"),"direct":True})
    by_role={str(r["semantic_role"]):r for r in producers}; checks={str(r["semantic_role"]):r for r in verifiers}
    for role,receipt in sorted(by_role.items()):
        node_id=f"role:{role}"; nodes.append({"node_id":node_id,"node_class":"MEASURED_ROLE","evidence_hash":receipt.get("measurement_hash"),"status":receipt.get("status")})
        for object_id in receipt.get("raw_object_ids",[]):
            raw_id=f"raw:{object_id}"; nodes.append({"node_id":raw_id,"node_class":"RAW_EVIDENCE_OBJECT","sha256":object_id})
            edges.append({"source":raw_id,"target":node_id,"edge_class":"DERIVES_ROLE","producer_receipt":receipt.get("producer_execution_receipt"),"verifier_receipt":checks.get(role,{}).get("verifier_execution_receipt"),"direct":True})
    process=candidate.get("process",{}); product=candidate.get("product",{})
    nodes.extend([{"node_id":"process:target","node_class":"TARGET_PROCESS","evidence_hash":process.get("record_hash")},{"node_id":"product:target","node_class":"PRODUCT","evidence_hash":canonical_hash(product)}])
    edges.append({"source":"process:target","target":"product:target","edge_class":"PRODUCES","producer_receipt":process.get("record_hash"),"verifier_receipt":candidate.get("typed_incident_verification",{}).get("raw_evidence_hash"),"direct":True})
    unique={str(n["node_id"]):n for n in nodes}; valid_edges=[e for e in edges if e.get("source") and e.get("target")]
    unresolved=[str(n["node_id"]) for n in unique.values() if n.get("status")=="BLOCK"]+ [f"parse:{x['path']}" for x in topology.get("parse_failures",[])]
    record={"candidate_id":candidate["candidate_id"],"nodes":[unique[k] for k in sorted(unique)],"edges":valid_edges,"unresolved_regions":unresolved,"recovery_regions":[{"region":x,"legal_next_probe":"repeat_source_bound_measurement"} for x in unresolved],"legal_next_probes":["resolve_unresolved_evidence"],"prohibited_transitions":["patch","count","truth_read","candidate_substitution"],"authority_allowed":"topology-derived probe planning","authority_forbidden":["terminal transfer","repair","count"]}
    return {**record,"graph_hash":canonical_hash(record)}


def compile_coupled_projection_graph(candidate: Mapping[str, Any], local_graph: Mapping[str, Any], boundary: Mapping[str, Any]) -> dict[str, Any]:
    dimensions={cell["dimension"]:cell for cell in boundary["cells"]}
    projections=("source_declared_vs_materialized_provider","normal_control_vs_target","runner_vs_harness","service_available_vs_unavailable","source_topology_vs_incident")
    edges=[]
    for projection in projections:
        unresolved=sum(cell["state"]!="VERIFIED" for cell in dimensions.values())
        edges.append({"projection_id":projection,"local_graph_hash":local_graph["graph_hash"],"boundary_volume_hash":boundary["volume_hash"],"matched_dimensions":sorted(k for k,v in dimensions.items() if v["state"]=="VERIFIED"),"conflicting_dimensions":[],"unresolved_dimension_count":unresolved,"transfer_allowed":"narrow_probe_reuse_only" if unresolved==0 else "none","terminal_transfer_allowed":False})
    record={"candidate_id":candidate["candidate_id"],"projection_edges":edges,"false_terminal_transfer_count":0,"authority_allowed":"same-candidate projection comparison","authority_forbidden":["cross-candidate terminal","repair","count"]}
    return {**record,"graph_hash":canonical_hash(record)}


def compile_decisive_board(*, candidate_id: str, role_receipts: Iterable[Mapping[str, Any]], boundary: Mapping[str, Any], local_graph: Mapping[str, Any], coupled_graph: Mapping[str, Any], observer_state_hash: str, provisional_root: str, modality_observations: Iterable[Mapping[str, Any]], budgets: Mapping[str, Any]) -> dict[str, Any]:
    """Derive the decisive board.  No caller-supplied hypothesis or probe API exists."""
    roles=tuple(role_receipts); modalities=tuple(modality_observations)
    cells=[{"cell_id":f"boundary:{c['dimension']}","state":c['state'],"evidence":c['raw_measurement_receipts']} for c in boundary["cells"]]
    cells.extend({"cell_id":f"modality:{m['modality']}","state":m['state'],"evidence":m['raw_object_ids']} for m in modalities)
    causal_ontology=("source_owned_behavior_defect","provider_owned","environment_owned","platform_owned","network_or_transport_owned","harness_owned","test_or_expectation_fragility","mixed_failure","insufficient_evidence")
    causal_evidence=sorted(str(r.get('measurement_hash')) for r in roles)
    cells.append({"cell_id":"causal_terminal","state":"UNRESOLVED","evidence":causal_evidence})
    hypotheses=[{"hypothesis_id":name,"derived_from":causal_evidence,"claim":name,"prior_mode":"unweighted_registered_ontology"} for name in causal_ontology]
    constraints=[]; probes=[]
    for cell in cells:
        if cell["state"] in {"UNRESOLVED","CONTRADICTED"}:
            hid=f"hypothesis:{cell['cell_id']}"; hypotheses.append({"hypothesis_id":hid,"derived_from":cell["evidence"],"claim":"boundary_or_evidence_gap"})
            constraints.append({"constraint_id":f"constraint:{cell['cell_id']}","hypothesis_id":hid,"required_state":"VERIFIED","derived_from":cell["evidence"]})
            probes.append({"probe_id":f"probe:{cell['cell_id']}","hypothesis_id":hid,"neutral_output_keys":["return_code","stdout_sha256","stderr_sha256"],"prerequisites":cell["evidence"],"cost":1.0,"risk":0.0,"network":False})
    record={"candidate_id":candidate_id,"role_receipt_hashes":sorted(str(r.get('measurement_hash')) for r in roles),"boundary_volume_hash":boundary["volume_hash"],"local_graph_hash":local_graph["graph_hash"],"coupled_graph_hash":coupled_graph["graph_hash"],"observer_state_hash":observer_state_hash,"provisional_root":provisional_root,"cells":cells,"derived_hypotheses":hypotheses,"derived_constraints":constraints,"derived_probe_contracts":probes,"budgets":dict(budgets),"caller_supplied_hypothesis_count":0,"caller_supplied_constraint_count":0,"caller_supplied_probe_count":0}
    return {**record,"frame_hash":canonical_hash(record)}
