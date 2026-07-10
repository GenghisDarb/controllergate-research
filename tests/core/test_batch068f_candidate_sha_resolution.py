from __future__ import annotations

from controllergate.core.agnostic_provenance_lock import agnostic_provenance_lock_scaffold
from controllergate.core.candidate_sha_resolver import (
    acceptable_candidate_sha_source_policy,
    candidate_sha_resolution_engine_policy,
)
from controllergate.core.issue_epoch_snapshot import decision_time_epoch_policy
from controllergate.core.runtime_wrapper_activation_watchdog import runtime_wrapper_activation_watchdog
from controllergate.core.sha_resolution_confidence import classify_sha_resolution, sha_resolution_confidence_schema
from scripts.generate_batch068f_candidate_sha_resolution_intake import PUBLIC_SUMMARY


def test_batch068f_candidate_sha_policy_forbids_guessing_and_patching() -> None:
    policy = candidate_sha_resolution_engine_policy()

    assert policy["status"] == "PASS"
    assert "assistant guess" in policy["forbidden_sha_sources"]
    assert "modern HEAD" in policy["forbidden_sha_sources"]
    assert policy["patch_authority"] is False
    assert policy["test_execution_authority"] is False


def test_batch068f_epoch_snapshot_is_metadata_only() -> None:
    policy = decision_time_epoch_policy()
    confidence = classify_sha_resolution(
        "latest_default_branch_commit_before_issue_created_verified",
        commit_resolves=True,
    )

    assert policy["epoch_snapshot_is_not_reproduction_proof"] is True
    assert policy["epoch_snapshot_allows_metadata_scan_only"] is True
    assert policy["epoch_snapshot_allows_patch_or_test_execution"] is False
    assert confidence["confidence"] == "decision_time_epoch_snapshot_commit"
    assert confidence["tier2_allowed"] is True
    assert "patch_generation" in confidence["forbidden_use"]
    assert "test_execution" in confidence["forbidden_use"]


def test_batch068f_unresolved_sha_remains_tier1() -> None:
    confidence = classify_sha_resolution("sha_unresolved_request_only", commit_resolves=False)

    assert confidence["confidence"] == "unresolved_sha_required"
    assert confidence["tier"] == 1
    assert confidence["tier2_allowed"] is False


def test_batch068f_confidence_schema_and_source_policy_are_explicit() -> None:
    schema = sha_resolution_confidence_schema()
    source_policy = acceptable_candidate_sha_source_policy()

    assert "exact_reproduction_commit" in schema["confidence_levels"]
    assert "decision_time_epoch_snapshot_commit" in schema["tier2_allowed_confidence_levels"]
    assert source_policy["epoch_snapshot_is_not_issue_reproduction_proof"] is True


def test_batch068f_runtime_watchdog_blocks_activation_below_threshold() -> None:
    watchdog = runtime_wrapper_activation_watchdog(issue_derived_repair_count=4, threshold=20)

    assert watchdog["activation_state"] == "activation_threshold_not_met"
    assert watchdog["runtime_wrapper_activation_allowed"] is False
    assert watchdog["live_device_repair_enabled"] is False
    assert watchdog["self_maintaining_software_claim_allowed"] is False


def test_batch068f_runtime_scaffold_is_dormant() -> None:
    scaffold = agnostic_provenance_lock_scaffold()

    assert scaffold["status"] == "scaffolded_with_config_and_audit"
    assert scaffold["activation_state"] == "not_run_precondition_blocked"
    assert scaffold["active_collection_enabled"] is False
    assert scaffold["patch_authority"] is False


def test_batch068f_public_summary_uses_neutral_language() -> None:
    lowered = PUBLIC_SUMMARY.lower()

    for forbidden in ["reactome", "chromosomal", "biological", "torus", "tld", "tot-brot", "tot-bulb", "apoptosis"]:
        assert forbidden not in lowered
    assert "not repair proof" in lowered
    assert "full scoring remains not_run/disallowed" in lowered
