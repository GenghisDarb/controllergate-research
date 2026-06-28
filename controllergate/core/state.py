from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .evidence import write_json_deterministic

VALID_STATUSES = {"PASS", "BLOCKED", "NOT_RUN", "NOT_APPLICABLE", "FAILED"}


def create_consolidated_state(**fields: Any) -> dict[str, Any]:
    state = {
        "lane_id": fields.get("lane_id"),
        "lane_type": fields.get("lane_type"),
        "status": fields.get("status", "BLOCKED"),
        "exact_blocker": fields.get("exact_blocker"),
        "current_protocol_version": fields.get("current_protocol_version", "v2.13"),
        "raw_evidence_files": fields.get("raw_evidence_files", []),
        "diagnostic_files": fields.get("diagnostic_files", []),
        "deprecated_files": fields.get("deprecated_files", []),
        "next_actions": fields.get("next_actions", []),
    }
    state.update(fields)
    return state


def load_consolidated_state(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def append_raw_evidence_reference(state: dict[str, Any], path: str, sha256: str | None = None) -> dict[str, Any]:
    state.setdefault("raw_evidence_files", []).append({"path": path, "sha256": sha256})
    return state


def distinguish_status(value: str) -> bool:
    return value in VALID_STATUSES


def save_consolidated_state(path: str | Path, state: dict[str, Any]) -> None:
    write_json_deterministic(path, state)
