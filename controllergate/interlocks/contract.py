from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class InterlockContract:
    interlock_id: str
    canonical_inputs: tuple[str, ...]
    allowed_states: tuple[str, ...] = ("PASS",)
    forbidden_states: tuple[str, ...] = ("BLOCK", "FAIL", "MISSING")
    negative_regulator: str = "block_on_missing_or_forbidden_evidence"
    output_token: str = "INTERLOCK_AUDIT_TOKEN"
    positive_test: str = "verified evidence passes"
    negative_test: str = "missing or forbidden evidence blocks"
    reopen_condition: str = "provide verified evidence"

    @property
    def can_authorize_patch(self) -> bool:
        return False
