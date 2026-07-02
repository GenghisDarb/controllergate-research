from controllergate.runtime.blue_green_deployment import simulate_blue_green


def test_blue_green_deployment_is_simulated_only():
    result = simulate_blue_green("a" * 64, "b" * 64, "PASS")
    assert result["simulation_only"] is True
    assert result["live_deployment_attempted"] is False
    assert result["promotion_decision"] == "shadow_deploy_ready"
    assert result["production_readiness_claimed"] is False
