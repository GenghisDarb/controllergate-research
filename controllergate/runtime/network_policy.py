from __future__ import annotations


def execution_network_policy() -> dict[str, object]:
    return {
        "network_mode": "none",
        "network_requests_allowed": False,
        "network_request_count_expected": 0,
        "phase": "offline_materialization_and_collection",
        "status": "PASS",
    }


def resolution_network_policy() -> dict[str, object]:
    return {
        "network_mode": "bridge",
        "network_requests_allowed": True,
        "authorization_reason": "download declared provider archives into content-addressed wheelhouse",
        "candidate_test_execution_allowed": False,
        "phase": "controlled_dependency_resolution",
        "status": "PASS",
    }
