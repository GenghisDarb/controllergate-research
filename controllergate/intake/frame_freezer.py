from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from controllergate.core.evidence import hash_record


def freeze_frame(records: list[dict[str, Any]], *, maximum: int = 12, random_seed: int = 74019) -> dict[str, Any]:
    selected = records[:maximum]
    freeze_time = datetime.now(timezone.utc).isoformat()
    frozen = [{**item, "frame_position": index, "frame_freeze_timestamp": freeze_time} for index, item in enumerate(selected)]
    frame_hash = hash_record(frozen)
    return {"status": "PASS" if len(frozen) >= 12 else "PARTIAL", "frame_freeze_timestamp": freeze_time, "candidate_count": len(frozen), "candidates": frozen, "frame_hash": frame_hash, "random_seed": random_seed, "no_post_freeze_issue_reread": True, "adaptive_replenishment": False}
