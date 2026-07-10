from __future__ import annotations

from controllergate.core.seed_harvest import PARKED_PYTEST_CANDIDATE_ID, build_seed_record
from controllergate.core.seed_ranking import rank_seeds
from controllergate.core.seed_source_approval import batch068_source_policy


def test_batch068_parks_pytest_without_reopen_evidence() -> None:
    record = build_seed_record(
        index=1,
        candidate_id=PARKED_PYTEST_CANDIDATE_ID,
        repo_url="https://github.com/pytest-dev/pytest",
        issue_url_or_source_url="https://github.com/pytest-dev/pytest/issues/13895",
        candidate_sha="041aacad506b6c6891f2898f2bd378e0896e8b86",
        source_type="approved_external_issue_source",
        source_hash="0" * 64,
        source_paths=["outputs/example.json"],
        raw_status="pytest_runner_target_split_unresolved_after_model_probe",
        already_counted=False,
        parked=True,
    )
    assert record["promotion_status"] == "parked_with_reopen_condition"
    assert record["parked_candidate_status"] == "parked_candidate_without_reopen_evidence"
    assert record["allowed_next_action"] == "batch063f_pytest_runner_target_specific_evidence_intake"


def test_batch068_excludes_already_counted_candidates_from_active_seed_inventory() -> None:
    record = build_seed_record(
        index=2,
        candidate_id="freezegun_547_py313_datetimes_assertion",
        repo_url="https://github.com/spulec/freezegun",
        issue_url_or_source_url="https://github.com/spulec/freezegun/issues/547",
        candidate_sha="a" * 40,
        source_type="approved_external_issue_source",
        source_hash="1" * 64,
        source_paths=["outputs/example.json"],
        raw_status="PASS",
        already_counted=True,
        parked=False,
    )
    assert record["promotion_status"] == "rejected_with_exact_blocker"
    assert record["promotion_blocker"] == "already_counted_repair"


def test_batch068_ranks_active_unseen_issue_lead_above_parked_and_counted() -> None:
    active = build_seed_record(
        index=3,
        candidate_id="codex_wave3_example_issues_123",
        repo_url="https://github.com/example/project",
        issue_url_or_source_url="https://github.com/example/project/issues/123",
        candidate_sha="b" * 40,
        source_type="approved_external_issue_source",
        source_hash="2" * 64,
        source_paths=["outputs/example.json"],
        raw_status="rejected_native_test_missing",
        already_counted=False,
        parked=False,
    )
    parked = build_seed_record(
        index=4,
        candidate_id=PARKED_PYTEST_CANDIDATE_ID,
        repo_url="https://github.com/pytest-dev/pytest",
        issue_url_or_source_url="https://github.com/pytest-dev/pytest/issues/13895",
        candidate_sha="c" * 40,
        source_type="approved_external_issue_source",
        source_hash="3" * 64,
        source_paths=["outputs/example.json"],
        raw_status="blocked_unproven_runner_target_model",
        already_counted=False,
        parked=True,
    )
    counted = build_seed_record(
        index=5,
        candidate_id="cloudpickle_507_py313_typevar_distutils",
        repo_url="https://github.com/cloudpipe/cloudpickle",
        issue_url_or_source_url="https://github.com/cloudpipe/cloudpickle/issues/507",
        candidate_sha="d" * 40,
        source_type="approved_external_issue_source",
        source_hash="4" * 64,
        source_paths=["outputs/example.json"],
        raw_status="PASS",
        already_counted=True,
        parked=False,
    )
    ranking = rank_seeds([parked, counted, active])
    assert ranking[0]["candidate_id"] == "codex_wave3_example_issues_123"
    assert ranking[0]["promotion_status"] == "approved_for_command_boundary_probe"


def test_batch068_source_policy_preserves_no_repair_boundary() -> None:
    policy = batch068_source_policy()
    assert policy["patch_generation_allowed"] is False
    assert policy["patch_application_allowed"] is False
    assert policy["duplicate_replay_allowed"] is False
    assert policy["count_gate_allowed"] is False
    assert policy["full_scoring"] == "NOT_RUN/disallowed"
