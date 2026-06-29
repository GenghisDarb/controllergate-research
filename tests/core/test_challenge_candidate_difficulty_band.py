from __future__ import annotations

from controllergate.core.clean_repair import challenge_candidate_difficulty_band


def _attempt(**overrides: object) -> dict[str, object]:
    base = {
        "lead_id": "candidate_x",
        "repo_url": "https://example.test/repo",
        "resolved_commit_sha": "a" * 40,
        "test_path_hint": "tests/test_target.py",
        "target_test_present": True,
        "environment_file_present": True,
        "environment_files": ["pyproject.toml"],
        "collection_status": "PASS",
        "failure_replay_status": "PRE_PATCH_FAILURE_OBSERVED",
        "semantic_failure_signature_hash": "b" * 64,
        "traceback_candidate_source_file_count": 3,
        "patchable_source_function_count": 3,
        "environment_metadata": {"declared_dependency_strings": ["pytest"]},
    }
    base.update(overrides)
    return base


def test_moderate_native_candidate_is_admitted():
    result = challenge_candidate_difficulty_band(_attempt())

    assert result["admission_decision"] == "admitted_native_replay_candidate"
    assert result["repairability_score"] <= 4


def test_candidate_without_target_test_is_rejected():
    result = challenge_candidate_difficulty_band(_attempt(target_test_present=False))

    assert result["admission_decision"] == "rejected_missing_target_test"


def test_too_broad_candidate_is_rejected_as_escape_boundary_risk():
    result = challenge_candidate_difficulty_band(_attempt(traceback_candidate_source_file_count=6))

    assert result["admission_decision"] == "rejected_escape_boundary_risk"


def test_too_trivial_candidate_is_rejected_for_memory_challenge():
    result = challenge_candidate_difficulty_band(
        _attempt(
            traceback_candidate_source_file_count=1,
            patchable_source_function_count=1,
            failure_text_direct_edit_hint=True,
        )
    )

    assert result["blocker"] == "challenge_candidate_too_trivial_for_memory_challenge"
