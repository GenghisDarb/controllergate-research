from controllergate.core.patch_quarantine import audit_patch_quarantine, build_patch_artifact_denylist


def test_batch008_patch_artifacts_are_denied_to_all_arms():
    denylist = build_patch_artifact_denylist()
    denied = set(denylist["denylist"])
    assert "outputs/clean_replication_batch_008/assembled_patch_batch008.diff" in denied
    assert "outputs/clean_replication_batch_008/fragment_patch_candidates_batch008.json" in denied
    manifests = [
        {"arm": "memory_enabled_arm", "allowed_context_paths": ["configs/clean_replication_batch_009.json"], "reads_successful_patch": False, "reads_patch_rationale": False},
        {"arm": "memory_disabled_null_seed_0", "allowed_context_paths": ["outputs/clean_replication_batch_008/target_replay_after_declared_extras.json"], "reads_successful_patch": False, "reads_patch_rationale": False},
    ]
    assert audit_patch_quarantine(manifests, denylist)["status"] == "PASS"


def test_arm_access_to_batch008_patch_diff_fails_quarantine():
    denylist = build_patch_artifact_denylist()
    manifest = {
        "arm": "memory_enabled_arm",
        "allowed_context_paths": ["outputs/clean_replication_batch_008/assembled_patch_batch008.diff"],
        "reads_successful_patch": False,
        "reads_patch_rationale": False,
    }
    assert audit_patch_quarantine([manifest], denylist)["blocker"] == "matched_null_patch_quarantine_failed"
