from __future__ import annotations

from controllergate.core.targeted_seed import seed_presence, validate_seed_schema


def _seed(candidate_id: str = "reader_issue_999") -> dict[str, object]:
    return {
        "candidate_id": candidate_id,
        "candidate_class": "native_candidate",
        "source_type": "public_github_repo",
        "repo_url": "https://github.com/example/project",
        "source_commit_sha": "0" * 40,
        "issue_url": "https://github.com/example/project/issues/999",
        "issue_title": "Target behavior fails",
        "issue_text_snapshot": "Steps to reproduce are listed without a repair.",
        "issue_text_snapshot_source": "manual_reviewed_issue_text",
        "native_target_test_command": "python -m pytest tests/test_target.py::test_target -q",
        "native_target_test_paths": ["tests/test_target.py"],
        "target_behavior_description": "The existing test should fail before repair.",
        "reproduction_steps": ["checkout source commit", "run native target test"],
        "expected_failure_type": "assertion_failure",
        "environment_lock_source": "requirements.txt",
        "setup_commands": ["python -m pip install -r requirements.txt"],
        "forbidden_evidence_attestation": {
            "fixed_commit_used": False,
            "later_commit_used": False,
            "gold_patch_used": False,
            "pr_patch_used": False,
            "future_test_used": False,
            "hidden_label_used": False,
        },
        "registry_author": "manual_seed_review",
        "registry_review_status": "seed_draft",
        "created_utc": "2026-07-01T00:00:00Z",
        "notes": "Prospective candidate lead only.",
    }


def test_missing_targeted_seed_blocks_before_acquisition(tmp_path):
    result = seed_presence(tmp_path / "targeted_prospective_seed_batch012.json")

    assert result["status"] == "BLOCK"
    assert result["seed_present"] is False
    assert result["blocker"] == "targeted_prospective_seed_missing_or_invalid"


def test_duplicate_repaired_candidate_is_rejected():
    result = validate_seed_schema(_seed("darker_skip_glob_failing_test"), set())

    assert result["status"] == "BLOCK"
    assert result["blocker"] == "targeted_seed_duplicate_candidate"


def test_valid_targeted_seed_shape_passes_schema_gate():
    result = validate_seed_schema(_seed(), set())

    assert result["status"] == "PASS"
    assert result["valid"] is True
