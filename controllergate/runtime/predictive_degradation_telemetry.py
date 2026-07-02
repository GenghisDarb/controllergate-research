from __future__ import annotations

import json
from hashlib import sha256
from typing import Any

TELEMETRY_FIELDS = [
    "latency_ms",
    "memory_mb",
    "warning_count",
    "exception_near_miss_count",
    "flaky_drift_count",
    "dependency_churn_count",
    "function_level_degradation_markers",
]


def telemetry_schema() -> dict[str, Any]:
    return {"status": "PASS", "fields": TELEMETRY_FIELDS, "autonomous_repair_scheduled": False}


def maintenance_weights(record: dict[str, Any]) -> dict[str, Any]:
    weights = {
        "latency": min(int(record.get("latency_ms", 0)) // 100, 10),
        "memory": min(int(record.get("memory_mb", 0)) // 256, 10),
        "warnings": int(record.get("warning_count", 0)),
        "near_misses": int(record.get("exception_near_miss_count", 0)) * 2,
        "flaky_drift": int(record.get("flaky_drift_count", 0)) * 2,
        "dependency_churn": int(record.get("dependency_churn_count", 0)) * 2,
    }
    total = sum(weights.values())
    digest = sha256(json.dumps(record, sort_keys=True, default=str).encode("utf-8")).hexdigest()
    return {
        "status": "PASS",
        "input_hash": digest,
        "maintenance_weights": weights,
        "maintenance_weight_total": total,
        "autonomous_repair_triggered": False,
        "claim_boundary": "monitoring_and_scoring_only",
    }
