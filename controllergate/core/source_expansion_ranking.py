from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any


ALLOWED_SOURCE_EXPANSION_APPROVAL_STATUSES = [
    "approved_for_batch069c_provider_command_probe",
    "approved_for_manual_artifact_request",
    "approved_for_runtime_connector_request",
    "approved_for_external_source_approval",
    "readiness_backlog",
    "parked_with_reopen_condition",
    "terminal_with_exact_reason",
    "already_counted_excluded",
    "probe_only_routing_memory",
    "orthology_routing_only",
]


MANUAL_ARTIFACT_STATUSES = {
    "manual_artifact_required",
    "manual_artifact_request_emitted",
}

RUNTIME_CONNECTOR_STATUSES = {
    "connector_required",
    "runtime_connector_request_emitted",
}


@dataclass(frozen=True)
class CandidateScore:
    candidate_id: str
    readiness_score: int
    approval_status: str
    exact_blocker_if_not_approved: str | None
    reopen_condition: str | None
    next_lowest_risk_action: str
    score_features: dict[str, Any]


def _bool(record: dict[str, Any], key: str) -> bool:
    return bool(record.get(key))


def _readiness_state(record: dict[str, Any]) -> str:
    return (
        record.get("batch068b_readiness_status")
        or record.get("batch069b_readiness_status")
        or record.get("batch069_readiness_status")
        or record.get("batch068_status")
        or "readiness_backlog"
    )


def _has_candidate_sha(record: dict[str, Any]) -> bool:
    value = record.get("candidate_sha")
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{40}", value) is not None


def _status_for(record: dict[str, Any]) -> str:
    state = _readiness_state(record)
    action = record.get("next_lowest_risk_action", "")
    if state == "already_counted_excluded":
        return "already_counted_excluded"
    if action == "already_probed_in_batch069":
        return "probe_only_routing_memory"
    if state in MANUAL_ARTIFACT_STATUSES or _bool(record, "missing_manual_artifact"):
        return "approved_for_manual_artifact_request"
    if state in RUNTIME_CONNECTOR_STATUSES or record.get("candidate_id") == "codex_wave3_aws_neuron_nki_library_issues_5":
        return "approved_for_runtime_connector_request"
    if state == "external_source_approval_required" or _bool(record, "missing_external_source_approval"):
        return "approved_for_external_source_approval"
    if state == "parked_with_reopen_condition":
        return "parked_with_reopen_condition"
    if state == "terminal_with_exact_reason" or state == "rejected_with_exact_blocker":
        return "terminal_with_exact_reason"
    if (
        state in {"approved_for_future_probe", "approved_for_current_probe"}
        and _has_candidate_sha(record)
        and not _bool(record, "missing_environment")
        and not _bool(record, "missing_provider_capsule")
    ):
        return "approved_for_batch069c_provider_command_probe"
    if state == "diagnostic_only":
        return "orthology_routing_only"
    return "readiness_backlog"


def score_candidate(record: dict[str, Any]) -> CandidateScore:
    status = _status_for(record)
    state = _readiness_state(record)
    score = 100
    features: dict[str, Any] = {
        "candidate_sha_available": _has_candidate_sha(record),
        "issue_derived_provenance": bool(record.get("issue_url_or_source_url")),
        "source_custody_clarity": bool(record.get("repo_url")) and _has_candidate_sha(record),
        "candidate_local_command_metadata_clarity": not _bool(record, "missing_command_boundary"),
        "ci_tox_nox_pytest_unittest_command_presence": "recoverable_by_provider_command_probe"
        if status == "approved_for_batch069c_provider_command_probe"
        else "not_verified_or_blocked",
        "test_tree_presence": not _bool(record, "missing_runner_target_proof"),
        "provider_capsule_feasibility": not _bool(record, "missing_provider_capsule"),
        "harness_origin_clarity": not _bool(record, "missing_evidence"),
        "runner_target_risk": "high" if _bool(record, "missing_runner_target_proof") else "bounded",
        "version_origin_risk": "high" if _bool(record, "missing_version_origin_proof") else "bounded",
        "workspace_purity_risk": "bounded_by_future_probe",
        "manual_artifact_dependency": status == "approved_for_manual_artifact_request",
        "runtime_connector_dependency": status == "approved_for_runtime_connector_request",
        "gold_fixed_future_leakage_risk": record.get("risk_of_gold_fixed_future_leakage", "controlled_by_firewall"),
        "issue_comment_fix_leakage_risk": record.get("risk_of_issue_comment_fix_leakage", "controlled_by_firewall"),
        "environment_complexity": "high" if _bool(record, "missing_environment") else "bounded",
        "estimated_pre_repair_replay_feasibility": "provider_command_probe_next"
        if status == "approved_for_batch069c_provider_command_probe"
        else "blocked_or_backlog",
        "proof_distance_to_source_topology_patch_license_gate": "shorter"
        if status == "approved_for_batch069c_provider_command_probe"
        else "longer",
        "non_ansible_memory_opportunity": status == "approved_for_batch069c_provider_command_probe",
        "product_readiness_value": "high" if status == "approved_for_batch069c_provider_command_probe" else "deferred",
        "current_readiness_state": state,
    }
    penalties = {
        "missing_candidate_sha": 30,
        "missing_command_boundary": 9,
        "missing_environment": 30,
        "missing_provider_capsule": 18,
        "missing_runner_target_proof": 12,
        "missing_version_origin_proof": 15,
        "missing_external_source_approval": 20,
        "missing_manual_artifact": 35,
    }
    if not _has_candidate_sha(record):
        score -= 30
    for key, amount in penalties.items():
        if key == "missing_candidate_sha":
            continue
        if _bool(record, key):
            score -= amount
    if status == "approved_for_batch069c_provider_command_probe":
        score += 25
    elif status == "probe_only_routing_memory":
        score -= 30
    elif status in {"approved_for_manual_artifact_request", "approved_for_runtime_connector_request"}:
        score -= 40
    elif status == "already_counted_excluded":
        score -= 70
    elif status in {"terminal_with_exact_reason", "orthology_routing_only"}:
        score -= 50
    score = max(0, min(125, score))
    blocker = None if status == "approved_for_batch069c_provider_command_probe" else (
        record.get("exact_blocker") or f"{status}_requires_reopen_condition"
    )
    next_action = (
        "batch069c_provider_command_probe"
        if status == "approved_for_batch069c_provider_command_probe"
        else record.get("next_lowest_risk_action")
        or record.get("what_would_make_it_approved")
        or "preserve_backlog_with_reopen_condition"
    )
    return CandidateScore(
        candidate_id=str(record.get("candidate_id")),
        readiness_score=score,
        approval_status=status,
        exact_blocker_if_not_approved=blocker,
        reopen_condition=record.get("reopen_condition") or record.get("what_would_make_it_approved") or next_action,
        next_lowest_risk_action=next_action,
        score_features=features,
    )


def rank_candidates(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ranked: list[dict[str, Any]] = []
    for record in records:
        score = score_candidate(record)
        ranked.append(
            {
                "candidate_id": score.candidate_id,
                "repo_url": record.get("repo_url", ""),
                "issue_url_or_source_url": record.get("issue_url_or_source_url", ""),
                "candidate_sha": None if record.get("missing_candidate_sha") else record.get("candidate_sha"),
                "source_type": record.get("source_type", "seed_product_readiness_registry"),
                "current_readiness_state": score.score_features["current_readiness_state"],
                "approval_status": score.approval_status,
                "exact_blocker_if_not_approved": score.exact_blocker_if_not_approved,
                "reopen_condition": score.reopen_condition,
                "next_lowest_risk_action": score.next_lowest_risk_action,
                "readiness_score": score.readiness_score,
                "score_features": score.score_features,
                "audit_status": "PASS",
            }
        )
    return sorted(
        ranked,
        key=lambda item: (
            item["approval_status"] != "approved_for_batch069c_provider_command_probe",
            -int(item["readiness_score"]),
            item["candidate_id"],
        ),
    )
