from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from controllergate.governance.master_completion_ledger import REQUIRED_GOALS


TITLES = (
    "Official Batch098 ingest", "Contradiction-root reconstruction", "Causal-evidence hierarchy", "Corrected constraint model", "Official Batch099 ingest", "Incident identity and provider parity", "Typed incident rematerialization", "Matched counterfactual execution", "Causal ownership closure", "Architecture gain", "TLD routing gain", "Balanced historical cohort", "Abstention-required cohort", "Mixed-failure cohort", "Prospective validation", "Memory-lift validation", "Protected repair actuation", "External replication", "Public default non-TLD mode", "Product Beta", "Self-maintaining software evidence",
)

EVIDENCE = {
    0: ["outputs/post_v2_37_hardening_batch099_causal_differential_intervention_contradiction_root_closure_master_completion_ledger/batch098_official_ingest/ingest_receipts/batch098_official_ingest_receipt.json"],
    1: ["outputs/post_v2_37_hardening_batch099_causal_differential_intervention_contradiction_root_closure_master_completion_ledger/causal_differential/batch099_contradiction_root_map_v1.jsonl"],
    2: ["outputs/post_v2_37_hardening_batch099_causal_differential_intervention_contradiction_root_closure_master_completion_ledger/causal_differential/batch099_causal_evidence_hierarchy_v1.json"],
    3: ["outputs/post_v2_37_hardening_batch099_causal_differential_intervention_contradiction_root_closure_master_completion_ledger/causal_differential/batch099_corrected_constraint_model_v1.json"],
    4: ["outputs/post_v2_37_hardening_batch100_matched_counterfactual_execution_causal_ownership_architecture_gain_master_roadmap_lock/batch099_official_ingest/ingest_receipts/batch099_official_ingest_receipt.json"],
}

COMPLETIONS = {0: ("9813ac5d4503bed8e09e4ae92e33083563bddcd0", "Batch099"), 1: ("d456deff6a87509abddd3e8133391a36defa0bf5", "Batch099"), 2: ("d456deff6a87509abddd3e8133391a36defa0bf5", "Batch099"), 3: ("d456deff6a87509abddd3e8133391a36defa0bf5", "Batch099"), 4: ("0db790033f1baa3e5278f4fe64652e374e7b3cd2", "Batch100")}

BLOCKERS = {
    5: ["candidate_incident_identity_parity_not_yet_reconstructed"],
    6: ["typed_incident_rematerialization_not_yet_executed"],
    7: ["candidate_bound_matched_counterfactual_execution_missing"],
    8: ["ownership_grade_differential_evidence_missing"],
    9: ["architecture_gain_not_established"],
    10: ["tld_routing_gain_not_established"],
    11: ["historical_cohort_below_24_episodes"],
    12: ["abstention_required_cohort_missing"],
    13: ["preregistered_mixed_failure_cohort_missing"],
    14: ["prospective_held_out_validation_not_run"],
    15: ["memory_lift_not_demonstrated"],
    16: ["protected_repair_prerequisites_not_met"],
    17: ["independent_external_replication_not_run"],
    18: ["ordinary_public_non_tld_default_not_validated"],
    19: ["product_beta_exit_criteria_not_met"],
    20: ["self_maintaining_software_not_demonstrated"],
}


def digest(relative: str) -> str:
    return hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="configs/controllergate_master_completion_ledger_v2.json")
    parser.add_argument("--updated-commit", default="0db790033f1baa3e5278f4fe64652e374e7b3cd2")
    args = parser.parse_args()
    timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    goals = []
    for index, goal_id in enumerate(REQUIRED_GOALS):
        current = EVIDENCE.get(index, [])
        complete = index in COMPLETIONS
        goals.append({
            "goal_id": goal_id,
            "title": TITLES[index],
            "status": "COMPLETE" if complete else "NOT_STARTED",
            "prerequisites": [] if index == 0 else [REQUIRED_GOALS[index - 1]] if index <= 10 else [REQUIRED_GOALS[4]],
            "required_evidence": [f"executed evidence for {TITLES[index].lower()}"],
            "current_evidence": current,
            "evidence_hashes": {path: digest(path) for path in current},
            "completion_commit": COMPLETIONS[index][0] if complete else None,
            "completion_batch": COMPLETIONS[index][1] if complete else None,
            "active_blockers": [] if complete else BLOCKERS[index],
            "reopen_conditions": ["independently verified evidence defect or append-only supersession"],
            "authority_allowed": ["evidence and protocol work within the recorded scope"],
            "authority_forbidden": ["claim promotion without executed goal evidence", "repair count mutation", "release promotion"],
            "last_updated_commit": args.updated_commit,
            "last_updated_timestamp": timestamp,
        })
    ledger = {"schema_version": "controllergate-master-completion-ledger-v2", "append_only": True, "batch_output_links": {"Batch098": "outputs/post_v2_37_hardening_batch098_causal_hypergraph_real_materialization_topology_probe_closure", "Batch099": "outputs/post_v2_37_hardening_batch099_causal_differential_intervention_contradiction_root_closure_master_completion_ledger", "Batch100": "outputs/post_v2_37_hardening_batch100_matched_counterfactual_execution_causal_ownership_architecture_gain_master_roadmap_lock"}, "supersession_receipts": [], "goals": goals}
    path = ROOT / args.output
    path.write_text(json.dumps(ledger, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"status": "PASS", "goal_count": len(goals), "output": args.output}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
