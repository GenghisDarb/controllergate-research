from __future__ import annotations


TARGET_SENTINELS = ("TARGET_STARTED", "TARGET_COMPLETED")


def sentinel_coverage(required: list[str], observed: list[str]) -> dict[str, object]:
    missing = sorted(set(required) - set(observed))
    return {"status": "PASS" if not missing else "BLOCK", "missing": missing, "covered": not missing}
