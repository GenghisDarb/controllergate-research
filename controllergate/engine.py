from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .core.frontier_state import verify_state_hash


class FrontierEngine:
    """Read-only interface to the validated ControllerGate frontier state."""

    def __init__(self, repo_root: str | Path):
        self.repo_root = Path(repo_root)
        self.state_path = self.repo_root / "outputs" / "frontier" / "CURRENT_FRONTIER_STATE.json"
        semantic = self.repo_root / "outputs" / "post_v2_37_hardening_batch068h_semantic_pathway_secure_provider_probe" / "candidate_state_index_batch068h.json"
        legacy = self.repo_root / "outputs" / "post_v2_37_hardening_batch068g_tier2_metadata_command_orthology_hardening" / "candidate_state_index_batch068g.json"
        self.index_path = semantic if semantic.is_file() else legacy

    def status(self) -> dict[str, Any]:
        return json.loads(self.state_path.read_text(encoding="utf-8"))

    def validate(self) -> dict[str, Any]:
        state = self.status()
        index = json.loads(self.index_path.read_text(encoding="utf-8"))
        return {
            "status": "PASS" if verify_state_hash(state) and index.get("candidate_count") == 25 else "FAIL",
            "frontier_state_hash_valid": verify_state_hash(state),
            "candidate_count": index.get("candidate_count"),
            "frontier_protocol_promoted": bool(state.get("frontier_engine_protocol_promoted", False)),
        }

    def plan(self, candidate_id: str) -> dict[str, Any]:
        frontier = self.status()
        index = json.loads(self.index_path.read_text(encoding="utf-8"))
        record = next((item for item in index["records"] if item["candidate_id"] == candidate_id), None)
        if record is None:
            return {"status": "BLOCK", "blocker": "frontier_candidate_unknown", "candidate_id": candidate_id}
        path = self.repo_root / record["state_path"]
        state = json.loads(path.read_text(encoding="utf-8"))
        interlock_runtime = str(frontier.get("validated_current_protocol", "")).startswith(("v2.16", "v2.17", "v2.18"))
        return {
            "status": "PASS",
            "candidate_id": candidate_id,
            "tier": state["tier_label"],
            "terminal_state": frontier.get("provider_probe_classification") if interlock_runtime else state.get("terminal_state", state.get("candidate_state")),
            "next_allowed_action": frontier.get("next_safe_action") if interlock_runtime else state["next_allowed_action"],
            "provider_probe_authorized": False if interlock_runtime else state["tier_label"] == "Tier 3 static provider-command-probe authorization",
            "execution_authorized": False,
            "execution_blocker": "interlock_runtime_requires_next_authorized_evidence_lane" if interlock_runtime else "frontier_execution_not_authorized_static_planning_only",
            "state_hash": state["state_hash"],
        }
