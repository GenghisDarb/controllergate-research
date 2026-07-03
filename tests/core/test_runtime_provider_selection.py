from controllergate.core.runtime_provider_registry import runtime_provider_registry
from controllergate.core.runtime_provider_selection import select_runtime_provider


def test_selection_falls_back_to_self_hosted_plan_without_verified_provider():
    decision = select_runtime_provider(runtime_provider_registry("3.7"), "3.7")
    assert decision["status"] == "BLOCK"
    assert decision["decision"] == "self_hosted_runtime_required"
    assert decision["blocker"] == "runtime_provider_exact_version_unavailable"
    assert decision["target_replay_allowed"] is False


def test_selection_accepts_only_verified_exact_family_provider():
    registry = runtime_provider_registry("3.7")
    registry["providers"].append(
        {
            "provider_id": "verified_python37",
            "provider_type": "hosted",
            "runtime_family": "3.7",
            "exact_runtime_verified": True,
        }
    )
    decision = select_runtime_provider(registry, "3.7")
    assert decision["status"] == "PASS"
    assert decision["selected_provider_id"] == "verified_python37"
    assert decision["target_replay_allowed"] is True

