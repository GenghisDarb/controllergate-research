from __future__ import annotations

RULE_FAMILIES = {
    "identity_preservation": ("artifact_custody", "candidate_identity", "source_revision"),
    "failure_oracle_integrity": ("failure_signature", "target_test", "command_authority", "harness_origin"),
    "runtime_origin_containment": ("runner_origin", "target_import_origin", "provider_and_cofactor", "environment_compartment"),
    "workspace_nonmutation": ("workspace_and_execution_boundary",),
    "source_topology_scope": ("source_and_failure_topology",),
    "rollback_proof_custody": ("rollback_and_proof_path",),
}


def family_for_role(role: str) -> str:
    return next(name for name, roles in RULE_FAMILIES.items() if role in roles)
