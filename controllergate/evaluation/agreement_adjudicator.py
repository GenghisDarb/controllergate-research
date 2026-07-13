from __future__ import annotations

from typing import Any

from controllergate.core.evidence import hash_record


def adjudicate(builder: dict[str, Any], critic: dict[str, Any], *, builder_source_hash: str, critic_source_hash: str) -> dict[str, Any]:
    independent = builder_source_hash != critic_source_hash and builder.get("evaluator") != critic.get("evaluator")
    hardcoded = builder.get("hardcoded_all_pass") is True or critic.get("hardcoded_all_pass") is True
    coordinates_match = builder.get("coordinates") == critic.get("coordinates")
    record: dict[str, Any] = {
        "status": "PASS" if independent and coordinates_match and not hardcoded else "BLOCK",
        "independent_modules": independent,
        "coordinates_match": coordinates_match,
        "hardcoded_all_pass_rejected": not hardcoded,
        "builder_source_hash": builder_source_hash,
        "critic_source_hash": critic_source_hash,
        "builder_report_hash": builder.get("report_hash"),
        "critic_report_hash": critic.get("report_hash"),
    }
    record["agreement_hash"] = hash_record(record)
    return record

