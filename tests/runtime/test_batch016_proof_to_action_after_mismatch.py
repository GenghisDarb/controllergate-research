import json
from pathlib import Path


def test_proof_to_action_after_mismatch_does_not_admit_patch():
    path = Path("outputs/clean_replication_batch_016/proof_to_action_issue112_mismatch.json")
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data["action_type"] in {"environment_restore_required", "sandbox_probe_required", "manual_seed_refinement_required", "safe_stop_required"}
        assert data["action_type"] not in {"patch_ready_for_review", "shadow_deploy_ready", "repair_candidate_admitted"}
        assert data["status"] == "PASS"
