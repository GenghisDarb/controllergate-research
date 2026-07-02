from controllergate.core.target_intent_signature import evaluate_target_intent


def test_command_environment_variant_records_hashes_and_signatures():
    result = evaluate_target_intent(
        "GIT_DIR=.git darker --check src",
        "TypeError: unsupported operand type(s) for /: 'tuple' and 'str'",
    )
    assert len(result["expected_signature_hash"]) == 64
    assert len(result["actual_failure_signature_hash"]) == 64
    assert result["negative_precondition_hits"]
