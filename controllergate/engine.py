from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .core.frontier_state import verify_state_hash
from .current_pathway import current_pathway
from .product.cycle import run_controlled_cycle
from .product.manifest import load_manifest
from .state.run_state import RunState
from .state.state_store import StateStore


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
        interlock_runtime = str(frontier.get("validated_current_protocol", "")).startswith(("v2.16", "v2.17", "v2.18", "v2.19"))
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

    def execute(self, candidate_id: str, authorization_manifest: str | Path, checkpoint: str | Path) -> dict[str, Any]:
        index = json.loads(self.index_path.read_text(encoding="utf-8"))
        item = next((row for row in index["records"] if row["candidate_id"] == candidate_id), None)
        if item is None: return {"status": "BLOCK", "blocker": "frontier_candidate_unknown"}
        state = json.loads((self.repo_root / item["state_path"]).read_text(encoding="utf-8"))
        auth_path = Path(authorization_manifest)
        if not auth_path.is_file(): return {"status": "BLOCK", "blocker": "execution_authorization_manifest_required"}
        auth = json.loads(auth_path.read_text(encoding="utf-8"))
        from .runtime.maintenance_dispatcher import dispatch
        current = json.loads(self.state_path.parent.parent.joinpath("current/CURRENT_PROTOCOL_STATE.json").read_text(encoding="utf-8"))
        return dispatch(candidate_id=candidate_id, candidate_sha=str(state.get("candidate_sha")), current_state_hash=str(current.get("state_hash")), authorization_path=auth_path, plan_path=Path(auth.get("plan_path", "")), checkpoint_path=Path(checkpoint), event_ledger_path=Path(auth.get("event_ledger_path", "")))

    def execute_manifest(self, manifest_path: str | Path, checkpoint: str | Path, event_ledger: str | Path, authorization_store: str | Path) -> dict[str, Any]:
        path = Path(manifest_path)
        if not path.is_file(): return {"status": "BLOCK", "blocker": "candidate_manifest_required"}
        manifest = json.loads(path.read_text(encoding="utf-8"))
        from .runtime.maintenance_dispatcher import dispatch_candidate_manifest
        return dispatch_candidate_manifest(manifest=manifest, checkpoint_path=Path(checkpoint), event_ledger_path=Path(event_ledger), authorization_store=Path(authorization_store))


def run_manifest(manifest_path: str | Path) -> dict[str, Any]:
    """Canonical manifest admission boundary.

    External execution remains delegated to the pathway executor after a
    runtime-root attestation and explicit authorization are attached.
    """
    path = Path(manifest_path)
    if not path.is_file(): return {"status": "BLOCK", "exact_blocker": "manifest_missing"}
    manifest, validation = load_manifest(path)
    if validation["status"] != "PASS": return {"status": "BLOCK", "exact_blocker": "manifest_invalid", **validation}
    store = StateStore(Path(manifest["runtime_root"]) / "state")
    state = RunState(manifest["run_id"], str(validation["manifest_hash"]))
    if manifest.get("execution_mode") == "historical_non_counting":
        attestations = manifest.get("historical_attestations", {})
        failed = [name for name in ("source", "provider", "target") if attestations.get(name, {}).get("status") != "PASS"]
        if failed:
            state.status = "SAFE_ABSTENTION"
            state.blocker = f"historical_admission_blocked:{','.join(failed)}"
            state.evidence["historical_admission"] = {
                "execution_mode": "historical_non_counting",
                "attestations": attestations,
                "repair_count_increment": False,
            }
            store.save(state)
            return {"status": state.status, "run_id": state.run_id, "exact_blocker": state.blocker,
                    "completed_stages": [], "repair_count_increment": False,
                    "state_hash": state.record()["state_hash"]}
    store.save(state)
    return run_controlled_cycle(manifest, state, store, stop_after=manifest.get("stop_after"))


def resume_run(manifest_path: str | Path, run_id: str) -> dict[str, Any]:
    manifest, validation = load_manifest(manifest_path)
    if validation["status"] != "PASS": return {"status": "BLOCK", **validation}
    store = StateStore(Path(manifest["runtime_root"]) / "state")
    state = store.load(run_id)
    if manifest.get("execution_mode") == "historical_non_counting" and state.status == "SAFE_ABSTENTION":
        return {"status": state.status, "run_id": run_id, "completed_stages": state.completed_stages,
                "blocker": state.blocker, "repair_count_increment": False,
                "state_hash": state.record()["state_hash"]}
    return run_controlled_cycle(manifest, state, store)


def verify_run(manifest_path: str | Path, run_id: str) -> dict[str, Any]:
    manifest, validation = load_manifest(manifest_path)
    store = StateStore(Path(manifest["runtime_root"]) / "state")
    state = store.load(run_id); record = state.record()
    return {"status": "PASS" if state.status in {"CONTROLLED_PRODUCT_ALPHA_CYCLE_PASS", "SAFE_ABSTENTION"} else "BLOCK",
            "run_id": run_id, "idempotent": record == state.record(), "state_hash": record["state_hash"],
            "manifest_hash": validation.get("manifest_hash")}
