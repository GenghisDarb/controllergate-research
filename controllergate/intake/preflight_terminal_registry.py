from __future__ import annotations

from typing import Any

from controllergate.core.evidence import hash_record


ORDER = ("issue_snapshot", "source", "runtime", "target", "command", "provider_dry_lock", "collection", "contamination")


def terminal_record(candidate_id: str, stages: dict[str, dict[str, Any]]) -> dict[str, Any]:
    blocker = None
    for name in ORDER:
        stage = stages.get(name, {})
        if stage.get("status") not in {"PASS", "CLEAN"}:
            blocker = stage.get("blocker") or f"{name}_blocked"
            break
    admitted = blocker is None
    record = {
        "candidate_id": candidate_id,
        "status": "PREFLIGHT_PASS" if admitted else "PREFLIGHT_BLOCK",
        "admitted_to_execution_frame": admitted,
        "terminal_blocker": blocker,
        "stage_statuses": {name: stages.get(name, {}).get("status", "NOT_RUN") for name in ORDER},
        "target_execution_count": 0,
        "execution_frame_frozen": False,
    }
    record["terminal_hash"] = hash_record(record)
    return record
