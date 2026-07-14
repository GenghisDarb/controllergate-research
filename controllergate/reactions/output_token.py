from __future__ import annotations

from dataclasses import dataclass

from .stable_identity import stable_hash


@dataclass(frozen=True)
class OutputToken:
    token_id: str
    event_id: str
    candidate_id: str
    output_identities: dict[str, str]
    verifier: str
    parent_hash: str | None

    @property
    def token_hash(self) -> str:
        return stable_hash({"token_id": self.token_id, "event_id": self.event_id,
                            "candidate_id": self.candidate_id, "output_identities": self.output_identities,
                            "verifier": self.verifier, "parent_hash": self.parent_hash})
