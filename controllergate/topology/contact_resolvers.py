from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from controllergate.core.evidence import hash_record, sha256_file


HANDLER_BY_ROLE = {
    "candidate_identity": ("establish_source_identity",),
    "source_revision": ("establish_candidate_sha",),
    "target_test": ("resolve_native_target_paths",),
    "command_authority": ("extract_authoritative_commands", "rank_and_normalize_commands"),
    "harness_origin": ("classify_harness_origin",),
    "runner_origin": ("resolve_runner_target_relationship",),
    "provider_and_cofactor": ("classify_provider_feasibility",),
    "rollback_and_proof_path": ("emit_candidate_terminal_state",),
}


def _resolve(role: str, candidate: dict[str, Any], state_path: Path, extra_evidence: list[Path] | None = None) -> dict[str, Any]:
    transitions = [item for item in candidate.get("semantic_transitions", []) if item.get("handler_name") in HANDLER_BY_ROLE.get(role, ())]
    evidence_sources: list[str] = []
    evidence_hashes: list[str] = []
    for item in transitions:
        if item.get("decision_time_evidence_consumed"):
            evidence_sources.append(f"{state_path.as_posix()}#{item['handler_name']}")
            evidence_hashes.extend(str(value) for value in item.get("input_hashes", []) if value)
            if item.get("verification_hash"):
                evidence_hashes.append(str(item["verification_hash"]))
    for path in extra_evidence or []:
        if path.is_file():
            evidence_sources.append(path.as_posix())
            evidence_hashes.append(sha256_file(path))
    safe = [item for item in transitions if item.get("operation_status") == "COMPLETED" and item.get("gate_decision") == "PASS" and item.get("verification_status") == "PASS"]
    if evidence_sources and safe:
        status = "ESTABLISHED"; decision = "PASS"; verifier = "PASS"; blocker = None; missing: list[str] = []
    elif evidence_sources:
        status = "PARTIAL"
        decision = "BLOCK"
        verifier = "PARTIAL"
        transition_blocker = transitions[-1].get("blocker_code") if transitions else None
        blocker = transition_blocker or f"{role}_not_fully_verified"
        missing = [f"complete_{role}_evidence"]
    else:
        status = "NOT_ESTABLISHED"; decision = "BLOCK"; verifier = "NOT_ESTABLISHED"; blocker = f"{role}_role_specific_evidence_missing"; missing = [f"role_specific_{role}_evidence"]
    return {
        "canonical_role": role, "evidence_sources": evidence_sources, "evidence_hashes": sorted(set(evidence_hashes)),
        "authority_class": "decision_time_repository_evidence", "decision_time_status": "safe", "independent_verifier": f"verify_{role}_contact",
        "verifier_result": verifier, "evidence_status": status, "gate_decision": decision, "confidence": 1.0 if decision == "PASS" else (0.5 if evidence_sources else 0.0),
        "blocker": blocker, "missing_evidence": missing, "reopen_conditions": [] if decision == "PASS" else [f"provide_decision_time_safe_{role}_evidence"],
        "generic_template_derived": False,
    }


def resolve_artifact_custody_contact(candidate: dict[str, Any], state_path: Path, evidence: list[Path]) -> dict[str, Any]: return _resolve("artifact_custody", candidate, state_path, evidence)
def resolve_candidate_identity_contact(candidate: dict[str, Any], state_path: Path, evidence: list[Path]) -> dict[str, Any]: return _resolve("candidate_identity", candidate, state_path, evidence)
def resolve_source_revision_contact(candidate: dict[str, Any], state_path: Path, evidence: list[Path]) -> dict[str, Any]: return _resolve("source_revision", candidate, state_path, evidence)
def resolve_failure_signature_contact(candidate: dict[str, Any], state_path: Path, evidence: list[Path]) -> dict[str, Any]: return _resolve("failure_signature", candidate, state_path, evidence)
def resolve_target_test_contact(candidate: dict[str, Any], state_path: Path, evidence: list[Path]) -> dict[str, Any]: return _resolve("target_test", candidate, state_path, evidence)
def resolve_command_authority_contact(candidate: dict[str, Any], state_path: Path, evidence: list[Path]) -> dict[str, Any]: return _resolve("command_authority", candidate, state_path, evidence)
def resolve_harness_origin_contact(candidate: dict[str, Any], state_path: Path, evidence: list[Path]) -> dict[str, Any]: return _resolve("harness_origin", candidate, state_path, evidence)
def resolve_runner_origin_contact(candidate: dict[str, Any], state_path: Path, evidence: list[Path]) -> dict[str, Any]: return _resolve("runner_origin", candidate, state_path, evidence)
def resolve_target_import_origin_contact(candidate: dict[str, Any], state_path: Path, evidence: list[Path]) -> dict[str, Any]: return _resolve("target_import_origin", candidate, state_path, evidence)
def resolve_provider_cofactor_contact(candidate: dict[str, Any], state_path: Path, evidence: list[Path]) -> dict[str, Any]: return _resolve("provider_and_cofactor", candidate, state_path, evidence)
def resolve_environment_compartment_contact(candidate: dict[str, Any], state_path: Path, evidence: list[Path]) -> dict[str, Any]: return _resolve("environment_compartment", candidate, state_path, evidence)
def resolve_workspace_execution_contact(candidate: dict[str, Any], state_path: Path, evidence: list[Path]) -> dict[str, Any]: return _resolve("workspace_and_execution_boundary", candidate, state_path, evidence)
def resolve_source_failure_topology_contact(candidate: dict[str, Any], state_path: Path, evidence: list[Path]) -> dict[str, Any]: return _resolve("source_and_failure_topology", candidate, state_path, evidence)
def resolve_rollback_proof_contact(candidate: dict[str, Any], state_path: Path, evidence: list[Path]) -> dict[str, Any]: return _resolve("rollback_and_proof_path", candidate, state_path, evidence)


RESOLVERS: tuple[Callable[[dict[str, Any], Path, list[Path]], dict[str, Any]], ...] = (
    resolve_artifact_custody_contact, resolve_candidate_identity_contact, resolve_source_revision_contact, resolve_failure_signature_contact,
    resolve_target_test_contact, resolve_command_authority_contact, resolve_harness_origin_contact, resolve_runner_origin_contact,
    resolve_target_import_origin_contact, resolve_provider_cofactor_contact, resolve_environment_compartment_contact,
    resolve_workspace_execution_contact, resolve_source_failure_topology_contact, resolve_rollback_proof_contact,
)


def resolve_all_contacts(candidate: dict[str, Any], state_path: Path, role_evidence: dict[str, list[Path]]) -> list[dict[str, Any]]:
    records = []
    for resolver in RESOLVERS:
        role = resolver.__name__.removeprefix("resolve_").removesuffix("_contact")
        role = {"provider_cofactor": "provider_and_cofactor", "workspace_execution": "workspace_and_execution_boundary", "source_failure_topology": "source_and_failure_topology", "rollback_proof": "rollback_and_proof_path"}.get(role, role)
        records.append(resolver(candidate, state_path, role_evidence.get(role, [])))
    return records
