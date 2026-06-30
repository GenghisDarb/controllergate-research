from __future__ import annotations

from typing import Any


TARGET_BEHAVIOR_MARKERS = (
    "skip_glob",
    "isort",
    "conf/settings",
    "test_isort_respects_skip_glob",
)

PRECONDITION_MARKERS = (
    "create_formatter",
    "StopIteration",
    "EntryPoint",
    "Can't find the Black package",
    "No module named 'black'",
    "formatter",
)


def classify_runtime_path(output: str, *, returncode: int | None) -> dict[str, Any]:
    found = [marker for marker in TARGET_BEHAVIOR_MARKERS if marker in output]
    missing = [marker for marker in TARGET_BEHAVIOR_MARKERS if marker not in output]
    precondition_hits = [marker for marker in PRECONDITION_MARKERS if marker in output]
    if returncode == 0:
        classification = "target_passed_after_normalization"
        target_behavior_reached = True
    elif precondition_hits:
        classification = "precondition_before_target_behavior"
        target_behavior_reached = False
    elif "ModuleNotFoundError" in output or "ImportError" in output:
        classification = "environment_dependency_block"
        target_behavior_reached = False
    elif {"skip_glob", "isort"}.issubset(set(found)):
        classification = "aligned_target_behavior_reached"
        target_behavior_reached = True
    else:
        classification = "ambiguous_runtime_path"
        target_behavior_reached = False
    return {
        "classification": classification,
        "target_behavior_reached": target_behavior_reached,
        "failure_before_target_behavior": classification in {"precondition_before_target_behavior", "environment_dependency_block", "ambiguous_runtime_path"},
        "semantic_markers_found": found,
        "semantic_markers_missing": missing,
        "precondition_markers_found": precondition_hits,
    }


def fragment_generation_authorized(runtime_classification: str, dual_projection_status: str) -> bool:
    return runtime_classification in {"aligned_target_behavior_reached", "target_behavior_reached_and_failed"} and dual_projection_status == "PASS"


def classify_declared_precondition_replay(output: str, *, returncode: int | None) -> dict[str, Any]:
    base = classify_runtime_path(output, returncode=returncode)
    if returncode == 0:
        status = "target_passed_after_declared_precondition_resolution"
    elif base["classification"] == "environment_dependency_block":
        status = "environment_dependency_failure_after_declared_extras"
    elif base["classification"] == "precondition_before_target_behavior":
        status = "target_precondition_unresolved_after_declared_extras"
    elif base["target_behavior_reached"] is True:
        status = "target_behavior_reached_and_failed"
    else:
        status = "ambiguous_runtime_path_after_declared_extras"
    return {
        **base,
        "status": status,
        "target_passed_after_declared_precondition_resolution": status == "target_passed_after_declared_precondition_resolution",
    }


EXPLICIT_COMPLETION_OUTCOMES = {
    "repair_success",
    "candidate_retired_precondition_unresolved",
    "candidate_retired_precondition_only",
    "candidate_retired_no_patchable_source",
    "candidate_retired_fragment_generation_failed",
    "candidate_retired_validation_failed",
    "blocked_forbidden_evidence_or_file",
}


def completion_decision(
    *,
    target_behavior_reached: bool,
    target_passed_after_normalization: bool,
    precondition_unresolved: bool,
    patch_generated: bool,
    target_validation_passed: bool,
    duplicate_replay_passed: bool,
    forbidden_evidence_or_file: bool = False,
) -> str:
    if forbidden_evidence_or_file:
        return "blocked_forbidden_evidence_or_file"
    if target_validation_passed and duplicate_replay_passed and patch_generated:
        return "repair_success"
    if patch_generated:
        return "candidate_retired_validation_failed"
    if target_passed_after_normalization:
        return "candidate_retired_precondition_only"
    if precondition_unresolved and not target_behavior_reached:
        return "candidate_retired_precondition_unresolved"
    if target_behavior_reached:
        return "candidate_retired_fragment_generation_failed"
    return "candidate_retired_precondition_unresolved"


def downstream_gate_violation(gates: list[dict[str, Any]]) -> bool:
    blocked_seen = False
    for gate in gates:
        status = gate.get("status")
        if blocked_seen and status == "PASS":
            return True
        if status in {"BLOCK", "FAILED"}:
            blocked_seen = True
    return False
