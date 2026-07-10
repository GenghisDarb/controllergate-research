from __future__ import annotations

from typing import Any

from .source_identity import sha256_json


def build_seed_identity_cache(records: list[dict[str, Any]]) -> dict[str, Any]:
    compact = [
        {
            "candidate_id": row.get("candidate_id"),
            "repo_url": row.get("repo_url"),
            "issue_url": row.get("issue_url"),
            "repo_identity_status": row.get("repo_identity_status"),
            "issue_identity_status": row.get("issue_identity_status"),
            "candidate_sha_status": row.get("candidate_sha_status"),
            "approval_status": row.get("approval_status"),
            "autonomy_tier": row.get("autonomy_tier"),
        }
        for row in records
    ]
    return {
        "status": "PASS",
        "cache_scope": "source_identity_routing_memory_only",
        "record_count": len(compact),
        "records": compact,
        "cache_hash": sha256_json(compact),
        "raw_source_committed": False,
        "patch_authority": False,
        "audit_status": "PASS",
    }
