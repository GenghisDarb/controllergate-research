from __future__ import annotations


def repairability_score(fields: dict[str, object]) -> int:
    score = 0
    if fields.get("external_network_required"):
        score += 5
    if not fields.get("target_test_present", False):
        score += 5
    if not fields.get("environment_file_present", False):
        score += 5
    if not fields.get("command_collects_target", False):
        score += 5
    if fields.get("semantic_failure_capture_available"):
        score -= 3
    if fields.get("target_command_width") == "single_node":
        score -= 4
    elif fields.get("target_command_width") == "single_file":
        score -= 1
    return score


def escape_boundary_risk(score: int) -> str:
    return "escape_boundary_risk" if score >= 5 else "bounded_or_admissible"


def structural_navigation_map(candidate_id: str, fields: dict[str, object]) -> dict[str, object]:
    score = repairability_score(fields)
    return {"candidate_id": candidate_id, **fields, "repairability_score": score, "escape_boundary_risk": escape_boundary_risk(score)}


def coupled_dependency_projection_map(target_test_files: list[str], source_files: list[str], environment_files: list[str]) -> dict[str, object]:
    return {"target_test_files": target_test_files, "candidate_source_files_from_traceback": source_files, "environment_files": environment_files}


def interlock_invariant_map(source_files: list[str]) -> dict[str, object]:
    return {"status": "PASS" if source_files else "BLOCK", "invariants": [{"file": path, "patchable": True} for path in source_files]}


def candidate_admission_decision(fields: dict[str, object]) -> str:
    score = repairability_score(fields)
    if fields.get("external_network_required"):
        return "rejected_external_network_dependency"
    if not fields.get("target_test_present", False):
        return "rejected_missing_target_test"
    if score >= 5:
        return "rejected_escape_boundary_risk"
    return "admitted_native_replay_candidate"
