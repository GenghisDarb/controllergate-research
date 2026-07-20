#!/usr/bin/env python3
"""Append Batch101 post-experiment status receipts to every master goal."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "configs/controllergate_master_completion_ledger_v2.json"
OUT = ROOT / "outputs/post_v2_37_hardening_batch101_canonical_semantic_replay_exact_incident_salvage_ownership_closure"
STAMP = "2026-07-19T23:59:00Z"
IMPLEMENTATION_COMMIT = "d9bf6b53bc9a8cf9c01c0f5fd41920dc057a3e54"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
    evidence_paths = [
        OUT / "batch101_registered_cell_execution_ledger_v1.jsonl",
        OUT / "pair_validity_receipts_v3.jsonl",
        OUT / "controller_audit_counterfactual_terminal_records_v4.jsonl",
        OUT / "architecture_component_gain_gate_v3.json",
    ]
    rels = [path.relative_to(ROOT).as_posix() for path in evidence_paths]
    hashes = {rel: digest(ROOT / rel) for rel in rels}
    # Preserve the eight sealed Batch101 transitions.  A status review that
    # does not change status is reflected on each goal and in the generated
    # goal-status output; it is not a supersession transition.
    receipts = [row for row in ledger.setdefault("supersession_receipts", []) if not row.get("transition_id", "").endswith(":post-experiment-review")]
    ledger["supersession_receipts"] = receipts
    exact = {
        "CG-GOAL-006-TYPED-INCIDENT-REMATERIALIZATION": ["seven_programs_remain_not_exactly_materialized", "openbb_cells_not_executed"],
        "CG-GOAL-008-CAUSAL-OWNERSHIP-CLOSURE": ["necessity_not_executed", "sufficiency_not_executed", "remaining_alternatives_not_excluded"],
        "CG-GOAL-009-ARCHITECTURE-GAIN": ["zero_supported_ownership_terminals", "architecture_gain_not_scoreable"],
        "CG-GOAL-010-TLD-ROUTING-GAIN": ["zero_supported_ownership_terminals", "tld_ordering_gain_not_scoreable"],
        "CG-GOAL-018-PUBLIC-DEFAULT-NON-TLD-MODE": ["installed_cross_platform_non_tld_end_to_end_test_not_yet_complete"],
    }
    for goal in ledger["goals"]:
        if goal["goal_id"] in exact:
            goal["active_blockers"] = sorted(set(goal.get("active_blockers", []) + exact[goal["goal_id"]]))
        goal["last_updated_timestamp"] = STAMP
        goal["last_updated_commit"] = IMPLEMENTATION_COMMIT
    ledger["last_updated_batch"] = "Batch101"
    ledger["last_updated_timestamp"] = STAMP
    ledger["last_updated_commit"] = IMPLEMENTATION_COMMIT
    LEDGER.write_text(json.dumps(ledger, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"status": "PASS", "goals_reviewed": len(ledger["goals"]), "transition_receipts": len(receipts)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
