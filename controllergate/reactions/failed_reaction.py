from __future__ import annotations

from dataclasses import dataclass, asdict

from .stable_identity import stable_hash


@dataclass(frozen=True)
class FailedReaction:
    event_id: str
    candidate_id: str
    outcome: str
    attempted_transition: str
    input_hashes: dict[str, str]
    catalyst_id: str
    regulators: list[str]
    failure_signature: str
    rollback_requirement: str
    reopen_condition: str
    new_evidence_required: str

    def record(self) -> dict[str, object]:
        value = asdict(self)
        value["terminal_status"] = "BLOCKED_EXACT"
        value["failed_reaction_hash"] = stable_hash(value)
        value["output_token_minted"] = False
        return value
