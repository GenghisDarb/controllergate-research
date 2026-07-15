from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from .stable_identity import stable_hash


SOURCE_OWNERSHIP_REQUIREMENTS = (
    "candidate_identity", "incident_snapshot", "source_revision", "source_test_immutability",
    "provider_runtime_identity", "target_provenance", "command_authority", "runner_origin",
    "harness_origin", "duplicate_failure_reproduction", "normal_incident_shared_frame",
    "direct_divergence", "provider_alternative_excluded", "environment_alternative_excluded",
    "platform_alternative_excluded", "network_transport_alternative_excluded",
    "harness_target_alternative_excluded", "expectation_checked", "direct_source_contact",
    "repair_critical_interlocks_clear", "causal_elbow_open", "no_material_alternative",
)

REPAIR_LICENSE_REQUIREMENTS = (
    "source_ownership_token", "single_use_authorization", "human_review", "write_access_lease",
    "allowlisted_source_region", "patch_plan_hash", "source_only_scope", "test_tree_immutability",
    "maximum_patch_size", "forbidden_file_scan", "validation_plan", "native_invariant_plan",
    "fresh_duplicate_workspace_plan", "same_provider_replay_plan", "rollback_ready_token",
    "proof_count_nonduplication_plan", "resource_budget", "network_policy", "public_write_prohibition",
)


@dataclass(frozen=True)
class AuthorityToken:
    token_type: str
    candidate_id: str
    run_id: str
    frame_hash: str
    requirement_hashes: tuple[tuple[str, str], ...]
    verifier: str
    expires_at: str
    nonce: str

    @property
    def token_hash(self) -> str:
        return stable_hash({"type": self.token_type, "candidate": self.candidate_id, "run": self.run_id,
                            "frame": self.frame_hash, "requirements": self.requirement_hashes,
                            "verifier": self.verifier, "expires": self.expires_at, "nonce": self.nonce})


def mint_authority_token(token_type: str, *, candidate_id: str, run_id: str, frame_hash: str,
                         evidence: dict[str, str], verifier: str, expires_at: str, nonce: str) -> AuthorityToken:
    required = SOURCE_OWNERSHIP_REQUIREMENTS if token_type == "SOURCE_OWNERSHIP_TOKEN" else REPAIR_LICENSE_REQUIREMENTS if token_type == "REPAIR_LICENSE_TOKEN" else ()
    missing = [name for name in required if not evidence.get(name)]
    if missing:
        raise ValueError(f"missing {token_type} evidence: {','.join(missing)}")
    if token_type == "REPAIR_LICENSE_TOKEN" and evidence.get("source_ownership_token", "").startswith("generic-prefix"):
        raise ValueError("repair license requires a concrete source ownership token")
    return AuthorityToken(token_type, candidate_id, run_id, frame_hash, tuple(sorted(evidence.items())), verifier, expires_at, nonce)
