from __future__ import annotations


def backtrack(trace: list[dict[str, object]], reason: str) -> dict[str, object]:
    if not trace:
        raise ValueError("backtrack_without_probe")
    return {"from_probe": trace[-1]["selected_probe"], "reason": reason, "next_action": "select_remaining_authorized_probe"}
