from __future__ import annotations

from scripts.post_v2_37_hardening_and_batch002_runner import validate_targeted_issue_seed


def _valid_seed() -> dict[str, object]:
    return {
        "candidate_id": "reader_issue_targeted_seed",
        "candidate_class": "issue_derived_reproduction_candidate",
        "source_type": "public_github_repo",
        "repo_url": "https://github.com/lemon24/reader",
        "source_commit_sha": "a" * 40,
        "source_commit_selection_method": "explicit_sha_or_default_branch_before_issue_created_at",
        "issue_url": "https://github.com/lemon24/reader/issues/123",
        "issue_created_at": "2024-01-01T00:00:00Z",
        "issue_title": "Example failure",
        "issue_text_snapshot": "Steps to reproduce:\\n```python\\nraise ValueError('x')\\n```\\nExpected behavior differs from actual behavior.",
        "issue_text_snapshot_source": "manual_snapshot_or_github_issue_body",
        "target_behavior_description": "expected failing behavior",
        "reproduction_steps": ["run the code block"],
        "expected_failure_type": "ValueError",
        "environment_lock_source": "pyproject.toml",
        "setup_commands": [],
        "forbidden_evidence_attestation": {
            "fixed_commit_used": False,
            "later_commit_used": False,
            "pr_patch_used": False,
            "gold_patch_used": False,
            "future_test_used": False,
        },
        "registry_author": "manual_targeted_issue_seed",
        "registry_review_status": "seed_draft",
        "created_utc": "2026-06-29T00:00:00Z",
        "notes": "neutral notes only",
    }


def test_valid_targeted_issue_seed_passes_shape_validation():
    assert validate_targeted_issue_seed(_valid_seed(), set())["status"] == "PASS"


def test_duplicate_candidate_blocks():
    seed = _valid_seed()
    assert validate_targeted_issue_seed(seed, {seed["candidate_id"]})["blocker"] == "targeted_issue_seed_duplicate_candidate"


def test_missing_issue_text_blocks():
    seed = _valid_seed()
    seed["issue_text_snapshot"] = ""
    assert validate_targeted_issue_seed(seed, set())["blocker"] == "targeted_issue_seed_missing_issue_text"


def test_solution_guidance_blocks():
    seed = _valid_seed()
    seed["issue_text_snapshot"] = "Steps to reproduce are present. The fix is to change parser.py."
    assert validate_targeted_issue_seed(seed, set())["blocker"] == "targeted_issue_seed_contains_solution_guidance"


def test_source_commit_sha_must_be_40_hex():
    seed = _valid_seed()
    seed["source_commit_sha"] = "not-a-sha"
    assert validate_targeted_issue_seed(seed, set())["blocker"] == "targeted_issue_seed_commit_unresolved"


def test_setup_commands_cannot_fetch_or_create_tests():
    seed = _valid_seed()
    seed["setup_commands"] = ["curl https://example.com/repro.py"]
    assert validate_targeted_issue_seed(seed, set())["blocker"] == "targeted_issue_seed_setup_unsafe"
