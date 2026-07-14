from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Iterable

from controllergate.state.integrity import canonical_hash


TOKEN_ORDER = (
    "CANDIDATE_IDENTITY_VERIFIED_TOKEN", "ISSUE_SNAPSHOT_VERIFIED_TOKEN", "SOURCE_ACQUIRED_TOKEN",
    "RUNTIME_ATTESTED_TOKEN", "PROVIDER_EXECUTION_READY_TOKEN", "TARGET_OR_REPRODUCER_VERIFIED_TOKEN",
    "COMMAND_AUTHORITY_VERIFIED_TOKEN", "DUPLICATE_FAILURE_REPRODUCED_TOKEN", "CAUSAL_OWNERSHIP_TOKEN",
    "AST_CONTACT_DOMAIN_TOKEN", "REPAIR_LICENSE_TOKEN", "PATCH_APPLIED_TOKEN", "VALIDATION_PASSED_TOKEN",
    "DUPLICATE_CLEAN_REPLAY_TOKEN", "ROLLBACK_READY_TOKEN", "PROOF_APPENDED_TOKEN",
    "COUNT_DECISION_TOKEN", "CANARY_HEALTH_TOKEN", "TERMINAL_MEMORY_TOKEN",
)


@dataclass(frozen=True)
class ReactionToken:
    token_type: str
    candidate_id: str
    run_id: str
    producer_event: str
    input_token_hashes: tuple[str, ...]
    payload_identity: str
    independent_verifier: str
    created_time: str
    token_hash: str

    @classmethod
    def mint(cls, *, token_type: str, candidate_id: str, run_id: str, producer_event: str,
             input_tokens: Iterable["ReactionToken"], payload: Any, independent_verifier: str,
             reaction_status: str = "PASS") -> "ReactionToken":
        if reaction_status != "PASS":
            raise ValueError("failed reaction cannot mint output token")
        if token_type not in TOKEN_ORDER:
            raise ValueError("unknown reaction token type")
        inputs = tuple(token.token_hash for token in input_tokens)
        created = datetime.now(timezone.utc).isoformat()
        unsigned = {
            "token_type": token_type, "candidate_id": candidate_id, "run_id": run_id,
            "producer_event": producer_event, "input_token_hashes": inputs,
            "payload_identity": canonical_hash(payload), "independent_verifier": independent_verifier,
            "created_time": created,
        }
        return cls(**unsigned, token_hash=canonical_hash(unsigned))

    def record(self) -> dict[str, Any]:
        return asdict(self)


def require_tokens(tokens: Iterable[ReactionToken], required: Iterable[str], *, candidate_id: str, run_id: str) -> None:
    values = list(tokens)
    present = {token.token_type for token in values if token.candidate_id == candidate_id and token.run_id == run_id}
    missing = set(required) - present
    if missing:
        raise ValueError(f"missing reaction tokens: {','.join(sorted(missing))}")
    if len({token.token_hash for token in values}) != len(values):
        raise ValueError("reaction token cycle or duplicate detected")
