from __future__ import annotations

from .evidence import write_json_deterministic


def write_claim_boundary(path: str, boundary: dict[str, object]) -> None:
    write_json_deterministic(path, boundary)


def enforce_no_full_scoring(boundary: dict[str, object]) -> bool:
    return boundary.get("full_scoring") == "NOT_RUN/disallowed"


def enforce_no_self_maintaining_claim(boundary: dict[str, object]) -> bool:
    return boundary.get("self_maintaining_software", boundary.get("self_maintaining_software_status")) == "false/not_demonstrated"


def enforce_no_memory_lift_without_matched_null(boundary: dict[str, object]) -> bool:
    return boundary.get("memory_lift", boundary.get("memory_lift_status")) == "undemonstrated" or boundary.get("matched_null_experiment_attempted") is True


def classify_evidence_level(boundary: dict[str, object]) -> str:
    return str(boundary.get("evidence_level", "bounded_research_evidence"))
