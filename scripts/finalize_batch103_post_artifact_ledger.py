"""Persist the conservative Batch103 post-artifact goal transitions."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "configs/controllergate_master_completion_ledger_v2.json"
OUT = ROOT / "outputs/post_v2_37_hardening_batch103_reactome_isomorphism_causal_planning_gain_exact_materialization"
HANDOFF = OUT / "batch103_official_artifact_handoff_verification.json"
WORKFLOW_HEAD = "3aa1a749be0a1e13bd735623c812335af9795f76"
STAMP = "2026-07-20T15:17:38Z"
TRANSITION_ID = "batch103:CG-GOAL-030-REACTOME-CAUSAL-PLANNING-GAIN:post-artifact-evaluation"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
    goals = {row["goal_id"]: row for row in ledger["goals"]}
    goal29 = goals["CG-GOAL-029-REACTOME-EXECUTABLE-MAINTENANCE-MAPPING"]
    goal29["active_blockers"] = [
        "shadow execution remains nonauthorizing",
        "completed ablation established no causal planning gain",
    ]
    goal29["last_updated_commit"] = WORKFLOW_HEAD
    goal29["last_updated_timestamp"] = STAMP

    handoff_rel = HANDOFF.relative_to(ROOT).as_posix()
    goal30 = goals["CG-GOAL-030-REACTOME-CAUSAL-PLANNING-GAIN"]
    previous_status = "IN_PROGRESS"
    goal30["status"] = "BLOCKED"
    if handoff_rel not in goal30["current_evidence"]:
        goal30["current_evidence"].append(handoff_rel)
    goal30["evidence_hashes"][handoff_rel] = _sha256(HANDOFF)
    goal30["active_blockers"] = [
        "zero candidates improved a preregistered public metric",
        "post-freeze aggregate truth join measured zero causal accuracy",
        "each Reactome arm produced one false attribution in the post-freeze aggregate truth join",
        "R4 not established",
    ]
    goal30["last_updated_commit"] = WORKFLOW_HEAD
    goal30["last_updated_timestamp"] = STAMP

    goal31 = goals["CG-GOAL-031-REACTOME-CROSS-CANDIDATE-GENERALIZATION"]
    goal31["active_blockers"] = [
        "R4 local gain not established",
        "no gain replicated across three candidates, two causal families, and multiple repository/provider classes",
        "R5 not established",
    ]
    goal31["last_updated_commit"] = WORKFLOW_HEAD
    goal31["last_updated_timestamp"] = STAMP

    transitions = {row["transition_id"] for row in ledger.get("supersession_receipts", [])}
    transition_value = {
                "transition_id": TRANSITION_ID,
                "goal_id": goal30["goal_id"],
                "previous_status": previous_status,
                "new_status": "BLOCKED",
                "transition_reason": (
                    "The successful official workflow, independently verified artifact, and local "
                    "post-freeze aggregate truth join established no preregistered planning gain."
                ),
                "evidence_paths": [handoff_rel],
                "evidence_sha256s": {handoff_rel: _sha256(HANDOFF)},
                "transition_commit": WORKFLOW_HEAD,
                "active_blockers": goal30["active_blockers"],
                "reopen_conditions": [
                    "a new preregistered frozen-plan experiment improves a public metric on at least two candidates without false attribution, unsafe authority, or leakage"
                ],
                "authority_allowed": ["append-only evidence-backed status transition"],
                "authority_forbidden": [
                    "private calibration output persistence",
                    "historical rewrite",
                    "silent blocker removal",
                    "completion without evidence",
                ],
            }
    if TRANSITION_ID not in transitions:
        ledger.setdefault("supersession_receipts", []).append(transition_value)
    else:
        transition = next(
            row for row in ledger["supersession_receipts"]
            if row["transition_id"] == TRANSITION_ID
        )
        transition.update(transition_value)
    ledger["last_updated_batch"] = "Batch103"
    ledger["last_updated_commit"] = WORKFLOW_HEAD
    ledger["last_updated_timestamp"] = STAMP
    LEDGER.write_text(
        json.dumps(ledger, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(
        json.dumps(
            {
                "status": "PASS",
                "goal_030_status": goal30["status"],
                "transition_id": TRANSITION_ID,
                "ledger_sha256": _sha256(LEDGER),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
