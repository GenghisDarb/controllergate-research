from __future__ import annotations

from controllergate.core.targeted_seed import harmonize_batch014_seed


def _seed() -> dict[str, object]:
    return {
        "candidate_id": "darker_issue_112_relative_git_dir",
        "candidate_class": "issue_derived_reproduction_candidate",
        "source_type": "public_github_repo",
        "repo_url": "https://github.com/akaihola/darker",
        "source_commit_selection_method": "default_branch_before_issue_created_at",
        "issue_url": "https://github.com/akaihola/darker/issues/112",
        "issue_title": "Relative git dir failure",
        "issue_text_snapshot": "Reproduction command and observed error only.",
        "issue_text_snapshot_source": "manual_redacted_issue_snapshot_no_solution_sections",
        "target_behavior_description": "Command should not fail with the repository error.",
        "reproduction_steps": ["run darker --check src with GIT_DIR=.git"],
        "expected_failure_type": "repository error",
        "environment_lock_source": "pyproject.toml",
        "setup_commands": [],
        "forbidden_evidence_attestation": {
            "fixed_commit_used": False,
            "later_commit_used": False,
            "gold_patch_used": False,
            "pr_patch_used": False,
            "future_test_used": False,
            "hidden_label_used": False,
            "solution_comment_used": False,
            "issue_solution_section_used": False,
        },
        "registry_author": "manual_seed_review",
        "registry_review_status": "seed_draft",
        "created_utc": "2026-07-01T00:00:00Z",
        "notes": "Reviewed seed draft.",
    }


def test_batch014_seed_harmonization_passes_complete_issue_seed():
    result = harmonize_batch014_seed(_seed(), set())

    assert result["status"] == "PASS"
    assert result["normalized_seed"]["evidence_class"] == "issue_derived"


def test_missing_forbidden_evidence_attestation_blocks():
    seed = _seed()
    del seed["forbidden_evidence_attestation"]["hidden_label_used"]

    result = harmonize_batch014_seed(seed, set())

    assert result["status"] == "BLOCK"
    assert result["blocker"] == "targeted_seed_missing_forbidden_evidence_attestation"
