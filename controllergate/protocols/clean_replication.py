from __future__ import annotations

from dataclasses import dataclass, asdict


@dataclass(frozen=True)
class CleanReplicationConfig:
    batch_id: str
    candidate_source_mode: str = "mixed"
    lead_pool_path: str = "inputs/clean_replication_batch_001_lead_pool.json"
    max_candidates_to_verify: int = 4
    max_candidate_verification_attempts: int = 20
    max_repos_attempted: int = 10
    max_candidate_or_issue_leads_attempted: int = 20
    max_repairs_to_attempt: int = 4
    max_successful_repairs_target: int = 2
    provenance_level: str = "strict"
    evidence_class: str = "native"
    matched_null_required: bool = False
    environment_resolution_required: bool = True
    max_environment_resolution_seconds_per_lead: int = 900
    full_scoring: bool = False


def default_clean_replication_config(batch_id: str = "clean_replication_batch_001") -> dict[str, object]:
    return asdict(CleanReplicationConfig(batch_id=batch_id))


def validate_clean_replication_config(config: dict[str, object]) -> dict[str, object]:
    lead_pool_path = config.get("lead_pool_path")
    ok = (
        config.get("full_scoring") is False
        and config.get("environment_resolution_required", True) is True
        and int(config.get("max_environment_resolution_seconds_per_lead", 0)) <= 900
        and (lead_pool_path is None or isinstance(lead_pool_path, str))
        and int(config.get("max_candidates_to_verify", 0)) <= 4
        and int(config.get("max_candidate_verification_attempts", 0)) <= 20
        and int(config.get("max_repos_attempted", 0)) <= 10
        and int(config.get("max_candidate_or_issue_leads_attempted", 0)) <= 20
        and int(config.get("max_repairs_to_attempt", 0)) <= 4
    )
    return {"status": "PASS" if ok else "FAIL", "batch_id": config.get("batch_id")}
