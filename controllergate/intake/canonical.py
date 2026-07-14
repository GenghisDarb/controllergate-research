from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from controllergate.reactions.token_kernel import ReactionToken


@dataclass(frozen=True)
class CanonicalIntake:
    candidate_id: str
    run_id: str

    def verify_identity(self, identity: dict[str, Any]) -> ReactionToken:
        if identity.get("status") != "PASS" or len(str(identity.get("source_commit_sha", ""))) != 40:
            raise ValueError("candidate identity not verified")
        return ReactionToken.mint(token_type="CANDIDATE_IDENTITY_VERIFIED_TOKEN", candidate_id=self.candidate_id, run_id=self.run_id, producer_event="candidate_identity_verified", input_tokens=(), payload=identity, independent_verifier="controllergate.intake.canonical")

    def source_acquired(self, identity_token: ReactionToken, source: dict[str, Any]) -> ReactionToken:
        if source.get("immutable") is not True or not source.get("tree_hash"):
            raise ValueError("immutable source acquisition required")
        return ReactionToken.mint(token_type="SOURCE_ACQUIRED_TOKEN", candidate_id=self.candidate_id, run_id=self.run_id, producer_event="source_acquired", input_tokens=(identity_token,), payload=source, independent_verifier="controllergate.intake.canonical")
