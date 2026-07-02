from __future__ import annotations

from controllergate.core.targeted_seed import proposed_native_seed_verification_guard


def test_unresolved_native_issue112_commit_blocks():
    seed = {
        "candidate_id": "darker_issue_112",
        "candidate_class": "native_candidate",
        "repo_url": "https://github.com/akaihola/darker",
        "issue_url": "https://github.com/akaihola/darker/issues/112",
        "native_target_test_paths": ["tests/test_black_diff.py"],
    }

    result = proposed_native_seed_verification_guard(seed)

    assert result["status"] == "BLOCK"
    assert "native_seed_commit_unresolved" in result["blockers"]


def test_missing_native_target_test_blocks_native_issue112_claim():
    seed = {
        "candidate_id": "darker_issue_112",
        "candidate_class": "native_candidate",
        "repo_url": "https://github.com/akaihola/darker",
        "issue_url": "https://github.com/akaihola/darker/issues/112",
        "source_commit_sha": "8f39377d51a9a18315ffb74176d2b8a32a4b1287",
    }

    result = proposed_native_seed_verification_guard(seed)

    assert result["status"] == "BLOCK"
    assert "native_seed_target_test_missing" in result["blockers"]
