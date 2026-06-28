from __future__ import annotations

from controllergate.core.candidate_admission import repair_queue_admission_decision
from controllergate.core.clean_repair import build_verified_candidate_repair_queue, generate_patch_candidate


def test_verified_candidate_can_enter_repair_queue():
    candidate = {
        "lead_id": "darker_non_ascii_drop_changes",
        "decision": "verified_native_candidate_pending_repair",
        "failure_replay_status": "PRE_PATCH_FAILURE_OBSERVED",
        "repo_url": "https://example.invalid/repo.git",
        "resolved_commit_sha": "1" * 40,
        "test_path_hint": "tests/test_a.py",
        "semantic_failure_signature_hash": "2" * 64,
    }

    assert repair_queue_admission_decision(candidate)["admitted_to_repair_queue"] is True
    assert build_verified_candidate_repair_queue([candidate], 1)[0]["candidate_id"] == "darker_non_ascii_drop_changes"


def test_unverified_candidate_cannot_enter_repair_queue():
    candidate = {"lead_id": "darker_non_ascii_drop_changes", "decision": "rejected", "failure_replay_status": "PASSING_PRE_PATCH_NOT_A_FAILURE"}

    assert repair_queue_admission_decision(candidate)["blocker"] == "candidate_not_verified_for_repair_generation"
    assert build_verified_candidate_repair_queue([candidate], 1) == []


def test_patch_generation_cannot_run_without_patchable_subset(tmp_path):
    patch = generate_patch_candidate(
        {"candidate_id": "darker_non_ascii_drop_changes"},
        tmp_path,
        {"context_capsule_hash": "abc"},
        {"patchable_source_files": []},
        {"allowed_source_files": []},
    )

    assert patch["patch_candidate_generated"] is False
    assert patch["blocker"] == "clean_repair_no_safe_source_patch_generated"
