from __future__ import annotations

from controllergate.core.clean_repair import matched_null_ensemble_score, memory_routing_delta


def _run(status: str) -> dict[str, object]:
    return {
        "candidate_id": "candidate_x",
        "repo_url": "https://example.test/repo",
        "commit_sha": "a" * 40,
        "target_test_path": "tests/test_target.py",
        "target_validation_status": status,
        "duplicate_replay_status": status,
    }


def test_no_relevant_memory_keeps_delta_passive():
    result = memory_routing_delta({"relevant_markers": []})

    assert result["routing_delta_active"] is False
    assert result["blocker"] == "no_relevant_failure_memory_available"


def test_relevant_memory_must_change_routing_to_be_active():
    result = memory_routing_delta({"relevant_markers": ["PINNED_EDGE"]})

    assert result["routing_delta_active"] is False
    assert result["blocker"] == "failure_memory_markers_passive"


def test_passive_memory_delta_forces_score_zero():
    score = matched_null_ensemble_score(
        _run("PASS"),
        [_run("FAIL") for _ in range(5)],
        memory_routing_delta({"relevant_markers": ["PINNED_EDGE"]}),
    )

    assert score["matched_null_ensemble_separation_score"] == 0.0
    assert score["preliminary_single_candidate_memory_separation_evidence"] is False
