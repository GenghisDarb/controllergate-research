from __future__ import annotations

from pathlib import Path
from typing import Iterable

from .artifacts import is_archive_or_cache_payload
from .evidence import sha256_file

ALLOWED_INTAKE_CLASSIFICATIONS = [
    "approved_for_command_boundary_recovery",
    "approved_for_runtime_connector_planning",
    "approved_for_source_custody_only",
    "rejected_future_or_gold_evidence",
    "rejected_issue_fix_guidance",
    "rejected_missing_hash",
    "rejected_missing_provenance",
    "rejected_unsafe_payload",
    "rejected_candidate_mapping_not_in_scope",
    "quarantined_pending_review",
]

FORBIDDEN_TEXT_MARKERS = [
    "gold patch",
    "fixed commit",
    "future commit",
    "apply this patch",
    "solution patch",
    "workaround fix",
]


def scan_quarantine_path(path: Path, scoped_candidate_ids: Iterable[str]) -> dict[str, object]:
    scoped = set(scoped_candidate_ids)
    result: dict[str, object] = {
        "path": str(path),
        "size_bytes": path.stat().st_size,
        "sha256": sha256_file(path),
        "is_archive_or_cache_payload": is_archive_or_cache_payload(path.name),
        "structured_text_opened": False,
        "candidate_id": None,
        "classification": "quarantined_pending_review",
        "reason": "pending_review",
    }
    if is_archive_or_cache_payload(path.name):
        result["classification"] = "rejected_unsafe_payload"
        result["reason"] = "raw_archive_or_cache_payload_not_accepted_for_batch068b"
        return result
    text = path.read_text(encoding="utf-8", errors="replace")
    result["structured_text_opened"] = True
    lowered = text.lower()
    if any(marker in lowered for marker in FORBIDDEN_TEXT_MARKERS):
        result["classification"] = "rejected_future_or_gold_evidence"
        result["reason"] = "forbidden_guidance_marker_detected"
        return result
    candidate_id = None
    for scoped_id in scoped:
        if scoped_id in text:
            candidate_id = scoped_id
            break
    result["candidate_id"] = candidate_id
    if candidate_id is None:
        result["classification"] = "rejected_candidate_mapping_not_in_scope"
        result["reason"] = "artifact_candidate_id_not_in_batch068b_scope"
    else:
        result["classification"] = "quarantined_pending_review"
        result["reason"] = "candidate_mapped_but_not_yet_schema_approved"
    return result
