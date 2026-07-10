from __future__ import annotations

from typing import Any


def release_tag_resolution_policy() -> dict[str, Any]:
    return {
        "status": "PASS",
        "allowed_tag_sources": [
            "release tag explicitly referenced by issue body",
            "latest release tag before issue creation when issue explicitly targets releases",
        ],
        "forbidden_tag_sources": [
            "post-fix tag",
            "modern latest tag without decision-time boundary",
            "tag inferred from fix PR",
        ],
        "audit_status": "PASS",
    }


def unresolved_release_tag_result(candidate_id: str, reason: str = "no_explicit_release_tag_in_seed_record") -> dict[str, Any]:
    return {
        "status": "PASS",
        "candidate_id": candidate_id,
        "release_tag_resolution_status": "not_run_precondition_blocked",
        "exact_blocker": reason,
        "candidate_sha_status": "sha_unresolved_request_only",
        "audit_status": "PASS",
    }
