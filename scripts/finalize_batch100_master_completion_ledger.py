"""Apply executed Batch100 evidence to the permanent completion ledger."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "configs/controllergate_master_completion_ledger_v2.json"
RECEIPT = ROOT / "outputs/post_v2_37_hardening_batch100_matched_counterfactual_execution_causal_ownership_architecture_gain_master_roadmap_lock/batch100_official_workflow_execution_receipt.json"
RUN_HEAD = "8c1e56e0cefa6ca8445600264e75a62dce9ba2f1"
STAMP = "2026-07-19T22:37:27Z"


def main() -> int:
    ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
    by_id = {row["goal_id"]: row for row in ledger["goals"]}
    rel = RECEIPT.relative_to(ROOT).as_posix()
    digest = hashlib.sha256(RECEIPT.read_bytes()).hexdigest()
    updates = {
        "CG-GOAL-005-INCIDENT-IDENTITY-AND-PARITY": ("COMPLETE_WITH_LIMITED_SCOPE", ["exact_incident_provider_parity_limited_for_registered_candidates"]),
        "CG-GOAL-006-TYPED-INCIDENT-REMATERIALIZATION": ("BLOCKED", ["typed_incident_materialized_2_of_9", "registered_exact_provider_cells_missing"]),
        "CG-GOAL-007-MATCHED-COUNTERFACTUAL-EXECUTION": ("COMPLETE_WITH_LIMITED_SCOPE", ["16_of_32_registered_cells_received_duplicate_clean_replay", "remaining_exact_provider_cells_blocked"]),
        "CG-GOAL-008-CAUSAL-OWNERSHIP-CLOSURE": ("BLOCKED", ["necessity_sufficiency_interaction_and_ownership_receipts_zero"]),
        "CG-GOAL-009-ARCHITECTURE-GAIN": ("BLOCKED", ["causal_coverage_zero", "architecture_gain_not_established"]),
        "CG-GOAL-010-TLD-ROUTING-GAIN": ("BLOCKED", ["tld_ordering_gain_not_established"]),
    }
    for goal_id, (status, blockers) in updates.items():
        goal = by_id[goal_id]
        goal["status"] = status
        goal["active_blockers"] = blockers
        goal["current_evidence"] = sorted(set([*goal.get("current_evidence", []), rel]))
        goal.setdefault("evidence_hashes", {})[rel] = digest
        goal["last_updated_commit"] = RUN_HEAD
        goal["last_updated_timestamp"] = STAMP
        if status == "COMPLETE_WITH_LIMITED_SCOPE":
            goal["completion_commit"] = RUN_HEAD
            goal["completion_batch"] = "Batch100"
    by_id["CG-GOAL-018-PUBLIC-DEFAULT-NON-TLD-MODE"]["active_blockers"] = ["ordinary_public_non_tld_default_mode_not_established"]
    ledger["last_updated_batch"] = "Batch100"
    ledger["last_updated_commit"] = RUN_HEAD
    ledger["last_updated_timestamp"] = STAMP
    LEDGER.write_text(json.dumps(ledger, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
