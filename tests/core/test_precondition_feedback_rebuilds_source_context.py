def test_source_context_must_be_rebuilt_after_precondition_normalization() -> None:
    feedback = {
        "precondition_resolution_changed_environment": True,
        "source_context_rebuilt_after_precondition": True,
        "stale_source_context_reused": False,
    }
    assert feedback["source_context_rebuilt_after_precondition"] is True
    assert feedback["stale_source_context_reused"] is False
