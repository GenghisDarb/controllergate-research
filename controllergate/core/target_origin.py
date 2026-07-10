from __future__ import annotations

from typing import Any


def verify_target_origin_mode(mode: str, record: dict[str, Any]) -> dict[str, Any]:
    if mode not in {"pinned_source_mode", "pinned_wheel_mode"}:
        return {"status": "BLOCK", "blocker": "mixed_target_origin_mode_rejected"}
    origin = str(record.get("origin") or "")
    if mode == "pinned_source_mode":
        passed = origin.startswith("/source/nbclient/") and record.get("source_hash_match") is True and record.get("source_read_only") is True and record.get("git_directory_present") is False
    else:
        passed = origin.startswith("/venv/") and "/site-packages/nbclient/" in origin and record.get("wheel_hash_verified") is True and record.get("source_on_sys_path") is False
    return {"status": "PASS" if passed else "BLOCK", "mode": mode, "origin": origin, "blocker": None if passed else f"{mode}_identity_failed"}
