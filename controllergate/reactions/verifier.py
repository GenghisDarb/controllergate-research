from __future__ import annotations

from .event import ReactionResult


def verify_result(result: ReactionResult) -> dict[str, object]:
    outcome = result.event_record.get("outcome")
    token_valid = (outcome == "REACTION_COMPLETED") == (result.output_token is not None)
    failure_valid = (outcome != "REACTION_COMPLETED") == (result.failure is not None)
    return {"status": "PASS" if token_valid and failure_valid else "BLOCK",
            "token_contract_valid": token_valid, "failed_reaction_contract_valid": failure_valid}
