from __future__ import annotations

from controllergate.reactions.stable_identity import stable_hash


LEVELS = {f"LEVEL_{i}_{name}" for i, name in enumerate(["ABSENT", "SCHEMA_ONLY", "CONTROLLED_FIXTURE_VALIDATED",
                                                         "HISTORICAL_REAL_REPLAY", "PROSPECTIVE_CONTROLLED_PILOT",
                                                         "BOUNDED_LIVE_OPERATION"])}


def adjudicate_dimension(dimension: str, level: str, evidence_ids: list[str], execution_record_ids: list[str],
                         log_hashes: list[str], independent_verifier: str, limitations: list[str],
                         next_promotion_requirement: str) -> dict[str, object]:
    if level not in LEVELS: raise ValueError("invalid_maturity_level")
    numeric = int(level.split("_", 2)[1])
    sufficient = numeric == 0 or (evidence_ids and execution_record_ids and log_hashes and independent_verifier)
    effective = level if sufficient else "LEVEL_0_ABSENT"
    value = {"dimension": dimension, "level": effective, "requested_level": level,
             "evidence_ids": evidence_ids, "execution_record_ids": execution_record_ids,
             "log_hashes": log_hashes, "independent_verifier": independent_verifier,
             "limitations": limitations, "next_promotion_requirement": next_promotion_requirement}
    value["maturity_hash"] = stable_hash(value)
    return value
