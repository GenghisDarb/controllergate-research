from __future__ import annotations

import re
from typing import Any

from .test_framework_detector import detect_framework_from_record


COMMAND_CONFIDENCE_LEVELS = [
    "exact_declared_command",
    "high_confidence_project_local_inference",
    "medium_confidence_requires_manual_artifact",
    "low_confidence_routing_only",
    "blocked_forbidden_or_untrusted",
]


def has_verified_sha(record: dict[str, Any]) -> bool:
    sha = record.get("candidate_sha") or record.get("verified_candidate_sha")
    return isinstance(sha, str) and re.fullmatch(r"[0-9a-f]{40}", sha) is not None


def infer_command_orthology(record: dict[str, Any]) -> dict[str, Any]:
    framework = detect_framework_from_record(record)
    confidence = framework["confidence"]
    blockers: list[str] = []
    if not has_verified_sha(record):
        blockers.append("candidate_sha_still_missing")
        confidence = "low_confidence_routing_only"
    if record.get("missing_manual_artifact") or record.get("manual_artifact_required"):
        blockers.append("manual_artifact_still_required")
        confidence = "medium_confidence_requires_manual_artifact"
    if record.get("runtime_connector_required") or record.get("candidate_id") == "codex_wave3_aws_neuron_nki_library_issues_5":
        blockers.append("runtime_connector_still_required")
        confidence = "medium_confidence_requires_manual_artifact"
    if record.get("missing_environment") or record.get("missing_provider_capsule"):
        blockers.append("provider_or_environment_still_missing")
        if confidence != "medium_confidence_requires_manual_artifact":
            confidence = "low_confidence_routing_only"
    if record.get("approval_status") in {"rejected_future_or_gold_evidence", "rejected_untrusted_source"}:
        blockers.append("blocked_forbidden_or_untrusted")
        confidence = "blocked_forbidden_or_untrusted"
    approved_for_probe = confidence in {"exact_declared_command", "high_confidence_project_local_inference"} and not blockers
    return {
        "candidate_id": record.get("candidate_id"),
        "command_family": framework["test_framework_family"],
        "confidence": confidence,
        "confidence_levels": COMMAND_CONFIDENCE_LEVELS,
        "approved_for_future_provider_command_probe": approved_for_probe,
        "blockers": blockers,
        "allowed_use": "routing_and_future_provider_command_probe_only" if approved_for_probe else "routing_or_intake_only",
        "forbidden_use": ["patch_authority", "repair_proof", "count_gate_evidence", "memory_lift_evidence"],
        "audit_status": "PASS",
    }
