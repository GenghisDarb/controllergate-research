from __future__ import annotations

from controllergate.core.clean_repair import no_overreach_validation, post_patch_constraint_revalidation
from controllergate.core.patch_safety import duplicate_replay_requires_three_of_three, target_validation_requires_exit_zero


def test_target_validation_requires_exit_status_zero():
    assert target_validation_requires_exit_zero(0)
    assert not target_validation_requires_exit_zero(1)


def test_duplicate_replay_requires_three_of_three():
    assert duplicate_replay_requires_three_of_three([0, 0, 0])
    assert not duplicate_replay_requires_three_of_three([0, 0])
    assert not duplicate_replay_requires_three_of_three([0, 1, 0])


def test_post_patch_revalidation_requires_same_patch_bytes():
    record = post_patch_constraint_revalidation(
        {"candidate_id": "candidate", "repo_url": "https://example.invalid/repo.git", "commit_sha": "1" * 40},
        {"repo_url": "https://example.invalid/repo.git", "commit_sha": "1" * 40},
        {"status": "PASS"},
        {"status": "PASS", "same_patch_bytes_across_replays": True},
    )
    assert record["status"] == "PASS"

    overreach = no_overreach_validation({"candidate_id": "candidate"}, {"status": "PASS"}, {"status": "PASS"})
    assert overreach["status"] == "PASS"
    assert overreach["stronger_robustness_claim_allowed"] is False
