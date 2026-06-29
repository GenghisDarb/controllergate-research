from __future__ import annotations

from controllergate.core.candidate_admission import target_node_admission_decision


def test_issue_fallback_not_needed_when_native_target_admitted() -> None:
    decision = target_node_admission_decision(
        {"status": "PASS", "selected_node": "src/darker/tests/test_main_isort.py::test_isort_respects_skip_glob"},
        {"status": "PRE_PATCH_FAILURE_OBSERVED", "environment_only_failure": False},
    )
    assert decision["status"] == "PASS"
    assert decision["admission_decision"] == "admitted_intended_target_node"


def test_passing_intended_target_blocks_native_repair_before_issue_fallback() -> None:
    decision = target_node_admission_decision(
        {"status": "PASS", "selected_node": "src/darker/tests/test_main_isort.py::test_isort_respects_skip_glob"},
        {"status": "PASSING_PRE_PATCH", "environment_only_failure": False},
    )
    assert decision["status"] == "BLOCK"
    assert decision["blocker"] == "intended_target_node_passed_pre_patch"
