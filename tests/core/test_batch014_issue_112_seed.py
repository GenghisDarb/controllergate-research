from __future__ import annotations

from controllergate.core.targeted_seed import proposed_native_seed_verification_guard


def test_issue112_issue_derived_seed_is_not_native_claim():
    seed = {
        "candidate_id": "darker_issue_112_relative_git_dir",
        "candidate_class": "issue_derived_reproduction_candidate",
        "repo_url": "https://github.com/akaihola/darker",
        "issue_url": "https://github.com/akaihola/darker/issues/112",
    }

    result = proposed_native_seed_verification_guard(seed)

    assert result["status"] == "PASS"
    assert result["issue_derived_classification_allowed"] is True


def test_issue112_native_black_diff_claim_blocks_without_alignment_proof():
    seed = {
        "candidate_id": "darker_issue_112",
        "candidate_class": "native_candidate",
        "repo_url": "https://github.com/akaihola/darker",
        "issue_url": "https://github.com/akaihola/darker/issues/112",
        "source_commit_sha": "8f39377d51a9a18315ffb74176d2b8a32a4b1287",
        "native_target_test_command": "python -m pytest tests/test_black_diff.py::TestBlackDiff::test_black_diff -q --tb=no",
        "native_target_test_paths": ["tests/test_black_diff.py"],
    }

    result = proposed_native_seed_verification_guard(seed)

    assert result["status"] == "BLOCK"
    assert result["blocker"] == "native_seed_issue_target_mismatch"
