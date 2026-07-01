from __future__ import annotations

import hashlib
import json
from pathlib import Path


def sha256_json_file(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def baseline_registry_drift_precheck_policy() -> dict[str, object]:
    return {
        "status": "PASS",
        "runs_before_candidate_acquisition": True,
        "full_replay_required": False,
        "expected_confirmed_native_repair_count": 4,
        "expected_issue_derived_repair_count": 0,
        "expected_current_protocol": "v2.13",
        "blockers": [
            "baseline_registry_drift_detected",
            "confirmed_repair_episode_registry_missing",
            "confirmed_repair_episode_count_mismatch",
            "claim_boundary_registry_drift",
        ],
    }


def baseline_registry_snapshot(registry_path: str | Path) -> dict[str, object]:
    path = Path(registry_path)
    if not path.is_file():
        return {"status": "BLOCK", "blocker": "confirmed_repair_episode_registry_missing"}
    registry = json.loads(path.read_text(encoding="utf-8"))
    episodes = registry.get("episodes", [])
    native = [item for item in episodes if isinstance(item, dict) and item.get("episode_type") == "external_non_ansible_source_only_target_repair"]
    issue = [item for item in episodes if isinstance(item, dict) and item.get("episode_type") == "issue_derived_repair_feasibility"]
    return {
        "status": "PASS",
        "registry_path": path.as_posix(),
        "registry_sha256": sha256_json_file(path),
        "confirmed_native_repair_count": len(native),
        "confirmed_issue_derived_repair_count": len(issue),
        "claim_boundary": registry.get("claim_boundary", {}),
        "current_protocol_version": "v2.13",
    }


def baseline_registry_drift_precheck(snapshot: dict[str, object]) -> dict[str, object]:
    if snapshot.get("status") != "PASS":
        return {"status": "BLOCK", "blocker": snapshot.get("blocker", "baseline_registry_drift_detected")}
    claim = snapshot.get("claim_boundary", {})
    errors = []
    if snapshot.get("confirmed_native_repair_count") != 4:
        errors.append("confirmed_repair_episode_count_mismatch")
    if snapshot.get("confirmed_issue_derived_repair_count") != 0:
        errors.append("confirmed_repair_episode_count_mismatch")
    if not isinstance(claim, dict) or claim.get("full_scoring") != "NOT_RUN/disallowed":
        errors.append("claim_boundary_registry_drift")
    if snapshot.get("current_protocol_version") != "v2.13":
        errors.append("baseline_registry_drift_detected")
    return {
        "status": "PASS" if not errors else "BLOCK",
        "blocker": None if not errors else errors[0],
        "registry_sha256_before_candidate_acquisition": snapshot.get("registry_sha256"),
        "confirmed_native_repair_count": snapshot.get("confirmed_native_repair_count"),
        "confirmed_issue_derived_repair_count": snapshot.get("confirmed_issue_derived_repair_count"),
        "current_protocol_version": snapshot.get("current_protocol_version"),
        "claim_boundary_registry_intact": not errors,
        "dry_run_hash_precheck_only": True,
    }
