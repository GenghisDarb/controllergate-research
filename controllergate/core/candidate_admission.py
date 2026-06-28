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


def verified_native_candidate_for_repair(candidate: dict[str, object]) -> bool:
    return (
        candidate.get("decision") == "verified_native_candidate_pending_repair"
        and candidate.get("failure_replay_status") == "PRE_PATCH_FAILURE_OBSERVED"
        and bool(candidate.get("repo_url"))
        and bool(candidate.get("resolved_commit_sha") or candidate.get("commit_hint"))
        and bool(candidate.get("test_path_hint"))
    )


def repair_queue_admission_decision(candidate: dict[str, object]) -> dict[str, object]:
    admitted = verified_native_candidate_for_repair(candidate)
    return {
        "candidate_id": candidate.get("lead_id"),
        "status": "PASS" if admitted else "BLOCK",
        "admitted_to_repair_queue": admitted,
        "blocker": None if admitted else "candidate_not_verified_for_repair_generation",
    }
