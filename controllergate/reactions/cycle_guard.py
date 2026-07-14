from __future__ import annotations

from .stable_identity import stable_hash


class CycleGuard:
    def __init__(self) -> None:
        self._seen: set[str] = set()

    def decide(self, *, candidate_id: str, event_id: str, input_hashes: list[str], provider: str,
               command: str, blocker: str | None, evidence: list[str], new_evidence: bool = False,
               regulator_changed: bool = False, authorized_duplicate: bool = False) -> dict[str, object]:
        fingerprint = stable_hash([candidate_id, event_id, input_hashes, provider, command, blocker, evidence])
        repeated = fingerprint in self._seen
        allowed = not repeated or new_evidence or regulator_changed or authorized_duplicate
        if allowed:
            self._seen.add(fingerprint)
        return {"status": "PASS" if allowed else "BLOCK", "fingerprint": fingerprint,
                "repeated": repeated, "new_evidence": new_evidence,
                "regulator_changed": regulator_changed, "authorized_duplicate": authorized_duplicate,
                "exact_blocker": None if allowed else "reaction_cycle_without_new_evidence"}
