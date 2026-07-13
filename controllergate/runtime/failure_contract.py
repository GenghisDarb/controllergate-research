from __future__ import annotations

from typing import Any

from controllergate.runtime.failure_signature_v2 import semantic_failure_signature

FAILURE_CLASSES = {
    "CANDIDATE_FAILURE_REPRODUCED", "ENVIRONMENT_FAILURE_REPRODUCED", "HARNESS_FAILURE_REPRODUCED",
    "RESOURCE_TIMEOUT_REPRODUCED", "PROCESS_SIGNAL_REPRODUCED", "EMPTY_FAILURE_OUTPUT", "FAILURE_NOT_REPRODUCED",
}


def classify_failure(
    *, returncode: int, output: str, target: str, timed_out: bool = False,
    process_signal: int | None = None, ownership_events: list[str] | None = None,
) -> dict[str, Any]:
    signature = semantic_failure_signature(output, target=target, ownership_events=ownership_events)
    lower = output.lower()
    if returncode == 0:
        classification = "FAILURE_NOT_REPRODUCED"
    elif timed_out or returncode == 124:
        classification = "RESOURCE_TIMEOUT_REPRODUCED"
    elif process_signal is not None or returncode < 0:
        classification = "PROCESS_SIGNAL_REPRODUCED"
    elif not output.strip():
        classification = "EMPTY_FAILURE_OUTPUT"
    elif any(token in lower for token in ("modulenotfounderror", "importerror", "no matching distribution", "environment")):
        classification = "ENVIRONMENT_FAILURE_REPRODUCED"
    elif any(token in lower for token in ("fixture", "setup failed", "teardown failed")) and not ownership_events:
        classification = "HARNESS_FAILURE_REPRODUCED"
    elif any(token in lower for token in ("assertionerror", "traceback", "exception", "terminal state")) and ownership_events:
        classification = "CANDIDATE_FAILURE_REPRODUCED"
    else:
        classification = "HARNESS_FAILURE_REPRODUCED"
    return {
        "classification": classification,
        "returncode": returncode,
        "timed_out": timed_out,
        "process_signal": process_signal,
        "target": target,
        "ownership_evidence_present": bool(ownership_events),
        "signature": signature,
        "candidate_failure_evidence": classification == "CANDIDATE_FAILURE_REPRODUCED" and signature["status"] == "PASS",
    }


def duplicate_failure_contract(first: dict[str, Any], second: dict[str, Any]) -> dict[str, Any]:
    same_class = first.get("classification") == second.get("classification")
    first_sig = first.get("signature", {}).get("semantic_failure_signature")
    second_sig = second.get("signature", {}).get("semantic_failure_signature")
    same_signature = bool(first_sig) and first_sig == second_sig
    candidate = same_class and same_signature and first.get("classification") == "CANDIDATE_FAILURE_REPRODUCED"
    return {
        "status": "PASS" if same_class else "BLOCK",
        "equivalent_classification": same_class,
        "equivalent_nonempty_signature": same_signature,
        "candidate_failure_reproduced": candidate,
        "terminal_classification": first.get("classification") if same_class else "FAILURE_NOT_REPRODUCED",
    }
