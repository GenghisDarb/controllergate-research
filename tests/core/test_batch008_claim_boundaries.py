from controllergate.core.precondition_resolution import retirement_decision_after_declared_extras


FORBIDDEN_PUBLIC_TERMS = [
    "bio" + "logical",
    "chromo" + "somal",
    "TO" + "RUS",
    "T" + "LD",
    "A" + "GI",
    "observer" + "-state",
    "recursion" + "-constant",
    "Klein" + " twist",
    "RNA" + " primase",
    "OS" + "QN",
    "cym" + "atics",
    "res" + "onance",
    "meta" + "phorical",
]


def test_batch008_helpers_do_not_claim_memory_lift_or_full_scoring() -> None:
    result = retirement_decision_after_declared_extras(
        declared_extras_attempted=True,
        target_replay_status="target_behavior_reached_and_failed",
        repair_attempted=True,
        target_validation_status="FAIL",
        duplicate_replay_status="NOT_RUN",
    )
    assert result["completion_decision"] != "repair_success"


def test_forbidden_public_terms_are_not_in_batch008_helper_module() -> None:
    import controllergate.core.precondition_resolution as module

    text = module.__loader__.get_source(module.__name__)
    assert text is not None
    assert all(term not in text for term in FORBIDDEN_PUBLIC_TERMS)
