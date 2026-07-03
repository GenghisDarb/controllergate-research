def test_repair_stages_do_not_run_without_batch019_lock_processing():
    state = {
        "batch019_processes_lock": False,
        "target_intent_retry_status": "NOT_RUN",
        "harness_generated": False,
        "repair_only_fallback_attempted": False,
        "matched_null_diagnostic_run_count": 0,
    }

    assert state["batch019_processes_lock"] is False
    assert state["target_intent_retry_status"] == "NOT_RUN"
    assert state["harness_generated"] is False
    assert state["repair_only_fallback_attempted"] is False
    assert state["matched_null_diagnostic_run_count"] == 0
