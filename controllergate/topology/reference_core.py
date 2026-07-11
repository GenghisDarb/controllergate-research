from __future__ import annotations

from controllergate.core.evidence import hash_record

from .types import ReferenceCoreState

REFERENCE_ROLES = (
    ("CG-REF-01", "provenance_and_candidate_identity_anchor"),
    ("CG-REF-02", "decision_time_evidence_boundary"),
    ("CG-REF-03", "prerepair_failure_reference_state_signature"),
    ("CG-REF-04", "environment_command_harness_reference_state"),
    ("CG-REF-05", "rollback_and_proof_ledger_anchor"),
)


def build_reference_core(evidence: dict[str, object]) -> tuple[ReferenceCoreState, ...]:
    source_hash = hash_record(evidence)
    return tuple(
        ReferenceCoreState(role_id, role, source_hash, f"verify_{role}", hash_record({"role": role, "source": source_hash}))
        for role_id, role in REFERENCE_ROLES
    )


def build_semantic_reference_core(role_manifests: dict[str, dict[str, object]]) -> tuple[ReferenceCoreState, ...]:
    records = []
    for role_id, role in REFERENCE_ROLES:
        manifest = role_manifests.get(role_id)
        if not manifest or not manifest.get("evidence_hashes"):
            raise ValueError(f"role_specific_reference_evidence_missing:{role_id}")
        evidence_hash = hash_record(manifest)
        records.append(ReferenceCoreState(role_id, role, evidence_hash, f"verify_{role_id.lower().replace('-', '_')}", hash_record({"role_id": role_id, "evidence_hash": evidence_hash}), True, str(manifest.get("reopen_condition", "new_decision_time_safe_evidence"))))
    return tuple(records)
