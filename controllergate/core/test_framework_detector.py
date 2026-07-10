from __future__ import annotations

from typing import Any

from .command_pattern_library import native_command_pattern_library


def test_framework_signature_library() -> dict[str, Any]:
    return {
        "status": "PASS",
        "families": [
            {
                "test_framework_family": row["pattern_id"],
                "metadata_signatures": row["metadata_signatures"],
                "test_tree_signatures": row["test_tree_signatures"],
                "minimum_evidence_for_family_detection": "candidate-era metadata plus source-tree presence",
                "audit_status": "PASS",
            }
            for row in native_command_pattern_library()["records"]
        ],
    }


def detect_framework_from_record(record: dict[str, Any]) -> dict[str, Any]:
    if record.get("manual_artifact_required"):
        family = "manual_artifact_required"
        confidence = "medium_confidence_requires_manual_artifact"
    elif record.get("runtime_connector_required"):
        family = "runtime_connector_required"
        confidence = "medium_confidence_requires_manual_artifact"
    elif record.get("missing_command_boundary"):
        family = "unknown"
        confidence = "low_confidence_routing_only"
    elif record.get("missing_environment") or record.get("missing_provider_capsule"):
        family = "provider_gated"
        confidence = "low_confidence_routing_only"
    else:
        family = "candidate_local_metadata"
        confidence = "high_confidence_project_local_inference"
    return {
        "test_framework_family": family,
        "confidence": confidence,
        "audit_status": "PASS",
    }
