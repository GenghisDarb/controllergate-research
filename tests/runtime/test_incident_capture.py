from controllergate.runtime.incident_capture import capture_incident


def test_incident_bundle_hashes_are_deterministic_and_secrets_redacted():
    kwargs = {
        "command": ["python", "-m", "pytest"],
        "cwd": "C:/tmp/work",
        "env": {"API_TOKEN": "secret", "PATH": "bin"},
        "stack_trace": "Traceback\nException: boom",
        "dependency_metadata": {"drift_detected": False},
        "source_closure_hint": ["pkg/mod.py"],
        "timestamp": "2026-07-02T00:00:00+00:00",
        "incident_id": "incident-1",
    }
    first = capture_incident(**kwargs)
    second = capture_incident(**kwargs)
    assert first["incident_bundle_hash"] == second["incident_bundle_hash"]
    assert first["redacted_environment"]["API_TOKEN"] == "<redacted>"
    assert first["secrets_captured"] is False
    assert first["incident_classification"] == "runtime_failure"
