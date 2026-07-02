from controllergate.runtime.predictive_degradation_telemetry import maintenance_weights, telemetry_schema


def test_telemetry_produces_weights_without_autonomous_repair():
    schema = telemetry_schema()
    result = maintenance_weights({"latency_ms": 250, "warning_count": 2})
    assert schema["autonomous_repair_scheduled"] is False
    assert result["maintenance_weight_total"] > 0
    assert result["autonomous_repair_triggered"] is False
