from controllergate.core.patch_quarantine import audit_patch_quarantine, build_patch_artifact_denylist


def test_null_ensemble_cannot_read_patch_diff_or_memory_ledger():
    denylist = build_patch_artifact_denylist(["configs/failure_memory_weight_ledger.json"])
    null_manifest = {
        "arm": "memory_disabled_null_seed_1",
        "allowed_context_paths": ["configs/failure_memory_weight_ledger.json"],
        "reads_successful_patch": False,
        "reads_patch_rationale": False,
        "uses_failure_memory": False,
    }
    assert audit_patch_quarantine([null_manifest], denylist)["status"] == "FAIL"


def test_null_ensemble_clean_context_passes_quarantine():
    denylist = build_patch_artifact_denylist(["configs/failure_memory_weight_ledger.json"])
    null_manifest = {
        "arm": "memory_disabled_null_seed_1",
        "allowed_context_paths": ["configs/clean_replication_batch_009.json"],
        "reads_successful_patch": False,
        "reads_patch_rationale": False,
        "uses_failure_memory": False,
    }
    assert audit_patch_quarantine([null_manifest], denylist)["status"] == "PASS"
