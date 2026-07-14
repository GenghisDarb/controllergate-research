from __future__ import annotations

from controllergate.reactions.stable_identity import stable_hash


def seal_deployment(records: list[dict[str, object]]) -> dict[str, object]:
    passed = any(row.get("status") == "ROLLBACK_DRILL_PASSED" for row in records)
    value = {"status": "DEPLOYMENT_READINESS_RECORDED" if passed else "CANARY_REJECTED",
             "production_deployment": False, "records": records}
    value["proof_hash"] = stable_hash(value)
    return value
