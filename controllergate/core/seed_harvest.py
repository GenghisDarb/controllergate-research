from __future__ import annotations

import re
from typing import Any

from .seed_source_approval import FORBIDDEN_DIRECT_REPAIR_SEED_CLASSES

PARKED_PYTEST_CANDIDATE_ID = "pytest_13895_pytest9_skiptest_behavior"

PROMOTION_STATUSES = [
    "approved_for_pre_repair_replay_attempt",
    "approved_for_provider_capsule_probe",
    "approved_for_command_boundary_probe",
    "approved_for_manual_artifact_request",
    "routing_memory_only",
    "diagnostic_only",
    "rejected_with_exact_blocker",
    "parked_with_reopen_condition",
]

REQUIRED_BATCH068_CANDIDATE_FIELDS = [
    "seed_id",
    "candidate_id",
    "repo_url",
    "issue_url_or_source_url",
    "candidate_sha_if_known",
    "candidate_sha_status",
    "source_type",
    "source_hash",
    "source_custody_status",
    "issue_derived_status",
    "manual_artifact_status",
    "already_counted_status",
    "parked_candidate_status",
    "probe_only_status",
    "gold_fixed_future_exclusion_status",
    "label_blindness_status",
    "decision_time_safe_status",
    "license_or_terms_status",
    "harness_origin_status",
    "command_boundary_risk",
    "provider_capsule_risk",
    "workspace_purity_risk",
    "runner_target_risk",
    "version_origin_risk",
    "source_topology_risk",
    "pre_repair_replay_feasibility",
    "estimated_materialization_cost",
    "cross_family_ast_homology_hint",
    "reward_signal_initial_class",
    "promotion_status",
    "promotion_blocker",
    "allowed_next_action",
    "forbidden_next_action",
    "audit_status",
]


def normalize_candidate_id(value: object) -> str:
    text = str(value or "").strip()
    text = re.sub(r"\s+", "_", text)
    return text


def is_placeholder_candidate_id(candidate_id: str) -> bool:
    lowered = candidate_id.lower()
    return (
        not candidate_id
        or candidate_id.startswith("<")
        or "/" in candidate_id
        or "\\" in candidate_id
        or lowered.startswith("null_seed")
        or lowered in {"pass", "fail", "block", "none", "unknown"}
    )


def candidate_sha_status(candidate_sha: str | None) -> str:
    if candidate_sha and re.fullmatch(r"[0-9a-fA-F]{40}", candidate_sha):
        return "sha40_recorded"
    if candidate_sha:
        return "sha_recorded_noncanonical"
    return "unknown"


def is_probe_only_signal(candidate_id: str, raw_status: str) -> bool:
    lowered = f"{candidate_id} {raw_status}".lower()
    return any(
        token in lowered
        for token in [
            "probe_only",
            "target_nonmaterialization",
            "nonmaterialization",
            "timeout_class",
            "blocked_timeout",
            "compiled_dependency",
            "dependency_too_heavy",
            "dependency_boundary",
            "environment_boundary",
        ]
    )


def classify_promotion_status(
    *,
    candidate_id: str,
    repo_url: str,
    issue_url_or_source_url: str,
    candidate_sha: str | None,
    raw_status: str,
    already_counted: bool,
    parked: bool,
) -> tuple[str, str | None, str]:
    if parked:
        return (
            "parked_with_reopen_condition",
            "parked_candidate_without_reopen_evidence",
            "batch063f_pytest_runner_target_specific_evidence_intake",
        )
    if already_counted:
        return (
            "rejected_with_exact_blocker",
            "already_counted_repair",
            "no_repair_attempt_already_counted",
        )
    if is_probe_only_signal(candidate_id, raw_status):
        return ("diagnostic_only", "probe_only_environmental", "no_repair_attempt_probe_only")
    if issue_url_or_source_url.startswith("https://github.com/") and candidate_sha_status(candidate_sha) == "sha40_recorded":
        return ("approved_for_command_boundary_probe", None, "batch069_multi_candidate_provider_command_probe")
    if repo_url.startswith("https://github.com/") and candidate_sha_status(candidate_sha) == "sha40_recorded":
        return ("approved_for_provider_capsule_probe", None, "batch069_multi_candidate_provider_command_probe")
    if repo_url.startswith("https://github.com/"):
        return ("approved_for_manual_artifact_request", None, "batch068b_manual_artifact_and_external_source_custody_intake")
    return ("rejected_with_exact_blocker", "blocked_untrusted_source", "no_repair_attempt_untrusted_source")


def build_seed_record(
    *,
    index: int,
    candidate_id: str,
    repo_url: str,
    issue_url_or_source_url: str,
    candidate_sha: str | None,
    source_type: str,
    source_hash: str,
    source_paths: list[str],
    raw_status: str,
    already_counted: bool,
    parked: bool,
) -> dict[str, Any]:
    promotion_status, promotion_blocker, allowed_next_action = classify_promotion_status(
        candidate_id=candidate_id,
        repo_url=repo_url,
        issue_url_or_source_url=issue_url_or_source_url,
        candidate_sha=candidate_sha,
        raw_status=raw_status,
        already_counted=already_counted,
        parked=parked,
    )
    issue_based = issue_url_or_source_url.startswith("https://github.com/") and "/issues/" in issue_url_or_source_url
    return {
        "seed_id": f"batch068_seed_{index:03d}_{candidate_id}",
        "candidate_id": candidate_id,
        "repo_url": repo_url,
        "issue_url_or_source_url": issue_url_or_source_url,
        "candidate_sha_if_known": candidate_sha or None,
        "candidate_sha_status": candidate_sha_status(candidate_sha),
        "source_type": source_type,
        "source_hash": source_hash,
        "source_paths": source_paths,
        "source_custody_status": "repo_local_safe_prior_artifact_hash_recorded",
        "issue_derived_status": "issue_derived_lead" if issue_based else "not_issue_derived_or_unknown",
        "manual_artifact_status": "not_manual_artifact",
        "already_counted_status": "already_counted_repair" if already_counted else "not_already_counted",
        "parked_candidate_status": "parked_candidate_without_reopen_evidence" if parked else "not_parked",
        "probe_only_status": "probe_only_environmental" if is_probe_only_signal(candidate_id, raw_status) else "not_probe_only",
        "gold_fixed_future_exclusion_status": "PASS",
        "label_blindness_status": "PASS",
        "decision_time_safe_status": "decision_time_safe_repo_local_prior_evidence",
        "license_or_terms_status": "not_assessed_for_patch_batch068",
        "harness_origin_status": "issue_origin_requires_future_harness_firewall" if issue_based else "harness_origin_not_yet_materialized",
        "command_boundary_risk": "medium_requires_command_boundary_probe" if issue_based else "unknown_requires_future_manifest",
        "provider_capsule_risk": "medium_requires_provider_capsule_probe",
        "workspace_purity_risk": "low_future_isolated_workspace_required",
        "runner_target_risk": "blocked_specific_pytest_runner_target_required" if parked else "low_or_medium_non_pytest_runner_target",
        "version_origin_risk": "low_sha40_recorded" if candidate_sha_status(candidate_sha) == "sha40_recorded" else "medium_version_origin_required",
        "source_topology_risk": "unknown_until_pre_repair_replay",
        "pre_repair_replay_feasibility": "future_probe_required",
        "estimated_materialization_cost": "medium" if issue_based else "unknown",
        "cross_family_ast_homology_hint": "routing_only_not_repair_proof",
        "reward_signal_initial_class": "routing_signal_only",
        "promotion_status": promotion_status,
        "promotion_blocker": promotion_blocker,
        "allowed_next_action": allowed_next_action,
        "forbidden_next_action": sorted(FORBIDDEN_DIRECT_REPAIR_SEED_CLASSES),
        "audit_status": "PASS",
        "raw_prior_status": raw_status or "unknown",
    }


def is_active_repair_seed(record: dict[str, Any]) -> bool:
    return record.get("promotion_status") in {
        "approved_for_pre_repair_replay_attempt",
        "approved_for_provider_capsule_probe",
        "approved_for_command_boundary_probe",
    }
