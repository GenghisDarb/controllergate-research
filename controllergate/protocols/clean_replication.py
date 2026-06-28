from __future__ import annotations

from dataclasses import dataclass, asdict


@dataclass(frozen=True)
class CleanReplicationConfig:
    batch_id: str
    candidate_source_mode: str = "mixed"
    max_candidates_to_verify: int = 4
    max_repairs_to_attempt: int = 4
    max_successful_repairs_target: int = 2
    provenance_level: str = "strict"
    evidence_class: str = "native"
    matched_null_required: bool = False
    full_scoring: bool = False


def default_clean_replication_config(batch_id: str = "clean_replication_batch_001") -> dict[str, object]:
    return asdict(CleanReplicationConfig(batch_id=batch_id))


def validate_clean_replication_config(config: dict[str, object]) -> dict[str, object]:
    ok = config.get("full_scoring") is False and config.get("max_candidates_to_verify", 0) <= 4 and config.get("max_repairs_to_attempt", 0) <= 4
    return {"status": "PASS" if ok else "FAIL", "batch_id": config.get("batch_id")}
