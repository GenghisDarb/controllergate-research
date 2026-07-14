from __future__ import annotations

from datetime import datetime, timezone

from .health_contract import HealthContract


def monitor(executions: list[dict[str, object]], contract: HealthContract) -> dict[str, object]:
    passed = len(executions) >= contract.minimum_events and all(
        row.get("returncode") == contract.expected_returncode for row in executions)
    return {"status": "CANARY_HEALTH_WINDOW_PASSED" if passed else "CANARY_REJECTED",
            "event_count": len(executions), "skip_count": 0, "observed_at": datetime.now(timezone.utc).isoformat()}
