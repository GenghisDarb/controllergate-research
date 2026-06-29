from __future__ import annotations

from controllergate.core.clean_repair import matched_null_score


def _arm(status: str) -> dict[str, object]:
    return {
        "candidate_id": "darker_stdin_filename",
        "repo_url": "https://github.com/akaihola/darker",
        "commit_sha": "6ecafca023a354fe7d9539d1d20bf10391bdb24a",
        "target_test_path": "src/darker/tests/test_main_stdin_filename.py",
        "target_validation_status": status,
        "duplicate_replay_status": status,
    }


def test_equal_success_gives_no_memory_separation():
    result = matched_null_score(_arm("PASS"), _arm("PASS"), memory_active=True, arm_b_clean=True)

    assert result["matched_null_separation_score"] == 0.0
    assert result["preliminary_single_candidate_memory_separation_evidence"] is False


def test_passive_memory_gives_no_memory_separation():
    result = matched_null_score(_arm("PASS"), _arm("FAIL"), memory_active=False, arm_b_clean=True)

    assert result["matched_null_separation_score"] == 0.0
    assert result["preliminary_single_candidate_memory_separation_evidence"] is False


def test_arm_a_success_can_count_only_when_memory_active_and_arm_b_clean():
    result = matched_null_score(_arm("PASS"), _arm("FAIL"), memory_active=True, arm_b_clean=True)

    assert result["matched_null_separation_score"] == 1.0
    assert result["preliminary_single_candidate_memory_separation_evidence"] is True


def test_unmatched_arms_do_not_compute_score():
    arm_b = _arm("FAIL")
    arm_b["commit_sha"] = "b" * 40

    result = matched_null_score(_arm("PASS"), arm_b, memory_active=True, arm_b_clean=True)

    assert result["status"] == "NOT_COMPUTED"
    assert result["blocker"] == "matched_null_arms_not_comparable"
