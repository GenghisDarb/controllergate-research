from __future__ import annotations

from controllergate.runtime.openbb_docker_supervisor import encode_stdout_result, parse_stdout_result
from controllergate.runtime.poetry_isolation import application_socket_denial_policy, powershell_invocation


def test_openbb_structured_result_round_trip_needs_no_host_evidence_mount():
    value = {"status": "BLOCKED_EXACT_WITH_NEW_EVIDENCE", "reason": "fixture"}
    assert parse_stdout_result(encode_stdout_result(value)) == value


def test_poetry_powershell_arguments_and_network_policy_are_separate():
    command = powershell_invocation("C:/Program Files/Poetry/bin/poetry.exe")
    assert command[-3:] == ["C:/Program Files/Poetry/bin/poetry.exe", "init", "-n"]
    policy = application_socket_denial_policy()
    assert policy["status"] == "PASS" and policy["environment_marker_only"] is False
