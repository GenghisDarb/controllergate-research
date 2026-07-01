from __future__ import annotations


def issue_derived_harness_policy() -> dict[str, object]:
    return {
        "status": "PASS",
        "evidence_class": "issue_derived_reproduction_candidate",
        "ephemeral_only": True,
        "modifies_source": False,
        "modifies_tests": False,
        "uses_network": False,
        "increments_native_repair_count": False,
        "forbidden_evidence": [
            "fixed_commit_contents",
            "later_commit_contents",
            "pr_patch_contents",
            "fixed_diffs",
            "gold_patches",
            "future_tests",
        ],
    }


def issue_derived_verification_not_run(blocker: str) -> dict[str, object]:
    return {
        "status": "NOT_RUN",
        "candidate_class": None,
        "issue_derived_candidate_verified": False,
        "increments_native_repair_count": False,
        "blocker": blocker,
    }
