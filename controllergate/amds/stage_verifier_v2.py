from __future__ import annotations

import hashlib
import inspect
import json
from typing import Any, Mapping


STAGE_KEYS = {
    "Seed": ("probe_contracts", "active_hypotheses", "seed_receipt"),
    "NormalizeEvidence": ("normalized_evidence", "normalized_evidence_hash"),
    "FreezeFrame": ("frozen_frame_hash", "probe_contracts_bound_into_frame"),
    "DecomposeContacts": ("decomposed_contacts",),
    "ExpandFrontier": ("frontier", "frontier_hash"),
    "MaterializeRequirements": ("materialized_requirements", "legal_probe_count"),
    "SelectMinimalProbe": ("selected_probe_id", "planner_receipt"),
    "ExecuteProbe": ("probe_executions", "spent_nonces", "unique_probe_operation_count"),
    "VerifyObservation": ("verified_observations", "verified_observation_count"),
    "UpdateConstraints": ("verified_causal_facts", "truth_maintenance"),
    "MarkCertain": ("certain_hypotheses",),
    "DetectContradictionAndBacktrack": ("contradictions", "backtrack_count", "nogoods"),
    "InterlockAndElbowAudit": ("interlock_elbow_audit",),
    "ControllerAuditCommitOrAbstain": ("legal_probe_exhaustion_receipt", "terminal", "terminal_writer", "patch_authority"),
}


def _hash(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()


def verify_transition(stage_index: int, before: Mapping[str, Any], after: Mapping[str, Any]) -> dict[str, Any]:
    from .stage_runtime_v7 import STAGES

    stage = STAGES[stage_index]
    expected_trace = list(STAGES[: stage_index + 1])
    keys = STAGE_KEYS[stage]
    added_or_changed = [key for key in keys if key in after and (key not in before or before.get(key) != after.get(key))]
    terminal_written_early = stage_index < len(STAGES) - 1 and "terminal" in after
    hashes_consistent = before != after and after.get("executed_stages") == expected_trace
    status = "PASS" if len(added_or_changed) == len(keys) and hashes_consistent and not terminal_written_early else "BLOCK"
    return {
        "status": status,
        "stage": stage,
        "stage_specific_keys": list(keys),
        "reconstructed_changed_keys": added_or_changed,
        "input_state_hash": _hash(before),
        "output_state_hash": _hash(after),
        "expected_trace": expected_trace,
        "actual_trace": list(after.get("executed_stages", ())),
        "terminal_written_early": terminal_written_early,
        "verifier": "controllergate.amds.stage_verifier_v2.verify_transition",
        "verifier_code_hash": _hash(inspect.getsource(verify_transition)),
        "independent_reconstruction": True,
    }
