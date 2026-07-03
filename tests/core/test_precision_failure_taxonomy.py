from controllergate.core.failure_taxonomy import classify_failure


def test_materialization_block_maps_to_specific_taxonomy():
    record = classify_failure("manual_lock_environment_materialization_failed")
    assert record["status"] == "PASS"
    assert record["taxonomy_class"] == "dependency_materialization_failed"
    assert record["generic_failure_used"] is False
