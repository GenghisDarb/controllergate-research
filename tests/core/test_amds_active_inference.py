from controllergate.core.amds_active_inference import amds_probe_queue
from controllergate.core.search_space_geometry import build_search_space_feature_vector


def test_amds_active_inference_produces_probe_queue_not_repair_claim():
    vector = build_search_space_feature_vector(
        candidate_id="darker_issue_112_relative_git_dir",
        candidate_class="issue_derived_reproduction_candidate",
        source_type="public_github_repo",
        repo_url="https://github.com/akaihola/darker",
        source_commit_sha=None,
        issue_url="https://github.com/akaihola/darker/issues/112",
        issue_timestamp_status="PASS",
        dependency_lock_status="ABSENT",
        target_intent_alignment_status="NOT_RUN",
        blocker_if_not_probeable="manual_dependency_lock_absent",
    )
    queue = amds_probe_queue(vector)

    assert queue["candidate_status"] == "blocked_on_manual_dependency_lock"
    assert queue["candidate_probe_queue"]
    assert queue["repair_success_claim"] is False
    assert queue["memory_lift_claim"] is False
