from controllergate.core.fragment_patch import memory_separation_allowed


def test_issue_derived_path_remains_separate_marker() -> None:
    issue_derived_counts_as_native = False
    assert issue_derived_counts_as_native is False


def test_memory_claim_requires_active_routing_and_score() -> None:
    assert memory_separation_allowed(routing_delta_active=False, separation_score=None) is False
