from __future__ import annotations

from controllergate.core.clean_repair import matched_null_ensemble_policy, matched_null_ensemble_score


def _run(status: str) -> dict[str, object]:
    return {
        "candidate_id": "candidate_x",
        "repo_url": "https://example.test/repo",
        "commit_sha": "a" * 40,
        "target_test_path": "tests/test_target.py",
        "target_validation_status": status,
        "duplicate_replay_status": status,
    }


def test_null_ensemble_defaults_to_at_least_five_runs():
    policy = matched_null_ensemble_policy()

    assert policy["null_ensemble_size"] >= 5
    assert policy["each_null_run_memory_disabled"] is True


def test_null_ensemble_success_rate_one_scores_zero():
    result = matched_null_ensemble_score(
        _run("PASS"),
        [_run("PASS") for _ in range(5)],
        {"routing_delta_active": True},
    )

    assert result["null_ensemble_success_rate"] == 1.0
    assert result["matched_null_ensemble_separation_score"] == 0.0
    assert result["preliminary_single_candidate_memory_separation_evidence"] is False


def test_memory_enabled_success_against_all_failed_nulls_can_separate():
    result = matched_null_ensemble_score(
        _run("PASS"),
        [_run("FAIL") for _ in range(5)],
        {"routing_delta_active": True},
    )

    assert result["matched_null_ensemble_separation_score"] == 1.0
    assert result["preliminary_single_candidate_memory_separation_evidence"] is True
