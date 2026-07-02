from controllergate.core.lock_sequence_registry import registry_records, validate_operation


def test_lock_sequence_registry_blocks_operations_with_missing_locks():
    blocked = validate_operation("repair_candidate_admission", ["provenance", "projection"])
    assert blocked["status"] == "BLOCK"
    assert "perturbation" in blocked["missing_locks"]
    passed = validate_operation("repair_candidate_admission", ["provenance", "projection", "perturbation", "null"])
    assert passed["status"] == "PASS"
    assert registry_records()["status"] == "PASS"
