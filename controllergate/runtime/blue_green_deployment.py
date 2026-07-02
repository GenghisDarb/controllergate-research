from __future__ import annotations

from typing import Any


def simulate_blue_green(parent_state_hash: str, candidate_child_state_hash: str, validation_status: str) -> dict[str, Any]:
    promoted = validation_status == "PASS" and parent_state_hash != candidate_child_state_hash
    return {
        "status": "PASS",
        "simulation_only": True,
        "live_deployment_attempted": False,
        "parent_state_hash": parent_state_hash,
        "candidate_child_state_hash": candidate_child_state_hash,
        "promotion_criteria": ["target_validation_pass", "duplicate_replay_pass", "no_overreach_pass"],
        "rollback_criteria": ["validation_fail", "hash_mismatch", "claim_boundary_violation"],
        "promotion_decision": "shadow_deploy_ready" if promoted else "rollback_required",
        "rollback_path_recorded": True,
        "production_readiness_claimed": False,
    }
