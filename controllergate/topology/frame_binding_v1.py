from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping


BOUND_KEYS = (
    "board_cells", "board_edges", "causal_regions", "boundary_cells", "environment_exhausted_handoff",
    "projection_pairs", "orthology_invariants", "causal_hypotheses", "constraints", "minimal_probes",
    "predicted_partitions", "semantic_verifiers", "controls", "budgets", "probe_nonces", "observer_state_contract",
    "provisional_branch_root", "modality_contracts", "tld_shadow_identities", "sealed_truth_custody_identity",
    "proof_release_parent", "legal_probe_exhaustion_root", "nogood_store_root",
)


def canonical_frame(payload: Mapping[str, Any]) -> dict[str, Any]:
    missing = [key for key in BOUND_KEYS if key not in payload]
    if missing:
        raise ValueError(f"complete decisive frame missing: {missing}")
    return {key: payload[key] for key in BOUND_KEYS}


def freeze_complete_frame(payload: Mapping[str, Any]) -> dict[str, Any]:
    canonical = canonical_frame(payload)
    frame_hash = hashlib.sha256(json.dumps(canonical, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()
    return {"frame_hash": frame_hash, "canonical_frame": canonical, "unexecuted_probe_authorizations_valid": True, "authority_allowed": "frozen probe execution only", "authority_forbidden": ["unregistered probe", "post-freeze mutation", "terminal truth"]}


def validate_frozen_frame(frozen: Mapping[str, Any], current: Mapping[str, Any]) -> dict[str, Any]:
    observed = freeze_complete_frame(current)["frame_hash"]
    changed = observed != frozen.get("frame_hash")
    return {"status": "INVALIDATED" if changed else "PASS", "expected_frame_hash": frozen.get("frame_hash"), "observed_frame_hash": observed, "unexecuted_probe_authorizations_valid": not changed}


def authorize_probe(probe_id: str, frozen: Mapping[str, Any], *, extension: Mapping[str, Any] | None = None) -> dict[str, Any]:
    registered = {row["probe_id"] for row in frozen["canonical_frame"]["minimal_probes"]}
    if probe_id in registered:
        return {"status": "AUTHORIZED", "frame_hash": frozen["frame_hash"], "frame_extension": False}
    valid_extension = bool(extension and extension.get("parent_frame_hash") == frozen.get("frame_hash") and extension.get("new_frame_hash") and extension.get("authorized") is True)
    return {"status": "AUTHORIZED" if valid_extension else "REJECTED", "frame_hash": frozen["frame_hash"], "frame_extension": valid_extension, "reason": None if valid_extension else "unregistered_post_freeze_probe"}
