from __future__ import annotations

from collections.abc import Mapping
from typing import Any


TERMINAL_TYPES = {
    "CANDIDATE_FAILURE_REPRODUCED",
    "ENVIRONMENT_FAILURE_REPRODUCED",
    "PROVIDER_FAILURE_REPRODUCED",
    "HARNESS_FAILURE_REPRODUCED",
    "COLLECTION_FAILURE_REPRODUCED",
    "RESOURCE_TIMEOUT_REPRODUCED",
    "TARGET_NOT_FOUND",
    "EXPECTED_TARGET_PASS",
    "FAILURE_NOT_REPRODUCED",
}


def classify_capsule_failure(record: Mapping[str, Any]) -> dict[str, Any]:
    stage = str(record.get("stage", ""))
    returncode = record.get("return_code")
    timeout = bool(record.get("timeout_state"))
    signal = record.get("process_signal")
    exception = str(record.get("exception_class") or "")
    nodes = list(record.get("target_nodes") or [])
    tail = str(record.get("bounded_output_tail") or "")
    if stage == "provider_installation" and returncode not in {0, None}:
        classification = "PROVIDER_FAILURE_REPRODUCED"
    elif stage == "collection" and (not nodes or returncode not in {0, None}):
        classification = "TARGET_NOT_FOUND" if "not found" in tail.lower() or not nodes else "COLLECTION_FAILURE_REPRODUCED"
    elif timeout:
        classification = "RESOURCE_TIMEOUT_REPRODUCED"
    elif stage in {"fixture_setup", "harness"} or exception.startswith(("Harness", "Fixture")):
        classification = "HARNESS_FAILURE_REPRODUCED"
    elif stage == "test_execution" and returncode == 0:
        classification = "EXPECTED_TARGET_PASS"
    elif stage == "test_execution" and nodes and returncode not in {0, None} and ("assert" in tail.lower() or exception in {"AssertionError", "CandidateException"}):
        classification = "CANDIDATE_FAILURE_REPRODUCED"
    elif stage in {"environment", "runtime"} or signal or exception.startswith(("Environment", "Import", "ModuleNotFound")):
        classification = "ENVIRONMENT_FAILURE_REPRODUCED"
    else:
        classification = "FAILURE_NOT_REPRODUCED"
    return {
        "status": "PASS",
        "classification": classification,
        "candidate_failure_admissible": classification == "CANDIDATE_FAILURE_REPRODUCED",
        "timeout_alone_is_candidate_failure": False,
        "nonzero_and_repeated_hash_sufficient": False,
        "process_signal": signal,
        "allowed_terminal_type": classification in TERMINAL_TYPES,
    }
