from __future__ import annotations


def connector_health(result: dict[str, object]) -> dict[str, object]:
    okay = result.get("status") in {"CONNECTOR_READ_EXECUTED", "CONNECTOR_WRITE_AUTHORITY_DISABLED"}
    return {"status": "CONNECTOR_HEALTH_CHECK_PASSED" if okay else "BLOCKED_EXACT_WITH_NEW_EVIDENCE",
            "source_result": result.get("status")}
