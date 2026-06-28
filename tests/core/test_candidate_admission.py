from __future__ import annotations

from controllergate.core.candidate_admission import (
    candidate_admission_decision,
    coupled_dependency_projection_map,
    escape_boundary_risk,
    interlock_invariant_map,
    repairability_score,
    structural_navigation_map,
)


def test_candidate_scoring_and_admission():
    fields = {
        "target_test_present": True,
        "environment_file_present": True,
        "command_collects_target": True,
        "external_network_required": False,
        "semantic_failure_capture_available": True,
        "target_command_width": "single_node",
    }

    score = repairability_score(fields)
    assert score <= 0
    assert escape_boundary_risk(score) == "bounded_or_admissible"
    assert candidate_admission_decision(fields) == "admitted_native_replay_candidate"
    assert structural_navigation_map("candidate", fields)["candidate_id"] == "candidate"


def test_candidate_hard_blocks():
    assert candidate_admission_decision({"external_network_required": True}) == "rejected_external_network_dependency"
    assert candidate_admission_decision({"target_test_present": False}) == "rejected_missing_target_test"
    assert coupled_dependency_projection_map(["t.py"], ["src/a.py"], ["pyproject.toml"])["environment_files"] == [
        "pyproject.toml"
    ]
    assert interlock_invariant_map(["src/a.py"])["status"] == "PASS"
