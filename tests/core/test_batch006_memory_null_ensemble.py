from controllergate.core.fragment_patch import memory_separation_allowed


def test_memory_separation_cannot_be_claimed_when_routing_is_passive() -> None:
    assert memory_separation_allowed(routing_delta_active=False, separation_score=1.0) is False


def test_memory_separation_requires_threshold_and_active_routing() -> None:
    assert memory_separation_allowed(routing_delta_active=True, separation_score=0.94) is False
    assert memory_separation_allowed(routing_delta_active=True, separation_score=0.95) is True
