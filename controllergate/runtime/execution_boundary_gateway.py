from __future__ import annotations

import json
from hashlib import sha256
from typing import Any


def stable_hash(value: Any) -> str:
    return sha256(json.dumps(value, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def build_crossing_record(
    *,
    source_hash: str,
    policy_hash: str,
    action_manifest: dict[str, Any],
    claim_boundary: dict[str, Any],
    verified: bool,
) -> dict[str, Any]:
    action_hash = stable_hash(action_manifest)
    status = "PASS" if verified and action_manifest.get("status") == "PASS" else "BLOCK"
    return {
        "status": status,
        "source_hash": source_hash,
        "policy_hash": policy_hash,
        "action_hash": action_hash,
        "claim_boundary_hash": stable_hash(claim_boundary),
        "proof_space_separated_from_runtime_space": True,
        "direct_runtime_mutation_allowed": False,
        "transport_log_required": True,
        "blocker": None if status == "PASS" else "unverified_direct_runtime_mutation_blocked",
    }


def verify_transport(source_sha256: str, destination_sha256: str) -> dict[str, Any]:
    return {
        "status": "PASS" if source_sha256 == destination_sha256 else "BLOCK",
        "source_sha256": source_sha256,
        "destination_sha256": destination_sha256,
        "sha256_match": source_sha256 == destination_sha256,
    }
