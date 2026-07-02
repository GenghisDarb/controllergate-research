from __future__ import annotations

import json
from hashlib import sha256
from typing import Any


def _hash(value: Any) -> str:
    return sha256(json.dumps(value, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def classify_dependency_drift(active: dict[str, str], locked: dict[str, str]) -> dict[str, Any]:
    missing = sorted(set(locked) - set(active))
    extra = sorted(set(active) - set(locked))
    version_mismatch = sorted(name for name in set(active) & set(locked) if active[name] != locked[name])
    drift_detected = bool(missing or extra or version_mismatch)
    if drift_detected and (missing or version_mismatch):
        classification = "likely_environment_drift"
    elif drift_detected:
        classification = "mixed"
    else:
        classification = "likely_code_defect"
    return {
        "status": "PASS",
        "classification": classification,
        "drift_detected": drift_detected,
        "active_environment_hash": _hash(active),
        "locked_environment_hash": _hash(locked),
        "missing": missing,
        "extra": extra,
        "version_mismatch": version_mismatch,
        "restore_environment_before_code_repair": drift_detected,
        "undeclared_dependency_install_allowed": False,
    }
