from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .core.frontier_state import verify_state_hash


class FrontierEngine:
    """Read-only interface to the unpromoted ControllerGate frontier state."""

    def __init__(self, repo_root: str | Path):
        self.repo_root = Path(repo_root)
        self.state_path = self.repo_root / "outputs" / "frontier" / "CURRENT_FRONTIER_STATE.json"
        self.index_path = self.repo_root / "outputs" / "post_v2_37_hardening_batch068g_tier2_metadata_command_orthology_hardening" / "candidate_state_index_batch068g.json"

    def status(self) -> dict[str, Any]:
        return json.loads(self.state_path.read_text(encoding="utf-8"))

    def validate(self) -> dict[str, Any]:
        state = self.status()
        index = json.loads(self.index_path.read_text(encoding="utf-8"))
        return {
            "status": "PASS" if verify_state_hash(state) and index.get("candidate_count") == 25 else "FAIL",
            "frontier_state_hash_valid": verify_state_hash(state),
            "candidate_count": index.get("candidate_count"),
            "frontier_protocol_promoted": False,
        }

    def plan(self, candidate_id: str) -> dict[str, Any]:
        index = json.loads(self.index_path.read_text(encoding="utf-8"))
        record = next((item for item in index["records"] if item["candidate_id"] == candidate_id), None)
        if record is None:
            return {"status": "BLOCK", "blocker": "frontier_candidate_unknown", "candidate_id": candidate_id}
        path = self.repo_root / record["state_path"]
        state = json.loads(path.read_text(encoding="utf-8"))
        return {
            "status": "PASS",
            "candidate_id": candidate_id,
            "tier": state["tier_label"],
            "terminal_state": state["terminal_state"],
            "next_allowed_action": state["next_allowed_action"],
            "provider_probe_authorized": state["tier_label"] == "Tier 3 static provider-command-probe authorization",
            "execution_authorized": False,
            "execution_blocker": "frontier_execution_not_authorized_static_planning_only",
            "state_hash": state["state_hash"],
        }
