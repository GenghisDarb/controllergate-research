from controllergate.runtime.syntax_micro_rollback import validate_fragment


def test_syntax_invalid_fragment_triggers_micro_rollback():
    result = validate_fragment("def broken(:\n    pass\n")
    assert result["status"] == "ROLLBACK"
    assert result["syntax_valid"] is False
    assert result["accepted_repair_evidence"] is False
