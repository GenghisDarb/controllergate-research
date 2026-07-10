from __future__ import annotations

from typing import Any

from controllergate.core.evidence import hash_record
from .interlock_registry import HANDLERS, POLICIES, VERIFIERS
from .interlock_types import InterlockInput


def evaluate_interlocks(
    interlock_ids: list[str], *, candidate_id: str, prior_state: str,
    proposed_next_state: str, evidence: dict[str, Any], evidence_hashes: list[str],
) -> dict[str, Any]:
    records = []
    for interlock_id in interlock_ids:
        inp = InterlockInput(interlock_id, candidate_id, prior_state, proposed_next_state, evidence, tuple(evidence_hashes))
        output = HANDLERS[interlock_id](inp)
        verification = VERIFIERS[interlock_id](inp, output)
        records.append({"interlock_id": interlock_id, "handler": output.as_dict(), "verifier": verification.as_dict(), "policy_hash": hash_record(POLICIES[interlock_id])})
    passed = all(row["handler"]["decision"] == "PASS" and row["verifier"]["status"] == "PASS" for row in records)
    return {"status": "PASS" if passed else "BLOCK", "records": records, "evaluated_count": len(records)}
